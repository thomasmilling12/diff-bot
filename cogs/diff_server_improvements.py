"""
cogs/diff_server_improvements.py
─────────────────────────────────
Background-task features:
  7.  Daily activity digest → mod-hub (9 AM UTC)
  8.  1-hour meet reminder  → meet-info channel
  9.  Inactive member re-engagement DM (weekly, 45+ days no attendance)
  10. Crew competition weekly leaderboard post
  11. !meetphotos command — open 24-hour photo-submission window in a thread
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks

# ── Helpers to reach main-bot globals ─────────────────────────────────────────
def _main():
    return sys.modules.get("__main__")

def _get(name, default=None):
    m = _main()
    return getattr(m, name, default) if m else default

# ── Constants pulled from main bot at runtime ──────────────────────────────────
def MOD_HUB()         -> int: return _get("MOD_HUB_CHANNEL_ID", 0)
def STAFF_LOGS()      -> int: return _get("STAFF_LOGS_CHANNEL_ID", 0)
def GUILD_ID()        -> int: return _get("GUILD_ID", 0)
def LOGO_URL()        -> str: return _get("DIFF_LOGO_URL", "")
def LEADER_ROLE()     -> int: return _get("LEADER_ROLE_ID", 0)
def CO_LEADER_ROLE()  -> int: return _get("CO_LEADER_ROLE_ID", 0)
def MANAGER_ROLE()    -> int: return _get("MANAGER_ROLE_ID", 0)
def HOST_ROLE()       -> int: return _get("HOST_ROLE_ID", 0)
def CREW_ROLE()       -> int: return _get("CREW_MEMBER_ROLE_ID", 0)
def MEET_INFO_CH()    -> int: return _get("MEET_INFO_CHANNEL_ID", 0)
def LB_CHANNEL()      -> int: return _get("LEADERBOARD_CHANNEL_ID", 0)
def ACTIVITY_FILE()   -> str: return _get("ACTIVITY_FILE", "diff_data/diff_activity_stats.json")
def MEETS_FILE()      -> str: return _get("MEETS_FILE", "diff_data/diff_meet_records.json")
def OM_FILE()         -> str: return _get("_OM_DATA_FILE", "diff_data/diff_official_meets.json")
def REP_FILE()        -> str: return _get("REPUTATION_FILE", "diff_data/diff_reputation_stats.json")
def DATA_FOLDER()     -> str: return _get("DATA_FOLDER", "diff_data")

# Persistent state file for this cog
_STATE_FILE = os.path.join("diff_data", "diff_improvements_state.json")
_PHOTO_SUBMISSIONS_FILE = os.path.join("diff_data", "diff_photo_submissions.json")
# Channel used for photo submission announcements (general meet channel)
_MEET_GENERAL_CHANNEL_ID = 1485870611069796374  # _OFFICIAL_MEET_CHANNEL_ID


def _state_load() -> dict:
    try:
        with open(_STATE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _state_save(d: dict) -> None:
    os.makedirs(os.path.dirname(_STATE_FILE), exist_ok=True)
    with open(_STATE_FILE, "w") as f:
        json.dump(d, f, indent=2)


def _load_json(path: str) -> dict:
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _load_photo_submissions() -> dict:
    try:
        with open(_PHOTO_SUBMISSIONS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_photo_submissions(d: dict) -> None:
    os.makedirs(os.path.dirname(_PHOTO_SUBMISSIONS_FILE), exist_ok=True)
    with open(_PHOTO_SUBMISSIONS_FILE, "w") as f:
        json.dump(d, f, indent=2)


class DiffServerImprovements(commands.Cog):
    """Background tasks: digest, meet reminders, inactive DMs, crew LB, photo submissions."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._reminded_meets: set[str] = set()  # meet IDs already reminded this session
        self._digest_sent_today: str = ""        # ISO date of last digest
        self._inactive_check_done: str = ""      # ISO week of last inactive run
        self._crew_lb_done: str = ""             # ISO week of last crew LB post

        self._daily_digest.start()
        self._meet_reminder_check.start()
        self._inactive_member_check.start()
        self._crew_leaderboard_weekly.start()

    def cog_unload(self) -> None:
        self._daily_digest.cancel()
        self._meet_reminder_check.cancel()
        self._inactive_member_check.cancel()
        self._crew_leaderboard_weekly.cancel()

    # ─────────────────────────────────────────────────────────────────────────
    # 7. Daily activity digest → mod-hub at 09:00 UTC
    # ─────────────────────────────────────────────────────────────────────────

    @tasks.loop(minutes=10)
    async def _daily_digest(self) -> None:
        now = datetime.now(timezone.utc)
        today_str = now.strftime("%Y-%m-%d")
        if self._digest_sent_today == today_str:
            return
        if now.hour != 9:
            return

        self._digest_sent_today = today_str
        guild = self.bot.get_guild(GUILD_ID())
        if not guild:
            return

        mod_hub = guild.get_channel(MOD_HUB())
        if not isinstance(mod_hub, discord.TextChannel):
            return

        # Gather stats from JSON files
        activity  = _load_json(ACTIVITY_FILE())
        rep_data  = _load_json(REP_FILE())
        meets_raw = _load_json(MEETS_FILE())

        # Members who joined in the last 24 hours
        yesterday = now - timedelta(hours=24)
        new_members = [
            m for m in guild.members
            if m.joined_at and m.joined_at > yesterday and not m.bot
        ]

        # Open tickets count
        ticket_count = sum(
            1 for ch in guild.text_channels
            if (ch.topic or "") and "ticket_owner=" in ch.topic and "ticket_type=" in ch.topic
        )

        # Meets in the last 24 hours (any meet with created_at in last 24h)
        recent_meets = 0
        for mid, mrec in meets_raw.items():
            try:
                created = datetime.fromisoformat(mrec.get("created_at", ""))
                if created.replace(tzinfo=timezone.utc) > yesterday:
                    recent_meets += 1
            except Exception:
                pass

        # Warning count from main data
        _main_mod = _main()
        warn_data = {}
        if _main_mod:
            warn_data = getattr(_main_mod, "data", {}).get("warnings", {})
        recent_warns = 0
        for _uid, _wlist in warn_data.items():
            for _w in _wlist:
                try:
                    _wt = datetime.fromisoformat(_w.get("timestamp", ""))
                    if _wt.replace(tzinfo=timezone.utc) > yesterday:
                        recent_warns += 1
                except Exception:
                    pass

        embed = discord.Embed(
            title="📊 DIFF Daily Activity Digest",
            description=f"Summary for **{now.strftime('%A, %B %d %Y')}**",
            color=discord.Color.blurple(),
            timestamp=now,
        )
        embed.add_field(name="👋 New Members (24h)", value=str(len(new_members)), inline=True)
        embed.add_field(name="🎟️ Open Tickets",     value=str(ticket_count),    inline=True)
        embed.add_field(name="🚗 Meets Created (24h)", value=str(recent_meets), inline=True)
        embed.add_field(name="⚠️ Warnings Issued (24h)", value=str(recent_warns), inline=True)
        embed.add_field(name="👥 Total Members", value=str(guild.member_count or 0), inline=True)
        embed.set_footer(text="Different Meets • Daily Digest")
        if LOGO_URL():
            embed.set_thumbnail(url=LOGO_URL())

        try:
            await mod_hub.send(embed=embed)
        except Exception:
            pass

    @_daily_digest.before_loop
    async def _before_daily_digest(self) -> None:
        await self.bot.wait_until_ready()

    # ─────────────────────────────────────────────────────────────────────────
    # 8. 1-hour meet reminder
    # ─────────────────────────────────────────────────────────────────────────

    @tasks.loop(minutes=5)
    async def _meet_reminder_check(self) -> None:
        guild = self.bot.get_guild(GUILD_ID())
        if not guild:
            return

        meet_ch = guild.get_channel(MEET_INFO_CH()) or guild.get_channel(_MEET_GENERAL_CHANNEL_ID)
        if not isinstance(meet_ch, discord.TextChannel):
            return

        now_ts = datetime.now(timezone.utc).timestamp()
        meets  = _load_json(MEETS_FILE())

        for meet_id, rec in meets.items():
            sched = rec.get("scheduled_time")
            if not sched or rec.get("closed"):
                continue
            try:
                sched_ts = float(sched)
            except (TypeError, ValueError):
                continue

            time_until = sched_ts - now_ts
            # Remind when 55–65 minutes away and not yet reminded
            if 55 * 60 < time_until < 65 * 60 and meet_id not in self._reminded_meets:
                self._reminded_meets.add(meet_id)
                host_id   = rec.get("host_id")
                title     = rec.get("title") or meet_id
                host_str  = f"<@{host_id}>" if host_id else "TBD"
                embed = discord.Embed(
                    title="⏰ Meet Starting in 1 Hour!",
                    description=(
                        f"**{title}** is starting in approximately **1 hour**!\n\n"
                        f"🎮 **Host:** {host_str}\n"
                        f"🕒 **Scheduled:** <t:{int(sched_ts)}:F>"
                    ),
                    color=discord.Color.green(),
                    timestamp=datetime.now(timezone.utc),
                )
                embed.set_footer(text="Different Meets • Auto Reminder")
                if LOGO_URL():
                    embed.set_thumbnail(url=LOGO_URL())
                try:
                    await meet_ch.send(content="@here", embed=embed)
                except Exception:
                    pass

        # Also check official meets (_om_load_records)
        om_data = _load_json(OM_FILE())
        for om_id, om_rec in om_data.items():
            sched = om_rec.get("scheduled_time") or om_rec.get("start_unix")
            if not sched or om_rec.get("closed"):
                continue
            try:
                sched_ts = float(sched)
            except (TypeError, ValueError):
                continue
            reminder_key = f"om_{om_id}"
            time_until = sched_ts - now_ts
            if 55 * 60 < time_until < 65 * 60 and reminder_key not in self._reminded_meets:
                self._reminded_meets.add(reminder_key)
                title    = om_rec.get("title") or om_id
                host_id  = om_rec.get("host_id")
                host_str = f"<@{host_id}>" if host_id else "TBD"
                embed = discord.Embed(
                    title="⏰ Official Meet Starting in 1 Hour!",
                    description=(
                        f"**{title}** is kicking off in **1 hour**!\n\n"
                        f"🎮 **Host:** {host_str}\n"
                        f"🕒 **Time:** <t:{int(sched_ts)}:F>"
                    ),
                    color=discord.Color.brand_green(),
                    timestamp=datetime.now(timezone.utc),
                )
                embed.set_footer(text="Different Meets • Auto Reminder")
                if LOGO_URL():
                    embed.set_thumbnail(url=LOGO_URL())
                try:
                    await meet_ch.send(content="@here", embed=embed)
                except Exception:
                    pass

    @_meet_reminder_check.before_loop
    async def _before_meet_reminder(self) -> None:
        await self.bot.wait_until_ready()

    # ─────────────────────────────────────────────────────────────────────────
    # 9. Inactive member re-engagement DM (weekly, members with 0 attendance in 45+ days)
    # ─────────────────────────────────────────────────────────────────────────

    @tasks.loop(hours=24)
    async def _inactive_member_check(self) -> None:
        now = datetime.now(timezone.utc)
        iso_week = now.strftime("%Y-W%U")
        if self._inactive_check_done == iso_week:
            return
        # Only run once a week on Monday UTC
        if now.weekday() != 0:
            return

        self._inactive_check_done = iso_week
        guild = self.bot.get_guild(GUILD_ID())
        if not guild:
            return

        activity = _load_json(ACTIVITY_FILE())
        cutoff   = now - timedelta(days=45)
        dm_sent  = 0

        for uid_str, stats in activity.items():
            last_updated = stats.get("last_updated")
            if not last_updated:
                continue
            try:
                last_dt = datetime.fromisoformat(last_updated).replace(tzinfo=timezone.utc)
            except Exception:
                continue
            if last_dt > cutoff:
                continue  # recently active

            try:
                member = guild.get_member(int(uid_str))
            except Exception:
                continue
            if not member or member.bot:
                continue

            attended = stats.get("meets_attended", 0)
            try:
                embed = discord.Embed(
                    title="👋 We miss you at DIFF Meets!",
                    description=(
                        f"Hey {member.mention}!\n\n"
                        "It's been a while since we've seen you at a meet. "
                        "We have regular sessions running — would love to see you back behind the wheel!\n\n"
                        f"You've attended **{attended}** meet(s) with us so far. "
                        "Come join the next one and keep the streak going! 🚗💨"
                    ),
                    color=discord.Color.from_rgb(88, 101, 242),
                    timestamp=now,
                )
                embed.add_field(
                    name="🗓️ Find Upcoming Meets",
                    value="Check **#upcoming-meets** in the server for the latest schedule.",
                    inline=False,
                )
                embed.set_footer(text="Different Meets • Community Team")
                if LOGO_URL():
                    embed.set_thumbnail(url=LOGO_URL())
                await member.send(embed=embed)
                dm_sent += 1
                await asyncio.sleep(1)  # rate-limit courtesy
            except (discord.Forbidden, discord.HTTPException):
                pass

        # Log to staff logs
        logs_ch = guild.get_channel(STAFF_LOGS())
        if isinstance(logs_ch, discord.TextChannel) and dm_sent > 0:
            try:
                log_e = discord.Embed(
                    title="📬 Inactive Member Re-Engagement",
                    description=f"Sent re-engagement DMs to **{dm_sent}** member(s) inactive 45+ days.",
                    color=discord.Color.blurple(),
                    timestamp=now,
                )
                log_e.set_footer(text="Different Meets • Weekly Inactive Check")
                await logs_ch.send(embed=log_e)
            except Exception:
                pass

    @_inactive_member_check.before_loop
    async def _before_inactive_check(self) -> None:
        await self.bot.wait_until_ready()

    # ─────────────────────────────────────────────────────────────────────────
    # 10. Crew competition weekly leaderboard post (Monday 10 AM UTC)
    # ─────────────────────────────────────────────────────────────────────────

    @tasks.loop(hours=24)
    async def _crew_leaderboard_weekly(self) -> None:
        now = datetime.now(timezone.utc)
        iso_week = now.strftime("%Y-W%U")
        if self._crew_lb_done == iso_week:
            return
        # Only Mondays at 10 AM UTC
        if now.weekday() != 0 or now.hour < 10:
            return

        self._crew_lb_done = iso_week
        guild = self.bot.get_guild(GUILD_ID())
        if not guild:
            return

        lb_ch = guild.get_channel(LB_CHANNEL())
        if not isinstance(lb_ch, discord.TextChannel):
            return

        activity = _load_json(ACTIVITY_FILE())
        rep_data = _load_json(REP_FILE())
        crew_role = guild.get_role(CREW_ROLE())

        if not crew_role:
            return

        # For simplicity, group by display-name prefix (first word before space).
        # Real crew grouping would need a crew-membership JSON — this is a fair approximation.
        crew_scores: dict[str, dict] = {}

        for member in crew_role.members:
            if member.bot:
                continue
            uid_str = str(member.id)
            att  = activity.get(uid_str, {}).get("meets_attended", 0)
            rep  = rep_data.get(uid_str, {}).get("reputation", 0) if isinstance(rep_data.get(uid_str), dict) else 0
            score = att * 3 + rep

            # Try to group by crew name from display name (e.g. "[DIFF] Name" → "DIFF")
            dname = member.display_name
            crew_tag = "Independent"
            if "[" in dname and "]" in dname:
                crew_tag = dname[dname.index("[")+1:dname.index("]")].strip()
            elif "(" in dname and ")" in dname:
                crew_tag = dname[dname.index("(")+1:dname.index(")")].strip()

            entry = crew_scores.setdefault(crew_tag, {"score": 0, "members": 0, "top_rep": 0})
            entry["score"]   += score
            entry["members"] += 1
            entry["top_rep"]  = max(entry["top_rep"], rep)

        if not crew_scores:
            return

        sorted_crews = sorted(crew_scores.items(), key=lambda x: x[1]["score"], reverse=True)
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, (crew, stats) in enumerate(sorted_crews[:10]):
            medal = medals[i] if i < 3 else f"**#{i+1}**"
            lines.append(
                f"{medal} **{crew}** — "
                f"⭐ {stats['score']} pts · "
                f"👥 {stats['members']} members · "
                f"🏆 Top rep: {stats['top_rep']}"
            )

        embed = discord.Embed(
            title="🏁 Weekly Crew Leaderboard",
            description="\n".join(lines) or "*No crew data found.*",
            color=discord.Color.gold(),
            timestamp=now,
        )
        embed.set_footer(text=f"Week of {now.strftime('%B %d, %Y')} • Score = (Attendance × 3) + Reputation")
        if LOGO_URL():
            embed.set_thumbnail(url=LOGO_URL())

        try:
            await lb_ch.send(embed=embed)
        except Exception:
            pass

    @_crew_leaderboard_weekly.before_loop
    async def _before_crew_lb(self) -> None:
        await self.bot.wait_until_ready()

    # ─────────────────────────────────────────────────────────────────────────
    # 11. !meetphotos — open a 24-hour photo-submission thread
    # ─────────────────────────────────────────────────────────────────────────

    @commands.command(name="meetphotos")
    async def meetphotos(self, ctx: commands.Context, *, meet_name: str = "Recent Meet") -> None:
        """Open a 24-hour photo submission thread for a meet. Staff only."""
        if not isinstance(ctx.author, discord.Member):
            return
        is_staff = any(
            r.id in {LEADER_ROLE(), CO_LEADER_ROLE(), MANAGER_ROLE(), HOST_ROLE()}
            for r in ctx.author.roles
        )
        if not is_staff:
            return await ctx.send("Only staff can open photo submission windows.", delete_after=8)

        try:
            await ctx.message.delete()
        except Exception:
            pass

        now = datetime.now(timezone.utc)
        channel = ctx.channel

        # Create a public thread in the current channel
        try:
            thread = await channel.create_thread(
                name=f"📸 {meet_name} — Photo Submissions",
                auto_archive_duration=1440,  # 24 hours
                reason=f"Photo submission thread opened by {ctx.author}",
            )
        except discord.Forbidden:
            return await ctx.send("I need `Create Public Threads` permission in this channel.", delete_after=10)
        except Exception as e:
            return await ctx.send(f"Failed to create thread: `{e}`", delete_after=10)

        embed = discord.Embed(
            title="📸 Photo Submissions Open!",
            description=(
                f"Post your best screenshots from **{meet_name}** right here!\n\n"
                "**Guidelines:**\n"
                "• Drop your image(s) directly in this thread\n"
                "• Include a short caption if you like\n"
                "• Keep it clean — meet builds, scenery, moments\n\n"
                "⏰ This thread closes automatically after **24 hours**.\n"
                "Top photos may be featured in the community highlights!"
            ),
            color=discord.Color.from_rgb(255, 165, 0),
            timestamp=now,
        )
        embed.set_footer(text=f"Opened by {ctx.author.display_name} • Different Meets")
        if LOGO_URL():
            embed.set_thumbnail(url=LOGO_URL())

        await thread.send(embed=embed)

        # Announce in the channel
        announce_embed = discord.Embed(
            description=(
                f"📸 **Photo submissions for {meet_name} are now open!**\n"
                f"Drop your screenshots in {thread.mention} — window closes in 24 hours."
            ),
            color=discord.Color.from_rgb(255, 165, 0),
        )
        await channel.send(embed=announce_embed)

        # Store submission record
        subs = _load_photo_submissions()
        subs[str(thread.id)] = {
            "meet_name": meet_name,
            "opened_by": ctx.author.id,
            "opened_at": now.isoformat(),
            "channel_id": channel.id,
            "thread_id": thread.id,
        }
        _save_photo_submissions(subs)

    # ─────────────────────────────────────────────────────────────────────────
    # FAQ auto-surface when a support ticket opens (listener)
    # ─────────────────────────────────────────────────────────────────────────

    @commands.Cog.listener("on_message")
    async def _faq_auto_surface(self, message: discord.Message) -> None:
        """When the first message in a new ticket channel is posted, surface matching FAQs."""
        if message.author.id != self.bot.user.id:
            return
        if not isinstance(message.channel, discord.TextChannel):
            return
        topic = message.channel.topic or ""
        if "ticket_owner=" not in topic or "ticket_type=" not in topic:
            return

        # Only surface FAQ on the very first bot message (ticket creation embed)
        history = [m async for m in message.channel.history(limit=3, oldest_first=True)]
        if not history or history[0].id != message.id:
            return

        _main_mod = _main()
        if not _main_mod:
            return
        _faq_lookup = getattr(_main_mod, "_faq_lookup", None)
        if not _faq_lookup:
            return

        # Gather context from the embed description
        combined = ""
        if message.embeds:
            for emb in message.embeds:
                combined += (emb.description or "") + " ".join(
                    f.value for f in emb.fields
                )

        matches = _faq_lookup(combined)
        if not matches:
            return

        faq_embed = discord.Embed(
            title="💡 Relevant FAQs",
            description="These answers may help while you wait for staff:",
            color=discord.Color.yellow(),
        )
        for trigger, answer in matches[:3]:
            faq_embed.add_field(name=f"Q: {trigger}", value=answer[:512], inline=False)
        faq_embed.set_footer(text="DIFF FAQ System • Different Meets")
        try:
            await message.channel.send(embed=faq_embed)
        except Exception:
            pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DiffServerImprovements(bot))
