from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import discord
from discord.ext import commands

# =========================================================
# CONFIG
# =========================================================

GUILD_ID                = 850386896509337710
MANAGER_HUB_CHANNEL_ID  = 1485273802391814224
WRITEUP_CHANNEL_ID      = 1485826044865937612
WRITEUP_ALERT_CHANNEL_ID = 1485265848099799163  # staff-logs

MANAGER_ROLE_IDS: list[int] = []   # add role IDs here if non-Manage-Server staff need access

STRIKE_THRESHOLD = 3

COLOR_PRIMARY = 0x1F6FEB
COLOR_WARNING = 0xF39C12
COLOR_DANGER  = 0xE74C3C
COLOR_SUCCESS = 0x2ECC71
COLOR_MUTED   = 0x95A5A6

DATA_DIR     = Path("diff_data")
WRITEUPS_FILE = DATA_DIR / "manager_writeups.json"
STRIKES_FILE  = DATA_DIR / "manager_writeup_strikes.json"

# =========================================================
# HELPERS
# =========================================================

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

def _load(path: Path, default) -> Any:
    if not path.exists():
        _save(path, default)
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _save(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def _has_access(member: discord.Member) -> bool:
    if member.guild_permissions.manage_guild or member.guild_permissions.administrator:
        return True
    role_ids = {r.id for r in member.roles}
    return any(rid in role_ids for rid in MANAGER_ROLE_IDS if rid)

def _id_from_embed(interaction: discord.Interaction) -> str:
    """Extract WU-XXXX from the embed title after a bot restart."""
    if interaction.message and interaction.message.embeds:
        title = interaction.message.embeds[0].title or ""
        match = re.search(r"(WU-\d+)", title)
        if match:
            return match.group(1)
    return ""

# =========================================================
# MODALS
# =========================================================

class WriteUpModal(discord.ui.Modal):
    def __init__(self, cog: "ManagerWriteUpSystem", writeup_type: str):
        super().__init__(title=f"{writeup_type} Form")
        self.cog          = cog
        self.writeup_type = writeup_type

        self.member_field   = discord.ui.TextInput(label="Member Mention / Name",    placeholder="@username or Discord name",              max_length=100,  required=True)
        self.psn_field      = discord.ui.TextInput(label="PSN",                       placeholder="Example: Smokey",                        max_length=100,  required=False)
        self.reason_field   = discord.ui.TextInput(label="Reason",                    placeholder="Explain the issue clearly.",              style=discord.TextStyle.paragraph, max_length=1200, required=True)
        self.evidence_field = discord.ui.TextInput(label="Evidence Link",             placeholder="Message link, image link, clip, etc.",   max_length=400,  required=False)
        self.severity_field = discord.ui.TextInput(label="Severity",                  placeholder="Low / Medium / High",                    max_length=30,   required=True)

        self.add_item(self.member_field)
        self.add_item(self.psn_field)
        self.add_item(self.reason_field)
        self.add_item(self.evidence_field)
        self.add_item(self.severity_field)

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.create_writeup(
            interaction  = interaction,
            writeup_type = self.writeup_type,
            member_name  = str(self.member_field).strip(),
            psn          = str(self.psn_field).strip()   or "Not Provided",
            reason       = str(self.reason_field).strip(),
            evidence     = str(self.evidence_field).strip() or "No evidence link provided",
            severity     = str(self.severity_field).strip(),
        )


class RemoveWriteUpModal(discord.ui.Modal, title="Remove Write-Up"):
    writeup_id_field = discord.ui.TextInput(label="Write-Up ID",      placeholder="Example: WU-0001",                    max_length=20,  required=True)
    reason_field     = discord.ui.TextInput(label="Removal Reason",    placeholder="Why should this write-up be removed?", style=discord.TextStyle.paragraph, max_length=500, required=True)

    def __init__(self, cog: "ManagerWriteUpSystem"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.remove_by_id(
            interaction     = interaction,
            writeup_id      = str(self.writeup_id_field).strip().upper(),
            removal_reason  = str(self.reason_field).strip(),
        )

# =========================================================
# ACTION BUTTONS (persistent — ID extracted from embed)
# =========================================================

class WriteUpActionView(discord.ui.View):
    """
    Persistent view attached to each write-up embed.
    writeup_id is passed when first posting; after a restart it is
    recovered from the embed title via _id_from_embed().
    """
    def __init__(self, cog: "ManagerWriteUpSystem", writeup_id: str = ""):
        super().__init__(timeout=None)
        self.cog        = cog
        self.writeup_id = writeup_id

    def _wid(self, interaction: discord.Interaction) -> str:
        return self.writeup_id or _id_from_embed(interaction)

    @discord.ui.button(label="Mark Resolved", style=discord.ButtonStyle.success,
                       emoji="✅", custom_id="diff_writeup_resolve")
    async def mark_resolved(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not _has_access(interaction.user):
            await interaction.response.send_message("You do not have permission.", ephemeral=True)
            return
        await self.cog.resolve_writeup(interaction, self._wid(interaction))

    @discord.ui.button(label="Add Strike", style=discord.ButtonStyle.danger,
                       emoji="⚠️", custom_id="diff_writeup_add_strike")
    async def add_strike(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not _has_access(interaction.user):
            await interaction.response.send_message("You do not have permission.", ephemeral=True)
            return
        await self.cog.add_strike(interaction, self._wid(interaction))

    @discord.ui.button(label="Delete Entry", style=discord.ButtonStyle.secondary,
                       emoji="🗑️", custom_id="diff_writeup_delete")
    async def delete_entry(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not _has_access(interaction.user):
            await interaction.response.send_message("You do not have permission.", ephemeral=True)
            return
        await self.cog.delete_writeup(interaction, self._wid(interaction))

# =========================================================
# PANEL DROPDOWN + VIEW (persistent)
# =========================================================

class ManagerWriteUpSelect(discord.ui.Select):
    def __init__(self, cog: "ManagerWriteUpSystem"):
        self.cog = cog
        super().__init__(
            placeholder="Select a manager action...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="Member Write-Up",  value="Member Write-Up",  emoji="📝", description="Create a standard member write-up"),
                discord.SelectOption(label="Host Write-Up",    value="Host Write-Up",    emoji="🏁", description="Create a host-specific write-up"),
                discord.SelectOption(label="Warning Notice",   value="Warning Notice",   emoji="⚠️", description="Issue a warning entry"),
                discord.SelectOption(label="Strike Entry",     value="Strike Entry",     emoji="🚨", description="Issue a strike entry"),
                discord.SelectOption(label="Remove Write-Up",  value="Remove Write-Up",  emoji="🗑️", description="Remove an existing write-up by ID"),
            ],
            custom_id="diff_manager_writeup_select",
        )

    async def callback(self, interaction: discord.Interaction):
        if not isinstance(interaction.user, discord.Member) or not _has_access(interaction.user):
            await interaction.response.send_message("You do not have permission to use this panel.", ephemeral=True)
            return
        selected = self.values[0]
        if selected == "Remove Write-Up":
            await interaction.response.send_modal(RemoveWriteUpModal(self.cog))
        else:
            await interaction.response.send_modal(WriteUpModal(self.cog, selected))


class ManagerWriteUpPanel(discord.ui.View):
    def __init__(self, cog: "ManagerWriteUpSystem"):
        super().__init__(timeout=None)
        self.add_item(ManagerWriteUpSelect(cog))

# =========================================================
# COG
# =========================================================

class ManagerWriteUpSystem(commands.Cog, name="ManagerWriteUpSystem"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        _load(WRITEUPS_FILE, {"counter": 0, "entries": {}})
        _load(STRIKES_FILE,  {})
        self.bot.add_view(ManagerWriteUpPanel(self))
        self.bot.add_view(WriteUpActionView(self))

    @commands.Cog.listener()
    async def on_ready(self):
        print("[ManagerWriteUpSystem] Cog ready.")

    # ── data helpers ─────────────────────────────────────────

    def _get_writeups(self) -> Dict[str, Any]:
        return _load(WRITEUPS_FILE, {"counter": 0, "entries": {}})

    def _set_writeups(self, data: Dict[str, Any]) -> None:
        _save(WRITEUPS_FILE, data)

    def _get_strikes(self) -> Dict[str, int]:
        return _load(STRIKES_FILE, {})

    def _set_strikes(self, data: Dict[str, int]) -> None:
        _save(STRIKES_FILE, data)

    def _next_id(self) -> str:
        data = self._get_writeups()
        data["counter"] += 1
        self._set_writeups(data)
        return f"WU-{data['counter']:04d}"

    # ── embed builder ────────────────────────────────────────

    def _build_embed(self, entry: Dict[str, Any], color: int) -> discord.Embed:
        embed = discord.Embed(
            title     = f"📋 {entry['writeup_type']} • {entry['writeup_id']}",
            color     = color,
            timestamp = _utcnow(),
        )
        embed.add_field(name="Date",         value=entry["date"],           inline=True)
        embed.add_field(name="Member",       value=entry["member_name"],    inline=True)
        embed.add_field(name="PSN",          value=entry["psn"],            inline=True)
        embed.add_field(name="Submitted By", value=entry["submitted_by"],   inline=True)
        embed.add_field(name="Severity",     value=entry["severity"],       inline=True)
        embed.add_field(name="Status",       value=entry["status"],         inline=True)
        embed.add_field(name="Reason",       value=entry["reason"][:1024],  inline=False)
        embed.add_field(name="Evidence",     value=entry["evidence"][:1024],inline=False)
        embed.add_field(name="Strike Count", value=str(entry.get("strike_count", 0)), inline=True)
        if entry.get("resolved_by"):
            embed.add_field(name="Resolved By", value=entry["resolved_by"], inline=True)
        if entry.get("removed_by"):
            embed.add_field(name="Removed By",      value=entry["removed_by"],      inline=True)
            embed.add_field(name="Removal Reason",  value=entry.get("removal_reason", "—")[:512], inline=False)
        embed.set_footer(text="Different Meets • Manager Write-Up System")
        return embed

    # ── panel embed builder ───────────────────────────────────

    def _build_panel_embed(self) -> discord.Embed:
        data     = self._get_writeups()
        total    = len(data["entries"])
        active   = sum(1 for e in data["entries"].values() if e["status"] == "Active")
        resolved = sum(1 for e in data["entries"].values() if e["status"] == "Resolved")

        embed = discord.Embed(
            title       = "🛠️ DIFF Manager Write-Up Hub",
            description = (
                "Use the dropdown menu below to manage crew write-ups professionally.\n\n"
                "**Available actions:**\n"
                "• 📝 Member Write-Up\n"
                "• 🏁 Host Write-Up\n"
                "• ⚠️ Warning Notice\n"
                "• 🚨 Strike Entry\n"
                "• 🗑️ Remove Write-Up"
            ),
            color = COLOR_PRIMARY,
        )
        embed.add_field(
            name  = "How It Works",
            value = "Select an option from the dropdown, fill in the form, and the bot will post the write-up in the write-up channel with action buttons.",
            inline= False,
        )
        embed.add_field(
            name  = "System Notes",
            value = (
                "All entries are stored automatically. Strike totals are tracked per member. "
                f"Repeat offenders are flagged when they hit **{STRIKE_THRESHOLD} strikes**."
            ),
            inline= False,
        )
        embed.add_field(name="📊 Total Entries", value=str(total),    inline=True)
        embed.add_field(name="🔴 Active",        value=str(active),   inline=True)
        embed.add_field(name="✅ Resolved",       value=str(resolved), inline=True)
        embed.set_footer(text="Different Meets • Manager Hub")
        return embed

    # ── core logic ───────────────────────────────────────────

    async def create_writeup(
        self,
        interaction:  discord.Interaction,
        writeup_type: str,
        member_name:  str,
        psn:          str,
        reason:       str,
        evidence:     str,
        severity:     str,
    ):
        if not interaction.guild or interaction.guild.id != GUILD_ID:
            await interaction.response.send_message("This system is not configured for this server.", ephemeral=True)
            return

        writeup_id = self._next_id()
        date_text  = _utcnow().strftime("%m/%d/%Y")

        strikes = self._get_strikes()
        current_strikes = strikes.get(member_name, 0)
        if writeup_type == "Strike Entry":
            current_strikes += 1
            strikes[member_name] = current_strikes
            self._set_strikes(strikes)

        entry: Dict[str, Any] = {
            "writeup_id":       writeup_id,
            "writeup_type":     writeup_type,
            "member_name":      member_name,
            "psn":              psn,
            "reason":           reason,
            "evidence":         evidence,
            "severity":         severity,
            "submitted_by":     interaction.user.mention,
            "submitted_by_id":  interaction.user.id,
            "date":             date_text,
            "status":           "Active",
            "created_at":       _utcnow().isoformat(),
            "strike_count":     current_strikes,
            "message_id":       None,
            "resolved_by":      None,
            "removed_by":       None,
            "removal_reason":   None,
        }

        data = self._get_writeups()
        data["entries"][writeup_id] = entry
        self._set_writeups(data)

        color = {
            "Warning Notice": COLOR_WARNING,
            "Host Write-Up":  COLOR_DANGER,
            "Strike Entry":   COLOR_DANGER,
        }.get(writeup_type, COLOR_PRIMARY)

        ch = interaction.guild.get_channel(WRITEUP_CHANNEL_ID)
        if ch is None:
            await interaction.response.send_message(
                f"❌ Write-up channel not found (ID: {WRITEUP_CHANNEL_ID}).", ephemeral=True
            )
            return

        msg = await ch.send(embed=self._build_embed(entry, color), view=WriteUpActionView(self, writeup_id))

        data = self._get_writeups()
        data["entries"][writeup_id]["message_id"] = msg.id
        self._set_writeups(data)

        if current_strikes >= STRIKE_THRESHOLD:
            await self._threshold_alert(interaction.guild, entry, current_strikes)

        await interaction.response.send_message(
            f"✅ **{writeup_type}** created — ID: `{writeup_id}`", ephemeral=True
        )

    async def _threshold_alert(self, guild: discord.Guild, entry: Dict[str, Any], strikes: int):
        if not WRITEUP_ALERT_CHANNEL_ID:
            return
        ch = guild.get_channel(WRITEUP_ALERT_CHANNEL_ID)
        if ch is None:
            return
        embed = discord.Embed(
            title       = "🚨 Strike Threshold Reached",
            description = (
                f"**Member:** {entry['member_name']}\n"
                f"**PSN:** {entry['psn']}\n"
                f"**Total Strikes:** {strikes}\n"
                f"**Latest Entry:** {entry['writeup_id']}"
            ),
            color     = COLOR_DANGER,
            timestamp = _utcnow(),
        )
        embed.set_footer(text="Different Meets • Automatic Strike Alert")
        try:
            await ch.send(embed=embed)
        except discord.HTTPException:
            pass

    async def resolve_writeup(self, interaction: discord.Interaction, writeup_id: str):
        if not writeup_id:
            await interaction.response.send_message("Could not determine write-up ID.", ephemeral=True)
            return
        data  = self._get_writeups()
        entry = data["entries"].get(writeup_id)
        if not entry:
            await interaction.response.send_message(f"Write-up `{writeup_id}` not found.", ephemeral=True)
            return
        entry["status"]      = "Resolved"
        entry["resolved_by"] = interaction.user.mention
        entry["resolved_at"] = _utcnow().isoformat()
        data["entries"][writeup_id] = entry
        self._set_writeups(data)
        try:
            await interaction.message.edit(
                embed = self._build_embed(entry, COLOR_SUCCESS),
                view  = WriteUpActionView(self, writeup_id),
            )
        except discord.HTTPException:
            pass
        await interaction.response.send_message(f"✅ `{writeup_id}` marked as resolved.", ephemeral=True)

    async def add_strike(self, interaction: discord.Interaction, writeup_id: str):
        if not writeup_id:
            await interaction.response.send_message("Could not determine write-up ID.", ephemeral=True)
            return
        data        = self._get_writeups()
        entry       = data["entries"].get(writeup_id)
        if not entry:
            await interaction.response.send_message(f"Write-up `{writeup_id}` not found.", ephemeral=True)
            return
        strikes     = self._get_strikes()
        member_name = entry["member_name"]
        strikes[member_name]   = strikes.get(member_name, 0) + 1
        self._set_strikes(strikes)
        entry["strike_count"]  = strikes[member_name]
        entry["status"]        = "Strike Added"
        data["entries"][writeup_id] = entry
        self._set_writeups(data)
        try:
            await interaction.message.edit(
                embed = self._build_embed(entry, COLOR_DANGER),
                view  = WriteUpActionView(self, writeup_id),
            )
        except discord.HTTPException:
            pass
        if strikes[member_name] >= STRIKE_THRESHOLD and interaction.guild:
            await self._threshold_alert(interaction.guild, entry, strikes[member_name])
        await interaction.response.send_message(
            f"⚠️ Strike added to **{member_name}**. Total strikes: **{strikes[member_name]}**.",
            ephemeral=True,
        )

    async def delete_writeup(self, interaction: discord.Interaction, writeup_id: str):
        if not writeup_id:
            await interaction.response.send_message("Could not determine write-up ID.", ephemeral=True)
            return
        data = self._get_writeups()
        entry = data["entries"].pop(writeup_id, None)
        if not entry:
            await interaction.response.send_message(f"Write-up `{writeup_id}` not found.", ephemeral=True)
            return
        self._set_writeups(data)
        try:
            await interaction.message.delete()
        except discord.HTTPException:
            pass
        await interaction.response.send_message(f"🗑️ `{writeup_id}` deleted.", ephemeral=True)

    async def remove_by_id(self, interaction: discord.Interaction, writeup_id: str, removal_reason: str):
        data  = self._get_writeups()
        entry = data["entries"].get(writeup_id)
        if not entry:
            await interaction.response.send_message(f"Write-up ID `{writeup_id}` not found.", ephemeral=True)
            return
        entry["status"]         = "Removed"
        entry["removed_by"]     = interaction.user.mention
        entry["removal_reason"] = removal_reason
        entry["removed_at"]     = _utcnow().isoformat()
        data["entries"][writeup_id] = entry
        self._set_writeups(data)

        ch = interaction.guild.get_channel(WRITEUP_CHANNEL_ID) if interaction.guild else None
        if ch and entry.get("message_id"):
            try:
                msg   = await ch.fetch_message(entry["message_id"])
                embed = self._build_embed(entry, COLOR_MUTED)
                await msg.edit(embed=embed, view=WriteUpActionView(self, writeup_id))
            except discord.HTTPException:
                pass

        await interaction.response.send_message(f"✅ `{writeup_id}` marked as removed.", ephemeral=True)

    # =========================================================
    # PREFIX COMMANDS
    # =========================================================

    @commands.command(name="postwriteuppanel")
    @commands.has_permissions(manage_guild=True)
    async def post_writeup_panel(self, ctx: commands.Context):
        """Post the write-up hub panel in the manager hub channel."""
        channel = ctx.guild.get_channel(MANAGER_HUB_CHANNEL_ID)
        if channel is None:
            await ctx.send("❌ Manager hub channel not found.", delete_after=8)
            return
        await channel.send(embed=self._build_panel_embed(), view=ManagerWriteUpPanel(self))
        await ctx.send("✅ Write-up panel posted.", delete_after=6)
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="writeuphistory")
    @commands.has_permissions(manage_guild=True)
    async def writeup_history(self, ctx: commands.Context, *, member_name: str):
        """View write-up history for a member.  Usage: !writeuphistory Member Name"""
        data    = self._get_writeups()
        strikes = self._get_strikes()
        entries: List[Dict[str, Any]] = sorted(
            [e for e in data["entries"].values()
             if e["member_name"].lower() == member_name.lower()],
            key=lambda x: x["created_at"],
            reverse=True,
        )[:10]

        if not entries:
            await ctx.send(f"No write-up history found for **{member_name}**.", delete_after=10)
            return

        embed = discord.Embed(
            title = f"📚 Write-Up History  •  {member_name}",
            color = COLOR_WARNING,
        )
        lines = [
            f"**{e['writeup_id']}** — {e['writeup_type']} — `{e['status']}` — {e['date']}"
            for e in entries
        ]
        embed.add_field(name="Recent Entries (up to 10)", value="\n".join(lines), inline=False)
        embed.add_field(name="⚠️ Total Strikes", value=str(strikes.get(member_name, 0)), inline=True)
        embed.set_footer(text="Different Meets • Write-Up History")
        await ctx.send(embed=embed)

    @commands.command(name="writeupstats")
    @commands.has_permissions(manage_guild=True)
    async def writeup_stats(self, ctx: commands.Context):
        """Show overall write-up system stats."""
        data     = self._get_writeups()
        total    = len(data["entries"])
        active   = sum(1 for e in data["entries"].values() if e["status"] == "Active")
        resolved = sum(1 for e in data["entries"].values() if e["status"] == "Resolved")
        removed  = sum(1 for e in data["entries"].values() if e["status"] == "Removed")
        strikes  = self._get_strikes()
        flagged  = sum(1 for v in strikes.values() if v >= STRIKE_THRESHOLD)

        embed = discord.Embed(title="📊 DIFF Write-Up Stats", color=COLOR_PRIMARY)
        embed.add_field(name="📁 Total Entries",   value=str(total),    inline=True)
        embed.add_field(name="🔴 Active",          value=str(active),   inline=True)
        embed.add_field(name="✅ Resolved",         value=str(resolved), inline=True)
        embed.add_field(name="🗑️ Removed",         value=str(removed),  inline=True)
        embed.add_field(name="🚨 Members Flagged", value=str(flagged),  inline=True)
        embed.add_field(name="⚠️ Strike Threshold", value=str(STRIKE_THRESHOLD), inline=True)
        embed.set_footer(text="Different Meets • Manager Write-Up Stats")
        await ctx.send(embed=embed)

    @commands.command(name="writeupresetstrikes")
    @commands.has_permissions(administrator=True)
    async def reset_strikes(self, ctx: commands.Context, *, member_name: str):
        """Reset strike count for a member.  Usage: !writeupresetstrikes Member Name"""
        strikes = self._get_strikes()
        if member_name not in strikes:
            await ctx.send(f"No strikes on record for **{member_name}**.", delete_after=8)
            return
        strikes.pop(member_name)
        self._set_strikes(strikes)
        await ctx.send(f"✅ Strikes reset for **{member_name}**.", delete_after=8)
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="writeuphelp")
    @commands.has_permissions(manage_guild=True)
    async def writeup_help(self, ctx: commands.Context):
        """Show all write-up system commands."""
        embed = discord.Embed(title="📋 Write-Up System Commands", color=COLOR_PRIMARY)
        embed.add_field(
            name  = "Panel",
            value = "`!postwriteuppanel` — Post the write-up hub in the manager hub channel",
            inline= False,
        )
        embed.add_field(
            name  = "Lookup",
            value = (
                "`!writeuphistory <name>` — View a member's write-up history\n"
                "`!writeupstats` — System-wide stats\n"
            ),
            inline= False,
        )
        embed.add_field(
            name  = "Management",
            value = "`!writeupresetstrikes <name>` — Clear a member's strike count *(Admin only)*",
            inline= False,
        )
        embed.add_field(
            name  = "Panel Actions (dropdown)",
            value = (
                "• 📝 Member Write-Up\n"
                "• 🏁 Host Write-Up\n"
                "• ⚠️ Warning Notice\n"
                "• 🚨 Strike Entry\n"
                "• 🗑️ Remove Write-Up by ID\n"
            ),
            inline= False,
        )
        embed.add_field(
            name  = "Entry Buttons",
            value = "Each posted entry has: ✅ Mark Resolved  |  ⚠️ Add Strike  |  🗑️ Delete Entry",
            inline= False,
        )
        embed.set_footer(text="Different Meets • Manager Write-Up System")
        await ctx.send(embed=embed)


# =========================================================
# SETUP
# =========================================================

async def setup(bot: commands.Bot):
    await bot.add_cog(ManagerWriteUpSystem(bot))
