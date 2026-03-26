from __future__ import annotations

import discord
from discord.ext import commands

GUILD_ID    = 850386896509337710
CHANNEL_ID  = 1486040942065750058

DIFF_LOGO_URL = (
    "https://media.discordapp.net/attachments/1107375326625005719/1484949205331083375/"
    "content.png?ex=69c01637&is=69bec4b7&hm=2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
    "&=&format=webp&quality=lossless&width=1376&height=917"
)

EMBED_COLOR = 0x111111
PANEL_TAG   = "DIFF_MEMES_PANEL_V1"


class DiffMemesPanel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("[DiffMemesPanel] Cog ready.")
        guild = self.bot.get_guild(GUILD_ID)
        if guild is None:
            return
        channel = guild.get_channel(CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            return
        await self._post_or_refresh(channel)

    def _build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="DIFF Memes Hub",
            description=(
                "Welcome to the **DIFF Memes Channel** — the place for jokes, funny clips, "
                "lighthearted content, and community laughs.\n\n"
                "Use this channel to:\n"
                "• Share funny car meet memes\n"
                "• Post GTA / PS5 / DIFF-related jokes\n"
                "• Drop reaction images, clips, and entertaining content\n"
                "• Keep the community active with good energy\n\n"
                "**Channel Purpose**\n"
                "This channel is here to keep the server fun, social, and entertaining while still "
                "representing DIFF properly.\n\n"
                "**Please avoid:**\n"
                "• Spam or flooding the channel\n"
                "• Offensive or disrespectful posts\n"
                "• Anything that breaks server rules\n\n"
                "Post smart. Keep it funny. Keep it DIFF."
            ),
            color=EMBED_COLOR,
        )
        embed.add_field(
            name="📋 Staff Commands",
            value="`!postmemespanel` — Post / refresh this panel",
            inline=False,
        )
        embed.set_image(url=DIFF_LOGO_URL)
        embed.set_footer(text=PANEL_TAG)
        return embed

    async def _post_or_refresh(self, channel: discord.TextChannel) -> discord.Message | None:
        embed = self._build_embed()
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

    @commands.command(name="postmemespanel")
    @commands.has_permissions(manage_guild=True)
    async def post_memes_panel(self, ctx: commands.Context):
        """Posts or refreshes the DIFF Memes Hub panel. Usage: !postmemespanel"""
        channel = ctx.guild.get_channel(CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            await ctx.send("❌ Memes channel not found.", delete_after=8)
            return
        try:
            await ctx.message.delete()
        except Exception:
            pass
        msg = await self._post_or_refresh(channel)
        if msg:
            await ctx.send(f"✅ Memes panel posted/refreshed in {channel.mention}.", delete_after=8)


async def setup(bot: commands.Bot):
    await bot.add_cog(DiffMemesPanel(bot))
