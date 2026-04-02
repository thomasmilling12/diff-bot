"""
cogs/diff_advanced_features.py
────────────────────────────────
15 advanced community + staff features for DIFF Meets.

 1.  Meet schedule/calendar   (!schedulemeet, !schedule, !cancelmeet + RSVP button)
 2.  RSVP 30-min reminder     (background task — DMs RSVPd members before meet)
 3.  Post-meet recap          (!meetrecap)
 4.  Birthday system          (!setbirthday — daily announcement task)
 5.  Member bio               (!setbio, !bio)
 6.  Achievements / badges    (!awardachievements, !achievements)
 7.  XP / level system        (!xp, !levels — message XP + meet XP)
 8.  Channel lock/unlock      (!lock, !unlock)
 9.  Anti-spam auto-timeout   (on_message — 5 msgs / 4s → 10-min timeout)
10.  Auto-dehoist             (on_member_join + on_member_update, toggleable)
11.  Ticket transcript        (!transcript — fetches channel history → .txt)
12.  Staff roster             (!stafflist)
13.  Scheduled announcements  (!scheduleannounce, !myannouncements)
14.  Bulk role DM             (!roledm — button confirmation)
15.  Auto-updating stats      (!setstats — hourly embed refresh)

Config:  diff_data/diff_adv_config.json
  {
    "schedule_channel_id": null,
    "birthday_channel_id": null,
    "stats_channel_id":    null,
    "stats_message_id":    null,
    "dehoist_enabled":     false
  }
"""

from __future__ import annotations

import asyncio
import io
import json
import math
import os
import re
import sys
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks

_EST_TZ = ZoneInfo("America/New_York")


def _est_now() -> datetime:
    return datetime.now(_EST_TZ)


# ── Main-bot globals ──────────────────────────────────────────────────────────
def _main():
    return sys.modules.get("__main__")


def _get(name, default=None):
    m = _main()
    return getattr(m, name, default) if m else default


def _GUILD_ID()    -> int: return _get("GUILD_ID",              0)
def _MOD_HUB()     -> int: return _get("MOD_HUB_CHANNEL_ID",   0)
def _STAFF_LOGS()  -> int: return _get("STAFF_LOGS_CHANNEL_ID", 0)
def _LOGO()        -> str: return _get("DIFF_LOGO_URL",         "")
def _LEADER()      -> int: return _get("LEADER_ROLE_ID",        0)
def _CO_LEADER()   -> int: return _get("CO_LEADER_ROLE_ID",     0)
def _MANAGER()     -> int: return _get("MANAGER_ROLE_ID",       0)
def _HOST()        -> int: return _get("HOST_ROLE_ID",          0)
def _VERIFIED()    -> int: return _get("VERIFIED_ROLE_ID",      0)
def _CREW()        -> int: return _get("CREW_MEMBER_ROLE_ID",   0)
def _ACT_FILE()    -> str: return _get("ACTIVITY_FILE",         "diff_data/diff_activity_stats.json")
def _MEETS_FILE()  -> str: return _get("MEETS_FILE",            "diff_data/diff_meet_records.json")
def _FEEDBACK_FILE() -> str: return os.path.join("diff_data", "diff_feedback.json")

_DATA              = "diff_data"
_SCHEDULE_FILE     = os.path.join(_DATA, "diff_schedule.json")
_BIRTHDAYS_FILE    = os.path.join(_DATA, "diff_birthdays.json")
_BIOS_FILE         = os.path.join(_DATA, "diff_bios.json")
_ACHIEVEMENTS_FILE = os.path.join(_DATA, "diff_achievements.json")
_XP_FILE           = os.path.join(_DATA, "diff_xp.json")
_ADV_CONFIG_FILE   = os.path.join(_DATA, "diff_adv_config.json")
_SCHED_ANN_FILE    = os.path.join(_DATA, "diff_sched_announcements.json")

# ── Achievement definitions ───────────────────────────────────────────────────
_ACHIEVEMENTS = {
    "first_meet":   {"name": "First Wheel",      "emoji": "🚗", "desc": "Attended your first DIFF meet"},
    "ten_meets":    {"name": "10 Meets Club",     "emoji": "🎯", "desc": "Attended 10 meets"},
    "twenty_five":  {"name": "Road Veteran",      "emoji": "🏅", "desc": "Attended 25 meets"},
    "fifty_meets":  {"name": "Legend",            "emoji": "🏆", "desc": "Attended 50 meets"},
    "first_host":   {"name": "First Time Host",   "emoji": "🎮", "desc": "Hosted your first meet"},
    "five_host":    {"name": "Experienced Host",  "emoji": "⭐", "desc": "Hosted 5 meets"},
    "ten_host":     {"name": "Master Host",       "emoji": "👑", "desc": "Hosted 10 meets"},
}
_ATT_THRESHOLDS  = [(50, "fifty_meets"), (25, "twenty_five"), (10, "ten_meets"), (1, "first_meet")]
_HOST_THRESHOLDS = [(10, "ten_host"), (5, "five_host"), (1, "first_host")]

# ── XP helpers ────────────────────────────────────────────────────────────────
def _level_for_xp(xp: int) -> int:
    return max(1, int(math.sqrt(max(xp, 0) / 50)))


def _xp_for_level(lvl: int) -> int:
    return lvl * lvl * 50


def _xp_bar(xp: int, level: int) -> str:
    base   = _xp_for_level(level)
    nxt    = _xp_for_level(level + 1)
    total  = max(nxt - base, 1)
    filled = int(10 * max(xp - base, 0) / total)
    filled = min(filled, 10)
    return "█" * filled + "░" * (10 - filled)


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


def _cfg() -> dict:
    return _load(_ADV_CONFIG_FILE)


def _cfg_set(**kw) -> None:
    c = _cfg()
    c.update(kw)
    _save(_ADV_CONFIG_FILE, c)


# ── Misc helpers ──────────────────────────────────────────────────────────────
def _brand(embed: discord.Embed) -> discord.Embed:
    if _LOGO():
        embed.set_thumbnail(url=_LOGO())
    return embed


def _is_staff(member: discord.Member) -> bool:
    return any(r.id in {_LEADER(), _CO_LEADER(), _MANAGER(), _HOST()} for r in member.roles)


_SYMBOL_RE = re.compile(r"^[^A-Za-z0-9]")


# ══════════════════════════════════════════════════════════════════════════════
# Pi-compatible button subclasses
# ══════════════════════════════════════════════════════════════════════════════

