from __future__ import annotations

import asyncio
import json
import os
import re
from typing import Optional

import discord
from discord.ext import commands

# =========================================================
# CONFIG
# =========================================================
TARGET_CHANNEL_ID  = 1177449010949259355
GUILD_ID           = 850386896509337710
LOG_CHANNEL_ID     = 1485265848099799163   # staff-logs

COLOR_TEAM_ROLE_ID = 0   # <-- fill in your Color Team role ID
TICKET_CATEGORY_ID = 0   # <-- fill in the category ID where tickets should be created

DATA_FILE = os.path.join("diff_data", "color_lab_panel.json")

DIFF_LOGO_URL = (
    "https://media.discordapp.net/attachments/1107375326625005719/"
    "1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm="
    "2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
    "&=&format=webp&quality=lossless&width=1376&height=917"
)

EMBED_COLOR   = 0x8F7CFF
SUCCESS_COLOR = 0x57F287
ERROR_COLOR   = 0xED4245
PANEL_TAG     = "DIFF_COLOR_LAB_PANEL"


# =========================================================
# STORAGE HELPERS
# =========================================================
def _load() -> dict:
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict) -> None:
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def _get_msg_id() -> Optional[int]:
    v = _load().get("panel_message_id")
    return int(v) if v else None


def _set_msg_id(mid: int) -> None:
    d = _load()
    d["panel_message_id"] = mid
    _save(d)


def _clean_name(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9-]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text[:25] if text else "request"


# =========================================================
# MODALS
# =========================================================
class ColorTicketRequestModal(discord.ui.Modal, title="Open Private Color Request"):
    reference = discord.ui.TextInput(
        label="Reference Image Link or Description",
        placeholder="Paste image link or describe the exact color/build",
        required=True,
        max_length=300,
        style=discord.TextStyle.paragraph,
    )
    hex_code = discord.ui.TextInput(
        label="Hex Code",
        placeholder="#A9E3D6 or Unknown",
        required=True,
        max_length=30,
    )
    car_name = discord.ui.TextInput(
        label="Car Name",
        placeholder="Example: Vorschlaghammer",
        required=True,
        max_length=100,
    )
    finish = discord.ui.TextInput(
        label="Finish",
        placeholder="Metallic / Pearlescent / Matte / Unknown",
        required=True,
        max_length=100,
    )
    extra_notes = discord.ui.TextInput(
        label="Extra Notes",
        placeholder="Anything else the Color Team should know",
        required=False,
        max_length=400,
        style=discord.TextStyle.paragraph,
    )

    def __init__(self, cog: "ColorLabCog"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            return await interaction.response.send_message(
                "This can only be used inside the server.", ephemeral=True
            )

        if COLOR_TEAM_ROLE_ID == 0 or TICKET_CATEGORY_ID == 0:
            return await interaction.response.send_message(
                "The Color Lab ticket system is not fully configured yet. "
                "Please ask staff to set the Color Team role and ticket category.",
                ephemeral=True,
            )

        color_team_role = guild.get_role(COLOR_TEAM_ROLE_ID)
        category = guild.get_channel(TICKET_CATEGORY_ID)

        if color_team_role is None:
            return await interaction.response.send_message(
                "Could not find the Color Team role. Please contact staff.", ephemeral=True
            )
        if not isinstance(category, discord.CategoryChannel):
            return await interaction.response.send_message(
                "Could not find the ticket category. Please contact staff.", ephemeral=True
            )

        requester = interaction.user

        # Prevent duplicate open tickets for the same user
        for ch in category.text_channels:
            if ch.topic and f"color_user:{requester.id}" in ch.topic:
                return await interaction.response.send_message(
                    f"You already have an open color ticket: {ch.mention}", ephemeral=True
                )

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            requester: discord.PermissionOverwrite(
                view_channel=True, send_messages=True,
                read_message_history=True, attach_files=True, embed_links=True,
            ),
            color_team_role: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True,
                manage_messages=True, attach_files=True, embed_links=True,
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True, send_messages=True,
                manage_channels=True, manage_messages=True, read_message_history=True,
            ),
        }

        await interaction.response.defer(ephemeral=True)

        try:
            ticket_ch = await guild.create_text_channel(
                name=f"color-{_clean_name(requester.display_name)}",
                category=category,
                overwrites=overwrites,
                topic=f"DIFF Color Lab private ticket | color_user:{requester.id}",
                reason=f"Color request ticket for {requester}",
            )
        except Exception as e:
            return await interaction.followup.send(
                f"Failed to create ticket channel: {e}", ephemeral=True
            )

        ticket_embed = discord.Embed(
            title="🎨 Private Color Request",
            description=(
                f"{requester.mention}, your private Color Lab ticket is open.\n\n"
                f"{color_team_role.mention} will review your request and reply here."
            ),
            color=EMBED_COLOR,
        )
        ticket_embed.add_field(name="Reference", value=str(self.reference), inline=False)
        ticket_embed.add_field(name="Hex Code", value=f"`{self.hex_code}`", inline=True)
        ticket_embed.add_field(name="Car Name", value=str(self.car_name), inline=True)
        ticket_embed.add_field(name="Finish", value=str(self.finish), inline=True)
        if str(self.extra_notes).strip():
            ticket_embed.add_field(name="Extra Notes", value=str(self.extra_notes), inline=False)
        ticket_embed.set_thumbnail(url=DIFF_LOGO_URL)
        ticket_embed.set_footer(text="DIFF Color Lab • Private Ticket")

        await ticket_ch.send(
            content=f"{requester.mention} {color_team_role.mention}",
            embed=ticket_embed,
            view=ColorTicketControlsView(self.cog),
            allowed_mentions=discord.AllowedMentions(users=True, roles=True),
        )

        await interaction.followup.send(
            f"Your private color ticket has been created: {ticket_ch.mention}", ephemeral=True
        )
        await self.cog.log_action(
            guild, f"🎨 Opened color ticket {ticket_ch.mention} for {requester.mention}"
        )


