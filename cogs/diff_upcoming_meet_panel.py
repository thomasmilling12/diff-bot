from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone, timedelta
from typing import Optional

import discord
from discord.ext import commands

# =========================================================
# CONFIG
# =========================================================
UPCOMING_HUB_CHANNEL_ID  = 1485861257708834836
OFFICIAL_MEET_CHANNEL_ID = 1485870611069796374
POPUP_MEET_CHANNEL_ID    = 1484768466023223418
MEET_CHAT_CHANNEL_ID     = 1195953265377021952
MEET_MEDIA_CHANNEL_ID    = 1266933655486332999
LOG_CHANNEL_ID           = 1485265848099799163
GUILD_ID                 = 850386896509337710

CARMEET_ROLE_ID = 1138691141009674260

STAFF_ROLE_IDS: set[int] = {
    850391095845584937,   # Leader
    850391378559238235,   # Co-Leader
    990011447193006101,   # Manager
}

PANEL_TAG  = "DIFF_UPCOMING_MEET_PANEL_V1"
DATA_DIR   = "diff_data"
PANEL_FILE = os.path.join(DATA_DIR, "upcoming_meet_panel.json")
STATE_FILE = os.path.join(DATA_DIR, "upcoming_meet_state.json")

DIFF_LOGO_URL = (
    "https://media.discordapp.net/attachments/1107375326625005719/"
    "1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm="
    "2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
    "&=&format=webp&quality=lossless&width=1376&height=917"
)

# =========================================================
# DATE / TIME PARSER
# =========================================================
_TZ_OFFSETS: dict[str, int] = {
    "UTC": 0,   "GMT": 0,
    "EST": -300,"EDT": -240,
    "CST": -360,"CDT": -300,
    "MST": -420,"MDT": -360,
    "PST": -480,"PDT": -420,
    "AST": -240,"ADT": -180,
    "HST": -600,"AKST": -540,"AKDT": -480,
    "BST": 60,  "CET": 60,  "CEST": 120,
    "EET": 120, "EEST": 180,
    "IST": 330, "JST": 540, "AEST": 600,"AEDT": 660,
}
_DATE_FORMATS = [
    "%B %d %Y %I:%M %p","%B %d %Y %I%p",
    "%B %d, %Y %I:%M %p","%B %d, %Y %I%p",
    "%m/%d/%Y %I:%M %p", "%m/%d/%Y %I%p",
    "%m/%d/%Y %H:%M",    "%Y-%m-%d %H:%M",
    "%Y-%m-%d %I:%M %p", "%B %d %I:%M %p",
    "%B %d %I%p",
]

