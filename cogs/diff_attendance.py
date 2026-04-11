from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Optional

import discord
from discord.ext import commands

# =========================================================
# CONFIG
# =========================================================
TARGET_CHANNEL_ID     = 1486589047232135309   # crew-events channel
LOG_CHANNEL_ID        = 1485265848099799163   # staff-logs
CREW_MEMBER_ROLE_ID   = 886702076552441927    # pinged when attendance opens

STAFF_ROLE_IDS: set[int] = {
    850391095845584937,   # Leader
    850391378559238235,   # Co-Leader
    990011447193006101,   # Manager
}

PANEL_TAG   = "DIFF_ATTENDANCE_PANEL_V1"
DATA_DIR    = "diff_data"
PANEL_FILE  = os.path.join(DATA_DIR, "attendance_panel.json")
SESSION_FILE = os.path.join(DATA_DIR, "attendance_sessions.json")

EMBED_COLOR   = 0x5865F2
WARNING_COLOR = 0xFEE75C
ERROR_COLOR   = 0xED4245

DIFF_LOGO_URL = (
    "https://media.discordapp.net/attachments/1107375326625005719/"
    "1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm="
    "2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
    "&=&format=webp&quality=lossless&width=1376&height=917"
)


# =========================================================
# FILE HELPERS
# =========================================================
def _load_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def _load_sessions() -> dict:
    data = _load_json(SESSION_FILE)
    data.setdefault("sessions", {})
    return data


def _save_sessions(data: dict) -> None:
    _save_json(SESSION_FILE, data)


def _get_panel_msg_id() -> Optional[int]:
    v = _load_json(PANEL_FILE).get("panel_message_id")
    return int(v) if v else None


def _save_panel_msg_id(msg_id: int) -> None:
    data = _load_json(PANEL_FILE)
    data["panel_message_id"] = msg_id
    _save_json(PANEL_FILE, data)


def _now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def _make_session_id() -> str:
    return str(int(datetime.now(timezone.utc).timestamp() * 1000))


# =========================================================
# PERMISSIONS
# =========================================================
def _is_staff(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    return any(r.id in STAFF_ROLE_IDS for r in member.roles)


# =========================================================
# EMBEDS
# =========================================================
def _session_embed(session_id: str, session: dict) -> discord.Embed:
    checked   = len(session.get("checked_in_users", {}))
    expected  = len(session.get("expected_users", {}))
    no_shows  = len(session.get("no_show_users", {}))
    is_open   = session.get("status", "open") == "open"

    embed = discord.Embed(
        title="✅ DIFF Real Attendance Session",
        color=EMBED_COLOR if is_open else WARNING_COLOR,
        description=(
            f"**Session ID:** `{session_id}`\n"
            f"**Event Title:** {session.get('title', 'Untitled Meet')}\n"
            f"**Host:** {session.get('host', 'Not set')}\n"
            f"**Theme:** {session.get('theme', 'Not set')}\n"
            f"**Status:** **{'OPEN' if is_open else 'CLOSED'}**\n"
            f"**Started:** <t:{session.get('created_at', _now_ts())}:F>"
        ),
    )

    embed.add_field(
        name="Live Tracking",
        value=(
            f"✅ Checked In: **{checked}**\n"
            f"📋 Expected (RSVP): **{expected}**\n"
            f"❌ No-Shows: **{no_shows}**"
        ),
        inline=False,
    )
    embed.add_field(
        name="How it Works",
        value=(
            "Members who actually show up should press **Check In**.\n"
            "When staff closes this session the system compares expected "
            "members vs real check-ins and flags no-shows automatically."
        ),
        inline=False,
    )
    if session.get("notes"):
        embed.add_field(name="Notes", value=session["notes"], inline=False)

    embed.set_thumbnail(url=DIFF_LOGO_URL)
    embed.set_footer(text="DIFF Real Attendance System")
    return embed


def _panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title="📋 DIFF Meet Attendance",
        description=(
            "Track who actually showed up at each DIFF meet — not just who RSVPed.\n"
            "Open a session when the meet starts, members check in, and staff reviews no-shows when it closes."
        ),
        color=EMBED_COLOR,
    )
    embed.set_thumbnail(url=DIFF_LOGO_URL)
    embed.add_field(
        name="📌 How It Works",
        value=(
            "› **1.** Press **Create Attendance Session** and fill in the meet details\n"
            "› **2.** The bot posts a live check-in message in this channel\n"
            "› **3.** Members press **Check In** when they join the meet\n"
            "› **4.** Staff closes the session — no-shows are flagged automatically"
        ),
        inline=False,
    )
    embed.add_field(
        name="📊 What Gets Recorded",
        value=(
            "› Host name & meet title\n"
            "› Theme / event type\n"
            "› Every member who checked in (with timestamp)\n"
            "› No-shows from the expected RSVP list"
        ),
        inline=False,
    )
    embed.add_field(
        name="💡 Tip",
        value="Use **View Open Sessions** to see any currently active check-ins.",
        inline=False,
    )
    embed.set_footer(text="Different Meets • Attendance System  |  Staff-only panel")
    return embed


