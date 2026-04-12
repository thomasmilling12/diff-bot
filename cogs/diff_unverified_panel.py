from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import Optional

import discord
from discord.ext import commands

# =========================
# CONFIG
# =========================
TARGET_CHANNEL_ID  = 1486058055991824655
UNVERIFIED_ROLE_ID = 1486011550916411512
VERIFIED_ROLE_ID   = 1141424243616256032
RULES_CHANNEL_ID   = 1047161846257438743
JOIN_MEETS_CHANNEL = 1277084633858576406

PING_COOLDOWN_SECS = 600  # 10 minutes between pings

DATA_FILE = os.path.join("diff_data", "unverified_panel.json")

DIFF_LOGO_URL = (
    "https://media.discordapp.net/attachments/1107375326625005719/"
    "1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm="
    "2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
    "&=&format=webp&quality=lossless&width=1376&height=917"
)
EMBED_COLOR = 0xED4245
FOOTER_TEXT = "DIFF Verification System"
PANEL_TAG   = "DIFF_UNVERIFIED_PANEL"

STAFF_ROLE_IDS = {850391095845584937, 850391378559238235, 990011447193006101, 1055823929358430248}

# In-memory cooldown: guild_id → last ping timestamp
_ping_cooldowns: dict[int, float] = {}


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


def _is_staff(member: discord.Member) -> bool:
    return (
        any(r.id in STAFF_ROLE_IDS for r in member.roles)
        or member.guild_permissions.manage_guild
        or member.guild_permissions.administrator
    )


def _staff_label(member: discord.Member) -> str:
    for r in reversed(member.roles):
        if r.id in STAFF_ROLE_IDS:
            return f" ({r.name})"
    return ""


def _unverified_members(guild: discord.Guild) -> list[discord.Member]:
    role = guild.get_role(UNVERIFIED_ROLE_ID)
    if role is None:
        return []
    return sorted(role.members, key=lambda m: m.joined_at or datetime.min.replace(tzinfo=timezone.utc))


