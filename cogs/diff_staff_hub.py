"""
DIFF Staff Hub — Unified staff control panel.
Merges all staff panels into one message with two dropdowns:
  • 📊 View a dashboard  (read-only info sections)
  • ⚙️ Open a staff tool (action sections with buttons)
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Optional

import discord
from discord.ext import commands

STAFF_DASHBOARD_CHANNEL_ID = 1485273802391814224

STAFF_ROLE_IDS: set[int] = {
    850391095845584937,   # Leader
    850391378559238235,   # Co-Leader
    990011447193006101,   # Manager
}

HUB_PANEL_TAG   = "DIFF_STAFF_HUB_V1"
DATA_DIR        = "diff_data"
APPS_FILE       = "diff_applications_full.json"
COOLDOWN_FILE   = os.path.join(DATA_DIR, "diff_reapply_cooldowns.json")
MEMBER_DB_FILE  = os.path.join(DATA_DIR, "diff_member_database.json")
ACTIVITY_FILE   = os.path.join(DATA_DIR, "diff_activity_stats.json")


def _is_staff(member: discord.Member) -> bool:
    return member.guild_permissions.administrator or any(r.id in STAFF_ROLE_IDS for r in member.roles)


def _load(path: str, default=None):
    if default is None:
        default = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Local embed builders for info dashboards ──────────────────

def _build_recruitment_embed() -> discord.Embed:
    cooldowns = _load(COOLDOWN_FILE)
    members   = _load(MEMBER_DB_FILE)
    apps      = _load(APPS_FILE, {"applications": {}}).get("applications", {})
    now_dt    = datetime.utcnow()

    active_cds = 0
    for e in cooldowns.values():
        try:
            if datetime.fromisoformat(e.get("expires_at", "")) > now_dt:
                active_cds += 1
        except Exception:
            pass

    embed = discord.Embed(
        title="📊 DIFF Staff Recruitment Dashboard",
        description="Live snapshot of the DIFF application system.",
        color=discord.Color.blurple(),
        timestamp=_utcnow(),
    )
    embed.add_field(name="Total Applications", value=str(len(apps)),                                                          inline=True)
    embed.add_field(name="Pending",            value=str(sum(1 for a in apps.values() if a.get("status") == "Pending")),      inline=True)
    embed.add_field(name="Approved",           value=str(sum(1 for a in apps.values() if a.get("status") == "Approved")),     inline=True)
    embed.add_field(name="Denied",             value=str(sum(1 for a in apps.values() if a.get("status") == "Denied")),       inline=True)
    embed.add_field(name="Timed Out",          value=str(sum(1 for a in apps.values() if a.get("status") == "Timed Out")),    inline=True)
    embed.add_field(name="Active Cooldowns",   value=str(active_cds),                                                         inline=True)
    embed.add_field(name="Members Logged",     value=str(len(members)),                                                       inline=True)
    embed.set_footer(text="Different Meets • Staff Hub")
    return embed


def _build_activity_embed(guild: Optional[discord.Guild]) -> discord.Embed:
    data    = _load(ACTIVITY_FILE, {"members": {}})
    members = data.get("members", {})
    ranked  = sorted(members.items(), key=lambda x: (x[1].get("attended", 0), x[1].get("hosted", 0)), reverse=True)
    medals  = ["🥇", "🥈", "🥉"]

    lb_lines, watch_lines, penalty_lines = [], [], []
    for idx, (uid, stats) in enumerate(ranked[:5], start=1):
        m    = guild.get_member(int(uid)) if guild else None
        name = m.mention if m else f"<@{uid}>"
        pfx  = medals[idx - 1] if idx <= 3 else f"{idx}."
        lb_lines.append(f"{pfx} {name} — {stats.get('attended', 0)} att / {stats.get('hosted', 0)} hosted")

    for uid, stats in ranked:
        m    = guild.get_member(int(uid)) if guild else None
        name = m.mention if m else f"<@{uid}>"
        if stats.get("attended", 0) >= 5 and stats.get("no_shows", 0) <= 1:
            watch_lines.append(f"{name} — {stats.get('attended', 0)} att / {stats.get('hosted', 0)} hosted")
        if stats.get("no_shows", 0) > 0 or stats.get("penalty_points", 0) > 0:
            penalty_lines.append(f"{name} — {stats.get('no_shows', 0)} no-shows / {stats.get('penalty_points', 0)} pts")
        if len(watch_lines) >= 5 and len(penalty_lines) >= 5:
            break

    embed = discord.Embed(
        title="📈 DIFF Activity Dashboard",
        description="Live overview of attendance, leaderboard, and promotion watch.",
        color=discord.Color.blue(),
        timestamp=_utcnow(),
    )
    embed.add_field(name="🏆 Top Activity",    value="\n".join(lb_lines[:5])      or "No data yet.", inline=False)
    embed.add_field(name="📈 Promotion Watch", value="\n".join(watch_lines[:5])   or "None yet.",    inline=False)
    embed.add_field(name="⚠️ Penalty Watch",   value="\n".join(penalty_lines[:5]) or "None recorded.", inline=False)
    embed.set_footer(text="Different Meets • Staff Hub")
    return embed


# ── Info dropdown ────────────────────────────────────────────

class StaffInfoSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="📊 View a dashboard...",
            min_values=1, max_values=1,
            custom_id="diff_staff_hub_info_v1",
            options=[
                discord.SelectOption(label="📊 Recruitment Dashboard", value="recruitment",
                                     description="Application counts, cooldowns, members logged"),
                discord.SelectOption(label="📈 Activity Dashboard",     value="activity",
                                     description="Attendance, promotion watch, penalty watch"),
                discord.SelectOption(label="📈 Manager Performance",    value="performance",
                                     description="Manager leaderboard and scoring breakdown"),
                discord.SelectOption(label="🏆 Manager Season",         value="season",
                                     description="Current season standings and promotion threshold"),
                discord.SelectOption(label="🌐 Server Statistics",      value="serverstats",
                                     description="Live member count, boosts, channels, roles"),
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        if not isinstance(interaction.user, discord.Member) or not _is_staff(interaction.user):
            return await interaction.response.send_message("Staff only.", ephemeral=True)

        val = self.values[0]
        bot = interaction.client

        try:
            if val == "recruitment":
                embed = _build_recruitment_embed()
                return await interaction.response.send_message(embed=embed, ephemeral=True)

            if val == "activity":
                embed = _build_activity_embed(interaction.guild)
                return await interaction.response.send_message(embed=embed, ephemeral=True)

            if val == "performance":
                cog = bot.cogs.get("ManagerPerformance")
                if not cog:
                    return await interaction.response.send_message("Manager Performance system not loaded.", ephemeral=True)
                return await interaction.response.send_message(embed=cog.build_leaderboard_embed(), ephemeral=True)

            if val == "season":
                cog = bot.cogs.get("ManagerSeasonSystem")
                if not cog:
                    return await interaction.response.send_message("Manager Season system not loaded.", ephemeral=True)
                return await interaction.response.send_message(embed=cog.build_main_embed(), ephemeral=True)

            if val == "serverstats":
                cog = bot.cogs.get("ServerStatsCog")
                if not cog or not interaction.guild:
                    return await interaction.response.send_message("Server Stats system not loaded.", ephemeral=True)
                return await interaction.response.send_message(embed=cog._build_embed(interaction.guild), ephemeral=True)

        except Exception as e:
            print(f"[StaffHub/info] Error: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
                else:
                    await interaction.followup.send("Something went wrong.", ephemeral=True)
            except Exception:
                pass


# ── Action tools dropdown ────────────────────────────────────

class StaffToolSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="⚙️ Open a staff tool...",
            min_values=1, max_values=1,
            custom_id="diff_staff_hub_tool_v1",
            options=[
                discord.SelectOption(label="🛡️ Moderation Tools", value="moderation",
                                     description="Member profiles, punishments, strikes, flagged hosts"),
                discord.SelectOption(label="📝 Write-Up Hub",      value="writeups",
                                     description="Issue member/host write-ups, warnings, and strikes"),
                discord.SelectOption(label="📁 Case Management",   value="cases",
                                     description="Create and manage official staff case files"),
                discord.SelectOption(label="🧠 Manager Hub",       value="managerhub",
                                     description="Manager sections, performance logging, crew logos"),
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        if not isinstance(interaction.user, discord.Member) or not _is_staff(interaction.user):
            return await interaction.response.send_message("Staff only.", ephemeral=True)

        val = self.values[0]
        bot = interaction.client

        try:
            if val == "moderation":
                cog = bot.cogs.get("StaffDashboardSystem")
                if not cog:
                    return await interaction.response.send_message("Staff Dashboard system not loaded.", ephemeral=True)
                from cogs.diff_staff_dashboard import StaffDashboardView
                return await interaction.response.send_message(
                    embed=cog._dashboard_embed(), view=StaffDashboardView(cog), ephemeral=True
                )

            if val == "writeups":
                cog = bot.cogs.get("ManagerWriteUpSystem")
                if not cog:
                    return await interaction.response.send_message("Write-Up system not loaded.", ephemeral=True)
                from cogs.diff_manager_writeups import ManagerWriteUpPanel
                return await interaction.response.send_message(
                    embed=cog._build_panel_embed(), view=ManagerWriteUpPanel(cog), ephemeral=True
                )

            if val == "cases":
                cog = bot.cogs.get("CaseSystem")
                if not cog:
                    return await interaction.response.send_message("Case Management system not loaded.", ephemeral=True)
                from cogs.diff_case_system import CasePanelView
                return await interaction.response.send_message(
                    embed=cog.build_case_panel_embed(), view=CasePanelView(cog), ephemeral=True
                )

            if val == "managerhub":
                cog = bot.cogs.get("ManagerHubSystem")
                if not cog:
                    return await interaction.response.send_message("Manager Hub system not loaded.", ephemeral=True)
                from cogs.diff_manager_hub import ManagerHubView
                return await interaction.response.send_message(
                    embed=cog.build_main_embed(), view=ManagerHubView(cog), ephemeral=True
                )

        except Exception as e:
            print(f"[StaffHub/tool] Error: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
                else:
                    await interaction.followup.send("Something went wrong.", ephemeral=True)
            except Exception:
                pass


# ── Combined view ────────────────────────────────────────────

class StaffHubView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(StaffInfoSelect())
        self.add_item(StaffToolSelect())


# ── Cog ─────────────────────────────────────────────────────

class StaffHubCog(commands.Cog, name="StaffHubCog"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(StaffHubView())

    async def cog_load(self):
        print("[StaffHub] Cog loaded — unified staff panel ready.")

    def _build_hub_embed(self) -> discord.Embed:
        DIFF_LOGO_URL = (
            "https://media.discordapp.net/attachments/1107375326625005719/"
            "1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm="
            "2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
            "&=&format=webp&quality=lossless&width=1376&height=917"
        )
        embed = discord.Embed(
            title="🎮 DIFF Staff Control Panel",
            description=(
                "Welcome to the unified DIFF staff hub. Everything you need is in one place.\n"
                "Select from either dropdown below — your response is **only visible to you**."
            ),
            color=0x5865F2,
        )
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.add_field(
            name="📊 View a Dashboard",
            value=(
                "› **Recruitment** — application counts & cooldowns\n"
                "› **Activity** — attendance, promotions & penalties\n"
                "› **Manager Performance** — leaderboard & scores\n"
                "› **Season Standings** — current season rankings\n"
                "› **Server Statistics** — live member & boost counts"
            ),
            inline=False,
        )
        embed.add_field(
            name="⚙️ Open a Staff Tool",
            value=(
                "› **Moderation** — member profiles, strikes, flagged hosts\n"
                "› **Write-Ups** — issue write-ups, warnings & strikes\n"
                "› **Case Management** — create & manage case files\n"
                "› **Manager Hub** — full manager control panel"
            ),
            inline=False,
        )
        embed.set_footer(text="Different Meets • Staff Dashboard  |  Responses are private")
        return embed

    @commands.command(name="staffhub")
    async def post_staff_hub(self, ctx: commands.Context):
        if not isinstance(ctx.author, discord.Member) or not _is_staff(ctx.author):
            return
        try:
            await ctx.message.delete()
        except Exception:
            pass
        channel = self.bot.get_channel(STAFF_DASHBOARD_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            await ctx.send("Staff dashboard channel not found.", delete_after=8)
            return
        async for msg in channel.history(limit=50):
            if msg.author.id == self.bot.user.id:
                for e in msg.embeds:
                    if e.title == "🎮 DIFF Staff Control Panel":
                        try:
                            await msg.delete()
                        except Exception:
                            pass
                        break
        await channel.send(embed=self._build_hub_embed(), view=StaffHubView())
        await ctx.send("✅ Staff hub posted.", delete_after=5)


async def setup(bot: commands.Bot):
    await bot.add_cog(StaffHubCog(bot))
