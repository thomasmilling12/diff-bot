from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta
from typing import Optional

import discord
from discord.ext import commands

# =========================================================
# CONFIG
# =========================================================
MOD_HUB_CHANNEL_ID     = 1486598266211664003   # panel lives here
MOD_LOG_CHANNEL_ID     = 1486598266211664003   # mod action logs
WARNING_LOG_CHANNEL_ID = 1486599502834958366   # warn-specific logs

STAFF_ROLE_IDS: set[int] = {
    850391095845584937,   # Leader
    850391378559238235,   # Co-Leader
    990011447193006101,   # Manager
}

PANEL_TAG  = "DIFF_MOD_HUB_PANEL_V1"
DATA_DIR   = "diff_data"
PANEL_FILE = os.path.join(DATA_DIR, "mod_hub_panel.json")
WARN_FILE  = os.path.join(DATA_DIR, "mod_warnings.json")
CASE_FILE  = os.path.join(DATA_DIR, "mod_cases.json")

DIFF_LOGO_URL = (
    "https://media.discordapp.net/attachments/1107375326625005719/"
    "1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm="
    "2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
    "&=&format=webp&quality=lossless&width=1376&height=917"
)


# =========================================================
# FILE / DATA HELPERS
# =========================================================
def _load_json(path: str, default=None):
    if default is None:
        default = {}
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save_json(path: str, data) -> None:
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


def _next_case() -> int:
    data = _load_json(CASE_FILE, {"last_case": 0})
    data["last_case"] = data.get("last_case", 0) + 1
    _save_json(CASE_FILE, data)
    return data["last_case"]


def _add_warning(guild_id: int, user_id: int, entry: dict) -> None:
    data = _load_json(WARN_FILE)
    gk, uk = str(guild_id), str(user_id)
    data.setdefault(gk, {}).setdefault(uk, []).append(entry)
    _save_json(WARN_FILE, data)


def _warn_count(guild_id: int, user_id: int) -> int:
    data = _load_json(WARN_FILE)
    return len(data.get(str(guild_id), {}).get(str(user_id), []))


def _is_staff(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    return any(r.id in STAFF_ROLE_IDS for r in member.roles)


# =========================================================
# EMBED BUILDERS
# =========================================================
def _panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🛡️ DIFF Moderation Hub",
        description=(
            "Staff moderation control centre for **Different Meets**.\n"
            "Use the buttons below to take action on members — all actions are logged automatically."
        ),
        color=0xED4245,
    )
    embed.set_thumbnail(url=DIFF_LOGO_URL)
    embed.add_field(
        name="⚠️ Available Actions",
        value=(
            "› **Warn Member** — issue an official warning\n"
            "› **Timeout Member** — temporarily restrict access\n"
            "› **Kick Member** — remove from the server\n"
            "› **Ban Member** — permanently remove from the server\n"
            "› **Check Warnings** — view a member's warning history"
        ),
        inline=False,
    )
    embed.add_field(
        name="📌 Notes",
        value=(
            "All actions require a target user and reason.\n"
            "Every action is logged to #mod-logs with full details."
        ),
        inline=False,
    )
    embed.set_footer(text="Different Meets • Moderation Hub  |  Staff-only actions")
    return embed


def _action_log_embed(
    action: str,
    target: discord.Member | discord.User,
    moderator: discord.Member,
    reason: str,
    case_id: int,
    extra: str = "",
) -> discord.Embed:
    embed = discord.Embed(
        title=f"🛡️ Moderation Action • {action}",
        color=discord.Color.red(),
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name="User",      value=f"{target.mention}\n`{target.id}`",     inline=True)
    embed.add_field(name="Moderator", value=f"{moderator.mention}\n`{moderator.id}`", inline=True)
    embed.add_field(name="Case",      value=f"`#{case_id}`",                         inline=True)
    embed.add_field(name="Reason",    value=reason or "No reason provided.",          inline=False)
    if extra:
        embed.add_field(name="Extra", value=extra, inline=False)
    embed.set_thumbnail(url=DIFF_LOGO_URL)
    embed.set_footer(text="DIFF Meets • Moderation Logs")
    return embed


