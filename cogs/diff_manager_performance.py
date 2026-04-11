from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import discord
from discord.ext import commands

# =========================================================
# CONFIG
# =========================================================

GUILD_ID = 850386896509337710
MANAGER_LEADERBOARD_CHANNEL_ID = 1485273802391814224

PANEL_TITLE = "📈 DIFF Manager Performance Leaderboard"
PANEL_DESCRIPTION = (
    "Track manager activity, support, and contribution across **Different Meets**.\n\n"
    "This panel shows the current top-performing managers based on recruitment, meet support, "
    "management actions, issue reporting, and warning activity.\n\n"
    "Stats update live — the panel always reflects the latest scores."
)
FOOTER_TEXT = "Different Meets • Manager Performance System"

RECRUITMENT_POINTS    = 3
MEET_SUPPORT_POINTS   = 2
MANAGER_ACTION_POINTS = 2
ISSUE_REPORT_POINTS   = 1
WARNING_FILED_POINTS  = 1

VALID_STATS = {
    "recruitment":       "recruitment",
    "recruit":           "recruitment",
    "r":                 "recruitment",
    "meet_support":      "meet_support",
    "meetsupport":       "meet_support",
    "ms":                "meet_support",
    "manager_actions":   "manager_actions",
    "manageractions":    "manager_actions",
    "actions":           "manager_actions",
    "a":                 "manager_actions",
    "issues_reported":   "issues_reported",
    "issues":            "issues_reported",
    "issue":             "issues_reported",
    "i":                 "issues_reported",
    "warnings_filed":    "warnings_filed",
    "warnings":          "warnings_filed",
    "warning":           "warnings_filed",
    "w":                 "warnings_filed",
}

STAT_LABELS = {
    "recruitment":      ("Recruitment",      RECRUITMENT_POINTS),
    "meet_support":     ("Meet Support",     MEET_SUPPORT_POINTS),
    "manager_actions":  ("Manager Actions",  MANAGER_ACTION_POINTS),
    "issues_reported":  ("Issues Reported",  ISSUE_REPORT_POINTS),
    "warnings_filed":   ("Warnings Filed",   WARNING_FILED_POINTS),
}

DATA_DIR   = Path("diff_data")
STATS_FILE = DATA_DIR / "manager_performance_stats.json"
STATE_FILE = DATA_DIR / "manager_performance_state.json"


# =========================================================
# HELPERS
# =========================================================

