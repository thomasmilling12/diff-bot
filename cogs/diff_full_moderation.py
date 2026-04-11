from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import discord
from discord.ext import commands

# =========================================================
# CONFIG
# =========================================================

GUILD_ID = 850386896509337710

DIFF_LOGO_URL = "https://media.discordapp.net/attachments/1107375326625005719/1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm=2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a&=&format=webp&quality=lossless&width=1376&height=917"

MOD_ALERT_CHANNEL_ID = 1485265848099799163   # staff-logs

WARNING_ROLE_ID    = 0   # optional — fill in role ID
RESTRICTED_ROLE_ID = 0   # optional — fill in role ID
HOST_REVIEW_ROLE_ID = 0  # optional — fill in role ID

SEND_DM_NOTIFICATIONS = True

WARNING_THRESHOLD    = 2
RESTRICTED_THRESHOLD = 3
CRITICAL_THRESHOLD   = 4

HOST_BAD_FEEDBACK_THRESHOLD   = 2.5
HOST_WRITEUP_THRESHOLD        = 2
HOST_LOW_ATTENDANCE_THRESHOLD = 2

COLOR_PRIMARY = 0x1F6FEB
COLOR_SUCCESS = 0x2ECC71
COLOR_WARNING = 0xF39C12
COLOR_DANGER  = 0xE74C3C
COLOR_MUTED   = 0x95A5A6

DATA_DIR           = Path("diff_data")
MOD_PROFILES_FILE  = DATA_DIR / "moderation_profiles.json"
HOST_PROFILES_FILE = DATA_DIR / "host_performance_profiles.json"

# =========================================================
# HELPERS
# =========================================================

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

