from __future__ import annotations

import asyncio
import json
import os
import re
from datetime import datetime, timezone, timedelta
from typing import Optional

import discord
from discord.ext import commands

# Common timezone abbreviation → UTC offset (minutes)
_TZ_OFFSETS: dict[str, int] = {
    "UTC": 0, "GMT": 0,
    "EST": -300, "EDT": -240,
    "CST": -360, "CDT": -300,
    "MST": -420, "MDT": -360,
    "PST": -480, "PDT": -420,
    "AST": -240, "ADT": -180,
    "HST": -600, "AKST": -540, "AKDT": -480,
    "BST": 60,   "CET": 60,    "CEST": 120,
    "EET": 120,  "EEST": 180,
    "IST": 330,  "JST": 540,   "AEST": 600, "AEDT": 660,
}

_DATE_FORMATS = [
    "%B %d %Y %I:%M %p",
    "%B %d %Y %I%p",
    "%B %d, %Y %I:%M %p",
    "%B %d, %Y %I%p",
    "%m/%d/%Y %I:%M %p",
    "%m/%d/%Y %I%p",
    "%m/%d/%Y %H:%M",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d %I:%M %p",
    "%B %d %I:%M %p",
    "%B %d %I%p",
]


def _parse_datetime(text: str) -> Optional[int]:
    """
    Parse a human-readable date string typed by the host into a UTC unix timestamp.
    Supports timezone abbreviations (EST, PST, UTC, etc.) at the end of the string.
    Returns the unix timestamp on success, None on failure.
    """
    text = text.strip()

    # Pull timezone abbreviation off the end if present
    tz_offset_minutes = 0   # default to UTC
    tz_found = False
    parts = text.rsplit(None, 1)
    if len(parts) == 2 and parts[-1].upper() in _TZ_OFFSETS:
        tz_offset_minutes = _TZ_OFFSETS[parts[-1].upper()]
        text = parts[0].strip()
        tz_found = True

    # Normalise AM/PM spacing so "9PM" → "9 PM"
    text = re.sub(r"(\d)(AM|PM|am|pm)", r"\1 \2", text, flags=re.IGNORECASE)
    # Collapse extra spaces
    text = re.sub(r"\s+", " ", text).strip()

    # If no year in the string, inject current year
    if not re.search(r"\b(202\d|203\d)\b", text):
        text = text + f" {datetime.now(timezone.utc).year}"

    for fmt in _DATE_FORMATS:
        try:
            naive = datetime.strptime(text, fmt)
            # Apply the timezone offset
            tz = timezone(timedelta(minutes=tz_offset_minutes))
            aware = naive.replace(tzinfo=tz)
            return int(aware.timestamp())
        except ValueError:
            continue

    return None

# =========================================================
# CONFIG
# =========================================================
TARGET_CHANNEL_ID    = 1486589047232135309
GUILD_ID             = 850386896509337710
LOG_CHANNEL_ID       = 1485265848099799163   # staff-logs

# Staff roles that can create events / refresh panel
STAFF_ROLE_IDS = {
    850391095845584937,   # Leader
    850391378559238235,   # Co-Leader
    990011447193006101,   # Manager
}

COLLAB_REVIEW_ROLE_ID  = 0                  # <-- role pinged in collab tickets
COLLAB_CATEGORY_ID     = 0                  # <-- category where collab tickets are created
CREW_MEMBER_ROLE_ID    = 886702076552441927  # pinged when a new crew event is posted

DATA_DIR        = "diff_data"
DATA_FILE       = os.path.join(DATA_DIR, "crew_events_panel.json")
EVENTS_FILE     = os.path.join(DATA_DIR, "crew_events_data.json")
COLLAB_FILE     = os.path.join(DATA_DIR, "crew_collab_data.json")

DIFF_LOGO_URL = (
    "https://media.discordapp.net/attachments/1107375326625005719/"
    "1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm="
    "2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
    "&=&format=webp&quality=lossless&width=1376&height=917"
)

EMBED_COLOR   = 0x5865F2
SUCCESS_COLOR = 0x57F287
WARNING_COLOR = 0xFEE75C
ERROR_COLOR   = 0xED4245
PANEL_TAG     = "DIFF_CREW_EVENTS_PANEL"


