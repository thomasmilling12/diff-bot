import asyncio
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import discord
from discord.ext import commands

# =========================================================
# CONFIG
# =========================================================

ANNOUNCEMENT_PANEL_CHANNEL_ID = 1486228191243669646
MANAGER_DASHBOARD_CHANNEL_ID  = 1486228191243669646  # change with !setdiffdashboard
HOST_ROLE_ID                  = 1055823929358430248
URGENT_PING_ROLE_ID           = 0
STAFF_LOG_CHANNEL_ID          = 1485265848099799163
PUNISHMENT_LOG_CHANNEL_ID     = 0

MANAGER_ROLE_IDS: list[int] = []

REMINDER_DELAY_MINUTES    = 15
ESCALATION_DELAY_MINUTES  = 30
AUTO_ESCALATE_USE_URGENT_ROLE = True

PANEL_HEADER_URL        = ""
ANNOUNCEMENT_BANNER_URL = ""
DIFF_LOGO_URL           = ""

DATA_FILE = Path("diff_data/host_team_announcement_panel.json")

ANNOUNCEMENT_PANEL_TITLES = {
    "🏁 DIFF Intelligence Announcement Center",
    "🏁 DIFF Announcement Intelligence Center",
    "🏁 DIFF Host Team Announcement Center",
    "📢 DIFF Host Team Announcement Panel",
}


# =========================================================
# STORAGE
# =========================================================

def load_data() -> dict:
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_data(data: dict) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def ensure_data_shape(data: dict) -> dict:
    data.setdefault("announcement_panel_message_id", None)
    data.setdefault("dashboard_panel_message_id", None)
    data.setdefault("announcements", {})
    data.setdefault("host_stats", {})
    return data


# =========================================================
# HELPERS
# =========================================================

ANNOUNCEMENT_TYPES = {
    "general_update": {
        "label": "General Update",
        "emoji": "📢",
        "title_prefix": "DIFF Host Update",
        "color": 0xF59E0B,
    },
    "host_call": {
        "label": "Host Call",
        "emoji": "🎤",
        "title_prefix": "DIFF Host Call",
        "color": 0xFB923C,
    },
    "reminder": {
        "label": "Reminder",
        "emoji": "⏰",
        "title_prefix": "DIFF Host Reminder",
        "color": 0xFBBF24,
    },
    "schedule_notice": {
        "label": "Schedule Notice",
        "emoji": "📅",
        "title_prefix": "DIFF Schedule Notice",
        "color": 0xD97706,
    },
    "urgent_notice": {
        "label": "Urgent Notice",
        "emoji": "🚨",
        "title_prefix": "DIFF Urgent Notice",
        "color": 0xEF4444,
    },
    "meeting_notice": {
        "label": "Meeting Notice",
        "emoji": "🧠",
        "title_prefix": "DIFF Team Meeting",
        "color": 0xF97316,
    },
}

TYPE_KEYWORDS = {
    "schedule_notice": [
        "schedule", "assigned", "assignment", "hosting slot", "availability",
        "calendar", "rescheduled", "swap", "time change", "time moved",
    ],
    "reminder": [
        "reminder", "don't forget", "make sure", "check in", "be ready", "remember",
    ],
    "host_call": [
        "who can host", "need host", "hosts respond", "reply below", "check availability",
        "need coverage", "roll call", "can anyone host",
    ],
    "meeting_notice": [
        "meeting", "vc", "voice chat", "briefing", "discussion", "staff meeting",
    ],
    "urgent_notice": [
        "urgent", "immediately", "asap", "right now", "critical", "important notice",
        "emergency", "do this now",
    ],
}

URGENT_WORDS = [
    "urgent", "asap", "immediately", "right now", "critical", "emergency",
    "must", "important", "do this now", "need this fixed", "required today",
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def detect_urgent(body: str, title: str = "") -> bool:
    haystack = clean_text(f"{title} {body}")
    return any(word in haystack for word in URGENT_WORDS)


def suggest_announcement_type(body: str, title: str = "") -> str:
    haystack = clean_text(f"{title} {body}")
    best_key = "general_update"
    best_score = 0
    for key, keywords in TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in haystack)
        if score > best_score:
            best_key = key
            best_score = score
    if best_score == 0 and detect_urgent(body, title):
        return "urgent_notice"
    return best_key


def user_is_manager(member: discord.Member) -> bool:
    if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
        return True
    if MANAGER_ROLE_IDS:
        role_ids = {role.id for role in member.roles}
        return any(rid in role_ids for rid in MANAGER_ROLE_IDS)
    return False


def get_host_ping() -> str:
    return f"<@&{HOST_ROLE_ID}>"


def get_urgent_ping() -> str:
    return f"<@&{URGENT_PING_ROLE_ID}>" if URGENT_PING_ROLE_ID else ""


def maybe_set_image(embed: discord.Embed, url: str) -> None:
    if url and url.strip():
        embed.set_image(url=url.strip())


def maybe_set_thumbnail(embed: discord.Embed, url: str) -> None:
    if url and url.strip():
        embed.set_thumbnail(url=url.strip())


def get_target_host_ids(guild: discord.Guild) -> list[int]:
    role = guild.get_role(HOST_ROLE_ID)
    if not role:
        return []
    return [m.id for m in role.members if not m.bot]


def get_member_display(guild: discord.Guild, user_id: int) -> str:
    member = guild.get_member(user_id)
    return member.display_name if member else f"User {user_id}"


def ensure_host_stat(data: dict, user_id: int, display_name: str = "") -> dict:
    stats = data["host_stats"].setdefault(str(user_id), {
        "name": display_name or f"User {user_id}",
        "total_required": 0,
        "acknowledged": 0,
        "missed": 0,
        "response_seconds_total": 0.0,
        "response_count": 0,
        "weekly_acknowledged": 0,
        "weekly_missed": 0,
        "warning_count": 0,
        "flagged": False,
        "last_warning_reason": "",
        "last_updated": utc_now_iso(),
    })
    if display_name:
        stats["name"] = display_name
    stats["last_updated"] = utc_now_iso()
    return stats


