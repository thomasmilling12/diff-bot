from __future__ import annotations

import discord
from discord.ext import commands

GUILD_ID   = 850386896509337710
CHANNEL_ID = 1486041362708299897

DIFF_LOGO_URL = (
    "https://media.discordapp.net/attachments/1107375326625005719/1484949205331083375/"
    "content.png?ex=69c01637&is=69bec4b7&hm=2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
    "&=&format=webp&quality=lossless&width=1376&height=917"
)

EMBED_COLOR = 0x111111
PANEL_TAG   = "DIFF_IRL_CAR_PHOTOS_PANEL_V1"


class DiffIRLCarPhotosPanel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("[DiffIRLCarPhotosPanel] Cog ready.")
        guild = self.bot.get_guild(GUILD_ID)
        if guild is None:
            return
        channel = guild.get_channel(CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            return
        await self._post_or_refresh(channel)

    def _build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="DIFF IRL Car Photos Hub",
            description=(
                "Welcome to the **DIFF IRL Car Photos Channel** — the place to share your real-life car pictures, "
                "clean shots, favorite angles, edits, and automotive photography.\n\n"
                "Use this channel to:\n"
                "• Post your own IRL car photos\n"
                "• Share clean rollers, parked shots, and detailed angles\n"
                "• Show off mods, fitment, wheels, paint, and builds\n"
                "• Support other members' real-life car content\n\n"
                "**Channel Purpose**\n"
                "This channel is for showcasing real cars, real photography, and clean automotive content that fits "
                "the DIFF style.\n\n"
                "**Please avoid:**\n"
                "• Low-effort spam or unrelated posts\n"
                "• Blurry photo dumps with no context\n"
                "• Disrespectful comments toward other members' vehicles\n"
                "• Anything that breaks server rules\n\n"
                "Keep it clean. Keep it real. Keep it DIFF."
            ),
            color=EMBED_COLOR,
        )
        embed.add_field(
            name="📋 Staff Commands",
            value="`!postirlpanel` — Post / refresh this panel",
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

    @commands.command(name="postirlpanel")
    @commands.has_permissions(manage_guild=True)
    async def post_irl_panel(self, ctx: commands.Context):
        """Posts or refreshes the DIFF IRL Car Photos panel. Usage: !postirlpanel"""
        channel = ctx.guild.get_channel(CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            await ctx.send("❌ IRL car photos channel not found.", delete_after=8)
            return
        try:
            await ctx.message.delete()
        except Exception:
            pass
        msg = await self._post_or_refresh(channel)
        if msg:
            await ctx.send(f"✅ IRL car photos panel posted/refreshed in {channel.mention}.", delete_after=8)


async def setup(bot: commands.Bot):
    await bot.add_cog(DiffIRLCarPhotosPanel(bot))
