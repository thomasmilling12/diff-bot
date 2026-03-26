from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import discord
from discord.ext import commands

# =========================================================
# CONFIG
# =========================================================
MOD_LOG_CHANNEL_ID     = 1486598266211664003
WARNING_LOG_CHANNEL_ID = 1486599502834958366
PANEL_CHANNEL_ID       = 1486599502834958366   # panel lives in warning-logs channel

STAFF_ROLE_IDS: set[int] = {
    850391095845584937,   # Leader
    850391378559238235,   # Co-Leader
    990011447193006101,   # Manager
}

AUTO_TIMEOUT_MINS = 60

# Shared with diff_mod_hub.py so warnings from both systems count together
DATA_DIR   = "diff_data"
WARN_FILE  = os.path.join(DATA_DIR, "mod_warnings.json")
CASE_FILE  = os.path.join(DATA_DIR, "mod_cases.json")
PANEL_FILE = os.path.join(DATA_DIR, "smart_punishment_panel.json")

PANEL_TAG = "DIFF_SMART_PUNISHMENT_V1"

DIFF_LOGO_URL = (
    "https://media.discordapp.net/attachments/1107375326625005719/"
    "1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm="
    "2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
    "&=&format=webp&quality=lossless&width=1376&height=917"
)


# =========================================================
# FILE HELPERS
# =========================================================
def _load(path: str, default=None):
    if default is None:
        default = {}
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _dump(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Panel ID ──────────────────────────────────────────────
def _get_panel_id() -> Optional[int]:
    v = _load(PANEL_FILE).get("panel_message_id")
    return int(v) if v else None


def _set_panel_id(msg_id: int) -> None:
    data = _load(PANEL_FILE)
    data["panel_message_id"] = msg_id
    _dump(PANEL_FILE, data)


# ── Cases ─────────────────────────────────────────────────
def _next_case() -> int:
    data = _load(CASE_FILE, {"last_case": 0})
    data["last_case"] = data.get("last_case", 0) + 1
    _dump(CASE_FILE, data)
    return data["last_case"]


# ── Warnings ──────────────────────────────────────────────
def _add_warning(guild_id: int, user_id: int, entry: dict) -> None:
    data = _load(WARN_FILE)
    data.setdefault(str(guild_id), {}).setdefault(str(user_id), []).append(entry)
    _dump(WARN_FILE, data)


def _get_warnings(guild_id: int, user_id: int) -> list:
    return _load(WARN_FILE).get(str(guild_id), {}).get(str(user_id), [])


def _set_warnings(guild_id: int, user_id: int, warnings: list) -> None:
    data = _load(WARN_FILE)
    data.setdefault(str(guild_id), {})[str(user_id)] = warnings
    _dump(WARN_FILE, data)


# ── Staff check ───────────────────────────────────────────
def _is_staff(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    return any(r.id in STAFF_ROLE_IDS for r in member.roles)


# =========================================================
# EMBED BUILDERS
# =========================================================
def _action_embed(
    title: str,
    color: discord.Color,
    member: discord.Member | discord.User,
    moderator: discord.Member,
    case_id: int,
    reason: str,
    extra: str = "",
) -> discord.Embed:
    embed = discord.Embed(title=title, color=color, timestamp=_utcnow())
    embed.add_field(name="User",      value=f"{member.mention}\n`{member.id}`",       inline=True)
    embed.add_field(name="Moderator", value=f"{moderator.mention}\n`{moderator.id}`", inline=True)
    embed.add_field(name="Case",      value=f"`#{case_id}`",                           inline=True)
    embed.add_field(name="Reason",    value=reason or "No reason provided.",           inline=False)
    if extra:
        embed.add_field(name="Extra", value=extra, inline=False)
    embed.set_thumbnail(url=DIFF_LOGO_URL)
    embed.set_footer(text="DIFF Meets • Smart Punishment System")
    return embed


def _panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title="⚖️ DIFF Smart Punishment System",
        color=discord.Color.dark_red(),
        description=(
            "**Automatic Warning Escalation**\n\n"
            "Use the buttons below to warn members. Punishments escalate automatically.\n\n"
            "**Escalation Rules:**\n"
            "• **1 warning** — Warning only\n"
            "• **2 warnings** — Auto timeout (60 min)\n"
            "• **3 warnings** — Auto kick\n"
            "• **4+ warnings** — Auto ban\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "All actions are logged. Staff can remove warnings with `!remove_warning`.\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        ),
    )
    embed.add_field(
        name="📋 Staff Commands",
        value=(
            "`!remove_warning @user` — Remove the most recent warning from a member\n"
            "`!refresh_smart_punishment` — Refresh this panel"
        ),
        inline=False,
    )
    embed.set_thumbnail(url=DIFF_LOGO_URL)
    embed.set_footer(text=PANEL_TAG)
    return embed


# =========================================================
# MODALS
# =========================================================
class WarnModal(discord.ui.Modal, title="Warn Member"):
    reason = discord.ui.TextInput(
        label="Warning Reason",
        placeholder="Enter the reason for this warning…",
        style=discord.TextStyle.paragraph, max_length=500, required=True,
    )

    def __init__(self, cog: "SmartPunishmentCog", member: discord.Member):
        super().__init__()
        self.cog    = cog
        self.member = member

    async def on_submit(self, interaction: discord.Interaction) -> None:
        mod = interaction.user
        if not isinstance(mod, discord.Member) or not _is_staff(mod):
            return await interaction.response.send_message(
                "Only staff can use this panel.", ephemeral=True
            )
        if self.member == mod:
            return await interaction.response.send_message(
                "You cannot warn yourself.", ephemeral=True
            )
        if self.member.guild_permissions.administrator:
            return await interaction.response.send_message(
                "You cannot warn an administrator.", ephemeral=True
            )

        case_id    = _next_case()
        reason_txt = str(self.reason).strip()

        _add_warning(interaction.guild.id, self.member.id, {
            "case_id":      case_id,
            "reason":       reason_txt,
            "moderator_id": mod.id,
            "timestamp":    _utcnow().isoformat(),
        })
        total = len(_get_warnings(interaction.guild.id, self.member.id))

        warn_embed = _action_embed(
            "⚠️ Warning Issued", discord.Color.orange(),
            self.member, mod, case_id, reason_txt,
            extra=f"Total warnings: {total}",
        )

        await self.cog.send_to(WARNING_LOG_CHANNEL_ID, embed=warn_embed)
        await self.cog.send_to(MOD_LOG_CHANNEL_ID,     embed=warn_embed)

        # Auto-escalation
        escalation = await self.cog.escalate(interaction, self.member, total, reason_txt, mod)

        try:
            dm = discord.Embed(
                title="⚠️ You Have Been Warned",
                description=(
                    f"You were warned in **{interaction.guild.name}**.\n\n"
                    f"**Reason:** {reason_txt}\n"
                    f"**Case:** #{case_id}\n"
                    f"**Total Warnings:** {total}"
                    + (f"\n**Escalation:** {escalation}" if escalation else "")
                ),
                color=discord.Color.orange(),
            )
            dm.set_thumbnail(url=DIFF_LOGO_URL)
            dm.set_footer(text="DIFF Meets • Smart Punishment System")
            await self.member.send(embed=dm)
        except Exception:
            pass

        msg = f"Warned {self.member.mention}. Total warnings: **{total}**."
        if escalation:
            msg += f"\nAuto-escalation applied: **{escalation}**."
        await interaction.response.send_message(msg, ephemeral=True)


# =========================================================
# EPHEMERAL SELECTION VIEWS  (non-persistent)
# =========================================================
class _WarnTargetSelect(discord.ui.UserSelect):
    def __init__(self, cog: "SmartPunishmentCog"):
        super().__init__(placeholder="Select a member to warn…", min_values=1, max_values=1)
        self.cog = cog

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
                "Could not find that member.", ephemeral=True
            )
        await interaction.response.send_modal(WarnModal(self.cog, user))