# =========================================================
# JSON HELPERS
# =========================================================
def _ensure_dirs() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


def _load(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(path: str, data: dict) -> None:
    _ensure_dirs()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def _get_panel_msg_id() -> Optional[int]:
    v = _load(DATA_FILE).get("panel_message_id")
    return int(v) if v else None


def _set_panel_msg_id(mid: int) -> None:
    d = _load(DATA_FILE)
    d["panel_message_id"] = mid
    _save(DATA_FILE, d)


def _load_events() -> dict:
    d = _load(EVENTS_FILE)
    d.setdefault("events", {})
    return d


def _save_events(data: dict) -> None:
    _save(EVENTS_FILE, data)


def _clean_name(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9-]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text[:40] if text else "collab"


def _now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def _make_event_id() -> str:
    return str(int(datetime.now(timezone.utc).timestamp() * 1000))


# =========================================================
# PERMISSION HELPER
# =========================================================
def _is_staff(member: discord.Member) -> bool:
    if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
        return True
    return any(r.id in STAFF_ROLE_IDS for r in member.roles)


# =========================================================
# EVENT EMBED BUILDER
# =========================================================
def _event_embed(event_id: str, event: dict) -> discord.Embed:
    counts = event.get("counts", {})
    embed = discord.Embed(
        title="🏁 DIFF Official Crew Event",
        color=EMBED_COLOR,
        description=(
            f"**Event ID:** `{event_id}`\n"
            f"**Title:** {event.get('title', 'Untitled Event')}\n"
            f"**Date:** <t:{event.get('timestamp', _now_ts())}:F>\n"
            f"**Starts:** <t:{event.get('timestamp', _now_ts())}:R>\n"
            f"**Host:** {event.get('host', 'Not set')}\n"
            f"**Theme:** {event.get('theme', 'Not set')}"
        ),
    )
    embed.add_field(name="Event Notes", value=event.get("notes", "No extra notes."), inline=False)
    embed.add_field(
        name="RSVP Tracking",
        value=(
            f"✅ Attending: **{counts.get('attending', 0)}**\n"
            f"❓ Maybe: **{counts.get('maybe', 0)}**\n"
            f"❌ Not Attending: **{counts.get('not_attending', 0)}**"
        ),
        inline=False,
    )
    embed.add_field(name="How to Join", value="Use the buttons below to submit your RSVP.", inline=False)
    embed.set_thumbnail(url=DIFF_LOGO_URL)
    embed.set_footer(text=f"DIFF Crew Events System • Event ID: {event_id}")
    return embed


# =========================================================
# MODALS
# =========================================================
class CreateEventModal(discord.ui.Modal, title="Create Crew Event"):
    title_input = discord.ui.TextInput(
        label="Event Title", placeholder="Example: Friday Night Crew Meet",
        required=True, max_length=100,
    )
    timestamp_input = discord.ui.TextInput(
        label="Date & Time",
        placeholder="Example: March 28 9:00 PM EST  or  03/28 9PM PST",
        required=True, max_length=50,
    )
    host_input = discord.ui.TextInput(
        label="Host", placeholder="@Host or Host Name",
        required=True, max_length=100,
    )
    theme_input = discord.ui.TextInput(
        label="Theme", placeholder="Example: Clean JDM / Crew Collab / Pop-Up Meet",
        required=True, max_length=100,
    )
    notes_input = discord.ui.TextInput(
        label="Event Notes", placeholder="Extra rules, location details, or event notes",
        required=False, style=discord.TextStyle.paragraph, max_length=500,
    )

    def __init__(self, cog: "CrewEventsCog"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        member = interaction.user if isinstance(interaction.user, discord.Member) else None
        if member is None or not _is_staff(member):
            return await interaction.response.send_message(
                "Only staff can create official crew events.", ephemeral=True
            )

        ts = _parse_datetime(str(self.timestamp_input))
        if ts is None:
            return await interaction.response.send_message(
                "❌ Couldn't read that date/time. Try one of these formats:\n"
                "• `March 28 9:00 PM EST`\n"
                "• `03/28/2026 9PM PST`\n"
                "• `2026-03-28 21:00 UTC`\n\n"
                "Supported zones: EST, EDT, CST, CDT, MST, MDT, PST, PDT, UTC, GMT, and more.",
                ephemeral=True,
            )

        event_id = _make_event_id()
        events = _load_events()
        events["events"][event_id] = {
            "title":      str(self.title_input),
            "timestamp":  ts,
            "host":       str(self.host_input),
            "theme":      str(self.theme_input),
            "notes":      str(self.notes_input) if str(self.notes_input).strip() else "No extra notes.",
            "message_id": None,
            "channel_id": interaction.channel_id,
            "rsvps":      {},
            "counts":     {"attending": 0, "maybe": 0, "not_attending": 0},
            "created_by": interaction.user.id,
            "created_at": _now_ts(),
        }
        _save_events(events)

        view  = EventRSVPView(self.cog, event_id)
        embed = _event_embed(event_id, events["events"][event_id])

        crew_role = interaction.guild.get_role(CREW_MEMBER_ROLE_ID) if interaction.guild else None
        ping_content = crew_role.mention if crew_role else None

        await interaction.response.send_message(
            content=ping_content,
            embed=embed,
            view=view,
            allowed_mentions=discord.AllowedMentions(roles=True),
        )

        sent = await interaction.original_response()
        events = _load_events()
        if event_id in events["events"]:
            events["events"][event_id]["message_id"] = sent.id
            _save_events(events)

        # Bind view to the specific message for correct restart recovery
        self.cog.bot.add_view(view, message_id=sent.id)

        await self.cog.log_action(
            interaction.guild,
            f"📅 Created crew event `{event_id}` in <#{interaction.channel_id}> by {interaction.user.mention}"
        )


class CollabRequestModal(discord.ui.Modal, title="Crew Collab Request"):
    crew_name    = discord.ui.TextInput(label="Other Crew Name", placeholder="Example: Evolution", required=True, max_length=100)
    contact_name = discord.ui.TextInput(label="Contact / Representative", placeholder="Their leader or staff contact", required=True, max_length=100)
    idea         = discord.ui.TextInput(label="Collab Idea", placeholder="What kind of event or collab are you requesting?",
                                        required=True, style=discord.TextStyle.paragraph, max_length=400)
    availability = discord.ui.TextInput(label="Availability", placeholder="Example: Fridays or Saturdays after 8 PM EST", required=True, max_length=150)
    extra_notes  = discord.ui.TextInput(label="Extra Notes", placeholder="Anything else staff should know",
                                        required=False, style=discord.TextStyle.paragraph, max_length=400)

    def __init__(self, cog: "CrewEventsCog"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            return await interaction.response.send_message("This can only be used in the server.", ephemeral=True)

        if COLLAB_CATEGORY_ID == 0:
            return await interaction.response.send_message(
                "The collab ticket system is not fully configured yet. "
                "Please ask staff to set the collab ticket category.",
                ephemeral=True,
            )

        category = guild.get_channel(COLLAB_CATEGORY_ID)
        if not isinstance(category, discord.CategoryChannel):
            return await interaction.response.send_message(
                "Could not find the collab ticket category. Contact staff.", ephemeral=True
            )

        review_role = guild.get_role(COLLAB_REVIEW_ROLE_ID) if COLLAB_REVIEW_ROLE_ID else None
        requester   = interaction.user
        collabs     = _load(COLLAB_FILE)

        existing_id = collabs.get(str(requester.id))
        if existing_id:
            existing_ch = guild.get_channel(int(existing_id))
            if existing_ch:
                return await interaction.response.send_message(
                    f"You already have an open collab request: {existing_ch.mention}", ephemeral=True
                )
            collabs.pop(str(requester.id), None)
            _save(COLLAB_FILE, collabs)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            requester: discord.PermissionOverwrite(
                view_channel=True, send_messages=True,
                read_message_history=True, attach_files=True, embed_links=True,
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True, send_messages=True,
                manage_channels=True, manage_messages=True, read_message_history=True,
            ),
        }
        if review_role:
            overwrites[review_role] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True,
                manage_messages=True, manage_channels=True,
                attach_files=True, embed_links=True,
            )

        await interaction.response.defer(ephemeral=True)

        ticket_ch = await guild.create_text_channel(
            name=f"collab-{_clean_name(str(self.crew_name))}-{_clean_name(requester.display_name)[:12]}",
            category=category,
            overwrites=overwrites,
            topic=f"DIFF Crew Collab | crew_collab_request_user_id:{requester.id} | status:open",
            reason=f"Crew collab request for {requester}",
        )

        collabs[str(requester.id)] = ticket_ch.id
        _save(COLLAB_FILE, collabs)

        embed = discord.Embed(
            title="🤝 Crew Collab Request",
            description="A new private crew collab request has been submitted.",
            color=EMBED_COLOR,
        )
        embed.add_field(name="Submitted By",              value=requester.mention,          inline=False)
        embed.add_field(name="Other Crew Name",           value=str(self.crew_name),        inline=True)
        embed.add_field(name="Contact / Representative",  value=str(self.contact_name),     inline=True)
        embed.add_field(name="Availability",              value=str(self.availability),     inline=False)
        embed.add_field(name="Collab Idea",               value=str(self.idea),             inline=False)
        if str(self.extra_notes).strip():
            embed.add_field(name="Extra Notes", value=str(self.extra_notes), inline=False)
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.set_footer(text="DIFF Crew Events • Collab Request")

        content = requester.mention + (f" {review_role.mention}" if review_role else "")
        await ticket_ch.send(
            content=content,
            embed=embed,
            view=CollabTicketView(self.cog),
            allowed_mentions=discord.AllowedMentions(users=True, roles=True),
        )

        await interaction.followup.send(
            f"Your collab request ticket has been created: {ticket_ch.mention}", ephemeral=True
        )
        await self.cog.log_action(
            guild, f"🤝 Opened collab ticket {ticket_ch.mention} for {requester.mention}"
        )


# =========================================================
# VIEWS
# =========================================================
class EventRSVPView(discord.ui.View):
    """
    NOTE: custom_ids are unique per event_id so each event's buttons are
    bound to their own message via bot.add_view(..., message_id=...).
    """
    def __init__(self, cog: "CrewEventsCog", event_id: str):
        super().__init__(timeout=None)
        self.cog      = cog
        self.event_id = event_id

        # Inject event_id into each button's custom_id at creation time
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.custom_id:
                child.custom_id = f"{child.custom_id}:{event_id}"

    async def _update_rsvp(self, interaction: discord.Interaction, status: str):
        events = _load_events()
        event  = events.get("events", {}).get(self.event_id)
        if not event:
            return await interaction.response.send_message(
                "This event could not be found.", ephemeral=True
            )

        uid      = str(interaction.user.id)
        previous = event["rsvps"].get(uid)
        labels   = {"attending": "Attending ✅", "maybe": "Maybe ❓", "not_attending": "Not Attending ❌"}

        if previous == status:
            return await interaction.response.send_message(
                f"Your RSVP is already set to **{labels[status]}**.", ephemeral=True
            )

        if previous in event["counts"]:
            event["counts"][previous] = max(0, event["counts"][previous] - 1)
        event["rsvps"][uid]     = status
        event["counts"][status] = event["counts"].get(status, 0) + 1
        _save_events(events)

        try:
            await interaction.message.edit(embed=_event_embed(self.event_id, event), view=self)
        except Exception:
            pass

        await interaction.response.send_message(
            f"Your RSVP has been updated to **{labels[status]}**.", ephemeral=True
        )

    @discord.ui.button(label="Attending",     emoji="✅", style=discord.ButtonStyle.success,   custom_id="crew_event_attending")
    async def attending(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._update_rsvp(interaction, "attending")

    @discord.ui.button(label="Maybe",         emoji="❓", style=discord.ButtonStyle.secondary,  custom_id="crew_event_maybe")
    async def maybe(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._update_rsvp(interaction, "maybe")

    @discord.ui.button(label="Not Attending", emoji="❌", style=discord.ButtonStyle.danger,    custom_id="crew_event_not_attending")
    async def not_attending(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._update_rsvp(interaction, "not_attending")


class CrewEventsPanelView(discord.ui.View):
    def __init__(self, cog: "CrewEventsCog"):
        super().__init__(timeout=None)
        self.cog = cog
        self.add_item(discord.ui.Button(
            label="Crew Control Hub",
            emoji="🏁",
            url="https://discord.com/channels/850386896509337710/1486589047232135309",
            style=discord.ButtonStyle.link,
        ))
        self.add_item(discord.ui.Button(
            label="Color Lab",
            emoji="🎨",
            url="https://discord.com/channels/850386896509337710/1177449010949259355",
            style=discord.ButtonStyle.link,
        ))

    @discord.ui.select(
        placeholder="⚡ Select an action...",
        custom_id="crew_events_combined_select_v1",
        options=[
            discord.SelectOption(
                label="Create Event", value="create_event", emoji="📅",
                description="Post a new crew event (staff only)",
            ),
            discord.SelectOption(
                label="View Upcoming Events", value="view_upcoming", emoji="📌",
                description="See all scheduled events with RSVP counts",
            ),
            discord.SelectOption(
                label="Request Collab", value="request_collab", emoji="🤝",
                description="Submit a private crew collab request",
            ),
            discord.SelectOption(
                label="Start Attendance Session", value="attendance_create", emoji="🧠",
                description="Open a live check-in for an active meet (staff only)",
            ),
            discord.SelectOption(
                label="View Open Check-ins", value="attendance_view", emoji="📋",
                description="See any currently active attendance sessions",
            ),
            discord.SelectOption(
                label="Refresh Panel", value="refresh_panel", emoji="♻️",
                description="Re-post this panel (staff only)",
            ),
        ],
    )
    async def combined_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        val = select.values[0]
        member = interaction.user if isinstance(interaction.user, discord.Member) else None

        if val == "create_event":
            if member is None or not _is_staff(member):
                return await interaction.response.send_message(
                    "Only staff can create official crew events.", ephemeral=True
                )
            await interaction.response.send_modal(CreateEventModal(self.cog))

        elif val == "view_upcoming":
            events  = _load_events().get("events", {})
            current = _now_ts()
            upcoming = sorted(
                [(int(e.get("timestamp", 0)), eid, e)
                 for eid, e in events.items() if int(e.get("timestamp", 0)) >= current],
                key=lambda x: x[0],
            )
            if not upcoming:
                return await interaction.response.send_message(
                    "There are no upcoming crew events right now.", ephemeral=True
                )
            embed = discord.Embed(title="📌 Upcoming Crew Events", color=EMBED_COLOR,
                                  description="Here are the next scheduled crew events.")
            for ts, eid, e in upcoming[:10]:
                c = e.get("counts", {})
                embed.add_field(
                    name=f"{e.get('title', 'Untitled')} • `{eid}`",
                    value=(
                        f"Date: <t:{ts}:F>\n"
                        f"Host: {e.get('host', 'Not set')}\n"
                        f"Theme: {e.get('theme', 'Not set')}\n"
                        f"RSVPs: ✅ {c.get('attending', 0)} | ❓ {c.get('maybe', 0)} | ❌ {c.get('not_attending', 0)}"
                    ),
                    inline=False,
                )
            embed.set_thumbnail(url=DIFF_LOGO_URL)
            await interaction.response.send_message(embed=embed, ephemeral=True)

        elif val == "request_collab":
            await interaction.response.send_modal(CollabRequestModal(self.cog))

        elif val == "attendance_create":
            if member is None or not _is_staff(member):
                return await interaction.response.send_message(
                    "Only staff can start attendance sessions.", ephemeral=True
                )
            att_cog = interaction.client.cogs.get("AttendanceCog")
            if att_cog is None:
                return await interaction.response.send_message(
                    "Attendance system not loaded.", ephemeral=True
                )
            from cogs.diff_attendance import CreateAttendanceModal as AttModal
            await interaction.response.send_modal(AttModal(att_cog))

        elif val == "attendance_view":
            from cogs.diff_attendance import _load_sessions
            sessions = _load_sessions().get("sessions", {})
            open_list = sorted(
                [(s.get("created_at", 0), sid, s)
                 for sid, s in sessions.items() if s.get("status") == "open"],
                key=lambda x: x[0], reverse=True,
            )
            if not open_list:
                return await interaction.response.send_message(
                    "There are no open check-in sessions right now.", ephemeral=True
                )
            embed = discord.Embed(title="📋 Open Check-in Sessions", color=EMBED_COLOR,
                                  description="Currently active attendance sessions:")
            for _, sid, s in open_list[:10]:
                checkins = s.get("checkins", {})
                embed.add_field(
                    name=f"{s.get('title', 'Untitled Meet')} • `{sid}`",
                    value=f"Host: {s.get('host', 'N/A')}\nChecked in: **{len(checkins)}**",
                    inline=False,
                )
            embed.set_thumbnail(url=DIFF_LOGO_URL)
            await interaction.response.send_message(embed=embed, ephemeral=True)

        elif val == "refresh_panel":
            if member is None or not _is_staff(member):
                return await interaction.response.send_message(
                    "Only staff can refresh the panel.", ephemeral=True
                )
            await interaction.response.defer(ephemeral=True)
            await self.cog.ensure_panel()
            await interaction.followup.send("✅ Panel refreshed.", ephemeral=True)


class CollabTicketView(discord.ui.View):
    def __init__(self, cog: "CrewEventsCog"):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Approve Collab", emoji="✅", style=discord.ButtonStyle.success,
                       custom_id="crew_events_collab_approve_v1")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user if isinstance(interaction.user, discord.Member) else None
        if member is None or not _is_staff(member):
            return await interaction.response.send_message("Only staff can approve collab requests.", ephemeral=True)
        embed = discord.Embed(title="✅ Collab Approved",
                              description="This collab request has been approved by staff.",
                              color=SUCCESS_COLOR)
        embed.set_footer(text=f"Approved by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)
        await self.cog.log_action(
            interaction.guild,
            f"✅ Approved collab in {interaction.channel.mention} by {interaction.user.mention}"
        )

    @discord.ui.button(label="Deny Collab", emoji="❌", style=discord.ButtonStyle.danger,
                       custom_id="crew_events_collab_deny_v1")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user if isinstance(interaction.user, discord.Member) else None
        if member is None or not _is_staff(member):
            return await interaction.response.send_message("Only staff can deny collab requests.", ephemeral=True)
        embed = discord.Embed(title="❌ Collab Denied",
                              description="This collab request has been denied by staff.",
                              color=ERROR_COLOR)
        embed.set_footer(text=f"Denied by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)
        await self.cog.log_action(
            interaction.guild,
            f"❌ Denied collab in {interaction.channel.mention} by {interaction.user.mention}"
        )

    @discord.ui.button(label="Close Ticket", emoji="🔒", style=discord.ButtonStyle.secondary,
                       custom_id="crew_events_collab_close_v1")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user if isinstance(interaction.user, discord.Member) else None
        if member is None or not _is_staff(member):
            return await interaction.response.send_message("Only staff can close collab tickets.", ephemeral=True)

        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message(
                "This button only works in a collab ticket channel.", ephemeral=True
            )

        collabs = _load(COLLAB_FILE)
        if channel.topic and "crew_collab_request_user_id:" in channel.topic:
            try:
                uid = channel.topic.split("crew_collab_request_user_id:")[1].split("|")[0].strip()
                if collabs.get(str(uid)) == channel.id:
                    collabs.pop(str(uid), None)
                    _save(COLLAB_FILE, collabs)
            except Exception:
                pass

        await interaction.response.send_message("Closing collab ticket in 5 seconds…")
        await self.cog.log_action(
            interaction.guild,
            f"🔒 Closed collab ticket `#{channel.name}` by {interaction.user.mention}"
        )
        await asyncio.sleep(5)
        await channel.delete(reason=f"Closed by {interaction.user}")


# =========================================================
# COG
# =========================================================
class CrewEventsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        _ensure_dirs()
        self.bot         = bot
        self._panel_view  = CrewEventsPanelView(self)
        self._collab_view = CollabTicketView(self)
        bot.add_view(self._panel_view)
        bot.add_view(self._collab_view)

    # ------------------------------------------------------------------
    async def _rebuild_event_views(self) -> None:
        """Re-register each event's RSVP view bound to its specific message."""
        events = _load_events().get("events", {})
        for event_id, event in events.items():
            msg_id = event.get("message_id")
            if msg_id:
                self.bot.add_view(EventRSVPView(self, event_id), message_id=int(msg_id))

    # ------------------------------------------------------------------
    async def log_action(self, guild: Optional[discord.Guild], message: str) -> None:
        if guild is None:
            return
        ch = guild.get_channel(LOG_CHANNEL_ID)
        if isinstance(ch, discord.TextChannel):
            try:
                await ch.send(message)
            except Exception:
                pass

    # ------------------------------------------------------------------
    def _build_panel_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🎮 DIFF Crew Events & Attendance",
            description=(
                "Your hub for crew events, collabs, and meet attendance tracking.\n"
                "Select an action from the dropdown — responses are **only visible to you**."
            ),
            color=EMBED_COLOR,
        )
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.add_field(
            name="📅 Crew Events",
            value=(
                "› **Create Event** — post a new scheduled crew event *(staff only)*\n"
                "› **View Upcoming Events** — see all events with RSVP counts\n"
                "› **Request Collab** — submit a private crew collab request\n"
                "› Events are posted here with RSVP buttons for members"
            ),
            inline=False,
        )
        embed.add_field(
            name="🧠 Meet Attendance",
            value=(
                "› **Start Attendance Session** — open a live check-in when a meet begins *(staff only)*\n"
                "› **View Open Check-ins** — see any currently active sessions\n"
                "› Tracks who actually showed up vs. who RSVPed"
            ),
            inline=False,
        )
        embed.set_footer(text="Different Meets • Crew Events & Attendance  |  Responses are private")
        return embed

    # ------------------------------------------------------------------
    async def _get_channel(self) -> Optional[discord.TextChannel]:
        ch = self.bot.get_channel(TARGET_CHANNEL_ID)
        if ch is None:
            try:
                ch = await self.bot.fetch_channel(TARGET_CHANNEL_ID)
            except Exception:
                return None
        return ch if isinstance(ch, discord.TextChannel) else None

    # ------------------------------------------------------------------
    async def ensure_panel(self) -> None:
        channel = await self._get_channel()
        if channel is None:
            print(f"[CrewEvents] Channel not found: {TARGET_CHANNEL_ID}")
            return

        embed    = self._build_panel_embed()
        saved_id = _get_panel_msg_id()

        if saved_id:
            try:
                msg = await channel.fetch_message(saved_id)
                await msg.edit(embed=embed, view=self._panel_view)
                print("[CrewEvents] Panel refreshed.")
                return
            except discord.NotFound:
                pass
            except Exception as e:
                print(f"[CrewEvents] Edit failed: {e}")

        # Remove stale duplicates — match by tag OR known old titles
        _stale_titles = {
            "🚨 DIFF Crew Events Command Center",
            "🎮 DIFF Crew Events & Attendance",
            "📋 DIFF Meet Attendance",
            "🧠 DIFF Real Attendance System",
            "DIFF Meet Attendance System",
        }
        try:
            async for msg in channel.history(limit=50):
                if msg.author == self.bot.user and msg.embeds:
                    e0 = msg.embeds[0]
                    if PANEL_TAG in (e0.footer.text or "") or e0.title in _stale_titles:
                        try:
                            await msg.delete()
                        except Exception:
                            pass
        except Exception:
            pass

        try:
            new_msg = await channel.send(embed=embed, view=self._panel_view)
            _set_panel_msg_id(new_msg.id)
            print(f"[CrewEvents] Panel posted: {new_msg.id}")
        except Exception as e:
            print(f"[CrewEvents] Failed to post panel: {e}")

    # ------------------------------------------------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        await self.ensure_panel()
        await self._rebuild_event_views()
        print("[CrewEvents] Cog ready.")

    @commands.command(name="refresh_crew_events_panel")
    @commands.has_permissions(manage_guild=True)
    async def refresh_cmd(self, ctx: commands.Context):
        """Force-refresh the Crew Events panel."""
        await self.ensure_panel()
        await ctx.send("Crew Events panel refreshed.", delete_after=10)


# =========================================================
# SETUP
# =========================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(CrewEventsCog(bot))
