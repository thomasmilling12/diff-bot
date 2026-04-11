from __future__ import annotations

import discord
from discord.ext import commands

GUILD_ID        = 850386896509337710
CHANNEL_ID      = 1485684577073758378
CARMEET_ROLE_ID = 1138691141009674260

DIFF_LOGO_URL = (
    "https://media.discordapp.net/attachments/1107375326625005719/1484949205331083375/"
    "content.png?ex=69c01637&is=69bec4b7&hm=2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
    "&=&format=webp&quality=lossless&width=1376&height=917"
)

EMBED_COLOR = 0x111111
PANEL_TAG   = "DIFF_MEET_CHANNEL_PANEL_V1"


class DiffMeetChannelPanel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("[DiffMeetChannelPanel] Cog ready.")
        guild = self.bot.get_guild(GUILD_ID)
        if guild is None:
            return
        channel = guild.get_channel(CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            return
        await self._post_or_refresh(channel)

    def _build_embed(self, guild: discord.Guild) -> discord.Embed:
        carmeet_role = guild.get_role(CARMEET_ROLE_ID)
        role_mention = carmeet_role.mention if carmeet_role else "@Car Meet"

        embed = discord.Embed(
            title="DIFF Meet Channel",
            description=(
                f"Welcome to the **DIFF Meet Channel** — this is where all official meets begin.\n\n"
                f"**Access:** This channel is for {role_mention} members only.\n\n"
                "**What this channel is used for:**\n"
                "• Meet start announcements\n"
                "• Meet locations & movement updates\n"
                "• Host instructions during the meet\n"
                "• Important real-time meet communication\n\n"
                "**Channel Rules:**\n"
                "• Only hosts or staff should speak here during meets\n"
                "• Follow all instructions posted in this channel\n"
                "• Do not spam or talk over hosts\n"
                "• Stay ready for location changes\n\n"
                "**Important:**\n"
                "When a meet is live, this channel becomes the main source of direction. "
                "Make sure notifications are on so you don't miss anything.\n\n"
                "Stay ready. Stay organized. Stay DIFF."
            ),
            color=EMBED_COLOR,
        )
        embed.add_field(
            name="📋 Staff Commands",
            value="`!postmeetchannelpanel` — Post / refresh this panel",
            inline=False,
        )
        embed.set_image(url=DIFF_LOGO_URL)
        embed.set_footer(text=PANEL_TAG)
        return embed

    async def _post_or_refresh(self, channel: discord.TextChannel) -> discord.Message | None:
        embed = self._build_embed(channel.guild)
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
                await existing.edit(content=None, embed=embed, view=None)
                return existing
            except Exception:
                pass

        return await channel.send(embed=embed)

    @commands.command(name="postmeetchannelpanel")
    @commands.has_permissions(manage_guild=True)
    async def post_meet_channel_panel(self, ctx: commands.Context):
        """Posts or refreshes the DIFF Meet Channel panel. Usage: !postmeetchannelpanel"""
        channel = ctx.guild.get_channel(CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            await ctx.send("❌ Meet channel not found.", delete_after=8)
            return
        try:
            await ctx.message.delete()
        except Exception:
            pass
        msg = await self._post_or_refresh(channel)
        if msg:
            await ctx.send(f"✅ Meet channel panel posted/refreshed in {channel.mention}.", delete_after=8)


async def setup(bot: commands.Bot):
    await bot.add_cog(DiffMeetChannelPanel(bot))
