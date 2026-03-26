from __future__ import annotations

import json
import os
from typing import Optional

import discord
from discord.ext import commands

# =========================================================
# CONFIG — Crew Announcement
# =========================================================
CREW_ANNOUNCE_CHANNEL_ID = 990097152044855326
CREW_ROLE_ID             = 886702076552441927   # @Crew Members ping

# =========================================================
# CONFIG — General Announcement
# =========================================================
GENERAL_ANNOUNCE_CHANNEL_ID = 1047166622235893911
# General announcements ping @everyone

# =========================================================
# CONFIG — Shared
# =========================================================
LOG_CHANNEL_ID = 1485265848099799163

STAFF_ROLE_IDS: set[int] = {
    850391095845584937,   # Leader
    850391378559238235,   # Co-Leader
    990011447193006101,   # Manager
}

CREW_PANEL_TAG    = "DIFF_CREW_ANNOUNCE_PANEL_V1"
GENERAL_PANEL_TAG = "DIFF_GENERAL_ANNOUNCE_PANEL_V1"

DATA_DIR         = "diff_data"
CREW_PANEL_FILE    = os.path.join(DATA_DIR, "crew_announce_panel.json")
GENERAL_PANEL_FILE = os.path.join(DATA_DIR, "general_announce_panel.json")

DIFF_LOGO_URL = (
    "https://media.discordapp.net/attachments/1107375326625005719/"
    "1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm="
    "2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
    "&=&format=webp&quality=lossless&width=1376&height=917"
)


# =========================================================
# HELPERS
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


def _get_saved_msg_id(path: str) -> Optional[int]:
    v = _load_json(path).get("panel_message_id")
    return int(v) if v else None


def _save_msg_id(path: str, msg_id: int) -> None:
    data = _load_json(path)
    data["panel_message_id"] = msg_id
    _save_json(path, data)