def format_seconds(seconds: float) -> str:
    if seconds <= 0:
        return "—"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if minutes >= 60:
        hours = minutes // 60
        minutes = minutes % 60
        return f"{hours}h {minutes}m"
    return f"{minutes}m {secs}s"


def leaderboard_rows(data: dict) -> list[tuple]:
    rows = []
    for user_id, stat in data["host_stats"].items():
        total = stat.get("total_required", 0)
        ack   = stat.get("acknowledged", 0)
        missed = stat.get("missed", 0)
        pct   = (ack / total * 100.0) if total else 0.0
        avg   = (
            stat.get("response_seconds_total", 0.0) / stat.get("response_count", 1)
            if stat.get("response_count", 0) else 0.0
        )
        rows.append((pct, -avg, -ack, user_id, stat.get("name", user_id), total, ack, missed, avg))
    rows.sort(reverse=True)
    return rows


def ignored_announcements_list(data: dict) -> list[tuple]:
    items = []
    for ann_id, record in data["announcements"].items():
        if record.get("closed"):
            missing = record.get("missing_host_ids_final", [])
            if missing:
                items.append((record.get("created_at", ""), ann_id, record.get("title", "No title"), missing))
    items.sort(reverse=True)
    return items


def apply_miss_to_host(data: dict, guild: discord.Guild, user_id: int) -> tuple[dict, str | None]:
    stats = ensure_host_stat(data, user_id, get_member_display(guild, user_id))
    stats["missed"]        = int(stats.get("missed", 0)) + 1
    stats["weekly_missed"] = int(stats.get("weekly_missed", 0)) + 1
    reason = None
    if stats["missed"] == 3:
        stats["warning_count"]       = int(stats.get("warning_count", 0)) + 1
        stats["last_warning_reason"] = "Missed 3 announcements"
        reason = "Missed 3 announcements → warning threshold reached."
    elif stats["missed"] == 5:
        stats["warning_count"]       = int(stats.get("warning_count", 0)) + 1
        stats["flagged"]             = True
        stats["last_warning_reason"] = "Missed 5 announcements"
        reason = "Missed 5 announcements → host flagged for managers."
    return stats, reason


# =========================================================
# EMBEDS
# =========================================================

def build_announcement_panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🏁 DIFF Intelligence Announcement Center",
        description=(
            "Managers can send smart host announcements from one control panel.\n\n"
            "**Features**\n"
            "• Auto-suggest announcement type from message text\n"
            "• Urgent wording detection\n"
            "• Auto reminders (15 min) + escalation (30 min)\n"
            "• Host acknowledgement tracking\n"
            "• Response speed leaderboard + discipline tracking\n\n"
            "📋 **Staff Commands**\n"
            "`!diffsuitepanels` — Refresh both panels\n"
            "`!sethostrole @role` — Set host role to track\n"
            "`!seturgentrole @role` — Set urgent ping role\n"
            "`!setdifflogchannel #ch` — Set staff log channel\n"
            "`!setdiffpunishchannel #ch` — Set discipline log channel\n"
            "`!setdiffdashboard #ch` — Move manager dashboard\n"
            "`!resetdiffweekly` — Reset weekly stats"
        ),
        color=0xF59E0B,
    )
    embed.add_field(
        name="How It Works",
        value=(
            "1. Press **Create Smart Announcement**\n"
            "2. Type your message\n"
            "3. DIFF suggests the type automatically\n"
            "4. Hosts click **Seen / Acknowledged**\n"
            "5. Reminders and logs happen automatically"
        ),
        inline=False,
    )
    maybe_set_image(embed, PANEL_HEADER_URL)
    maybe_set_thumbnail(embed, DIFF_LOGO_URL)
    embed.set_footer(text="DIFF • Intelligence Suite")
    return embed


def build_dashboard_panel_embed(data: dict) -> discord.Embed:
    total_ann   = len(data["announcements"])
    open_ann    = sum(1 for a in data["announcements"].values() if not a.get("closed"))
    total_hosts = len(data["host_stats"])
    total_flags = sum(1 for s in data["host_stats"].values() if s.get("flagged"))
    total_warns = sum(int(s.get("warning_count", 0)) for s in data["host_stats"].values())

    embed = discord.Embed(
        title="📱 DIFF Manager Dashboard",
        description=(
            "Use the buttons below to view live announcement stats, "
            "host performance, and ignored announcements."
        ),
        color=0xF59E0B,
    )
    embed.add_field(name="Announcements",   value=str(total_ann),   inline=True)
    embed.add_field(name="Open / Tracking", value=str(open_ann),    inline=True)
    embed.add_field(name="Hosts Tracked",   value=str(total_hosts), inline=True)
    embed.add_field(name="Warnings",        value=str(total_warns), inline=True)
    embed.add_field(name="Flagged Hosts",   value=str(total_flags), inline=True)
    embed.add_field(
        name="Reminder Cycle",
        value=f"{REMINDER_DELAY_MINUTES}m / {ESCALATION_DELAY_MINUTES}m",
        inline=True,
    )
    maybe_set_thumbnail(embed, DIFF_LOGO_URL)
    embed.set_footer(text="DIFF • Manager Dashboard")
    return embed


def build_sent_embed(
    member: discord.Member,
    announcement_type: str,
    custom_title: str,
    body: str,
    urgent_mode: bool,
) -> discord.Embed:
    info = ANNOUNCEMENT_TYPES[announcement_type]
    title_text = custom_title.strip() if custom_title.strip() else info["title_prefix"]
    if urgent_mode:
        title_text = f"URGENT • {title_text}"
    embed = discord.Embed(
        title=f"{info['emoji']} {title_text}",
        description=body,
        color=info["color"],
    )
    embed.set_author(
        name=f"DIFF Management • {member.display_name}",
        icon_url=member.display_avatar.url,
    )
    embed.add_field(name="Type",    value=info["label"],   inline=True)
    embed.add_field(name="Sent By", value=member.mention,  inline=True)
    embed.add_field(name="Target",  value=get_host_ping(), inline=True)
    if urgent_mode:
        embed.add_field(name="Priority", value="Urgent mode enabled", inline=False)
    maybe_set_image(embed, ANNOUNCEMENT_BANNER_URL)
    maybe_set_thumbnail(embed, DIFF_LOGO_URL)
    embed.set_footer(text="Press the button below once you have seen this.")
    return embed


