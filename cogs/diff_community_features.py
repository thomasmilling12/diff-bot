"""
cogs/diff_community_features.py
────────────────────────────────
12 community & moderation features — all times in Eastern Time (ET).

 1.  Post-meet feedback     (!meetfeedback / !feedbackresults)
 2.  Meet voting polls      (!meetvote — auto-closes after 24h)
 3.  Attendance streaks     (!updatestreaks / !streak)
 4.  RSVP waitlist          (!joinwaitlist / !nextwaitlist / !waitlist)
 5.  Temp-ban               (!tempban — auto-unban background task)
 6.  Word + invite filter   (!filter add/remove/list — invite always on)
 7.  Member lookup          (!lookup)
 8.  Giveaway system        (!giveaway — button entry, auto-draw)
 9.  Monthly recap          (auto-post 1st of month, 10 AM ET → mod-hub)
10.  Suggestion box         (!suggest — posts to mod-hub with reactions)
11.  Staff on-duty          (!onduty / !offduty / !whosonduty)
12.  Monthly application    (auto-post 1st of month alongside recap)
"""

from __future__ import annotations

import asyncio
import json
import os
import random
import re
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks

_EST_TZ = ZoneInfo("America/New_York")


def _est_now() -> datetime:
    return datetime.now(_EST_TZ)


# ── Access main-bot globals safely ────────────────────────────────────────────
def _main():
    return sys.modules.get("__main__")


def _get(name, default=None):
    m = _main()
    return getattr(m, name, default) if m else default


# ── Runtime constants from bot.py ─────────────────────────────────────────────
def _GUILD_ID()       -> int: return _get("GUILD_ID", 0)
def _MOD_HUB()        -> int: return _get("MOD_HUB_CHANNEL_ID", 0)
def _STAFF_LOGS()     -> int: return _get("STAFF_LOGS_CHANNEL_ID", 0)
def _LOGO()           -> str: return _get("DIFF_LOGO_URL", "")
def _LEADER()         -> int: return _get("LEADER_ROLE_ID", 0)
def _CO_LEADER()      -> int: return _get("CO_LEADER_ROLE_ID", 0)
def _MANAGER()        -> int: return _get("MANAGER_ROLE_ID", 0)
def _HOST()           -> int: return _get("HOST_ROLE_ID", 0)
def _ACTIVITY_FILE()  -> str: return _get("ACTIVITY_FILE", "diff_data/diff_activity_stats.json")
def _MEETS_FILE()     -> str: return _get("MEETS_FILE", "diff_data/diff_meet_records.json")
def _REP_FILE()       -> str: return _get("REPUTATION_FILE", "diff_data/diff_reputation_stats.json")
def _APPS_FILE()      -> str: return _get("APPLICATIONS_FILE", "diff_applications_full.json")

_DATA = "diff_data"
_TEMPBAN_FILE       = os.path.join(_DATA, "diff_tempbans.json")
_GIVEAWAY_FILE      = os.path.join(_DATA, "diff_giveaways.json")
_ONDUTY_FILE        = os.path.join(_DATA, "diff_onduty.json")
_SUGGESTIONS_FILE   = os.path.join(_DATA, "diff_suggestions.json")
_WORD_FILTER_FILE   = os.path.join(_DATA, "diff_word_filter.json")
_STREAKS_FILE       = os.path.join(_DATA, "diff_streaks.json")
_WAITLIST_FILE      = os.path.join(_DATA, "diff_waitlists.json")
_FEEDBACK_FILE      = os.path.join(_DATA, "diff_feedback.json")
_MONTHLY_STATE_FILE = os.path.join(_DATA, "diff_monthly_state.json")
_POLLS_FILE         = os.path.join(_DATA, "diff_polls.json")


