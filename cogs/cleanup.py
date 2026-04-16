"""
cogs/cleanup.py
Smart Auto Cleanup + Recovery cog for Different Meets V2.

Background loop scans every 6h.  Staff commands are prefix-only.
"""

import asyncio
import logging
import sqlite3
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import discord
from discord.ext import commands, tasks

from utils.cleanup_logic import (
    CLEANUP_CONFIG,
    FLAG_AT_RISK,
    FLAG_GHOST,
    FLAG_REVIEW,
    FLAG_SAFE,
    clear_flag,
    get_all_active_flags,
    get_flag,
    get_recoveries,
    get_review_queue,
    get_stats,
    init_db,
    is_exempt,
    log_action,
    mark_recovered,
    record_reminder_sent,
    set_flag,
    set_review_decision,
    should_send_reminder,
)
from utils.recovery_tracker import log_recovery_event

log = logging.getLogger("diff_cleanup")

# ── Key IDs (mirror bot.py) ───────────────────────────────────────────────────
GUILD_ID         = 850386896509337710
STAFF_LOGS_ID    = 1485265848099799163
VERIFIED_ROLE_ID = 1141424243616256032

STAFF_ROLES = {"Leader", "Co-Leader", "Manager", "Moderator", "Admin"}

_TIER_ICONS: dict[str, str] = {
    "Strong":  "💚",
    "Active":  "🔵",
    "At Risk": "🟡",
    "Ghost":   "🔴",
}

# ── Embed colours ─────────────────────────────────────────────────────────────
_C_GREEN  = discord.Color.from_rgb(30,  160, 60)
_C_YELLOW = discord.Color.from_rgb(210, 150, 0)
_C_RED    = discord.Color.from_rgb(200, 30,  30)
_C_BLUE   = discord.Color.from_rgb(30,  100, 200)


# ══════════════════════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def _activity_row(user_id: int):
    """Read one member_activity row from diff_activity.db (read-only)."""
    db_path = Path("diff_data/diff_activity.db")
    if not db_path.exists():
        return None
    try:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM member_activity WHERE user_id=?", (user_id,)
        ).fetchone()
        conn.close()
        return row
    except Exception as _e:
        log.error("[Cleanup] _activity_row(%s): %s", user_id, _e)
        return None


def _days_since(ts) -> int:
    """Full days since a UNIX timestamp. Returns 999 if ts is None."""
    if ts is None:
        return 999
    return max(0, int((time.time() - ts) / 86400))


