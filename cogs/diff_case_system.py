from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import discord
from discord.ext import commands

GUILD_ID              = 850386896509337710
CASE_PANEL_CHANNEL_ID = 1485273802391814224   # Manager Hub
CASE_LOG_CHANNEL_ID   = 1485265848099799163   # Staff Logs
CASE_ARCHIVE_CHANNEL_ID = 1485265848099799163 # Staff Logs (same)

LEADER_ROLE_ID    = 850391095845584937
CO_LEADER_ROLE_ID = 850391378559238235
MANAGER_ROLE_ID   = 990011447193006101

DATA_DIR   = "diff_data"
CASES_FILE = os.path.join(DATA_DIR, "case_system.json")

COLOR_PRIMARY = 0x1F6FEB
COLOR_SUCCESS = 0x2ECC71
COLOR_WARNING = 0xF39C12
COLOR_DANGER  = 0xE74C3C
COLOR_MUTED   = 0x95A5A6

PANEL_TAG = "DIFF_CASE_PANEL_V1"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def load_json(path: str, default):
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=4)
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path: str, data) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def has_staff_access(member: discord.Member) -> bool:
    if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
        return True
    role_ids = {role.id for role in member.roles}
    return bool(role_ids & {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID})


def _parse_case_id_from_embed(message: discord.Message) -> Optional[str]:
    """Pull case ID out of the embed title (e.g. '🧾 DIFF Case File • CASE-0003')."""
    if not message or not message.embeds:
        return None
    title = message.embeds[0].title or ""
    if "•" in title:
        return title.split("•")[-1].strip()
    return None


# ---------------------------------------------------------------------------
# Modals
# ---------------------------------------------------------------------------

