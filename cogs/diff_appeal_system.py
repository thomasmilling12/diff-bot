from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import discord
from discord.ext import commands

# =========================================================
# CONFIG
# =========================================================
APPEAL_PANEL_CHANNEL_ID  = 1156363575150002226   # public panel  (#crew-write-ups)
APPEAL_REVIEW_CHANNEL_ID = 1486598266211664003   # staff review  (mod-hub)
APPEAL_LOG_CHANNEL_ID    = 1485265848099799163   # decision log

STAFF_ROLE_IDS: set[int] = {
    850391095845584937,   # Leader
    850391378559238235,   # Co-Leader
    990011447193006101,   # Manager
}

LEADER_ROLE_ID = 850391095845584937   # used for staff ping

APPEAL_COOLDOWN_HOURS = 24   # min hours between submissions per user

DATA_DIR     = "diff_data"
APPEALS_FILE = os.path.join(DATA_DIR, "appeals.json")
PANEL_FILE   = os.path.join(DATA_DIR, "appeal_panel.json")
WARN_FILE    = os.path.join(DATA_DIR, "mod_warnings.json")

DIFF_LOGO_URL = (
    "https://media.discordapp.net/attachments/1107375326625005719/"
    "1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm="
    "2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
    "&=&format=webp&quality=lossless&width=1376&height=917"
)

# ── Appeal type metadata ──────────────────────────────────
APPEAL_TYPES: dict[str, dict] = {
    "warning":    {"label": "⚠️ Warning Appeal",        "emoji": "⚠️",  "color": 0xFFA500},
    "timeout":    {"label": "⏰ Timeout / Mute Appeal",  "emoji": "⏰",  "color": 0xFF6B6B},
    "ban":        {"label": "🔨 Ban Appeal",             "emoji": "🔨",  "color": 0xFF0000},
    "kick":       {"label": "👢 Kick Review",            "emoji": "👢",  "color": 0xFF8C00},
    "build":      {"label": "🚗 Build Denial Appeal",    "emoji": "🚗",  "color": 0x5865F2},
    "exclusion":  {"label": "🏁 Meet Exclusion Appeal",  "emoji": "🏁",  "color": 0x57F287},
}