# =========================
# BUTTONS  (subclass style — works after restart on Pi)
# =========================
class PingButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Ping Unverified Role",
            style=discord.ButtonStyle.danger,
            emoji="📣",
            custom_id="diff_unverified_ping_v2",
        )

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("Server only.", ephemeral=True)

        member = interaction.user
        if not isinstance(member, discord.Member) or not _is_staff(member):
            return await interaction.response.send_message(
                "You need staff permissions to use this.", ephemeral=True
            )

        # Cooldown check
        guild_id = interaction.guild.id
        now = time.monotonic()
        last = _ping_cooldowns.get(guild_id, 0)
        remaining = PING_COOLDOWN_SECS - (now - last)
        if remaining > 0:
            mins = int(remaining // 60)
            secs = int(remaining % 60)
            wait = f"{mins}m {secs}s" if mins else f"{secs}s"
            return await interaction.response.send_message(
                f"⏳ Cooldown active — you can ping again in **{wait}**.", ephemeral=True
            )

        role = interaction.guild.get_role(UNVERIFIED_ROLE_ID)
        if role is None:
            return await interaction.response.send_message("Unverified role not found.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        _ping_cooldowns[guild_id] = now

        label = _staff_label(member)
        count = len(_unverified_members(interaction.guild))

        ping_embed = discord.Embed(
            title="📌 Verification Reminder",
            description=(
                f"You're seeing this because you haven't verified yet.\n"
                f"Follow the steps below to unlock full access to DIFF.\n\n"
                f"📜 **Step 1** — Read the rules in <#{RULES_CHANNEL_ID}>\n"
                f"✅ **Step 2** — Complete verification and click the button\n"
                f"🎮 **Step 3** — Head to <#{JOIN_MEETS_CHANNEL}> to join meets"
            ),
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc),
        )
        ping_embed.set_thumbnail(url=DIFF_LOGO_URL)
        ping_embed.set_footer(
            text=f"Sent by {member.display_name}{label}  •  {FOOTER_TEXT}"
        )

        channel = interaction.channel
        await channel.send(
            content=role.mention,
            embed=ping_embed,
            allowed_mentions=discord.AllowedMentions(roles=True),
        )

        # DM each unverified member
        dm_ok = 0
        dm_fail = 0
        for m in role.members:
            try:
                dm_embed = discord.Embed(
                    title="📌 DIFF — Verification Reminder",
                    description=(
                        f"Hey {m.display_name}! A staff member has sent a verification reminder.\n\n"
                        f"📜 **Step 1** — Read the rules in <#{RULES_CHANNEL_ID}>\n"
                        f"✅ **Step 2** — Complete verification\n"
                        f"🎮 **Step 3** — Head to <#{JOIN_MEETS_CHANNEL}> to join meets\n\n"
                        f"Complete this to unlock full access to **{interaction.guild.name}**!"
                    ),
                    color=discord.Color.red(),
                    timestamp=datetime.now(timezone.utc),
                )
                dm_embed.set_thumbnail(url=DIFF_LOGO_URL)
                dm_embed.set_footer(text=FOOTER_TEXT)
                await m.send(embed=dm_embed)
                dm_ok += 1
            except Exception:
                dm_fail += 1

        dm_note = f"\n📬 DMs sent: **{dm_ok}** delivered, **{dm_fail}** failed (DMs closed)." if (dm_ok + dm_fail) else ""
        await interaction.followup.send(
            f"✅ Pinged **{count}** unverified member(s).{dm_note}",
            ephemeral=True,
        )


class ListUnverifiedButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="List Unverified Members",
            style=discord.ButtonStyle.secondary,
            emoji="👥",
            custom_id="diff_unverified_list_v2",
        )

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("Server only.", ephemeral=True)

        member = interaction.user
        if not isinstance(member, discord.Member) or not _is_staff(member):
            return await interaction.response.send_message("Staff only.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        members = _unverified_members(interaction.guild)

        if not members:
            return await interaction.followup.send(
                "✅ No unverified members right now!", ephemeral=True
            )

        now = datetime.now(timezone.utc)

        # Bucket by how long they've been unverified
        today = week = month = older = 0
        for m in members:
            days = (now - m.joined_at).days if m.joined_at else 999
            if days == 0:
                today += 1
            elif days <= 7:
                week += 1
            elif days <= 30:
                month += 1
            else:
                older += 1

        # 10 most recently joined (most actionable)
        recent = members[-10:][::-1]  # newest first
        recent_lines = []
        for m in recent:
            days = (now - m.joined_at).days if m.joined_at else None
            duration = f"{days}d ago" if days is not None and days > 0 else "today"
            recent_lines.append(f"• [{m.display_name}](https://discord.com/users/{m.id}) — joined **{duration}**")

        embed = discord.Embed(
            title=f"👥 Unverified Members — {len(members)} total",
            color=EMBED_COLOR,
            timestamp=now,
        )
        embed.add_field(
            name="📊 Breakdown",
            value=(
                f"🟢 Joined today: **{today}**\n"
                f"🟡 Joined this week: **{week}**\n"
                f"🟠 Joined this month: **{month}**\n"
                f"🔴 Older than 30 days: **{older}**"
            ),
            inline=False,
        )
        embed.add_field(
            name="🕐 10 Most Recently Joined",
            value="\n".join(recent_lines) if recent_lines else "None",
            inline=False,
        )
        embed.set_footer(text=FOOTER_TEXT)
        await interaction.followup.send(embed=embed, ephemeral=True)


# =========================
# VIEW
# =========================
class UnverifiedPingView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(PingButton())
        self.add_item(ListUnverifiedButton())


# =========================
# COG
# =========================
class UnverifiedPanelCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._view = UnverifiedPingView()
        bot.add_view(self._view)

    def _build_embed(self, guild: Optional[discord.Guild] = None) -> discord.Embed:
        count = len(_unverified_members(guild)) if guild else 0
        count_str = f"**{count}** unverified member{'s' if count != 1 else ''} right now." if guild else ""

        embed = discord.Embed(
            title="📍 DIFF Unverified Members",
            description=(
                "If you're seeing this channel, you haven't completed server verification yet.\n"
                "Follow the steps below to unlock full access to DIFF.\n\n"
                + (f"👥 There are currently {count_str}" if count_str else "")
            ),
            color=EMBED_COLOR,
        )
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.add_field(
            name="✅ How to Get Verified",
            value=(
                f"• Go to <#{RULES_CHANNEL_ID}> and read the rules\n"
                f"• Click the verification button at the bottom of that channel\n"
                f"• Once complete, your access will be unlocked automatically"
            ),
            inline=False,
        )
        embed.add_field(
            name="🎮 After Verifying",
            value=(
                f"• Head to <#{JOIN_MEETS_CHANNEL}> to see how to join meets\n"
                f"• Explore the rest of the server\n"
                f"• Follow any announcements from staff"
            ),
            inline=False,
        )
        embed.add_field(
            name="🔔 Staff Actions",
            value=(
                "**Ping Unverified Role** — sends a reminder ping in this channel and DMs all unverified members *(10 min cooldown)*\n"
                "**List Unverified Members** — shows a private list of who still needs to verify"
            ),
            inline=False,
        )
        embed.set_footer(text=f"{FOOTER_TEXT}  |  {PANEL_TAG}")
        embed.timestamp = datetime.now(timezone.utc)
        return embed

    async def _get_channel(self) -> Optional[discord.TextChannel]:
        ch = self.bot.get_channel(TARGET_CHANNEL_ID)
        if ch is None:
            try:
                ch = await self.bot.fetch_channel(TARGET_CHANNEL_ID)
            except Exception:
                return None
        return ch if isinstance(ch, discord.TextChannel) else None

    async def ensure_panel(self, guild: Optional[discord.Guild] = None) -> None:
        channel = await self._get_channel()
        if channel is None:
            print(f"[UnverifiedPanel] Channel not found: {TARGET_CHANNEL_ID}")
            return

        embed = self._build_embed(guild or channel.guild)
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

        # Clean up stale duplicates
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

    @commands.Cog.listener()
    async def on_ready(self):
        print("[UnverifiedPanel] Cog ready.")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Refresh the panel count when someone joins."""
        await self.ensure_panel(member.guild)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Refresh the panel when someone gains/loses the unverified role."""
        before_ids = {r.id for r in before.roles}
        after_ids  = {r.id for r in after.roles}
        if UNVERIFIED_ROLE_ID in (before_ids ^ after_ids):
            await self.ensure_panel(after.guild)

    @commands.command(name="refresh_unverified_panel")
    @commands.has_permissions(manage_guild=True)
    async def refresh_cmd(self, ctx: commands.Context):
        """Force-refresh the unverified panel."""
        await self.ensure_panel(ctx.guild)
        await ctx.send("Unverified panel refreshed.", delete_after=10)


# =========================
# SETUP
# =========================
async def setup(bot: commands.Bot):
    await bot.add_cog(UnverifiedPanelCog(bot))
