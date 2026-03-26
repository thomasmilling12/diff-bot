from __future__ import annotations

import json
import os
from typing import Optional

import discord
from discord.ext import commands

# =========================================================
# CONFIG
# =========================================================
TARGET_CHANNEL_ID = 1485861257708834836

STAFF_ROLE_IDS: set[int] = {
    850391095845584937,   # Leader
    850391378559238235,   # Co-Leader
    990011447193006101,   # Manager
}

PANEL_TAG  = "DIFF_UPCOMING_MEET_PANEL_V1"
DATA_DIR   = "diff_data"
PANEL_FILE = os.path.join(DATA_DIR, "upcoming_meet_panel.json")

DIFF_LOGO_URL = (
    "https://media.discordapp.net/attachments/1107375326625005719/"
    "1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm="
    "2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
    "&=&format=webp&quality=lossless&width=1376&height=917"
)

BUTTONS = [
    ("🏁 Official Meet Posts", "https://discord.com/channels/850386896509337710/1485870611069796374"),
    ("⚡ Pop-Up Meets",        "https://discord.com/channels/850386896509337710/1484768466023223418"),
    ("💬 Meet Chat",           "https://discord.com/channels/850386896509337710/1195953265377021952"),
    ("📸 Meet Media",          "https://discord.com/channels/850386896509337710/1266933655486332999"),
]


# =========================================================
# HELPERS
# =========================================================
def _load_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def _get_panel_msg_id() -> Optional[int]:
    v = _load_json(PANEL_FILE).get("panel_message_id")
    return int(v) if v else None


def _save_panel_msg_id(msg_id: int) -> None:
    data = _load_json(PANEL_FILE)
    data["panel_message_id"] = msg_id
    _save_json(PANEL_FILE, data)


def _is_staff(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    return any(r.id in STAFF_ROLE_IDS for r in member.roles)


# =========================================================
# VIEW + EMBED
# =========================================================
class UpcomingMeetPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for label, url in BUTTONS:
            self.add_item(discord.ui.Button(
                label=label, url=url, style=discord.ButtonStyle.link
            ))


def _panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title="📅 DIFF Upcoming Meet Hub",
        color=discord.Color.gold(),
        description=(
            "**What this channel is used for**\n\n"
            "This channel keeps members updated on **upcoming DIFF meets** before they begin.\n\n"
            "You can use this channel to:\n"
            "• Check what meet is coming up next\n"
            "• See official meet posts and timing\n"
            "• Stay ready for future public or pop-up meet drops\n"
            "• Know where to go once a meet announcement is live\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "**Quick Access Buttons Below**\n"
            "Use the buttons to jump straight to important meet channels.\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        ),
    )
    embed.set_thumbnail(url=DIFF_LOGO_URL)
    embed.set_footer(text=PANEL_TAG)
    return embed


# =========================================================
# COG
# =========================================================
class UpcomingMeetPanelCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot  = bot
        self.view = UpcomingMeetPanelView()
        self.bot.add_view(self.view)

    async def ensure_panel(self) -> None:
        channel = self.bot.get_channel(TARGET_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            try:
                channel = await self.bot.fetch_channel(TARGET_CHANNEL_ID)
            except Exception:
                channel = None
        if not isinstance(channel, discord.TextChannel):
            print(f"[UpcomingMeetPanel] Channel {TARGET_CHANNEL_ID} not found.")
            return

        embed    = _panel_embed()
        saved_id = _get_panel_msg_id()

        if saved_id:
            try:
                msg = await channel.fetch_message(saved_id)
                await msg.edit(embed=embed, view=self.view)
                print("[UpcomingMeetPanel] Panel refreshed.")
                return
            except discord.NotFound:
                pass
            except Exception as e:
                print(f"[UpcomingMeetPanel] Edit failed: {e}")

        # Fallback: remove stale panel by tag
        try:
            async for msg in channel.history(limit=50):
                if (
                    msg.author == self.bot.user
                    and msg.embeds
                    and msg.embeds[0].footer.text == PANEL_TAG
                ):
                    try:
                        await msg.delete()
                    except Exception:
                        pass
        except Exception:
            pass

        try:
            new_msg = await channel.send(embed=embed, view=self.view)
            _save_panel_msg_id(new_msg.id)
            print(f"[UpcomingMeetPanel] Panel posted: {new_msg.id}")
        except Exception as e:
            print(f"[UpcomingMeetPanel] Post failed: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.ensure_panel()
        print("[UpcomingMeetPanel] Cog ready.")

    @commands.command(name="refresh_upcoming_meet_panel")
    @commands.has_permissions(manage_guild=True)
    async def cmd_refresh(self, ctx: commands.Context):
        await self.ensure_panel()
        await ctx.send("Upcoming meet panel refreshed.", delete_after=8)


# =========================================================
# SETUP
# =========================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(UpcomingMeetPanelCog(bot))
