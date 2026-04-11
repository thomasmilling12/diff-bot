from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Optional

import discord
from discord.ext import commands

# =========================
# CONFIG
# =========================
TARGET_CHANNEL_ID  = 1486058055991824655
UNVERIFIED_ROLE_ID = 1486011550916411512

DATA_FILE = os.path.join("diff_data", "unverified_panel.json")

DIFF_LOGO_URL = (
    "https://media.discordapp.net/attachments/1107375326625005719/"
    "1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm="
    "2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
    "&=&format=webp&quality=lossless&width=1376&height=917"
)
EMBED_COLOR = 0x2B2D31
FOOTER_TEXT = "DIFF Verification System"
PANEL_TAG   = "DIFF_UNVERIFIED_PANEL"


# =========================
# STORAGE HELPERS
# =========================
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


def _set_msg_id(message_id: int) -> None:
    d = _load()
    d["panel_message_id"] = message_id
    _save(d)


# =========================
# VIEW
# =========================
class UnverifiedPingView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Ping Unverified Role",
        style=discord.ButtonStyle.danger,
        emoji="📣",
        custom_id="diff_unverified_ping_button_v1",
    )
    async def ping_unverified(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if not interaction.guild:
            return await interaction.response.send_message(
                "This button can only be used in a server.", ephemeral=True
            )

        member = interaction.user
        if not isinstance(member, discord.Member):
            return await interaction.response.send_message(
                "Could not verify your staff permissions.", ephemeral=True
            )

        if not (
            member.guild_permissions.manage_guild
            or member.guild_permissions.manage_messages
            or member.guild_permissions.administrator
        ):
            return await interaction.response.send_message(
                "You need staff permissions to use this button.", ephemeral=True
            )

        role = interaction.guild.get_role(UNVERIFIED_ROLE_ID)
        if role is None:
            return await interaction.response.send_message(
                "Could not find the Unverified role.", ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        channel = interaction.channel
        if not isinstance(channel, discord.abc.Messageable):
            return await interaction.followup.send(
                "I couldn't send the ping in this channel.", ephemeral=True
            )

        STAFF_ROLE_IDS = {850391095845584937, 850391378559238235, 990011447193006101, 1055823929358430248}
        role_label = ""
        for r in reversed(member.roles):
            if r.id in STAFF_ROLE_IDS:
                role_label = f" ({r.name})"
                break

        ping_embed = discord.Embed(
            title="📌 Verification Reminder",
            description=(
                "Please complete the server verification process to unlock full access.\n\n"
                "• Read the **rules** and **verification** channels\n"
                "• Follow the steps posted by staff\n"
                "• Your access will be unlocked once verification is complete"
            ),
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc),
        )
        ping_embed.set_thumbnail(url=DIFF_LOGO_URL)
        ping_embed.set_footer(text=f"Sent by {member.display_name}{role_label}  •  DIFF Verification System")

        await channel.send(
            content=role.mention,
            embed=ping_embed,
            allowed_mentions=discord.AllowedMentions(roles=True),
        )

        await interaction.followup.send("Unverified role ping sent.", ephemeral=True)


# =========================
# COG
# =========================
class UnverifiedPanelCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._view = UnverifiedPingView()
        bot.add_view(self._view)

    # ------------------------------------------------------------------
    def _build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="📍 DIFF Unverified Members",
            description=(
                "If you're seeing this channel, you haven't completed server verification yet.\n"
                "Follow the steps below to unlock full access to DIFF."
            ),
            color=0xED4245,
        )
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.add_field(
            name="✅ How to Get Verified",
            value=(
                "• Read the **rules** and **verification** channels\n"
                "• Follow any steps posted by staff\n"
                "• Once complete, your access will be unlocked"
            ),
            inline=False,
        )
        embed.add_field(
            name="⚙️ What Happens When Staff Ping",
            value=(
                "• The **Unverified** role is pinged\n"
                "• A reminder is posted here\n"
                "• Members are directed to finish verification"
            ),
            inline=False,
        )
        embed.add_field(
            name="🔔 Staff Action",
            value="Press the button below to send a verification reminder to all unverified members.",
            inline=False,
        )
        embed.set_footer(text=f"DIFF Verification System  |  {PANEL_TAG}")
        embed.timestamp = datetime.now(timezone.utc)
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
            print(f"[UnverifiedPanel] Channel not found: {TARGET_CHANNEL_ID}")
            return

        embed = self._build_embed()
        saved_id = _get_msg_id()

        if saved_id:
            try:
                msg = await channel.fetch_message(saved_id)
                await msg.edit(embed=embed, view=self._view)
                print("[UnverifiedPanel] Panel refreshed.")
                return
            except discord.NotFound:
                pass
            except Exception as e:
                print(f"[UnverifiedPanel] Edit failed: {e}")

        # Delete any stale duplicates
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

        try:
            new_msg = await channel.send(embed=embed, view=self._view)
            _set_msg_id(new_msg.id)
            print(f"[UnverifiedPanel] Panel posted: {new_msg.id}")
        except Exception as e:
            print(f"[UnverifiedPanel] Failed to post panel: {e}")

    # ------------------------------------------------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        await self.ensure_panel()
        print("[UnverifiedPanel] Cog ready.")

    @commands.command(name="refresh_unverified_panel")
    @commands.has_permissions(manage_guild=True)
    async def refresh_cmd(self, ctx: commands.Context):
        """Force-refresh the unverified panel."""
        await self.ensure_panel()
        await ctx.send("Unverified panel refreshed.", delete_after=10)


# =========================
# SETUP
# =========================
async def setup(bot: commands.Bot):
    await bot.add_cog(UnverifiedPanelCog(bot))