# ── JSON helpers ──────────────────────────────────────────────────────────────
def _load(path: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save(path: str, d: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(d, f, indent=2)


# ── Shared helpers ────────────────────────────────────────────────────────────
def _is_staff(member: discord.Member) -> bool:
    return any(r.id in {_LEADER(), _CO_LEADER(), _MANAGER(), _HOST()} for r in member.roles)


def _parse_duration(s: str) -> "timedelta | None":
    """Parse '30m', '2h', '3d', '1w' → timedelta. Returns None if invalid."""
    m = re.fullmatch(r"(\d+)(m|h|d|w)", s.strip().lower())
    if not m:
        return None
    v, u = int(m.group(1)), m.group(2)
    return {"m": timedelta(minutes=v), "h": timedelta(hours=v),
            "d": timedelta(days=v),    "w": timedelta(weeks=v)}[u]


def _brand(embed: discord.Embed) -> discord.Embed:
    if _LOGO():
        embed.set_thumbnail(url=_LOGO())
    return embed


# ══════════════════════════════════════════════════════════════════════════════
# Pi-compatible Button subclasses (no unsupported decorator kwargs)
# ══════════════════════════════════════════════════════════════════════════════

class _StarButton(discord.ui.Button):
    def __init__(self, stars: int, feedback_id: str) -> None:
        super().__init__(
            label="⭐" * stars,
            style=discord.ButtonStyle.secondary,
            custom_id=f"difffb_{feedback_id}_{stars}",
        )
        self.stars = stars
        self.feedback_id = feedback_id

    async def callback(self, interaction: discord.Interaction) -> None:
        fb  = _load(_FEEDBACK_FILE)
        ses = fb.setdefault(self.feedback_id, {"ratings": {}, "meet_name": "Meet"})
        uid = str(interaction.user.id)
        if uid in ses.get("ratings", {}):
            return await interaction.response.send_message(
                "You've already rated this meet.", ephemeral=True
            )
        ses.setdefault("ratings", {})[uid] = self.stars
        _save(_FEEDBACK_FILE, fb)
        await interaction.response.send_message(
            f"Thanks! You rated this meet **{self.stars}/5 ⭐**.", ephemeral=True
        )


class _FeedbackView(discord.ui.View):
    def __init__(self, feedback_id: str) -> None:
        super().__init__(timeout=None)
        for i in range(1, 6):
            self.add_item(_StarButton(i, feedback_id))


class _GiveawayEnterButton(discord.ui.Button):
    def __init__(self, giveaway_id: str, min_meets: int = 0) -> None:
        super().__init__(
            label="🎉 Enter Giveaway",
            style=discord.ButtonStyle.success,
            custom_id=f"diffgw_{giveaway_id}",
        )
        self.giveaway_id = giveaway_id
        self.min_meets   = min_meets

    async def callback(self, interaction: discord.Interaction) -> None:
        if not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Server only.", ephemeral=True)
        gw  = _load(_GIVEAWAY_FILE)
        entry = gw.get(self.giveaway_id)
        if not entry or entry.get("ended"):
            return await interaction.response.send_message("This giveaway has ended.", ephemeral=True)
        uid = str(interaction.user.id)
        if uid in entry.get("entrants", []):
            return await interaction.response.send_message("You're already entered!", ephemeral=True)
        if self.min_meets > 0:
            attended = _load(_ACTIVITY_FILE()).get(uid, {}).get("meets_attended", 0)
            if attended < self.min_meets:
                return await interaction.response.send_message(
                    f"You need **{self.min_meets}** meets attended to enter. You have **{attended}**.",
                    ephemeral=True,
                )
        entry.setdefault("entrants", []).append(uid)
        _save(_GIVEAWAY_FILE, gw)
        count = len(entry["entrants"])
        await interaction.response.send_message(
            f"🎉 Entered! **{count}** entrant(s) so far.", ephemeral=True
        )


class _GiveawayView(discord.ui.View):
    def __init__(self, giveaway_id: str, min_meets: int = 0) -> None:
        super().__init__(timeout=None)
        self.add_item(_GiveawayEnterButton(giveaway_id, min_meets))


class _PollButton(discord.ui.Button):
    def __init__(self, poll_id: str, idx: int, label: str) -> None:
        super().__init__(
            label=f"{idx + 1}. {label[:55]}",
            style=discord.ButtonStyle.primary,
            custom_id=f"diffpoll_{poll_id}_{idx}",
        )
        self.poll_id = poll_id
        self.idx     = idx

    async def callback(self, interaction: discord.Interaction) -> None:
        polls = _load(_POLLS_FILE)
        poll  = polls.get(self.poll_id)
        if not poll or poll.get("ended"):
            return await interaction.response.send_message("This poll has ended.", ephemeral=True)
        uid = str(interaction.user.id)
        if uid in poll.get("votes", {}):
            return await interaction.response.send_message("You've already voted!", ephemeral=True)
        poll.setdefault("votes", {})[uid] = self.idx
        _save(_POLLS_FILE, polls)
        await interaction.response.send_message(
            f"✅ Voted for **{poll['options'][self.idx]}**!", ephemeral=True
        )


class _PollView(discord.ui.View):
    def __init__(self, poll_id: str, options: list) -> None:
        super().__init__(timeout=None)
        for i, opt in enumerate(options[:5]):
            self.add_item(_PollButton(poll_id, i, opt))


# ══════════════════════════════════════════════════════════════════════════════
# Cog
# ══════════════════════════════════════════════════════════════════════════════

class DiffCommunityFeatures(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._tempban_check.start()
        self._giveaway_check.start()
        self._poll_check.start()
        self._monthly_tasks.start()

    def cog_unload(self) -> None:
        self._tempban_check.cancel()
        self._giveaway_check.cancel()
        self._poll_check.cancel()
        self._monthly_tasks.cancel()

    def _staff(self, ctx: commands.Context) -> bool:
        return isinstance(ctx.author, discord.Member) and (
            _is_staff(ctx.author) or ctx.author.guild_permissions.administrator
        )

    async def _del(self, ctx: commands.Context) -> None:
        try:
            await ctx.message.delete()
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────────────────────
    # 1. Post-meet feedback
    # ──────────────────────────────────────────────────────────────────────────

    @commands.command(name="meetfeedback")
    async def meetfeedback(self, ctx: commands.Context, *, meet_name: str = "Recent Meet") -> None:
        """Open a star-rating feedback thread for a meet. Staff only."""
        if not self._staff(ctx):
            return
        await self._del(ctx)

        now         = _est_now()
        feedback_id = f"{ctx.guild.id}_{int(now.timestamp())}"
        fb          = _load(_FEEDBACK_FILE)
        fb[feedback_id] = {"meet_name": meet_name, "ratings": {}, "opened_at": now.isoformat()}
        _save(_FEEDBACK_FILE, fb)

        try:
            thread = await ctx.channel.create_thread(
                name=f"📊 {meet_name} — Rate This Meet",
                auto_archive_duration=1440,
                reason=f"Feedback for {meet_name}",
            )
        except discord.Forbidden:
            return await ctx.send("Missing `Create Public Threads` permission.", delete_after=10)
        except Exception as e:
            return await ctx.send(f"Thread creation failed: `{e}`", delete_after=10)

        embed = _brand(discord.Embed(
            title=f"📊 How was {meet_name}?",
            description=(
                "Click a star rating below — your feedback helps staff improve future meets!\n\n"
                "⭐ Poor  •  ⭐⭐⭐ Good  •  ⭐⭐⭐⭐⭐ Amazing"
            ),
            color=discord.Color.blurple(),
            timestamp=now,
        ))
        embed.set_footer(text=f"Different Meets • Feedback • {now.strftime('%I:%M %p ET')}")
        await thread.send(embed=embed, view=_FeedbackView(feedback_id))

        await ctx.channel.send(
            embed=discord.Embed(
                description=f"📊 **Rate {meet_name}** in {thread.mention}!",
                color=discord.Color.blurple(),
            )
        )

    @commands.command(name="feedbackresults")
    async def feedbackresults(self, ctx: commands.Context, feedback_id: str = "") -> None:
        """Show star-rating results. Omit ID to use the most recent session."""
        if not self._staff(ctx):
            return
        await self._del(ctx)
        fb = _load(_FEEDBACK_FILE)
        if not feedback_id:
            if not fb:
                return await ctx.send("No feedback sessions yet.", delete_after=10)
            feedback_id = sorted(fb.keys())[-1]
        ses = fb.get(feedback_id)
        if not ses:
            return await ctx.send(f"Session `{feedback_id}` not found.", delete_after=10)
        ratings = ses.get("ratings", {})
        if not ratings:
            return await ctx.send("No ratings submitted yet.", delete_after=10)

        avg   = sum(ratings.values()) / len(ratings)
        tally = {i: 0 for i in range(1, 6)}
        for v in ratings.values():
            tally[v] += 1
        max_v = max(tally.values()) or 1

        embed = _brand(discord.Embed(
            title=f"📊 Feedback — {ses.get('meet_name', 'Meet')}",
            description=(
                f"**Average:** {'⭐' * round(avg)} ({avg:.1f}/5)\n"
                f"**Responses:** {len(ratings)}"
            ),
            color=discord.Color.blurple(),
            timestamp=_est_now(),
        ))
        for stars in range(5, 0, -1):
            bar = "█" * tally[stars] + "░" * (max_v - tally[stars])
            embed.add_field(name="⭐" * stars, value=f"`{bar}` {tally[stars]}", inline=False)
        embed.set_footer(text="Different Meets • Feedback System")
        await ctx.send(embed=embed, delete_after=60)

    # ──────────────────────────────────────────────────────────────────────────
    # 2. Meet voting polls
    # ──────────────────────────────────────────────────────────────────────────

    @commands.command(name="meetvote")
    async def meetvote(self, ctx: commands.Context, *, args: str) -> None:
        """!meetvote <question> | Option1 | Option2 | ... (max 5 options, 24h vote)"""
        if not self._staff(ctx):
            return
        await self._del(ctx)
        parts = [p.strip() for p in args.split("|")]
        if len(parts) < 3:
            return await ctx.send(
                "Format: `!meetvote <question> | Option1 | Option2 | ...`", delete_after=12
            )
        question, options = parts[0], parts[1:6]
        now      = _est_now()
        poll_id  = f"{ctx.guild.id}_{int(now.timestamp())}"
        expiry   = now + timedelta(hours=24)
        expiry_ts = int(expiry.timestamp())

        polls = _load(_POLLS_FILE)
        polls[poll_id] = {
            "question": question, "options": options, "votes": {},
            "channel_id": ctx.channel.id, "guild_id": ctx.guild.id,
            "expiry_ts": expiry_ts, "ended": False, "message_id": None,
        }

        embed = _brand(discord.Embed(
            title="🗳️ DIFF Meet Vote",
            description=(
                f"**{question}**\n\n"
                + "\n".join(f"{i+1}. {opt}" for i, opt in enumerate(options))
                + f"\n\n⏰ Closes <t:{expiry_ts}:R>"
            ),
            color=discord.Color.blurple(),
            timestamp=now,
        ))
        embed.set_footer(text=f"Posted by {ctx.author.display_name} • Different Meets")
        msg = await ctx.send(embed=embed, view=_PollView(poll_id, options))
        polls[poll_id]["message_id"] = msg.id
        _save(_POLLS_FILE, polls)

    @tasks.loop(minutes=5)
    async def _poll_check(self) -> None:
        now_ts = int(_est_now().timestamp())
        polls  = _load(_POLLS_FILE)
        changed = False
        for poll_id, poll in polls.items():
            if poll.get("ended") or poll.get("expiry_ts", 0) > now_ts:
                continue
            poll["ended"] = True
            changed       = True
            guild   = self.bot.get_guild(poll.get("guild_id", _GUILD_ID()))
            channel = guild.get_channel(poll["channel_id"]) if guild else None
            if not isinstance(channel, discord.TextChannel):
                continue
            votes   = poll.get("votes", {})
            options = poll.get("options", [])
            tally   = {i: 0 for i in range(len(options))}
            for v in votes.values():
                tally[v] = tally.get(v, 0) + 1
            sorted_opts = sorted(tally.items(), key=lambda x: x[1], reverse=True)
            now = _est_now()
            lines = [
                f"{'🥇' if i == 0 else '▪️'} **{options[idx]}** — {cnt} vote(s)"
                for i, (idx, cnt) in enumerate(sorted_opts)
            ]
            embed = _brand(discord.Embed(
                title="🗳️ Poll Results",
                description=f"**{poll['question']}**\n\n" + "\n".join(lines),
                color=discord.Color.blurple(),
                timestamp=now,
            ))
            embed.add_field(name="Total Votes", value=str(len(votes)), inline=True)
            embed.set_footer(text="Different Meets • Poll Closed")
            try:
                await channel.send(embed=embed)
            except Exception:
                pass
        if changed:
            _save(_POLLS_FILE, polls)

    @_poll_check.before_loop
    async def _before_poll(self) -> None:
        await self.bot.wait_until_ready()

    # ──────────────────────────────────────────────────────────────────────────
    # 3. Attendance streaks
    # ──────────────────────────────────────────────────────────────────────────

    @commands.command(name="updatestreaks")
    async def updatestreaks(self, ctx: commands.Context, *, meet_id: str) -> None:
        """Update attendance streaks from a meet's checked-in list. Staff only."""
        if not self._staff(ctx):
            return
        await self._del(ctx)
        meets = _load(_MEETS_FILE())
        meet  = meets.get(meet_id)
        if not meet:
            return await ctx.send(f"Meet `{meet_id}` not found.", delete_after=10)
        checked_in = meet.get("checked_in", [])
        if not checked_in:
            return await ctx.send(f"No check-ins for `{meet_id}`.", delete_after=10)

        streaks     = _load(_STREAKS_FILE)
        now         = _est_now()
        milestones  = {3: "🔥 3-Meet Streak!", 5: "🔥🔥 5-Meet Streak!", 10: "🏆 10-Meet Streak!"}
        celebrations = []

        for uid in checked_in:
            uid_str = str(uid)
            s = streaks.setdefault(uid_str, {"streak": 0, "best_streak": 0, "last_meet_id": None})
            if s.get("last_meet_id") == meet_id:
                continue  # already processed this meet for this member
            s["streak"]      = s.get("streak", 0) + 1
            s["best_streak"] = max(s.get("best_streak", 0), s["streak"])
            s["last_meet_id"] = meet_id
            if s["streak"] in milestones and ctx.guild:
                member = ctx.guild.get_member(int(uid))
                if member:
                    celebrations.append((member, s["streak"], milestones[s["streak"]]))

        _save(_STREAKS_FILE, streaks)

        for member, streak_count, label in celebrations:
            try:
                await ctx.channel.send(embed=_brand(discord.Embed(
                    title=label,
                    description=f"{member.mention} has attended **{streak_count} meets in a row**! 🚗💨",
                    color=discord.Color.orange(),
                    timestamp=now,
                )))
            except Exception:
                pass

        await ctx.send(
            f"✅ Streaks updated for **{len(checked_in)}** attendees of `{meet_id}`.",
            delete_after=15,
        )

    @commands.command(name="streak")
    async def streak_cmd(self, ctx: commands.Context, member: discord.Member = None) -> None:
        """Check your (or another member's) attendance streak."""
        target  = member or ctx.author
        uid_str = str(target.id)
        s       = _load(_STREAKS_FILE).get(uid_str, {})
        embed   = _brand(discord.Embed(
            title=f"🔥 Attendance Streak — {target.display_name}",
            description=(
                f"**Current Streak:** {s.get('streak', 0)} meet(s)\n"
                f"**Best Streak:** {s.get('best_streak', 0)} meet(s)"
            ),
            color=discord.Color.orange(),
            timestamp=_est_now(),
        ))
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="Different Meets • Streak Tracker")
        await ctx.send(embed=embed, delete_after=30)

    # ──────────────────────────────────────────────────────────────────────────
    # 4. RSVP waitlist
    # ──────────────────────────────────────────────────────────────────────────

    @commands.command(name="joinwaitlist")
    async def joinwaitlist(self, ctx: commands.Context, meet_id: str) -> None:
        """Add yourself to the waitlist for a meet."""
        await self._del(ctx)
        wl   = _load(_WAITLIST_FILE)
        lst  = wl.setdefault(meet_id, [])
        uid  = str(ctx.author.id)
        if uid in lst:
            return await ctx.send(f"You're already on the waitlist for `{meet_id}`.", delete_after=10)
        lst.append(uid)
        _save(_WAITLIST_FILE, wl)
        pos = lst.index(uid) + 1
        await ctx.send(
            f"✅ Added to waitlist for **{meet_id}** — you're **#{pos}** in line.", delete_after=15
        )

    @commands.command(name="nextwaitlist")
    async def nextwaitlist(self, ctx: commands.Context, meet_id: str) -> None:
        """Notify the next person on the waitlist that a spot opened. Staff only."""
        if not self._staff(ctx):
            return
        await self._del(ctx)
        wl  = _load(_WAITLIST_FILE)
        lst = wl.get(meet_id, [])
        if not lst:
            return await ctx.send(f"Waitlist for `{meet_id}` is empty.", delete_after=10)
        next_uid = lst.pop(0)
        _save(_WAITLIST_FILE, wl)
        member = ctx.guild.get_member(int(next_uid)) if ctx.guild else None
        if not member:
            return await ctx.send(
                f"Next person (`{next_uid}`) is no longer in the server. Run again.", delete_after=10
            )
        try:
            await member.send(embed=_brand(discord.Embed(
                title="🎉 A Spot Opened — DIFF Waitlist",
                description=(
                    f"A spot opened up for **{meet_id}**!\n\n"
                    "Head to the server RSVP panel to claim your spot before it fills again."
                ),
                color=discord.Color.green(),
                timestamp=_est_now(),
            )))
            await ctx.send(
                f"✅ Notified {member.mention}. **{len(lst)}** remaining on waitlist.", delete_after=12
            )
        except discord.Forbidden:
            await ctx.send(
                f"{member.mention} has DMs closed — removed. Run again for the next.", delete_after=12
            )

    @commands.command(name="waitlist")
    async def waitlist_view(self, ctx: commands.Context, meet_id: str) -> None:
        """View the current waitlist for a meet. Staff only."""
        if not self._staff(ctx):
            return
        await self._del(ctx)
        lst = _load(_WAITLIST_FILE).get(meet_id, [])
        if not lst:
            return await ctx.send(f"Waitlist for `{meet_id}` is empty.", delete_after=10)
        lines = [f"{i+1}. <@{uid}>" for i, uid in enumerate(lst)]
        embed = _brand(discord.Embed(
            title=f"📋 Waitlist — {meet_id}",
            description="\n".join(lines),
            color=discord.Color.blurple(),
            timestamp=_est_now(),
        ))
        embed.set_footer(text=f"{len(lst)} in queue")
        await ctx.send(embed=embed, delete_after=30)

    # ──────────────────────────────────────────────────────────────────────────
    # 5. Temp-ban + auto-unban
    # ──────────────────────────────────────────────────────────────────────────

    @commands.command(name="tempban")
    async def tempban(
        self,
        ctx: commands.Context,
        member: discord.Member,
        duration: str,
        *,
        reason: str = "No reason provided",
    ) -> None:
        """!tempban @user <duration> [reason]  — e.g. !tempban @User 24h Spamming"""
        if not self._staff(ctx):
            return
        td = _parse_duration(duration)
        if td is None:
            return await ctx.send(
                "Invalid duration. Use: `30m`, `1h`, `6h`, `24h`, `3d`, `7d`", delete_after=10
            )
        await self._del(ctx)
        now       = _est_now()
        expiry    = now + td
        expiry_ts = int(expiry.timestamp())

        bans = _load(_TEMPBAN_FILE)
        bans[str(member.id)] = {
            "user_id": member.id, "username": str(member),
            "reason": reason, "banned_by": ctx.author.id,
            "expiry_ts": expiry_ts, "guild_id": ctx.guild.id,
        }
        _save(_TEMPBAN_FILE, bans)

        try:
            await member.send(embed=_brand(discord.Embed(
                title="🔨 Temporary Ban — DIFF Meets",
                description=(
                    f"**Reason:** {reason}\n"
                    f"**Duration:** {duration}\n"
                    f"**Unban:** <t:{expiry_ts}:F> ET"
                ),
                color=discord.Color.red(),
                timestamp=now,
            )))
        except Exception:
            pass

        await member.ban(delete_message_days=0, reason=f"[Temp-Ban {duration}] {reason}")
        embed = _brand(discord.Embed(
            title="🔨 Member Temp-Banned",
            description=(
                f"**Member:** {member.mention} (`{member.id}`)\n"
                f"**Duration:** `{duration}`\n"
                f"**Unban:** <t:{expiry_ts}:F>\n"
                f"**Reason:** {reason}\n"
                f"**By:** {ctx.author.mention}"
            ),
            color=discord.Color.red(),
            timestamp=now,
        ))
        embed.set_footer(text="DIFF Temp-Ban System")
        logs_ch = ctx.guild.get_channel(_STAFF_LOGS())
        if isinstance(logs_ch, discord.TextChannel):
            try:
                await logs_ch.send(embed=embed)
            except Exception:
                pass
        await ctx.send(embed=embed, delete_after=30)

    @tasks.loop(minutes=2)
    async def _tempban_check(self) -> None:
        now_ts  = _est_now().timestamp()
        bans    = _load(_TEMPBAN_FILE)
        expired = [uid for uid, b in bans.items() if b.get("expiry_ts", 0) <= now_ts]
        if not expired:
            return
        for uid in expired:
            b     = bans.pop(uid)
            guild = self.bot.get_guild(b.get("guild_id", _GUILD_ID()))
            if not guild:
                continue
            try:
                await guild.unban(discord.Object(id=int(uid)), reason="Temp-ban expired")
                logs_ch = guild.get_channel(_STAFF_LOGS())
                if isinstance(logs_ch, discord.TextChannel):
                    await logs_ch.send(embed=_brand(discord.Embed(
                        title="✅ Temp-Ban Expired — Unbanned",
                        description=(
                            f"**User:** `{b.get('username', uid)}` (`{uid}`)\n"
                            f"**Original reason:** {b.get('reason', 'N/A')}"
                        ),
                        color=discord.Color.green(),
                        timestamp=_est_now(),
                    )))
            except Exception:
                pass
        _save(_TEMPBAN_FILE, bans)

    @_tempban_check.before_loop
    async def _before_tempban(self) -> None:
        await self.bot.wait_until_ready()

    # ──────────────────────────────────────────────────────────────────────────
    # 6. Word + invite filter
    # ──────────────────────────────────────────────────────────────────────────

    @commands.Cog.listener("on_message")
    async def _content_filter(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return
        if not isinstance(message.channel, discord.TextChannel):
            return
        if isinstance(message.author, discord.Member) and _is_staff(message.author):
            return

        low = message.content.lower()

        # Always-on invite filter
        if re.search(r"discord\.gg/\S+|discord\.com/invite/\S+", low):
            try:
                await message.delete()
            except Exception:
                pass
            try:
                await message.channel.send(
                    f"{message.author.mention} Sharing Discord invites is not allowed here.",
                    delete_after=8,
                )
            except Exception:
                pass
            logs_ch = message.guild.get_channel(_STAFF_LOGS())
            if isinstance(logs_ch, discord.TextChannel):
                try:
                    await logs_ch.send(embed=discord.Embed(
                        title="🔗 Invite Link Removed",
                        description=(
                            f"**Author:** {message.author.mention} (`{message.author.id}`)\n"
                            f"**Channel:** {message.channel.mention}\n"
                            f"**Content:** `{message.content[:200]}`"
                        ),
                        color=discord.Color.orange(),
                        timestamp=_est_now(),
                    ))
                except Exception:
                    pass
            return

        # Configurable word filter
        wf       = _load(_WORD_FILTER_FILE)
        words    = wf.get("words", [])
        hit      = [w for w in words if w.lower() in low]
        if not hit:
            return
        try:
            await message.delete()
        except Exception:
            pass
        try:
            await message.channel.send(
                f"{message.author.mention} Your message was removed for restricted content.",
                delete_after=8,
            )
        except Exception:
            pass
        logs_ch = message.guild.get_channel(_STAFF_LOGS())
        if isinstance(logs_ch, discord.TextChannel):
            try:
                await logs_ch.send(embed=discord.Embed(
                    title="🚫 Word Filter Triggered",
                    description=(
                        f"**Author:** {message.author.mention} (`{message.author.id}`)\n"
                        f"**Channel:** {message.channel.mention}\n"
                        f"**Triggered:** `{', '.join(hit)}`\n"
                        f"**Content:** `{message.content[:300]}`"
                    ),
                    color=discord.Color.red(),
                    timestamp=_est_now(),
                ))
            except Exception:
                pass

    @commands.group(name="filter", invoke_without_command=True)
    async def filter_group(self, ctx: commands.Context) -> None:
        await ctx.send(
            "Usage: `!filter add <word>` · `!filter remove <word>` · `!filter list`",
            delete_after=15,
        )

    @filter_group.command(name="add")
    async def filter_add(self, ctx: commands.Context, *, word: str) -> None:
        if not self._staff(ctx):
            return
        wf = _load(_WORD_FILTER_FILE)
        w  = word.strip().lower()
        if w in wf.setdefault("words", []):
            return await ctx.send(f"`{w}` is already filtered.", delete_after=8)
        wf["words"].append(w)
        _save(_WORD_FILTER_FILE, wf)
        await self._del(ctx)
        await ctx.send(f"✅ `{w}` added to word filter.", delete_after=8)

    @filter_group.command(name="remove")
    async def filter_remove(self, ctx: commands.Context, *, word: str) -> None:
        if not self._staff(ctx):
            return
        wf = _load(_WORD_FILTER_FILE)
        w  = word.strip().lower()
        if w not in wf.get("words", []):
            return await ctx.send(f"`{w}` not in filter.", delete_after=8)
        wf["words"].remove(w)
        _save(_WORD_FILTER_FILE, wf)
        await self._del(ctx)
        await ctx.send(f"🗑️ `{w}` removed from word filter.", delete_after=8)

    @filter_group.command(name="list")
    async def filter_list(self, ctx: commands.Context) -> None:
        if not self._staff(ctx):
            return
        await self._del(ctx)
        words = _load(_WORD_FILTER_FILE).get("words", [])
        if not words:
            return await ctx.send("Word filter is empty. Use `!filter add <word>`.", delete_after=12)
        embed = _brand(discord.Embed(
            title="🚫 Filtered Words",
            description="\n".join(f"• `{w}`" for w in words),
            color=discord.Color.red(),
            timestamp=_est_now(),
        ))
        embed.set_footer(text=f"{len(words)} words filtered")
        await ctx.send(embed=embed, delete_after=30)

    # ──────────────────────────────────────────────────────────────────────────
    # 7. Member lookup
    # ──────────────────────────────────────────────────────────────────────────

    @commands.command(name="lookup")
    async def lookup(self, ctx: commands.Context, member: discord.Member) -> None:
        """Pull a full profile on any member. Staff only."""
        if not self._staff(ctx):
            return
        await self._del(ctx)

        uid     = str(member.id)
        now     = _est_now()
        act     = _load(_ACTIVITY_FILE()).get(uid, {})
        rep_r   = _load(_REP_FILE()).get(uid, {})
        rep     = rep_r.get("reputation", 0) if isinstance(rep_r, dict) else 0
        streaks = _load(_STREAKS_FILE).get(uid, {})

        # Warnings from main bot data
        _mm       = _main()
        warn_list = []
        if _mm:
            warn_list = getattr(_mm, "data", {}).get("warnings", {}).get(uid, [])

        # Appeal denials
        _adf = getattr(_mm, "_appeal_denial_load", None) if _mm else None
        appeal_denials = len((_adf() if _adf else {}).get(uid, {}))

        # Open tickets
        open_tickets = sum(
            1 for ch in (ctx.guild.text_channels if ctx.guild else [])
            if f"ticket_owner={member.id}" in (ch.topic or "") and "ticket_type=" in (ch.topic or "")
        )

        # Account info
        created_ts = int(member.created_at.timestamp())
        joined_ts  = int(member.joined_at.timestamp()) if member.joined_at else 0
        roles_str  = ", ".join(r.name for r in member.roles[1:7]) or "None"

        embed = discord.Embed(
            title=f"🔍 Member Lookup — {member.display_name}",
            color=discord.Color.blurple(),
            timestamp=now,
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="👤 Username",        value=str(member),                                  inline=True)
        embed.add_field(name="🆔 User ID",         value=f"`{member.id}`",                              inline=True)
        embed.add_field(name="📅 Account Created", value=f"<t:{created_ts}:D>",                         inline=True)
        embed.add_field(name="📥 Joined Server",   value=f"<t:{joined_ts}:D>" if joined_ts else "N/A",  inline=True)
        embed.add_field(name="⚠️ Warnings",        value=str(len(warn_list)),                           inline=True)
        embed.add_field(name="⭐ Reputation",      value=str(rep),                                      inline=True)
        embed.add_field(name="🚗 Meets Attended",  value=str(act.get("meets_attended", 0)),             inline=True)
        embed.add_field(name="🎮 Meets Hosted",    value=str(act.get("meets_hosted", 0)),               inline=True)
        embed.add_field(name="🔥 Current Streak",  value=f"{streaks.get('streak', 0)} meet(s)",         inline=True)
        embed.add_field(name="🏆 Best Streak",     value=f"{streaks.get('best_streak', 0)} meet(s)",    inline=True)
        embed.add_field(name="🎟️ Open Tickets",    value=str(open_tickets),                             inline=True)
        embed.add_field(name="⚖️ Appeal Denials",  value=str(appeal_denials),                           inline=True)
        embed.add_field(name="🏷️ Top Roles",       value=roles_str,                                     inline=False)

        # Bio (from diff_advanced_features data)
        bio_txt = _load(os.path.join("diff_data", "diff_bios.json")).get(uid, "")
        if bio_txt:
            embed.add_field(name="📝 Bio", value=bio_txt[:200], inline=False)

        # Achievements
        ach_db  = _load(os.path.join("diff_data", "diff_achievements.json"))
        earned  = ach_db.get(uid, [])
        _ACH_DEF = {
            "first_meet":  ("🚗", "First Wheel"),  "ten_meets":   ("🎯", "10 Meets Club"),
            "twenty_five": ("🏅", "Road Veteran"),  "fifty_meets": ("🏆", "Legend"),
            "first_host":  ("🎮", "First Time Host"), "five_host": ("⭐", "Experienced Host"),
            "ten_host":    ("👑", "Master Host"),
        }
        if earned:
            badge_str = "  ".join(f"{_ACH_DEF[k][0]}{_ACH_DEF[k][1]}" for k in earned if k in _ACH_DEF)
            embed.add_field(name="🏅 Achievements", value=badge_str or "None", inline=False)

        # XP / Level
        xp_entry = _load(os.path.join("diff_data", "diff_xp.json")).get(uid, {})
        if xp_entry:
            import math as _math
            xp_val  = xp_entry.get("xp", 0)
            xp_lvl  = max(1, int(_math.sqrt(max(xp_val, 0) / 50)))
            embed.add_field(name="⭐ XP / Level", value=f"{xp_val:,} XP · Level {xp_lvl}", inline=True)

        if warn_list:
            lw = warn_list[-1]
            embed.add_field(
                name="📋 Last Warning",
                value=f"*{lw.get('reason', 'N/A')}* — by <@{lw.get('moderator_id', '?')}>",
                inline=False,
            )
        embed.set_footer(
            text=f"Looked up by {ctx.author.display_name} • {now.strftime('%I:%M %p ET')}"
        )
        await ctx.send(embed=embed, delete_after=120)

    # ──────────────────────────────────────────────────────────────────────────
    # 8. Giveaway system
    # ──────────────────────────────────────────────────────────────────────────

    @commands.command(name="giveaway")
    async def giveaway(self, ctx: commands.Context, duration: str, *, prize: str) -> None:
        """!giveaway <duration> <prize> [min_meets:<N>]"""
        if not self._staff(ctx):
            return
        await self._del(ctx)

        mm = re.search(r"min_meets:(\d+)", prize)
        min_meets = int(mm.group(1)) if mm else 0
        if mm:
            prize = prize.replace(mm.group(0), "").strip()

        td = _parse_duration(duration)
        if td is None:
            return await ctx.send("Invalid duration. Use: `30m`, `1h`, `6h`, `24h`, `3d`", delete_after=10)

        now       = _est_now()
        expiry    = now + td
        expiry_ts = int(expiry.timestamp())
        gw_id     = f"{ctx.guild.id}_{expiry_ts}"

        gw_data = _load(_GIVEAWAY_FILE)
        gw_data[gw_id] = {
            "channel_id": ctx.channel.id, "guild_id": ctx.guild.id,
            "host_id": ctx.author.id, "prize": prize,
            "min_meets": min_meets, "expiry_ts": expiry_ts,
            "entrants": [], "ended": False, "message_id": None,
        }

        req = f"\n🎯 **Requirement:** {min_meets}+ meets attended" if min_meets else ""
        embed = _brand(discord.Embed(
            title="🎉 GIVEAWAY!",
            description=(
                f"**Prize:** {prize}{req}\n\n"
                f"Press the button to enter!\n\n"
                f"⏰ **Ends:** <t:{expiry_ts}:R> (<t:{expiry_ts}:F>)"
            ),
            color=discord.Color.gold(),
            timestamp=now,
        ))
        embed.set_footer(text=f"Hosted by {ctx.author.display_name} • Different Meets")
        msg = await ctx.send(embed=embed, view=_GiveawayView(gw_id, min_meets))
        gw_data[gw_id]["message_id"] = msg.id
        _save(_GIVEAWAY_FILE, gw_data)

    @tasks.loop(minutes=1)
    async def _giveaway_check(self) -> None:
        now_ts  = int(_est_now().timestamp())
        gw_data = _load(_GIVEAWAY_FILE)
        changed = False
        for gw_id, gw in gw_data.items():
            if gw.get("ended") or gw.get("expiry_ts", 0) > now_ts:
                continue
            gw["ended"] = True
            changed     = True
            guild   = self.bot.get_guild(gw.get("guild_id", _GUILD_ID()))
            channel = guild.get_channel(gw["channel_id"]) if guild else None
            now     = _est_now()

            entrants = gw.get("entrants", [])
            if not entrants:
                if isinstance(channel, discord.TextChannel):
                    try:
                        await channel.send(embed=discord.Embed(
                            title="🎉 Giveaway Ended — No Entries",
                            description=f"No one entered the **{gw['prize']}** giveaway.",
                            color=discord.Color.red(), timestamp=now,
                        ))
                    except Exception:
                        pass
                continue

            winner_id  = random.choice(entrants)
            winner     = guild.get_member(int(winner_id)) if guild else None
            winner_str = winner.mention if winner else f"<@{winner_id}>"

            embed = _brand(discord.Embed(
                title="🎉 Giveaway Winner!",
                description=(
                    f"🏆 {winner_str} won **{gw['prize']}**!\n\n"
                    f"Contact <@{gw['host_id']}> to claim your prize.\n"
                    f"👥 {len(entrants)} total entries."
                ),
                color=discord.Color.gold(), timestamp=now,
            ))
            embed.set_footer(text="Different Meets • Giveaway")
            if isinstance(channel, discord.TextChannel):
                try:
                    await channel.send(content=winner_str, embed=embed)
                except Exception:
                    pass
            if winner:
                try:
                    await winner.send(embed=_brand(discord.Embed(
                        title="🎉 You Won a DIFF Giveaway!",
                        description=f"You won **{gw['prize']}**! Contact <@{gw['host_id']}> to claim it.",
                        color=discord.Color.gold(), timestamp=now,
                    )))
                except Exception:
                    pass
        if changed:
            _save(_GIVEAWAY_FILE, gw_data)

    @_giveaway_check.before_loop
    async def _before_giveaway(self) -> None:
        await self.bot.wait_until_ready()

    # ──────────────────────────────────────────────────────────────────────────
    # 10. Suggestion box
    # ──────────────────────────────────────────────────────────────────────────

    @commands.cooldown(1, 600, commands.BucketType.user)
    @commands.command(name="suggest")
    async def suggest(self, ctx: commands.Context, *, suggestion: str = "") -> None:
        """Submit a suggestion to DIFF leadership."""
        await self._del(ctx)
        if not suggestion:
            return await ctx.send(
                "Usage: `!suggest <your idea here>`", delete_after=10
            )
        now    = _est_now()
        sug_id = str(int(now.timestamp()))
        sug_db = _load(_SUGGESTIONS_FILE)
        sug_db[sug_id] = {
            "user_id": ctx.author.id, "text": suggestion,
            "created_at": now.isoformat(), "status": "pending",
        }
        _save(_SUGGESTIONS_FILE, sug_db)

        if ctx.guild:
            mod_hub = ctx.guild.get_channel(_MOD_HUB())
            if isinstance(mod_hub, discord.TextChannel):
                embed = _brand(discord.Embed(
                    title="💡 New Suggestion",
                    description=suggestion,
                    color=discord.Color.yellow(),
                    timestamp=now,
                ))
                embed.set_author(
                    name=ctx.author.display_name,
                    icon_url=ctx.author.display_avatar.url,
                )
                embed.add_field(
                    name="Member", value=f"{ctx.author.mention} (`{ctx.author.id}`)", inline=True
                )
                embed.set_footer(text="React ✅ Planned  ❌ Denied  🤔 Under Review")
                try:
                    msg = await mod_hub.send(embed=embed)
                    for emoji in ["✅", "❌", "🤔"]:
                        await msg.add_reaction(emoji)
                    sug_db[sug_id]["message_id"] = msg.id
                    _save(_SUGGESTIONS_FILE, sug_db)
                except Exception:
                    pass

        try:
            await ctx.author.send(embed=_brand(discord.Embed(
                title="✅ Suggestion Submitted",
                description=(
                    f"Your suggestion has been sent to DIFF leadership for review!\n\n"
                    f"> {suggestion[:200]}"
                ),
                color=discord.Color.green(),
                timestamp=now,
            )))
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────────────────────
    # 11. Staff on-duty toggle
    # ──────────────────────────────────────────────────────────────────────────

    async def _refresh_onduty_embed(self, guild: discord.Guild) -> None:
        od   = _load(_ONDUTY_FILE)
        duty = od.get("on_duty", {})
        now  = _est_now()
        lines = [
            f"✅ <@{uid}> — on since <t:{info.get('since_ts', 0)}:R>"
            for uid, info in duty.items()
        ]
        embed = _brand(discord.Embed(
            title="🛡️ DIFF Staff On Duty",
            description="\n".join(lines) if lines else "*No staff currently on duty.*",
            color=discord.Color.green() if lines else discord.Color.greyple(),
            timestamp=now,
        ))
        embed.set_footer(
            text=f"Updated {now.strftime('%I:%M %p ET')} • Use !onduty / !offduty to toggle"
        )
        mod_hub = guild.get_channel(_MOD_HUB())
        if not isinstance(mod_hub, discord.TextChannel):
            return
        msg_id = od.get("embed_message_id")
        if msg_id:
            try:
                msg = await mod_hub.fetch_message(int(msg_id))
                await msg.edit(embed=embed)
                return
            except Exception:
                pass
        msg = await mod_hub.send(embed=embed)
        od["embed_message_id"] = msg.id
        _save(_ONDUTY_FILE, od)

    @commands.command(name="onduty")
    async def onduty(self, ctx: commands.Context) -> None:
        """Mark yourself as on duty in mod-hub."""
        if not isinstance(ctx.author, discord.Member) or not _is_staff(ctx.author):
            return
        await self._del(ctx)
        od   = _load(_ONDUTY_FILE)
        duty = od.setdefault("on_duty", {})
        uid  = str(ctx.author.id)
        if uid in duty:
            return await ctx.send("You're already on duty!", delete_after=8)
        duty[uid] = {"since_ts": int(_est_now().timestamp()), "username": str(ctx.author)}
        _save(_ONDUTY_FILE, od)
        await ctx.send(f"✅ {ctx.author.mention} is now **on duty**.", delete_after=10)
        if ctx.guild:
            await self._refresh_onduty_embed(ctx.guild)

    @commands.command(name="offduty")
    async def offduty(self, ctx: commands.Context) -> None:
        """Mark yourself as off duty."""
        if not isinstance(ctx.author, discord.Member) or not _is_staff(ctx.author):
            return
        await self._del(ctx)
        od   = _load(_ONDUTY_FILE)
        duty = od.get("on_duty", {})
        uid  = str(ctx.author.id)
        if uid not in duty:
            return await ctx.send("You're not currently on duty.", delete_after=8)
        del duty[uid]
        _save(_ONDUTY_FILE, od)
        await ctx.send(f"👋 {ctx.author.mention} is now **off duty**.", delete_after=10)
        if ctx.guild:
            await self._refresh_onduty_embed(ctx.guild)

    @commands.command(name="whosonduty")
    async def whosonduty(self, ctx: commands.Context) -> None:
        """See who's currently on duty."""
        duty = _load(_ONDUTY_FILE).get("on_duty", {})
        now  = _est_now()
        if not duty:
            return await ctx.send("No staff are currently on duty.", delete_after=12)
        lines = [
            f"✅ <@{uid}> — since <t:{info.get('since_ts', 0)}:R>"
            for uid, info in duty.items()
        ]
        embed = _brand(discord.Embed(
            title="🛡️ Staff Currently On Duty",
            description="\n".join(lines),
            color=discord.Color.green(),
            timestamp=now,
        ))
        embed.set_footer(text=f"Different Meets • {now.strftime('%I:%M %p ET')}")
        await ctx.send(embed=embed, delete_after=30)

    # ──────────────────────────────────────────────────────────────────────────
    # 9 & 12. Monthly recap + application report (1st of month, 10 AM ET)
    # ──────────────────────────────────────────────────────────────────────────

    @tasks.loop(hours=24)
    async def _monthly_tasks(self) -> None:
        now = _est_now()
        if now.day != 1 or now.hour < 10:
            return
        state_key = now.strftime("%Y-%m")
        state     = _load(_MONTHLY_STATE_FILE)
        if state.get("last_monthly") == state_key:
            return
        state["last_monthly"] = state_key
        _save(_MONTHLY_STATE_FILE, state)

        guild   = self.bot.get_guild(_GUILD_ID())
        mod_hub = guild.get_channel(_MOD_HUB()) if guild else None
        if not guild or not isinstance(mod_hub, discord.TextChannel):
            return

        # Previous month bounds
        prev_1st  = (now.replace(day=1) - timedelta(days=1)).replace(day=1)
        prev_lbl  = prev_1st.strftime("%B %Y")
        month_pfx = prev_1st.strftime("%Y-%m")
        m_start   = prev_1st.replace(tzinfo=_EST_TZ)
        m_end     = now.replace(day=1, tzinfo=_EST_TZ)

        activity  = _load(_ACTIVITY_FILE())
        meets_raw = _load(_MEETS_FILE())

        # Meets held in previous month
        month_meets = sum(
            1 for rec in meets_raw.values()
            if (rec.get("created_at") or "").startswith(month_pfx)
        )

        # New members in previous month
        new_members = sum(
            1 for m in guild.members
            if m.joined_at and m_start <= m.joined_at.astimezone(_EST_TZ) < m_end and not m.bot
        )

        # Top 3 attendees + hosts
        medals = ["🥇", "🥈", "🥉"]
        top_att = sorted(
            [(u, s.get("meets_attended", 0)) for u, s in activity.items()],
            key=lambda x: x[1], reverse=True,
        )[:3]
        top_host = sorted(
            [(u, s.get("meets_hosted", 0)) for u, s in activity.items()],
            key=lambda x: x[1], reverse=True,
        )[:3]

        att_lines  = [f"{medals[i]} <@{u}> — {c} meets" for i, (u, c) in enumerate(top_att) if c > 0]
        host_lines = [f"{medals[i]} <@{u}> — {c} hosted" for i, (u, c) in enumerate(top_host) if c > 0]

        recap = _brand(discord.Embed(
            title=f"📅 Monthly Recap — {prev_lbl}",
            color=discord.Color.blurple(),
            timestamp=now,
        ))
        recap.add_field(name="🚗 Meets Held",    value=str(month_meets),           inline=True)
        recap.add_field(name="👋 New Members",   value=str(new_members),            inline=True)
        recap.add_field(name="👥 Total Members", value=str(guild.member_count or 0), inline=True)
        recap.add_field(name="🏆 Top Attendees", value="\n".join(att_lines) or "*No data*",  inline=False)
        recap.add_field(name="🎮 Top Hosts",     value="\n".join(host_lines) or "*No data*", inline=False)
        recap.set_footer(text=f"Different Meets • Monthly Recap • {now.strftime('%I:%M %p ET')}")
        try:
            await mod_hub.send(embed=recap)
        except Exception:
            pass

        # Application report from applications file
        try:
            apps_raw = _load(_APPS_FILE())
            if apps_raw:
                month_apps = [
                    a for a in apps_raw.values()
                    if (a.get("created_at") or a.get("submitted_at") or "").startswith(month_pfx)
                ]
                accepted = sum(1 for a in month_apps if a.get("status") == "Approved")
                denied   = sum(1 for a in month_apps if a.get("status") == "Denied")
                pending  = sum(1 for a in month_apps if a.get("status") not in {"Approved", "Denied"})
                rate_str = f"{accepted / len(month_apps) * 100:.0f}%" if month_apps else "N/A"

                app_embed = _brand(discord.Embed(
                    title=f"📝 Application Report — {prev_lbl}",
                    color=discord.Color.orange(),
                    timestamp=now,
                ))
                app_embed.add_field(name="📥 Total Received", value=str(len(month_apps)), inline=True)
                app_embed.add_field(name="✅ Accepted",        value=str(accepted),         inline=True)
                app_embed.add_field(name="❌ Denied",          value=str(denied),            inline=True)
                app_embed.add_field(name="⏳ Pending",         value=str(pending),           inline=True)
                app_embed.add_field(name="📊 Accept Rate",     value=rate_str,               inline=True)
                app_embed.set_footer(
                    text=f"Different Meets • App Report • {now.strftime('%I:%M %p ET')}"
                )
                await mod_hub.send(embed=app_embed)
        except Exception:
            pass

    @_monthly_tasks.before_loop
    async def _before_monthly(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DiffCommunityFeatures(bot))
