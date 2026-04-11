from __future__ import annotations

import json
import re
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

# Set to a channel ID or leave 0 to fall back to the command's own channel
STAFF_DASHBOARD_CHANNEL_ID = 0
APPEAL_PANEL_CHANNEL_ID    = 0
APPEAL_REVIEW_CHANNEL_ID   = 1485265848099799163   # staff-logs
STAFF_INSIGHTS_CHANNEL_ID  = 1485265848099799163   # staff-logs

STAFF_ROLE_IDS: list[int] = []  # optional extra staff role IDs

WARNING_ROLE_ID     = 0
RESTRICTED_ROLE_ID  = 0
HOST_REVIEW_ROLE_ID = 0

COLOR_PRIMARY = 0x1F6FEB
COLOR_SUCCESS = 0x2ECC71
COLOR_WARNING = 0xF39C12
COLOR_DANGER  = 0xE74C3C
COLOR_MUTED   = 0x95A5A6

DATA_DIR           = Path("diff_data")
MOD_PROFILES_FILE  = DATA_DIR / "moderation_profiles.json"
HOST_PROFILES_FILE = DATA_DIR / "host_performance_profiles.json"
APPEALS_FILE       = DATA_DIR / "appeals_system.json"

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

def _has_access(member: discord.Member) -> bool:
    if member.guild_permissions.manage_guild or member.guild_permissions.administrator:
        return True
    role_ids = {r.id for r in member.roles}
    return any(rid in role_ids for rid in STAFF_ROLE_IDS if rid)

def _appeal_id_from_embed(interaction: discord.Interaction) -> str:
    """Recover APL-XXXX from the embed title after a restart."""
    if interaction.message and interaction.message.embeds:
        title = interaction.message.embeds[0].title or ""
        m = re.search(r"(APL-\d+)", title)
        if m:
            return m.group(1)
    return ""

# =========================================================
# MODALS
# =========================================================