def _parse_datetime(text: str) -> Optional[int]:
    text = text.strip()
    tz_offset = 0
    parts = text.rsplit(None, 1)
    if len(parts) == 2 and parts[-1].upper() in _TZ_OFFSETS:
        tz_offset = _TZ_OFFSETS[parts[-1].upper()]
        text = parts[0].strip()
    text = re.sub(r"(\d)(AM|PM|am|pm)", r"\1 \2", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    if not re.search(r"\b(202\d|203\d)\b", text):
        text = text + f" {datetime.now(timezone.utc).year}"
    for fmt in _DATE_FORMATS:
        try:
            naive = datetime.strptime(text, fmt)
            tz    = timezone(timedelta(minutes=tz_offset))
            return int(naive.replace(tzinfo=tz).timestamp())
        except ValueError:
            continue
    return None


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


def _get_panel_msg_id() -> Optional[int]:
    v = _load_json(PANEL_FILE).get("panel_message_id")
    return int(v) if v else None


def _save_panel_msg_id(msg_id: int) -> None:
    data = _load_json(PANEL_FILE)
    data["panel_message_id"] = msg_id
    _save_json(PANEL_FILE, data)


def _load_state() -> dict:
    return _load_json(STATE_FILE)


def _save_state(data: dict) -> None:
    _save_json(STATE_FILE, data)


# =========================================================
# PERMISSIONS + PING HELPERS
# =========================================================
def _is_staff(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    return any(r.id in STAFF_ROLE_IDS for r in member.roles)


def _ping_content(mode: str, guild: Optional[discord.Guild]) -> Optional[str]:
    if mode == "everyone":
        return "@everyone"
    if mode == "here":
        return "@here"
    if mode == "carmeet" and guild:
        role = guild.get_role(CARMEET_ROLE_ID)
        return role.mention if role else None
    return None


def _ping_mentions(mode: str) -> discord.AllowedMentions:
    if mode in ("everyone", "here"):
        return discord.AllowedMentions(everyone=True)
    if mode == "carmeet":
        return discord.AllowedMentions(roles=True)
    return discord.AllowedMentions.none()


# =========================================================
# EMBEDS
# =========================================================
def _hub_embed() -> discord.Embed:
    state   = _load_state()
    current = state.get("current_meet")

    if current:
        is_live    = current.get("live", False)
        is_official = current["meet_type"] == "official"
        ch_id  = OFFICIAL_MEET_CHANNEL_ID if is_official else POPUP_MEET_CHANNEL_ID
        mtype  = "🏁 Official Meet" if is_official else "⚡ Pop-Up Meet"

        if is_live:
            embed = discord.Embed(
                title="🔴 DIFF Meet — LIVE NOW",
                description=(
                    "**A DIFF meet is happening right now!**\n"
                    f"Head over to <#{ch_id}> for the official post and all live details.\n\n"
                    f"🎙️ Active hosts → <#{MEET_CHAT_CHANNEL_ID}>\n"
                    f"📋 Meet info → <#{MEET_MEDIA_CHANNEL_ID}>"
                ),
                color=discord.Color.red(),
            )
            embed.add_field(name="🎭 Theme",     value=current["theme"], inline=True)
            embed.add_field(name="👤 Host",      value=current["host"],  inline=True)
            embed.add_field(name="🏷️ Type",      value=mtype,            inline=True)
            embed.add_field(
                name="🔗 Meet Status",
                value=f"🟢 **Live** — <#{ch_id}>",
                inline=False,
            )
        else:
            embed = discord.Embed(
                title="📅 DIFF Upcoming Meet Hub",
                description=(
                    "A meet has been scheduled — details are locked in below.\n"
                    "Stay ready and check back for any updates."
                ),
                color=discord.Color.gold(),
            )
            embed.add_field(name="🎭 Theme",       value=current["theme"],              inline=True)
            embed.add_field(name="👤 Host",        value=current["host"],               inline=True)
            embed.add_field(name="🏷️ Type",        value=mtype,                         inline=True)
            embed.add_field(name="📅 Date & Time", value=f"<t:{current['timestamp']}:F>", inline=True)
            embed.add_field(name="⏱️ Countdown",   value=f"<t:{current['timestamp']}:R>", inline=True)
            embed.add_field(name="📢 Full Post",   value=f"<#{ch_id}>",                inline=True)

            notes = current.get("notes", "").strip()
            if notes:
                embed.add_field(name="📝 Notes", value=notes, inline=False)

            embed.add_field(
                name="🔗 Meet Status",
                value="🟡 **Scheduled** — not yet live",
                inline=False,
            )

        embed.set_thumbnail(url=DIFF_LOGO_URL)

    else:
        embed = discord.Embed(
            title="📅 DIFF Upcoming Meet Hub",
            description=(
                "No upcoming meet is scheduled right now.\n"
                "Stay tuned — when the next meet drops, all the details will appear here."
            ),
            color=0x2C2F33,
        )
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.add_field(
            name="📢 What This Channel Is For",
            value=(
                "• Check what meet is coming up next\n"
                "• See official meet posts and timing\n"
                "• Stay ready for public or pop-up meet drops\n"
                "• Know where to go once a meet goes live"
            ),
            inline=False,
        )
        embed.add_field(
            name="🔗 Quick Access",
            value=(
                f"🏁 Official posts → <#{OFFICIAL_MEET_CHANNEL_ID}>\n"
                f"⚡ Pop-up posts → <#{POPUP_MEET_CHANNEL_ID}>\n"
                f"🎙️ Active hosts → <#{MEET_CHAT_CHANNEL_ID}>\n"
                f"📋 Meet info → <#{MEET_MEDIA_CHANNEL_ID}>"
            ),
            inline=False,
        )
        embed.add_field(
            name="🔗 Meet Status",
            value="⚫ **No active meet**",
            inline=False,
        )

    embed.set_footer(text=f"Different Meets • Upcoming Meet Hub  |  {PANEL_TAG}")
    embed.timestamp = datetime.now(timezone.utc)
    return embed


# =========================================================
# MODALS
# =========================================================
class CreateMeetModal(discord.ui.Modal, title="Create Upcoming Meet"):
    theme_input = discord.ui.TextInput(
        label="Meet Theme / Title",
        placeholder="Example: DIFF Official Meet – JDM Night",
        max_length=120, required=True,
    )
    host_input = discord.ui.TextInput(
        label="Host",
        placeholder="@Host or Host Name",
        max_length=120, required=True,
    )
    time_input = discord.ui.TextInput(
        label="Date & Time",
        placeholder="Example: April 5 9:00 PM EST  or  04/05 9PM PST",
        max_length=50, required=True,
    )
    notes_input = discord.ui.TextInput(
        label="Extra Notes (optional)",
        placeholder="Rules, entry info, style direction…",
        style=discord.TextStyle.paragraph, max_length=1200, required=False,
    )

    def __init__(self, cog: "UpcomingMeetCog", meet_type: str, ping_mode: str):
        super().__init__()
        self.cog       = cog
        self.meet_type = meet_type
        self.ping_mode = ping_mode

    async def on_submit(self, interaction: discord.Interaction) -> None:
        member = interaction.user
        if not isinstance(member, discord.Member) or not _is_staff(member):
            return await interaction.response.send_message(
                "Only staff can use this system.", ephemeral=True
            )

        ts = _parse_datetime(str(self.time_input))
        if ts is None:
            return await interaction.response.send_message(
                "❌ Couldn't read that date/time. Try:\n"
                "• `April 5 9:00 PM EST`\n"
                "• `04/05/2026 9PM PST`\n"
                "• `2026-04-05 21:00 UTC`",
                ephemeral=True,
            )

        await self.cog.create_meet_post(
            interaction=interaction,
            meet_type=self.meet_type,
            ping_mode=self.ping_mode,
            theme=str(self.theme_input).strip(),
            host=str(self.host_input).strip(),
            ts=ts,
            notes=str(self.notes_input).strip(),
        )


# =========================================================
# INTERMEDIATE VIEWS  (ephemeral, not persistent)
# =========================================================
class PingModeView(discord.ui.View):
    def __init__(self, cog: "UpcomingMeetCog", meet_type: str):
        super().__init__(timeout=120)
        self.cog       = cog
        self.meet_type = meet_type

    async def _open_modal(self, interaction: discord.Interaction, mode: str) -> None:
        await interaction.response.send_modal(
            CreateMeetModal(self.cog, self.meet_type, mode)
        )

    @discord.ui.button(label="Ping @everyone",     style=discord.ButtonStyle.danger,    emoji="📣")
    async def ping_everyone(self, i: discord.Interaction, b: discord.ui.Button):
        await self._open_modal(i, "everyone")

    @discord.ui.button(label="Ping @here",         style=discord.ButtonStyle.primary,   emoji="📍")
    async def ping_here(self, i: discord.Interaction, b: discord.ui.Button):
        await self._open_modal(i, "here")

    @discord.ui.button(label="Ping Car Meet Role", style=discord.ButtonStyle.success,   emoji="🚗")
    async def ping_carmeet(self, i: discord.Interaction, b: discord.ui.Button):
        await self._open_modal(i, "carmeet")

    @discord.ui.button(label="No Ping",            style=discord.ButtonStyle.secondary, emoji="🔕")
    async def ping_none(self, i: discord.Interaction, b: discord.ui.Button):
        await self._open_modal(i, "none")


class MeetTypeView(discord.ui.View):
    def __init__(self, cog: "UpcomingMeetCog"):
        super().__init__(timeout=120)
        self.cog = cog

    @discord.ui.button(label="Official Meet", style=discord.ButtonStyle.primary,   emoji="🏁")
    async def official(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="**Step 2 — Choose ping type:**",
            view=PingModeView(self.cog, "official"),
        )

    @discord.ui.button(label="Pop-Up Meet", style=discord.ButtonStyle.secondary, emoji="⚡")
    async def popup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="**Step 2 — Choose ping type:**",
            view=PingModeView(self.cog, "popup"),
        )


# =========================================================
# STAFF ACTION SELECT  (dropdown)
# =========================================================
class StaffActionsSelect(discord.ui.Select):
    def __init__(self, cog: "UpcomingMeetCog"):
        self.cog = cog
        super().__init__(
            custom_id="diff_upcoming_staff_actions_v2",
            placeholder="🛠️ Staff Actions — choose an action...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Create Meet Post",
                    value="create",
                    emoji="📝",
                    description="Schedule an upcoming official or pop-up meet.",
                ),
                discord.SelectOption(
                    label="Mark Meet Live",
                    value="live",
                    emoji="🚨",
                    description="Mark the current scheduled meet as live now.",
                ),
                discord.SelectOption(
                    label="Clear Current Meet",
                    value="clear",
                    emoji="🗑️",
                    description="Remove the active meet and reset the hub panel.",
                ),
                discord.SelectOption(
                    label="Refresh Panel",
                    value="refresh",
                    emoji="♻️",
                    description="Force-refresh the hub embed with latest data.",
                ),
            ],
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        member = interaction.user
        if not isinstance(member, discord.Member) or not _is_staff(member):
            return await interaction.response.send_message(
                "Only staff can use these actions.", ephemeral=True
            )

        selected = self.values[0]

        if selected == "create":
            await interaction.response.send_message(
                "**Step 1 — Choose meet type:**",
                view=MeetTypeView(self.cog),
                ephemeral=True,
            )

        elif selected == "live":
            await self.cog.mark_meet_live(interaction)

        elif selected == "clear":
            await self.cog.clear_meet(interaction)

        elif selected == "refresh":
            await self.cog.ensure_panel()
            await interaction.response.send_message(
                "♻️ Hub panel refreshed.", ephemeral=True
            )