# =========================================================
# MODALS
# =========================================================
class WarnModal(discord.ui.Modal, title="Warn Member"):
    reason = discord.ui.TextInput(
        label="Warning Reason",
        placeholder="Enter the reason for the warning…",
        style=discord.TextStyle.paragraph, max_length=500, required=True,
    )

    def __init__(self, cog: "ModHubCog", member: discord.Member):
        super().__init__()
        self.cog    = cog
        self.member = member

    async def on_submit(self, interaction: discord.Interaction) -> None:
        mod = interaction.user
        if not isinstance(mod, discord.Member) or not _is_staff(mod):
            return await interaction.response.send_message(
                "Only staff can use this panel.", ephemeral=True
            )

        case_id    = _next_case()
        reason_txt = str(self.reason).strip()
        _add_warning(interaction.guild.id, self.member.id, {
            "case_id":      case_id,
            "reason":       reason_txt,
            "moderator_id": mod.id,
            "timestamp":    datetime.now(timezone.utc).isoformat(),
        })
        total = _warn_count(interaction.guild.id, self.member.id)

        warn_embed = discord.Embed(
            title="⚠️ Member Warned",
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc),
        )
        warn_embed.add_field(name="User",           value=f"{self.member.mention}\n`{self.member.id}`", inline=True)
        warn_embed.add_field(name="Moderator",      value=mod.mention,    inline=True)
        warn_embed.add_field(name="Case",           value=f"`#{case_id}`", inline=True)
        warn_embed.add_field(name="Reason",         value=reason_txt,      inline=False)
        warn_embed.add_field(name="Total Warnings", value=str(total),      inline=False)
        warn_embed.set_thumbnail(url=DIFF_LOGO_URL)
        warn_embed.set_footer(text="DIFF Meets • Warning System")

        log_embed = _action_log_embed(
            "Warn", self.member, mod, reason_txt, case_id,
            extra=f"Total warnings: {total}",
        )

        await self.cog.send_to(WARNING_LOG_CHANNEL_ID, embed=warn_embed)
        await self.cog.send_to(MOD_LOG_CHANNEL_ID, embed=log_embed)

        try:
            dm = discord.Embed(
                title="⚠️ You Have Been Warned",
                description=(
                    f"You were warned in **{interaction.guild.name}**.\n\n"
                    f"**Reason:** {reason_txt}\n"
                    f"**Case:** #{case_id}\n"
                    f"**Total Warnings:** {total}"
                ),
                color=discord.Color.orange(),
            )
            dm.set_thumbnail(url=DIFF_LOGO_URL)
            dm.set_footer(text="DIFF Meets • Moderation")
            await self.member.send(embed=dm)
        except Exception:
            pass

        await interaction.response.send_message(
            f"Warned {self.member.mention}. Case `#{case_id}` — total warnings: **{total}**.",
            ephemeral=True,
        )


class TimeoutModal(discord.ui.Modal, title="Timeout Member"):
    duration_input = discord.ui.TextInput(
        label="Duration (minutes)",
        placeholder="Example: 60",
        max_length=10, required=True,
    )
    reason = discord.ui.TextInput(
        label="Timeout Reason",
        placeholder="Enter the reason for the timeout…",
        style=discord.TextStyle.paragraph, max_length=500, required=True,
    )

    def __init__(self, cog: "ModHubCog", member: discord.Member):
        super().__init__()
        self.cog    = cog
        self.member = member

    async def on_submit(self, interaction: discord.Interaction) -> None:
        mod = interaction.user
        if not isinstance(mod, discord.Member) or not _is_staff(mod):
            return await interaction.response.send_message(
                "Only staff can use this panel.", ephemeral=True
            )

        try:
            minutes = int(str(self.duration_input).strip())
            if minutes <= 0:
                raise ValueError
        except ValueError:
            return await interaction.response.send_message(
                "Duration must be a whole number greater than 0.", ephemeral=True
            )

        case_id    = _next_case()
        reason_txt = str(self.reason).strip()
        until      = datetime.now(timezone.utc) + timedelta(minutes=minutes)

        try:
            await self.member.timeout(until, reason=reason_txt)
        except Exception as e:
            return await interaction.response.send_message(
                f"Failed to timeout member: {e}", ephemeral=True
            )

        log_embed = _action_log_embed(
            "Timeout", self.member, mod, reason_txt, case_id,
            extra=f"Duration: {minutes} minute(s)",
        )
        await self.cog.send_to(MOD_LOG_CHANNEL_ID, embed=log_embed)

        try:
            dm = discord.Embed(
                title="⏳ You Have Been Timed Out",
                description=(
                    f"You were timed out in **{interaction.guild.name}**.\n\n"
                    f"**Duration:** {minutes} minute(s)\n"
                    f"**Reason:** {reason_txt}\n"
                    f"**Case:** #{case_id}"
                ),
                color=discord.Color.red(),
            )
            dm.set_thumbnail(url=DIFF_LOGO_URL)
            dm.set_footer(text="DIFF Meets • Moderation")
            await self.member.send(embed=dm)
        except Exception:
            pass

        await interaction.response.send_message(
            f"Timed out {self.member.mention} for {minutes} minute(s). Case `#{case_id}`.",
            ephemeral=True,
        )