class AppealModal(discord.ui.Modal, title="DIFF Appeal Form"):
    writeup_id_field = discord.ui.TextInput(
        label="Write-Up ID / Strike ID",
        placeholder="Example: WU-0001",
        max_length=30,
        required=True,
    )
    reason_field = discord.ui.TextInput(
        label="Why are you appealing?",
        placeholder="Explain your side clearly and respectfully.",
        style=discord.TextStyle.paragraph,
        max_length=1400,
        required=True,
    )
    evidence_field = discord.ui.TextInput(
        label="Evidence Link",
        placeholder="Clip, screenshot, message link, etc.",
        max_length=400,
        required=False,
    )

    def __init__(self, cog: "StaffDashboardSystem"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        evidence = str(self.evidence_field).strip()
        await self.cog.submit_appeal(
            interaction = interaction,
            writeup_id  = str(self.writeup_id_field).strip().upper(),
            reason      = str(self.reason_field).strip(),
            evidence    = evidence if evidence else "No evidence provided",
        )


class ProfileLookupModal(discord.ui.Modal, title="View Member Moderation Profile"):
    user_id_field = discord.ui.TextInput(
        label="Discord User ID",
        placeholder="Right-click member → Copy ID",
        max_length=30,
        required=True,
    )

    def __init__(self, cog: "StaffDashboardSystem"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.send_member_profile_lookup(interaction, str(self.user_id_field).strip())


class HostLookupModal(discord.ui.Modal, title="View Host Profile"):
    user_id_field = discord.ui.TextInput(
        label="Discord User ID",
        placeholder="Right-click member → Copy ID",
        max_length=30,
        required=True,
    )

    def __init__(self, cog: "StaffDashboardSystem"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.send_host_profile_lookup(interaction, str(self.user_id_field).strip())


class PunishmentModal(discord.ui.Modal, title="Approve Punishment"):
    user_id_field = discord.ui.TextInput(
        label="Discord User ID",
        placeholder="Right-click member → Copy ID",
        max_length=30,
        required=True,
    )
    punishment_type_field = discord.ui.TextInput(
        label="Punishment Type",
        placeholder="warning  or  restricted",
        max_length=30,
        required=True,
    )
    reason_field = discord.ui.TextInput(
        label="Reason",
        placeholder="Why is this punishment being applied?",
        style=discord.TextStyle.paragraph,
        max_length=500,
        required=True,
    )

    def __init__(self, cog: "StaffDashboardSystem"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.apply_punishment(
            interaction,
            str(self.user_id_field).strip(),
            str(self.punishment_type_field).strip().lower(),
            str(self.reason_field).strip(),
        )


class ResetStrikesModal(discord.ui.Modal, title="Reset Member Strikes"):
    user_id_field = discord.ui.TextInput(
        label="Discord User ID",
        placeholder="Right-click member → Copy ID",
        max_length=30,
        required=True,
    )
    reason_field = discord.ui.TextInput(
        label="Reset Reason",
        placeholder="Why are the strikes being reset?",
        style=discord.TextStyle.paragraph,
        max_length=500,
        required=True,
    )

    def __init__(self, cog: "StaffDashboardSystem"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.reset_member_strikes(
            interaction,
            str(self.user_id_field).strip(),
            str(self.reason_field).strip(),
        )


class ReviewHostModal(discord.ui.Modal, title="Review Flagged Host"):
    user_id_field = discord.ui.TextInput(
        label="Host Discord User ID",
        placeholder="Right-click member → Copy ID",
        max_length=30,
        required=True,
    )
    action_field = discord.ui.TextInput(
        label="Action",
        placeholder="clear  or  keep",
        max_length=20,
        required=True,
    )
    note_field = discord.ui.TextInput(
        label="Review Note",
        placeholder="Explain the decision.",
        style=discord.TextStyle.paragraph,
        max_length=500,
        required=True,
    )

    def __init__(self, cog: "StaffDashboardSystem"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.review_flagged_host(
            interaction,
            str(self.user_id_field).strip(),
            str(self.action_field).strip().lower(),
            str(self.note_field).strip(),
        )

# =========================================================
# VIEWS
# =========================================================

class StaffDashboardView(discord.ui.View):
    def __init__(self, cog: "StaffDashboardSystem"):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="View Member Profile", style=discord.ButtonStyle.primary,
                       emoji="👤", custom_id="diff_dashboard_profiles")
    async def view_profiles(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not _has_access(interaction.user):
            await interaction.response.send_message("Staff access required.", ephemeral=True)
            return
        await interaction.response.send_modal(ProfileLookupModal(self.cog))

    @discord.ui.button(label="View Host Profile", style=discord.ButtonStyle.primary,
                       emoji="🏁", custom_id="diff_dashboard_host_profiles")
    async def view_host_profiles(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not _has_access(interaction.user):
            await interaction.response.send_message("Staff access required.", ephemeral=True)
            return
        await interaction.response.send_modal(HostLookupModal(self.cog))

    @discord.ui.button(label="Approve Punishment", style=discord.ButtonStyle.danger,
                       emoji="⚠️", custom_id="diff_dashboard_punish")
    async def approve_punishments(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not _has_access(interaction.user):
            await interaction.response.send_message("Staff access required.", ephemeral=True)
            return
        await interaction.response.send_modal(PunishmentModal(self.cog))

    @discord.ui.button(label="Reset Strikes", style=discord.ButtonStyle.secondary,
                       emoji="🔄", custom_id="diff_dashboard_reset_strikes")
    async def reset_strikes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not _has_access(interaction.user):
            await interaction.response.send_message("Staff access required.", ephemeral=True)
            return
        await interaction.response.send_modal(ResetStrikesModal(self.cog))

    @discord.ui.button(label="Review Flagged Host", style=discord.ButtonStyle.success,
                       emoji="📉", custom_id="diff_dashboard_review_hosts")
    async def review_flagged_hosts(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not _has_access(interaction.user):
            await interaction.response.send_message("Staff access required.", ephemeral=True)
            return
        await interaction.response.send_modal(ReviewHostModal(self.cog))


class AppealPanelView(discord.ui.View):
    def __init__(self, cog: "StaffDashboardSystem"):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Submit an Appeal", style=discord.ButtonStyle.primary,
                       emoji="🧾", custom_id="diff_submit_appeal")
    async def submit_appeal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AppealModal(self.cog))


class AppealReviewView(discord.ui.View):
    """
    Persistent view on appeal review embeds.
    appeal_id is passed when first posting; after a restart it is
    recovered from the embed title via _appeal_id_from_embed().
    """
    def __init__(self, cog: "StaffDashboardSystem", appeal_id: str = ""):
        super().__init__(timeout=None)
        self.cog       = cog
        self.appeal_id = appeal_id

    def _aid(self, interaction: discord.Interaction) -> str:
        return self.appeal_id or _appeal_id_from_embed(interaction)

    @discord.ui.button(label="Accept Appeal", style=discord.ButtonStyle.success,
                       emoji="✅", custom_id="diff_appeal_accept")
    async def accept_appeal(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not _has_access(interaction.user):
            await interaction.response.send_message("Staff access required.", ephemeral=True)
            return
        await self.cog.review_appeal(interaction, self._aid(interaction), accepted=True)

    @discord.ui.button(label="Deny Appeal", style=discord.ButtonStyle.danger,
                       emoji="❌", custom_id="diff_appeal_deny")
    async def deny_appeal(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not _has_access(interaction.user):
            await interaction.response.send_message("Staff access required.", ephemeral=True)
            return
        await self.cog.review_appeal(interaction, self._aid(interaction), accepted=False)

# =========================================================
# COG
# =========================================================

class StaffDashboardSystem(commands.Cog, name="StaffDashboardSystem"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        _load(APPEALS_FILE, {"counter": 0, "entries": {}})
        self.bot.add_view(StaffDashboardView(self))
        self.bot.add_view(AppealPanelView(self))
        self.bot.add_view(AppealReviewView(self))

    @commands.Cog.listener()
    async def on_ready(self):
        print("[StaffDashboardSystem] Cog ready.")

    # ── storage ──────────────────────────────────────────────

    def _members(self) -> Dict[str, Any]:
        return _load(MOD_PROFILES_FILE,  {})

    def _set_members(self, data: Dict[str, Any]) -> None:
        _save(MOD_PROFILES_FILE, data)

    def _hosts(self) -> Dict[str, Any]:
        return _load(HOST_PROFILES_FILE, {})

    def _set_hosts(self, data: Dict[str, Any]) -> None:
        _save(HOST_PROFILES_FILE, data)

    def _appeals(self) -> Dict[str, Any]:
        return _load(APPEALS_FILE, {"counter": 0, "entries": {}})

    def _set_appeals(self, data: Dict[str, Any]) -> None:
        _save(APPEALS_FILE, data)

    def _next_appeal_id(self) -> str:
        data = self._appeals()
        data["counter"] += 1
        self._set_appeals(data)
        return f"APL-{data['counter']:04d}"

    # ── insights ─────────────────────────────────────────────

    def _member_insight(self, profile: Dict[str, Any]) -> str:
        strikes  = int(profile.get("strikes", 0))
        writeups = int(profile.get("writeups", 0))
        flags    = profile.get("flags", [])
        if strikes >= 4 or writeups >= 5:
            return "🔴 High-risk — recommend immediate staff review."
        if strikes >= 2 or writeups >= 3 or flags:
            return "🟡 Rising moderation pattern — monitor closely."
        return "🟢 Low-risk based on current moderation data."

    def _host_insight(self, profile: Dict[str, Any]) -> str:
        fb_avg  = float(profile.get("feedback_average", 0))
        wus     = int(profile.get("host_writeups", 0))
        att_avg = float(profile.get("attendance_average", 0))
        hosted  = int(profile.get("hosted_meets", 0))
        if (hosted >= 2 and fb_avg and fb_avg <= 2.5) or wus >= 2:
            return "🔴 Declining performance — host review recommended."
        if hosted >= 2 and att_avg <= 3:
            return "🟡 Struggling with turnout — may need support."
        return "🟢 Stable based on current performance data."

    # ── embed builders ────────────────────────────────────────

    def _dashboard_embed(self) -> discord.Embed:
        data      = self._members()
        host_data = self._hosts()
        appeal_data = self._appeals()

        total_m   = len(data)
        flagged_m = sum(1 for p in data.values() if p.get("flags"))
        flagged_h = sum(1 for p in host_data.values() if p.get("review_flagged"))
        pending_a = sum(1 for e in appeal_data["entries"].values() if e["status"] == "Pending Review")

        embed = discord.Embed(
            title       = "📱 DIFF Staff Dashboard",
            description = (
                "Use the buttons below to manage moderation and host reviews.\n\n"
                "**Dashboard tools:**\n"
                "• 👤 View member moderation profile\n"
                "• 🏁 View host performance profile\n"
                "• ⚠️ Approve punishments (assign roles)\n"
                "• 🔄 Reset member strikes + clear flags\n"
                "• 📉 Review / clear flagged hosts"
            ),
            color = COLOR_PRIMARY,
        )
        embed.add_field(name="👥 Member Profiles",    value=str(total_m),   inline=True)
        embed.add_field(name="🚩 Flagged Members",    value=str(flagged_m), inline=True)
        embed.add_field(name="📉 Hosts Under Review", value=str(flagged_h), inline=True)
        embed.add_field(name="🧾 Pending Appeals",    value=str(pending_a), inline=True)
        embed.add_field(
            name  = "Smart Insight Layer",
            value = "This dashboard surfaces high-risk members and declining hosts automatically via `!smartinsights`.",
            inline= False,
        )
        embed.add_field(
            name="📋 Staff Commands",
            value=(
                "`!poststaffdashboard` — Post / refresh this dashboard\n"
                "`!flaggedhosts` — List hosts currently under review\n"
                "`!smartinsights` — Run AI-style moderation insight scan\n"
                "`!appealhistory @user` — View a member's full appeal history\n"
                "`!appealstats` — Show server-wide appeal statistics\n"
                "`!dashboardhelp` — View all staff dashboard commands"
            ),
            inline=False,
        )
        embed.set_footer(text="Different Meets • Staff Dashboard")
        return embed

    def _appeal_panel_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title       = "🧾 DIFF Appeal Center",
            description = (
                "If you believe a write-up, strike, or moderation action against you was unfair, "
                "press the button below to submit an appeal for staff review."
            ),
            color = COLOR_WARNING,
        )
        embed.add_field(
            name  = "Guidelines",
            value = (
                "• Be honest and respectful\n"
                "• Include your write-up or strike ID (e.g. `WU-0001`)\n"
                "• Attach evidence if you have it\n"
                "• Appeals are reviewed privately by staff"
            ),
            inline=False,
        )
        embed.set_footer(text="Different Meets • Appeal System")
        return embed

    def _member_profile_embed(self, member: discord.Member, profile: Dict[str, Any]) -> discord.Embed:
        strikes = int(profile.get("strikes", 0))
        flags   = profile.get("flags", [])
        color   = COLOR_DANGER if "critical_flag" in flags or "restricted_flag" in flags else (
                  COLOR_WARNING if "warning_flag" in flags else COLOR_PRIMARY)
        embed = discord.Embed(title=f"🛡️ Moderation Profile  •  {member}", color=color)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="⚠️ Write-Ups",    value=str(profile.get("writeups", 0)),         inline=True)
        embed.add_field(name="🚨 Strikes",       value=str(strikes),                             inline=True)
        embed.add_field(name="📊 Feedback",      value=f"{profile.get('feedback_average', 0)}/5 ({profile.get('feedback_entries', 0)} ratings)", inline=True)
        embed.add_field(name="🏟️ Attendance",    value=str(profile.get("attendance_count", 0)), inline=True)
        embed.add_field(name="🏁 Hosted Meets",  value=str(profile.get("hosted_meets", 0)),     inline=True)
        embed.add_field(name="🚩 Flags",         value=", ".join(flags) if flags else "None",   inline=True)
        embed.add_field(name="🧠 Risk Insight",  value=self._member_insight(profile),            inline=False)
        embed.set_footer(text="Different Meets • Staff Dashboard")
        return embed

    def _host_profile_embed(self, member: discord.Member, profile: Dict[str, Any]) -> discord.Embed:
        color = COLOR_DANGER if profile.get("review_flagged") else COLOR_PRIMARY
        embed = discord.Embed(title=f"🏁 Host Performance Profile  •  {member}", color=color)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="🏁 Hosted Meets",   value=str(profile.get("hosted_meets", 0)),       inline=True)
        embed.add_field(name="👥 Attendance Avg", value=str(profile.get("attendance_average", 0)), inline=True)
        embed.add_field(name="📊 Feedback Avg",   value=f"{profile.get('feedback_average', 0)}/5 ({profile.get('feedback_entries', 0)} ratings)", inline=True)
        embed.add_field(name="⚠️ Host Write-Ups", value=str(profile.get("host_writeups", 0)),      inline=True)
        embed.add_field(name="🔍 Review Flagged", value="🚨 Yes" if profile.get("review_flagged") else "✅ No", inline=True)
        embed.add_field(name="🧠 Host Insight",   value=self._host_insight(profile),                inline=False)
        embed.set_footer(text="Different Meets • Staff Dashboard")
        return embed

    # ── profile lookups ───────────────────────────────────────

    async def send_member_profile_lookup(self, interaction: discord.Interaction, uid_text: str):
        if not interaction.guild:
            await interaction.response.send_message("Server only.", ephemeral=True)
            return
        try:
            uid = int(uid_text)
        except ValueError:
            await interaction.response.send_message("❌ Invalid user ID — right-click the member and copy their ID.", ephemeral=True)
            return
        member = interaction.guild.get_member(uid)
        if member is None:
            await interaction.response.send_message("❌ Member not found in this server.", ephemeral=True)
            return
        profile = self._members().get(str(uid))
        if not profile:
            await interaction.response.send_message("No moderation profile found for that member yet.", ephemeral=True)
            return
        await interaction.response.send_message(embed=self._member_profile_embed(member, profile), ephemeral=True)

    async def send_host_profile_lookup(self, interaction: discord.Interaction, uid_text: str):
        if not interaction.guild:
            await interaction.response.send_message("Server only.", ephemeral=True)
            return
        try:
            uid = int(uid_text)
        except ValueError:
            await interaction.response.send_message("❌ Invalid user ID — right-click the member and copy their ID.", ephemeral=True)
            return
        member = interaction.guild.get_member(uid)
        if member is None:
            await interaction.response.send_message("❌ Member not found in this server.", ephemeral=True)
            return
        profile = self._hosts().get(str(uid))
        if not profile:
            await interaction.response.send_message("No host profile found for that member yet.", ephemeral=True)
            return
        await interaction.response.send_message(embed=self._host_profile_embed(member, profile), ephemeral=True)

    # ── punishment / reset ────────────────────────────────────

    async def apply_punishment(self, interaction: discord.Interaction, uid_text: str,
                                punishment_type: str, reason: str):
        if not interaction.guild:
            await interaction.response.send_message("Server only.", ephemeral=True)
            return
        try:
            uid = int(uid_text)
        except ValueError:
            await interaction.response.send_message("❌ Invalid user ID.", ephemeral=True)
            return
        member = interaction.guild.get_member(uid)
        if member is None:
            await interaction.response.send_message("❌ Member not found.", ephemeral=True)
            return

        role_id = WARNING_ROLE_ID if punishment_type == "warning" else (
                  RESTRICTED_ROLE_ID if punishment_type == "restricted" else 0)
        if not role_id:
            await interaction.response.send_message(
                f"❌ No role configured for `{punishment_type}`. "
                "Set `WARNING_ROLE_ID` or `RESTRICTED_ROLE_ID` in the cog config.",
                ephemeral=True,
            )
            return
        role = interaction.guild.get_role(role_id)
        if role is None:
            await interaction.response.send_message("❌ Punishment role not found in this server.", ephemeral=True)
            return
        try:
            if role not in member.roles:
                await member.add_roles(role, reason=f"Dashboard punishment: {reason}")
        except discord.HTTPException as e:
            await interaction.response.send_message(f"❌ Could not apply role: {e}", ephemeral=True)
            return
        await interaction.response.send_message(
            f"✅ Applied **{punishment_type}** to {member.mention}.", ephemeral=True
        )

    async def reset_member_strikes(self, interaction: discord.Interaction, uid_text: str, reason: str):
        if not interaction.guild:
            await interaction.response.send_message("Server only.", ephemeral=True)
            return
        try:
            uid = int(uid_text)
        except ValueError:
            await interaction.response.send_message("❌ Invalid user ID.", ephemeral=True)
            return
        data    = self._members()
        profile = data.get(str(uid))
        if not profile:
            await interaction.response.send_message("No moderation profile found for that member.", ephemeral=True)
            return
        profile["strikes"]      = 0
        profile["flags"]        = []
        profile["last_updated"] = _utcnow().isoformat()
        data[str(uid)]          = profile
        self._set_members(data)

        member = interaction.guild.get_member(uid)
        if member:
            for rid in [WARNING_ROLE_ID, RESTRICTED_ROLE_ID]:
                r = interaction.guild.get_role(rid) if rid else None
                if r and r in member.roles:
                    try:
                        await member.remove_roles(r, reason=f"Strike reset: {reason}")
                    except discord.HTTPException:
                        pass

        await interaction.response.send_message("✅ Strikes and flags reset successfully.", ephemeral=True)

    async def review_flagged_host(self, interaction: discord.Interaction, uid_text: str,
                                   action: str, note: str):
        if not interaction.guild:
            await interaction.response.send_message("Server only.", ephemeral=True)
            return
        try:
            uid = int(uid_text)
        except ValueError:
            await interaction.response.send_message("❌ Invalid user ID.", ephemeral=True)
            return
        data    = self._hosts()
        profile = data.get(str(uid))
        if not profile:
            await interaction.response.send_message("No host profile found for that member.", ephemeral=True)
            return

        if action == "clear":
            profile["review_flagged"] = False
            profile["last_updated"]   = _utcnow().isoformat()
            data[str(uid)]            = profile
            self._set_hosts(data)
            member = interaction.guild.get_member(uid)
            if member and HOST_REVIEW_ROLE_ID:
                r = interaction.guild.get_role(HOST_REVIEW_ROLE_ID)
                if r and r in member.roles:
                    try:
                        await member.remove_roles(r, reason=f"Host review cleared: {note}")
                    except discord.HTTPException:
                        pass
            await interaction.response.send_message("✅ Host review flag cleared.", ephemeral=True)
        elif action == "keep":
            await interaction.response.send_message("✅ Host review flag kept in place.", ephemeral=True)
        else:
            await interaction.response.send_message("Action must be `clear` or `keep`.", ephemeral=True)

    # ── appeals ───────────────────────────────────────────────

    async def submit_appeal(self, interaction: discord.Interaction, writeup_id: str,
                             reason: str, evidence: str):
        if not interaction.guild:
            await interaction.response.send_message("Server only.", ephemeral=True)
            return

        appeal_id = self._next_appeal_id()
        entry: Dict[str, Any] = {
            "appeal_id":     appeal_id,
            "user_id":       interaction.user.id,
            "username":      str(interaction.user),
            "writeup_id":    writeup_id,
            "reason":        reason,
            "evidence":      evidence,
            "status":        "Pending Review",
            "submitted_at":  _utcnow().isoformat(),
            "reviewed_by":   None,
            "reviewed_at":   None,
            "decision_note": None,
            "message_id":    None,
        }

        data = self._appeals()
        data["entries"][appeal_id] = entry
        self._set_appeals(data)

        ch = interaction.guild.get_channel(APPEAL_REVIEW_CHANNEL_ID)
        if ch:
            embed = discord.Embed(
                title     = f"🧾 New Appeal Submitted • {appeal_id}",
                color     = COLOR_WARNING,
                timestamp = _utcnow(),
            )
            embed.add_field(name="User",           value=interaction.user.mention, inline=True)
            embed.add_field(name="Write-Up ID",    value=writeup_id,               inline=True)
            embed.add_field(name="Status",         value="Pending Review",         inline=True)
            embed.add_field(name="Appeal Reason",  value=reason[:1024],            inline=False)
            embed.add_field(name="Evidence",       value=evidence[:1024],          inline=False)
            embed.set_footer(text="Different Meets • Appeal Review")
            msg = await ch.send(embed=embed, view=AppealReviewView(self, appeal_id))
            data = self._appeals()
            data["entries"][appeal_id]["message_id"] = msg.id
            self._set_appeals(data)

        await interaction.response.send_message(
            f"✅ Appeal **{appeal_id}** submitted. Staff will review it shortly.", ephemeral=True
        )

    async def review_appeal(self, interaction: discord.Interaction, appeal_id: str, accepted: bool):
        if not appeal_id:
            await interaction.response.send_message("Could not determine appeal ID.", ephemeral=True)
            return
        data  = self._appeals()
        entry = data["entries"].get(appeal_id)
        if not entry:
            await interaction.response.send_message(f"Appeal `{appeal_id}` not found.", ephemeral=True)
            return

        entry["status"]        = "Accepted" if accepted else "Denied"
        entry["reviewed_by"]   = interaction.user.mention
        entry["reviewed_at"]   = _utcnow().isoformat()
        entry["decision_note"] = "Appeal accepted by staff." if accepted else "Appeal denied by staff."
        data["entries"][appeal_id] = entry
        self._set_appeals(data)

        color = COLOR_SUCCESS if accepted else COLOR_DANGER
        embed = discord.Embed(
            title     = f"🧾 Appeal Reviewed • {appeal_id}",
            color     = color,
            timestamp = _utcnow(),
        )
        embed.add_field(name="User",          value=f"<@{entry['user_id']}>",   inline=True)
        embed.add_field(name="Write-Up ID",   value=entry["writeup_id"],         inline=True)
        embed.add_field(name="Status",        value=entry["status"],             inline=True)
        embed.add_field(name="Appeal Reason", value=entry["reason"][:1024],     inline=False)
        embed.add_field(name="Evidence",      value=entry["evidence"][:1024],   inline=False)
        embed.add_field(name="Reviewed By",   value=entry["reviewed_by"],        inline=True)
        embed.set_footer(text="Different Meets • Appeal Review")

        try:
            await interaction.message.edit(embed=embed, view=AppealReviewView(self, appeal_id))
        except discord.HTTPException:
            pass

        if interaction.guild:
            member = interaction.guild.get_member(entry["user_id"])
            if member:
                decision = "accepted ✅" if accepted else "denied ❌"
                try:
                    appeal_em = discord.Embed(
                        title="DIFF Appeal Decision",
                        description=f"Your appeal **{appeal_id}** (for `{entry['writeup_id']}`) has been **{decision}** by staff.",
                        color=discord.Color.green() if accepted else discord.Color.red(),
                    )
                    appeal_em.set_author(name="Different Meets", icon_url=DIFF_LOGO_URL)
                    appeal_em.set_thumbnail(url=DIFF_LOGO_URL)
                    await member.send(embed=appeal_em)
                except discord.HTTPException:
                    pass

        await interaction.response.send_message(
            f"✅ Appeal **{appeal_id}** has been **{entry['status'].lower()}**.", ephemeral=True
        )

    # =========================================================
    # PREFIX COMMANDS
    # =========================================================

    @commands.command(name="poststaffdashboard")
    @commands.has_permissions(manage_guild=True)
    async def post_staff_dashboard(self, ctx: commands.Context):
        """Post the staff dashboard panel.  Usage: !poststaffdashboard"""
        ch = ctx.guild.get_channel(STAFF_DASHBOARD_CHANNEL_ID) or ctx.channel
        await ch.send(embed=self._dashboard_embed(), view=StaffDashboardView(self))
        await ctx.send(f"✅ Staff dashboard posted in {ch.mention}.", delete_after=6)
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="postappealpanel")
    @commands.has_permissions(manage_guild=True)
    async def post_appeal_panel(self, ctx: commands.Context):
        """Post the member appeal panel.  Usage: !postappealpanel"""
        ch = ctx.guild.get_channel(APPEAL_PANEL_CHANNEL_ID) or ctx.channel
        await ch.send(embed=self._appeal_panel_embed(), view=AppealPanelView(self))
        await ctx.send(f"✅ Appeal panel posted in {ch.mention}.", delete_after=6)
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="flaggedhosts")
    @commands.has_permissions(manage_guild=True)
    async def flagged_hosts(self, ctx: commands.Context):
        """List all currently flagged hosts.  Usage: !flaggedhosts"""
        data    = self._hosts()
        flagged = [p for p in data.values() if p.get("review_flagged")]
        if not flagged:
            await ctx.send("✅ No hosts are currently flagged for review.", delete_after=10)
            return

        lines = []
        for p in flagged[:10]:
            lines.append(
                f"**{p['display_name']}** — Feedback: {p.get('feedback_average', 0)}/5 | "
                f"Host WUs: {p.get('host_writeups', 0)} | "
                f"Att. Avg: {p.get('attendance_average', 0)}"
            )

        embed = discord.Embed(
            title       = "📉 Hosts Currently Under Review",
            description = "\n".join(lines),
            color       = COLOR_WARNING,
        )
        embed.add_field(
            name  = "Next Steps",
            value = "Use the **Review Flagged Host** button on the staff dashboard to clear or keep each flag.",
            inline=False,
        )
        embed.set_footer(text="Different Meets • Staff Dashboard")
        await ctx.send(embed=embed)

    @commands.command(name="smartinsights")
    @commands.has_permissions(manage_guild=True)
    async def smart_insights(self, ctx: commands.Context):
        """Run smart risk analysis across all profiles.  Usage: !smartinsights"""
        member_data = self._members()
        host_data   = self._hosts()

        risky_members: List[tuple] = []
        for uid, p in member_data.items():
            insight = self._member_insight(p)
            if "High-risk" in insight or "Rising moderation" in insight:
                risky_members.append((p.get("display_name", f"<@{uid}>"), insight))

        risky_hosts: List[tuple] = []
        for uid, p in host_data.items():
            insight = self._host_insight(p)
            if "Declining" in insight or "Struggling" in insight:
                risky_hosts.append((p.get("display_name", f"<@{uid}>"), insight))

        embed = discord.Embed(title="🧠 Smart Moderation Insights", color=COLOR_PRIMARY)
        embed.add_field(
            name  = "🚨 High-Risk / Rising Members",
            value = "\n".join(f"**{n}** — {i}" for n, i in risky_members[:8])
                    if risky_members else "No risky members detected.",
            inline=False,
        )
        embed.add_field(
            name  = "📉 Declining / Struggling Hosts",
            value = "\n".join(f"**{n}** — {i}" for n, i in risky_hosts[:8])
                    if risky_hosts else "No declining hosts detected.",
            inline=False,
        )
        embed.add_field(
            name  = "Summary",
            value = f"{len(risky_members)} member(s) flagged · {len(risky_hosts)} host(s) flagged",
            inline=False,
        )
        embed.set_footer(text="Different Meets • Smart Insights")
        await ctx.send(embed=embed)

    @commands.command(name="appealhistory")
    @commands.has_permissions(manage_guild=True)
    async def appeal_history(self, ctx: commands.Context, member: discord.Member):
        """View all appeals for a member.  Usage: !appealhistory @member"""
        data    = self._appeals()
        entries = [
            e for e in data["entries"].values()
            if e["user_id"] == member.id
        ]
        if not entries:
            await ctx.send(f"No appeals found for {member.mention}.", delete_after=10)
            return

        entries.sort(key=lambda e: e["submitted_at"], reverse=True)
        lines = [
            f"**{e['appeal_id']}** — WU: `{e['writeup_id']}` — `{e['status']}` — {e['submitted_at'][:10]}"
            for e in entries[:10]
        ]
        embed = discord.Embed(
            title       = f"🧾 Appeal History  •  {member}",
            description = "\n".join(lines),
            color       = COLOR_WARNING,
        )
        embed.set_footer(text="Different Meets • Appeal System")
        await ctx.send(embed=embed)

    @commands.command(name="appealstats")
    @commands.has_permissions(manage_guild=True)
    async def appeal_stats(self, ctx: commands.Context):
        """Show appeal system stats.  Usage: !appealstats"""
        data    = self._appeals()
        entries = data["entries"]
        total   = len(entries)
        pending  = sum(1 for e in entries.values() if e["status"] == "Pending Review")
        accepted = sum(1 for e in entries.values() if e["status"] == "Accepted")
        denied   = sum(1 for e in entries.values() if e["status"] == "Denied")

        embed = discord.Embed(title="📊 Appeal System Stats", color=COLOR_PRIMARY)
        embed.add_field(name="📋 Total Appeals",    value=str(total),    inline=True)
        embed.add_field(name="⏳ Pending Review",   value=str(pending),  inline=True)
        embed.add_field(name="✅ Accepted",          value=str(accepted), inline=True)
        embed.add_field(name="❌ Denied",            value=str(denied),   inline=True)
        embed.set_footer(text="Different Meets • Staff Dashboard")
        await ctx.send(embed=embed)

    @commands.command(name="dashboardhelp")
    @commands.has_permissions(manage_guild=True)
    async def dashboard_help(self, ctx: commands.Context):
        """Show all staff dashboard commands.  Usage: !dashboardhelp"""
        embed = discord.Embed(title="📋 Staff Dashboard Commands", color=COLOR_PRIMARY)
        embed.add_field(
            name="Panels",
            value=(
                "`!poststaffdashboard` — Post the staff action dashboard\n"
                "`!postappealpanel` — Post the member appeal panel\n"
            ),
            inline=False,
        )
        embed.add_field(
            name="Dashboard Buttons",
            value=(
                "• 👤 **View Member Profile** — look up by user ID (ephemeral)\n"
                "• 🏁 **View Host Profile** — look up by user ID (ephemeral)\n"
                "• ⚠️ **Approve Punishment** — assign warning/restricted role\n"
                "• 🔄 **Reset Strikes** — clear strikes + flags + remove roles\n"
                "• 📉 **Review Flagged Host** — clear or keep host review flag\n"
            ),
            inline=False,
        )
        embed.add_field(
            name="Commands",
            value=(
                "`!flaggedhosts` — List all hosts currently under review\n"
                "`!smartinsights` — Risk analysis across all profiles\n"
                "`!appealhistory @m` — View a member's appeal history\n"
                "`!appealstats` — Overall appeal system stats\n"
            ),
            inline=False,
        )
        embed.add_field(
            name="Appeal Flow",
            value=(
                "Member presses **Submit Appeal** → fills form → bot posts to staff-logs with "
                "✅ Accept / ❌ Deny buttons → staff reviews → member gets a DM with the decision."
            ),
            inline=False,
        )
        embed.set_footer(text="Different Meets • Staff Dashboard")
        await ctx.send(embed=embed)


# =========================================================
# SETUP
# =========================================================

async def setup(bot: commands.Bot):
    await bot.add_cog(StaffDashboardSystem(bot))