def _load(path: Path, default: Any) -> Any:
    if not path.exists():
        _save(path, default)
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _save(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def _default_member(user_id: int, display_name: str) -> Dict[str, Any]:
    return {
        "user_id":          user_id,
        "display_name":     display_name,
        "writeups":         0,
        "strikes":          0,
        "feedback_entries": 0,
        "feedback_average": 0.0,
        "attendance_count": 0,
        "hosted_meets":     0,
        "flags":            [],
        "last_updated":     _utcnow().isoformat(),
    }

def _default_host(user_id: int, display_name: str) -> Dict[str, Any]:
    return {
        "user_id":            user_id,
        "display_name":       display_name,
        "hosted_meets":       0,
        "attendance_total":   0,
        "attendance_average": 0.0,
        "feedback_entries":   0,
        "feedback_average":   0.0,
        "host_writeups":      0,
        "warnings":           0,
        "review_flagged":     False,
        "last_updated":       _utcnow().isoformat(),
    }

# =========================================================
# COG
# =========================================================

class FullModerationSystem(commands.Cog, name="FullModerationSystem"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        _load(MOD_PROFILES_FILE,  {})
        _load(HOST_PROFILES_FILE, {})

    @commands.Cog.listener()
    async def on_ready(self):
        print("[FullModerationSystem] Cog ready.")

    # ── storage ──────────────────────────────────────────────

    def _members(self) -> Dict[str, Any]:
        return _load(MOD_PROFILES_FILE, {})

    def _set_members(self, data: Dict[str, Any]) -> None:
        _save(MOD_PROFILES_FILE, data)

    def _hosts(self) -> Dict[str, Any]:
        return _load(HOST_PROFILES_FILE, {})

    def _set_hosts(self, data: Dict[str, Any]) -> None:
        _save(HOST_PROFILES_FILE, data)

    def _get_or_create_member(self, user_id: int, display_name: str) -> Dict[str, Any]:
        data = self._members()
        key  = str(user_id)
        if key not in data:
            data[key] = _default_member(user_id, display_name)
            self._set_members(data)
        return data[key]

    def _get_or_create_host(self, user_id: int, display_name: str) -> Dict[str, Any]:
        data = self._hosts()
        key  = str(user_id)
        if key not in data:
            data[key] = _default_host(user_id, display_name)
            self._set_hosts(data)
        return data[key]

    # =========================================================
    # PUBLIC INTEGRATION METHODS
    # Called from other cogs when events occur
    # =========================================================

    async def register_writeup(self, guild: discord.Guild, member: discord.Member,
                                source: str = "writeup_system") -> None:
        data    = self._members()
        key     = str(member.id)
        profile = data.get(key, _default_member(member.id, str(member)))
        profile["writeups"]      += 1
        profile["display_name"]   = str(member)
        profile["last_updated"]   = _utcnow().isoformat()
        data[key] = profile
        self._set_members(data)
        await self._evaluate_member(guild, member, source=f"Write-Up ({source})")

    async def register_strike(self, guild: discord.Guild, member: discord.Member,
                               source: str = "strike_system") -> None:
        data    = self._members()
        key     = str(member.id)
        profile = data.get(key, _default_member(member.id, str(member)))
        profile["strikes"]       += 1
        profile["display_name"]   = str(member)
        profile["last_updated"]   = _utcnow().isoformat()
        data[key] = profile
        self._set_members(data)
        await self._evaluate_member(guild, member, source=f"Strike ({source})")

    async def register_feedback(self, guild: discord.Guild, member: discord.Member,
                                 rating: float, source: str = "feedback_system") -> None:
        data    = self._members()
        key     = str(member.id)
        profile = data.get(key, _default_member(member.id, str(member)))
        old_avg, old_n = float(profile["feedback_average"]), int(profile["feedback_entries"])
        new_n   = old_n + 1
        profile["feedback_average"] = round(((old_avg * old_n) + rating) / new_n, 2)
        profile["feedback_entries"] = new_n
        profile["display_name"]     = str(member)
        profile["last_updated"]     = _utcnow().isoformat()
        data[key] = profile
        self._set_members(data)

    async def register_attendance(self, guild: discord.Guild, member: discord.Member,
                                   source: str = "attendance_system") -> None:
        data    = self._members()
        key     = str(member.id)
        profile = data.get(key, _default_member(member.id, str(member)))
        profile["attendance_count"] += 1
        profile["display_name"]      = str(member)
        profile["last_updated"]      = _utcnow().isoformat()
        data[key] = profile
        self._set_members(data)

    async def register_hosted_meet(self, guild: discord.Guild, host: discord.Member,
                                    attendance_count: int = 0, source: str = "host_system") -> None:
        mdata    = self._members()
        mk       = str(host.id)
        mprofile = mdata.get(mk, _default_member(host.id, str(host)))
        mprofile["hosted_meets"]  += 1
        mprofile["display_name"]   = str(host)
        mprofile["last_updated"]   = _utcnow().isoformat()
        mdata[mk] = mprofile
        self._set_members(mdata)

        hdata    = self._hosts()
        hk       = str(host.id)
        hprofile = hdata.get(hk, _default_host(host.id, str(host)))
        hprofile["hosted_meets"]      += 1
        hprofile["attendance_total"]  += max(0, attendance_count)
        if hprofile["hosted_meets"] > 0:
            hprofile["attendance_average"] = round(
                hprofile["attendance_total"] / hprofile["hosted_meets"], 2
            )
        hprofile["display_name"]   = str(host)
        hprofile["last_updated"]   = _utcnow().isoformat()
        hdata[hk] = hprofile
        self._set_hosts(hdata)
        await self._evaluate_host(guild, host, source=f"Hosted Meet ({source})")

    async def register_host_feedback(self, guild: discord.Guild, host: discord.Member,
                                      rating: float, source: str = "feedback_system") -> None:
        data    = self._hosts()
        key     = str(host.id)
        profile = data.get(key, _default_host(host.id, str(host)))
        old_avg, old_n = float(profile["feedback_average"]), int(profile["feedback_entries"])
        new_n   = old_n + 1
        profile["feedback_average"] = round(((old_avg * old_n) + rating) / new_n, 2)
        profile["feedback_entries"] = new_n
        profile["display_name"]     = str(host)
        profile["last_updated"]     = _utcnow().isoformat()
        data[key] = profile
        self._set_hosts(data)
        await self._evaluate_host(guild, host, source=f"Host Feedback ({source})")

    async def register_host_writeup(self, guild: discord.Guild, host: discord.Member,
                                     source: str = "writeup_system") -> None:
        data    = self._hosts()
        key     = str(host.id)
        profile = data.get(key, _default_host(host.id, str(host)))
        profile["host_writeups"]  += 1
        profile["display_name"]    = str(host)
        profile["last_updated"]    = _utcnow().isoformat()
        data[key] = profile
        self._set_hosts(data)
        await self._evaluate_host(guild, host, source=f"Host Write-Up ({source})")

    # ── alerts / role actions ─────────────────────────────────

    async def _alert(self, guild: discord.Guild, title: str, description: str, color: int = COLOR_WARNING):
        if not MOD_ALERT_CHANNEL_ID:
            return
        ch = guild.get_channel(MOD_ALERT_CHANNEL_ID)
        if ch is None:
            return
        embed = discord.Embed(title=title, description=description,
                              color=color, timestamp=_utcnow())
        embed.set_footer(text="Different Meets • Full Moderation System")
        try:
            await ch.send(embed=embed)
        except discord.HTTPException:
            pass

    async def _safe_add_role(self, member: discord.Member, role_id: int, reason: str):
        if not role_id:
            return
        role = member.guild.get_role(role_id)
        if not role or role in member.roles:
            return
        try:
            await member.add_roles(role, reason=reason)
        except discord.HTTPException:
            pass

    async def _dm(self, member: discord.Member, message: str):
        if not SEND_DM_NOTIFICATIONS:
            return
        try:
            em = discord.Embed(
                description=message,
                color=discord.Color.dark_blue(),
            )
            em.set_author(name="Different Meets", icon_url=DIFF_LOGO_URL)
            em.set_thumbnail(url=DIFF_LOGO_URL)
            await member.send(embed=em)
        except discord.HTTPException:
            pass

    async def _evaluate_member(self, guild: discord.Guild, member: discord.Member, source: str):
        data    = self._members()
        profile = data.get(str(member.id))
        if not profile:
            return
        strikes = int(profile["strikes"])
        flags   = set(profile.get("flags", []))

        if strikes >= WARNING_THRESHOLD and "warning_flag" not in flags:
            flags.add("warning_flag")
            await self._safe_add_role(member, WARNING_ROLE_ID, "Reached moderation warning threshold")
            await self._alert(guild, "⚠️ Member Warning Threshold Reached",
                              f"**Member:** {member.mention}\n**Strikes:** {strikes}\n**Source:** {source}",
                              COLOR_WARNING)
            await self._dm(member,
                           f"You have reached the DIFF warning threshold with **{strikes} strike(s)**. "
                           "Please review server expectations.")

        if strikes >= RESTRICTED_THRESHOLD and "restricted_flag" not in flags:
            flags.add("restricted_flag")
            await self._safe_add_role(member, RESTRICTED_ROLE_ID, "Reached moderation restricted threshold")
            await self._alert(guild, "🚨 Member Restricted Threshold Reached",
                              f"**Member:** {member.mention}\n**Strikes:** {strikes}\n**Source:** {source}",
                              COLOR_DANGER)
            await self._dm(member,
                           f"You have reached the DIFF restricted threshold with **{strikes} strike(s)**. "
                           "Staff may review your access.")

        if strikes >= CRITICAL_THRESHOLD and "critical_flag" not in flags:
            flags.add("critical_flag")
            await self._alert(guild, "🛑 Critical Moderation Threshold Reached",
                              f"**Member:** {member.mention}\n**Strikes:** {strikes}\n"
                              f"**Source:** {source}\n\nStaff review is recommended immediately.",
                              COLOR_DANGER)
            await self._dm(member,
                           f"You have reached a critical moderation threshold with **{strikes} strike(s)**. "
                           "Staff review may follow.")

        profile["flags"]        = sorted(flags)
        profile["last_updated"] = _utcnow().isoformat()
        data[str(member.id)]    = profile
        self._set_members(data)

    async def _evaluate_host(self, guild: discord.Guild, host: discord.Member, source: str):
        data    = self._hosts()
        profile = data.get(str(host.id))
        if not profile:
            return

        fb_avg       = float(profile["feedback_average"]) if profile["feedback_entries"] > 0 else 5.0
        host_wus     = int(profile["host_writeups"])
        att_avg      = float(profile["attendance_average"]) if profile["hosted_meets"] > 0 else 999.0

        should_flag = (
            (profile["feedback_entries"] > 0 and fb_avg <= HOST_BAD_FEEDBACK_THRESHOLD) or
            (host_wus >= HOST_WRITEUP_THRESHOLD) or
            (profile["hosted_meets"] > 0 and att_avg <= HOST_LOW_ATTENDANCE_THRESHOLD)
        )

        if should_flag and not profile.get("review_flagged", False):
            profile["review_flagged"] = True
            profile["last_updated"]   = _utcnow().isoformat()
            data[str(host.id)]        = profile
            self._set_hosts(data)
            await self._safe_add_role(host, HOST_REVIEW_ROLE_ID, "Flagged for host performance review")
            await self._alert(guild, "📉 Host Review Flagged",
                              (f"**Host:** {host.mention}\n"
                               f"**Feedback Avg:** {profile['feedback_average']}/5\n"
                               f"**Host Write-Ups:** {host_wus}\n"
                               f"**Attendance Avg:** {profile['attendance_average']}\n"
                               f"**Source:** {source}"),
                              COLOR_WARNING)
            await self._dm(host,
                           "Your hosting profile has been flagged for review based on recent "
                           "moderation/performance data.")

    # =========================================================
    # EMBED BUILDERS
    # =========================================================

    def _member_embed(self, member: discord.Member, profile: Dict[str, Any]) -> discord.Embed:
        strikes = int(profile["strikes"])
        color   = COLOR_PRIMARY
        if strikes >= CRITICAL_THRESHOLD:
            color = COLOR_DANGER
        elif strikes >= RESTRICTED_THRESHOLD:
            color = COLOR_DANGER
        elif strikes >= WARNING_THRESHOLD:
            color = COLOR_WARNING

        embed = discord.Embed(title=f"🛡️ Moderation Profile  •  {member}", color=color)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="⚠️ Write-Ups",     value=str(profile["writeups"]),         inline=True)
        embed.add_field(name="🚨 Strikes",        value=str(strikes),                     inline=True)
        embed.add_field(name="📊 Feedback Avg",   value=f"{profile['feedback_average']}/5 ({profile['feedback_entries']} ratings)", inline=True)
        embed.add_field(name="🏟️ Attendance",     value=str(profile["attendance_count"]), inline=True)
        embed.add_field(name="🏁 Hosted Meets",   value=str(profile["hosted_meets"]),     inline=True)
        embed.add_field(name="🚩 Active Flags",   value=", ".join(profile["flags"]) if profile["flags"] else "None", inline=True)
        embed.set_footer(text="Different Meets • Full Moderation System")
        return embed

    def _host_embed(self, host: discord.Member, profile: Dict[str, Any]) -> discord.Embed:
        color = COLOR_DANGER if profile.get("review_flagged") else COLOR_PRIMARY
        embed = discord.Embed(title=f"🏁 Host Performance Profile  •  {host}", color=color)
        embed.set_thumbnail(url=host.display_avatar.url)
        embed.add_field(name="🏁 Hosted Meets",   value=str(profile["hosted_meets"]),       inline=True)
        embed.add_field(name="👥 Attendance Avg", value=str(profile["attendance_average"]),  inline=True)
        embed.add_field(name="📊 Feedback Avg",   value=f"{profile['feedback_average']}/5 ({profile['feedback_entries']} ratings)", inline=True)
        embed.add_field(name="⚠️ Host Write-Ups", value=str(profile["host_writeups"]),       inline=True)
        embed.add_field(name="🔍 Review Flagged", value="🚨 Yes" if profile["review_flagged"] else "✅ No", inline=True)
        embed.set_footer(text="Different Meets • Full Moderation System")
        return embed

    # =========================================================
    # PREFIX COMMANDS — LOOKUP
    # =========================================================

    @commands.command(name="modprofile")
    @commands.has_permissions(manage_guild=True)
    async def mod_profile(self, ctx: commands.Context, member: discord.Member):
        """View a member's full moderation profile.  Usage: !modprofile @member"""
        data    = self._members()
        profile = data.get(str(member.id))
        if not profile:
            await ctx.send(f"No moderation profile found for {member.mention} yet.\n"
                           f"Use `!modsync writeup/strike/attendance @member` to start tracking.")
            return
        await ctx.send(embed=self._member_embed(member, profile))

    @commands.command(name="hostprofile")
    @commands.has_permissions(manage_guild=True)
    async def host_profile(self, ctx: commands.Context, member: discord.Member):
        """View a host's performance profile.  Usage: !hostprofile @member"""
        data    = self._hosts()
        profile = data.get(str(member.id))
        if not profile:
            await ctx.send(f"No host profile found for {member.mention} yet.\n"
                           f"Use `!modsync hostmeet @member <count>` to start tracking.")
            return
        await ctx.send(embed=self._host_embed(member, profile))

    @commands.command(name="hostleaderboard")
    @commands.has_permissions(manage_guild=True)
    async def host_leaderboard(self, ctx: commands.Context):
        """View the top 10 hosts ranked by feedback, attendance, and meets hosted."""
        data = self._hosts()
        if not data:
            await ctx.send("No host data available yet.")
            return

        ranked = sorted(
            data.values(),
            key=lambda p: (float(p["feedback_average"]), float(p["attendance_average"]), int(p["hosted_meets"])),
            reverse=True,
        )[:10]

        lines = []
        for i, p in enumerate(ranked, start=1):
            flag = " 🚨" if p.get("review_flagged") else ""
            lines.append(
                f"**{i}. {p['display_name']}**{flag}  "
                f"— Feedback: {p['feedback_average']}/5 | Att. Avg: {p['attendance_average']} | Meets: {p['hosted_meets']}"
            )

        embed = discord.Embed(
            title       = "🏆 Host Performance Leaderboard",
            description = "\n".join(lines),
            color       = COLOR_SUCCESS,
        )
        embed.set_footer(text="Different Meets • Full Moderation System")
        await ctx.send(embed=embed)

    @commands.command(name="modstats")
    @commands.has_permissions(manage_guild=True)
    async def mod_stats(self, ctx: commands.Context):
        """Show system-wide moderation stats."""
        mdata = self._members()
        hdata = self._hosts()

        total_m      = len(mdata)
        total_h      = len(hdata)
        total_strikes = sum(int(p["strikes"]) for p in mdata.values())
        total_wus     = sum(int(p["writeups"]) for p in mdata.values())
        flagged_m     = sum(1 for p in mdata.values() if p.get("flags"))
        flagged_h     = sum(1 for p in hdata.values() if p.get("review_flagged"))

        embed = discord.Embed(title="📊 Full Moderation Stats", color=COLOR_PRIMARY)
        embed.add_field(name="👥 Member Profiles",   value=str(total_m),       inline=True)
        embed.add_field(name="🏁 Host Profiles",     value=str(total_h),       inline=True)
        embed.add_field(name="⚠️ Total Write-Ups",   value=str(total_wus),     inline=True)
        embed.add_field(name="🚨 Total Strikes",     value=str(total_strikes), inline=True)
        embed.add_field(name="🚩 Flagged Members",   value=str(flagged_m),     inline=True)
        embed.add_field(name="📉 Flagged Hosts",     value=str(flagged_h),     inline=True)
        embed.set_footer(text="Different Meets • Full Moderation System")
        await ctx.send(embed=embed)

    # =========================================================
    # PREFIX COMMANDS — MANUAL SYNC
    # =========================================================

    @commands.group(name="modsync", invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def modsync(self, ctx: commands.Context):
        """Manual moderation sync commands."""
        embed = discord.Embed(title="🔄 Modsync Subcommands", color=COLOR_PRIMARY)
        embed.add_field(
            name="Member",
            value=(
                "`!modsync writeup @m` — register a write-up\n"
                "`!modsync strike @m` — register a strike\n"
                "`!modsync attendance @m` — register attendance\n"
                "`!modsync feedback @m <1-5>` — log feedback rating\n"
            ),
            inline=False,
        )
        embed.add_field(
            name="Host",
            value=(
                "`!modsync hostmeet @m <count>` — register a hosted meet\n"
                "`!modsync hostfeedback @m <1-5>` — log host feedback\n"
                "`!modsync hostwriteup @m` — register a host write-up\n"
            ),
            inline=False,
        )
        embed.set_footer(text="Different Meets • Full Moderation System")
        await ctx.send(embed=embed)

    @modsync.command(name="writeup")
    async def ms_writeup(self, ctx: commands.Context, member: discord.Member):
        await self.register_writeup(ctx.guild, member, source="manual")
        await ctx.send(f"✅ Write-up registered for {member.mention}.", delete_after=8)

    @modsync.command(name="strike")
    async def ms_strike(self, ctx: commands.Context, member: discord.Member):
        await self.register_strike(ctx.guild, member, source="manual")
        await ctx.send(f"✅ Strike registered for {member.mention}.", delete_after=8)

    @modsync.command(name="attendance")
    async def ms_attendance(self, ctx: commands.Context, member: discord.Member):
        await self.register_attendance(ctx.guild, member, source="manual")
        await ctx.send(f"✅ Attendance registered for {member.mention}.", delete_after=8)

    @modsync.command(name="feedback")
    async def ms_feedback(self, ctx: commands.Context, member: discord.Member, rating: float):
        if not (1.0 <= rating <= 5.0):
            await ctx.send("❌ Rating must be between 1 and 5.", delete_after=8)
            return
        await self.register_feedback(ctx.guild, member, rating, source="manual")
        await ctx.send(f"✅ Feedback {rating}/5 registered for {member.mention}.", delete_after=8)

    @modsync.command(name="hostmeet")
    async def ms_hostmeet(self, ctx: commands.Context, member: discord.Member, attendance_count: int = 0):
        await self.register_hosted_meet(ctx.guild, member, attendance_count, source="manual")
        await ctx.send(f"✅ Hosted meet registered for {member.mention} (attendance: {attendance_count}).", delete_after=8)

    @modsync.command(name="hostfeedback")
    async def ms_hostfeedback(self, ctx: commands.Context, member: discord.Member, rating: float):
        if not (1.0 <= rating <= 5.0):
            await ctx.send("❌ Rating must be between 1 and 5.", delete_after=8)
            return
        await self.register_host_feedback(ctx.guild, member, rating, source="manual")
        await ctx.send(f"✅ Host feedback {rating}/5 registered for {member.mention}.", delete_after=8)

    @modsync.command(name="hostwriteup")
    async def ms_hostwriteup(self, ctx: commands.Context, member: discord.Member):
        await self.register_host_writeup(ctx.guild, member, source="manual")
        await ctx.send(f"✅ Host write-up registered for {member.mention}.", delete_after=8)

    # =========================================================
    # PREFIX COMMANDS — MANAGEMENT
    # =========================================================

    @commands.command(name="modclearflags")
    @commands.has_permissions(administrator=True)
    async def mod_clear_flags(self, ctx: commands.Context, member: discord.Member):
        """Clear all moderation flags for a member.  Usage: !modclearflags @member"""
        data    = self._members()
        key     = str(member.id)
        profile = data.get(key)
        if not profile:
            await ctx.send(f"No profile found for {member.mention}.", delete_after=8)
            return
        profile["flags"]        = []
        profile["last_updated"] = _utcnow().isoformat()
        data[key] = profile
        self._set_members(data)
        await ctx.send(f"✅ All moderation flags cleared for {member.mention}.", delete_after=8)

    @commands.command(name="unflaghost")
    @commands.has_permissions(administrator=True)
    async def unflag_host(self, ctx: commands.Context, member: discord.Member):
        """Clear the review flag on a host profile.  Usage: !unflaghost @member"""
        data    = self._hosts()
        key     = str(member.id)
        profile = data.get(key)
        if not profile:
            await ctx.send(f"No host profile found for {member.mention}.", delete_after=8)
            return
        profile["review_flagged"] = False
        profile["last_updated"]   = _utcnow().isoformat()
        data[key] = profile
        self._set_hosts(data)
        await ctx.send(f"✅ Host review flag cleared for {member.mention}.", delete_after=8)

    @commands.command(name="modresetprofile")
    @commands.has_permissions(administrator=True)
    async def mod_reset_profile(self, ctx: commands.Context, member: discord.Member):
        """Completely reset a member's moderation profile.  Usage: !modresetprofile @member"""
        data = self._members()
        key  = str(member.id)
        if key in data:
            data.pop(key)
            self._set_members(data)
        hdata = self._hosts()
        if key in hdata:
            hdata.pop(key)
            self._set_hosts(hdata)
        await ctx.send(f"✅ Moderation profile reset for {member.mention}.", delete_after=8)
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="modhelp")
    @commands.has_permissions(manage_guild=True)
    async def mod_help(self, ctx: commands.Context):
        """Show all full moderation system commands."""
        embed = discord.Embed(title="📋 Full Moderation System Commands", color=COLOR_PRIMARY)
        embed.add_field(
            name="Profiles",
            value=(
                "`!modprofile @m` — Member moderation profile\n"
                "`!hostprofile @m` — Host performance profile\n"
                "`!hostleaderboard` — Top 10 hosts\n"
                "`!modstats` — System-wide stats\n"
            ),
            inline=False,
        )
        embed.add_field(
            name="Manual Sync",
            value=(
                "`!modsync` — Show all sync subcommands\n"
                "`!modsync writeup/strike/attendance/feedback @m`\n"
                "`!modsync hostmeet/hostfeedback/hostwriteup @m`\n"
            ),
            inline=False,
        )
        embed.add_field(
            name="Management *(Admin only)*",
            value=(
                "`!modclearflags @m` — Remove all member flags\n"
                "`!unflaghost @m` — Clear host review flag\n"
                "`!modresetprofile @m` — Wipe a profile entirely\n"
            ),
            inline=False,
        )
        embed.add_field(
            name="⚡ Auto-Alerts (staff-logs)",
            value=(
                f"• **{WARNING_THRESHOLD}+ strikes** → Warning flag\n"
                f"• **{RESTRICTED_THRESHOLD}+ strikes** → Restricted flag\n"
                f"• **{CRITICAL_THRESHOLD}+ strikes** → Critical alert\n"
                f"• Host avg feedback ≤ {HOST_BAD_FEEDBACK_THRESHOLD} or "
                f"≥{HOST_WRITEUP_THRESHOLD} host write-ups → Host review flag\n"
            ),
            inline=False,
        )
        embed.set_footer(text="Different Meets • Full Moderation System")
        await ctx.send(embed=embed)

    # =========================================================
    # TEST EXAMPLE COMMAND
    # =========================================================

    @commands.command(name="posttestexample")
    @commands.has_permissions(administrator=True)
    async def post_test_example(self, ctx: commands.Context):
        """
        Posts a full example walkthrough of every system using the seeded
        test data.  Usage: !posttestexample
        """
        await ctx.message.delete()
        ch = ctx.channel

        # ── header ──────────────────────────────────────────
        header = discord.Embed(
            title       = "🧪 DIFF Bot — Full System Demo",
            description = (
                "This is a live walkthrough of all active systems using realistic "
                "DIFF meet community data.\n\n"
                "**Systems covered:**\n"
                "1️⃣  Manager Hub (All-Time Leaderboard)\n"
                "2️⃣  Season #3 Weekly Standings\n"
                "3️⃣  Manager Write-Up System (5 entries)\n"
                "4️⃣  Member Moderation Profiles\n"
                "5️⃣  Host Performance Leaderboard\n"
                "6️⃣  Full System Stats"
            ),
            color = COLOR_PRIMARY,
        )
        header.set_footer(text="Different Meets • System Demo")
        await ch.send(embed=header)

        # ── 1. manager hub all-time leaderboard ─────────────
        perf_path = DATA_DIR / "manager_performance_stats.json"
        perf_data = _load(perf_path, {})
        ranked_all = sorted(perf_data.items(), key=lambda x: x[1].get("points", 0), reverse=True)

        lb_lines = []
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        for rank, (name, s) in enumerate(ranked_all, 1):
            medal = medals.get(rank, f"**#{rank}**")
            lb_lines.append(
                f"{medal} **{name}** — {s.get('points', 0)} pts | "
                f"{s.get('meets_hosted', 0)} meets | "
                f"{s.get('attendees_total', 0)} attendees"
            )

        e1 = discord.Embed(
            title       = "1️⃣  Manager Hub — All-Time Leaderboard",
            description = "\n".join(lb_lines) if lb_lines else "No data yet.",
            color       = 0xF1C40F,
        )
        e1.set_footer(text="Updated in real-time via !manageradd")
        await ch.send(embed=e1)

        # ── 2. season leaderboard ────────────────────────────
        season_path = DATA_DIR / "manager_season_stats.json"
        meta_path   = DATA_DIR / "manager_season_meta.json"
        seas_data   = _load(season_path, {})
        meta        = _load(meta_path,   {"season_number": 1})
        ranked_seas = sorted(seas_data.items(), key=lambda x: x[1].get("points", 0), reverse=True)

        seas_lines = []
        for rank, (name, s) in enumerate(ranked_seas, 1):
            medal = medals.get(rank, f"**#{rank}**")
            promo = " ⚡ Promo Alert" if s.get("points", 0) >= 25 else ""
            seas_lines.append(
                f"{medal} **{name}** — {s.get('points', 0)} pts this week | "
                f"{s.get('meets_hosted', 0)} meets{promo}"
            )

        e2 = discord.Embed(
            title       = f"2️⃣  Season #{meta.get('season_number', '?')} — Weekly Standings",
            description = "\n".join(seas_lines) if seas_lines else "No data yet.",
            color       = 0x9B59B6,
        )
        e2.add_field(name="Promo Threshold",  value="25 pts", inline=True)
        e2.add_field(name="Reset Command",    value="`!seasonendweek`", inline=True)
        e2.set_footer(text="Resets weekly via !seasonendweek")
        await ch.send(embed=e2)

        # ── 3. write-up entries ──────────────────────────────
        wu_path  = DATA_DIR / "manager_writeups.json"
        str_path = DATA_DIR / "manager_writeup_strikes.json"
        wu_data  = _load(wu_path,  {"counter": 0, "entries": {}})
        str_data = _load(str_path, {})
        entries  = wu_data.get("entries", {})

        type_colors = {
            "Member Write-Up": COLOR_PRIMARY,
            "Host Write-Up":   COLOR_DANGER,
            "Warning Notice":  COLOR_WARNING,
            "Strike Entry":    COLOR_DANGER,
        }
        status_icons = {
            "Active":   "🔴",
            "Resolved": "✅",
            "Removed":  "⬛",
        }

        wu_header = discord.Embed(
            title       = f"3️⃣  Manager Write-Up System — {len(entries)} Entries",
            description = (
                "Each entry below represents a live write-up embed with action buttons "
                "(Mark Resolved / Add Strike / Delete Entry).\n\n"
                "Entries survive bot restarts — buttons recover the write-up ID from the embed title."
            ),
            color = COLOR_WARNING,
        )
        wu_header.add_field(name="Active",   value=str(sum(1 for e in entries.values() if e["status"] == "Active")),   inline=True)
        wu_header.add_field(name="Resolved", value=str(sum(1 for e in entries.values() if e["status"] == "Resolved")), inline=True)
        wu_header.add_field(name="Strike Threshold", value="3 strikes → auto-alert fires to staff-logs", inline=False)
        wu_header.set_footer(text="Panel posted via !postwriteuppanel")
        await ch.send(embed=wu_header)

        for wid, entry in entries.items():
            color  = type_colors.get(entry["writeup_type"], COLOR_PRIMARY)
            s_icon = status_icons.get(entry["status"], "❓")
            e_wu   = discord.Embed(
                title     = f"📋 {entry['writeup_type']} • {wid}",
                color     = COLOR_SUCCESS if entry["status"] == "Resolved" else color,
                timestamp = _utcnow(),
            )
            e_wu.add_field(name="Date",         value=entry["date"],                   inline=True)
            e_wu.add_field(name="Member",        value=entry["member_name"],            inline=True)
            e_wu.add_field(name="PSN",           value=entry["psn"],                   inline=True)
            e_wu.add_field(name="Submitted By",  value=entry["submitted_by"],           inline=True)
            e_wu.add_field(name="Severity",      value=entry["severity"],              inline=True)
            e_wu.add_field(name="Status",        value=f"{s_icon} {entry['status']}",  inline=True)
            e_wu.add_field(name="Reason",        value=entry["reason"][:1024],         inline=False)
            e_wu.add_field(name="Evidence",      value=entry["evidence"][:512],        inline=False)
            e_wu.add_field(name="Strike Count",  value=str(entry.get("strike_count", 0)), inline=True)
            if entry.get("resolved_by"):
                e_wu.add_field(name="Resolved By", value=entry["resolved_by"], inline=True)
            if entry.get("strike_count", 0) >= 3:
                e_wu.add_field(
                    name  = "⚠️ Alert",
                    value = "Strike threshold reached — auto-alert posted to staff-logs",
                    inline= False,
                )
            e_wu.set_footer(text="Different Meets • Manager Write-Up System")
            await ch.send(embed=e_wu)

        # ── 4. member moderation profiles ───────────────────
        mod_data    = self._members()
        flag_colors = {"critical_flag": COLOR_DANGER, "restricted_flag": COLOR_DANGER, "warning_flag": COLOR_WARNING}

        mod_header = discord.Embed(
            title       = f"4️⃣  Full Moderation — {len(mod_data)} Member Profiles",
            description = (
                "Each profile tracks write-ups, strikes, feedback, and attendance.\n"
                "Flags fire automatically when strike thresholds are crossed.\n\n"
                f"⚠️ Warning threshold: **{WARNING_THRESHOLD}+ strikes**\n"
                f"🚨 Restricted threshold: **{RESTRICTED_THRESHOLD}+ strikes**\n"
                f"🛑 Critical threshold: **{CRITICAL_THRESHOLD}+ strikes**"
            ),
            color = COLOR_PRIMARY,
        )
        mod_header.set_footer(text="Use !modprofile @member for individual lookups")
        await ch.send(embed=mod_header)

        for uid, p in mod_data.items():
            strikes = int(p["strikes"])
            flags   = p.get("flags", [])
            if "critical_flag" in flags:
                c = COLOR_DANGER
            elif "restricted_flag" in flags:
                c = COLOR_DANGER
            elif "warning_flag" in flags:
                c = COLOR_WARNING
            else:
                c = COLOR_SUCCESS

            e_m = discord.Embed(
                title = f"🛡️ {p['display_name']}",
                color = c,
            )
            e_m.add_field(name="⚠️ Write-Ups",    value=str(p["writeups"]),         inline=True)
            e_m.add_field(name="🚨 Strikes",       value=str(strikes),               inline=True)
            e_m.add_field(name="📊 Feedback",      value=f"{p['feedback_average']}/5 ({p['feedback_entries']} ratings)", inline=True)
            e_m.add_field(name="🏟️ Attendance",    value=str(p["attendance_count"]), inline=True)
            e_m.add_field(name="🏁 Hosted",        value=str(p["hosted_meets"]),     inline=True)
            e_m.add_field(
                name  = "🚩 Flags",
                value = ", ".join(flags) if flags else "None",
                inline= True,
            )
            if flags:
                e_m.add_field(
                    name  = "🔔 Auto-Actions Fired",
                    value = (
                        ("⚠️ Warning alert\n" if "warning_flag" in flags else "") +
                        ("🚨 Restricted alert\n" if "restricted_flag" in flags else "") +
                        ("🛑 Critical staff alert" if "critical_flag" in flags else "")
                    ).strip() or "—",
                    inline=False,
                )
            e_m.set_footer(text="Different Meets • Full Moderation System")
            await ch.send(embed=e_m)

        # ── 5. host performance leaderboard ─────────────────
        host_data   = self._hosts()
        ranked_host = sorted(
            host_data.values(),
            key=lambda p: (float(p["feedback_average"]), float(p["attendance_average"]), int(p["hosted_meets"])),
            reverse=True,
        )

        host_lines = []
        for rank, p in enumerate(ranked_host, 1):
            medal   = medals.get(rank, f"**#{rank}**")
            flagged = " 🚨 Under Review" if p.get("review_flagged") else ""
            host_lines.append(
                f"{medal} **{p['display_name']}**{flagged}\n"
                f"└─ {p['hosted_meets']} meets | Att. avg: {p['attendance_average']} | "
                f"Feedback: {p['feedback_average']}/5 | Host WUs: {p['host_writeups']}"
            )

        e5 = discord.Embed(
            title       = "5️⃣  Host Performance Leaderboard",
            description = "\n\n".join(host_lines) if host_lines else "No host data yet.",
            color       = COLOR_SUCCESS,
        )
        e5.add_field(
            name  = "Review Flag Triggers",
            value = (
                f"• Feedback avg ≤ {HOST_BAD_FEEDBACK_THRESHOLD}/5\n"
                f"• ≥{HOST_WRITEUP_THRESHOLD} host write-ups\n"
                f"• Attendance avg ≤ {HOST_LOW_ATTENDANCE_THRESHOLD}"
            ),
            inline=False,
        )
        e5.set_footer(text="Use !hostprofile @member for individual lookups")
        await ch.send(embed=e5)

        # ── 6. system summary stats ──────────────────────────
        total_strikes = sum(int(p["strikes"]) for p in mod_data.values())
        total_wus     = sum(int(p["writeups"]) for p in mod_data.values())
        flagged_m     = sum(1 for p in mod_data.values() if p.get("flags"))
        flagged_h     = sum(1 for p in host_data.values() if p.get("review_flagged"))
        wu_total      = wu_data.get("counter", 0)
        wu_active     = sum(1 for e in entries.values() if e["status"] == "Active")

        e6 = discord.Embed(
            title = "6️⃣  Full System Stats",
            color = COLOR_PRIMARY,
        )
        e6.add_field(name="👥 Manager Profiles",   value=str(len(perf_data)),  inline=True)
        e6.add_field(name="🏁 Host Profiles",      value=str(len(host_data)),  inline=True)
        e6.add_field(name="📋 Write-Up Entries",   value=f"{wu_total} total / {wu_active} active", inline=True)
        e6.add_field(name="🚨 Total Strikes",      value=str(total_strikes),   inline=True)
        e6.add_field(name="🚩 Flagged Members",    value=str(flagged_m),       inline=True)
        e6.add_field(name="📉 Hosts Under Review", value=str(flagged_h),       inline=True)
        e6.add_field(
            name  = "Data Files",
            value = "`diff_data/` — all JSON, persists across restarts",
            inline=False,
        )
        e6.add_field(
            name  = "Active Cogs",
            value = (
                "`diff_manager_hub` · `diff_manager_season` · `diff_manager_writeups`\n"
                "`diff_full_moderation` · `diff_feedback_system`\n"
                "`diff_welcome_join` · `partner_expansion` · `partner_request_system`"
            ),
            inline=False,
        )
        e6.set_footer(text="Different Meets • Full System Demo Complete")
        await ch.send(embed=e6)


# =========================================================
# SETUP
# =========================================================

async def setup(bot: commands.Bot):
    await bot.add_cog(FullModerationSystem(bot))