class KickModal(discord.ui.Modal, title="Kick Member"):
    reason = discord.ui.TextInput(
        label="Kick Reason",
        placeholder="Enter the reason for the kick…",
        style=discord.TextStyle.paragraph, max_length=500, required=True,
    )

    def __init__(self, cog: "ModHubCog", member: discord.Member):
        super().__init__()
        self.cog    = cog
        self.member = member

    async def on_submit(self, interaction: discord.Interaction) -> None:
        mod = interaction.user
        if not isinstance(mod, discord.Member) or not _is_staff(mod):
            return await interaction.response.send_message(
                "Only staff can use this panel.", ephemeral=True
            )

        case_id    = _next_case()
        reason_txt = str(self.reason).strip()

        try:
            dm = discord.Embed(
                title="👢 You Have Been Kicked",
                description=(
                    f"You were kicked from **{interaction.guild.name}**.\n\n"
                    f"**Reason:** {reason_txt}\n"
                    f"**Case:** #{case_id}"
                ),
                color=discord.Color.red(),
            )
            dm.set_thumbnail(url=DIFF_LOGO_URL)
            dm.set_footer(text="DIFF Meets • Moderation")
            await self.member.send(embed=dm)
        except Exception:
            pass

        try:
            await self.member.kick(reason=reason_txt)
        except Exception as e:
            return await interaction.response.send_message(
                f"Failed to kick member: {e}", ephemeral=True
            )

        log_embed = _action_log_embed("Kick", self.member, mod, reason_txt, case_id)
        await self.cog.send_to(MOD_LOG_CHANNEL_ID, embed=log_embed)

        await interaction.response.send_message(
            f"Kicked `{self.member}`. Case `#{case_id}`.", ephemeral=True
        )


class BanModal(discord.ui.Modal, title="Ban Member"):
    reason = discord.ui.TextInput(
        label="Ban Reason",
        placeholder="Enter the reason for the ban…",
        style=discord.TextStyle.paragraph, max_length=500, required=True,
    )

    def __init__(self, cog: "ModHubCog", member: discord.Member):
        super().__init__()
        self.cog    = cog
        self.member = member

    async def on_submit(self, interaction: discord.Interaction) -> None:
        mod = interaction.user
        if not isinstance(mod, discord.Member) or not _is_staff(mod):
            return await interaction.response.send_message(
                "Only staff can use this panel.", ephemeral=True
            )

        case_id    = _next_case()
        reason_txt = str(self.reason).strip()

        try:
            dm = discord.Embed(
                title="🔨 You Have Been Banned",
                description=(
                    f"You were banned from **{interaction.guild.name}**.\n\n"
                    f"**Reason:** {reason_txt}\n"
                    f"**Case:** #{case_id}"
                ),
                color=discord.Color.dark_red(),
            )
            dm.set_thumbnail(url=DIFF_LOGO_URL)
            dm.set_footer(text="DIFF Meets • Moderation")
            await self.member.send(embed=dm)
        except Exception:
            pass

        try:
            await self.member.ban(reason=reason_txt, delete_message_seconds=0)
        except Exception as e:
            return await interaction.response.send_message(
                f"Failed to ban member: {e}", ephemeral=True
            )

        log_embed = _action_log_embed("Ban", self.member, mod, reason_txt, case_id)
        await self.cog.send_to(MOD_LOG_CHANNEL_ID, embed=log_embed)

        await interaction.response.send_message(
            f"Banned `{self.member}`. Case `#{case_id}`.", ephemeral=True
        )


# =========================================================
# MEMBER-SELECT EPHEMERAL VIEWS  (not persistent)
# =========================================================
class _MemberSelect(discord.ui.UserSelect):
    def __init__(self, cog: "ModHubCog", action: str):
        super().__init__(
            placeholder=f"Select a member to {action.lower()}…",
            min_values=1, max_values=1,
        )
        self.cog    = cog
        self.action = action

    async def callback(self, interaction: discord.Interaction) -> None:
        mod = interaction.user
        if not isinstance(mod, discord.Member) or not _is_staff(mod):
            return await interaction.response.send_message(
                "Only staff can use this panel.", ephemeral=True
            )

        user = self.values[0]
        if not isinstance(user, discord.Member):
            user = interaction.guild.get_member(user.id)
        if user is None:
            return await interaction.response.send_message(
                "Could not find that member in the server.", ephemeral=True
            )

        modal_map = {
            "Warn":    WarnModal,
            "Timeout": TimeoutModal,
            "Kick":    KickModal,
            "Ban":     BanModal,
        }
        modal_cls = modal_map.get(self.action)
        if modal_cls:
            await interaction.response.send_modal(modal_cls(self.cog, user))


class _MemberSelectView(discord.ui.View):
    def __init__(self, cog: "ModHubCog", action: str):
        super().__init__(timeout=120)
        self.add_item(_MemberSelect(cog, action))