def build_log_embed(guild: discord.Guild, announcement_id: str, record: dict) -> discord.Embed:
    ack_ids     = record.get("acknowledged_host_ids", [])
    missing_ids = record.get("missing_host_ids_current", [])
    ack_preview     = "\n".join(f"• {get_member_display(guild, uid)}" for uid in ack_ids[:15]) or "None yet"
    missing_preview = "\n".join(f"• {get_member_display(guild, uid)}" for uid in missing_ids[:15]) or "None"

    embed = discord.Embed(
        title="📊 DIFF Announcement Log",
        color=0xF59E0B,
        timestamp=utc_now(),
    )
    embed.add_field(name="Announcement ID", value=announcement_id,                              inline=False)
    embed.add_field(name="Type",     value=record.get("type_label", "Unknown"),                 inline=True)
    embed.add_field(name="Urgent",   value="Yes" if record.get("urgent_mode") else "No",        inline=True)
    embed.add_field(name="Closed",   value="Yes" if record.get("closed") else "No",             inline=True)
    embed.add_field(name="Title",    value=record.get("title", "No title"),                     inline=False)
    embed.add_field(name="Acknowledged", value=str(len(ack_ids)),                               inline=True)
    embed.add_field(name="Missing",  value=str(len(missing_ids)),                               inline=True)
    embed.add_field(name="Message Link", value=record.get("jump_url", "Unavailable"),           inline=True)
    embed.add_field(name="Acknowledged By", value=ack_preview[:1024],                          inline=False)
    embed.add_field(name="Still Missing",   value=missing_preview[:1024],                      inline=False)
    maybe_set_thumbnail(embed, DIFF_LOGO_URL)
    embed.set_footer(text="DIFF • Staff Dashboard")
    return embed


def build_warning_embed(guild: discord.Guild, user_id: int, stats: dict, reason: str) -> discord.Embed:
    embed = discord.Embed(
        title="⚠️ DIFF Host Discipline Notice",
        description=f"{get_member_display(guild, user_id)} has reached a discipline threshold.",
        color=0xEF4444,
        timestamp=utc_now(),
    )
    embed.add_field(name="Host",     value=f"<@{user_id}>",                     inline=True)
    embed.add_field(name="Warnings", value=str(stats.get("warning_count", 0)),   inline=True)
    embed.add_field(name="Flagged",  value="Yes" if stats.get("flagged") else "No", inline=True)
    embed.add_field(name="Reason",   value=reason,                               inline=False)
    maybe_set_thumbnail(embed, DIFF_LOGO_URL)
    embed.set_footer(text="DIFF • Discipline Tracking")
    return embed


def build_stats_embed(data: dict) -> discord.Embed:
    total       = len(data["announcements"])
    closed      = sum(1 for a in data["announcements"].values() if a.get("closed"))
    acknowledged = sum(len(a.get("acknowledged_host_ids", [])) for a in data["announcements"].values())
    reminders   = sum(1 for a in data["announcements"].values() if a.get("reminder_sent"))
    escalations = sum(1 for a in data["announcements"].values() if a.get("escalation_sent"))

    embed = discord.Embed(title="📈 DIFF Announcement Stats", color=0xF59E0B, timestamp=utc_now())
    embed.add_field(name="Total Announcements",   value=str(total),        inline=True)
    embed.add_field(name="Closed",                value=str(closed),       inline=True)
    embed.add_field(name="Total Acknowledgements",value=str(acknowledged), inline=True)
    embed.add_field(name="Reminders Sent",        value=str(reminders),    inline=True)
    embed.add_field(name="Escalations Sent",      value=str(escalations),  inline=True)
    maybe_set_thumbnail(embed, DIFF_LOGO_URL)
    embed.set_footer(text="DIFF • Manager Dashboard")
    return embed


def build_leaderboard_embed(data: dict) -> discord.Embed:
    rows = leaderboard_rows(data)
    embed = discord.Embed(title="🏆 DIFF Host Responsiveness Leaderboard", color=0xF59E0B, timestamp=utc_now())
    if not rows:
        embed.description = "No host stats yet."
        return embed

    top_lines = []
    for idx, row in enumerate(rows[:10], start=1):
        pct, _, _, user_id, name, total, ack, missed, avg = row
        top_lines.append(f"**{idx}. {name}** — {pct:.0f}% ack | avg {format_seconds(avg)} | missed {missed}")

    low_rows = sorted(rows, key=lambda x: (x[0], -x[8], -x[7]))[:5]
    low_lines = []
    for row in low_rows:
        pct, _, _, user_id, name, total, ack, missed, avg = row
        low_lines.append(f"**{name}** — {pct:.0f}% ack | avg {format_seconds(avg)} | missed {missed}")

    embed.add_field(name="Top Hosts",          value="\n".join(top_lines)[:1024],              inline=False)
    embed.add_field(name="Lowest Performers",  value=("\n".join(low_lines) or "None")[:1024],  inline=False)
    maybe_set_thumbnail(embed, DIFF_LOGO_URL)
    embed.set_footer(text="DIFF • Weekly Host Performance")
    return embed


def build_ignored_embed(guild: discord.Guild, data: dict) -> discord.Embed:
    items = ignored_announcements_list(data)
    embed = discord.Embed(title="🚫 DIFF Ignored Announcements", color=0xEF4444, timestamp=utc_now())
    if not items:
        embed.description = "No ignored announcements recorded."
        return embed

    lines = []
    for created_at, ann_id, title, missing in items[:10]:
        missing_names = ", ".join(get_member_display(guild, uid) for uid in missing[:5])
        if len(missing) > 5:
            missing_names += f" +{len(missing) - 5} more"
        lines.append(f"**{title}**\nMissing: {missing_names}\nID: `{ann_id}`")
    embed.description = "\n\n".join(lines)[:4096]
    maybe_set_thumbnail(embed, DIFF_LOGO_URL)
    embed.set_footer(text="DIFF • Manager Review")
    return embed