class ColorResultModal(discord.ui.Modal, title="Post Official Color Result"):
    requester = discord.ui.TextInput(
        label="Requester",
        placeholder="@user or username",
        required=True,
        max_length=100,
    )
    base_color = discord.ui.TextInput(
        label="Base Color",
        placeholder="Example: #A9E3D6 / Seafoam Blue",
        required=True,
        max_length=100,
    )
    pearl = discord.ui.TextInput(
        label="Pearl Color",
        placeholder="Example: Ice White / Diamond Blue / None",
        required=True,
        max_length=100,
    )
    finish = discord.ui.TextInput(
        label="Finish",
        placeholder="Metallic / Pearlescent / Matte / Worn",
        required=True,
        max_length=100,
    )
    notes = discord.ui.TextInput(
        label="Extra Notes",
        placeholder="Any GTA notes, lighting notes, or tips",
        required=False,
        max_length=400,
        style=discord.TextStyle.paragraph,
    )

    async def on_submit(self, interaction: discord.Interaction):
        member = interaction.user if isinstance(interaction.user, discord.Member) else None
        if member is None:
            return await interaction.response.send_message(
                "Could not verify your permissions.", ephemeral=True
            )

        allowed = (
            member.guild_permissions.manage_messages
            or member.guild_permissions.administrator
            or (COLOR_TEAM_ROLE_ID and any(r.id == COLOR_TEAM_ROLE_ID for r in member.roles))
        )
        if not allowed:
            return await interaction.response.send_message(
                "Only staff or the Color Team can post official color results.", ephemeral=True
            )

        embed = discord.Embed(
            title="✅ Official Color Result",
            color=SUCCESS_COLOR,
            description="A Color Team member has posted the official result for this request.",
        )
        embed.add_field(name="Requester",  value=str(self.requester),  inline=False)
        embed.add_field(name="Base Color", value=str(self.base_color), inline=True)
        embed.add_field(name="Pearl",      value=str(self.pearl),      inline=True)
        embed.add_field(name="Finish",     value=str(self.finish),     inline=True)
        if str(self.notes).strip():
            embed.add_field(name="Notes", value=str(self.notes), inline=False)
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.set_footer(text=f"Posted by {interaction.user.display_name} • DIFF Color Lab")
        await interaction.response.send_message(embed=embed)


# =========================================================
# VIEWS
# =========================================================
class ColorLabPanelView(discord.ui.View):
    def __init__(self, cog: "ColorLabCog"):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Open Private Request",
        emoji="🎫",
        style=discord.ButtonStyle.primary,
        custom_id="diff_color_lab_open_private_request_v1",
    )
    async def open_private_request(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ColorTicketRequestModal(self.cog))

    @discord.ui.button(
        label="Refresh Panel",
        emoji="♻️",
        style=discord.ButtonStyle.secondary,
        custom_id="diff_color_lab_refresh_private_panel_v1",
    )
    async def refresh_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user if isinstance(interaction.user, discord.Member) else None
        if member is None:
            return await interaction.response.send_message(
                "Could not verify your permissions.", ephemeral=True
            )
        allowed = (
            member.guild_permissions.manage_messages
            or member.guild_permissions.manage_channels
            or member.guild_permissions.administrator
            or (COLOR_TEAM_ROLE_ID and any(r.id == COLOR_TEAM_ROLE_ID for r in member.roles))
        )
        if not allowed:
            return await interaction.response.send_message(
                "Only staff or the Color Team can refresh this panel.", ephemeral=True
            )
        await interaction.response.defer(ephemeral=True)
        await self.cog.ensure_panel()
        await interaction.followup.send("Color Lab panel refreshed.", ephemeral=True)


