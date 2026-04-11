from __future__ import annotations

import discord
from discord.ext import commands

GUILD_ID              = 850386896509337710
HOST_PANEL_CHANNEL_ID = 1485840926612918383
MEET_CHANNEL_ID       = 1485684577073758378
HOST_LOG_CHANNEL_ID   = 1485265848099799163   # Staff Logs

HOST_ROLE_ID      = 1055823929358430248
PS5_ROLE_ID       = 1485668852921798849
CARMEET_ROLE_ID   = 1138691141009674260

DIFF_LOGO_URL = (
    "https://media.discordapp.net/attachments/1107375326625005719/1484949205331083375/"
    "content.png?ex=69c01637&is=69bec4b7&hm=2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
    "&=&format=webp&quality=lossless&width=1376&height=917"
)

EMBED_COLOR = 0x111111
PANEL_TAG   = "DIFF_HOST_MEET_SYSTEM_V1"


# ---------------------------------------------------------------------------
# Modals
# ---------------------------------------------------------------------------

class LocationUpdateModal(discord.ui.Modal, title="DIFF Meet Location Update"):
    location_name = discord.ui.TextInput(
        label="New Location / Spot Name",
        placeholder="Example: Airport Parking Lot / Spot 2",
        max_length=100,
    )
    extra_notes = discord.ui.TextInput(
        label="Extra Notes",
        placeholder="Example: Pull in slowly, stay in order, no revving",
        required=False,
        style=discord.TextStyle.paragraph,
        max_length=300,
    )

    def __init__(self, cog: "DiffMeetHostSystem"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        meet_channel = interaction.client.get_channel(MEET_CHANNEL_ID)
        if meet_channel is None:
            await interaction.response.send_message("Meet channel not found.", ephemeral=True)
            return

        embed = discord.Embed(
            title="DIFF Meet Location Update",
            description=(
                f"**Host:** {interaction.user.mention}\n"
                f"**New Location:** {self.location_name}\n\n"
                f"**Notes:**\n{self.extra_notes or 'No extra notes provided.'}"
            ),
            color=EMBED_COLOR,
        )
        embed.set_image(url=DIFF_LOGO_URL)
        embed.set_footer(text="DIFF Meet Location Update")

        await meet_channel.send(embed=embed)
        await self.cog.log_host_action(
            interaction.guild,
            f"📍 **Location Update**\nHost: {interaction.user.mention}\nLocation: {self.location_name}",
        )
        await interaction.response.send_message(
            f"Location update sent in {meet_channel.mention}.", ephemeral=True
        )


# ---------------------------------------------------------------------------
# View
# ---------------------------------------------------------------------------

class HostMeetControlView(discord.ui.View):
    def __init__(self, cog: "DiffMeetHostSystem"):
        super().__init__(timeout=None)
        self.cog = cog

    def _has_access(self, user: discord.Member) -> bool:
        if user.guild_permissions.administrator or user.guild_permissions.manage_guild:
            return True
        return any(r.id == HOST_ROLE_ID for r in user.roles)

    @discord.ui.button(label="Start Meet", style=discord.ButtonStyle.success, emoji="🏁", custom_id="diff:start_meet")
    async def start_meet(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._has_access(interaction.user):
            await interaction.response.send_message("Only approved hosts or staff can use this panel.", ephemeral=True)
            return

        meet_channel = interaction.client.get_channel(MEET_CHANNEL_ID)
        if meet_channel is None:
            await interaction.response.send_message("Meet channel not found.", ephemeral=True)
            return

        ps_role  = f"<@&{PS5_ROLE_ID}>"
        cm_role  = f"<@&{CARMEET_ROLE_ID}>"

        embed = discord.Embed(
            title="DIFF Official Meet Started",
            description=(
                f"{ps_role} {cm_role}\n\n"
                f"The meet is now **live**.\n\n"
                f"**Host:** {interaction.user.mention}\n\n"
                f"**Use this channel for:**\n"
                f"• Meet start updates\n"
                f"• Meet locations\n"
                f"• Host instructions\n"
                f"• Movement between spots\n\n"
                f"Please stay ready and follow host directions."
            ),
            color=EMBED_COLOR,
        )
        embed.set_image(url=DIFF_LOGO_URL)
        embed.set_footer(text="DIFF Meet Start Notice")

        await meet_channel.send(embed=embed)
        await self.cog.log_host_action(
            interaction.guild,
            f"🏁 **Meet Started**\nHost: {interaction.user.mention}\nChannel: {meet_channel.mention}",
        )
        await interaction.response.send_message(
            f"Meet start message sent in {meet_channel.mention}.", ephemeral=True
        )

    @discord.ui.button(label="Post Location Update", style=discord.ButtonStyle.primary, emoji="📍", custom_id="diff:location_update")
    async def location_update(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._has_access(interaction.user):
            await interaction.response.send_message("Only approved hosts or staff can use this panel.", ephemeral=True)
            return
        await interaction.response.send_modal(LocationUpdateModal(self.cog))

    @discord.ui.button(label="End Meet", style=discord.ButtonStyle.danger, emoji="🛑", custom_id="diff:end_meet")
    async def end_meet(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._has_access(interaction.user):
            await interaction.response.send_message("Only approved hosts or staff can use this panel.", ephemeral=True)
            return

        meet_channel = interaction.client.get_channel(MEET_CHANNEL_ID)
        if meet_channel is None:
            await interaction.response.send_message("Meet channel not found.", ephemeral=True)
            return

        embed = discord.Embed(
            title="DIFF Meet Ended",
            description=(
                f"The meet has now **ended**.\n\n"
                f"**Host:** {interaction.user.mention}\n\n"
                f"Thank you to everyone who attended and helped keep the meet clean.\n"
                f"Watch for the next official announcement and future events."
            ),
            color=EMBED_COLOR,
        )
        embed.set_image(url=DIFF_LOGO_URL)
        embed.set_footer(text="DIFF Meet End Notice")

        await meet_channel.send(embed=embed)
        await self.cog.log_host_action(
            interaction.guild,
            f"🛑 **Meet Ended**\nHost: {interaction.user.mention}\nChannel: {meet_channel.mention}",
        )
        await interaction.response.send_message(
            f"Meet end message sent in {meet_channel.mention}.", ephemeral=True
        )


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------

class DiffMeetHostSystem(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(HostMeetControlView(self))

    @commands.Cog.listener()
    async def on_ready(self):
        print("[DiffMeetHostSystem] Cog ready. (panel managed by UnifiedHostHubView in bot.py)")

    def _build_panel_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="DIFF Host Meet Control",
            description=(
                "Use this panel to control the live meet flow.\n\n"
                "**Available Actions:**\n"
                "🏁 **Start Meet** — posts the official meet-start message in the meet channel\n"
                "📍 **Post Location Update** — sends the next spot / movement update\n"
                "🛑 **End Meet** — closes out the meet officially\n\n"
                "**Notes:**\n"
                "• Only approved hosts or staff can use this panel\n"
                "• All activity is logged to the staff channel\n"
                "• This panel auto-refreshes and avoids duplicates"
            ),
            color=EMBED_COLOR,
        )
        embed.add_field(
            name="📋 Staff Commands",
            value="`!posthostpanel` — Post / refresh this panel",
            inline=False,
        )
        embed.set_image(url=DIFF_LOGO_URL)
        embed.set_footer(text=PANEL_TAG)
        return embed

    async def log_host_action(self, guild: discord.Guild | None, text: str):
        if guild is None:
            return
        log_channel = guild.get_channel(HOST_LOG_CHANNEL_ID)
        if log_channel is not None:
            try:
                await log_channel.send(text)
            except Exception:
                pass

    async def _post_or_refresh(self, channel: discord.TextChannel) -> discord.Message | None:
        embed = self._build_panel_embed()
        view  = HostMeetControlView(self)
        existing: discord.Message | None = None

        async for msg in channel.history(limit=50):
            if msg.author.id == self.bot.user.id and msg.embeds:
                footer = msg.embeds[0].footer.text if msg.embeds[0].footer else ""
                if footer == PANEL_TAG:
                    if existing is None:
                        existing = msg
                    else:
                        try:
                            await msg.delete()
                        except Exception:
                            pass

        if existing:
            try:
                await existing.edit(content=None, embed=embed, view=view)
                return existing
            except Exception:
                pass

        return await channel.send(embed=embed, view=view)

    @commands.command(name="posthostpanel")
    @commands.has_permissions(manage_guild=True)
    async def post_host_panel(self, ctx: commands.Context):
        """Posts or refreshes the Host Meet Control panel. Usage: !posthostpanel"""
        channel = ctx.guild.get_channel(HOST_PANEL_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            await ctx.send("❌ Host panel channel not found.", delete_after=8)
            return
        try:
            await ctx.message.delete()
        except Exception:
            pass
        await self._post_or_refresh(channel)
        await ctx.send(f"✅ Host meet control panel posted/refreshed in {channel.mention}.", delete_after=8)


async def setup(bot: commands.Bot):
    await bot.add_cog(DiffMeetHostSystem(bot))