# ══════════════════════════════════════════════════════════════════════════════
# COG
# ══════════════════════════════════════════════════════════════════════════════
class CleanupCog(commands.Cog, name="Cleanup"):
    """Smart Auto Cleanup + Recovery System."""

    def __init__(self, bot: commands.Bot):
        self.bot      = bot
        self.scanning = False
        init_db()
        self.cleanup_scan_loop.start()

    def cog_unload(self):
        self.cleanup_scan_loop.cancel()

    # ── Staff log ─────────────────────────────────────────────────────────────
    async def _log_staff(self, embed: discord.Embed) -> None:
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return
        ch = guild.get_channel(STAFF_LOGS_ID)
        if ch:
            try:
                await ch.send(embed=embed)
            except discord.HTTPException as e:
                log.error("[Cleanup] Staff log failed: %s", e)

    # ── DM helper ────────────────────────────────────────────────────────────
    async def _send_dm(self, member: discord.Member) -> bool:
        """Send a DIFF-styled re-engagement DM. Returns True on success."""
        try:
            embed = discord.Embed(
                title="DIFF CHECK-IN ✅",
                description=(
                    "You've been inactive for a bit. If you still want to be part of "
                    "**Different Meets**, make sure you:\n\n"
                    "• ✅  Get verified\n"
                    "• 🚗  Check the meet channels\n"
                    "• 🎮  Pull up to the next meet\n\n"
                    "*Need help? Reach out to staff.*"
                ),
                color=_C_BLUE,
                timestamp=datetime.now(timezone.utc),
            )
            embed.set_footer(text="— Different Meets Staff")
            await member.send(embed=embed)
            return True
        except (discord.Forbidden, discord.HTTPException):
            return False

    # ── Core scan ────────────────────────────────────────────────────────────
    async def _scan_logic(self) -> dict:
        """Full member scan. Returns counts dict."""
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return {}

        now  = time.time()
        cfg  = CLEANUP_CONFIG
        vr   = guild.get_role(VERIFIED_ROLE_ID)
        cnts = dict(
            scanned=0, flagged_at_risk=0, flagged_ghost=0,
            reminders_sent=0, escalated=0, recovered=0, skipped=0,
        )

        for member in guild.members:
            if member.bot:
                continue
            if is_exempt(member):
                cnts["skipped"] += 1
                continue

            cnts["scanned"] += 1
            flag = get_flag(member.id)
            act  = _activity_row(member.id)

            # ── Recovery: were they recently active? ──────────────────────
            if flag and not flag["recovered"]:
                last_act = None
                if act:
                    last_act = act["last_message"] or act["last_vc"]
                if last_act and (now - last_act) < 48 * 3600:
                    mark_recovered(member.id)
                    log_recovery_event(member.id, "message")
                    cnts["recovered"] += 1
                    e = discord.Embed(
                        title="✅ Member Recovered",
                        description=(
                            f"**{member.display_name}** (`{member.id}`) became active "
                            "and has been removed from the cleanup queue."
                        ),
                        color=_C_GREEN,
                        timestamp=datetime.now(timezone.utc),
                    )
                    e.set_footer(text="Different Meets • Auto Cleanup — Recovery")
                    await self._log_staff(e)
                    continue

            # ── Build member metrics ──────────────────────────────────────
            last_ts    = (act["last_message"] or act["last_vc"]) if act else None
            days_inact = _days_since(last_ts)
            score      = (
                int(act["last_health_score"])
                if act and act["last_health_score"] is not None
                else None
            )
            tier       = (act["health_tier"] if act else None) or "Unknown"
            meets      = int(act["meet_attendance_count"] or 0) if act else 0
            verified   = (vr in member.roles) if vr else False

            # ── Determine flag type ───────────────────────────────────────
            flag_type: str | None = None
            reasons:   list[str]  = []

            if score is not None:
                if (score <= cfg["scan_score_ghost_max"]
                        and days_inact >= cfg["inactivity_days_ghost"]):
                    flag_type = FLAG_GHOST
                    reasons.append(f"Score {score} (Ghost tier), inactive {days_inact}d")
                elif (score <= cfg["scan_score_at_risk_max"]
                        and days_inact >= cfg["inactivity_days_at_risk"]):
                    flag_type = FLAG_AT_RISK
                    reasons.append(f"Score {score} (At Risk tier), inactive {days_inact}d")

            if not verified and act and act["join_ts"]:
                join_days = (now - act["join_ts"]) / 86400
                if join_days >= cfg["min_join_age_days"]:
                    reasons.append("Not verified")
                    if flag_type is None:
                        flag_type = FLAG_AT_RISK

            if not flag_type:
                continue

            reason_str = "; ".join(reasons)
            set_flag(
                member.id, member.display_name, flag_type, reason_str,
                score or 0, tier, days_inact, verified, meets,
            )

            if flag_type == FLAG_GHOST:
                cnts["flagged_ghost"] += 1
            else:
                cnts["flagged_at_risk"] += 1

            # ── Grace period check — escalate if expired ──────────────────
            refreshed = get_flag(member.id)
            if (refreshed
                    and refreshed["grace_expires_at"] < now
                    and refreshed["flag_type"] != FLAG_REVIEW):
                set_flag(
                    member.id, member.display_name, FLAG_REVIEW, reason_str,
                    score or 0, tier, days_inact, verified, meets,
                )
                cnts["escalated"] += 1
                e = discord.Embed(
                    title="⚠️ Moved to Cleanup Review",
                    color=_C_RED,
                    timestamp=datetime.now(timezone.utc),
                )
                e.set_thumbnail(url=member.display_avatar.url)
                e.add_field(name="Member",   value=f"{member.mention} (`{member.id}`)", inline=True)
                e.add_field(name="Score",    value=str(score or "N/A"),                 inline=True)
                e.add_field(name="Tier",     value=tier,                                inline=True)
                e.add_field(name="Inactive", value=f"{days_inact}d",                    inline=True)
                e.add_field(name="Verified", value="✅" if verified else "❌",           inline=True)
                e.add_field(name="Meets",    value=str(meets),                          inline=True)
                e.add_field(name="Reason",   value=reason_str,                          inline=False)
                e.set_footer(text="Different Meets • Auto Cleanup — use !cleanupqueue to review")
                await self._log_staff(e)
                await asyncio.sleep(0.5)
                continue

            # ── Send DM reminder ──────────────────────────────────────────
            if cfg["dm_reminders_enabled"] and should_send_reminder(member.id):
                sent = await self._send_dm(member)
                if sent:
                    record_reminder_sent(member.id)
                    cnts["reminders_sent"] += 1
                    e = discord.Embed(
                        title="📩 Re-engagement DM Sent",
                        description=(
                            f"Sent check-in DM to **{member.display_name}** (`{member.id}`)."
                        ),
                        color=_C_BLUE,
                        timestamp=datetime.now(timezone.utc),
                    )
                    e.add_field(name="Flag",     value=flag_type,        inline=True)
                    e.add_field(name="Inactive", value=f"{days_inact}d", inline=True)
                    e.set_footer(text="Different Meets • Auto Cleanup")
                    await self._log_staff(e)
                await asyncio.sleep(1.5)

            # ── Log new flags to staff ────────────────────────────────────
            if not flag:
                icon = "👻" if flag_type == FLAG_GHOST else "🟡"
                e = discord.Embed(
                    title=f"{icon} Member Flagged — {flag_type}",
                    color=_C_RED if flag_type == FLAG_GHOST else _C_YELLOW,
                    timestamp=datetime.now(timezone.utc),
                )
                e.set_thumbnail(url=member.display_avatar.url)
                e.add_field(name="Member",   value=f"{member.mention} (`{member.id}`)", inline=True)
                e.add_field(name="Score",    value=str(score or "N/A"),                 inline=True)
                e.add_field(name="Inactive", value=f"{days_inact}d",                    inline=True)
                e.add_field(name="Reason",   value=reason_str,                          inline=False)
                e.set_footer(text="Different Meets • Auto Cleanup")
                await self._log_staff(e)

            await asyncio.sleep(0.1)

        return cnts

    # ── Background loop ───────────────────────────────────────────────────────
    @tasks.loop(hours=6)
    async def cleanup_scan_loop(self):
        if self.scanning:
            return
        self.scanning = True
        try:
            counts = await asyncio.wait_for(self._scan_logic(), timeout=300)
            log.info("[CleanupScan] Complete: %s", counts)
        except asyncio.TimeoutError:
            log.error("[CleanupScan] Timed out (300s)")
        except Exception:
            log.error("[CleanupScan] Unhandled error:\n%s", traceback.format_exc())
        finally:
            self.scanning = False

    @cleanup_scan_loop.before_loop
    async def _before_scan(self):
        await self.bot.wait_until_ready()

    @cleanup_scan_loop.error
    async def _scan_error(self, error: Exception):
        log.error("[CleanupScan] Loop error: %s", error, exc_info=True)
        self.scanning = False

    # ── Recovery listeners ────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        flag = get_flag(message.author.id)
        if flag and not flag["recovered"]:
            mark_recovered(message.author.id)
            log_recovery_event(message.author.id, "message")
            e = discord.Embed(
                title="✅ Member Recovered — Chat Activity",
                description=(
                    f"**{message.author.display_name}** sent a message "
                    "and has been marked as recovered."
                ),
                color=_C_GREEN,
                timestamp=datetime.now(timezone.utc),
            )
            e.set_footer(text="Different Meets • Auto Cleanup — Recovery")
            await self._log_staff(e)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after:  discord.VoiceState,
    ):
        if member.bot:
            return
        if after.channel and not before.channel:
            flag = get_flag(member.id)
            if flag and not flag["recovered"]:
                mark_recovered(member.id)
                log_recovery_event(member.id, "vc_join")
                e = discord.Embed(
                    title="✅ Member Recovered — VC Activity",
                    description=(
                        f"**{member.display_name}** joined voice "
                        "and has been marked as recovered."
                    ),
                    color=_C_GREEN,
                    timestamp=datetime.now(timezone.utc),
                )
                e.set_footer(text="Different Meets • Auto Cleanup — Recovery")
                await self._log_staff(e)

    # ══════════════════════════════════════════════════════════════════════════
    # PREFIX COMMANDS
    # ══════════════════════════════════════════════════════════════════════════

    @commands.command(name="cleanupscan", aliases=["runscan", "forcescan"])
    @commands.has_any_role("Leader", "Co-Leader", "Manager", "Moderator", "Admin")
    async def cmd_cleanupscan(self, ctx: commands.Context):
        """Manually run the cleanup scan. Staff only."""
        if self.scanning:
            return await ctx.send("⏳ A scan is already running.", delete_after=8)
        msg = await ctx.send("🔍 Running cleanup scan — this may take a moment...")
        self.scanning = True
        try:
            counts = await asyncio.wait_for(self._scan_logic(), timeout=300)
        except asyncio.TimeoutError:
            return await msg.edit(content="❌ Scan timed out (5 min limit).")
        except Exception as e:
            return await msg.edit(content=f"❌ Scan failed: `{e}`")
        finally:
            self.scanning = False

        embed = discord.Embed(
            title="🔍 Cleanup Scan Complete",
            color=_C_BLUE,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="Members Scanned",     value=str(counts.get("scanned", 0)),         inline=True)
        embed.add_field(name="🟡 At Risk Flagged",  value=str(counts.get("flagged_at_risk", 0)),  inline=True)
        embed.add_field(name="🔴 Ghost Flagged",    value=str(counts.get("flagged_ghost", 0)),    inline=True)
        embed.add_field(name="📩 Reminders Sent",   value=str(counts.get("reminders_sent", 0)),   inline=True)
        embed.add_field(name="⚠️ Escalated",        value=str(counts.get("escalated", 0)),        inline=True)
        embed.add_field(name="✅ Recovered",         value=str(counts.get("recovered", 0)),        inline=True)
        embed.add_field(name="🚫 Skipped (exempt)", value=str(counts.get("skipped", 0)),          inline=True)
        embed.set_footer(text="Different Meets • Auto Cleanup")
        await msg.edit(content=None, embed=embed)

    @commands.command(name="cleanupqueue", aliases=["reviewqueue", "cqueue"])
    @commands.has_any_role("Leader", "Co-Leader", "Manager", "Moderator", "Admin")
    async def cmd_cleanupqueue(self, ctx: commands.Context):
        """Show members waiting for staff review. Staff only."""
        rows = get_review_queue()
        if not rows:
            return await ctx.send(embed=discord.Embed(
                title="✅ Queue Empty",
                description="No members are currently in the cleanup review queue.",
                color=_C_GREEN,
                timestamp=datetime.now(timezone.utc),
            ))

        now   = time.time()
        lines: list[str] = []
        for row in rows[:15]:
            member      = ctx.guild.get_member(row["user_id"])
            name        = member.mention if member else f"`{row['user_id']}`"
            display     = row["display_name"] or "Unknown"
            t_icon      = _TIER_ICONS.get(row["health_tier"] or "", "❓")
            flagged_ago = int((now - row["flagged_at"]) / 86400) if row["flagged_at"] else "?"
            verified    = "✅" if row["is_verified"] else "❌"
            lines.append(
                f"{t_icon} **{display}** {name}\n"
                f"  Score **{row['health_score']}** | "
                f"Inactive **{row['days_inactive']}d** | "
                f"Verified {verified} | "
                f"Flagged **{flagged_ago}d** ago | "
                f"Reminders **{row['reminders_sent']}**"
            )

        embed = discord.Embed(
            title=f"⚠️ Cleanup Review Queue — {len(rows)} member(s)",
            description="\n\n".join(lines),
            color=_C_RED,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(
            name="Quick Actions",
            value=(
                "`!healthscore @user` — full health breakdown\n"
                "`!clearflag @user` — remove flag\n"
                "`!flagmember @user` — manually flag someone\n"
                "`!memberjourney @user` — see their server journey"
            ),
            inline=False,
        )
        embed.set_footer(text="Different Meets • Auto Cleanup — Staff Review Required")
        await ctx.send(embed=embed)

    @commands.command(name="recoveries", aliases=["recovered", "recoveredmembers"])
    @commands.has_any_role("Leader", "Co-Leader", "Manager", "Moderator", "Admin")
    async def cmd_recoveries(self, ctx: commands.Context):
        """Show recently recovered members. Staff only."""
        rows = get_recoveries()
        if not rows:
            return await ctx.send(embed=discord.Embed(
                title="No Recoveries Yet",
                description="No members have been flagged and recovered yet.",
                color=_C_BLUE,
                timestamp=datetime.now(timezone.utc),
            ))

        lines: list[str] = []
        for row in rows[:15]:
            member  = ctx.guild.get_member(row["user_id"])
            display = (
                member.display_name if member
                else (row["display_name"] or str(row["user_id"]))
            )
            rec_dt = (
                datetime.fromtimestamp(row["recovered_at"], tz=timezone.utc).strftime("%b %d")
                if row["recovered_at"] else "?"
            )
            lines.append(
                f"✅ **{display}** — score **{row['health_score']}** | "
                f"recovered **{rec_dt}** | _{row['reason'] or 'N/A'}_"
            )

        embed = discord.Embed(
            title=f"♻️ Recovered Members — {len(rows)} total",
            description="\n".join(lines),
            color=_C_GREEN,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_footer(text="Different Meets • Auto Cleanup — Recovery Tracking")
        await ctx.send(embed=embed)

    @commands.command(name="flagmember", aliases=["manuallyflag", "addflag"])
    @commands.has_any_role("Leader", "Co-Leader", "Manager", "Moderator", "Admin")
    async def cmd_flagmember(self, ctx: commands.Context, target: discord.Member):
        """Manually flag a member for cleanup review. Staff only."""
        if is_exempt(target):
            return await ctx.send(
                f"❌ **{target.display_name}** is exempt from cleanup and cannot be flagged.",
                delete_after=10,
            )

        act      = _activity_row(target.id)
        score    = int(act["last_health_score"] or 0) if act and act["last_health_score"] is not None else 0
        tier     = (act["health_tier"] if act else None) or "Unknown"
        meets    = int(act["meet_attendance_count"] or 0) if act else 0
        verified = any(r.id == VERIFIED_ROLE_ID for r in target.roles)
        last_ts  = (act["last_message"] or act["last_vc"]) if act else None
        days_in  = _days_since(last_ts)

        set_flag(
            target.id, target.display_name, FLAG_REVIEW,
            f"Manually flagged by {ctx.author.display_name}",
            score, tier, days_in, verified, meets,
        )
        log_action(target.id, target.display_name, "Manually Flagged", ctx.author.display_name)

        embed = discord.Embed(
            title="🚩 Member Flagged for Review",
            description=f"**{target.display_name}** has been added to the cleanup review queue.",
            color=_C_RED,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="Score",      value=str(score),               inline=True)
        embed.add_field(name="Tier",       value=tier,                     inline=True)
        embed.add_field(name="Flagged by", value=ctx.author.display_name,  inline=True)
        embed.set_footer(text="Different Meets • Auto Cleanup")
        await ctx.send(embed=embed)
        await self._log_staff(embed)

    @commands.command(name="clearflag", aliases=["removeflag", "unflag"])
    @commands.has_any_role("Leader", "Co-Leader", "Manager", "Moderator", "Admin")
    async def cmd_clearflag(self, ctx: commands.Context, target: discord.Member):
        """Remove a member's cleanup flag. Staff only."""
        removed = clear_flag(target.id)
        if not removed:
            return await ctx.send(
                f"ℹ️ **{target.display_name}** has no active cleanup flag.",
                delete_after=8,
            )
        log_action(target.id, target.display_name, "Flag Cleared", ctx.author.display_name)

        embed = discord.Embed(
            title="✅ Flag Cleared",
            description=(
                f"**{target.display_name}**'s cleanup flag has been removed "
                f"by {ctx.author.mention}."
            ),
            color=_C_GREEN,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_footer(text="Different Meets • Auto Cleanup")
        await ctx.send(embed=embed)
        await self._log_staff(embed)

    @commands.command(name="cleanupstats", aliases=["cstats", "flagstats"])
    @commands.has_any_role("Leader", "Co-Leader", "Manager", "Moderator", "Admin")
    async def cmd_cleanupstats(self, ctx: commands.Context):
        """Show overall cleanup stats and current config. Staff only."""
        stats = get_stats()
        cfg   = CLEANUP_CONFIG

        embed = discord.Embed(
            title="🧹 Auto Cleanup System — Stats",
            color=_C_BLUE,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(
            name="📊 Member Status",
            value=(
                f"Total Flagged:     **{stats['total_flagged']}**\n"
                f"🟡 At Risk:         **{stats['at_risk']}**\n"
                f"🔴 Ghost:           **{stats['ghost']}**\n"
                f"⚠️ In Review:       **{stats['in_review']}**\n"
                f"✅ Recovered:        **{stats['recovered']}**\n"
                f"💤 Still Inactive:  **{stats['still_inactive']}**\n"
                f"🗑️ Removed:         **{stats['removed']}**"
            ),
            inline=False,
        )
        embed.add_field(
            name="⚙️ Current Config",
            value=(
                f"DM Reminders:      {'✅' if cfg['dm_reminders_enabled'] else '❌'}\n"
                f"Auto Kick:         {'✅' if cfg['auto_kick_enabled'] else '❌'}\n"
                f"Staff Review Req:  {'✅' if cfg['require_staff_review'] else '❌'}\n"
                f"Grace — At Risk:   **{cfg['grace_period_at_risk']}d**\n"
                f"Grace — Ghost:     **{cfg['grace_period_ghost']}d**\n"
                f"Min Join Age:      **{cfg['min_join_age_days']}d**\n"
                f"Max Reminders:     **{cfg['max_reminders']}**\n"
                f"Reminder Cooldown: **{cfg['reminder_cooldown_days']}d**"
            ),
            inline=False,
        )
        embed.set_footer(text="Different Meets • Auto Cleanup System")
        await ctx.send(embed=embed)


# ══════════════════════════════════════════════════════════════════════════════
async def setup(bot: commands.Bot):
    await bot.add_cog(CleanupCog(bot))