class CreateCaseModal(discord.ui.Modal, title="Create DIFF Case File"):
    target_name = discord.ui.TextInput(
        label="Target Member / Host",
        placeholder="Discord name, mention text, or PSN",
        max_length=100,
        required=True,
    )
    case_type = discord.ui.TextInput(
        label="Case Type",
        placeholder="Moderation, Host Review, Appeal Review, Conduct, etc.",
        max_length=100,
        required=True,
    )
    summary = discord.ui.TextInput(
        label="Case Summary",
        placeholder="Brief overview of the situation.",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=True,
    )
    linked_ids = discord.ui.TextInput(
        label="Linked IDs",
        placeholder="WU-0001, APL-0002, STRIKE-1, etc.",
        max_length=400,
        required=False,
    )
    priority = discord.ui.TextInput(
        label="Priority",
        placeholder="Low / Medium / High / Critical",
        max_length=20,
        required=True,
    )

    def __init__(self, cog: "CaseSystem"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.create_case(
            interaction=interaction,
            target_name=str(self.target_name).strip(),
            case_type=str(self.case_type).strip(),
            summary=str(self.summary).strip(),
            linked_ids=str(self.linked_ids).strip() or "None",
            priority=str(self.priority).strip(),
        )


class CaseManageModal(discord.ui.Modal):
    def __init__(self, cog: "CaseSystem", case_id: str, action: str):
        super().__init__(title=f"{action} • {case_id}")
        self.cog = cog
        self.case_id = case_id
        self.action = action
        self.note = discord.ui.TextInput(
            label="Staff Note",
            placeholder="Explain the update or action taken.",
            style=discord.TextStyle.paragraph,
            max_length=1000,
            required=True,
        )
        self.add_item(self.note)

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.handle_case_action(
            interaction=interaction,
            case_id=self.case_id,
            action=self.action,
            note=str(self.note).strip(),
        )


class AssignCaseModal(discord.ui.Modal):
    def __init__(self, cog: "CaseSystem", case_id: str):
        super().__init__(title=f"Assign Owner • {case_id}")
        self.cog = cog
        self.case_id = case_id
        self.user_id_field = discord.ui.TextInput(
            label="Staff User ID",
            placeholder="Enter the Discord user ID of the staff member",
            max_length=30,
            required=True,
        )
        self.note_field = discord.ui.TextInput(
            label="Assignment Note",
            placeholder="Optional context for the assignment.",
            style=discord.TextStyle.paragraph,
            max_length=500,
            required=False,
        )
        self.add_item(self.user_id_field)
        self.add_item(self.note_field)

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.assign_case_owner(
            interaction=interaction,
            case_id=self.case_id,
            user_id_text=str(self.user_id_field).strip(),
            note=str(self.note_field).strip() or "No assignment note provided.",
        )


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

class _AddNoteBtn(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Add Note", style=discord.ButtonStyle.primary, emoji="📝", custom_id="diff_case_add_note")
    async def callback(self, interaction: discord.Interaction):
        if not has_staff_access(interaction.user):
            return await interaction.response.send_message("You do not have permission to manage cases.", ephemeral=True)
        case_id = self.view._get_case_id(interaction)
        if not case_id:
            return await interaction.response.send_message("Could not determine case ID.", ephemeral=True)
        await interaction.response.send_modal(CaseManageModal(self.view.cog, case_id, "Add Note"))

class _AssignOwnerBtn(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Assign Owner", style=discord.ButtonStyle.secondary, emoji="👤", custom_id="diff_case_assign_owner")
    async def callback(self, interaction: discord.Interaction):
        if not has_staff_access(interaction.user):
            return await interaction.response.send_message("You do not have permission to manage cases.", ephemeral=True)
        case_id = self.view._get_case_id(interaction)
        if not case_id:
            return await interaction.response.send_message("Could not determine case ID.", ephemeral=True)
        await interaction.response.send_modal(AssignCaseModal(self.view.cog, case_id))

class _CloseCaseBtn(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Close Case", style=discord.ButtonStyle.success, emoji="✅", custom_id="diff_case_close")
    async def callback(self, interaction: discord.Interaction):
        if not has_staff_access(interaction.user):
            return await interaction.response.send_message("You do not have permission to manage cases.", ephemeral=True)
        case_id = self.view._get_case_id(interaction)
        if not case_id:
            return await interaction.response.send_message("Could not determine case ID.", ephemeral=True)
        await interaction.response.send_modal(CaseManageModal(self.view.cog, case_id, "Close Case"))

class _ReopenCaseBtn(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Reopen Case", style=discord.ButtonStyle.secondary, emoji="🔄", custom_id="diff_case_reopen")
    async def callback(self, interaction: discord.Interaction):
        if not has_staff_access(interaction.user):
            return await interaction.response.send_message("You do not have permission to manage cases.", ephemeral=True)
        case_id = self.view._get_case_id(interaction)
        if not case_id:
            return await interaction.response.send_message("Could not determine case ID.", ephemeral=True)
        await interaction.response.send_modal(CaseManageModal(self.view.cog, case_id, "Reopen Case"))

class _ArchiveCaseBtn(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Archive Case", style=discord.ButtonStyle.danger, emoji="📦", custom_id="diff_case_archive")
    async def callback(self, interaction: discord.Interaction):
        if not has_staff_access(interaction.user):
            return await interaction.response.send_message("You do not have permission to manage cases.", ephemeral=True)
        case_id = self.view._get_case_id(interaction)
        if not case_id:
            return await interaction.response.send_message("Could not determine case ID.", ephemeral=True)
        await interaction.response.send_modal(CaseManageModal(self.view.cog, case_id, "Archive Case"))


class CaseActionView(discord.ui.View):
    """Persistent view attached to every case file embed."""
    def __init__(self, cog: "CaseSystem"):
        super().__init__(timeout=None)
        self.cog = cog
        self.add_item(_AddNoteBtn())
        self.add_item(_AssignOwnerBtn())
        self.add_item(_CloseCaseBtn())
        self.add_item(_ReopenCaseBtn())
        self.add_item(_ArchiveCaseBtn())

    def _get_case_id(self, interaction: discord.Interaction) -> Optional[str]:
        return _parse_case_id_from_embed(interaction.message)


class _CreateCaseFileBtn(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Create Case File", style=discord.ButtonStyle.primary, emoji="🧾", custom_id="diff_create_case_file")
    async def callback(self, interaction: discord.Interaction):
        if not has_staff_access(interaction.user):
            return await interaction.response.send_message("You do not have permission to create cases.", ephemeral=True)
        await interaction.response.send_modal(CreateCaseModal(self.view.cog))


class CasePanelView(discord.ui.View):
    def __init__(self, cog: "CaseSystem"):
        super().__init__(timeout=None)
        self.cog = cog
        self.add_item(_CreateCaseFileBtn())


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------

class CaseSystem(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(CasePanelView(self))
        self.bot.add_view(CaseActionView(self))

    @commands.Cog.listener()
    async def on_ready(self):
        print("[CaseSystem] Cog ready.")

    # ------------------------------------------------------------------
    # Data helpers
    # ------------------------------------------------------------------

    def get_cases(self) -> Dict[str, Any]:
        return load_json(CASES_FILE, {"counter": 0, "entries": {}})

    def save_cases(self, data: Dict[str, Any]) -> None:
        save_json(CASES_FILE, data)

    def next_case_id(self) -> str:
        data = self.get_cases()
        data["counter"] += 1
        self.save_cases(data)
        return f"CASE-{data['counter']:04d}"

    # ------------------------------------------------------------------
    # Embed builders
    # ------------------------------------------------------------------

    def build_case_embed(self, case: Dict[str, Any], color: int = COLOR_PRIMARY) -> discord.Embed:
        embed = discord.Embed(
            title=f"🧾 DIFF Case File • {case['case_id']}",
            description=case["summary"],
            color=color,
            timestamp=utcnow(),
        )
        embed.add_field(name="Target",      value=case["target_name"],          inline=True)
        embed.add_field(name="Case Type",   value=case["case_type"],             inline=True)
        embed.add_field(name="Priority",    value=case["priority"],              inline=True)
        embed.add_field(name="Status",      value=case["status"],                inline=True)
        embed.add_field(name="Created By",  value=case["created_by"],            inline=True)
        embed.add_field(name="Owner",       value=case["owner"] or "Unassigned", inline=True)
        embed.add_field(name="Linked IDs",  value=case["linked_ids"],            inline=False)

        history = case.get("history", [])
        if history:
            last_entries = history[-5:]
            history_text = "\n".join(
                f"• {e['timestamp'][:19]} — {e['action']} by {e['by']}"
                for e in last_entries
            )
            embed.add_field(name="Recent Case History", value=history_text[:1024], inline=False)

        embed.set_footer(text="Different Meets • Case System")
        return embed

    def build_case_panel_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🧾 DIFF Case Management Hub",
            description=(
                "Use this panel to create and manage official staff case files.\n\n"
                "**Case system uses:**\n"
                "• Link write-ups to one case\n"
                "• Link appeals to one case\n"
                "• Assign owners\n"
                "• Track actions and history\n"
                "• Close, reopen, or archive cases"
            ),
            color=COLOR_PRIMARY,
        )
        embed.add_field(
            name="Why Use Cases?",
            value=(
                "Cases keep moderation more organized by grouping related actions, "
                "evidence, and appeal outcomes into one place."
            ),
            inline=False,
        )
        embed.add_field(
            name="📋 Staff Commands",
            value=(
                "`!postcasepanel` — Post / refresh this panel\n"
                "`!caseinfo <CASE-0001>` — View full details of a case\n"
                "`!opencases` — List all currently open cases\n"
                "`!casehistory <CASE-0001>` — View archived case history"
            ),
            inline=False,
        )
        embed.set_footer(text=PANEL_TAG)
        return embed

    # ------------------------------------------------------------------
    # Panel auto-post
    # ------------------------------------------------------------------

    async def _post_or_refresh_panel(self):
        guild = self.bot.get_guild(GUILD_ID)
        if guild is None:
            return
        channel = guild.get_channel(CASE_PANEL_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            return

        embed = self.build_case_panel_embed()
        existing = None

        async for msg in channel.history(limit=50):
            if msg.author.id == self.bot.user.id and msg.embeds:
                footer = msg.embeds[0].footer.text if msg.embeds[0].footer else ""
                if footer == PANEL_TAG:
                    if existing is None:
                        existing = msg
                    else:
                        try:
                            await msg.delete()
                        except Exception:
                            pass

        if existing:
            try:
                await existing.edit(content=None, embed=embed, view=CasePanelView(self))
            except Exception:
                pass
        else:
            await channel.send(embed=embed, view=CasePanelView(self))

    # ------------------------------------------------------------------
    # Core case logic
    # ------------------------------------------------------------------

    async def create_case(
        self,
        interaction: discord.Interaction,
        target_name: str,
        case_type: str,
        summary: str,
        linked_ids: str,
        priority: str,
    ):
        if not interaction.guild or interaction.guild.id != GUILD_ID:
            await interaction.response.send_message("This system is not configured for this server.", ephemeral=True)
            return

        case_id = self.next_case_id()
        entry: Dict[str, Any] = {
            "case_id":        case_id,
            "target_name":    target_name,
            "case_type":      case_type,
            "summary":        summary,
            "linked_ids":     linked_ids,
            "priority":       priority,
            "status":         "Open",
            "created_by":     interaction.user.mention,
            "created_by_id":  interaction.user.id,
            "owner":          None,
            "owner_id":       None,
            "created_at":     utcnow().isoformat(),
            "message_id":     None,
            "history": [
                {
                    "action":    "Case Created",
                    "by":        interaction.user.mention,
                    "timestamp": utcnow().isoformat(),
                    "note":      summary,
                }
            ],
        }

        data = self.get_cases()
        data["entries"][case_id] = entry
        self.save_cases(data)

        channel = interaction.guild.get_channel(CASE_LOG_CHANNEL_ID)
        if channel is None:
            await interaction.response.send_message("Case log channel not found.", ephemeral=True)
            return

        embed = self.build_case_embed(entry, COLOR_PRIMARY)
        msg = await channel.send(embed=embed, view=CaseActionView(self))

        data = self.get_cases()
        data["entries"][case_id]["message_id"] = msg.id
        self.save_cases(data)

        await interaction.response.send_message(f"✅ Case file **{case_id}** created.", ephemeral=True)

    async def handle_case_action(
        self,
        interaction: discord.Interaction,
        case_id: str,
        action: str,
        note: str,
    ):
        data = self.get_cases()
        case = data["entries"].get(case_id)
        if not case:
            await interaction.response.send_message("Case not found.", ephemeral=True)
            return

        if action == "Close Case":
            case["status"] = "Closed"
            color = COLOR_SUCCESS
        elif action == "Reopen Case":
            case["status"] = "Open"
            color = COLOR_WARNING
        elif action == "Archive Case":
            case["status"] = "Archived"
            color = COLOR_MUTED
        else:
            color = COLOR_PRIMARY

        case["history"].append(
            {
                "action":    action,
                "by":        interaction.user.mention,
                "timestamp": utcnow().isoformat(),
                "note":      note,
            }
        )
        data["entries"][case_id] = case
        self.save_cases(data)

        await self.refresh_case_message(interaction.guild, case, color=color, extra_note=note)

        if action == "Archive Case":
            await self.send_case_archive(interaction.guild, case, note)

        await interaction.response.send_message(f"✅ {action} completed for **{case_id}**.", ephemeral=True)

    async def assign_case_owner(
        self,
        interaction: discord.Interaction,
        case_id: str,
        user_id_text: str,
        note: str,
    ):
        if not interaction.guild:
            await interaction.response.send_message("This can only be used in the server.", ephemeral=True)
            return
        try:
            owner_id = int(user_id_text)
        except ValueError:
            await interaction.response.send_message("Invalid user ID.", ephemeral=True)
            return

        owner = interaction.guild.get_member(owner_id)
        if owner is None:
            await interaction.response.send_message("That staff member was not found in the server.", ephemeral=True)
            return

        data = self.get_cases()
        case = data["entries"].get(case_id)
        if not case:
            await interaction.response.send_message("Case not found.", ephemeral=True)
            return

        case["owner"]    = owner.mention
        case["owner_id"] = owner.id
        case["history"].append(
            {
                "action":    "Owner Assigned",
                "by":        interaction.user.mention,
                "timestamp": utcnow().isoformat(),
                "note":      f"Assigned to {owner.mention}. {note}",
            }
        )
        data["entries"][case_id] = case
        self.save_cases(data)

        await self.refresh_case_message(interaction.guild, case, color=COLOR_PRIMARY, extra_note=note)
        await interaction.response.send_message(f"✅ **{case_id}** assigned to {owner.mention}.", ephemeral=True)

    # ------------------------------------------------------------------
    # Message helpers
    # ------------------------------------------------------------------

    async def refresh_case_message(
        self,
        guild: discord.Guild,
        case: Dict[str, Any],
        color: int,
        extra_note: Optional[str] = None,
    ):
        channel = guild.get_channel(CASE_LOG_CHANNEL_ID)
        if channel is None or not case.get("message_id"):
            return
        try:
            msg = await channel.fetch_message(case["message_id"])
        except discord.HTTPException:
            return

        embed = self.build_case_embed(case, color=color)
        if extra_note:
            embed.add_field(name="Latest Staff Note", value=extra_note[:1024], inline=False)

        try:
            await msg.edit(embed=embed, view=CaseActionView(self))
        except discord.HTTPException:
            pass

    async def send_case_archive(self, guild: discord.Guild, case: Dict[str, Any], note: str):
        channel = guild.get_channel(CASE_ARCHIVE_CHANNEL_ID)
        if channel is None:
            return
        embed = self.build_case_embed(case, color=COLOR_MUTED)
        embed.add_field(name="Archive Note", value=note[:1024], inline=False)
        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass

    # ------------------------------------------------------------------
    # Prefix commands
    # ------------------------------------------------------------------

    @commands.command(name="postcasepanel")
    @commands.has_permissions(manage_guild=True)
    async def post_case_panel(self, ctx: commands.Context):
        """Force-posts or refreshes the Case Management panel. Usage: !postcasepanel"""
        try:
            await ctx.message.delete()
        except Exception:
            pass
        await self._post_or_refresh_panel()
        channel = ctx.guild.get_channel(CASE_PANEL_CHANNEL_ID)
        mention = channel.mention if channel else f"<#{CASE_PANEL_CHANNEL_ID}>"
        await ctx.send(f"✅ Case panel posted/refreshed in {mention}.", delete_after=8)

    @commands.command(name="caseinfo")
    @commands.has_permissions(manage_guild=True)
    async def case_info(self, ctx: commands.Context, case_id: str):
        """Show details for a case. Usage: !caseinfo CASE-0001"""
        data = self.get_cases()
        case = data["entries"].get(case_id.upper())
        if not case:
            await ctx.send("Case not found.")
            return
        color_map = {"Closed": COLOR_SUCCESS, "Archived": COLOR_MUTED, "Open": COLOR_WARNING}
        color = color_map.get(case["status"], COLOR_PRIMARY)
        await ctx.send(embed=self.build_case_embed(case, color=color))

    @commands.command(name="opencases")
    @commands.has_permissions(manage_guild=True)
    async def open_cases(self, ctx: commands.Context):
        """List all open cases. Usage: !opencases"""
        data = self.get_cases()
        open_items = [c for c in data["entries"].values() if c["status"] == "Open"]
        if not open_items:
            await ctx.send("No open cases right now.")
            return
        embed = discord.Embed(title="📂 Open Cases", color=COLOR_WARNING)
        lines = [
            f"**{c['case_id']}** — {c['target_name']} — {c['case_type']} — Owner: {c['owner'] or 'Unassigned'}"
            for c in open_items[:15]
        ]
        embed.add_field(name="Current Open Cases", value="\n".join(lines), inline=False)
        embed.set_footer(text="Different Meets • Case System")
        await ctx.send(embed=embed)

    @commands.command(name="casehistory")
    @commands.has_permissions(manage_guild=True)
    async def case_history(self, ctx: commands.Context, case_id: str):
        """Show the full action history for a case. Usage: !casehistory CASE-0001"""
        data = self.get_cases()
        case = data["entries"].get(case_id.upper())
        if not case:
            await ctx.send("Case not found.")
            return
        history = case.get("history", [])
        if not history:
            await ctx.send("No history exists for that case.")
            return
        embed = discord.Embed(title=f"📜 Case History • {case['case_id']}", color=COLOR_PRIMARY)
        lines = [
            f"**{item['timestamp'][:19]}** — {item['action']} by {item['by']}\n{item['note']}"
            for item in history[-10:]
        ]
        embed.add_field(name="History Log", value="\n\n".join(lines)[:1024], inline=False)
        embed.set_footer(text="Different Meets • Case History")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(CaseSystem(bot))
