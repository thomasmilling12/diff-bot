from __future__ import annotations

import discord
from discord.ext import commands

GUILD_ID   = 850386896509337710
CHANNEL_ID = 1156043026855108679

DIFF_LOGO_URL = (
    "https://media.discordapp.net/attachments/1107375326625005719/1484949205331083375/"
    "content.png?ex=69c01637&is=69bec4b7&hm=2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
    "&=&format=webp&quality=lossless&width=1376&height=917"
)

EMBED_COLOR = 0x111111
PANEL_TAG   = "DIFF_CONTENT_SUPPORT_PANEL_V1"


class DiffContentSupportPanel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("[DiffContentSupportPanel] Cog ready.")
        guild = self.bot.get_guild(GUILD_ID)
        if guild is None:
            return
        channel = guild.get_channel(CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            return
        await self._post_or_refresh(channel)

    def _build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="DIFF Content Support Hub",
            description=(
                "Welcome to the **DIFF Content Support Channel** — your place for help, feedback, "
                "and improving your content.\n\n"
                "Use this channel to:\n"
                "• Ask for help with car photos, edits, or clips\n"
                "• Get feedback on your builds or posts\n"
                "• Share content ideas before posting\n"
                "• Learn how to improve your DIFF-style content\n\n"
                "**Channel Purpose**\n"
                "This channel is here to help members grow, improve, and stay consistent with "
                "clean, high-quality DIFF content.\n\n"
                "**Please avoid:**\n"
                "• Spamming links without context\n"
                "• Ignoring feedback from others\n"
                "• Off-topic conversations\n"
                "• Disrespectful behavior\n\n"
                "Ask smart. Improve fast. Stay DIFF."
            ),
            color=EMBED_COLOR,
        )
        embed.add_field(
            name="📋 Staff Commands",
            value="`!postcontentsupportpanel` — Post / refresh this panel",
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

    @commands.command(name="postcontentsupportpanel")
    @commands.has_permissions(manage_guild=True)
    async def post_content_support_panel(self, ctx: commands.Context):
        """Posts or refreshes the DIFF Content Support panel. Usage: !postcontentsupportpanel"""
        channel = ctx.guild.get_channel(CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            await ctx.send("❌ Content support channel not found.", delete_after=8)
            return
        try:
            await ctx.message.delete()
        except Exception:
            pass
        msg = await self._post_or_refresh(channel)
        if msg:
            await ctx.send(f"✅ Content support panel posted/refreshed in {channel.mention}.", delete_after=8)


async def setup(bot: commands.Bot):
    await bot.add_cog(DiffContentSupportPanel(bot))