# =========================================================
# MODAL
# =========================================================
class CreateAttendanceModal(discord.ui.Modal, title="Create Attendance Session"):
    title_input = discord.ui.TextInput(
        label="Event Title", placeholder="Example: Friday Night Meet",
        required=True, max_length=100,
    )
    host_input = discord.ui.TextInput(
        label="Host", placeholder="@Host or host name",
        required=True, max_length=100,
    )
    theme_input = discord.ui.TextInput(
        label="Theme", placeholder="Example: Clean JDM / Pop-Up / Crew Collab",
        required=True, max_length=100,
    )
    expected_input = discord.ui.TextInput(
        label="Expected User IDs (optional, comma separated)",
        placeholder="123456,789012  or leave blank if no RSVP list",
        required=False, style=discord.TextStyle.paragraph, max_length=500,
    )
    notes_input = discord.ui.TextInput(
        label="Notes (optional)",
        placeholder="Any extra notes for this session",
        required=False, style=discord.TextStyle.paragraph, max_length=400,
    )

    def __init__(self, cog: "AttendanceCog"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        member = interaction.user if isinstance(interaction.user, discord.Member) else None
        if member is None or not _is_staff(member):
            return await interaction.response.send_message(
                "Only staff can create attendance sessions.", ephemeral=True
            )

        expected_users: dict[str, bool] = {}
        raw = str(self.expected_input).strip()
        if raw:
            for chunk in raw.replace("\n", ",").split(","):
                uid = chunk.strip().lstrip("<@!").rstrip(">")
                if uid.isdigit():
                    expected_users[uid] = True

        session_id = _make_session_id()
        data = _load_sessions()
        data["sessions"][session_id] = {
            "title":            str(self.title_input),
            "host":             str(self.host_input),
            "theme":            str(self.theme_input),
            "notes":            str(self.notes_input).strip(),
            "status":           "open",
            "channel_id":       interaction.channel_id,
            "message_id":       None,
            "expected_users":   expected_users,
            "checked_in_users": {},
            "no_show_users":    {},
            "created_by":       interaction.user.id,
            "created_at":       _now_ts(),
            "closed_at":        None,
        }
        _save_sessions(data)

        view  = AttendanceSessionView(self.cog, session_id)
        embed = _session_embed(session_id, data["sessions"][session_id])

        crew_role = interaction.guild.get_role(CREW_MEMBER_ROLE_ID) if interaction.guild else None
        content   = crew_role.mention if crew_role else None

        await interaction.response.send_message(
            content=content,
            embed=embed,
            view=view,
            allowed_mentions=discord.AllowedMentions(roles=True),
        )

        sent = await interaction.original_response()
        data = _load_sessions()
        if session_id in data["sessions"]:
            data["sessions"][session_id]["message_id"] = sent.id
            _save_sessions(data)

        # Bind this session's view to its exact message so check-ins always
        # route to the right session even when multiple sessions are active.
        self.cog.bot.add_view(view, message_id=sent.id)

        await self.cog.log_action(
            interaction.guild,
            f"✅ Attendance session `{session_id}` created in "
            f"<#{interaction.channel_id}> by {interaction.user.mention}"
        )


# =========================================================
# VIEWS
# =========================================================
class AttendanceSessionView(discord.ui.View):
    def __init__(self, cog: "AttendanceCog", session_id: str):
        super().__init__(timeout=None)
        self.cog        = cog
        self.session_id = session_id

    async def _refresh(self, interaction: discord.Interaction, session: dict):
        try:
            await interaction.message.edit(
                embed=_session_embed(self.session_id, session), view=self
            )
        except Exception:
            pass

    @discord.ui.button(label="Check In", emoji="✅", style=discord.ButtonStyle.success,
                       custom_id="diff_attendance_check_in_v1")
    async def check_in(self, interaction: discord.Interaction, button: discord.ui.Button):
        data    = _load_sessions()
        session = data.get("sessions", {}).get(self.session_id)

        if not session:
            return await interaction.response.send_message(
                "This attendance session could not be found.", ephemeral=True
            )
        if session.get("status") != "open":
            return await interaction.response.send_message(
                "This attendance session is already closed.", ephemeral=True
            )

        uid = str(interaction.user.id)
        if uid in session["checked_in_users"]:
            return await interaction.response.send_message(
                "You are already checked in for this session. ✅", ephemeral=True
            )

        session["checked_in_users"][uid] = {
            "username":  str(interaction.user),
            "timestamp": _now_ts(),
        }
        session["no_show_users"].pop(uid, None)
        _save_sessions(data)

        await self._refresh(interaction, session)
        await interaction.response.send_message(
            "You have been checked in successfully. ✅", ephemeral=True
        )

    @discord.ui.button(label="Close Attendance", emoji="🔒", style=discord.ButtonStyle.danger,
                       custom_id="diff_attendance_close_v1")
    async def close_attendance(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user if isinstance(interaction.user, discord.Member) else None
        if member is None or not _is_staff(member):
            return await interaction.response.send_message(
                "Only staff can close attendance sessions.", ephemeral=True
            )

        data    = _load_sessions()
        session = data.get("sessions", {}).get(self.session_id)

        if not session:
            return await interaction.response.send_message(
                "This attendance session could not be found.", ephemeral=True
            )
        if session.get("status") == "closed":
            return await interaction.response.send_message(
                "This attendance session is already closed.", ephemeral=True
            )

        expected   = set(session.get("expected_users", {}).keys())
        checked_in = set(session.get("checked_in_users", {}).keys())
        no_shows   = {uid: True for uid in expected if uid not in checked_in}

        session["no_show_users"] = no_shows
        session["status"]        = "closed"
        session["closed_at"]     = _now_ts()
        session["closed_by"]     = interaction.user.id
        _save_sessions(data)

        try:
            await interaction.message.edit(
                embed=_session_embed(self.session_id, session), view=self
            )
        except Exception:
            pass

        checked_count  = len(session.get("checked_in_users", {}))
        expected_count = len(expected)
        no_show_count  = len(no_shows)

        summary = discord.Embed(
            title="📊 Attendance Session Closed",
            color=WARNING_COLOR,
            description=(
                f"**Event:** {session.get('title', 'Untitled Meet')}\n"
                f"**Checked In:** **{checked_count}**\n"
                f"**Expected:** **{expected_count}**\n"
                f"**No-Shows:** **{no_show_count}**"
            ),
        )

        if no_show_count:
            mentions = [f"<@{uid}>" for uid in list(no_shows.keys())[:15]]
            summary.add_field(
                name="No-Show Members",
                value="\n".join(mentions) or "No-show list saved.",
                inline=False,
            )
        else:
            summary.add_field(
                name="No-Show Members", value="No no-shows detected. ✅", inline=False
            )

        summary.set_thumbnail(url=DIFF_LOGO_URL)
        summary.set_footer(text=f"Closed by {interaction.user.display_name}")

        await interaction.response.send_message(embed=summary)

        await self.cog.log_action(
            interaction.guild,
            f"📊 Attendance session `{self.session_id}` closed by "
            f"{interaction.user.mention} | "
            f"Checked In: {checked_count} | Expected: {expected_count} | "
            f"No-Shows: {no_show_count}"
        )


class AttendancePanelView(discord.ui.View):
    def __init__(self, cog: "AttendanceCog"):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Create Attendance Session", emoji="🧠",
                       style=discord.ButtonStyle.primary,
                       custom_id="diff_attendance_create_session_v1")
    async def create_session(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user if isinstance(interaction.user, discord.Member) else None
        if member is None or not _is_staff(member):
            return await interaction.response.send_message(
                "Only staff can create attendance sessions.", ephemeral=True
            )
        await interaction.response.send_modal(CreateAttendanceModal(self.cog))

    @discord.ui.button(label="View Open Sessions", emoji="📌",
                       style=discord.ButtonStyle.secondary,
                       custom_id="diff_attendance_view_open_v1")
    async def view_open_sessions(self, interaction: discord.Interaction, button: discord.ui.Button):
        sessions = _load_sessions().get("sessions", {})
        open_list = sorted(
            [(s.get("created_at", 0), sid, s)
             for sid, s in sessions.items() if s.get("status") == "open"],
            key=lambda x: x[0], reverse=True,
        )

        if not open_list:
            return await interaction.response.send_message(
                "There are no open attendance sessions right now.", ephemeral=True
            )

        embed = discord.Embed(
            title="📌 Open Attendance Sessions",
            color=EMBED_COLOR,
            description="Currently open real attendance sessions:",
        )
        for _, sid, s in open_list[:10]:
            embed.add_field(
                name=f"{s.get('title', 'Untitled Meet')} • `{sid}`",
                value=(
                    f"Host: {s.get('host', 'Not set')}\n"
                    f"Theme: {s.get('theme', 'Not set')}\n"
                    f"Checked In: {len(s.get('checked_in_users', {}))}\n"
                    f"Expected: {len(s.get('expected_users', {}))}"
                ),
                inline=False,
            )
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Refresh Panel", emoji="♻️",
                       style=discord.ButtonStyle.secondary,
                       custom_id="diff_attendance_refresh_panel_v1")
    async def refresh_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user if isinstance(interaction.user, discord.Member) else None
        if member is None or not _is_staff(member):
            return await interaction.response.send_message(
                "Only staff can refresh this panel.", ephemeral=True
            )
        await interaction.response.defer(ephemeral=True)
        await self.cog.ensure_panel()
        await interaction.followup.send("Attendance panel refreshed.", ephemeral=True)


# =========================================================
# COG
# =========================================================
class AttendanceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot         = bot
        self.panel_view  = AttendancePanelView(self)
        self.bot.add_view(self.panel_view)

    async def cog_load(self):
        await self._rebuild_session_views()

    async def _rebuild_session_views(self):
        """Re-bind each open/closed session view to its saved message so
        check-in interactions always route to the correct session."""
        data = _load_sessions()
        for session_id, session in data.get("sessions", {}).items():
            msg_id = session.get("message_id")
            if msg_id:
                view = AttendanceSessionView(self, session_id)
                self.bot.add_view(view, message_id=int(msg_id))

    async def log_action(self, guild: Optional[discord.Guild], message: str):
        if guild is None or not LOG_CHANNEL_ID:
            return
        ch = guild.get_channel(LOG_CHANNEL_ID)
        if isinstance(ch, discord.TextChannel):
            try:
                await ch.send(message)
            except Exception:
                pass

    async def ensure_panel(self):
        channel = self.bot.get_channel(TARGET_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            try:
                channel = await self.bot.fetch_channel(TARGET_CHANNEL_ID)
            except Exception:
                channel = None
        if not isinstance(channel, discord.TextChannel):
            print(f"[Attendance] Channel {TARGET_CHANNEL_ID} not found.")
            return

        embed    = _panel_embed()
        saved_id = _get_panel_msg_id()

        if saved_id:
            try:
                msg = await channel.fetch_message(saved_id)
                await msg.edit(embed=embed, view=self.panel_view)
                print("[Attendance] Panel refreshed.")
                return
            except discord.NotFound:
                pass
            except Exception as e:
                print(f"[Attendance] Edit failed: {e}")

        # Fallback: scan and delete any stale panel by tag or known titles
        _old_titles = {
            "🧠 DIFF Real Attendance System",
            "📋 DIFF Meet Attendance",
            "DIFF Meet Attendance System",
        }
        try:
            async for msg in channel.history(limit=50):
                if (
                    msg.author == self.bot.user
                    and msg.embeds
                    and (
                        msg.embeds[0].footer.text == PANEL_TAG
                        or msg.embeds[0].title in _old_titles
                    )
                ):
                    try:
                        await msg.delete()
                    except Exception:
                        pass
        except Exception:
            pass

        try:
            new_msg = await channel.send(embed=embed, view=self.panel_view)
            _save_panel_msg_id(new_msg.id)
            print(f"[Attendance] Panel posted: {new_msg.id}")
        except Exception as e:
            print(f"[Attendance] Failed to post panel: {e}")

    @commands.command(name="refreshattendancepanel")
    async def refresh_panel_cmd(self, ctx: commands.Context):
        member = ctx.author if isinstance(ctx.author, discord.Member) else None
        if member is None or not _is_staff(member):
            return
        try:
            await ctx.message.delete()
        except Exception:
            pass
        _save_panel_msg_id(None)
        await self.ensure_panel()
        await ctx.send("✅ Attendance panel refreshed.", delete_after=6)

    @commands.Cog.listener()
    async def on_ready(self):
        await self._rebuild_session_views()
        print("[Attendance] Cog ready.")


# =========================================================
# SETUP
# =========================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(AttendanceCog(bot))