class _RsvpToggleButton(discord.ui.Button):
    def __init__(self, meet_id: str) -> None:
        super().__init__(
            label="✅ RSVP for this Meet",
            style=discord.ButtonStyle.success,
            custom_id=f"diff_sched_rsvp_{meet_id}",
        )
        self.meet_id = meet_id

    async def callback(self, interaction: discord.Interaction) -> None:
        sched = _load(_SCHEDULE_FILE)
        meet  = sched.get(self.meet_id)
        if not meet:
            return await interaction.response.send_message("Meet not found.", ephemeral=True)
        if meet.get("cancelled"):
            return await interaction.response.send_message("This meet has been cancelled.", ephemeral=True)
        uid   = str(interaction.user.id)
        rsvps = meet.setdefault("rsvps", [])
        if uid in rsvps:
            rsvps.remove(uid)
            _save(_SCHEDULE_FILE, sched)
            await interaction.response.send_message("❌ RSVP removed.", ephemeral=True)
        else:
            rsvps.append(uid)
            _save(_SCHEDULE_FILE, sched)
            await interaction.response.send_message(
                "✅ RSVP confirmed! You'll get a DM reminder 30 minutes before the meet starts.",
                ephemeral=True,
            )


class _RsvpView(discord.ui.View):
    def __init__(self, meet_id: str) -> None:
        super().__init__(timeout=None)
        self.add_item(_RsvpToggleButton(meet_id))