# =========================================================
# FILE HELPERS
# =========================================================
def _load(path: str, default=None):
    if default is None:
        default = {}
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _dump(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _is_staff(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    return any(r.id in STAFF_ROLE_IDS for r in member.roles)


# ── Panel ID ──────────────────────────────────────────────
def _get_panel_id() -> Optional[int]:
    v = _load(PANEL_FILE).get("panel_message_id")
    return int(v) if v else None


def _set_panel_id(msg_id: int) -> None:
    data = _load(PANEL_FILE)
    data["panel_message_id"] = msg_id
    _dump(PANEL_FILE, data)


# ── Appeals storage ───────────────────────────────────────
def _load_appeals() -> dict:
    return _load(APPEALS_FILE, {"last_id": 0, "appeals": {}})


def _next_appeal_id() -> int:
    data = _load_appeals()
    data["last_id"] = data.get("last_id", 0) + 1
    _dump(APPEALS_FILE, data)
    return data["last_id"]


def _save_appeal(appeal_id: int, record: dict) -> None:
    data = _load_appeals()
    data.setdefault("appeals", {})[str(appeal_id)] = record
    _dump(APPEALS_FILE, data)


def _get_appeal(appeal_id: int) -> Optional[dict]:
    return _load_appeals().get("appeals", {}).get(str(appeal_id))


def _update_appeal(appeal_id: int, **updates) -> None:
    data = _load_appeals()
    record = data.get("appeals", {}).get(str(appeal_id))
    if record:
        record.update(updates)
        data["appeals"][str(appeal_id)] = record
        _dump(APPEALS_FILE, data)


def _user_latest_appeal(user_id: int) -> Optional[dict]:
    """Return the most recent appeal for a user, or None."""
    data = _load_appeals()
    user_appeals = [
        r for r in data.get("appeals", {}).values()
        if r.get("user_id") == user_id
    ]
    if not user_appeals:
        return None
    return max(user_appeals, key=lambda r: r.get("created_at", ""))


def _user_on_cooldown(user_id: int) -> Optional[str]:
    """Return a cooldown message string if the user is still on cooldown, else None."""
    latest = _user_latest_appeal(user_id)
    if not latest:
        return None
    try:
        created = datetime.fromisoformat(latest["created_at"])
        if _utcnow() - created < timedelta(hours=APPEAL_COOLDOWN_HOURS):
            remaining = timedelta(hours=APPEAL_COOLDOWN_HOURS) - (_utcnow() - created)
            h, m = divmod(int(remaining.total_seconds() // 60), 60)
            return f"{h}h {m}m" if h else f"{m}m"
    except Exception:
        pass
    return None


# ── Warning reversal ─────────────────────────────────────
def _remove_latest_warning(guild_id: int, user_id: int) -> tuple[bool, str]:
    data = _load(WARN_FILE)
    gk, uk = str(guild_id), str(user_id)
    warnings = data.get(gk, {}).get(uk, [])
    if not warnings:
        return False, "No warning record found for this user."
    removed = warnings.pop()
    data.setdefault(gk, {})[uk] = warnings
    _dump(WARN_FILE, data)
    return True, f"Latest warning removed (Case #{removed.get('case_id', '?')})"


# =========================================================
# MODALS — one per appeal type for targeted questions
# =========================================================
class _BaseAppealModal(discord.ui.Modal):
    appeal_type: str = "unknown"

    extra_info = discord.ui.TextInput(
        label="Additional Context / Evidence",
        placeholder="Links, screenshots, or anything else relevant (optional).",
        style=discord.TextStyle.paragraph,
        max_length=800,
        required=False,
    )

    def __init__(self, cog: "AppealSystemCog"):
        super().__init__()
        self.cog = cog

    def _build_record(self, interaction: discord.Interaction, fields: dict) -> dict:
        appeal_id = _next_appeal_id()
        return {
            "appeal_id":       appeal_id,
            "appeal_type":     self.appeal_type,
            "guild_id":        interaction.guild.id if interaction.guild else None,
            "user_id":         interaction.user.id,
            "username":        str(interaction.user),
            "status":          "pending",
            "created_at":      _utcnow().isoformat(),
            "reviewed_by":     None,
            "reviewed_at":     None,
            "decision_note":   None,
            "review_message_id": None,
            "reversal_result": None,
            **fields,
        }

    async def _submit(
        self,
        interaction: discord.Interaction,
        record: dict,
        summary_lines: list[str],
    ) -> None:
        appeal_id = record["appeal_id"]
        _save_appeal(appeal_id, record)

        review_ch = interaction.client.get_channel(APPEAL_REVIEW_CHANNEL_ID)
        if not isinstance(review_ch, discord.TextChannel):
            return await interaction.response.send_message(
                "❌ Could not reach the staff review channel — please contact staff directly.",
                ephemeral=True,
            )

        meta   = APPEAL_TYPES.get(self.appeal_type, {"label": self.appeal_type, "color": 0x5865F2})
        embed  = discord.Embed(
            title=f"{meta['emoji']} Appeal #{appeal_id} — {meta['label']}",
            color=meta["color"],
            timestamp=_utcnow(),
        )
        embed.add_field(
            name="👤 Submitted By",
            value=f"{interaction.user.mention}\n`{interaction.user.id}`",
            inline=True,
        )
        embed.add_field(name="🏷️ Type",   value=meta["label"],    inline=True)
        embed.add_field(name="📋 Status", value="⏳ Pending Review", inline=True)
        for line in summary_lines:
            name, _, value = line.partition(": ")
            embed.add_field(name=name, value=value or "\u200b", inline=False)
        if record.get("extra_info"):
            embed.add_field(name="📎 Additional Context", value=record["extra_info"], inline=False)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="DIFF Meets • Appeal Review System")

        review_view = AppealReviewView(self.cog, appeal_id)
        self.cog.bot.add_view(review_view)

        review_msg = await review_ch.send(
            content=f"<@&{LEADER_ROLE_ID}> — New appeal submitted.",
            embed=embed,
            view=review_view,
            allowed_mentions=discord.AllowedMentions(roles=True),
        )
        _update_appeal(appeal_id, review_message_id=review_msg.id)

        confirm_embed = discord.Embed(
            title="✅ Appeal Submitted",
            description=(
                f"Your appeal (`#{appeal_id}`) has been received by DIFF staff.\n\n"
                "**What happens next:**\n"
                "• Staff will review your appeal privately\n"
                "• You'll receive a DM with the decision\n"
                "• Most appeals are reviewed within 24–48 hours\n\n"
                "*Do not open a support ticket about your appeal — it will be handled here.*"
            ),
            color=discord.Color.green(),
            timestamp=_utcnow(),
        )
        confirm_embed.set_footer(text=f"Appeal ID: #{appeal_id}  •  Different Meets")
        await interaction.response.send_message(embed=confirm_embed, ephemeral=True)


class WarningAppealModal(_BaseAppealModal, title="⚠️ Warning Appeal"):
    appeal_type = "warning"

    case_id = discord.ui.TextInput(
        label="Warning / Case ID (if known)",
        placeholder="e.g. WU-0001 — check your DM from the bot",
        max_length=30,
        required=False,
    )
    warn_reason = discord.ui.TextInput(
        label="What reason were you given for the warning?",
        placeholder="Copy the reason from your DM if you have it.",
        style=discord.TextStyle.paragraph,
        max_length=500,
        required=True,
    )
    appeal_reason = discord.ui.TextInput(
        label="Why should this warning be removed?",
        placeholder="Explain your side clearly and honestly.",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        record = self._build_record(interaction, {
            "case_id":      str(self.case_id).strip(),
            "warn_reason":  str(self.warn_reason).strip(),
            "appeal_reason": str(self.appeal_reason).strip(),
            "extra_info":   str(self.extra_info).strip(),
            "punishment_type": "warning",
        })
        await self._submit(interaction, record, [
            f"⚠️ Case ID: {record['case_id'] or 'Not provided'}",
            f"📄 Warning Reason: {record['warn_reason']}",
            f"📝 Appeal Reason: {record['appeal_reason']}",
        ])


class TimeoutAppealModal(_BaseAppealModal, title="⏰ Timeout / Mute Appeal"):
    appeal_type = "timeout"

    timeout_reason = discord.ui.TextInput(
        label="What reason were you given for the timeout?",
        style=discord.TextStyle.paragraph,
        max_length=500,
        required=True,
    )
    appeal_reason = discord.ui.TextInput(
        label="Why should the timeout be removed?",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        record = self._build_record(interaction, {
            "timeout_reason": str(self.timeout_reason).strip(),
            "appeal_reason":  str(self.appeal_reason).strip(),
            "extra_info":     str(self.extra_info).strip(),
            "punishment_type": "timeout",
        })
        await self._submit(interaction, record, [
            f"📄 Timeout Reason: {record['timeout_reason']}",
            f"📝 Appeal Reason: {record['appeal_reason']}",
        ])


class BanAppealModal(_BaseAppealModal, title="🔨 Ban Appeal"):
    appeal_type = "ban"

    ban_reason = discord.ui.TextInput(
        label="What reason were you given for the ban?",
        style=discord.TextStyle.paragraph,
        max_length=500,
        required=True,
    )
    appeal_reason = discord.ui.TextInput(
        label="Why should you be unbanned?",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=True,
    )
    acknowledgement = discord.ui.TextInput(
        label="Do you accept DIFF's rules if unbanned?",
        placeholder="Yes / No — and briefly explain.",
        max_length=200,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        record = self._build_record(interaction, {
            "ban_reason":      str(self.ban_reason).strip(),
            "appeal_reason":   str(self.appeal_reason).strip(),
            "acknowledgement": str(self.acknowledgement).strip(),
            "extra_info":      str(self.extra_info).strip(),
            "punishment_type": "ban",
        })
        await self._submit(interaction, record, [
            f"📄 Ban Reason: {record['ban_reason']}",
            f"📝 Appeal Reason: {record['appeal_reason']}",
            f"✔️ Acknowledgement: {record['acknowledgement']}",
        ])


class KickReviewModal(_BaseAppealModal, title="👢 Kick Review"):
    appeal_type = "kick"

    kick_reason = discord.ui.TextInput(
        label="What reason were you given for the kick?",
        style=discord.TextStyle.paragraph,
        max_length=500,
        required=True,
    )
    appeal_reason = discord.ui.TextInput(
        label="Why do you believe the kick was unwarranted?",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        record = self._build_record(interaction, {
            "kick_reason":   str(self.kick_reason).strip(),
            "appeal_reason": str(self.appeal_reason).strip(),
            "extra_info":    str(self.extra_info).strip(),
            "punishment_type": "kick",
        })
        await self._submit(interaction, record, [
            f"📄 Kick Reason: {record['kick_reason']}",
            f"📝 Appeal Reason: {record['appeal_reason']}",
        ])


class BuildDenialModal(_BaseAppealModal, title="🚗 Build Denial Appeal"):
    appeal_type = "build"

    car_model = discord.ui.TextInput(
        label="Car Model / Name",
        placeholder="e.g. Pegassi Zentorno, Karin Sultan RS",
        max_length=80,
        required=True,
    )
    denial_reason = discord.ui.TextInput(
        label="What reason were you given for the denial?",
        style=discord.TextStyle.paragraph,
        max_length=400,
        required=True,
    )
    appeal_reason = discord.ui.TextInput(
        label="Why should your build be reconsidered?",
        style=discord.TextStyle.paragraph,
        max_length=800,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        record = self._build_record(interaction, {
            "car_model":     str(self.car_model).strip(),
            "denial_reason": str(self.denial_reason).strip(),
            "appeal_reason": str(self.appeal_reason).strip(),
            "extra_info":    str(self.extra_info).strip(),
            "punishment_type": "build",
        })
        await self._submit(interaction, record, [
            f"🚗 Car: {record['car_model']}",
            f"📄 Denial Reason: {record['denial_reason']}",
            f"📝 Appeal Reason: {record['appeal_reason']}",
        ])


class MeetExclusionModal(_BaseAppealModal, title="🏁 Meet Exclusion Appeal"):
    appeal_type = "exclusion"

    meet_name = discord.ui.TextInput(
        label="Which meet were you excluded from?",
        placeholder="e.g. Saturday Night Imports — March 29",
        max_length=100,
        required=True,
    )
    exclusion_reason = discord.ui.TextInput(
        label="What reason were you given?",
        style=discord.TextStyle.paragraph,
        max_length=400,
        required=True,
    )
    appeal_reason = discord.ui.TextInput(
        label="Why should you have been allowed to attend?",
        style=discord.TextStyle.paragraph,
        max_length=800,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        record = self._build_record(interaction, {
            "meet_name":        str(self.meet_name).strip(),
            "exclusion_reason": str(self.exclusion_reason).strip(),
            "appeal_reason":    str(self.appeal_reason).strip(),
            "extra_info":       str(self.extra_info).strip(),
            "punishment_type":  "exclusion",
        })
        await self._submit(interaction, record, [
            f"🏁 Meet: {record['meet_name']}",
            f"📄 Exclusion Reason: {record['exclusion_reason']}",
            f"📝 Appeal Reason: {record['appeal_reason']}",
        ])


# ── Modal router ─────────────────────────────────────────
_MODAL_MAP: dict[str, type[_BaseAppealModal]] = {
    "warning":   WarningAppealModal,
    "timeout":   TimeoutAppealModal,
    "ban":       BanAppealModal,
    "kick":      KickReviewModal,
    "build":     BuildDenialModal,
    "exclusion": MeetExclusionModal,
}


# =========================================================
# STAFF DECISION MODAL
# =========================================================
class DecisionNoteModal(discord.ui.Modal, title="Appeal Decision Note"):
    note = discord.ui.TextInput(
        label="Decision Note (sent to the member)",
        placeholder="Explain the decision clearly and professionally.",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=True,
    )

    def __init__(self, cog: "AppealSystemCog", appeal_id: int, action: str):
        super().__init__()
        self.cog       = cog
        self.appeal_id = appeal_id
        self.action    = action

    async def on_submit(self, interaction: discord.Interaction) -> None:
        mod = interaction.user
        if not isinstance(mod, discord.Member) or not _is_staff(mod):
            return await interaction.response.send_message(
                "Only staff can review appeals.", ephemeral=True
            )
        await self.cog.process_decision(
            interaction, self.appeal_id, self.action, str(self.note).strip()
        )


# =========================================================
# REVIEW BUTTONS
# =========================================================
class _AppealActionButton(discord.ui.Button):
    _ACTION_STYLES = {
        "accepted":        (discord.ButtonStyle.success,   "✅", "Accept"),
        "denied":          (discord.ButtonStyle.danger,    "❌", "Deny"),
        "needs_more_info": (discord.ButtonStyle.secondary, "📨", "Need More Info"),
    }

    def __init__(self, cog: "AppealSystemCog", appeal_id: int, action: str):
        style, emoji, label = self._ACTION_STYLES[action]
        super().__init__(
            label=label, style=style, emoji=emoji,
            custom_id=f"diff_ap_{action[:4]}_{appeal_id}",
        )
        self.cog       = cog
        self.appeal_id = appeal_id
        self.action    = action

    async def callback(self, interaction: discord.Interaction) -> None:
        mod = interaction.user
        if not isinstance(mod, discord.Member) or not _is_staff(mod):
            return await interaction.response.send_message(
                "Only staff can review appeals.", ephemeral=True
            )
        await interaction.response.send_modal(
            DecisionNoteModal(self.cog, self.appeal_id, self.action)
        )


class AppealReviewView(discord.ui.View):
    def __init__(self, cog: "AppealSystemCog", appeal_id: int):
        super().__init__(timeout=None)
        self.cog       = cog
        self.appeal_id = appeal_id
        self.add_item(_AppealActionButton(cog, appeal_id, "accepted"))
        self.add_item(_AppealActionButton(cog, appeal_id, "denied"))
        self.add_item(_AppealActionButton(cog, appeal_id, "needs_more_info"))


# =========================================================
# PUBLIC PANEL — DROPDOWN
# =========================================================
class AppealSelect(discord.ui.Select):
    def __init__(self, cog: "AppealSystemCog"):
        self.cog = cog
        super().__init__(
            custom_id="diff_appeal_select_v2",
            placeholder="📋  Select the type of appeal...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Warning Appeal",
                    emoji="⚠️",
                    value="warning",
                    description="Appeal a warning or write-up you received.",
                ),
                discord.SelectOption(
                    label="Timeout / Mute Appeal",
                    emoji="⏰",
                    value="timeout",
                    description="Appeal a timeout or mute applied to your account.",
                ),
                discord.SelectOption(
                    label="Ban Appeal",
                    emoji="🔨",
                    value="ban",
                    description="Appeal a ban and request reinstatement to the server.",
                ),
                discord.SelectOption(
                    label="Kick Review",
                    emoji="👢",
                    value="kick",
                    description="Request a review of a kick from the server.",
                ),
                discord.SelectOption(
                    label="Build Denial Appeal",
                    emoji="🚗",
                    value="build",
                    description="Appeal a build denial at a DIFF meet.",
                ),
                discord.SelectOption(
                    label="Meet Exclusion Appeal",
                    emoji="🏁",
                    value="exclusion",
                    description="Appeal being excluded from a meet or event.",
                ),
                discord.SelectOption(
                    label="Check My Appeal Status",
                    emoji="🔍",
                    value="status",
                    description="Check the status of your most recent appeal.",
                ),
            ],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        value  = self.values[0]
        member = interaction.user

        # ── Status check (no cooldown gate needed) ────────────────────────────
        if value == "status":
            latest = _user_latest_appeal(member.id)
            if not latest:
                return await interaction.response.send_message(
                    embed=discord.Embed(
                        title="🔍 No Appeal Found",
                        description=(
                            "You haven't submitted any appeals yet.\n\n"
                            "Use the dropdown to submit one if you believe a staff action was unfair."
                        ),
                        color=discord.Color.light_grey(),
                    ),
                    ephemeral=True,
                )

            st     = latest.get("status", "pending")
            meta   = APPEAL_TYPES.get(latest.get("appeal_type", ""), {"label": "Appeal", "color": 0x5865F2})
            colors = {
                "pending":        discord.Color.orange(),
                "needs_more_info": discord.Color.gold(),
                "accepted":       discord.Color.green(),
                "denied":         discord.Color.red(),
            }
            icons = {
                "pending":         "⏳",
                "needs_more_info": "📨",
                "accepted":        "✅",
                "denied":          "❌",
            }
            embed = discord.Embed(
                title=f"🔍 Appeal #{latest['appeal_id']} — Status",
                color=colors.get(st, discord.Color.blurple()),
                timestamp=_utcnow(),
            )
            embed.add_field(name="📋 Type",   value=meta["label"],                     inline=True)
            embed.add_field(name="📊 Status", value=f"{icons.get(st,'?')} {st.replace('_',' ').title()}", inline=True)
            submitted = latest.get("created_at", "")
            if submitted:
                try:
                    ts = int(datetime.fromisoformat(submitted).timestamp())
                    embed.add_field(name="📅 Submitted", value=f"<t:{ts}:R>", inline=True)
                except Exception:
                    pass
            if latest.get("decision_note"):
                embed.add_field(name="📝 Staff Note", value=latest["decision_note"], inline=False)
            if latest.get("reversal_result"):
                embed.add_field(name="⚙️ Reversal Result", value=latest["reversal_result"], inline=False)
            embed.set_footer(text="Different Meets • Appeal System")
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # ── Cooldown check ────────────────────────────────────────────────────
        cooldown = _user_on_cooldown(member.id)
        if cooldown:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="⏳ Appeal Cooldown Active",
                    description=(
                        f"You submitted an appeal recently. Please wait **{cooldown}** before submitting another.\n\n"
                        "Use **Check My Appeal Status** to see your current appeal."
                    ),
                    color=discord.Color.orange(),
                ),
                ephemeral=True,
            )

        # ── Open the type-specific modal ───────────────────────────────────────
        modal_cls = _MODAL_MAP.get(value)
        if modal_cls:
            await interaction.response.send_modal(modal_cls(self.cog))
        else:
            await interaction.response.send_message(
                "Unknown appeal type — please try again.", ephemeral=True
            )


class AppealPanelView(discord.ui.View):
    def __init__(self, cog: "AppealSystemCog"):
        super().__init__(timeout=None)
        self.add_item(AppealSelect(cog))


# =========================================================
# PANEL EMBED
# =========================================================
def _panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title="📋 DIFF Appeal Center",
        color=0x5865F2,
        description=(
            "If you believe a staff action taken against you was unfair, "
            "use the dropdown below to submit an appeal for private staff review.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        ),
    )
    embed.add_field(
        name="📋 What You Can Appeal",
        value=(
            "⚠️ **Warnings** — write-ups or strikes you received\n"
            "⏰ **Timeouts** — mutes applied to your account\n"
            "🔨 **Bans** — removal from the server\n"
            "👢 **Kicks** — request a review after being kicked\n"
            "🚗 **Build Denials** — build turned away at a meet\n"
            "🏁 **Meet Exclusions** — barred from attending an event"
        ),
        inline=False,
    )
    embed.add_field(
        name="📐 Guidelines",
        value=(
            "• Be **honest and respectful** — troll appeals are denied without review\n"
            "• Include your **Case / Warning ID** if you have it\n"
            "• You may submit **one appeal every 24 hours**\n"
            "• Do **not** argue in public channels — it will be used against your case\n"
            "• Appeals are reviewed privately by staff within **24–48 hours**"
        ),
        inline=False,
    )
    embed.add_field(
        name="⚙️ Auto-Reversals on Acceptance",
        value=(
            "• ⚠️ Warning → latest warning removed automatically\n"
            "• ⏰ Timeout → cleared immediately\n"
            "• 🔨 Ban → user unbanned automatically\n"
            "• 👢 Kick → manual reinvite required *(Discord limitation)*"
        ),
        inline=False,
    )
    embed.set_thumbnail(url=DIFF_LOGO_URL)
    embed.set_footer(text="Different Meets • Appeal System  •  Select an option below ↓")
    return embed


# =========================================================
# COG
# =========================================================
class AppealSystemCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot        = bot
        self.panel_view = AppealPanelView(self)
        self.bot.add_view(self.panel_view)

    # ── Punishment reversal ───────────────────────────────
    async def reverse_punishment(
        self,
        guild: Optional[discord.Guild],
        user_id: int,
        punishment_type: str,
    ) -> str:
        pt = (punishment_type or "").lower().strip()

        if pt in {"warning", "warn"}:
            if guild is None:
                return "Warning reversal skipped: guild not found."
            ok, msg = _remove_latest_warning(guild.id, user_id)
            return msg

        if pt in {"timeout", "mute"}:
            if guild is None:
                return "Timeout reversal skipped: guild not found."
            member = guild.get_member(user_id)
            if member is None:
                try:
                    member = await guild.fetch_member(user_id)
                except Exception:
                    member = None
            if member is None:
                return "Timeout reversal skipped: member no longer in server."
            try:
                await member.timeout(None, reason="Accepted appeal — timeout cleared")
                return "Timeout cleared automatically."
            except Exception as e:
                return f"Timeout reversal failed: {str(e)[:300]}"

        if pt == "ban":
            if guild is None:
                return "Ban reversal skipped: guild not found."
            try:
                await guild.unban(
                    discord.Object(id=user_id),
                    reason="Accepted appeal — ban removed",
                )
                return "User unbanned automatically."
            except Exception as e:
                return f"Ban reversal failed: {str(e)[:300]}"

        if pt == "kick":
            return "Kick cannot be reversed automatically — manual reinvite required."

        return f"No automatic reversal configured for `{pt}`."

    # ── Log helper ────────────────────────────────────────
    async def _log(self, channel_id: int, **kwargs) -> None:
        ch = self.bot.get_channel(channel_id)
        if isinstance(ch, discord.TextChannel):
            try:
                await ch.send(**kwargs)
            except Exception:
                pass

    # ── Decision processor ────────────────────────────────
    async def process_decision(
        self,
        interaction: discord.Interaction,
        appeal_id: int,
        action: str,
        note: str,
    ) -> None:
        appeal = _get_appeal(appeal_id)
        if not appeal:
            return await interaction.response.send_message(
                "Appeal record not found.", ephemeral=True
            )
        if appeal.get("status") in {"accepted", "denied"}:
            return await interaction.response.send_message(
                "That appeal has already been fully reviewed.", ephemeral=True
            )

        label_map = {
            "accepted":        "Accepted ✅",
            "denied":          "Denied ❌",
            "needs_more_info": "Needs More Info 📨",
        }
        color_map = {
            "accepted":        discord.Color.green(),
            "denied":          discord.Color.red(),
            "needs_more_info": discord.Color.gold(),
        }
        status_label = label_map.get(action, action)
        color        = color_map.get(action, discord.Color.blurple())

        reversal_result: Optional[str] = None
        if action == "accepted":
            reversal_result = await self.reverse_punishment(
                guild=interaction.guild,
                user_id=appeal["user_id"],
                punishment_type=appeal.get("punishment_type", ""),
            )

        _update_appeal(
            appeal_id,
            status=action,
            reviewed_by=interaction.user.id,
            reviewed_at=_utcnow().isoformat(),
            decision_note=note,
            reversal_result=reversal_result,
        )

        meta = APPEAL_TYPES.get(appeal.get("appeal_type", ""), {"label": "Appeal", "emoji": "📋"})

        # Edit the review message
        try:
            updated = discord.Embed(
                title=f"{meta['emoji']} Appeal #{appeal_id} — {meta['label']}",
                color=color,
                timestamp=_utcnow(),
            )
            updated.add_field(
                name="👤 User",
                value=f"<@{appeal['user_id']}>\n`{appeal['user_id']}`",
                inline=True,
            )
            updated.add_field(name="📋 Status",      value=status_label,              inline=True)
            updated.add_field(name="👮 Reviewed By", value=interaction.user.mention,  inline=True)
            updated.add_field(name="📝 Decision Note", value=note,                   inline=False)
            if reversal_result:
                updated.add_field(name="⚙️ Punishment Reversal", value=reversal_result, inline=False)
            updated.set_footer(text="DIFF Meets • Appeal Review System")
            await interaction.message.edit(embed=updated, view=None)
        except Exception:
            pass

        # Log embed
        log_embed = discord.Embed(
            title=f"{meta['emoji']} Appeal {status_label} — #{appeal_id}",
            color=color,
            timestamp=_utcnow(),
        )
        log_embed.add_field(name="Appeal ID",    value=f"`#{appeal_id}`",                                       inline=True)
        log_embed.add_field(name="User",         value=f"<@{appeal['user_id']}> `{appeal['user_id']}`",         inline=True)
        log_embed.add_field(name="Reviewer",     value=f"{interaction.user.mention} `{interaction.user.id}`",   inline=True)
        log_embed.add_field(name="Type",         value=meta["label"],                                           inline=False)
        log_embed.add_field(name="Decision Note", value=note,                                                   inline=False)
        if reversal_result:
            log_embed.add_field(name="⚙️ Reversal", value=reversal_result, inline=False)
        log_embed.set_footer(text="DIFF Meets • Appeal Logs")
        await self._log(APPEAL_LOG_CHANNEL_ID, embed=log_embed)

        # DM the member
        try:
            user = (
                interaction.client.get_user(appeal["user_id"])
                or await interaction.client.fetch_user(appeal["user_id"])
            )
            dm = discord.Embed(
                title=f"📋 Your Appeal Has Been Reviewed — #{appeal_id}",
                description=(
                    f"Your **{meta['label']}** in **Different Meets** has been reviewed by staff.\n\n"
                    f"**Status:** {status_label}\n"
                    f"**Staff Note:** {note}"
                ),
                color=color,
                timestamp=_utcnow(),
            )
            if reversal_result:
                dm.add_field(name="⚙️ Punishment Reversal", value=reversal_result, inline=False)
            dm.set_footer(text="Different Meets • Appeal System")
            await user.send(embed=dm)
        except Exception:
            pass

        confirm = f"Appeal `#{appeal_id}` marked as **{status_label}**."
        if reversal_result:
            confirm += f"\n⚙️ Reversal: {reversal_result}"
        await interaction.response.send_message(confirm, ephemeral=True)

    # ── Panel management — RETIRED ─────────────────────────
    # Appeals are now handled through the unified DIFF Support Center panel
    # in #support-center (bot.py SupportDropdownView + AppealDropdown).
    # This cog no longer posts its own standalone panel.
    async def ensure_panel(self) -> None:
        print("[AppealSystem] Standalone appeal panel is retired — appeals now use the Support Center.")

    # ── Events / commands ─────────────────────────────────
    @commands.Cog.listener()
    async def on_ready(self):
        data = _load_appeals()
        restored = 0
        for appeal_id_str, appeal in data.get("appeals", {}).items():
            if appeal.get("status") in {"pending", "needs_more_info"}:
                try:
                    self.bot.add_view(AppealReviewView(self, int(appeal_id_str)))
                    restored += 1
                except Exception:
                    pass
        print(f"[AppealSystem] Restored {restored} pending review views.")
        # Panel is now in the unified Support Center — no standalone panel to post.

    @commands.command(name="post_appeal_panel")
    @commands.has_permissions(administrator=True)
    async def cmd_post_panel(self, ctx: commands.Context):
        try:
            await ctx.message.delete()
        except Exception:
            pass
        await ctx.send(
            "ℹ️ The standalone appeal panel is retired.\n"
            "Appeals are now handled through the **DIFF Support Center** panel in <#1156363575150002226>.\n"
            "Use `/post-support-panel` or `!refreshsupportpanel` to refresh that panel.",
            delete_after=15,
        )

    @commands.command(name="appeal_lookup")
    @commands.has_permissions(manage_messages=True)
    async def cmd_lookup(self, ctx: commands.Context, appeal_id: int):
        """Look up an appeal by ID."""
        record = _get_appeal(appeal_id)
        if not record:
            return await ctx.send(f"No appeal found with ID `#{appeal_id}`.", delete_after=10)
        meta  = APPEAL_TYPES.get(record.get("appeal_type", ""), {"label": "Appeal", "emoji": "📋"})
        st    = record.get("status", "pending")
        embed = discord.Embed(
            title=f"{meta['emoji']} Appeal #{appeal_id}",
            color=0x5865F2,
            timestamp=_utcnow(),
        )
        embed.add_field(name="User",     value=f"<@{record['user_id']}> `{record['user_id']}`", inline=True)
        embed.add_field(name="Type",     value=meta["label"],                                   inline=True)
        embed.add_field(name="Status",   value=st.replace("_", " ").title(),                    inline=True)
        if record.get("decision_note"):
            embed.add_field(name="Decision Note", value=record["decision_note"], inline=False)
        embed.set_footer(text="DIFF Meets • Appeal Lookup")
        await ctx.send(embed=embed, delete_after=60)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AppealSystemCog(bot))