def _is_staff(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    return any(r.id in STAFF_ROLE_IDS for r in member.roles)


async def _ensure_panel(
    bot: commands.Bot,
    channel_id: int,
    panel_file: str,
    panel_tag: str,
    panel_embed: discord.Embed,
    panel_view: discord.ui.View,
    label: str,
) -> None:
    channel = bot.get_channel(channel_id)
    if not isinstance(channel, discord.TextChannel):
        try:
            channel = await bot.fetch_channel(channel_id)
        except Exception:
            channel = None
    if not isinstance(channel, discord.TextChannel):
        print(f"[AnnouncePanels] {label} channel {channel_id} not found.")
        return

    saved_id = _get_saved_msg_id(panel_file)
    if saved_id:
        try:
            msg = await channel.fetch_message(saved_id)
            await msg.edit(embed=panel_embed, view=panel_view)
            print(f"[AnnouncePanels] {label} panel refreshed.")
            return
        except discord.NotFound:
            pass
        except Exception as e:
            print(f"[AnnouncePanels] {label} edit failed: {e}")

    # Fallback — scan and delete stale panel by footer tag
    try:
        async for msg in channel.history(limit=50):
            if (
                msg.author == bot.user
                and msg.embeds
                and msg.embeds[0].footer.text == panel_tag
            ):
                try:
                    await msg.delete()
                except Exception:
                    pass
    except Exception:
        pass

    try:
        new_msg = await channel.send(embed=panel_embed, view=panel_view)
        _save_msg_id(panel_file, new_msg.id)
        print(f"[AnnouncePanels] {label} panel posted: {new_msg.id}")
    except Exception as e:
        print(f"[AnnouncePanels] {label} post failed: {e}")


# =========================================================
# CREW ANNOUNCEMENT MODAL + VIEW
# =========================================================
class CrewAnnouncementModal(discord.ui.Modal, title="Create Crew Announcement"):
    title_input = discord.ui.TextInput(
        label="Announcement Title",
        placeholder="Example: Saturday Meet Update",
        max_length=100, required=True,
    )
    message_input = discord.ui.TextInput(
        label="Announcement Message",
        placeholder="Type the full crew announcement here...",
        style=discord.TextStyle.paragraph, max_length=2000, required=True,
    )
    footer_input = discord.ui.TextInput(
        label="Footer Text (optional)",
        placeholder="Example: DIFF Staff Team",
        max_length=100, required=False,
    )

    def __init__(self, cog: "AnnouncementPanelsCog"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction) -> None:
        member = interaction.user
        if not isinstance(member, discord.Member) or not _is_staff(member):
            return await interaction.response.send_message(
                "Only staff can post crew announcements.", ephemeral=True
            )

        channel = interaction.client.get_channel(CREW_ANNOUNCE_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message(
                "Crew announcement channel not found.", ephemeral=True
            )

        footer = str(self.footer_input).strip() or "DIFF Crew Announcement System"

        embed = discord.Embed(
            title=str(self.title_input),
            description=str(self.message_input),
            color=discord.Color.red(),
        )
        embed.set_author(
            name=f"Posted by {member.display_name}",
            icon_url=member.display_avatar.url if member.display_avatar else None,
        )
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.set_footer(text=footer)

        crew_role = interaction.guild.get_role(CREW_ROLE_ID) if interaction.guild else None
        ping = crew_role.mention if crew_role else ""

        await channel.send(
            content=ping,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True),
        )
        await interaction.response.send_message(
            "Crew announcement posted successfully.", ephemeral=True
        )
        await self.cog.log_action(
            interaction.guild,
            f"📢 Crew announcement `{str(self.title_input)}` posted by {member.mention}"
        )


class CrewAnnouncePanelView(discord.ui.View):
    def __init__(self, cog: "AnnouncementPanelsCog"):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Make Crew Announcement", emoji="📣",
                       style=discord.ButtonStyle.danger,
                       custom_id="diff_crew_announce_create_v1")
    async def make_crew_announcement(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user
        if not isinstance(member, discord.Member) or not _is_staff(member):
            return await interaction.response.send_message(
                "Only staff can use this button.", ephemeral=True
            )
        await interaction.response.send_modal(CrewAnnouncementModal(self.cog))

    @discord.ui.button(label="Refresh Panel", emoji="♻️",
                       style=discord.ButtonStyle.secondary,
                       custom_id="diff_crew_announce_refresh_v1")
    async def refresh_crew_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user
        if not isinstance(member, discord.Member) or not _is_staff(member):
            return await interaction.response.send_message(
                "Only staff can refresh this panel.", ephemeral=True
            )
        await interaction.response.defer(ephemeral=True)
        await self.cog.ensure_crew_panel()
        await interaction.followup.send("Crew announcement panel refreshed.", ephemeral=True)


# =========================================================
# GENERAL ANNOUNCEMENT MODAL + SMART-PING VIEW
# =========================================================
class GeneralAnnouncementModal(discord.ui.Modal, title="Create General Announcement"):
    title_input = discord.ui.TextInput(
        label="Announcement Title",
        placeholder="Example: Server Update",
        max_length=100, required=True,
    )
    message_input = discord.ui.TextInput(
        label="Announcement Message",
        placeholder="Type the full announcement here...",
        style=discord.TextStyle.paragraph, max_length=2000, required=True,
    )
    footer_input = discord.ui.TextInput(
        label="Footer Text (optional)",
        placeholder="Example: DIFF Staff Team",
        max_length=100, required=False,
    )

    def __init__(self, cog: "AnnouncementPanelsCog", ping_mode: str):
        super().__init__()
        self.cog       = cog
        self.ping_mode = ping_mode   # "everyone" | "here" | "crew" | "none"

    async def on_submit(self, interaction: discord.Interaction) -> None:
        member = interaction.user
        if not isinstance(member, discord.Member) or not _is_staff(member):
            return await interaction.response.send_message(
                "Only staff can post general announcements.", ephemeral=True
            )

        channel = interaction.client.get_channel(GENERAL_ANNOUNCE_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message(
                "General announcement channel not found.", ephemeral=True
            )

        footer = str(self.footer_input).strip() or "DIFF General Announcement System"

        embed = discord.Embed(
            title=str(self.title_input),
            description=str(self.message_input),
            color=discord.Color.blurple(),
        )
        embed.set_author(
            name=f"Posted by {member.display_name}",
            icon_url=member.display_avatar.url if member.display_avatar else None,
        )
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.set_footer(text=footer)

        # Resolve ping content and allowed_mentions based on chosen mode
        if self.ping_mode == "everyone":
            content          = "@everyone"
            allowed_mentions = discord.AllowedMentions(everyone=True)
        elif self.ping_mode == "here":
            content          = "@here"
            allowed_mentions = discord.AllowedMentions(everyone=True)
        elif self.ping_mode == "crew":
            crew_role        = interaction.guild.get_role(CREW_ROLE_ID) if interaction.guild else None
            content          = crew_role.mention if crew_role else None
            allowed_mentions = discord.AllowedMentions(roles=True)
        else:  # "none"
            content          = None
            allowed_mentions = discord.AllowedMentions.none()

        await channel.send(content=content, embed=embed, allowed_mentions=allowed_mentions)
        await interaction.response.send_message(
            f"General announcement posted with **{self.ping_mode}** ping.", ephemeral=True
        )
        await self.cog.log_action(
            interaction.guild,
            f"📢 General announcement `{str(self.title_input)}` "
            f"(ping: {self.ping_mode}) posted by {member.mention}"
        )


class _PingSelect(discord.ui.Select):
    """Dropdown that asks which ping type to use, then opens the modal."""

    def __init__(self, cog: "AnnouncementPanelsCog"):
        super().__init__(
            placeholder="Choose ping type then post announcement…",
            min_values=1,
            max_values=1,
            custom_id="diff_general_announce_ping_select_v1",
            options=[
                discord.SelectOption(label="Ping @everyone",  value="everyone", emoji="📣",
                                     description="Notify all server members"),
                discord.SelectOption(label="Ping @here",      value="here",     emoji="📍",
                                     description="Notify online members only"),
                discord.SelectOption(label="Ping Crew Role",  value="crew",     emoji="👥",
                                     description="Notify crew members"),
                discord.SelectOption(label="No Ping",         value="none",     emoji="🔕",
                                     description="Post without any ping"),
            ],
        )
        self.cog = cog

    async def callback(self, interaction: discord.Interaction) -> None:
        member = interaction.user
        if not isinstance(member, discord.Member) or not _is_staff(member):
            return await interaction.response.send_message(
                "Only staff can use this panel.", ephemeral=True
            )
        await interaction.response.send_modal(
            GeneralAnnouncementModal(self.cog, self.values[0])
        )


class GeneralAnnouncePanelView(discord.ui.View):
    def __init__(self, cog: "AnnouncementPanelsCog"):
        super().__init__(timeout=None)
        self.cog = cog
        self.add_item(_PingSelect(cog))

    @discord.ui.button(label="Refresh Panel", emoji="♻️",
                       style=discord.ButtonStyle.secondary,
                       custom_id="diff_general_announce_refresh_v1")
    async def refresh_general_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user
        if not isinstance(member, discord.Member) or not _is_staff(member):
            return await interaction.response.send_message(
                "Only staff can refresh this panel.", ephemeral=True
            )
        await interaction.response.defer(ephemeral=True)
        await self.cog.ensure_general_panel()
        await interaction.followup.send("General announcement panel refreshed.", ephemeral=True)


# =========================================================
# COG
# =========================================================
class AnnouncementPanelsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot              = bot
        self.crew_view        = CrewAnnouncePanelView(self)
        self.general_view     = GeneralAnnouncePanelView(self)
        self.bot.add_view(self.crew_view)
        self.bot.add_view(self.general_view)

    async def log_action(self, guild: Optional[discord.Guild], message: str) -> None:
        if not guild or not LOG_CHANNEL_ID:
            return
        ch = guild.get_channel(LOG_CHANNEL_ID)
        if isinstance(ch, discord.TextChannel):
            try:
                await ch.send(message)
            except Exception:
                pass

    def _crew_panel_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="📢 DIFF Crew Announcement Center",
            color=discord.Color.dark_red(),
            description=(
                "**Staff Announcement Panel**\n\n"
                "Use the button below to post an official crew announcement.\n"
                "The bot will ping **Crew Members** automatically.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "• Keep announcements clear and important\n"
                "• Use short titles when possible\n"
                "• Avoid spam or duplicate posts\n"
                "━━━━━━━━━━━━━━━━━━━━━━"
            ),
        )
        embed.add_field(
            name="📋 Staff Commands",
            value="`!refresh_crew_announce_panel` — Refresh this panel",
            inline=False,
        )
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.set_footer(text=CREW_PANEL_TAG)
        return embed

    def _general_panel_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="📢 DIFF General Announcement Center",
            color=discord.Color.dark_blue(),
            description=(
                "**Staff General Announcement Panel**\n\n"
                "Use the dropdown below to choose a ping type, then fill in your announcement.\n\n"
                "**Ping Options:**\n"
                "📣 **Ping @everyone** — notify all server members\n"
                "📍 **Ping @here** — notify online members only\n"
                "👥 **Ping Crew Role** — notify crew members\n"
                "🔕 **No Ping** — post without any ping\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Staff use only\n"
                "━━━━━━━━━━━━━━━━━━━━━━"
            ),
        )
        embed.add_field(
            name="📋 Staff Commands",
            value="`!refresh_general_announce_panel` — Refresh this panel",
            inline=False,
        )
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.set_footer(text=GENERAL_PANEL_TAG)
        return embed

    async def ensure_crew_panel(self) -> None:
        await _ensure_panel(
            self.bot,
            CREW_ANNOUNCE_CHANNEL_ID,
            CREW_PANEL_FILE,
            CREW_PANEL_TAG,
            self._crew_panel_embed(),
            self.crew_view,
            "Crew Announce",
        )

    async def ensure_general_panel(self) -> None:
        await _ensure_panel(
            self.bot,
            GENERAL_ANNOUNCE_CHANNEL_ID,
            GENERAL_PANEL_FILE,
            GENERAL_PANEL_TAG,
            self._general_panel_embed(),
            self.general_view,
            "General Announce",
        )

    @commands.Cog.listener()
    async def on_ready(self):
        await self.ensure_crew_panel()
        await self.ensure_general_panel()
        print("[AnnouncePanels] Cog ready.")

    @commands.command(name="refresh_crew_announce_panel")
    @commands.has_permissions(manage_guild=True)
    async def cmd_refresh_crew(self, ctx: commands.Context):
        await self.ensure_crew_panel()
        await ctx.send("Crew announcement panel refreshed.", delete_after=8)

    @commands.command(name="refresh_general_announce_panel")
    @commands.has_permissions(manage_guild=True)
    async def cmd_refresh_general(self, ctx: commands.Context):
        await self.ensure_general_panel()
        await ctx.send("General announcement panel refreshed.", delete_after=8)


# =========================================================
# SETUP
# =========================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(AnnouncementPanelsCog(bot))
