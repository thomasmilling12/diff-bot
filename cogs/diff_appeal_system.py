from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Optional

import discord
from discord.ext import commands

# =========================================================
# CONFIG
# =========================================================
APPEAL_PANEL_CHANNEL_ID  = 1156363575150002226   # public panel
APPEAL_REVIEW_CHANNEL_ID = 1486598266211664003   # staff review
APPEAL_LOG_CHANNEL_ID    = 1486598266211664003   # decision log

STAFF_ROLE_IDS: set[int] = {
    850391095845584937,   # Leader
    850391378559238235,   # Co-Leader
    990011447193006101,   # Manager
}

PANEL_TAG = "DIFF_APPEAL_PANEL_V1"

DATA_DIR     = "diff_data"
APPEALS_FILE = os.path.join(DATA_DIR, "appeals.json")
PANEL_FILE   = os.path.join(DATA_DIR, "appeal_panel.json")
WARN_FILE    = os.path.join(DATA_DIR, "mod_warnings.json")   # shared with mod hub + smart punishment

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


def _is_staff(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    return any(r.id in STAFF_ROLE_IDS for r in member.roles)


# ── Panel message ID ──────────────────────────────────────
def _get_panel_id() -> Optional[int]:
    v = _load(PANEL_FILE).get("panel_message_id")
    return int(v) if v else None


def _set_panel_id(msg_id: int) -> None:
    data = _load(PANEL_FILE)
    data["panel_message_id"] = msg_id
    _dump(PANEL_FILE, data)


# ── Appeals storage ───────────────────────────────────────
def _load_appeals() -> dict:
    return _load(APPEALS_FILE, {"last_id": 0, "appeals": {}})


def _next_appeal_id() -> int:
    data = _load_appeals()
    data["last_id"] = data.get("last_id", 0) + 1
    _dump(APPEALS_FILE, data)
    return data["last_id"]


def _save_appeal(appeal_id: int, record: dict) -> None:
    data = _load_appeals()
    data.setdefault("appeals", {})[str(appeal_id)] = record
    _dump(APPEALS_FILE, data)


def _get_appeal(appeal_id: int) -> Optional[dict]:
    return _load_appeals().get("appeals", {}).get(str(appeal_id))


def _update_appeal(appeal_id: int, **updates) -> None:
    data = _load_appeals()
    record = data.get("appeals", {}).get(str(appeal_id))
    if record:
        record.update(updates)
        data["appeals"][str(appeal_id)] = record
        _dump(APPEALS_FILE, data)


# ── Warning reversal helper ───────────────────────────────
def _remove_latest_warning(guild_id: int, user_id: int) -> tuple[bool, str]:
    data = _load(WARN_FILE)
    gk, uk = str(guild_id), str(user_id)
    warnings = data.get(gk, {}).get(uk, [])
    if not warnings:
        return False, "No warning record found for this user."
    removed = warnings.pop()
    data.setdefault(gk, {})[uk] = warnings
    _dump(WARN_FILE, data)
    return True, f"Latest warning removed (Case #{removed.get('case_id', '?')})"


# =========================================================
# MODALS
# =========================================================
class AppealModal(discord.ui.Modal, title="Submit an Appeal"):
    punishment_type = discord.ui.TextInput(
        label="What are you appealing?",
        placeholder="Example: warning, timeout, kick, ban",
        max_length=100, required=True,
    )
    punishment_reason = discord.ui.TextInput(
        label="Why were you punished?",
        placeholder="What reason were you given?",
        style=discord.TextStyle.paragraph, max_length=500, required=True,
    )
    appeal_reason = discord.ui.TextInput(
        label="Why should this be reviewed?",
        placeholder="Explain your side clearly and respectfully.",
        style=discord.TextStyle.paragraph, max_length=1200, required=True,
    )

    def __init__(self, cog: "AppealSystemCog"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction) -> None:
        appeal_id = _next_appeal_id()
        record = {
            "appeal_id":       appeal_id,
            "guild_id":        interaction.guild.id if interaction.guild else None,
            "user_id":         interaction.user.id,
            "username":        str(interaction.user),
            "punishment_type": str(self.punishment_type).strip(),
            "punishment_reason": str(self.punishment_reason).strip(),
            "appeal_reason":   str(self.appeal_reason).strip(),
            "status":          "pending",
            "created_at":      _utcnow().isoformat(),
            "reviewed_by":     None,
            "reviewed_at":     None,
            "decision_note":   None,
            "review_message_id": None,
            "reversal_result": None,
        }
        _save_appeal(appeal_id, record)

        review_ch = interaction.client.get_channel(APPEAL_REVIEW_CHANNEL_ID)
        if not isinstance(review_ch, discord.TextChannel):
            return await interaction.response.send_message(
                "Appeal could not be sent — staff review channel not found.", ephemeral=True
            )

        embed = discord.Embed(
            title=f"🧾 Appeal Submission #{appeal_id}",
            color=discord.Color.orange(),
            timestamp=_utcnow(),
        )
        embed.add_field(name="User",             value=f"{interaction.user.mention}\n`{interaction.user.id}`", inline=True)
        embed.add_field(name="Punishment Type",  value=record["punishment_type"],                               inline=True)
        embed.add_field(name="Status",           value="⏳ Pending Review",                                     inline=True)
        embed.add_field(name="Punishment Reason", value=record["punishment_reason"],                            inline=False)
        embed.add_field(name="Appeal Reason",    value=record["appeal_reason"],                                 inline=False)
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.set_footer(text="DIFF Meets • Appeal Review")

        review_view = AppealReviewView(self.cog, appeal_id)
        self.cog.bot.add_view(review_view)   # register for persistence

        review_msg = await review_ch.send(
            content=f"<@&{next(iter(STAFF_ROLE_IDS))}>",
            embed=embed,
            view=review_view,
            allowed_mentions=discord.AllowedMentions(roles=True),
        )
        _update_appeal(appeal_id, review_message_id=review_msg.id)

        await interaction.response.send_message(
            f"Your appeal has been submitted. Appeal ID: `#{appeal_id}`",
            ephemeral=True,
        )


class DecisionNoteModal(discord.ui.Modal, title="Appeal Decision Note"):
    note = discord.ui.TextInput(
        label="Decision Note",
        placeholder="Explain why this appeal was accepted, denied, or needs more info.",
        style=discord.TextStyle.paragraph, max_length=1000, required=True,
    )

    def __init__(self, cog: "AppealSystemCog", appeal_id: int, action: str):
        super().__init__()
        self.cog       = cog
        self.appeal_id = appeal_id
        self.action    = action

    async def on_submit(self, interaction: discord.Interaction) -> None:
        mod = interaction.user
        if not isinstance(mod, discord.Member) or not _is_staff(mod):
            return await interaction.response.send_message(
                "Only staff can review appeals.", ephemeral=True
            )
        await self.cog.process_decision(interaction, self.appeal_id, self.action, str(self.note).strip())


# =========================================================
# REVIEW BUTTONS  (per-appeal custom_ids → correct restore)
# =========================================================
class _AppealActionButton(discord.ui.Button):
    """A button whose custom_id encodes the appeal_id so it survives bot restarts."""

    _ACTION_STYLES = {
        "accepted":       (discord.ButtonStyle.success,   "✅", "Accept"),
        "denied":         (discord.ButtonStyle.danger,    "❌", "Deny"),
        "needs_more_info":(discord.ButtonStyle.secondary, "📨", "Need More Info"),
    }

    def __init__(self, cog: "AppealSystemCog", appeal_id: int, action: str):
        style, emoji, label = self._ACTION_STYLES[action]
        super().__init__(
            label=label, style=style, emoji=emoji,
            custom_id=f"diff_ap_{action[:4]}_{appeal_id}",
        )
        self.cog       = cog
        self.appeal_id = appeal_id
        self.action    = action

    async def callback(self, interaction: discord.Interaction) -> None:
        mod = interaction.user
        if not isinstance(mod, discord.Member) or not _is_staff(mod):
            return await interaction.response.send_message(
                "Only staff can review appeals.", ephemeral=True
            )
        await interaction.response.send_modal(
            DecisionNoteModal(self.cog, self.appeal_id, self.action)
        )


class AppealReviewView(discord.ui.View):
    def __init__(self, cog: "AppealSystemCog", appeal_id: int):
        super().__init__(timeout=None)
        self.cog       = cog
        self.appeal_id = appeal_id
        self.add_item(_AppealActionButton(cog, appeal_id, "accepted"))
        self.add_item(_AppealActionButton(cog, appeal_id, "denied"))
        self.add_item(_AppealActionButton(cog, appeal_id, "needs_more_info"))


# =========================================================
# PUBLIC PANEL VIEW  (one persistent button)
# =========================================================
class AppealPanelView(discord.ui.View):
    def __init__(self, cog: "AppealSystemCog"):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Submit Appeal", style=discord.ButtonStyle.primary,
        emoji="🧾", custom_id="diff_appeal_submit_v1",
    )
    async def submit_appeal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AppealModal(self.cog))