class _WarnTargetView(discord.ui.View):
    def __init__(self, cog: "SmartPunishmentCog"):
        super().__init__(timeout=120)
        self.add_item(_WarnTargetSelect(cog))


class _CheckSelect(discord.ui.UserSelect):
    def __init__(self):
        super().__init__(placeholder="Select a member to check warnings…", min_values=1, max_values=1)

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
                "Could not find that member.", ephemeral=True
            )

        warnings = _get_warnings(interaction.guild.id, user.id)
        if not warnings:
            return await interaction.response.send_message(
                f"{user.mention} has **0 warnings**.", ephemeral=True
            )

        # Show last 10
        recent = warnings[-10:]
        start  = max(1, len(warnings) - 9)
        lines  = [
            f"**{start + i}.** Case `#{w['case_id']}` — {w['reason']}"
            for i, w in enumerate(recent)
        ]
        embed = discord.Embed(
            title=f"📋 Warning History — {user}",
            description="\n".join(lines),
            color=discord.Color.orange(),
        )
        embed.add_field(name="Total Warnings", value=str(len(warnings)), inline=False)
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.set_footer(text="DIFF Meets • Smart Punishment System — showing last 10")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class _CheckView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(_CheckSelect())


# =========================================================
# PERSISTENT PANEL VIEW
# =========================================================
class SmartPunishmentView(discord.ui.View):
    def __init__(self, cog: "SmartPunishmentCog"):
        super().__init__(timeout=None)
        self.cog = cog

    async def _guard(self, interaction: discord.Interaction) -> bool:
        member = interaction.user
        if not isinstance(member, discord.Member) or not _is_staff(member):
            await interaction.response.send_message(
                "Only staff can use this panel.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Warn Member",    emoji="⚠️", style=discord.ButtonStyle.danger,
                       custom_id="diff_sp_warn_v1")
    async def issue_warn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        await interaction.response.send_message(
            "Select a member to warn:", view=_WarnTargetView(self.cog), ephemeral=True
        )

    @discord.ui.button(label="Check Warnings", emoji="📋", style=discord.ButtonStyle.secondary,
                       custom_id="diff_sp_check_v1")
    async def view_warnings(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        await interaction.response.send_message(
            "Select a member to check:", view=_CheckView(), ephemeral=True
        )


# =========================================================
# COG
# =========================================================
class SmartPunishmentCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot  = bot
        self.view = SmartPunishmentView(self)
        self.bot.add_view(self.view)

    async def send_to(self, channel_id: int, **kwargs) -> None:
        ch = self.bot.get_channel(channel_id)
        if isinstance(ch, discord.TextChannel):
            try:
                await ch.send(**kwargs)
            except Exception:
                pass

    # ── Escalation engine ─────────────────────────────────
    async def escalate(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        total: int,
        reason: str,
        mod: discord.Member,
    ) -> Optional[str]:

        if total == 2:
            case_id = _next_case()
            try:
                await member.timeout(
                    _utcnow() + timedelta(minutes=AUTO_TIMEOUT_MINS),
                    reason=f"Auto-escalation: {reason}",
                )
            except Exception as e:
                await self.send_to(MOD_LOG_CHANNEL_ID, embed=_action_embed(
                    "⚠️ Escalation Failed", discord.Color.red(), member, mod, case_id, reason,
                    extra=f"Timeout failed: {str(e)[:500]}",
                ))
                return None
            await self.send_to(MOD_LOG_CHANNEL_ID, embed=_action_embed(
                "⏳ Auto-Escalation: Timeout", discord.Color.red(), member, mod, case_id, reason,
                extra=f"Triggered by 2 warnings — Duration: {AUTO_TIMEOUT_MINS} min",
            ))
            return f"Timeout ({AUTO_TIMEOUT_MINS} min)"

        if total == 3:
            case_id = _next_case()
            try:
                await member.kick(reason=f"Auto-escalation: {reason}")
            except Exception as e:
                await self.send_to(MOD_LOG_CHANNEL_ID, embed=_action_embed(
                    "⚠️ Escalation Failed", discord.Color.red(), member, mod, case_id, reason,
                    extra=f"Kick failed: {str(e)[:500]}",
                ))
                return None
            await self.send_to(MOD_LOG_CHANNEL_ID, embed=_action_embed(
                "👢 Auto-Escalation: Kick", discord.Color.dark_red(), member, mod, case_id, reason,
                extra="Triggered by 3 warnings",
            ))
            return "Kick"

        if total >= 4:
            case_id = _next_case()
            try:
                await member.ban(reason=f"Auto-escalation: {reason}", delete_message_seconds=0)
            except Exception as e:
                await self.send_to(MOD_LOG_CHANNEL_ID, embed=_action_embed(
                    "⚠️ Escalation Failed", discord.Color.red(), member, mod, case_id, reason,
                    extra=f"Ban failed: {str(e)[:500]}",
                ))
                return None
            await self.send_to(MOD_LOG_CHANNEL_ID, embed=_action_embed(
                "🔨 Auto-Escalation: Ban", discord.Color.dark_red(), member, mod, case_id, reason,
                extra="Triggered by 4+ warnings",
            ))
            return "Ban"

        return None   # 1 warning → warn only

    # ── Panel management ──────────────────────────────────
    async def ensure_panel(self) -> None:
        channel = self.bot.get_channel(PANEL_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            try:
                channel = await self.bot.fetch_channel(PANEL_CHANNEL_ID)
            except Exception:
                channel = None
        if not isinstance(channel, discord.TextChannel):
            print(f"[SmartPunishment] Channel {PANEL_CHANNEL_ID} not found.")
            return

        embed    = _panel_embed()
        saved_id = _get_panel_id()

        if saved_id:
            try:
                msg = await channel.fetch_message(saved_id)
                await msg.edit(embed=embed, view=self.view)
                print("[SmartPunishment] Panel refreshed.")
                return
            except discord.NotFound:
                pass
            except Exception as e:
                print(f"[SmartPunishment] Edit failed: {e}")

        # Scan for stale panel
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
            _set_panel_id(new_msg.id)
            print(f"[SmartPunishment] Panel posted: {new_msg.id}")
        except Exception as e:
            print(f"[SmartPunishment] Post failed: {e}")

    # ── Events / commands ─────────────────────────────────
    @commands.Cog.listener()
    async def on_ready(self):
        await self.ensure_panel()
        print("[SmartPunishment] Cog ready.")

    @commands.command(name="remove_warning")
    async def cmd_remove_warning(self, ctx: commands.Context, member: discord.Member, warning_number: int):
        """Remove one warning from a member. Usage: !remove_warning @member <number>"""
        if not isinstance(ctx.author, discord.Member) or not _is_staff(ctx.author):
            return await ctx.send("Only staff can remove warnings.", delete_after=8)

        warnings = _get_warnings(ctx.guild.id, member.id)
        if not warnings:
            return await ctx.send(f"{member.mention} has no warnings.", delete_after=8)

        if not 1 <= warning_number <= len(warnings):
            return await ctx.send(
                f"Invalid number. {member.mention} has {len(warnings)} warning(s).", delete_after=8
            )

        removed = warnings.pop(warning_number - 1)
        _set_warnings(ctx.guild.id, member.id, warnings)

        embed = discord.Embed(
            title="🧾 Warning Removed",
            color=discord.Color.green(),
            timestamp=_utcnow(),
        )
        embed.add_field(name="User",             value=f"{member.mention}\n`{member.id}`", inline=True)
        embed.add_field(name="Moderator",        value=ctx.author.mention,                 inline=True)
        embed.add_field(name="Removed Warning",  value=f"Case `#{removed['case_id']}` — {removed['reason']}", inline=False)
        embed.add_field(name="Remaining",        value=str(len(warnings)),                 inline=False)
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.set_footer(text="DIFF Meets • Smart Punishment System")

        await self.send_to(MOD_LOG_CHANNEL_ID, embed=embed)
        await ctx.send(
            f"Removed warning #{warning_number} from {member.mention}. "
            f"Remaining warnings: **{len(warnings)}**.",
            delete_after=12,
        )

    @commands.command(name="refresh_smart_punishment")
    @commands.has_permissions(manage_guild=True)
    async def cmd_refresh(self, ctx: commands.Context):
        await self.ensure_panel()
        await ctx.send("Smart punishment panel refreshed.", delete_after=8)


# =========================================================
# SETUP
# =========================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(SmartPunishmentCog(bot))