class ColorTicketControlsView(discord.ui.View):
    def __init__(self, cog: "ColorLabCog"):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Post Official Result",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="diff_color_lab_ticket_post_result_v1",
    )
    async def post_result(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ColorResultModal())

    @discord.ui.button(
        label="Close Ticket",
        emoji="🔒",
        style=discord.ButtonStyle.danger,
        custom_id="diff_color_lab_ticket_close_v1",
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user if isinstance(interaction.user, discord.Member) else None
        if member is None:
            return await interaction.response.send_message(
                "Could not verify your permissions.", ephemeral=True
            )
        allowed = (
            member.guild_permissions.manage_channels
            or member.guild_permissions.administrator
            or (COLOR_TEAM_ROLE_ID and any(r.id == COLOR_TEAM_ROLE_ID for r in member.roles))
        )
        if not allowed:
            return await interaction.response.send_message(
                "Only staff or the Color Team can close tickets.", ephemeral=True
            )

        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message(
                "This button only works inside a ticket channel.", ephemeral=True
            )

        await interaction.response.send_message("Closing ticket in 5 seconds…")
        await self.cog.log_action(
            interaction.guild,
            f"🔒 Closed color ticket `#{channel.name}` by {interaction.user.mention}"
        )
        await asyncio.sleep(5)
        await channel.delete(reason=f"Closed by {interaction.user}")


# =========================================================
# COG
# =========================================================
class ColorLabCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._panel_view  = ColorLabPanelView(self)
        self._ticket_view = ColorTicketControlsView(self)
        bot.add_view(self._panel_view)
        bot.add_view(self._ticket_view)

    # ------------------------------------------------------------------
    def _build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🎨 DIFF Color Lab",
            description=(
                "Welcome to the official **DIFF Color Lab**.\n\n"
                "Need help recreating a custom GTA color? Press the button below to open a "
                "**private ticket** that only you and the **Color Team** can see.\n\n"
                "**How it works:**\n"
                "• Press **Open Private Request**\n"
                "• Fill in your reference image, hex code, car name, and finish\n"
                "• A private ticket is created just for you\n"
                "• Color Team responds directly inside your ticket\n\n"
                "**Why tickets:**\n"
                "• Keeps this channel clean\n"
                "• Requests are easier to track and follow up\n"
                "• Private one-on-one help from the Color Team"
            ),
            color=EMBED_COLOR,
        )
        embed.add_field(
            name="What to include",
            value=(
                "• Reference image or image link\n"
                "• Hex code if you have one\n"
                "• Car name\n"
                "• Finish type (Metallic / Matte / Pearlescent)"
            ),
            inline=False,
        )
        embed.add_field(
            name="Ticket Access",
            value="Only the requester, Color Team, and admins can see the ticket.",
            inline=False,
        )
        embed.add_field(
            name="Anti-Dupe System",
            value="This panel refreshes the same post instead of creating duplicates.",
            inline=False,
        )
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.set_footer(text=f"DIFF Color Lab • Private Request System • {PANEL_TAG}")
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
    async def ensure_panel(self) -> None:
        channel = await self._get_channel()
        if channel is None:
            print(f"[ColorLab] Channel not found: {TARGET_CHANNEL_ID}")
            return

        embed = self._build_embed()
        saved_id = _get_msg_id()

        if saved_id:
            try:
                msg = await channel.fetch_message(saved_id)
                await msg.edit(embed=embed, view=self._panel_view)
                print("[ColorLab] Panel refreshed.")
                return
            except discord.NotFound:
                pass
            except Exception as e:
                print(f"[ColorLab] Edit failed: {e}")

        # Remove stale duplicates by footer tag
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
            new_msg = await channel.send(embed=embed, view=self._panel_view)
            _set_msg_id(new_msg.id)
            print(f"[ColorLab] Panel posted: {new_msg.id}")
        except Exception as e:
            print(f"[ColorLab] Failed to post panel: {e}")

    # ------------------------------------------------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        await self.ensure_panel()
        print("[ColorLab] Cog ready.")

    @commands.command(name="refresh_color_lab")
    @commands.has_permissions(manage_guild=True)
    async def refresh_cmd(self, ctx: commands.Context):
        """Force-refresh the Color Lab panel."""
        await self.ensure_panel()
        await ctx.send("Color Lab panel refreshed.", delete_after=10)


# =========================================================
# SETUP
# =========================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(ColorLabCog(bot))
