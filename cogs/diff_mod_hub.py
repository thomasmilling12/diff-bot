from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta
from typing import Optional

import discord
from discord.ext import commands

# =========================================================
# CONFIG
# =========================================================
MOD_HUB_CHANNEL_ID     = 1486598266211664003
MOD_LOG_CHANNEL_ID     = 1486598266211664003
WARNING_LOG_CHANNEL_ID = 1486599502834958366

STAFF_ROLE_IDS: set[int] = {
    850391095845584937,   # Leader
    850391378559238235,   # Co-Leader
    990011447193006101,   # Manager
}

PANEL_TAG  = "DIFF_MOD_HUB_PANEL_V2"
DATA_DIR   = "diff_data"
PANEL_FILE = os.path.join(DATA_DIR, "mod_hub_panel.json")
WARN_FILE  = os.path.join(DATA_DIR, "mod_warnings.json")
CASE_FILE  = os.path.join(DATA_DIR, "mod_cases.json")

DIFF_LOGO_URL = (
    "https://media.discordapp.net/attachments/1107375326625005719/"
    "1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm="
    "2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
    "&=&format=webp&quality=lossless&width=1376&height=917"
)


# =========================================================
# FILE / DATA HELPERS
# =========================================================
def _load_json(path: str, default=None):
    if default is None:
        default = {}
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def _get_panel_msg_id() -> Optional[int]:
    v = _load_json(PANEL_FILE).get("panel_message_id")
    return int(v) if v else None


def _save_panel_msg_id(msg_id: int) -> None:
    data = _load_json(PANEL_FILE)
    data["panel_message_id"] = msg_id
    _save_json(PANEL_FILE, data)


def _next_case() -> int:
    data = _load_json(CASE_FILE, {"last_case": 0})
    data["last_case"] = data.get("last_case", 0) + 1
    _save_json(CASE_FILE, data)
    return data["last_case"]


def _add_warning(guild_id: int, user_id: int, entry: dict) -> None:
    data = _load_json(WARN_FILE)
    gk, uk = str(guild_id), str(user_id)
    data.setdefault(gk, {}).setdefault(uk, []).append(entry)
    _save_json(WARN_FILE, data)


def _get_warnings(guild_id: int, user_id: int) -> list:
    return _load_json(WARN_FILE).get(str(guild_id), {}).get(str(user_id), [])


def _warn_count(guild_id: int, user_id: int) -> int:
    return len(_get_warnings(guild_id, user_id))