def _load(path: Path, default):
    if not path.exists():
        _save(path, default)
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _save(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def _blank_stats(member_id: int, name: str) -> dict:
    return {
        "member_id": member_id,
        "name": name,
        "recruitment": 0,
        "meet_support": 0,
        "manager_actions": 0,
        "issues_reported": 0,
        "warnings_filed": 0,
    }

def _compute_score(stats: dict) -> int:
    return (
        stats.get("recruitment",     0) * RECRUITMENT_POINTS
        + stats.get("meet_support",    0) * MEET_SUPPORT_POINTS
        + stats.get("manager_actions", 0) * MANAGER_ACTION_POINTS
        + stats.get("issues_reported", 0) * ISSUE_REPORT_POINTS
        + stats.get("warnings_filed",  0) * WARNING_FILED_POINTS
    )

def _sorted_managers(managers: dict) -> list:
    rows = list(managers.values())
    for r in rows:
        r["score"] = _compute_score(r)
    rows.sort(
        key=lambda x: (x["score"], x.get("recruitment", 0), x.get("meet_support", 0)),
        reverse=True,
    )
    return rows


# =========================================================
# COG
# =========================================================

class ManagerPerformanceSystem(commands.Cog, name="ManagerPerformance"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        _load(STATS_FILE, {"managers": {}})
        _load(STATE_FILE, {"channel_id": MANAGER_LEADERBOARD_CHANNEL_ID, "message_id": None})

    @commands.Cog.listener()
    async def on_ready(self):
        print("[ManagerPerformance] Cog ready.")
        await self.post_or_refresh_panel()

    # ── embed builders ───────────────────────────────────────

    def build_leaderboard_embed(self) -> discord.Embed:
        data = _load(STATS_FILE, {"managers": {}})
        rows = _sorted_managers(data.get("managers", {}))

        embed = discord.Embed(
            title=PANEL_TITLE,
            description=PANEL_DESCRIPTION,
            color=discord.Color.blurple(),
        )

        if rows:
            medals = ["🥇", "🥈", "🥉"]
            lines = []
            for idx, item in enumerate(rows[:10], start=1):
                prefix = medals[idx - 1] if idx <= 3 else f"**#{idx}**"
                lines.append(
                    f"{prefix} <@{item['member_id']}> — **{item['score']} pts**"
                    f"  `R:{item['recruitment']} MS:{item['meet_support']}"
                    f" A:{item['manager_actions']} I:{item['issues_reported']}"
                    f" W:{item['warnings_filed']}`"
                )
            embed.add_field(name="🏆 Top Managers", value="\n".join(lines), inline=False)
        else:
            embed.add_field(
                name="🏆 Top Managers",
                value="No manager stats have been recorded yet.",
                inline=False,
            )

        embed.add_field(
            name="📊 Scoring System",
            value=(
                f"• Recruitment = **{RECRUITMENT_POINTS} pts**\n"
                f"• Meet Support = **{MEET_SUPPORT_POINTS} pts**\n"
                f"• Manager Actions = **{MANAGER_ACTION_POINTS} pts**\n"
                f"• Issues Reported = **{ISSUE_REPORT_POINTS} pt**\n"
                f"• Warnings Filed = **{WARNING_FILED_POINTS} pt**"
            ),
            inline=False,
        )

        embed.set_footer(text=FOOTER_TEXT)
        return embed

    def build_profile_embed(self, member: discord.Member) -> discord.Embed:
        data  = _load(STATS_FILE, {"managers": {}})
        key   = str(member.id)
        stats = data["managers"].get(key, _blank_stats(member.id, str(member)))
        score = _compute_score(stats)

        rows = _sorted_managers(data.get("managers", {}))
        rank = next((i + 1 for i, r in enumerate(rows) if str(r["member_id"]) == key), None)
        rank_str = f"#{rank}" if rank else "Unranked"

        embed = discord.Embed(
            title=f"📊 Manager Profile  •  {member.display_name}",
            color=discord.Color.green(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="🏅 Rank",            value=rank_str,                          inline=True)
        embed.add_field(name="⭐ Total Score",      value=str(score),                        inline=True)
        embed.add_field(name="\u200b",              value="\u200b",                          inline=True)
        embed.add_field(name="📣 Recruitment",      value=str(stats.get("recruitment",    0)), inline=True)
        embed.add_field(name="🤝 Meet Support",     value=str(stats.get("meet_support",   0)), inline=True)
        embed.add_field(name="⚙️ Manager Actions",  value=str(stats.get("manager_actions",0)), inline=True)
        embed.add_field(name="🔎 Issues Reported",  value=str(stats.get("issues_reported",0)), inline=True)
        embed.add_field(name="⚠️ Warnings Filed",   value=str(stats.get("warnings_filed", 0)), inline=True)
        embed.set_footer(text=FOOTER_TEXT)
        return embed

    # ── panel post/refresh ───────────────────────────────────

    async def post_or_refresh_panel(self):
        state      = _load(STATE_FILE, {"channel_id": MANAGER_LEADERBOARD_CHANNEL_ID, "message_id": None})
        channel_id = state.get("channel_id", MANAGER_LEADERBOARD_CHANNEL_ID)
        message_id = state.get("message_id")

        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception as e:
                print(f"[ManagerPerformance] Could not access channel: {e}")
                return False

        embed = self.build_leaderboard_embed()

        if message_id:
            try:
                msg = await channel.fetch_message(message_id)
                await msg.edit(embed=embed)
                return True
            except Exception:
                pass

        try:
            msg = await channel.send(embed=embed)
            state["message_id"] = msg.id
            state["channel_id"] = channel.id
            _save(STATE_FILE, state)
            return True
        except Exception as e:
            print(f"[ManagerPerformance] Failed to post panel: {e}")
            return False

    # ── stat adjustment helper ───────────────────────────────

    async def _adjust(self, member: discord.Member, **deltas) -> dict:
        data = _load(STATS_FILE, {"managers": {}})
        key  = str(member.id)
        if key not in data["managers"]:
            data["managers"][key] = _blank_stats(member.id, str(member))
        stats = data["managers"][key]
        stats["name"] = str(member)
        for field, delta in deltas.items():
            stats[field] = max(0, stats.get(field, 0) + delta)
        _save(STATS_FILE, data)
        await self.post_or_refresh_panel()
        return stats

    # =========================================================
    # PREFIX COMMANDS
    # =========================================================

    @commands.command(name="managerboard")
    @commands.has_permissions(manage_guild=True)
    async def manager_board(self, ctx: commands.Context):
        """Post or refresh the manager performance leaderboard panel."""
        ok = await self.post_or_refresh_panel()
        msg = "✅ Manager leaderboard refreshed." if ok else "❌ Failed to refresh the leaderboard."
        await ctx.send(msg, delete_after=8)
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="managerprofile")
    @commands.has_permissions(manage_guild=True)
    async def manager_profile(self, ctx: commands.Context, member: discord.Member):
        """View a manager's performance profile.  Usage: !managerprofile @member"""
        embed = self.build_profile_embed(member)
        await ctx.send(embed=embed)

    @commands.command(name="manageradd")
    @commands.has_permissions(manage_guild=True)
    async def manager_add(self, ctx: commands.Context, member: discord.Member, stat: str, amount: int = 1):
        """Add to a manager's stat.
        Usage: !manageradd @member <stat> [amount]
        Stats: recruitment (r), meet_support (ms), manager_actions (a), issues (i), warnings (w)
        Example: !manageradd @John r 2
        """
        field = VALID_STATS.get(stat.lower())
        if not field:
            await ctx.send(
                "❌ Unknown stat. Valid options: `recruitment` `meet_support` `manager_actions` `issues_reported` `warnings_filed`\n"
                "Short aliases: `r` `ms` `a` `i` `w`",
                delete_after=12,
            )
            return
        if amount <= 0:
            await ctx.send("❌ Amount must be a positive number.", delete_after=8)
            return

        stats = await self._adjust(member, **{field: amount})
        label, pts = STAT_LABELS[field]
        score = _compute_score(stats)
        await ctx.send(
            f"✅ Added **{amount}** {label} (+{amount * pts} pts) to {member.mention}. "
            f"New total score: **{score} pts**.",
            delete_after=10,
        )
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="managerremove")
    @commands.has_permissions(manage_guild=True)
    async def manager_remove(self, ctx: commands.Context, member: discord.Member, stat: str, amount: int = 1):
        """Remove from a manager's stat.
        Usage: !managerremove @member <stat> [amount]
        Example: !managerremove @John ms 1
        """
        field = VALID_STATS.get(stat.lower())
        if not field:
            await ctx.send(
                "❌ Unknown stat. Valid options: `recruitment` `meet_support` `manager_actions` `issues_reported` `warnings_filed`\n"
                "Short aliases: `r` `ms` `a` `i` `w`",
                delete_after=12,
            )
            return
        if amount <= 0:
            await ctx.send("❌ Amount must be a positive number.", delete_after=8)
            return

        stats = await self._adjust(member, **{field: -amount})
        label, _ = STAT_LABELS[field]
        score = _compute_score(stats)
        await ctx.send(
            f"✅ Removed **{amount}** {label} from {member.mention}. "
            f"New total score: **{score} pts**.",
            delete_after=10,
        )
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="managerresetall")
    @commands.has_permissions(administrator=True)
    async def manager_reset_all(self, ctx: commands.Context):
        """Reset ALL manager performance stats. Requires Administrator."""
        _save(STATS_FILE, {"managers": {}})
        await self.post_or_refresh_panel()
        await ctx.send("✅ All manager performance stats have been reset.", delete_after=10)
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="managerreset")
    @commands.has_permissions(manage_guild=True)
    async def manager_reset_one(self, ctx: commands.Context, member: discord.Member):
        """Reset a single manager's stats.  Usage: !managerreset @member"""
        data = _load(STATS_FILE, {"managers": {}})
        key  = str(member.id)
        if key in data["managers"]:
            data["managers"].pop(key)
            _save(STATS_FILE, data)
            await self.post_or_refresh_panel()
            await ctx.send(f"✅ Stats for {member.mention} have been reset.", delete_after=8)
        else:
            await ctx.send(f"ℹ️ {member.mention} has no recorded stats.", delete_after=8)
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="managerhelp")
    @commands.has_permissions(manage_guild=True)
    async def manager_help(self, ctx: commands.Context):
        """Show all manager performance commands."""
        embed = discord.Embed(
            title="📋 Manager Performance Commands",
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="Panel",
            value=(
                "`!managerboard` — Post / refresh the leaderboard panel\n"
            ),
            inline=False,
        )
        embed.add_field(
            name="Stats",
            value=(
                "`!managerprofile @member` — View a manager's profile\n"
                "`!manageradd @member <stat> [amount]` — Add to a stat\n"
                "`!managerremove @member <stat> [amount]` — Remove from a stat\n"
                "`!managerreset @member` — Reset one manager's stats\n"
                "`!managerresetall` — Reset everyone's stats *(Admin only)*\n"
            ),
            inline=False,
        )
        embed.add_field(
            name="Stat Aliases",
            value=(
                "`r` / `recruit` → Recruitment\n"
                "`ms` / `meetsupport` → Meet Support\n"
                "`a` / `actions` → Manager Actions\n"
                "`i` / `issues` → Issues Reported\n"
                "`w` / `warnings` → Warnings Filed\n"
            ),
            inline=False,
        )
        embed.set_footer(text=FOOTER_TEXT)
        await ctx.send(embed=embed)


# =========================================================
# SETUP
# =========================================================

async def setup(bot: commands.Bot):
    await bot.add_cog(ManagerPerformanceSystem(bot))