# =========================================================
# TRACKING / DISCIPLINE
# =========================================================

async def update_staff_log(bot: commands.Bot, guild: discord.Guild, announcement_id: str) -> None:
    if not STAFF_LOG_CHANNEL_ID:
        return
    data   = ensure_data_shape(load_data())
    record = data["announcements"].get(announcement_id)
    if not record:
        return
    log_channel = guild.get_channel(STAFF_LOG_CHANNEL_ID)
    if not isinstance(log_channel, discord.TextChannel):
        return
    log_message_id = record.get("log_message_id")
    if log_message_id:
        try:
            msg = await log_channel.fetch_message(log_message_id)
            await msg.edit(embed=build_log_embed(guild, announcement_id, record))
            return
        except Exception:
            pass
    try:
        new_msg = await log_channel.send(embed=build_log_embed(guild, announcement_id, record))
        data["announcements"][announcement_id]["log_message_id"] = new_msg.id
        save_data(data)
    except Exception as e:
        print(f"[HostTeamAnnouncementPanel] Staff log error: {e}")


async def maybe_send_discipline_notice(
    bot: commands.Bot, guild: discord.Guild, user_id: int, stats: dict, reason: str
) -> None:
    target = PUNISHMENT_LOG_CHANNEL_ID or STAFF_LOG_CHANNEL_ID
    if not target:
        return
    channel = guild.get_channel(target)
    if not isinstance(channel, discord.TextChannel):
        return
    try:
        await channel.send(embed=build_warning_embed(guild, user_id, stats, reason))
    except Exception:
        pass


# =========================================================
# ACK VIEW — per-announcement dynamic custom_id
# =========================================================

class AckButton(discord.ui.Button):
    def __init__(self, announcement_id: str):
        super().__init__(
            label="Seen / Acknowledged",
            emoji="✅",
            style=discord.ButtonStyle.green,
            custom_id=f"diff_ann_ack_{announcement_id}",
        )
        self.announcement_id = announcement_id

    async def callback(self, interaction: discord.Interaction) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("This can only be used inside the server.", ephemeral=True)
            return

        if HOST_ROLE_ID:
            role_ids = {r.id for r in interaction.user.roles}
            if HOST_ROLE_ID not in role_ids and not user_is_manager(interaction.user):
                await interaction.response.send_message(
                    "Only hosts or managers can acknowledge announcements.", ephemeral=True
                )
                return

        data   = ensure_data_shape(load_data())
        record = data["announcements"].get(self.announcement_id)
        if not record:
            await interaction.response.send_message("Announcement record not found.", ephemeral=True)
            return

        uid     = interaction.user.id
        ack_ids = set(record.get("acknowledged_host_ids", []))
        if uid in ack_ids:
            await interaction.response.send_message("You already acknowledged this announcement.", ephemeral=True)
            return

        ack_ids.add(uid)
        record["acknowledged_host_ids"] = sorted(ack_ids)
        missing_current = set(record.get("target_host_ids", [])) - ack_ids
        record["missing_host_ids_current"] = sorted(missing_current)

        created_at       = parse_iso(record["created_at"])
        response_seconds = max((utc_now() - created_at).total_seconds(), 0.0)

        host_stats = ensure_host_stat(data, uid, interaction.user.display_name)
        host_stats["acknowledged"]           = int(host_stats.get("acknowledged", 0)) + 1
        host_stats["weekly_acknowledged"]    = int(host_stats.get("weekly_acknowledged", 0)) + 1
        host_stats["response_seconds_total"] = float(host_stats.get("response_seconds_total", 0.0)) + response_seconds
        host_stats["response_count"]         = int(host_stats.get("response_count", 0)) + 1

        save_data(data)
        await update_staff_log(interaction.client, interaction.guild, self.announcement_id)
        await interaction.response.send_message("✅ Acknowledged.", ephemeral=True)


class AnnouncementAcknowledgeView(discord.ui.View):
    def __init__(self, announcement_id: str):
        super().__init__(timeout=None)
        self.announcement_id = announcement_id
        self.add_item(AckButton(announcement_id))


# =========================================================
# MODAL + CONFIRM
# =========================================================