# =========================================================
# MAIN PANEL VIEW  (persistent)
# =========================================================
class UpcomingMeetHubView(discord.ui.View):
    def __init__(self, cog: "UpcomingMeetCog"):
        super().__init__(timeout=None)
        self.cog = cog

        # Row 0 — quick-link buttons
        for label, ch_id in [
            ("🏁 Official Meet Posts", OFFICIAL_MEET_CHANNEL_ID),
            ("⚡ Pop-Up Meets",        POPUP_MEET_CHANNEL_ID),
            ("🎙️ Active Hosts",        MEET_CHAT_CHANNEL_ID),
            ("📋 Meet Info",           MEET_MEDIA_CHANNEL_ID),
        ]:
            self.add_item(discord.ui.Button(
                label=label,
                url=f"https://discord.com/channels/{GUILD_ID}/{ch_id}",
                style=discord.ButtonStyle.link,
                row=0,
            ))

        # Row 1 — staff dropdown
        self.add_item(StaffActionsSelect(cog))


# =========================================================
# COG
# =========================================================
class UpcomingMeetCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot  = bot
        self.view = UpcomingMeetHubView(self)
        self.bot.add_view(self.view)

    # --------------------------------------------------
    async def log_action(self, guild: Optional[discord.Guild], message: str) -> None:
        if not guild or not LOG_CHANNEL_ID:
            return
        ch = guild.get_channel(LOG_CHANNEL_ID)
        if isinstance(ch, discord.TextChannel):
            try:
                await ch.send(message)
            except Exception:
                pass

    # --------------------------------------------------
    async def _get_hub_channel(self) -> Optional[discord.TextChannel]:
        ch = self.bot.get_channel(UPCOMING_HUB_CHANNEL_ID)
        if not isinstance(ch, discord.TextChannel):
            try:
                ch = await self.bot.fetch_channel(UPCOMING_HUB_CHANNEL_ID)
            except Exception:
                ch = None
        return ch if isinstance(ch, discord.TextChannel) else None

    # --------------------------------------------------
    async def ensure_panel(self) -> None:
        channel = await self._get_hub_channel()
        if not channel:
            print(f"[UpcomingMeetPanel] Channel {UPCOMING_HUB_CHANNEL_ID} not found.")
            return

        embed    = _hub_embed()
        saved_id = _get_panel_msg_id()

        if saved_id:
            try:
                msg = await channel.fetch_message(saved_id)
                await msg.edit(embed=embed, view=self.view)
                print("[UpcomingMeetPanel] Panel refreshed.")
                return
            except discord.NotFound:
                pass
            except Exception as e:
                print(f"[UpcomingMeetPanel] Edit failed: {e}")

        # Fallback: scan by tag and remove stale panels
        try:
            async for msg in channel.history(limit=50):
                if (
                    msg.author == self.bot.user
                    and msg.embeds
                    and PANEL_TAG in (msg.embeds[0].footer.text or "")
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
            print(f"[UpcomingMeetPanel] Panel posted: {new_msg.id}")
        except Exception as e:
            print(f"[UpcomingMeetPanel] Post failed: {e}")

    # --------------------------------------------------
    async def create_meet_post(
        self,
        interaction: discord.Interaction,
        meet_type: str,
        ping_mode: str,
        theme: str,
        host: str,
        ts: int,
        notes: str,
    ) -> None:
        ch_id   = OFFICIAL_MEET_CHANNEL_ID if meet_type == "official" else POPUP_MEET_CHANNEL_ID
        channel = self.bot.get_channel(ch_id)
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message(
                "Target meet channel not found.", ephemeral=True
            )

        title = "🏁 DIFF Official Meet" if meet_type == "official" else "⚡ DIFF Pop-Up Meet"
        color = discord.Color.blue() if meet_type == "official" else discord.Color.orange()

        desc = (
            f"**Theme:** {theme}\n"
            f"**Host:** {host}\n"
            f"**Date:** <t:{ts}:F>\n"
            f"**Begins:** <t:{ts}:R>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "**Meet Notes**\n"
        )
        desc += (
            f"{notes}\n\n"
            if notes
            else (
                "• Follow all host instructions\n"
                "• Bring clean, realistic, theme-fitting vehicles\n"
                "• Use meet chat for updates\n\n"
            )
        )
        desc += f"━━━━━━━━━━━━━━━━━━━━━━\n**Quick Links:** 🎙️ <#{MEET_CHAT_CHANNEL_ID}> (Active Hosts) • 📋 <#{MEET_MEDIA_CHANNEL_ID}> (Meet Info)"

        embed = discord.Embed(title=title, description=desc, color=color)
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.set_footer(text="DIFF Meets • Upcoming Meet Automation")

        await channel.send(
            content=_ping_content(ping_mode, interaction.guild),
            embed=embed,
            allowed_mentions=_ping_mentions(ping_mode),
        )

        _save_state({
            "current_meet": {
                "meet_type": meet_type,
                "ping_mode": ping_mode,
                "theme":     theme,
                "host":      host,
                "timestamp": ts,
                "notes":     notes,
                "live":      False,
            }
        })

        await self.ensure_panel()
        await interaction.response.send_message(
            f"✅ {'Official' if meet_type == 'official' else 'Pop-up'} meet posted and hub updated.",
            ephemeral=True,
        )
        await self.log_action(
            interaction.guild,
            f"📅 Upcoming meet posted: **{theme}** by {interaction.user.mention}"
        )

    # --------------------------------------------------
    async def mark_meet_live(self, interaction: discord.Interaction) -> None:
        state   = _load_state()
        current = state.get("current_meet")
        if not current:
            return await interaction.response.send_message(
                "There is no current upcoming meet saved.", ephemeral=True
            )

        ch_id   = OFFICIAL_MEET_CHANNEL_ID if current["meet_type"] == "official" else POPUP_MEET_CHANNEL_ID
        channel = self.bot.get_channel(ch_id)
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message(
                "Meet channel not found.", ephemeral=True
            )

        live_embed = discord.Embed(
            title="🚨 Meet Is Now Live",
            description=(
                f"**Theme:** {current['theme']}\n"
                f"**Host:** {current['host']}\n\n"
                f"🎙️ Active hosts → <#{MEET_CHAT_CHANNEL_ID}>\n"
                f"📋 Meet info → <#{MEET_MEDIA_CHANNEL_ID}>"
            ),
            color=discord.Color.red(),
        )
        live_embed.set_thumbnail(url=DIFF_LOGO_URL)
        live_embed.set_footer(text="DIFF Meets • Live Meet Update")
        await channel.send(embed=live_embed)

        current["live"] = True
        _save_state(state)
        await self.ensure_panel()
        await interaction.response.send_message("🚨 Meet marked as live.", ephemeral=True)
        await self.log_action(
            interaction.guild,
            f"🚨 Meet marked live: **{current['theme']}** by {interaction.user.mention}"
        )

    # --------------------------------------------------
    async def clear_meet(self, interaction: discord.Interaction) -> None:
        _save_state({})
        await self.ensure_panel()
        await interaction.response.send_message(
            "🗑️ Current meet cleared and hub reset.", ephemeral=True
        )
        await self.log_action(
            interaction.guild,
            f"🗑️ Upcoming meet cleared by {interaction.user.mention}"
        )

    # --------------------------------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        print("[UpcomingMeetPanel] Cog ready.")

    @commands.command(name="refresh_upcoming_meet_panel")
    @commands.has_permissions(manage_guild=True)
    async def cmd_refresh(self, ctx: commands.Context):
        await self.ensure_panel()
        await ctx.send("Upcoming meet hub refreshed.", delete_after=8)


# =========================================================
# SETUP
# =========================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(UpcomingMeetCog(bot))