def _is_staff(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    return any(r.id in STAFF_ROLE_IDS for r in member.roles)


def _risk_label(count: int) -> str:
    if count >= 4:
        return "🔨 Ban threshold"
    if count == 3:
        return "👢 Kick threshold"
    if count == 2:
        return "⏳ Timeout threshold"
    if count == 1:
        return "⚠️ First warning"
    return "✅ Clean"


# =========================================================
# EMBED BUILDERS
# =========================================================
def _panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🛡️ DIFF Moderation Hub",
        description=(
            "Staff-only moderation control centre for **Different Meets**.\n"
            "Use the dropdown for all actions — quick buttons are also available below.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=0xED4245,
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(
        name="⚠️ Warnings",
        value="**Warn** — issues a logged warning\n**Check** — view full warning history",
        inline=True,
    )
    embed.add_field(
        name="⏳ Restrictions",
        value="**Timeout** — temporarily mute\n**Remove Timeout** — lift an active timeout",
        inline=True,
    )
    embed.add_field(
        name="🚫 Removals",
        value="**Kick** — remove (can rejoin)\n**Ban** — permanent removal",
        inline=True,
    )
    embed.add_field(
        name="📌 Notes",
        value=(
            "All actions require a target and reason.\n"
            "Every action is logged here with full case details.\n"
            "Members receive a DM for warnings, timeouts, kicks, and bans."
        ),
        inline=False,
    )
    embed.set_thumbnail(url=DIFF_LOGO_URL)
    embed.set_footer(text=PANEL_TAG)
    return embed


def _action_log_embed(
    action: str,
    target: discord.Member | discord.User,
    moderator: discord.Member,
    reason: str,
    case_id: int,
    extra: str = "",
    color: discord.Color = discord.Color.red(),
) -> discord.Embed:
    embed = discord.Embed(
        title=f"🛡️ {action}",
        color=color,
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name="User",      value=f"{target.mention}\n`{target.id}`",       inline=True)
    embed.add_field(name="Moderator", value=f"{moderator.mention}\n`{moderator.id}`", inline=True)
    embed.add_field(name="Case",      value=f"`#{case_id}`",                           inline=True)
    embed.add_field(name="Reason",    value=reason or "No reason provided.",            inline=False)
    if extra:
        embed.add_field(name="Details", value=extra, inline=False)
    embed.set_thumbnail(url=DIFF_LOGO_URL)
    embed.set_footer(text="DIFF Meets • Moderation Logs")
    return embed


def _warning_history_embed(user: discord.Member | discord.User, warnings: list) -> discord.Embed:
    recent = warnings[-10:]
    start  = max(1, len(warnings) - 9)
    lines  = []
    for i, w in enumerate(recent):
        ts = w.get("timestamp", "")
        date_str = ts[:10] if ts else "unknown"
        lines.append(
            f"**#{start + i}** — Case `#{w['case_id']}`\n"
            f"› {w['reason']}\n"
            f"› {date_str}"
        )
    embed = discord.Embed(
        title=f"📋 Warning History — {user.display_name}",
        description="\n\n".join(lines) if lines else "No warnings on record.",
        color=discord.Color.orange(),
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name="Total Warnings", value=str(len(warnings)), inline=True)
    embed.add_field(name="Risk Level",     value=_risk_label(len(warnings)),          inline=True)
    embed.set_thumbnail(url=DIFF_LOGO_URL)
    embed.set_footer(text="DIFF Meets • Moderation Hub — last 10 shown")
    return embed


def _server_stats_embed(guild_id: int, guild: discord.Guild) -> discord.Embed:
    all_data = _load_json(WARN_FILE).get(str(guild_id), {})
    total    = sum(len(v) for v in all_data.values())
    ranked   = sorted(all_data.items(), key=lambda x: len(x[1]), reverse=True)
    medals   = {1: "🥇", 2: "🥈", 3: "🥉"}

    lines = []
    for i, (uid, warns) in enumerate(ranked[:8], 1):
        m = guild.get_member(int(uid))
        name = m.mention if m else f"<@{uid}>"
        prefix = medals.get(i, f"**{i}.**")
        lines.append(f"{prefix} {name} — **{len(warns)}** warning(s) {_risk_label(len(warns))}")

    embed = discord.Embed(
        title="📊 Server Moderation Stats",
        description="\n".join(lines) if lines else "No warnings have been issued yet.",
        color=0xED4245,
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name="Total Warnings",    value=str(total),          inline=True)
    embed.add_field(name="Members Warned",    value=str(len(all_data)),  inline=True)
    embed.set_thumbnail(url=DIFF_LOGO_URL)
    embed.set_footer(text="DIFF Meets • Moderation Hub — top 8 shown")
    return embed


# =========================================================
# MODALS
# =========================================================
class WarnModal(discord.ui.Modal, title="Warn Member"):
    reason = discord.ui.TextInput(
        label="Warning Reason",
        placeholder="Enter the reason for the warning…",
        style=discord.TextStyle.paragraph, max_length=500, required=True,
    )

    def __init__(self, cog: "ModHubCog", member: discord.Member):
        super().__init__()
        self.cog    = cog
        self.member = member

    async def on_submit(self, interaction: discord.Interaction) -> None:
        mod = interaction.user
        if not isinstance(mod, discord.Member) or not _is_staff(mod):
            return await interaction.response.send_message("Only staff can use this panel.", ephemeral=True)

        case_id    = _next_case()
        reason_txt = str(self.reason).strip()
        _add_warning(interaction.guild.id, self.member.id, {
            "case_id":      case_id,
            "reason":       reason_txt,
            "moderator_id": mod.id,
            "timestamp":    datetime.now(timezone.utc).isoformat(),
        })
        total = _warn_count(interaction.guild.id, self.member.id)

        warn_embed = discord.Embed(
            title="⚠️ Member Warned",
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc),
        )
        warn_embed.add_field(name="User",           value=f"{self.member.mention}\n`{self.member.id}`", inline=True)
        warn_embed.add_field(name="Moderator",      value=mod.mention,    inline=True)
        warn_embed.add_field(name="Case",           value=f"`#{case_id}`", inline=True)
        warn_embed.add_field(name="Reason",         value=reason_txt,      inline=False)
        warn_embed.add_field(name="Total Warnings", value=str(total),      inline=True)
        warn_embed.add_field(name="Risk Level",     value=_risk_label(total), inline=True)
        warn_embed.set_thumbnail(url=DIFF_LOGO_URL)
        warn_embed.set_footer(text="DIFF Meets • Warning System")

        await self.cog.send_to(WARNING_LOG_CHANNEL_ID, embed=warn_embed)
        await self.cog.send_to(MOD_LOG_CHANNEL_ID, embed=_action_log_embed(
            "Warn", self.member, mod, reason_txt, case_id,
            extra=f"Total warnings: **{total}** — {_risk_label(total)}",
            color=discord.Color.orange(),
        ))

        try:
            dm = discord.Embed(
                title="⚠️ You Have Been Warned",
                description=(
                    f"You were warned in **{interaction.guild.name}**.\n\n"
                    f"**Reason:** {reason_txt}\n"
                    f"**Case:** #{case_id}\n"
                    f"**Total Warnings:** {total}"
                ),
                color=discord.Color.orange(),
            )
            dm.set_thumbnail(url=DIFF_LOGO_URL)
            dm.set_footer(text="DIFF Meets • Moderation")
            await self.member.send(embed=dm)
        except Exception:
            pass

        await interaction.response.send_message(
            f"Warned {self.member.mention}. Case `#{case_id}` — total warnings: **{total}**.",
            ephemeral=True,
        )


class TimeoutModal(discord.ui.Modal, title="Timeout Member"):
    duration_input = discord.ui.TextInput(
        label="Duration (minutes)",
        placeholder="Example: 60",
        max_length=10, required=True,
    )
    reason = discord.ui.TextInput(
        label="Timeout Reason",
        placeholder="Enter the reason for the timeout…",
        style=discord.TextStyle.paragraph, max_length=500, required=True,
    )

    def __init__(self, cog: "ModHubCog", member: discord.Member):
        super().__init__()
        self.cog    = cog
        self.member = member

    async def on_submit(self, interaction: discord.Interaction) -> None:
        mod = interaction.user
        if not isinstance(mod, discord.Member) or not _is_staff(mod):
            return await interaction.response.send_message("Only staff can use this panel.", ephemeral=True)

        try:
            minutes = int(str(self.duration_input).strip())
            if minutes <= 0:
                raise ValueError
        except ValueError:
            return await interaction.response.send_message(
                "Duration must be a whole number greater than 0.", ephemeral=True
            )

        case_id    = _next_case()
        reason_txt = str(self.reason).strip()
        until      = datetime.now(timezone.utc) + timedelta(minutes=minutes)

        try:
            await self.member.timeout(until, reason=reason_txt)
        except Exception as e:
            return await interaction.response.send_message(f"Failed to timeout member: {e}", ephemeral=True)

        await self.cog.send_to(MOD_LOG_CHANNEL_ID, embed=_action_log_embed(
            "Timeout", self.member, mod, reason_txt, case_id,
            extra=f"Duration: {minutes} minute(s)",
            color=discord.Color.blue(),
        ))

        try:
            dm = discord.Embed(
                title="⏳ You Have Been Timed Out",
                description=(
                    f"You were timed out in **{interaction.guild.name}**.\n\n"
                    f"**Duration:** {minutes} minute(s)\n"
                    f"**Reason:** {reason_txt}\n"
                    f"**Case:** #{case_id}"
                ),
                color=discord.Color.blue(),
            )
            dm.set_thumbnail(url=DIFF_LOGO_URL)
            dm.set_footer(text="DIFF Meets • Moderation")
            await self.member.send(embed=dm)
        except Exception:
            pass

        await interaction.response.send_message(
            f"Timed out {self.member.mention} for {minutes} minute(s). Case `#{case_id}`.",
            ephemeral=True,
        )


class KickModal(discord.ui.Modal, title="Kick Member"):
    reason = discord.ui.TextInput(
        label="Kick Reason",
        placeholder="Enter the reason for the kick…",
        style=discord.TextStyle.paragraph, max_length=500, required=True,
    )

    def __init__(self, cog: "ModHubCog", member: discord.Member):
        super().__init__()
        self.cog    = cog
        self.member = member

    async def on_submit(self, interaction: discord.Interaction) -> None:
        mod = interaction.user
        if not isinstance(mod, discord.Member) or not _is_staff(mod):
            return await interaction.response.send_message("Only staff can use this panel.", ephemeral=True)

        case_id    = _next_case()
        reason_txt = str(self.reason).strip()

        try:
            dm = discord.Embed(
                title="👢 You Have Been Kicked",
                description=(
                    f"You were kicked from **{interaction.guild.name}**.\n\n"
                    f"**Reason:** {reason_txt}\n"
                    f"**Case:** #{case_id}"
                ),
                color=discord.Color.red(),
            )
            dm.set_thumbnail(url=DIFF_LOGO_URL)
            dm.set_footer(text="DIFF Meets • Moderation")
            await self.member.send(embed=dm)
        except Exception:
            pass

        try:
            await self.member.kick(reason=reason_txt)
        except Exception as e:
            return await interaction.response.send_message(f"Failed to kick member: {e}", ephemeral=True)

        await self.cog.send_to(MOD_LOG_CHANNEL_ID, embed=_action_log_embed(
            "Kick", self.member, mod, reason_txt, case_id, color=discord.Color.red()
        ))
        await interaction.response.send_message(
            f"Kicked `{self.member}`. Case `#{case_id}`.", ephemeral=True
        )


class BanModal(discord.ui.Modal, title="Ban Member"):
    reason = discord.ui.TextInput(
        label="Ban Reason",
        placeholder="Enter the reason for the ban…",
        style=discord.TextStyle.paragraph, max_length=500, required=True,
    )

    def __init__(self, cog: "ModHubCog", member: discord.Member):
        super().__init__()
        self.cog    = cog
        self.member = member

    async def on_submit(self, interaction: discord.Interaction) -> None:
        mod = interaction.user
        if not isinstance(mod, discord.Member) or not _is_staff(mod):
            return await interaction.response.send_message("Only staff can use this panel.", ephemeral=True)

        case_id    = _next_case()
        reason_txt = str(self.reason).strip()

        try:
            dm = discord.Embed(
                title="🔨 You Have Been Banned",
                description=(
                    f"You were banned from **{interaction.guild.name}**.\n\n"
                    f"**Reason:** {reason_txt}\n"
                    f"**Case:** #{case_id}"
                ),
                color=discord.Color.dark_red(),
            )
            dm.set_thumbnail(url=DIFF_LOGO_URL)
            dm.set_footer(text="DIFF Meets • Moderation")
            await self.member.send(embed=dm)
        except Exception:
            pass

        try:
            await self.member.ban(reason=reason_txt, delete_message_seconds=0)
        except Exception as e:
            return await interaction.response.send_message(f"Failed to ban member: {e}", ephemeral=True)

        await self.cog.send_to(MOD_LOG_CHANNEL_ID, embed=_action_log_embed(
            "Ban", self.member, mod, reason_txt, case_id, color=discord.Color.dark_red()
        ))
        await interaction.response.send_message(
            f"Banned `{self.member}`. Case `#{case_id}`.", ephemeral=True
        )


# =========================================================
# EPHEMERAL MEMBER-SELECT VIEWS
# =========================================================
class _MemberSelect(discord.ui.UserSelect):
    def __init__(self, cog: "ModHubCog", action: str):
        super().__init__(
            placeholder=f"Select a member to {action.lower()}…",
            min_values=1, max_values=1,
        )
        self.cog    = cog
        self.action = action

    async def callback(self, interaction: discord.Interaction) -> None:
        mod = interaction.user
        if not isinstance(mod, discord.Member) or not _is_staff(mod):
            return await interaction.response.send_message("Only staff can use this panel.", ephemeral=True)

        user = self.values[0]
        if not isinstance(user, discord.Member):
            user = interaction.guild.get_member(user.id)
        if user is None:
            return await interaction.response.send_message("Could not find that member in the server.", ephemeral=True)

        modal_map = {
            "Warn":    WarnModal,
            "Timeout": TimeoutModal,
            "Kick":    KickModal,
            "Ban":     BanModal,
        }
        modal_cls = modal_map.get(self.action)
        if modal_cls:
            await interaction.response.send_modal(modal_cls(self.cog, user))


class _MemberSelectView(discord.ui.View):
    def __init__(self, cog: "ModHubCog", action: str):
        super().__init__(timeout=120)
        self.add_item(_MemberSelect(cog, action))


class _CheckWarningsSelect(discord.ui.UserSelect):
    def __init__(self):
        super().__init__(placeholder="Select a member to check warnings…", min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        mod = interaction.user
        if not isinstance(mod, discord.Member) or not _is_staff(mod):
            return await interaction.response.send_message("Only staff can use this panel.", ephemeral=True)
        user = self.values[0]
        if not isinstance(user, discord.Member):
            user = interaction.guild.get_member(user.id)
        warnings = _get_warnings(interaction.guild.id, user.id)
        embed = _warning_history_embed(user, warnings)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class _CheckWarningsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(_CheckWarningsSelect())


class _RemoveTimeoutSelect(discord.ui.UserSelect):
    def __init__(self, cog: "ModHubCog"):
        super().__init__(placeholder="Select a member to remove timeout from…", min_values=1, max_values=1)
        self.cog = cog

    async def callback(self, interaction: discord.Interaction) -> None:
        mod = interaction.user
        if not isinstance(mod, discord.Member) or not _is_staff(mod):
            return await interaction.response.send_message("Only staff can use this panel.", ephemeral=True)
        user = self.values[0]
        if not isinstance(user, discord.Member):
            user = interaction.guild.get_member(user.id)
        if user is None:
            return await interaction.response.send_message("Could not find that member.", ephemeral=True)
        if not user.is_timed_out():
            return await interaction.response.send_message(
                f"{user.mention} is not currently timed out.", ephemeral=True
            )
        try:
            await user.timeout(None, reason=f"Timeout removed by {mod}")
        except Exception as e:
            return await interaction.response.send_message(f"Failed to remove timeout: {e}", ephemeral=True)

        case_id = _next_case()
        await self.cog.send_to(MOD_LOG_CHANNEL_ID, embed=_action_log_embed(
            "Timeout Removed", user, mod, "Staff manually removed the active timeout.", case_id,
            color=discord.Color.green(),
        ))
        await interaction.response.send_message(
            f"Timeout removed from {user.mention}. Case `#{case_id}`.", ephemeral=True
        )


class _RemoveTimeoutView(discord.ui.View):
    def __init__(self, cog: "ModHubCog"):
        super().__init__(timeout=120)
        self.add_item(_RemoveTimeoutSelect(cog))


# =========================================================
# DROPDOWN  (row 0)
# =========================================================
class _ModHubSelect(discord.ui.Select):
    def __init__(self, cog: "ModHubCog"):
        super().__init__(
            custom_id="diff_mod_hub_select_v2",
            placeholder="🛡️ Select a moderation action…",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Warn a Member",
                    value="warn",
                    emoji="⚠️",
                    description="Issue an official logged warning.",
                ),
                discord.SelectOption(
                    label="Timeout a Member",
                    value="timeout",
                    emoji="⏳",
                    description="Temporarily restrict a member's access.",
                ),
                discord.SelectOption(
                    label="Remove Timeout",
                    value="untimeout",
                    emoji="🔓",
                    description="Lift an active timeout from a member.",
                ),
                discord.SelectOption(
                    label="Kick a Member",
                    value="kick",
                    emoji="👢",
                    description="Remove a member (they can rejoin).",
                ),
                discord.SelectOption(
                    label="Ban a Member",
                    value="ban",
                    emoji="🔨",
                    description="Permanently ban a member from the server.",
                ),
                discord.SelectOption(
                    label="Check Warnings",
                    value="check",
                    emoji="📋",
                    description="View a member's full warning history.",
                ),
                discord.SelectOption(
                    label="Server Mod Stats",
                    value="stats",
                    emoji="📊",
                    description="View server-wide moderation statistics.",
                ),
            ],
            row=0,
        )
        self.cog = cog

    async def callback(self, interaction: discord.Interaction) -> None:
        if not isinstance(interaction.user, discord.Member) or not _is_staff(interaction.user):
            return await interaction.response.send_message("Staff only.", ephemeral=True)

        selected = self.values[0]

        if selected == "warn":
            await interaction.response.send_message(
                "Select a member to warn:", view=_MemberSelectView(self.cog, "Warn"), ephemeral=True
            )
        elif selected == "timeout":
            await interaction.response.send_message(
                "Select a member to timeout:", view=_MemberSelectView(self.cog, "Timeout"), ephemeral=True
            )
        elif selected == "untimeout":
            await interaction.response.send_message(
                "Select a member to remove the timeout from:",
                view=_RemoveTimeoutView(self.cog), ephemeral=True
            )
        elif selected == "kick":
            await interaction.response.send_message(
                "Select a member to kick:", view=_MemberSelectView(self.cog, "Kick"), ephemeral=True
            )
        elif selected == "ban":
            await interaction.response.send_message(
                "Select a member to ban:", view=_MemberSelectView(self.cog, "Ban"), ephemeral=True
            )
        elif selected == "check":
            await interaction.response.send_message(
                "Select a member to check:", view=_CheckWarningsView(), ephemeral=True
            )
        elif selected == "stats":
            embed = _server_stats_embed(interaction.guild.id, interaction.guild)
            await interaction.response.send_message(embed=embed, ephemeral=True)