class _RoleDmConfirmButton(discord.ui.Button):
    def __init__(self, dm_id: str, role_id: int, msg_text: str) -> None:
        super().__init__(
            label="✅ Confirm — Send DMs Now",
            style=discord.ButtonStyle.danger,
            custom_id=f"diff_roledm_{dm_id}",
        )
        self.dm_id    = dm_id
        self.role_id  = role_id
        self.msg_text = msg_text

    async def callback(self, interaction: discord.Interaction) -> None:
        if not isinstance(interaction.user, discord.Member) or not _is_staff(interaction.user):
            return await interaction.response.send_message("Staff only.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        role = interaction.guild.get_role(self.role_id) if interaction.guild else None
        if not role:
            return await interaction.followup.send("Role not found.", ephemeral=True)
        sent = failed = 0
        for member in role.members:
            if member.bot:
                continue
            try:
                await member.send(self.msg_text)
                sent += 1
                await asyncio.sleep(0.6)
            except Exception:
                failed += 1
        await interaction.followup.send(
            f"✅ Done — **{sent}** DMs delivered, **{failed}** failed (DMs closed).",
            ephemeral=True,
        )
        self.disabled = True
        try:
            await interaction.message.edit(view=self.view)
        except Exception:
            pass


class _RoleDmView(discord.ui.View):
    def __init__(self, dm_id: str, role_id: int, msg_text: str) -> None:
        super().__init__(timeout=300)
        self.add_item(_RoleDmConfirmButton(dm_id, role_id, msg_text))


# ══════════════════════════════════════════════════════════════════════════════
# Cog
# ══════════════════════════════════════════════════════════════════════════════

class DiffAdvancedFeatures(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._spam_tracker: dict[int, list[float]] = {}
        self._xp_cd:        dict[int, float]       = {}
        self._reminded:     set[str]               = set()
        self._reminded_1h:  set[str]               = set()
        self._birthday_check.start()
        self._reminder_check.start()
        self._sched_ann_check.start()
        self._stats_update.start()
        self._daily_backup.start()

    def cog_unload(self) -> None:
        self._birthday_check.cancel()
        self._reminder_check.cancel()
        self._sched_ann_check.cancel()
        self._stats_update.cancel()
        self._daily_backup.cancel()

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
    # 1 & 2. Meet schedule/calendar + 30-min RSVP reminder
    # ──────────────────────────────────────────────────────────────────────────

    @commands.command(name="schedulemeet")
    async def schedulemeet(
        self, ctx: commands.Context, date: str, time_: str, *, description: str
    ) -> None:
        """!schedulemeet YYYY-MM-DD HH:MM <description>  (time is ET)"""
        if not self._staff(ctx):
            return
        await self._del(ctx)
        try:
            dt     = datetime.strptime(f"{date} {time_}", "%Y-%m-%d %H:%M").replace(tzinfo=_EST_TZ)
            dt_ts  = int(dt.timestamp())
        except ValueError:
            return await ctx.send(
                "Date/time format: `YYYY-MM-DD HH:MM` e.g. `2026-04-12 20:00`", delete_after=12
            )

        now     = _est_now()
        meet_id = f"sched_{int(now.timestamp())}"
        sched   = _load(_SCHEDULE_FILE)
        sched[meet_id] = {
            "description": description,
            "host_id":     ctx.author.id,
            "dt_ts":       dt_ts,
            "rsvps":       [],
            "cancelled":   False,
            "created_at":  now.isoformat(),
        }
        _save(_SCHEDULE_FILE, sched)

        cfg   = _cfg()
        sch_ch = ctx.guild.get_channel(cfg.get("schedule_channel_id") or 0) if ctx.guild else None
        target = sch_ch if isinstance(sch_ch, discord.TextChannel) else ctx.channel

        embed = _brand(discord.Embed(
            title="📅 Upcoming DIFF Meet",
            description=(
                f"**{description}**\n\n"
                f"🗓️ **Date/Time:** <t:{dt_ts}:F>\n"
                f"⏰ **Countdown:** <t:{dt_ts}:R>\n\n"
                f"Click the button to RSVP — you'll get a reminder 30 minutes before!"
            ),
            color=discord.Color.green(),
            timestamp=now,
        ))
        embed.set_footer(text=f"Posted by {ctx.author.display_name} • Meet ID: {meet_id}")
        msg = await target.send(embed=embed, view=_RsvpView(meet_id))
        sched[meet_id]["message_id"]  = msg.id
        sched[meet_id]["channel_id"]  = target.id
        _save(_SCHEDULE_FILE, sched)
        if target != ctx.channel:
            await ctx.send(f"✅ Meet posted in {target.mention}.", delete_after=8)

    @commands.command(name="cancelmeet")
    async def cancelmeet(self, ctx: commands.Context, meet_id: str) -> None:
        """Cancel a scheduled meet and notify RSVPd members."""
        if not self._staff(ctx):
            return
        await self._del(ctx)
        sched = _load(_SCHEDULE_FILE)
        meet  = sched.get(meet_id)
        if not meet:
            return await ctx.send(f"Meet `{meet_id}` not found.", delete_after=10)
        meet["cancelled"] = True
        _save(_SCHEDULE_FILE, sched)
        now = _est_now()
        for uid in meet.get("rsvps", []):
            member = ctx.guild.get_member(int(uid)) if ctx.guild else None
            if member:
                try:
                    await member.send(embed=discord.Embed(
                        title="❌ DIFF Meet Cancelled",
                        description=f"**{meet['description']}** has been cancelled by staff. Sorry for the inconvenience!",
                        color=discord.Color.red(),
                        timestamp=now,
                    ))
                except Exception:
                    pass
        await ctx.send(
            f"✅ Meet `{meet_id}` cancelled. **{len(meet.get('rsvps', []))}** member(s) notified.", delete_after=12
        )

    @commands.command(name="schedule")
    async def schedule_view(self, ctx: commands.Context) -> None:
        """Show all upcoming scheduled meets."""
        sched = _load(_SCHEDULE_FILE)
        now   = _est_now()
        now_ts = int(now.timestamp())
        upcoming = [
            (mid, m) for mid, m in sched.items()
            if not m.get("cancelled") and m.get("dt_ts", 0) > now_ts
        ]
        upcoming.sort(key=lambda x: x[1]["dt_ts"])
        if not upcoming:
            return await ctx.send("No upcoming meets scheduled.", delete_after=12)
        embed = _brand(discord.Embed(
            title="📅 Upcoming DIFF Meets",
            color=discord.Color.green(),
            timestamp=now,
        ))
        for mid, m in upcoming[:10]:
            rsvp_count = len(m.get("rsvps", []))
            embed.add_field(
                name=f"{m['description']}",
                value=f"<t:{m['dt_ts']}:F> · {rsvp_count} RSVPd · ID: `{mid}`",
                inline=False,
            )
        embed.set_footer(text="Different Meets • Schedule")
        await ctx.send(embed=embed, delete_after=60)

    @tasks.loop(minutes=1)
    async def _reminder_check(self) -> None:
        now_ts = int(_est_now().timestamp())
        sched  = _load(_SCHEDULE_FILE)
        guild  = self.bot.get_guild(_GUILD_ID())
        for mid, m in sched.items():
            if m.get("cancelled"):
                continue
            dt_ts = m.get("dt_ts", 0)
            diff  = dt_ts - now_ts

            # ── 1-hour reminder ──────────────────────────────────────────
            if mid not in self._reminded_1h and 3540 <= diff <= 3660:
                self._reminded_1h.add(mid)
                for uid in m.get("rsvps", []):
                    member = guild.get_member(int(uid)) if guild else None
                    if member:
                        try:
                            await member.send(embed=_brand(discord.Embed(
                                title="🔔 Meet Starting in 1 Hour!",
                                description=(
                                    f"**{m['description']}** is starting <t:{dt_ts}:R>.\n\n"
                                    "Start getting your car ready — see you there! 🚗"
                                ),
                                color=discord.Color.blurple(),
                                timestamp=_est_now(),
                            )))
                        except Exception:
                            pass

            # ── 30-minute reminder ────────────────────────────────────────
            if mid not in self._reminded and 1740 <= diff <= 1860:
                self._reminded.add(mid)
                for uid in m.get("rsvps", []):
                    member = guild.get_member(int(uid)) if guild else None
                    if member:
                        try:
                            await member.send(embed=_brand(discord.Embed(
                                title="⏰ Meet Starting in 30 Minutes!",
                                description=(
                                    f"**{m['description']}** starts <t:{dt_ts}:R>!\n\n"
                                    "Get ready and hop on — see you there! 🚗"
                                ),
                                color=discord.Color.orange(),
                                timestamp=_est_now(),
                            )))
                        except Exception:
                            pass

    @_reminder_check.before_loop
    async def _before_reminder(self) -> None:
        await self.bot.wait_until_ready()

    # ──────────────────────────────────────────────────────────────────────────
    # 3. Post-meet recap
    # ──────────────────────────────────────────────────────────────────────────

    @commands.command(name="meetrecap")
    async def meetrecap(self, ctx: commands.Context, meet_id: str) -> None:
        """Generate a public recap embed for a meet. Staff only."""
        if not self._staff(ctx):
            return
        await self._del(ctx)
        meets = _load(_MEETS_FILE())
        meet  = meets.get(meet_id)
        if not meet:
            return await ctx.send(f"Meet `{meet_id}` not found.", delete_after=10)

        now         = _est_now()
        attendees   = meet.get("checked_in", [])
        host_id     = meet.get("host_id")
        title_label = meet.get("title", meet_id)

        # Feedback average if available
        fb_data = _load(_FEEDBACK_FILE())
        avg_str = "No feedback yet"
        for ses in fb_data.values():
            ratings = ses.get("ratings", {})
            if ratings and ses.get("meet_name", "").lower() in title_label.lower():
                avg = sum(ratings.values()) / len(ratings)
                avg_str = f"{'⭐' * round(avg)} ({avg:.1f}/5)"
                break

        embed = _brand(discord.Embed(
            title=f"🏁 Meet Recap — {title_label}",
            color=discord.Color.green(),
            timestamp=now,
        ))
        embed.add_field(name="🎮 Host",       value=f"<@{host_id}>" if host_id else "Unknown", inline=True)
        embed.add_field(name="🚗 Attendees",  value=str(len(attendees)),                        inline=True)
        embed.add_field(name="⭐ Avg Rating", value=avg_str,                                    inline=True)
        if attendees:
            mention_list = " ".join(f"<@{uid}>" for uid in attendees[:20])
            if len(attendees) > 20:
                mention_list += f" *+{len(attendees) - 20} more*"
            embed.add_field(name="✅ Present", value=mention_list, inline=False)
        embed.set_footer(text=f"DIFF Meets • Recap posted by {ctx.author.display_name}")

        # Post to schedule channel if set, else current channel
        cfg    = _cfg()
        sch_ch = ctx.guild.get_channel(cfg.get("schedule_channel_id") or 0) if ctx.guild else None
        target = sch_ch if isinstance(sch_ch, discord.TextChannel) else ctx.channel
        await target.send(embed=embed)
        if target != ctx.channel:
            await ctx.send(f"✅ Recap posted in {target.mention}.", delete_after=8)

    # ──────────────────────────────────────────────────────────────────────────
    # 4. Birthday system
    # ──────────────────────────────────────────────────────────────────────────

    @commands.cooldown(1, 86400, commands.BucketType.user)
    @commands.command(name="setbirthday")
    async def setbirthday(self, ctx: commands.Context, month: int, day: int) -> None:
        """Register your birthday (month day). e.g. !setbirthday 4 15"""
        await self._del(ctx)
        if not (1 <= month <= 12 and 1 <= day <= 31):
            return await ctx.send("Invalid date. Use: `!setbirthday <month> <day>` e.g. `!setbirthday 4 15`", delete_after=10)
        bdays = _load(_BIRTHDAYS_FILE)
        bdays[str(ctx.author.id)] = {"month": month, "day": day, "notified_year": None}
        _save(_BIRTHDAYS_FILE, bdays)
        try:
            await ctx.author.send(embed=discord.Embed(
                title="🎂 Birthday Registered!",
                description=f"Your birthday ({month}/{day}) has been saved. The server will celebrate on your day! 🎉",
                color=discord.Color.pink(),
                timestamp=_est_now(),
            ))
        except Exception:
            await ctx.send("✅ Birthday registered!", delete_after=8)

    @commands.command(name="mybirthday")
    async def mybirthday(self, ctx: commands.Context, member: discord.Member = None) -> None:
        """Check your (or another member's) registered birthday."""
        target  = member or ctx.author
        uid_str = str(target.id)
        b       = _load(_BIRTHDAYS_FILE).get(uid_str)
        if not b:
            return await ctx.send(
                f"{'No birthday registered. Use `!setbirthday <month> <day>`.' if target == ctx.author else f'{target.display_name} has not registered their birthday.'}",
                delete_after=12,
            )
        await ctx.send(
            f"🎂 **{target.display_name}'s** birthday: **{b['month']}/{b['day']}**",
            delete_after=20,
        )

    @tasks.loop(hours=24)
    async def _birthday_check(self) -> None:
        now   = _est_now()
        today = (now.month, now.day)
        bdays = _load(_BIRTHDAYS_FILE)
        guild = self.bot.get_guild(_GUILD_ID())
        if not guild:
            return
        cfg     = _cfg()
        bday_ch = guild.get_channel(cfg.get("birthday_channel_id") or 0)
        changed = False
        for uid, b in bdays.items():
            if (b["month"], b["day"]) != today:
                continue
            if b.get("notified_year") == now.year:
                continue
            b["notified_year"] = now.year
            changed = True
            member  = guild.get_member(int(uid))
            if not member:
                continue
            if isinstance(bday_ch, discord.TextChannel):
                try:
                    _joined_ts = int(member.joined_at.timestamp()) if member.joined_at else None
                    bday_embed = discord.Embed(
                        title="🎂 Happy Birthday!",
                        description=(
                            f"Today is **{member.display_name}'s** birthday! 🎉\n\n"
                            f"Everyone show some love for {member.mention} — "
                            f"they've been a part of DIFF Meets and we're glad to have them! 🚗💨"
                        ),
                        color=discord.Color.from_rgb(255, 182, 193),
                        timestamp=now,
                    )
                    bday_embed.set_author(
                        name=member.display_name,
                        icon_url=member.display_avatar.url,
                    )
                    bday_embed.set_thumbnail(url=member.display_avatar.url)
                    if _joined_ts:
                        bday_embed.add_field(
                            name="📅 Member Since",
                            value=f"<t:{_joined_ts}:D>",
                            inline=True,
                        )
                    bday_embed.add_field(name="\u200b", value="React with 🎉 to wish them a happy birthday!", inline=False)
                    bday_embed.set_footer(text="Different Meets • Birthday Celebration")
                    bm = await bday_ch.send(content=member.mention, embed=_brand(bday_embed))
                    try:
                        await bm.add_reaction("🎉")
                        await bm.add_reaction("🎂")
                        await bm.add_reaction("🚗")
                    except Exception:
                        pass
                except Exception:
                    pass
            try:
                dm_embed = discord.Embed(
                    title="🎂 Happy Birthday from DIFF Meets!",
                    description=(
                        f"Wishing you an amazing birthday, **{member.display_name}**! 🎉\n\n"
                        "Thank you for being part of our community — enjoy your day! 🚗💨"
                    ),
                    color=discord.Color.from_rgb(255, 182, 193),
                    timestamp=now,
                )
                dm_embed.set_footer(text="Different Meets • PlayStation GTA Car Meets")
                if _LOGO():
                    dm_embed.set_thumbnail(url=_LOGO())
                await member.send(embed=dm_embed)
            except Exception:
                pass
        if changed:
            _save(_BIRTHDAYS_FILE, bdays)

    @_birthday_check.before_loop
    async def _before_birthday(self) -> None:
        await self.bot.wait_until_ready()

    # ──────────────────────────────────────────────────────────────────────────
    # 5. Member bio
    # ──────────────────────────────────────────────────────────────────────────

    @commands.command(name="setbio")
    async def setbio(self, ctx: commands.Context, *, bio: str) -> None:
        """Set a short bio that appears in your !lookup card (max 200 chars)."""
        await self._del(ctx)
        if len(bio) > 200:
            return await ctx.send("Bio must be 200 characters or fewer.", delete_after=10)
        bios = _load(_BIOS_FILE)
        bios[str(ctx.author.id)] = bio.strip()
        _save(_BIOS_FILE, bios)
        await ctx.send("✅ Bio saved! It will appear in your `!lookup` card.", delete_after=10)

    @commands.command(name="bio")
    async def bio_cmd(self, ctx: commands.Context, member: discord.Member = None) -> None:
        """See your (or another member's) bio."""
        target  = member or ctx.author
        bio_txt = _load(_BIOS_FILE).get(str(target.id), "")
        if not bio_txt:
            msg = "No bio set yet. Use `!setbio <text>`." if target == ctx.author else f"{target.display_name} has no bio set."
            return await ctx.send(msg, delete_after=12)
        embed = discord.Embed(
            title=f"📝 {target.display_name}'s Bio",
            description=bio_txt,
            color=discord.Color.blurple(),
            timestamp=_est_now(),
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        await ctx.send(embed=embed, delete_after=30)

    # ──────────────────────────────────────────────────────────────────────────
    # 6. Achievements / badges
    # ──────────────────────────────────────────────────────────────────────────

    def _check_and_award(self, uid_str: str, act: dict) -> list[str]:
        """Return list of newly earned achievement keys for a member."""
        ach_db  = _load(_ACHIEVEMENTS_FILE)
        earned  = set(ach_db.get(uid_str, []))
        new_ach = []
        attended = act.get("meets_attended", 0)
        hosted   = act.get("meets_hosted",   0)
        for threshold, key in _ATT_THRESHOLDS:
            if attended >= threshold and key not in earned:
                earned.add(key)
                new_ach.append(key)
        for threshold, key in _HOST_THRESHOLDS:
            if hosted >= threshold and key not in earned:
                earned.add(key)
                new_ach.append(key)
        if new_ach:
            ach_db[uid_str] = list(earned)
            _save(_ACHIEVEMENTS_FILE, ach_db)
        return new_ach

    @commands.command(name="awardachievements")
    async def awardachievements(self, ctx: commands.Context, meet_id: str = "") -> None:
        """Check and award achievements to all meet attendees (or all members)."""
        if not self._staff(ctx):
            return
        await self._del(ctx)
        now       = _est_now()
        activity  = _load(_ACT_FILE())
        guild     = ctx.guild

        if meet_id:
            meets = _load(_MEETS_FILE())
            meet  = meets.get(meet_id)
            if not meet:
                return await ctx.send(f"Meet `{meet_id}` not found.", delete_after=10)
            targets = [str(uid) for uid in meet.get("checked_in", [])]
        else:
            targets = list(activity.keys())

        awarded_total = 0
        for uid_str in targets:
            act = activity.get(uid_str, {})
            new = self._check_and_award(uid_str, act)
            if new and guild:
                member = guild.get_member(int(uid_str))
                if member:
                    awarded_total += len(new)
                    badge_lines = "\n".join(
                        f"{_ACHIEVEMENTS[k]['emoji']} **{_ACHIEVEMENTS[k]['name']}** — {_ACHIEVEMENTS[k]['desc']}"
                        for k in new if k in _ACHIEVEMENTS
                    )
                    try:
                        await member.send(embed=_brand(discord.Embed(
                            title="🏅 New Achievement Unlocked!",
                            description=f"You earned new badge(s):\n\n{badge_lines}",
                            color=discord.Color.gold(),
                            timestamp=now,
                        )))
                    except Exception:
                        pass
        await ctx.send(
            f"✅ Achievement check complete — **{awarded_total}** badge(s) awarded across **{len(targets)}** member(s).",
            delete_after=15,
        )

    @commands.command(name="achievements")
    async def achievements_cmd(self, ctx: commands.Context, member: discord.Member = None) -> None:
        """View your (or another member's) achievement badges."""
        target   = member or ctx.author
        uid_str  = str(target.id)
        ach_db   = _load(_ACHIEVEMENTS_FILE)
        earned   = ach_db.get(uid_str, [])
        now      = _est_now()
        if not earned:
            msg = "No achievements yet. Attend meets to earn badges!" if target == ctx.author else f"{target.display_name} has no achievements yet."
            return await ctx.send(msg, delete_after=12)
        lines = [
            f"{_ACHIEVEMENTS[k]['emoji']} **{_ACHIEVEMENTS[k]['name']}** — {_ACHIEVEMENTS[k]['desc']}"
            for k in earned if k in _ACHIEVEMENTS
        ]
        embed = discord.Embed(
            title=f"🏅 Achievements — {target.display_name}",
            description="\n".join(lines),
            color=discord.Color.gold(),
            timestamp=now,
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text=f"{len(earned)} badge(s) earned • Different Meets")
        await ctx.send(embed=embed, delete_after=60)

    # ──────────────────────────────────────────────────────────────────────────
    # 7. XP / Level system
    # ──────────────────────────────────────────────────────────────────────────

    def _add_xp(self, uid_str: str, amount: int) -> tuple[int, int, bool]:
        """Add XP and return (new_xp, new_level, levelled_up)."""
        xp_db   = _load(_XP_FILE)
        entry   = xp_db.setdefault(uid_str, {"xp": 0, "level": 1})
        old_lvl = _level_for_xp(entry["xp"])
        entry["xp"] += amount
        new_lvl = _level_for_xp(entry["xp"])
        entry["level"] = new_lvl
        _save(_XP_FILE, xp_db)
        return entry["xp"], new_lvl, new_lvl > old_lvl

    @commands.Cog.listener("on_message")
    async def _xp_listener(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return
        uid = message.author.id
        now = time.monotonic()
        if now - self._xp_cd.get(uid, 0) < 60:
            return
        self._xp_cd[uid] = now
        new_xp, new_lvl, levelled = self._add_xp(str(uid), 5)
        if levelled:
            try:
                await message.author.send(embed=_brand(discord.Embed(
                    title=f"⬆️ Level Up! You're now Level {new_lvl}",
                    description=(
                        f"Keep attending meets and chatting to level up further!\n\n"
                        f"**Total XP:** {new_xp:,}  |  **Level:** {new_lvl}\n"
                        f"`{_xp_bar(new_xp, new_lvl)}` → Level {new_lvl + 1}"
                    ),
                    color=discord.Color.gold(),
                    timestamp=_est_now(),
                )))
            except Exception:
                pass

    @commands.command(name="addxp")
    async def addxp(self, ctx: commands.Context, member: discord.Member, amount: int) -> None:
        """Manually add XP to a member. Staff only."""
        if not self._staff(ctx):
            return
        await self._del(ctx)
        new_xp, new_lvl, _ = self._add_xp(str(member.id), amount)
        await ctx.send(
            f"✅ Added **{amount} XP** to {member.mention}. Now at **{new_xp:,} XP / Level {new_lvl}**.",
            delete_after=12,
        )

    @commands.command(name="xp")
    async def xp_cmd(self, ctx: commands.Context, member: discord.Member = None) -> None:
        """Check your (or another member's) XP and level."""
        target  = member or ctx.author
        uid_str = str(target.id)
        entry   = _load(_XP_FILE).get(uid_str, {"xp": 0, "level": 1})
        xp      = entry.get("xp", 0)
        level   = _level_for_xp(xp)
        nxt     = _xp_for_level(level + 1)
        bar     = _xp_bar(xp, level)
        embed   = discord.Embed(
            title=f"⭐ XP — {target.display_name}",
            description=(
                f"**Level:** {level}\n"
                f"**XP:** {xp:,} / {nxt:,}\n"
                f"`{bar}` → Level {level + 1}"
            ),
            color=discord.Color.gold(),
            timestamp=_est_now(),
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="Earn XP by chatting (+5/min) and attending meets (+100)")
        await ctx.send(embed=embed, delete_after=30)

    @commands.command(name="levels")
    async def levels_cmd(self, ctx: commands.Context) -> None:
        """Show the server XP leaderboard."""
        xp_db = _load(_XP_FILE)
        if not xp_db:
            return await ctx.send("No XP data yet.", delete_after=10)
        sorted_members = sorted(xp_db.items(), key=lambda x: x[1].get("xp", 0), reverse=True)[:10]
        now    = _est_now()
        medals = ["🥇", "🥈", "🥉"]
        lines  = []
        for i, (uid, entry) in enumerate(sorted_members):
            xp  = entry.get("xp", 0)
            lvl = _level_for_xp(xp)
            pre = medals[i] if i < 3 else f"**{i+1}.**"
            lines.append(f"{pre} <@{uid}> — Level {lvl} · {xp:,} XP")
        embed = _brand(discord.Embed(
            title="⭐ XP Leaderboard",
            description="\n".join(lines),
            color=discord.Color.gold(),
            timestamp=now,
        ))
        embed.set_footer(text="Different Meets • XP System")
        await ctx.send(embed=embed, delete_after=60)

    # ──────────────────────────────────────────────────────────────────────────
    # 8. Channel lock / unlock
    # ──────────────────────────────────────────────────────────────────────────

    @commands.command(name="lock")
    async def lock(self, ctx: commands.Context, channel: discord.TextChannel = None) -> None:
        """Lock a channel so members can't send messages. Staff only."""
        if not self._staff(ctx):
            return
        await self._del(ctx)
        ch = channel or ctx.channel
        if not isinstance(ch, discord.TextChannel) or not ctx.guild:
            return
        verified_role = ctx.guild.get_role(_VERIFIED()) or ctx.guild.default_role
        await ch.set_permissions(verified_role, send_messages=False)
        await ch.send(embed=discord.Embed(
            description=f"🔒 **Channel locked** by {ctx.author.mention}. Members may not send messages.",
            color=discord.Color.red(),
            timestamp=_est_now(),
        ))
        logs_ch = ctx.guild.get_channel(_STAFF_LOGS())
        if isinstance(logs_ch, discord.TextChannel) and ch != ctx.channel:
            try:
                await logs_ch.send(
                    embed=discord.Embed(
                        title="🔒 Channel Locked",
                        description=f"{ch.mention} locked by {ctx.author.mention}",
                        color=discord.Color.red(),
                        timestamp=_est_now(),
                    )
                )
            except Exception:
                pass

    @commands.command(name="unlock")
    async def unlock(self, ctx: commands.Context, channel: discord.TextChannel = None) -> None:
        """Unlock a previously locked channel. Staff only."""
        if not self._staff(ctx):
            return
        await self._del(ctx)
        ch = channel or ctx.channel
        if not isinstance(ch, discord.TextChannel) or not ctx.guild:
            return
        verified_role = ctx.guild.get_role(_VERIFIED()) or ctx.guild.default_role
        await ch.set_permissions(verified_role, send_messages=True)
        await ch.send(embed=discord.Embed(
            description=f"🔓 **Channel unlocked** by {ctx.author.mention}.",
            color=discord.Color.green(),
            timestamp=_est_now(),
        ))

    # ──────────────────────────────────────────────────────────────────────────
    # 9. Anti-spam auto-timeout
    # ──────────────────────────────────────────────────────────────────────────

    @commands.Cog.listener("on_message")
    async def _antispam(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return
        if not isinstance(message.author, discord.Member):
            return
        if _is_staff(message.author) or message.author.guild_permissions.administrator:
            return
        uid  = message.author.id
        mono = time.monotonic()
        lst  = self._spam_tracker.setdefault(uid, [])
        lst[:] = [t for t in lst if mono - t < 4]
        lst.append(mono)
        if len(lst) < 5:
            return
        lst.clear()
        try:
            until = _est_now() + timedelta(minutes=10)
            await message.author.timeout(timedelta(minutes=10), reason="Auto-timeout: spam detected")
            try:
                await message.channel.send(
                    f"{message.author.mention} You've been timed out for 10 minutes for sending too many messages.",
                    delete_after=10,
                )
            except Exception:
                pass
            logs_ch = message.guild.get_channel(_STAFF_LOGS())
            if isinstance(logs_ch, discord.TextChannel):
                await logs_ch.send(embed=discord.Embed(
                    title="⚡ Anti-Spam — Auto Timeout (10 min)",
                    description=(
                        f"**Member:** {message.author.mention} (`{message.author.id}`)\n"
                        f"**Channel:** {message.channel.mention}\n"
                        f"**Expires:** <t:{int(until.timestamp())}:R>"
                    ),
                    color=discord.Color.orange(),
                    timestamp=_est_now(),
                ))
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────────────────────
    # 10. Auto-dehoist
    # ──────────────────────────────────────────────────────────────────────────

    async def _dehoist_member(self, member: discord.Member) -> None:
        cfg = _cfg()
        if not cfg.get("dehoist_enabled"):
            return
        display = member.nick or member.name
        if not _SYMBOL_RE.match(display):
            return
        clean = re.sub(r"^[^A-Za-z0-9]+", "", display) or f"DIFF-{member.name[:20]}"
        try:
            await member.edit(nick=clean, reason="Auto-dehoist: leading symbol removed")
        except Exception:
            pass

    @commands.Cog.listener("on_member_join")
    async def _dehoist_join(self, member: discord.Member) -> None:
        await self._dehoist_member(member)

    @commands.Cog.listener("on_member_update")
    async def _dehoist_update(self, before: discord.Member, after: discord.Member) -> None:
        if before.nick != after.nick:
            await self._dehoist_member(after)

    @commands.command(name="dehoist")
    async def dehoist_toggle(self, ctx: commands.Context, state: str) -> None:
        """!dehoist on  /  !dehoist off — toggle auto-dehoist. Staff only."""
        if not self._staff(ctx):
            return
        await self._del(ctx)
        enabled = state.lower() in {"on", "true", "yes", "enable"}
        _cfg_set(dehoist_enabled=enabled)
        await ctx.send(
            f"✅ Auto-dehoist **{'enabled' if enabled else 'disabled'}**.", delete_after=10
        )

    # ──────────────────────────────────────────────────────────────────────────
    # 11. Ticket transcript
    # ──────────────────────────────────────────────────────────────────────────

    @commands.command(name="transcript")
    async def transcript(self, ctx: commands.Context) -> None:
        """Generate a .txt transcript of this ticket channel and send it to staff logs + ticket owner."""
        if not self._staff(ctx):
            return
        await self._del(ctx)
        await ctx.send("⏳ Generating transcript…", delete_after=5)

        lines: list[str] = [
            f"═══════════════════════════════════════════",
            f"DIFF Meets — Ticket Transcript",
            f"Channel: #{ctx.channel.name}",
            f"Generated: {_est_now().strftime('%Y-%m-%d %I:%M %p ET')}",
            f"═══════════════════════════════════════════\n",
        ]
        try:
            async for msg in ctx.channel.history(limit=500, oldest_first=True):
                ts   = msg.created_at.astimezone(_EST_TZ).strftime("%Y-%m-%d %H:%M")
                body = msg.content or "[embed/attachment]"
                lines.append(f"[{ts}] {msg.author} ({msg.author.id}): {body}")
                for e in msg.embeds:
                    if e.title:
                        lines.append(f"  [Embed] {e.title}: {e.description or ''}")
        except Exception as ex:
            return await ctx.send(f"Error fetching messages: `{ex}`", delete_after=12)

        content = "\n".join(lines)
        buf     = io.BytesIO(content.encode("utf-8"))
        fname   = f"transcript_{ctx.channel.name}_{_est_now().strftime('%Y%m%d_%H%M')}.txt"
        file1   = discord.File(io.BytesIO(content.encode("utf-8")), filename=fname)

        # Send to staff logs
        logs_ch = ctx.guild.get_channel(_STAFF_LOGS()) if ctx.guild else None
        if isinstance(logs_ch, discord.TextChannel):
            try:
                await logs_ch.send(
                    embed=discord.Embed(
                        title="📋 Ticket Transcript",
                        description=f"Channel: {ctx.channel.mention} · {len(lines)} lines",
                        color=discord.Color.blurple(),
                        timestamp=_est_now(),
                    ),
                    file=file1,
                )
            except Exception:
                pass

        # Try to DM ticket owner from channel topic
        owner_id = None
        topic    = ctx.channel.topic or ""
        m        = re.search(r"ticket_owner=(\d+)", topic)
        if m:
            owner_id = int(m.group(1))
        if owner_id and ctx.guild:
            owner = ctx.guild.get_member(owner_id)
            if owner:
                try:
                    await owner.send(
                        embed=discord.Embed(
                            title="📋 Your Ticket Transcript",
                            description="A full transcript of your ticket has been attached below.",
                            color=discord.Color.blurple(),
                            timestamp=_est_now(),
                        ),
                        file=discord.File(io.BytesIO(content.encode("utf-8")), filename=fname),
                    )
                except Exception:
                    pass

        await ctx.send(f"✅ Transcript generated — **{len(lines)}** lines saved to staff logs.", delete_after=12)

    # ──────────────────────────────────────────────────────────────────────────
    # 12. Staff roster
    # ──────────────────────────────────────────────────────────────────────────

    @commands.command(name="stafflist")
    async def stafflist(self, ctx: commands.Context) -> None:
        """Show all staff members organised by role."""
        if not ctx.guild:
            return
        await self._del(ctx)
        now          = _est_now()
        staff_roles  = [
            (_LEADER(),     "👑 Leader"),
            (_CO_LEADER(),  "⭐ Co-Leader"),
            (_MANAGER(),    "🔧 Manager"),
            (_HOST(),       "🎮 Host"),
        ]
        embed = _brand(discord.Embed(
            title="🛡️ DIFF Meets Staff Roster",
            color=discord.Color.blurple(),
            timestamp=now,
        ))
        total = 0
        for role_id, label in staff_roles:
            role = ctx.guild.get_role(role_id)
            if not role or not role.members:
                continue
            members_txt = "\n".join(
                f"{'🟢' if m.status == discord.Status.online else '⚫'} {m.display_name}"
                for m in role.members if not m.bot
            )
            if members_txt:
                embed.add_field(name=f"{label} ({len(role.members)})", value=members_txt, inline=True)
                total += len(role.members)
        embed.set_footer(text=f"Total staff: {total} • {now.strftime('%I:%M %p ET')}")
        await ctx.send(embed=embed, delete_after=60)

    # ──────────────────────────────────────────────────────────────────────────
    # 13. Scheduled announcements
    # ──────────────────────────────────────────────────────────────────────────

    @commands.command(name="scheduleannounce")
    async def scheduleannounce(
        self,
        ctx: commands.Context,
        minutes: int,
        channel: discord.TextChannel,
        *,
        message: str,
    ) -> None:
        """!scheduleannounce <minutes_from_now> #channel <message>"""
        if not self._staff(ctx):
            return
        await self._del(ctx)
        if minutes < 1 or minutes > 10080:
            return await ctx.send("Minutes must be between 1 and 10080 (1 week).", delete_after=10)
        now      = _est_now()
        send_ts  = int((now + timedelta(minutes=minutes)).timestamp())
        ann_id   = str(send_ts)
        anns     = _load(_SCHED_ANN_FILE)
        anns[ann_id] = {
            "channel_id": channel.id, "guild_id": ctx.guild.id,
            "message":    message,    "send_at_ts": send_ts,
            "sent":       False,      "created_by": ctx.author.id,
        }
        _save(_SCHED_ANN_FILE, anns)
        await ctx.send(
            f"✅ Announcement scheduled for {channel.mention} in **{minutes} minute(s)** (<t:{send_ts}:R>).",
            delete_after=12,
        )

    @tasks.loop(minutes=1)
    async def _sched_ann_check(self) -> None:
        now_ts = int(_est_now().timestamp())
        anns   = _load(_SCHED_ANN_FILE)
        changed = False
        for ann_id, ann in anns.items():
            if ann.get("sent") or ann.get("send_at_ts", 0) > now_ts:
                continue
            ann["sent"] = True
            changed     = True
            guild   = self.bot.get_guild(ann.get("guild_id", _GUILD_ID()))
            channel = guild.get_channel(ann["channel_id"]) if guild else None
            if isinstance(channel, discord.TextChannel):
                try:
                    await channel.send(ann["message"])
                except Exception:
                    pass
        if changed:
            _save(_SCHED_ANN_FILE, anns)

    @_sched_ann_check.before_loop
    async def _before_sched_ann(self) -> None:
        await self.bot.wait_until_ready()

    # ──────────────────────────────────────────────────────────────────────────
    # 14. Bulk role DM
    # ──────────────────────────────────────────────────────────────────────────

    @commands.command(name="roledm")
    async def roledm(self, ctx: commands.Context, role: discord.Role, *, message: str) -> None:
        """!roledm @Role <message> — DM all members with a role. Requires confirmation."""
        if not self._staff(ctx):
            return
        await self._del(ctx)
        real_members = [m for m in role.members if not m.bot]
        dm_id        = str(int(_est_now().timestamp()))
        embed        = discord.Embed(
            title="📨 Bulk Role DM — Confirmation Required",
            description=(
                f"**Role:** {role.mention}\n"
                f"**Recipients:** {len(real_members)} member(s)\n\n"
                f"**Message preview:**\n> {message[:300]}\n\n"
                f"⚠️ Press the button to send. This cannot be undone.\n"
                f"*Expires in 5 minutes if not confirmed.*"
            ),
            color=discord.Color.orange(),
            timestamp=_est_now(),
        )
        await ctx.send(embed=embed, view=_RoleDmView(dm_id, role.id, message))

    # ──────────────────────────────────────────────────────────────────────────
    # 15. Auto-updating server stats
    # ──────────────────────────────────────────────────────────────────────────

    async def _rebuild_stats_embed(self, guild: discord.Guild) -> discord.Embed:
        now      = _est_now()
        verified = guild.get_role(_VERIFIED())
        crew     = guild.get_role(_CREW())
        host_r   = guild.get_role(_HOST())
        activity = _load(_ACT_FILE())
        meets_raw = _load(_MEETS_FILE())

        month_pfx  = now.strftime("%Y-%m")
        month_meets = sum(
            1 for m in meets_raw.values()
            if (m.get("created_at") or "").startswith(month_pfx)
        )

        embed = _brand(discord.Embed(
            title="📊 DIFF Meets — Server Stats",
            color=discord.Color.blurple(),
            timestamp=now,
        ))
        embed.add_field(name="👥 Total Members",    value=str(guild.member_count or 0),                                inline=True)
        embed.add_field(name="✅ Verified",         value=str(len(verified.members)) if verified else "N/A",          inline=True)
        embed.add_field(name="🎮 Hosts",            value=str(len(host_r.members))   if host_r   else "N/A",          inline=True)
        embed.add_field(name="🏎️ Crew Members",    value=str(len(crew.members))      if crew     else "N/A",          inline=True)
        embed.add_field(name="🚗 Meets This Month", value=str(month_meets),                                           inline=True)
        embed.add_field(name="📅 Total Meets",      value=str(len(meets_raw)),                                        inline=True)
        embed.set_footer(text=f"Auto-refreshes hourly • Last update {now.strftime('%I:%M %p ET')}")
        return embed

    @commands.command(name="setstats")
    async def setstats(self, ctx: commands.Context, channel: discord.TextChannel = None) -> None:
        """!setstats [#channel] — set where the live stats embed lives. Staff only."""
        if not self._staff(ctx):
            return
        await self._del(ctx)
        ch  = channel or ctx.channel
        cfg = _cfg()
        cfg["stats_channel_id"] = ch.id
        cfg["stats_message_id"] = None
        _save(_ADV_CONFIG_FILE, cfg)
        embed = await self._rebuild_stats_embed(ctx.guild)
        msg   = await ch.send(embed=embed)
        cfg["stats_message_id"] = msg.id
        _save(_ADV_CONFIG_FILE, cfg)
        await ctx.send(f"✅ Stats embed posted in {ch.mention} — updates every hour.", delete_after=10)

    @tasks.loop(hours=1)
    async def _stats_update(self) -> None:
        cfg = _cfg()
        ch_id  = cfg.get("stats_channel_id")
        msg_id = cfg.get("stats_message_id")
        if not ch_id or not msg_id:
            return
        guild   = self.bot.get_guild(_GUILD_ID())
        channel = guild.get_channel(int(ch_id)) if guild else None
        if not isinstance(channel, discord.TextChannel):
            return
        try:
            msg   = await channel.fetch_message(int(msg_id))
            embed = await self._rebuild_stats_embed(guild)
            await msg.edit(embed=embed)
        except discord.NotFound:
            guild = self.bot.get_guild(_GUILD_ID())
            if guild:
                embed = await self._rebuild_stats_embed(guild)
                new_msg = await channel.send(embed=embed)
                cfg["stats_message_id"] = new_msg.id
                _save(_ADV_CONFIG_FILE, cfg)
        except Exception:
            pass

    @_stats_update.before_loop
    async def _before_stats(self) -> None:
        await self.bot.wait_until_ready()

    # ──────────────────────────────────────────────────────────────────────────
    # Config helpers
    # ──────────────────────────────────────────────────────────────────────────

    @commands.command(name="setschedulechannel")
    async def setschedulechannel(self, ctx: commands.Context, channel: discord.TextChannel) -> None:
        """Set the channel where scheduled meets are posted. Staff only."""
        if not self._staff(ctx):
            return
        await self._del(ctx)
        _cfg_set(schedule_channel_id=channel.id)
        await ctx.send(f"✅ Schedule channel set to {channel.mention}.", delete_after=10)

    @commands.command(name="setbirthdaychannel")
    async def setbirthdaychannel(self, ctx: commands.Context, channel: discord.TextChannel) -> None:
        """Set the channel where birthday announcements are posted. Staff only."""
        if not self._staff(ctx):
            return
        await self._del(ctx)
        _cfg_set(birthday_channel_id=channel.id)
        await ctx.send(f"✅ Birthday channel set to {channel.mention}.", delete_after=10)

    # ──────────────────────────────────────────────────────────────────────────
    # Daily JSON backup task
    # ──────────────────────────────────────────────────────────────────────────

    @tasks.loop(hours=24)
    async def _daily_backup(self) -> None:
        """Zip all JSON data files once a day and keep the last 7 backups."""
        import zipfile, glob as _glob, time as _time
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        timestamp  = _time.strftime("%Y%m%d_%H%M%S")
        zip_path   = os.path.join(backup_dir, f"data_{timestamp}.zip")
        try:
            patterns = ["*.json", "diff_data/*.json"]
            files_to_zip = []
            for pat in patterns:
                files_to_zip.extend(_glob.glob(pat))
            if not files_to_zip:
                return
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for fp in files_to_zip:
                    zf.write(fp)
            existing = sorted(_glob.glob(os.path.join(backup_dir, "data_*.zip")))
            for old in existing[:-7]:
                try:
                    os.remove(old)
                except Exception:
                    pass
        except Exception:
            pass

    @_daily_backup.before_loop
    async def _before_backup(self) -> None:
        await self.bot.wait_until_ready()

    # ──────────────────────────────────────────────────────────────────────────
    # Announce new member features (!announcefeatures)
    # ──────────────────────────────────────────────────────────────────────────

    @commands.command(name="announcefeatures")
    async def announcefeatures(self, ctx: commands.Context, channel: discord.TextChannel = None) -> None:
        """Post an announcement about new member commands. Staff only."""
        if not self._staff(ctx):
            return
        await self._del(ctx)
        dest = channel or ctx.channel
        embed = discord.Embed(
            title="✨ New Member Features Available",
            description=(
                "We've added some cool new commands just for you. Here's what you can do:"
            ),
            color=discord.Color.blurple(),
            timestamp=_est_now(),
        )
        embed.add_field(
            name="🎂 Register Your Birthday",
            value="`!setbirthday <month> <day>` — e.g. `!setbirthday 9 6`\nThe server will celebrate your birthday with an announcement!",
            inline=False,
        )
        embed.add_field(
            name="📝 Set Your Bio",
            value="`!setbio <text>` — Write a short bio that shows up on your profile.",
            inline=False,
        )
        embed.add_field(
            name="⭐ Check Your XP & Level",
            value="`!xp` — See your current XP and level.\n`!levels` — View the server leaderboard.",
            inline=False,
        )
        embed.add_field(
            name="🏆 View Achievements",
            value="`!achievements` — See all badges and achievements you've earned.",
            inline=False,
        )
        embed.add_field(
            name="💡 Submit a Suggestion",
            value="`!suggest <idea>` — Send your ideas straight to leadership for review.",
            inline=False,
        )
        embed.add_field(
            name="📅 View Scheduled Meets",
            value="`!schedule` — See upcoming meets and RSVP.",
            inline=False,
        )
        embed.set_footer(text="DIFF Meets • New Features")
        await dest.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DiffAdvancedFeatures(bot))
