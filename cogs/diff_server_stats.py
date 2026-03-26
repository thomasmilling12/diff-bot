from __future__ import annotations

import json
import os
from typing import Optional

import discord
from discord.ext import commands, tasks

# =========================================================
# CONFIG
# =========================================================
TARGET_CHANNEL_ID = 1485273802391814224

DATA_DIR   = "diff_data"
PANEL_FILE = os.path.join(DATA_DIR, "server_stats_panel.json")

DIFF_LOGO_URL = (
    "https://media.discordapp.net/attachments/1107375326625005719/"
    "1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm="
    "2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
    "&=&format=webp&quality=lossless&width=1376&height=917"
)


# =========================================================
# HELPERS
# =========================================================
def _load() -> dict:
    if not os.path.exists(PANEL_FILE):
        return {}
    try:
        with open(PANEL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict) -> None:
    os.makedirs(os.path.dirname(PANEL_FILE), exist_ok=True)
    with open(PANEL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def _get_msg_id(guild_id: int) -> Optional[int]:
    v = _load().get(str(guild_id), {}).get("message_id")
    return int(v) if v else None


def _set_msg_id(guild_id: int, msg_id: int) -> None:
    data = _load()
    data.setdefault(str(guild_id), {})["message_id"] = msg_id
    _save(data)


def _clear_msg_id(guild_id: int) -> None:
    data = _load()
    data.get(str(guild_id), {}).pop("message_id", None)
    _save(data)


# =========================================================
# COG
# =========================================================
class ServerStatsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._updater.start()

    def cog_unload(self):
        self._updater.cancel()

    def _build_embed(self, guild: discord.Guild) -> discord.Embed:
        members     = guild.members
        total       = guild.member_count or len(members)
        bots        = sum(1 for m in members if m.bot)
        humans      = total - bots
        online      = sum(
            1 for m in members
            if getattr(m, "status", discord.Status.offline) != discord.Status.offline
        )
        boosts      = guild.premium_subscription_count or 0
        channels    = len(guild.channels)
        roles       = max(len(guild.roles) - 1, 0)   # exclude @everyone
        owner_str   = guild.owner.mention if guild.owner else "Unknown"

        embed = discord.Embed(
            title="📊 DIFF Server Statistics",
            description="Live server stats — auto-refreshes every 5 minutes.",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="👥 Total Members", value=f"**{total:,}**",   inline=True)
        embed.add_field(name="🙋 Humans",        value=f"**{humans:,}**",  inline=True)
        embed.add_field(name="🤖 Bots",          value=f"**{bots:,}**",    inline=True)

        embed.add_field(name="🟢 Online Now",    value=f"**{online:,}**",  inline=True)
        embed.add_field(name="💎 Boosts",        value=f"**{boosts:,}**",  inline=True)
        embed.add_field(name="🎭 Roles",         value=f"**{roles:,}**",   inline=True)

        embed.add_field(name="📁 Channels",      value=f"**{channels:,}**", inline=True)
        embed.add_field(name="🆔 Server ID",     value=f"`{guild.id}`",    inline=True)
        embed.add_field(name="👑 Owner",         value=owner_str,           inline=True)

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.set_footer(
            text="DIFF Meets • Server Stats",
            icon_url=DIFF_LOGO_URL,
        )
        return embed

    async def ensure_panel(self, guild: discord.Guild) -> None:
        channel = guild.get_channel(TARGET_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            return

        embed    = self._build_embed(guild)
        saved_id = _get_msg_id(guild.id)

        if saved_id:
            try:
                msg = await channel.fetch_message(saved_id)
                await msg.edit(embed=embed, content=None)
                return
            except discord.NotFound:
                _clear_msg_id(guild.id)
            except Exception:
                return

        # Post fresh panel
        try:
            new_msg = await channel.send(embed=embed)
            _set_msg_id(guild.id, new_msg.id)
        except Exception:
            pass

    @tasks.loop(minutes=5)
    async def _updater(self):
        for guild in self.bot.guilds:
            await self.ensure_panel(guild)

    @_updater.before_loop
    async def _before_updater(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            await self.ensure_panel(guild)
        print("[ServerStats] Cog ready.")

    @commands.command(name="refresh_server_stats")
    @commands.has_permissions(manage_guild=True)
    async def cmd_refresh(self, ctx: commands.Context):
        if ctx.guild:
            await self.ensure_panel(ctx.guild)
        await ctx.send("Server stats panel refreshed.", delete_after=8)


# =========================================================
# SETUP
# =========================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(ServerStatsCog(bot))