class SmartAnnouncementModal(discord.ui.Modal, title="Create Smart Announcement"):
    custom_title = discord.ui.TextInput(
        label="Title (optional)",
        placeholder="Leave blank to use the suggested DIFF title",
        required=False,
        max_length=100,
    )
    body_text = discord.ui.TextInput(
        label="Announcement message",
        placeholder="Type the host announcement here...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=2000,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("This can only be used in a server.", ephemeral=True)
            return
        if not user_is_manager(interaction.user):
            await interaction.response.send_message("You do not have permission to use this panel.", ephemeral=True)
            return

        suggested_type = suggest_announcement_type(self.body_text.value, self.custom_title.value or "")
        urgent_detected = detect_urgent(self.body_text.value, self.custom_title.value or "")

        info    = ANNOUNCEMENT_TYPES[suggested_type]
        preview = discord.Embed(
            title="🧠 Smart Suggestion Ready",
            description=(
                f"**Suggested Type:** {info['emoji']} {info['label']}\n"
                f"**Urgent Detected:** {'Yes ⚠️' if urgent_detected else 'No'}\n\n"
                "Press **Send Announcement** to post it."
            ),
            color=info["color"],
        )
        preview.add_field(
            name="Preview Title",
            value=(self.custom_title.value or info["title_prefix"]),
            inline=False,
        )
        preview.add_field(name="Preview Body", value=self.body_text.value[:1024], inline=False)

        await interaction.response.send_message(
            embed=preview,
            view=SmartAnnouncementConfirmView(
                suggested_type=suggested_type,
                urgent_detected=urgent_detected,
                draft_title=self.custom_title.value or "",
                draft_body=self.body_text.value,
            ),
            ephemeral=True,
        )


class SmartAnnouncementConfirmView(discord.ui.View):
    def __init__(self, suggested_type: str, urgent_detected: bool, draft_title: str, draft_body: str):
        super().__init__(timeout=600)
        self.suggested_type  = suggested_type
        self.urgent_detected = urgent_detected
        self.draft_title     = draft_title
        self.draft_body      = draft_body

    @discord.ui.button(label="Send Announcement", emoji="📢", style=discord.ButtonStyle.blurple)
    async def send_announcement(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("This can only be used in a server.", ephemeral=True)
            return
        if not user_is_manager(interaction.user):
            await interaction.response.send_message("You do not have permission to use this panel.", ephemeral=True)
            return

        panel_channel = interaction.guild.get_channel(ANNOUNCEMENT_PANEL_CHANNEL_ID)
        if not isinstance(panel_channel, discord.TextChannel):
            await interaction.response.send_message("Announcement panel channel not found.", ephemeral=True)
            return

        urgent_mode = self.urgent_detected
        pings = [get_host_ping()]
        if urgent_mode and AUTO_ESCALATE_USE_URGENT_ROLE and get_urgent_ping():
            pings.append(get_urgent_ping())
        content = " ".join(x for x in pings if x).strip()

        embed = build_sent_embed(
            member=interaction.user,
            announcement_type=self.suggested_type,
            custom_title=self.draft_title,
            body=self.draft_body,
            urgent_mode=urgent_mode,
        )

        announcement_id = f"ann-{int(utc_now().timestamp())}-{interaction.user.id}"
        ack_view = AnnouncementAcknowledgeView(announcement_id)
        interaction.client.add_view(ack_view)

        sent_message = await panel_channel.send(
            content=content,
            embed=embed,
            view=ack_view,
            allowed_mentions=discord.AllowedMentions(roles=True, users=True, everyone=False),
        )

        data = ensure_data_shape(load_data())
        target_host_ids = get_target_host_ids(interaction.guild)

        for host_id in target_host_ids:
            ensure_host_stat(data, host_id, get_member_display(interaction.guild, host_id))
            data["host_stats"][str(host_id)]["total_required"] = (
                int(data["host_stats"][str(host_id)].get("total_required", 0)) + 1
            )

        data["announcements"][announcement_id] = {
            "title":                  self.draft_title.strip() or ANNOUNCEMENT_TYPES[self.suggested_type]["title_prefix"],
            "type":                   self.suggested_type,
            "type_label":             ANNOUNCEMENT_TYPES[self.suggested_type]["label"],
            "urgent_mode":            urgent_mode,
            "message_id":             sent_message.id,
            "channel_id":             sent_message.channel.id,
            "jump_url":               sent_message.jump_url,
            "created_by_id":          interaction.user.id,
            "created_by_name":        interaction.user.display_name,
            "created_at":             utc_now_iso(),
            "target_host_ids":        sorted(target_host_ids),
            "acknowledged_host_ids":  [],
            "missing_host_ids_current": sorted(target_host_ids),
            "missing_host_ids_final": [],
            "reminder_sent":          False,
            "reminder_sent_at":       None,
            "escalation_sent":        False,
            "escalation_sent_at":     None,
            "log_message_id":         None,
            "closed":                 False,
        }
        save_data(data)

        await update_staff_log(interaction.client, interaction.guild, announcement_id)
        await interaction.response.send_message("✅ Smart announcement sent.", ephemeral=True)
        self.stop()

    @discord.ui.button(label="Cancel", emoji="❌", style=discord.ButtonStyle.gray)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_message("Cancelled.", ephemeral=True)
        self.stop()


# =========================================================
# PANEL VIEWS
# =========================================================

class IntelligencePanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Create Smart Announcement",
        emoji="🧠",
        style=discord.ButtonStyle.blurple,
        custom_id="diff_suite_create_announcement",
    )
    async def create_smart_announcement(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("This can only be used in a server.", ephemeral=True)
            return
        if not user_is_manager(interaction.user):
            await interaction.response.send_message("You do not have permission to use this panel.", ephemeral=True)
            return
        await interaction.response.send_modal(SmartAnnouncementModal())

    @discord.ui.button(
        label="Refresh Announcement Panel",
        emoji="♻️",
        style=discord.ButtonStyle.gray,
        custom_id="diff_suite_refresh_announcement_panel",
    )
    async def refresh_panel(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("This can only be used in a server.", ephemeral=True)
            return
        if not user_is_manager(interaction.user):
            await interaction.response.send_message("You do not have permission to use this panel.", ephemeral=True)
            return
        await ensure_announcement_panel(interaction.client)
        await interaction.response.send_message("✅ Announcement panel refreshed.", ephemeral=True)


class ManagerDashboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="View Announcement Stats",
        emoji="📈",
        style=discord.ButtonStyle.blurple,
        custom_id="diff_suite_view_stats",
    )
    async def view_stats(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not user_is_manager(interaction.user):
            await interaction.response.send_message("You do not have permission.", ephemeral=True)
            return
        data = ensure_data_shape(load_data())
        await interaction.response.send_message(embed=build_stats_embed(data), ephemeral=True)

    @discord.ui.button(
        label="View Host Performance",
        emoji="🏆",
        style=discord.ButtonStyle.green,
        custom_id="diff_suite_view_leaderboard",
    )
    async def view_leaderboard(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not user_is_manager(interaction.user):
            await interaction.response.send_message("You do not have permission.", ephemeral=True)
            return
        data = ensure_data_shape(load_data())
        await interaction.response.send_message(embed=build_leaderboard_embed(data), ephemeral=True)

    @discord.ui.button(
        label="View Ignored Announcements",
        emoji="🚫",
        style=discord.ButtonStyle.red,
        custom_id="diff_suite_view_ignored",
    )
    async def view_ignored(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not user_is_manager(interaction.user):
            await interaction.response.send_message("You do not have permission.", ephemeral=True)
            return
        data = ensure_data_shape(load_data())
        await interaction.response.send_message(
            embed=build_ignored_embed(interaction.guild, data), ephemeral=True
        )

    @discord.ui.button(
        label="Refresh Dashboard",
        emoji="♻️",
        style=discord.ButtonStyle.gray,
        custom_id="diff_suite_refresh_dashboard",
    )
    async def refresh_dashboard(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not user_is_manager(interaction.user):
            await interaction.response.send_message("You do not have permission.", ephemeral=True)
            return
        await ensure_dashboard_panel(interaction.client)
        await interaction.response.send_message("✅ Dashboard refreshed.", ephemeral=True)


# =========================================================
# UNIFIED HOST TEAM PANEL
# =========================================================

UNIFIED_HOST_TEAM_TAG = "Different Meets • Host Team"

_UNIFIED_OLD_FOOTER_TAGS = frozenset({
    "DIFF Meets • Host System • DIFF_HOST_TEAM_PANEL",
    "DIFF • Intelligence Suite",
    "DIFF • Manager Dashboard",
})
_UNIFIED_OLD_TITLES = frozenset({
    "🏁 DIFF HOST TEAM CHAT",
    "🏁 DIFF Intelligence Announcement Center",
    "🏁 DIFF Announcement Intelligence Center",
    "🏁 DIFF Host Team Announcement Center",
    "📢 DIFF Host Team Announcement Panel",
    "📱 DIFF Manager Dashboard",
})

_CHANNEL_LINKS = [
    ("📅", "Schedule / Planning",  "https://discord.com/channels/850386896509337710/1089579004517953546"),
    ("📍", "Meet Coordination",    "https://discord.com/channels/850386896509337710/1091157191895023626"),
    ("🚫", "Blacklist / Reports",  "https://discord.com/channels/850386896509337710/1057016810261712938"),
    ("📊", "Staff Logs",           "https://discord.com/channels/850386896509337710/1485265848099799163"),
    ("🛠️", "Host Tools",           "https://discord.com/channels/850386896509337710/1485840926612918383"),
    ("💬", "Host Team Chat",       "https://discord.com/channels/850386896509337710/1485830232270307410"),
]


def build_unified_host_team_embed(data: dict | None = None) -> discord.Embed:
    if data is None:
        data = ensure_data_shape(load_data())
    total_ann  = len(data["announcements"])
    open_ann   = sum(1 for a in data["announcements"].values() if not a.get("closed"))
    total_warn = sum(int(s.get("warning_count", 0)) for s in data["host_stats"].values())
    flagged    = sum(1 for s in data["host_stats"].values() if s.get("flagged"))

    embed = discord.Embed(
        title="🏁 DIFF Host Team",
        description="*Host coordination hub for DIFF meet leaders.*",
        color=0xC9A227,
    )
    maybe_set_thumbnail(embed, DIFF_LOGO_URL)
    embed.add_field(
        name="🚨 Coordination Rules",
        value=(
            "• Stay active and communicate clearly\n"
            "• Coordinate locations, themes, and timing\n"
            "• Check the blacklist before hosting\n"
            "• Keep everything organised and professional"
        ),
        inline=False,
    )
    embed.add_field(
        name="📢 Smart Announcement System",
        value=(
            "• Auto-suggests type from your message text\n"
            "• Detects urgent wording automatically\n"
            "• Auto-reminders (15 min) + escalation (30 min)\n"
            "• Tracks host acknowledgements and response speed"
        ),
        inline=False,
    )
    embed.add_field(name="Announcements",  value=str(total_ann),  inline=True)
    embed.add_field(name="Open / Active",  value=str(open_ann),   inline=True)
    embed.add_field(name="Warnings",       value=str(total_warn), inline=True)
    embed.add_field(name="Flagged Hosts",  value=str(flagged),    inline=True)
    embed.add_field(
        name="Reminder Cycle",
        value=f"{REMINDER_DELAY_MINUTES}m / {ESCALATION_DELAY_MINUTES}m",
        inline=True,
    )
    embed.set_footer(text=UNIFIED_HOST_TEAM_TAG + "  |  Announcement tools are Manager+ only")
    embed.timestamp = datetime.now(timezone.utc)
    return embed


class _HostTeamActionSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="🛠️  Announcement & Manager Tools",
            options=[
                discord.SelectOption(
                    label="Create Smart Announcement", value="create_ann", emoji="🧠",
                    description="Send a tracked announcement to the host team",
                ),
                discord.SelectOption(
                    label="View Announcement Stats", value="view_stats", emoji="📈",
                    description="Total announcements, reminders, and ack counts",
                ),
                discord.SelectOption(
                    label="View Host Performance", value="view_perf", emoji="🏆",
                    description="Host responsiveness leaderboard",
                ),
                discord.SelectOption(
                    label="View Ignored Announcements", value="view_ignored", emoji="🚫",
                    description="Announcements with missing acknowledgements",
                ),
                discord.SelectOption(
                    label="Refresh Panel", value="refresh", emoji="♻️",
                    description="Update this panel with the latest live stats",
                ),
            ],
            custom_id="diff_hostteam_unified:actions",
            row=2,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        val = self.values[0]
        if val == "refresh":
            await ensure_unified_host_team_panel(interaction.client)
            await interaction.response.send_message("✅ Host Team panel refreshed.", ephemeral=True)
            return
        if not isinstance(interaction.user, discord.Member) or not user_is_manager(interaction.user):
            return await interaction.response.send_message("Manager+ only.", ephemeral=True)
        if val == "create_ann":
            await interaction.response.send_modal(SmartAnnouncementModal())
        elif val == "view_stats":
            data = ensure_data_shape(load_data())
            await interaction.response.send_message(embed=build_stats_embed(data), ephemeral=True)
        elif val == "view_perf":
            data = ensure_data_shape(load_data())
            await interaction.response.send_message(embed=build_leaderboard_embed(data), ephemeral=True)
        elif val == "view_ignored":
            data = ensure_data_shape(load_data())
            await interaction.response.send_message(
                embed=build_ignored_embed(interaction.guild, data), ephemeral=True
            )


class UnifiedHostTeamView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for emoji, label, url in _CHANNEL_LINKS[:3]:
            self.add_item(discord.ui.Button(
                label=label, url=url, emoji=emoji,
                style=discord.ButtonStyle.link, row=0,
            ))
        for emoji, label, url in _CHANNEL_LINKS[3:]:
            self.add_item(discord.ui.Button(
                label=label, url=url, emoji=emoji,
                style=discord.ButtonStyle.link, row=1,
            ))
        self.add_item(_HostTeamActionSelect())


async def ensure_unified_host_team_panel(bot: commands.Bot) -> None:
    channel = bot.get_channel(ANNOUNCEMENT_PANEL_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        try:
            channel = await bot.fetch_channel(ANNOUNCEMENT_PANEL_CHANNEL_ID)
        except Exception:
            return
    if not isinstance(channel, discord.TextChannel):
        return

    data  = ensure_data_shape(load_data())
    embed = build_unified_host_team_embed(data)
    view  = UnifiedHostTeamView()

    unified_msg = None
    to_delete: list[discord.Message] = []

    async for msg in channel.history(limit=60):
        if msg.author.id != bot.user.id or not msg.embeds:
            continue
        footer_text = msg.embeds[0].footer.text if msg.embeds[0].footer else ""
        embed_title = msg.embeds[0].title or ""
        is_unified = footer_text.startswith(UNIFIED_HOST_TEAM_TAG)
        is_old = footer_text in _UNIFIED_OLD_FOOTER_TAGS or embed_title in _UNIFIED_OLD_TITLES
        if is_unified and unified_msg is None:
            unified_msg = msg
        elif is_unified or is_old:
            to_delete.append(msg)

    for m in to_delete:
        try:
            await m.delete()
        except Exception:
            pass

    if unified_msg:
        try:
            await unified_msg.edit(embed=embed, view=view)
            print("[UnifiedHostTeam] Panel refreshed.")
            return
        except Exception:
            pass

    try:
        await channel.send(embed=embed, view=view)
        print("[UnifiedHostTeam] Panel posted.")
    except Exception as e:
        print(f"[UnifiedHostTeam] Post failed: {e}")


# =========================================================
# PANEL MANAGEMENT
# =========================================================

async def _get_channel(bot: commands.Bot, channel_id: int) -> discord.TextChannel | None:
    ch = bot.get_channel(channel_id)
    if isinstance(ch, discord.TextChannel):
        return ch
    try:
        ch = await bot.fetch_channel(channel_id)
        return ch if isinstance(ch, discord.TextChannel) else None
    except Exception as e:
        print(f"[HostTeamAnnouncementPanel] Channel {channel_id} not found: {e}")
        return None


async def ensure_announcement_panel(bot: commands.Bot) -> None:
    data    = ensure_data_shape(load_data())
    channel = await _get_channel(bot, ANNOUNCEMENT_PANEL_CHANNEL_ID)
    if not channel:
        return

    embed      = build_announcement_panel_embed()
    view       = IntelligencePanelView()
    message_id = data.get("announcement_panel_message_id")

    if message_id:
        try:
            msg = await channel.fetch_message(message_id)
            await msg.edit(content=None, embed=embed, view=view)
            print("[HostTeamAnnouncementPanel] Announcement panel refreshed.")
            return
        except discord.NotFound:
            pass
        except Exception as e:
            print(f"[HostTeamAnnouncementPanel] Could not edit announcement panel: {e}")

    try:
        async for msg in channel.history(limit=50):
            if msg.author == bot.user and msg.embeds and msg.embeds[0].title in ANNOUNCEMENT_PANEL_TITLES:
                await msg.edit(content=None, embed=embed, view=view)
                data["announcement_panel_message_id"] = msg.id
                save_data(data)
                print("[HostTeamAnnouncementPanel] Found old announcement panel and refreshed it.")
                return
    except Exception as e:
        print(f"[HostTeamAnnouncementPanel] History scan failed: {e}")

    new_msg = await channel.send(embed=embed, view=view)
    data["announcement_panel_message_id"] = new_msg.id
    save_data(data)
    print("[HostTeamAnnouncementPanel] New announcement panel posted.")


async def ensure_dashboard_panel(bot: commands.Bot) -> None:
    data    = ensure_data_shape(load_data())
    channel = await _get_channel(bot, MANAGER_DASHBOARD_CHANNEL_ID)
    if not channel:
        return

    embed      = build_dashboard_panel_embed(data)
    view       = ManagerDashboardView()
    message_id = data.get("dashboard_panel_message_id")

    if message_id:
        try:
            msg = await channel.fetch_message(message_id)
            await msg.edit(content=None, embed=embed, view=view)
            return
        except discord.NotFound:
            pass
        except Exception as e:
            print(f"[HostTeamAnnouncementPanel] Could not edit dashboard panel: {e}")

    try:
        async for msg in channel.history(limit=50):
            if msg.author == bot.user and msg.embeds and msg.embeds[0].title == "📱 DIFF Manager Dashboard":
                await msg.edit(content=None, embed=embed, view=view)
                data["dashboard_panel_message_id"] = msg.id
                save_data(data)
                return
    except Exception:
        pass

    new_msg = await channel.send(embed=embed, view=view)
    data["dashboard_panel_message_id"] = new_msg.id
    save_data(data)
    print("[HostTeamAnnouncementPanel] New dashboard panel posted.")


# =========================================================
# BACKGROUND REMINDER LOOP
# =========================================================

async def process_open_announcements(bot: commands.Bot) -> None:
    data    = ensure_data_shape(load_data())
    changed = False

    for announcement_id, record in list(data["announcements"].items()):
        if record.get("closed"):
            continue

        channel = bot.get_channel(record.get("channel_id", 0))
        if not isinstance(channel, discord.TextChannel):
            continue

        guild      = channel.guild
        created_at = parse_iso(record["created_at"])
        elapsed    = utc_now() - created_at

        target_ids = set(record.get("target_host_ids", []))
        ack_ids    = set(record.get("acknowledged_host_ids", []))
        missing_ids = sorted(target_ids - ack_ids)
        record["missing_host_ids_current"] = missing_ids

        ann_changed = False

        if (
            elapsed >= timedelta(minutes=REMINDER_DELAY_MINUTES)
            and not record.get("reminder_sent")
            and missing_ids
        ):
            mentions = " ".join(f"<@{uid}>" for uid in missing_ids[:25])
            try:
                await channel.send(
                    content=f"⏰ Reminder: the following hosts still need to acknowledge this announcement.\n{mentions}",
                    allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
                )
                record["reminder_sent"]    = True
                record["reminder_sent_at"] = utc_now_iso()
                ann_changed = True
                changed     = True
            except Exception:
                pass

        if (
            elapsed >= timedelta(minutes=ESCALATION_DELAY_MINUTES)
            and not record.get("escalation_sent")
        ):
            if missing_ids:
                parts = ["🚨 Escalation: some hosts still have not acknowledged this announcement."]
                if AUTO_ESCALATE_USE_URGENT_ROLE and get_urgent_ping():
                    parts.append(get_urgent_ping())
                parts.append(" ".join(f"<@{uid}>" for uid in missing_ids[:25]))
                try:
                    await channel.send(
                        content="\n".join(p for p in parts if p),
                        allowed_mentions=discord.AllowedMentions(users=True, roles=True, everyone=False),
                    )
                except Exception:
                    pass

                for user_id in missing_ids:
                    stats, reason = apply_miss_to_host(data, guild, user_id)
                    if reason:
                        await maybe_send_discipline_notice(bot, guild, user_id, stats, reason)

            record["escalation_sent"]    = True
            record["escalation_sent_at"] = utc_now_iso()
            record["closed"]             = True
            record["missing_host_ids_final"] = missing_ids
            ann_changed = True
            changed     = True

        if ann_changed:
            await update_staff_log(bot, guild, announcement_id)

    if changed:
        save_data(data)
        await ensure_unified_host_team_panel(bot)


# =========================================================
# COG
# =========================================================

class HostTeamAnnouncementPanel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot          = bot
        self.reminder_task = None
        self.bot.add_view(IntelligencePanelView())
        self.bot.add_view(ManagerDashboardView())
        self.bot.add_view(UnifiedHostTeamView())

    @commands.Cog.listener()
    async def on_ready(self):
        if getattr(self.bot, "_diff_host_team_announcement_panel_ready", False):
            return
        self.bot._diff_host_team_announcement_panel_ready = True

        data = ensure_data_shape(load_data())
        for announcement_id in data.get("announcements", {}).keys():
            self.bot.add_view(AnnouncementAcknowledgeView(announcement_id))

        await ensure_unified_host_team_panel(self.bot)

        if self.reminder_task is None:
            self.reminder_task = self.bot.loop.create_task(self._reminder_loop())

        print("[HostTeamAnnouncementPanel] Cog ready.")

    async def _reminder_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                await process_open_announcements(self.bot)
            except Exception as e:
                print(f"[HostTeamAnnouncementPanel] Reminder loop error: {e}")
            await asyncio.sleep(60)

    def cog_unload(self):
        if self.reminder_task:
            self.reminder_task.cancel()

    @commands.command(name="diffsuitepanels")
    @commands.has_permissions(manage_guild=True)
    async def diffsuitepanels(self, ctx: commands.Context):
        await ensure_unified_host_team_panel(self.bot)
        try:
            await ctx.message.delete()
        except Exception:
            pass
        await ctx.send("✅ Host Team panel refreshed.", delete_after=8)

    @commands.command(name="hostannouncepanel")
    @commands.has_permissions(manage_guild=True)
    async def hostannouncepanel(self, ctx: commands.Context):
        await ensure_unified_host_team_panel(self.bot)
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="sethostrole")
    @commands.has_permissions(administrator=True)
    async def sethostrole(self, ctx: commands.Context, role: discord.Role):
        global HOST_ROLE_ID
        HOST_ROLE_ID = role.id
        await ctx.send(f"✅ Host role set to {role.mention}", delete_after=10)

    @commands.command(name="seturgentrole")
    @commands.has_permissions(administrator=True)
    async def seturgentrole(self, ctx: commands.Context, role: discord.Role):
        global URGENT_PING_ROLE_ID
        URGENT_PING_ROLE_ID = role.id
        await ctx.send(f"✅ Urgent role set to {role.mention}", delete_after=10)

    @commands.command(name="setdifflogchannel")
    @commands.has_permissions(administrator=True)
    async def setdifflogchannel(self, ctx: commands.Context, channel: discord.TextChannel):
        global STAFF_LOG_CHANNEL_ID
        STAFF_LOG_CHANNEL_ID = channel.id
        await ctx.send(f"✅ Staff log channel set to {channel.mention}", delete_after=10)

    @commands.command(name="setdiffpunishchannel")
    @commands.has_permissions(administrator=True)
    async def setdiffpunishchannel(self, ctx: commands.Context, channel: discord.TextChannel):
        global PUNISHMENT_LOG_CHANNEL_ID
        PUNISHMENT_LOG_CHANNEL_ID = channel.id
        await ctx.send(f"✅ Discipline log channel set to {channel.mention}", delete_after=10)

    @commands.command(name="setdiffdashboard")
    @commands.has_permissions(administrator=True)
    async def setdiffdashboard(self, ctx: commands.Context, channel: discord.TextChannel):
        global MANAGER_DASHBOARD_CHANNEL_ID
        MANAGER_DASHBOARD_CHANNEL_ID = channel.id
        await ensure_unified_host_team_panel(self.bot)
        await ctx.send(f"✅ Dashboard channel set to {channel.mention}", delete_after=10)

    @commands.command(name="resetdiffweekly")
    @commands.has_permissions(administrator=True)
    async def resetdiffweekly(self, ctx: commands.Context):
        data = ensure_data_shape(load_data())
        for stat in data["host_stats"].values():
            stat["weekly_acknowledged"] = 0
            stat["weekly_missed"]       = 0
        save_data(data)
        await ctx.send("✅ Weekly DIFF stats reset.", delete_after=10)


async def setup(bot: commands.Bot):
    await bot.add_cog(HostTeamAnnouncementPanel(bot))
