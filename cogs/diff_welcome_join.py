from __future__ import annotations

import discord
from discord.ext import commands
from pathlib import Path

# =========================================================
# CONFIG
# =========================================================
GUILD_ID = 850386896509337710

WELCOME_INFO_CHANNEL_ID = 1047161846257438743
VERIFY_CHANNEL_ID = 1277084633858576406
WELCOME_POST_CHANNEL_ID = 1486006000808103986
UNVERIFIED_ROLE_ID = 1486011550916411512

SERVER_NAME = "Different Meets"
EMBLEM_FILE_PATH = Path("diff_welcome_emblem.png")


# =========================================================
# VIEW
# =========================================================
class WelcomeLinksView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label="Open Welcome Channel",
                style=discord.ButtonStyle.link,
                url=f"https://discord.com/channels/{GUILD_ID}/{WELCOME_INFO_CHANNEL_ID}",
                emoji="📘",
            )
        )
        self.add_item(
            discord.ui.Button(
                label="Verify Account",
                style=discord.ButtonStyle.link,
                url=f"https://discord.com/channels/{GUILD_ID}/{VERIFY_CHANNEL_ID}",
                emoji="✅",
            )
        )


# =========================================================
# COG
# =========================================================
class DiffWelcomeJoinSystem(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("[DiffWelcomeJoinSystem] Cog ready.")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id != GUILD_ID:
            return

        unverified_role = member.guild.get_role(UNVERIFIED_ROLE_ID)
        if unverified_role:
            try:
                await member.add_roles(unverified_role, reason="Auto-assigned Unverified role on join")
            except Exception as e:
                print(f"[DiffWelcomeJoinSystem] Could not assign Unverified role: {e}")

        await self._send_welcome(member)


    @commands.command(name="previewwelcome")
    @commands.has_permissions(manage_guild=True)
    async def previewwelcome(self, ctx: commands.Context):
        """Send a preview of the welcome message to the welcome channel."""
        await self._send_welcome(ctx.author)
        try:
            await ctx.message.delete()
        except Exception:
            pass

    async def _send_welcome(self, member: discord.Member):
        channel = member.guild.get_channel(WELCOME_POST_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            return

        welcome_channel = member.guild.get_channel(WELCOME_INFO_CHANNEL_ID)
        verify_channel = member.guild.get_channel(VERIFY_CHANNEL_ID)

        welcome_ref = welcome_channel.mention if welcome_channel else f"<#{WELCOME_INFO_CHANNEL_ID}>"
        verify_ref = verify_channel.mention if verify_channel else f"<#{VERIFY_CHANNEL_ID}>"

        description = (
            f"Welcome to **{SERVER_NAME}**, {member.mention} 👋\n\n"
            f"Before you can take part in the community, please complete the steps below:\n\n"
            f"**1.** Visit {welcome_ref} to read the main community information.\n"
            f"**2.** Head to {verify_ref} and verify your account.\n"
            f"**3.** After verification, you can access the rest of the server and community channels.\n\n"
            f"⚠️ **Verification is required before participating in the community.**"
        )

        embed = discord.Embed(
            title="Welcome to Different Meets",
            description=description,
            color=discord.Color.blurple(),
        )
        embed.set_footer(text="Different Meets • Verify first, then enjoy the community")

        file = None
        if EMBLEM_FILE_PATH.exists():
            file = discord.File(EMBLEM_FILE_PATH, filename="diff_welcome_emblem.png")
            embed.set_image(url="attachment://diff_welcome_emblem.png")

        view = WelcomeLinksView()
        try:
            if file:
                await channel.send(content=member.mention, embed=embed, file=file, view=view)
            else:
                await channel.send(content=member.mention, embed=embed, view=view)
        except Exception as e:
            print(f"[DiffWelcomeJoinSystem] Failed to send welcome message: {e}")


# =========================================================
# SETUP
# =========================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(DiffWelcomeJoinSystem(bot))