class _CheckWarningsSelect(discord.ui.UserSelect):
    def __init__(self):
        super().__init__(
            placeholder="Select a member to check warnings…",
            min_values=1, max_values=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        mod = interaction.user
        if not isinstance(mod, discord.Member) or not _is_staff(mod):
            return await interaction.response.send_message(
                "Only staff can use this panel.", ephemeral=True
            )
        user = self.values[0]
        if not isinstance(user, discord.Member):
            user = interaction.guild.get_member(user.id)
        count = _warn_count(interaction.guild.id, user.id)
        embed = discord.Embed(
            title="📋 Warning Count",
            description=f"{user.mention} currently has **{count} warning(s)**.",
            color=discord.Color.orange(),
        )
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.set_footer(text="DIFF Meets • Warning System")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class _CheckWarningsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(_CheckWarningsSelect())


# =========================================================
# MAIN HUB VIEW  (persistent)
# =========================================================
class ModHubView(discord.ui.View):
    def __init__(self, cog: "ModHubCog"):
        super().__init__(timeout=None)
        self.cog = cog

    async def _staff_check(self, interaction: discord.Interaction) -> bool:
        member = interaction.user
        if not isinstance(member, discord.Member) or not _is_staff(member):
            await interaction.response.send_message(
                "Only staff can use this panel.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Warn Member",    emoji="⚠️", style=discord.ButtonStyle.secondary,
                       custom_id="diff_mod_warn_v1")
    async def warn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._staff_check(interaction):
            return
        await interaction.response.send_message(
            "Select a member to warn:", view=_MemberSelectView(self.cog, "Warn"), ephemeral=True
        )

    @discord.ui.button(label="Timeout Member", emoji="⏳", style=discord.ButtonStyle.primary,
                       custom_id="diff_mod_timeout_v1")
    async def timeout_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._staff_check(interaction):
            return
        await interaction.response.send_message(
            "Select a member to timeout:", view=_MemberSelectView(self.cog, "Timeout"), ephemeral=True
        )

    @discord.ui.button(label="Kick Member",    emoji="👢", style=discord.ButtonStyle.danger,
                       custom_id="diff_mod_kick_v1")
    async def kick(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._staff_check(interaction):
            return
        await interaction.response.send_message(
            "Select a member to kick:", view=_MemberSelectView(self.cog, "Kick"), ephemeral=True
        )

    @discord.ui.button(label="Ban Member",     emoji="🔨", style=discord.ButtonStyle.danger,
                       custom_id="diff_mod_ban_v1")
    async def ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._staff_check(interaction):
            return
        await interaction.response.send_message(
            "Select a member to ban:", view=_MemberSelectView(self.cog, "Ban"), ephemeral=True
        )

    @discord.ui.button(label="Check Warnings", emoji="📋", style=discord.ButtonStyle.success,
                       custom_id="diff_mod_checkwarn_v1")
    async def check_warnings(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._staff_check(interaction):
            return
        await interaction.response.send_message(
            "Select a member to check:", view=_CheckWarningsView(), ephemeral=True
        )


# =========================================================
# COG
# =========================================================
class ModHubCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot  = bot
        self.view = ModHubView(self)
        self.bot.add_view(self.view)

    async def send_to(self, channel_id: int, **kwargs) -> None:
        ch = self.bot.get_channel(channel_id)
        if isinstance(ch, discord.TextChannel):
            try:
                await ch.send(**kwargs)
            except Exception:
                pass

    async def ensure_panel(self) -> None:
        channel = self.bot.get_channel(MOD_HUB_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            try:
                channel = await self.bot.fetch_channel(MOD_HUB_CHANNEL_ID)
            except Exception:
                channel = None
        if not isinstance(channel, discord.TextChannel):
            print(f"[ModHub] Channel {MOD_HUB_CHANNEL_ID} not found.")
            return

        embed    = _panel_embed()
        saved_id = _get_panel_msg_id()

        if saved_id:
            try:
                msg = await channel.fetch_message(saved_id)
                await msg.edit(embed=embed, view=self.view)
                print("[ModHub] Panel refreshed.")
                return
            except discord.NotFound:
                pass
            except Exception as e:
                print(f"[ModHub] Edit failed: {e}")

        # Fallback: remove stale by tag
        try:
            async for msg in channel.history(limit=50):
                if (
                    msg.author == self.bot.user
                    and msg.embeds
                    and msg.embeds[0].title == "🛡️ DIFF Moderation Hub"
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
            print(f"[ModHub] Panel posted: {new_msg.id}")
        except Exception as e:
            print(f"[ModHub] Post failed: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.ensure_panel()
        print("[ModHub] Cog ready.")

    @commands.command(name="refresh_mod_hub")
    @commands.has_permissions(manage_guild=True)
    async def cmd_refresh(self, ctx: commands.Context):
        await self.ensure_panel()
        await ctx.send("Moderation hub refreshed.", delete_after=8)


# =========================================================
# SETUP
# =========================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(ModHubCog(bot))