# =========================================================
# MAIN HUB VIEW  (persistent)
# =========================================================
class ModHubView(discord.ui.View):
    def __init__(self, cog: "ModHubCog"):
        super().__init__(timeout=None)
        self.cog = cog
        self.add_item(_ModHubSelect(cog))

    async def _staff_check(self, interaction: discord.Interaction) -> bool:
        member = interaction.user
        if not isinstance(member, discord.Member) or not _is_staff(member):
            await interaction.response.send_message("Only staff can use this panel.", ephemeral=True)
            return False
        return True

    @discord.ui.button(
        label="Warn", emoji="⚠️",
        style=discord.ButtonStyle.secondary,
        custom_id="diff_mod_warn_v1", row=1,
    )
    async def warn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._staff_check(interaction):
            return
        await interaction.response.send_message(
            "Select a member to warn:", view=_MemberSelectView(self.cog, "Warn"), ephemeral=True
        )

    @discord.ui.button(
        label="Timeout", emoji="⏳",
        style=discord.ButtonStyle.primary,
        custom_id="diff_mod_timeout_v1", row=1,
    )
    async def timeout_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._staff_check(interaction):
            return
        await interaction.response.send_message(
            "Select a member to timeout:", view=_MemberSelectView(self.cog, "Timeout"), ephemeral=True
        )

    @discord.ui.button(
        label="Kick", emoji="👢",
        style=discord.ButtonStyle.danger,
        custom_id="diff_mod_kick_v1", row=1,
    )
    async def kick(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._staff_check(interaction):
            return
        await interaction.response.send_message(
            "Select a member to kick:", view=_MemberSelectView(self.cog, "Kick"), ephemeral=True
        )

    @discord.ui.button(
        label="Ban", emoji="🔨",
        style=discord.ButtonStyle.danger,
        custom_id="diff_mod_ban_v1", row=1,
    )
    async def ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._staff_check(interaction):
            return
        await interaction.response.send_message(
            "Select a member to ban:", view=_MemberSelectView(self.cog, "Ban"), ephemeral=True
        )

    @discord.ui.button(
        label="Check Warnings", emoji="📋",
        style=discord.ButtonStyle.success,
        custom_id="diff_mod_checkwarn_v1", row=1,
    )
    async def check_warnings(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._staff_check(interaction):
            return
        await interaction.response.send_message(
            "Select a member to check:", view=_CheckWarningsView(), ephemeral=True
        )


# =========================================================
# COG
# =========================================================
class ModHubCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot  = bot
        self.view = ModHubView(self)
        self.bot.add_view(self.view)

    async def send_to(self, channel_id: int, **kwargs) -> None:
        ch = self.bot.get_channel(channel_id)
        if isinstance(ch, discord.TextChannel):
            try:
                await ch.send(**kwargs)
            except Exception:
                pass

    async def ensure_panel(self) -> None:
        channel = self.bot.get_channel(MOD_HUB_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            try:
                channel = await self.bot.fetch_channel(MOD_HUB_CHANNEL_ID)
            except Exception:
                channel = None
        if not isinstance(channel, discord.TextChannel):
            print(f"[ModHub] Channel {MOD_HUB_CHANNEL_ID} not found.")
            return

        embed    = _panel_embed()
        saved_id = _get_panel_msg_id()

        if saved_id:
            try:
                msg = await channel.fetch_message(saved_id)
                await msg.edit(embed=embed, view=self.view)
                print("[ModHub] Panel refreshed.")
                return
            except discord.NotFound:
                pass
            except Exception as e:
                print(f"[ModHub] Edit failed: {e}")

        try:
            async for msg in channel.history(limit=50):
                if (
                    msg.author == self.bot.user
                    and msg.embeds
                    and msg.embeds[0].title == "🛡️ DIFF Moderation Hub"
                ):
                    try:
                        await msg.delete()
                    except Exception:
                        pass
        except Exception:
            pass

        try:
            new_msg = await channel.send(embed=embed, view=self.view)
            _save_panel_msg_id(new_msg.id)
            print(f"[ModHub] Panel posted: {new_msg.id}")
        except Exception as e:
            print(f"[ModHub] Post failed: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.ensure_panel()
        print("[ModHub] Cog ready.")

    @commands.command(name="refresh_mod_hub")
    @commands.has_permissions(manage_guild=True)
    async def cmd_refresh(self, ctx: commands.Context):
        await self.ensure_panel()
        await ctx.send("Moderation hub panel refreshed.", delete_after=8)


# =========================================================
# SETUP
# =========================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(ModHubCog(bot))
