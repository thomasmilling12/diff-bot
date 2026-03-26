import json
from pathlib import Path

import discord
from discord.ext import commands

# =========================================================
# CONFIG
# =========================================================

COLOR_TEAM_CHANNEL_ID = 1485453653916520549
COLOR_TEAM_ROLE_ID    = 0
URGENT_PING_ROLE_ID   = 0

MANAGER_ROLE_IDS: list[int] = []

PANEL_HEADER_URL        = ""
ANNOUNCEMENT_BANNER_URL = ""
DIFF_LOGO_URL           = ""

DATA_FILE = Path("diff_data/color_team_announcement_panel.json")

PANEL_TITLES = {
    "🎨 DIFF Color Team Announcement Center",
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


# =========================================================
# HELPERS
# =========================================================

def user_is_manager(member: discord.Member) -> bool:
    if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
        return True
    if MANAGER_ROLE_IDS:
        role_ids = {role.id for role in member.roles}
        return any(rid in role_ids for rid in MANAGER_ROLE_IDS)
    return False


def get_color_team_ping() -> str:
    return f"<@&{COLOR_TEAM_ROLE_ID}>" if COLOR_TEAM_ROLE_ID else "@Color Team"


def get_urgent_ping() -> str:
    return f"<@&{URGENT_PING_ROLE_ID}>" if URGENT_PING_ROLE_ID else ""


def maybe_set_image(embed: discord.Embed, url: str) -> None:
    if url and url.strip():
        embed.set_image(url=url.strip())


def maybe_set_thumbnail(embed: discord.Embed, url: str) -> None:
    if url and url.strip():
        embed.set_thumbnail(url=url.strip())


# =========================================================
# ANNOUNCEMENT TYPES
# =========================================================

ANNOUNCEMENT_TYPES: dict[str, dict] = {
    "general_update": {
        "label":        "General Update",
        "emoji":        "🎨",
        "title_prefix": "DIFF Color Team Update",
        "color":        0xF59E0B,
        "description":  "General Color Team notices and updates.",
    },
    "weekly_color": {
        "label":        "Weekly Color",
        "emoji":        "🌈",
        "title_prefix": "DIFF Weekly Color Notice",
        "color":        0xFBBF24,
        "description":  "Use for weekly crew color announcements.",
    },
    "submission_notice": {
        "label":        "Submission Notice",
        "emoji":        "📥",
        "title_prefix": "DIFF Color Submission Notice",
        "color":        0xFB923C,
        "description":  "Use for color requests, drops, and submissions.",
    },
    "reminder": {
        "label":        "Reminder",
        "emoji":        "⏰",
        "title_prefix": "DIFF Color Team Reminder",
        "color":        0xD97706,
        "description":  "Use for reminders and deadlines.",
    },
    "urgent_notice": {
        "label":        "Urgent Notice",
        "emoji":        "🚨",
        "title_prefix": "DIFF Urgent Color Notice",
        "color":        0xEF4444,
        "description":  "Use for urgent Color Team updates.",
    },
    "event_support": {
        "label":        "Event Support",
        "emoji":        "🏁",
        "title_prefix": "DIFF Event Color Support",
        "color":        0xF97316,
        "description":  "Use for meet/event-related Color Team coordination.",
    },
}

DEFAULT_TYPE = "general_update"


# =========================================================
# PER-USER STATE (in-memory)
# =========================================================

class ColorTeamState:
    def __init__(self):
        self._selection: dict[int, str]  = {}
        self._urgent:    dict[int, bool] = {}

    def set_selection(self, user_id: int, value: str) -> None:
        self._selection[user_id] = value

    def get_selection(self, user_id: int) -> str:
        return self._selection.get(user_id, DEFAULT_TYPE)

    def set_urgent(self, user_id: int, value: bool) -> None:
        self._urgent[user_id] = value

    def get_urgent(self, user_id: int) -> bool:
        return self._urgent.get(user_id, False)


STATE = ColorTeamState()


# =========================================================
# EMBEDS
# =========================================================

def build_panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🎨 DIFF Color Team Announcement Center",
        description=(
            "Managers can send branded Color Team announcements from one clean control panel.\n\n"
            "**Features**\n"
            "• Dropdown announcement types\n"
            "• Manager urgent ping mode\n"
            "• DIFF header image support\n"
            "• Auto Color Team ping\n"
            "• One no-dupe panel\n\n"
            "📋 **Commands**\n"
            "`!colorannouncepanel` — Refresh this panel\n"
            "`!setcolorteamrole @role` — Set Color Team role\n"
            "`!setcolorurgentrole @role` — Set urgent ping role"
        ),
        color=0xF59E0B,
    )
    embed.add_field(
        name="How To Use",
        value=(
            "1. Choose the announcement type from the dropdown\n"
            "2. Toggle urgent mode if needed\n"
            "3. Press **Open Announcement Form**\n"
            "4. Submit — the bot posts it automatically"
        ),
        inline=False,
    )
    embed.add_field(name="Access", value="Managers / authorized staff only.", inline=False)
    maybe_set_image(embed, PANEL_HEADER_URL)
    maybe_set_thumbnail(embed, DIFF_LOGO_URL)
    embed.set_footer(text="DIFF • Color Team System")
    return embed