# =========================================================
# PANEL EMBED
# =========================================================
def _panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🧾 DIFF Appeal Center",
        color=discord.Color.blurple(),
        description=(
            "**Appeal Information**\n\n"
            "Use this panel if you want staff to review a punishment decision.\n\n"
            "**Before submitting:**\n"
            "• Be respectful and honest\n"
            "• Explain your side clearly\n"
            "• Do not submit multiple appeals for the same issue\n"
            "• Troll or false appeals may be denied without review\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "**Accepted appeals can automatically reverse:**\n"
            "• ⚠️ Warning → latest warning removed\n"
            "• ⏰ Timeout → cleared immediately\n"
            "• 🔨 Ban → user unbanned automatically\n"
            "• 👢 Kick → reviewed manually (Discord cannot reverse kicks)\n\n"
            "Press the button below to submit your appeal.\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        ),
    )
    embed.set_thumbnail(url=DIFF_LOGO_URL)
    embed.set_footer(text=PANEL_TAG)
    return embed


# =========================================================
# COG
# =========================================================
class AppealSystemCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot        = bot
        self.panel_view = AppealPanelView(self)
        self.bot.add_view(self.panel_view)

    # ── Punishment reversal ───────────────────────────────
    async def reverse_punishment(
        self,
        guild: Optional[discord.Guild],
        user_id: int,
        punishment_type: str,
    ) -> str:
        pt = (punishment_type or "").lower().strip()

        if pt in {"warning", "warn"}:
            if guild is None:
                return "Warning reversal skipped: guild not found."
            ok, msg = _remove_latest_warning(guild.id, user_id)
            return msg

        if pt in {"timeout", "mute"}:
            if guild is None:
                return "Timeout reversal skipped: guild not found."
            member = guild.get_member(user_id)
            if member is None:
                try:
                    member = await guild.fetch_member(user_id)
                except Exception:
                    member = None
            if member is None:
                return "Timeout reversal skipped: member is no longer in the server."
            try:
                await member.timeout(None, reason="Accepted appeal — timeout cleared")
                return "Timeout cleared automatically."
            except Exception as e:
                return f"Timeout reversal failed: {str(e)[:500]}"

        if pt == "ban":
            if guild is None:
                return "Ban reversal skipped: guild not found."
            try:
                await guild.unban(discord.Object(id=user_id), reason="Accepted appeal — ban removed")
                return "User unbanned automatically."
            except Exception as e:
                return f"Ban reversal failed: {str(e)[:500]}"

        if pt == "kick":
            return "Kick cannot be reversed automatically. Manual reinvite required."

        return f"No automatic reversal configured for `{pt}`."

    # ── Log helper ────────────────────────────────────────
    async def _log(self, channel_id: int, **kwargs) -> None:
        ch = self.bot.get_channel(channel_id)
        if isinstance(ch, discord.TextChannel):
            try:
                await ch.send(**kwargs)
            except Exception:
                pass

    # ── Decision processor ────────────────────────────────
    async def process_decision(
        self,
        interaction: discord.Interaction,
        appeal_id: int,
        action: str,
        note: str,
    ) -> None:
        appeal = _get_appeal(appeal_id)
        if not appeal:
            return await interaction.response.send_message(
                "Appeal record not found.", ephemeral=True
            )
        if appeal.get("status") in {"accepted", "denied"}:
            return await interaction.response.send_message(
                "That appeal has already been fully reviewed.", ephemeral=True
            )

        label_map = {
            "accepted":        "Accepted",
            "denied":          "Denied",
            "needs_more_info": "Needs More Info",
        }
        color_map = {
            "accepted":        discord.Color.green(),
            "denied":          discord.Color.red(),
            "needs_more_info": discord.Color.gold(),
        }
        status_label = label_map.get(action, action)
        color        = color_map.get(action, discord.Color.blurple())

        # Auto-reverse punishment when accepted
        reversal_result: Optional[str] = None
        if action == "accepted":
            reversal_result = await self.reverse_punishment(
                guild=interaction.guild,
                user_id=appeal["user_id"],
                punishment_type=appeal.get("punishment_type", ""),
            )

        _update_appeal(
            appeal_id,
            status=action,
            reviewed_by=interaction.user.id,
            reviewed_at=_utcnow().isoformat(),
            decision_note=note,
            reversal_result=reversal_result,
        )

        status_icon = "✅" if action == "accepted" else "❌" if action == "denied" else "📨"

        # Edit the review message embed
        try:
            updated = discord.Embed(
                title=f"🧾 Appeal Submission #{appeal_id}",
                color=color,
                timestamp=_utcnow(),
            )
            updated.add_field(name="User",              value=f"<@{appeal['user_id']}>\n`{appeal['user_id']}`", inline=True)
            updated.add_field(name="Punishment Type",   value=appeal["punishment_type"],                         inline=True)
            updated.add_field(name="Status",            value=f"{status_icon} {status_label}",                   inline=True)
            updated.add_field(name="Punishment Reason", value=appeal["punishment_reason"],                        inline=False)
            updated.add_field(name="Appeal Reason",     value=appeal["appeal_reason"],                            inline=False)
            updated.add_field(name="Reviewed By",       value=interaction.user.mention,                           inline=True)
            updated.add_field(name="Decision Note",     value=note,                                               inline=False)
            if reversal_result:
                updated.add_field(name="⚙️ Punishment Reversal", value=reversal_result, inline=False)
            updated.set_thumbnail(url=DIFF_LOGO_URL)
            updated.set_footer(text="DIFF Meets • Appeal Review")
            await interaction.message.edit(embed=updated, view=None)
        except Exception:
            pass

        # Log the decision
        log_embed = discord.Embed(
            title=f"🧾 Appeal {status_label} — #{appeal_id}",
            color=color,
            timestamp=_utcnow(),
        )
        log_embed.add_field(name="Appeal ID",       value=f"`#{appeal_id}`",                                       inline=True)
        log_embed.add_field(name="User",             value=f"<@{appeal['user_id']}>\n`{appeal['user_id']}`",       inline=True)
        log_embed.add_field(name="Reviewer",         value=f"{interaction.user.mention}\n`{interaction.user.id}`", inline=True)
        log_embed.add_field(name="Punishment Type",  value=appeal["punishment_type"],                               inline=False)
        log_embed.add_field(name="Decision Note",    value=note,                                                    inline=False)
        if reversal_result:
            log_embed.add_field(name="⚙️ Punishment Reversal", value=reversal_result, inline=False)
        log_embed.set_thumbnail(url=DIFF_LOGO_URL)
        log_embed.set_footer(text="DIFF Meets • Appeal Logs")
        await self._log(APPEAL_LOG_CHANNEL_ID, embed=log_embed)

        # DM the user
        try:
            user = interaction.client.get_user(appeal["user_id"]) or \
                   await interaction.client.fetch_user(appeal["user_id"])
            dm = discord.Embed(
                title=f"🧾 Your Appeal Was {status_label}",
                description=(
                    f"Your appeal in **{interaction.guild.name if interaction.guild else 'the server'}** has been reviewed.\n\n"
                    f"**Appeal ID:** #{appeal_id}\n"
                    f"**Status:** {status_label}\n"
                    f"**Note:** {note}"
                ),
                color=color,
            )
            if reversal_result:
                dm.add_field(name="⚙️ Punishment Reversal", value=reversal_result, inline=False)
            dm.set_thumbnail(url=DIFF_LOGO_URL)
            dm.set_footer(text="DIFF Meets • Appeal System")
            await user.send(embed=dm)
        except Exception:
            pass

        confirm = f"Appeal `#{appeal_id}` marked as **{status_label}**."
        if reversal_result:
            confirm += f"\n⚙️ Reversal: **{reversal_result}**"
        await interaction.response.send_message(confirm, ephemeral=True)

    # ── Panel management ──────────────────────────────────
    async def ensure_panel(self) -> None:
        channel = self.bot.get_channel(APPEAL_PANEL_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            try:
                channel = await self.bot.fetch_channel(APPEAL_PANEL_CHANNEL_ID)
            except Exception:
                channel = None
        if not isinstance(channel, discord.TextChannel):
            print(f"[AppealSystem] Channel {APPEAL_PANEL_CHANNEL_ID} not found.")
            return

        embed    = _panel_embed()
        saved_id = _get_panel_id()

        if saved_id:
            try:
                msg = await channel.fetch_message(saved_id)
                await msg.edit(embed=embed, view=self.panel_view)
                print("[AppealSystem] Panel refreshed.")
                return
            except discord.NotFound:
                pass
            except Exception as e:
                print(f"[AppealSystem] Edit failed: {e}")

        # Remove stale panels, post fresh
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
            new_msg = await channel.send(embed=embed, view=self.panel_view)
            _set_panel_id(new_msg.id)
            print(f"[AppealSystem] Panel posted: {new_msg.id}")
        except Exception as e:
            print(f"[AppealSystem] Post failed: {e}")

    # ── Events / commands ─────────────────────────────────
    @commands.Cog.listener()
    async def on_ready(self):
        # Restore persistent review views for every open appeal
        data = _load_appeals()
        restored = 0
        for appeal_id_str, appeal in data.get("appeals", {}).items():
            if appeal.get("status") in {"pending", "needs_more_info"}:
                try:
                    self.bot.add_view(AppealReviewView(self, int(appeal_id_str)))
                    restored += 1
                except Exception:
                    pass

        await self.ensure_panel()
        print(f"[AppealSystem] Cog ready. ({restored} open appeal views restored)")

    @commands.command(name="refresh_appeal_panel")
    @commands.has_permissions(manage_guild=True)
    async def cmd_refresh(self, ctx: commands.Context):
        await self.ensure_panel()
        await ctx.send("Appeal panel refreshed.", delete_after=8)


# =========================================================
# SETUP
# =========================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(AppealSystemCog(bot))
