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
PANEL_FOOTER = "Different Meets • Live meet updates"


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
            title="🏁 DIFF Meet Channel",
            description=(
                "Meet starts, locations, and live host instructions—all in one place.\n\n"
                "**During meets:** hosts and staff only. Follow directions and keep chat clear.\n"
                f"**Access:** {role_mention} · Keep channel notifications on."
            ),
            color=EMBED_COLOR,
        )
        embed.set_footer(text=PANEL_FOOTER)
        return embed

    async def _post_or_refresh(self, channel: discord.TextChannel) -> discord.Message | None:
        embed = self._build_embed(channel.guild)
        existing: discord.Message | None = None

        async for msg in channel.history(limit=50):
            if msg.author.id == self.bot.user.id and msg.embeds:
                footer = msg.embeds[0].footer.text if msg.embeds[0].footer else ""
                if footer in (PANEL_TAG, PANEL_FOOTER):
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
            except discord.NotFound:
                pass
            except discord.HTTPException as exc:
                # An edit failure is not evidence the old panel disappeared.
                print(f"[DiffMeetChannelPanel] Refresh failed: {exc}")
                return None

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