def build_sent_embed(
    manager: discord.Member,
    announcement_type: str,
    custom_title: str,
    body: str,
    footer_text: str,
    urgent_mode: bool,
) -> discord.Embed:
    info        = ANNOUNCEMENT_TYPES[announcement_type]
    final_title = custom_title.strip() if custom_title.strip() else info["title_prefix"]
    if urgent_mode:
        final_title = f"URGENT • {final_title}"

    embed = discord.Embed(
        title=f"{info['emoji']} {final_title}",
        description=body,
        color=info["color"],
    )
    embed.set_author(
        name=f"DIFF Management • {manager.display_name}",
        icon_url=manager.display_avatar.url,
    )
    embed.add_field(name="Type",    value=info["label"],           inline=True)
    embed.add_field(name="Target",  value=get_color_team_ping(),   inline=True)
    embed.add_field(name="Sent By", value=manager.mention,         inline=True)
    if urgent_mode:
        embed.add_field(name="Priority", value="Urgent mode enabled", inline=False)
    maybe_set_image(embed, ANNOUNCEMENT_BANNER_URL)
    maybe_set_thumbnail(embed, DIFF_LOGO_URL)
    embed.set_footer(text=footer_text.strip() if footer_text.strip() else "DIFF Color Team")
    return embed


# =========================================================
# MODAL
# =========================================================

class ColorTeamAnnouncementModal(discord.ui.Modal):
    def __init__(self, announcement_type: str, urgent_mode: bool):
        info = ANNOUNCEMENT_TYPES[announcement_type]
        super().__init__(title=f"{info['label']} Announcement")
        self.announcement_type = announcement_type
        self.urgent_mode       = urgent_mode

        self.custom_title = discord.ui.TextInput(
            label="Custom title",
            placeholder=info["title_prefix"],
            required=False,
            max_length=100,
        )
        self.body_text = discord.ui.TextInput(
            label="Announcement message",
            placeholder="Write the full Color Team announcement here...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=2000,
        )
        self.footer_text = discord.ui.TextInput(
            label="Footer / sign-off",
            placeholder="DIFF Color Team",
            required=False,
            max_length=100,
        )
        self.add_item(self.custom_title)
        self.add_item(self.body_text)
        self.add_item(self.footer_text)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("This can only be used in a server.", ephemeral=True)
            return
        if not user_is_manager(interaction.user):
            await interaction.response.send_message("You do not have permission to use this panel.", ephemeral=True)
            return

        channel = interaction.guild.get_channel(COLOR_TEAM_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("Color Team channel not found.", ephemeral=True)
            return

        pings   = [get_color_team_ping()]
        if self.urgent_mode and get_urgent_ping():
            pings.append(get_urgent_ping())
        content = " ".join(p for p in pings if p).strip()

        embed = build_sent_embed(
            manager=interaction.user,
            announcement_type=self.announcement_type,
            custom_title=self.custom_title.value or "",
            body=self.body_text.value,
            footer_text=self.footer_text.value or "",
            urgent_mode=self.urgent_mode,
        )

        await channel.send(
            content=content,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True, users=True, everyone=False),
        )
        await interaction.response.send_message("✅ Color Team announcement sent.", ephemeral=True)


# =========================================================
# VIEW
# =========================================================

class ColorTeamTypeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=v["label"],
                value=k,
                emoji=v["emoji"],
                description=v["description"][:100],
            )
            for k, v in ANNOUNCEMENT_TYPES.items()
        ]
        super().__init__(
            placeholder="Choose announcement type...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="diff_color_team_type_select",
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("This can only be used in a server.", ephemeral=True)
            return
        if not user_is_manager(interaction.user):
            await interaction.response.send_message("You do not have permission to use this panel.", ephemeral=True)
            return
        selected = self.values[0]
        STATE.set_selection(interaction.user.id, selected)
        info = ANNOUNCEMENT_TYPES[selected]
        await interaction.response.send_message(
            f"Selected **{info['label']}** {info['emoji']}.",
            ephemeral=True,
        )


class ColorTeamAnnouncementPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ColorTeamTypeSelect())

    @discord.ui.button(
        label="Urgent Mode",
        emoji="🚨",
        style=discord.ButtonStyle.red,
        custom_id="diff_color_team_toggle_urgent",
        row=1,
    )
    async def toggle_urgent(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("This can only be used in a server.", ephemeral=True)
            return
        if not user_is_manager(interaction.user):
            await interaction.response.send_message("You do not have permission to use this panel.", ephemeral=True)
            return
        new_val = not STATE.get_urgent(interaction.user.id)
        STATE.set_urgent(interaction.user.id, new_val)
        await interaction.response.send_message(
            f"🚨 Urgent mode {'**enabled**' if new_val else '**disabled**'}.",
            ephemeral=True,
        )

    @discord.ui.button(
        label="Open Announcement Form",
        emoji="📢",
        style=discord.ButtonStyle.blurple,
        custom_id="diff_color_team_open_form",
        row=1,
    )
    async def open_form(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("This can only be used in a server.", ephemeral=True)
            return
        if not user_is_manager(interaction.user):
            await interaction.response.send_message("You do not have permission to use this panel.", ephemeral=True)
            return
        selected    = STATE.get_selection(interaction.user.id)
        urgent_mode = STATE.get_urgent(interaction.user.id)
        await interaction.response.send_modal(ColorTeamAnnouncementModal(selected, urgent_mode))

    @discord.ui.button(
        label="Refresh Panel",
        emoji="♻️",
        style=discord.ButtonStyle.gray,
        custom_id="diff_color_team_refresh_panel",
        row=1,
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
        await ensure_single_panel(interaction.client)
        await interaction.response.send_message("✅ Color Team panel refreshed.", ephemeral=True)


# =========================================================
# PANEL MANAGEMENT
# =========================================================

async def ensure_single_panel(bot: commands.Bot) -> None:
    data = load_data()
    channel = bot.get_channel(COLOR_TEAM_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        try:
            channel = await bot.fetch_channel(COLOR_TEAM_CHANNEL_ID)
        except Exception as e:
            print(f"[ColorTeamAnnouncementPanel] Channel not found: {e}")
            return

    embed            = build_panel_embed()
    view             = ColorTeamAnnouncementPanelView()
    panel_message_id = data.get("panel_message_id")

    if panel_message_id:
        try:
            msg = await channel.fetch_message(panel_message_id)
            await msg.edit(content=None, embed=embed, view=view)
            print("[ColorTeamAnnouncementPanel] Existing panel refreshed.")
            return
        except discord.NotFound:
            pass
        except Exception as e:
            print(f"[ColorTeamAnnouncementPanel] Could not edit saved panel: {e}")

    try:
        async for msg in channel.history(limit=50):
            if msg.author == bot.user and msg.embeds and msg.embeds[0].title in PANEL_TITLES:
                await msg.edit(content=None, embed=embed, view=view)
                data["panel_message_id"] = msg.id
                save_data(data)
                print("[ColorTeamAnnouncementPanel] Found old panel and refreshed it.")
                return
    except Exception as e:
        print(f"[ColorTeamAnnouncementPanel] History scan failed: {e}")

    new_msg = await channel.send(embed=embed, view=view)
    data["panel_message_id"] = new_msg.id
    save_data(data)
    print("[ColorTeamAnnouncementPanel] New panel posted.")


# =========================================================
# COG
# =========================================================

class ColorTeamAnnouncementPanel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(ColorTeamAnnouncementPanelView())

    @commands.Cog.listener()
    async def on_ready(self):
        if getattr(self.bot, "_diff_color_team_announcement_panel_ready", False):
            return
        self.bot._diff_color_team_announcement_panel_ready = True
        await ensure_single_panel(self.bot)
        print("[ColorTeamAnnouncementPanel] Cog ready.")

    @commands.command(name="colorannouncepanel")
    @commands.has_permissions(manage_guild=True)
    async def colorannouncepanel(self, ctx: commands.Context):
        await ensure_single_panel(self.bot)
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="setcolorteamrole")
    @commands.has_permissions(administrator=True)
    async def setcolorteamrole(self, ctx: commands.Context, role: discord.Role):
        global COLOR_TEAM_ROLE_ID
        COLOR_TEAM_ROLE_ID = role.id
        await ctx.send(f"✅ Color Team role set to {role.mention}", delete_after=10)

    @commands.command(name="setcolorurgentrole")
    @commands.has_permissions(administrator=True)
    async def setcolorurgentrole(self, ctx: commands.Context, role: discord.Role):
        global URGENT_PING_ROLE_ID
        URGENT_PING_ROLE_ID = role.id
        await ctx.send(f"✅ Color Team urgent role set to {role.mention}", delete_after=10)


async def setup(bot: commands.Bot):
    await bot.add_cog(ColorTeamAnnouncementPanel(bot))
