from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple

import discord
from discord.ext import commands

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

GUILD_ID = 850386896509337710

DATA_DIR   = "diff_data"
CHARTS_DIR = os.path.join(DATA_DIR, "dashboard_charts")

MOD_PROFILES_FILE  = os.path.join(DATA_DIR, "moderation_profiles.json")
HOST_PROFILES_FILE = os.path.join(DATA_DIR, "host_performance_profiles.json")

COLOR_PRIMARY = 0x1F6FEB
COLOR_SUCCESS = 0x2ECC71
COLOR_WARNING = 0xF39C12
COLOR_DANGER  = 0xE74C3C


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_dirs() -> None:
    os.makedirs(DATA_DIR,   exist_ok=True)
    os.makedirs(CHARTS_DIR, exist_ok=True)


def _load_json(path: str, default):
    _ensure_dirs()
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=4)
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


class NextLevelModerationSystem(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        _ensure_dirs()

    @commands.Cog.listener()
    async def on_ready(self):
        print("[NextLevelModerationSystem] Cog ready.")

    def _member_profiles(self) -> Dict[str, Any]:
        return _load_json(MOD_PROFILES_FILE, {})

    def _host_profiles(self) -> Dict[str, Any]:
        return _load_json(HOST_PROFILES_FILE, {})

    def _top_hosts(self, limit: int = 5) -> List[Dict[str, Any]]:
        hosts = [h for h in self._host_profiles().values() if int(h.get("hosted_meets", 0)) > 0]
        hosts.sort(
            key=lambda h: (
                float(h.get("feedback_average", 0)),
                float(h.get("attendance_average", 0)),
                int(h.get("hosted_meets", 0)),
            ),
            reverse=True,
        )
        return hosts[:limit]

    def _worst_hosts(self, limit: int = 5) -> List[Dict[str, Any]]:
        hosts = [h for h in self._host_profiles().values() if int(h.get("hosted_meets", 0)) > 0]
        hosts.sort(
            key=lambda h: (
                float(h.get("feedback_average", 999)),
                float(h.get("attendance_average", 999)),
                -int(h.get("host_writeups", 0)),
            )
        )
        return hosts[:limit]

    def _risky_members(self) -> List[Tuple[str, str]]:
        results: List[Tuple[str, str]] = []
        for profile in self._member_profiles().values():
            name      = profile.get("display_name", "Unknown Member")
            strikes   = int(profile.get("strikes", 0))
            writeups  = int(profile.get("writeups", 0))
            flags     = profile.get("flags", [])
            fb_avg    = float(profile.get("feedback_average", 0))
            score     = 0
            if strikes  >= 2: score += 2
            if strikes  >= 3: score += 2
            if writeups >= 3: score += 2
            if writeups >= 5: score += 2
            if flags:          score += 2
            if fb_avg and fb_avg <= 2.5: score += 1
            if score >= 6:
                results.append((name, "Recommend restriction review — member is trending high-risk."))
            elif score >= 4:
                results.append((name, "Recommend close monitoring — member risk is rising."))
        return results[:10]

    def _burnout_hosts(self) -> List[Tuple[str, str]]:
        results: List[Tuple[str, str]] = []
        for profile in self._host_profiles().values():
            name           = profile.get("display_name", "Unknown Host")
            hosted         = int(profile.get("hosted_meets", 0))
            fb_avg         = float(profile.get("feedback_average", 0))
            att_avg        = float(profile.get("attendance_average", 0))
            host_writeups  = int(profile.get("host_writeups", 0))
            review_flagged = bool(profile.get("review_flagged", False))
            score          = 0
            if hosted >= 3:                      score += 1
            if fb_avg  and fb_avg  <= 3:         score += 2
            if fb_avg  and fb_avg  <= 2.5:       score += 2
            if att_avg and att_avg <= 3:          score += 2
            if host_writeups >= 1:               score += 1
            if host_writeups >= 2:               score += 2
            if review_flagged:                   score += 2
            if score >= 6:
                results.append((name, "Recommend host role review — host may be declining or burning out."))
            elif score >= 4:
                results.append((name, "Recommend support/check-in — host may be struggling with performance."))
        return results[:10]

    def _punishment_suggestions(self) -> List[str]:
        suggestions: List[str] = []
        for name, insight in self._risky_members()[:5]:
            if "restriction" in insight.lower():
                suggestions.append(f"**{name}** — Recommend restriction.")
            else:
                suggestions.append(f"**{name}** — Recommend monitoring.")
        for name, insight in self._burnout_hosts()[:5]:
            if "host role review" in insight.lower():
                suggestions.append(f"**{name}** — Recommend removal from host role review queue.")
            else:
                suggestions.append(f"**{name}** — Recommend staff support review.")
        return suggestions[:10]

    def _make_host_chart(self) -> str:
        top = self._top_hosts(limit=5)
        out = os.path.join(CHARTS_DIR, "top_hosts_chart.png")
        names  = [h.get("display_name", "Unknown")[:12] for h in top] or ["No Data"]
        values = [float(h.get("feedback_average", 0))    for h in top] or [0]
        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.bar(names, values, color="#1F6FEB")
        ax.set_title("Top Hosts by Feedback Rating", fontsize=14, fontweight="bold")
        ax.set_xlabel("Host")
        ax.set_ylabel("Average Feedback")
        ax.set_ylim(0, 5)
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                    f"{val:.1f}", ha="center", va="bottom", fontsize=10)
        plt.tight_layout()
        plt.savefig(out, dpi=160, facecolor="#2B2D31")
        plt.close()
        return out

    def _make_risk_chart(self) -> str:
        out = os.path.join(CHARTS_DIR, "member_risk_chart.png")
        members = sorted(
            self._member_profiles().values(),
            key=lambda p: int(p.get("strikes", 0)) + int(p.get("writeups", 0)),
            reverse=True,
        )[:5]
        names  = [m.get("display_name", "Unknown")[:12] for m in members] or ["No Data"]
        values = [int(m.get("strikes", 0)) + int(m.get("writeups", 0)) for m in members] or [0]
        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.bar(names, values, color="#E74C3C")
        ax.set_title("Highest Moderation Risk Members", fontsize=14, fontweight="bold")
        ax.set_xlabel("Member")
        ax.set_ylabel("Risk Score (Write-Ups + Strikes)")
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                    str(val), ha="center", va="bottom", fontsize=10)
        plt.tight_layout()
        plt.savefig(out, dpi=160, facecolor="#2B2D31")
        plt.close()
        return out

    def _dashboard_embed(self) -> discord.Embed:
        members = self._member_profiles()
        hosts   = self._host_profiles()
        embed = discord.Embed(
            title="📊 DIFF Control Center",
            description="Live moderation and performance overview for staff.",
            color=COLOR_PRIMARY,
            timestamp=utcnow(),
        )
        embed.add_field(name="Member Profiles",  value=str(len(members)), inline=True)
        embed.add_field(name="Host Profiles",    value=str(len(hosts)),   inline=True)
        embed.add_field(name="Flagged Hosts",
                        value=str(sum(1 for h in hosts.values() if h.get("review_flagged"))),
                        inline=True)
        embed.add_field(name="Total Write-Ups",
                        value=str(sum(int(p.get("writeups", 0)) for p in members.values())),
                        inline=True)
        embed.add_field(name="Total Strikes",
                        value=str(sum(int(p.get("strikes", 0)) for p in members.values())),
                        inline=True)
        embed.add_field(name="System State", value="✅ Operational", inline=True)
        embed.set_footer(text="Different Meets • Visual Dashboard")
        return embed

    def _weekly_embed(self) -> discord.Embed:
        top_hosts   = self._top_hosts(limit=3)
        worst_hosts = self._worst_hosts(limit=3)
        risky       = self._risky_members()[:3]
        burnout     = self._burnout_hosts()[:3]

        embed = discord.Embed(
            title="🗓️ DIFF Weekly Moderation Report",
            description="Weekly summary of moderation, host performance, and predictive insights.",
            color=COLOR_SUCCESS,
            timestamp=utcnow(),
        )
        top_text   = "\n".join(
            f"**{i+1}. {h.get('display_name','Unknown')}** — {h.get('feedback_average',0)}/5"
            for i, h in enumerate(top_hosts)) or "No data"
        worst_text = "\n".join(
            f"**{i+1}. {h.get('display_name','Unknown')}** — {h.get('feedback_average',0)}/5"
            for i, h in enumerate(worst_hosts)) or "No data"
        risky_text  = "\n".join(f"**{n}** — {m}" for n, m in risky)  or "No elevated-risk members detected."
        burn_text   = "\n".join(f"**{n}** — {m}" for n, m in burnout) or "No declining hosts detected."

        embed.add_field(name="🏆 Top Hosts",                value=top_text,   inline=False)
        embed.add_field(name="📉 Worst Hosts",              value=worst_text,  inline=False)
        embed.add_field(name="🧠 Risky Members",            value=risky_text,  inline=False)
        embed.add_field(name="🔥 Burnout / Declining Hosts",value=burn_text,   inline=False)
        embed.set_footer(text="Different Meets • Weekly Report")
        return embed

    def _suggestion_embed(self) -> discord.Embed:
        suggestions = self._punishment_suggestions()
        embed = discord.Embed(
            title="🎯 Auto Punishment Suggestions",
            description="Suggested actions based on moderation and performance trends.",
            color=COLOR_WARNING,
            timestamp=utcnow(),
        )
        embed.add_field(
            name="Recommendations",
            value="\n".join(suggestions) if suggestions else "No active punishment suggestions right now.",
            inline=False,
        )
        embed.set_footer(text="Different Meets • Predictive Moderation")
        return embed

    @commands.command(name="visualdashboard")
    @commands.has_permissions(manage_guild=True)
    async def visual_dashboard(self, ctx: commands.Context):
        """Post the visual control-center dashboard with charts."""
        async with ctx.typing():
            embed = self._dashboard_embed()
            chart1 = self._make_host_chart()
            chart2 = self._make_risk_chart()
        await ctx.send(embed=embed)
        await ctx.send(file=discord.File(chart1, filename="top_hosts_chart.png"))
        await ctx.send(file=discord.File(chart2, filename="member_risk_chart.png"))

    @commands.command(name="weeklyreport")
    @commands.has_permissions(manage_guild=True)
    async def weekly_report(self, ctx: commands.Context):
        """Post the weekly moderation summary embed."""
        await ctx.send(embed=self._weekly_embed())

    @commands.command(name="topsandbottoms")
    @commands.has_permissions(manage_guild=True)
    async def tops_and_bottoms(self, ctx: commands.Context):
        """Show the top 5 and worst 5 hosts side by side."""
        top   = self._top_hosts(limit=5)
        worst = self._worst_hosts(limit=5)
        embed = discord.Embed(
            title="📊 Top Hosts / Worst Hosts",
            color=COLOR_PRIMARY,
            timestamp=utcnow(),
        )
        top_text = "\n".join(
            f"**{i+1}. {h.get('display_name','Unknown')}** — "
            f"Feedback {h.get('feedback_average',0)}/5 | Attendance {h.get('attendance_average',0)}"
            for i, h in enumerate(top)) or "No host data."
        worst_text = "\n".join(
            f"**{i+1}. {h.get('display_name','Unknown')}** — "
            f"Feedback {h.get('feedback_average',0)}/5 | Attendance {h.get('attendance_average',0)}"
            for i, h in enumerate(worst)) or "No host data."
        embed.add_field(name="🏆 Top Hosts",   value=top_text,   inline=False)
        embed.add_field(name="📉 Worst Hosts",  value=worst_text,  inline=False)
        embed.set_footer(text="Different Meets • Host Ranking")
        await ctx.send(embed=embed)

    @commands.command(name="predictivemod")
    @commands.has_permissions(manage_guild=True)
    async def predictive_mod(self, ctx: commands.Context):
        """Show predictive moderation insights for risky members and declining hosts."""
        risky   = self._risky_members()
        burnout = self._burnout_hosts()
        embed = discord.Embed(
            title="🧠 Predictive Moderation Insights",
            color=COLOR_DANGER,
            timestamp=utcnow(),
        )
        embed.add_field(
            name="Future Problem Members",
            value="\n".join(f"**{n}** — {m}" for n, m in risky[:8]) if risky else "No high-risk trends detected.",
            inline=False,
        )
        embed.add_field(
            name="Burnout / Declining Hosts",
            value="\n".join(f"**{n}** — {m}" for n, m in burnout[:8]) if burnout else "No host decline trends detected.",
            inline=False,
        )
        embed.set_footer(text="Different Meets • Predictive Moderation")
        await ctx.send(embed=embed)

    @commands.command(name="punishmentsuggestions")
    @commands.has_permissions(manage_guild=True)
    async def punishment_suggestions(self, ctx: commands.Context):
        """Show AI-generated punishment / action suggestions based on current data."""
        await ctx.send(embed=self._suggestion_embed())

    @commands.command(name="moddashboardcharts")
    @commands.has_permissions(manage_guild=True)
    async def mod_dashboard_charts(self, ctx: commands.Context):
        """Generate and send both moderation charts without the embed."""
        async with ctx.typing():
            chart1 = self._make_host_chart()
            chart2 = self._make_risk_chart()
        await ctx.send(file=discord.File(chart1, filename="top_hosts_chart.png"))
        await ctx.send(file=discord.File(chart2, filename="member_risk_chart.png"))


async def setup(bot: commands.Bot):
    await bot.add_cog(NextLevelModerationSystem(bot))
