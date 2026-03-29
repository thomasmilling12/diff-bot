from __future__ import annotations

import json
import os
from typing import Optional

import discord
from discord.ext import commands

# =========================================================
# CONFIG
# =========================================================
TARGET_CHANNEL_ID = 1486228191243669646
HOST_ROLE_ID      = 1055823929358430248

DATA_FILE = os.path.join("diff_data", "host_team_panel.json")

DIFF_LOGO_URL = (
    "https://media.discordapp.net/attachments/1107375326625005719/"
    "1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm="
    "2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
    "&=&format=webp&quality=lossless&width=1376&height=917"
)

PANEL_TAG = "DIFF_HOST_TEAM_PANEL"

CHANNEL_LINKS = {
    "📅 Schedule / Planning":   "https://discord.com/channels/850386896509337710/1089579004517953546",
    "📍 Meet Coordination":     "https://discord.com/channels/850386896509337710/1091157191895023626",
    "🚫 Blacklist / Reports":   "https://discord.com/channels/850386896509337710/1057016810261712938",
    "📊 Staff Logs":            "https://discord.com/channels/850386896509337710/1485265848099799163",
    "🛠️ Host Tools":            "https://discord.com/channels/850386896509337710/1485840926612918383",
    "💬 Host Team Chat":        "https://discord.com/channels/850386896509337710/1485830232270307410",
}


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


# =========================================================
# VIEW
# =========================================================
class HostTeamPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for label, link in CHANNEL_LINKS.items():
            self.add_item(discord.ui.Button(
                label=label,
                url=link,
                style=discord.ButtonStyle.link,
            ))


# =========================================================
# COG
# =========================================================
class HostTeamPanelCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._view = HostTeamPanelView()
        bot.add_view(self._view)

    # ------------------------------------------------------------------
    def _build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🏁 DIFF HOST TEAM CHAT",
            description=(
                "**Host Coordination Hub**\n\n"
                "Use this space to communicate, plan, and execute meets.\n\n"
                "🚨 **IMPORTANT:**\n"
                "• Stay active and communicate clearly\n"
                "• Coordinate locations, themes, and timing\n"
                "• Check the blacklist before hosting\n"
                "• Keep everything organized and professional\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "**Quick Access Tools Below** 👇"
            ),
            color=discord.Color.gold(),
        )
        embed.add_field(
            name="📋 Staff Commands",
            value="`!refresh_host_panel` — Refresh this panel",
            inline=False,
        )
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.set_footer(text=f"DIFF Meets • Host System • {PANEL_TAG}")
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
    async def ensure_panel(self) -> None:
        channel = await self._get_channel()
        if channel is None:
            print(f"[HostTeamPanel] Channel not found: {TARGET_CHANNEL_ID}")
            return

        embed = self._build_embed()
        saved_id = _get_msg_id()

        if saved_id:
            try:
                msg = await channel.fetch_message(saved_id)
                await msg.edit(embed=embed, view=self._view)
                print("[HostTeamPanel] Panel refreshed.")
                return
            except discord.NotFound:
                pass
            except Exception as e:
                print(f"[HostTeamPanel] Edit failed: {e}")

        # Remove stale duplicates
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

        # Post fresh panel and ping Host role
        try:
            role = channel.guild.get_role(HOST_ROLE_ID)
            content = role.mention if role else None
            new_msg = await channel.send(
                content=content,
                embed=embed,
                view=self._view,
                allowed_mentions=discord.AllowedMentions(roles=True),
            )
            _set_msg_id(new_msg.id)
            print(f"[HostTeamPanel] Panel posted: {new_msg.id}")
        except Exception as e:
            print(f"[HostTeamPanel] Failed to post panel: {e}")

    # ------------------------------------------------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        print("[HostTeamPanel] Cog ready. (panel managed by UnifiedHostTeamView)")

    @commands.command(name="refresh_host_panel")
    @commands.has_permissions(manage_guild=True)
    async def refresh_cmd(self, ctx: commands.Context):
        """Force-refresh the Host Team panel."""
        await self.ensure_panel()
        await ctx.send("Host Team panel refreshed.", delete_after=10)


# =========================================================
# SETUP
# =========================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(HostTeamPanelCog(bot))
