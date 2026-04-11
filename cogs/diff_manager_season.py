from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import discord
from discord.ext import commands, tasks

# =========================================================
# CONFIG
# =========================================================

GUILD_ID                   = 850386896509337710
SEASON_PANEL_CHANNEL_ID    = 1485273802391814224
PROMOTION_LOG_CHANNEL_ID   = 1485265848099799163  # staff-logs

MANAGER_ROLE_PING_ID       = None
SEASON_WINNER_ROLE_ID      = None
PROMOTION_TARGET_ROLE_ID   = None

PANEL_TITLE = "🏆 DIFF Manager Season Hub"
PANEL_DESCRIPTION = (
    "Track weekly manager performance, promotion suggestions, and season leaders across **Different Meets**.\n\n"
    "Each week starts fresh. Top performers are recognised and promotion suggestions are "
    "logged automatically when the score threshold is reached.\n\n"
    "This panel refreshes cleanly without creating duplicate posts."
)
FOOTER_TEXT = "Different Meets • Manager Season System"

RECRUITMENT_POINTS    = 3
MEET_SUPPORT_POINTS   = 2
MANAGER_ACTION_POINTS = 2
ISSUE_REPORT_POINTS   = 1
WARNING_FILED_POINTS  = 1

PROMOTION_SUGGESTION_SCORE = 25

RESET_WEEKDAY        = 0    # Monday
RESET_HOUR_UTC       = 16   # 12 PM Eastern (EDT)
ENABLE_AUTO_WEEKLY_RESET = False

DATA_DIR    = Path("diff_data")
STATE_FILE  = DATA_DIR / "manager_season_state.json"
STATS_FILE  = DATA_DIR / "manager_season_stats.json"
SEASON_FILE = DATA_DIR / "manager_season_meta.json"

VALID_STATS = {
    "recruitment": "recruitment", "recruit": "recruitment", "r": "recruitment",
    "meet_support": "meet_support", "meetsupport": "meet_support", "ms": "meet_support",
    "manager_actions": "manager_actions", "manageractions": "manager_actions",
    "actions": "manager_actions", "a": "manager_actions",
    "issues_reported": "issues_reported", "issues": "issues_reported",
    "issue": "issues_reported", "i": "issues_reported",
    "warnings_filed": "warnings_filed", "warnings": "warnings_filed",
    "warning": "warnings_filed", "w": "warnings_filed",
}
STAT_LABELS = {
    "recruitment":     ("Recruitment",     RECRUITMENT_POINTS),
    "meet_support":    ("Meet Support",    MEET_SUPPORT_POINTS),
    "manager_actions": ("Manager Actions", MANAGER_ACTION_POINTS),
    "issues_reported": ("Issues Reported", ISSUE_REPORT_POINTS),
    "warnings_filed":  ("Warnings Filed",  WARNING_FILED_POINTS),
}

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

def _blank(member_id: int, name: str) -> dict:
    return {
        "member_id": member_id,
        "name": name,
        "recruitment": 0,
        "meet_support": 0,
        "manager_actions": 0,
        "issues_reported": 0,
        "warnings_filed": 0,
    }

def _score(stats: dict) -> int:
    return (
        stats.get("recruitment",     0) * RECRUITMENT_POINTS
        + stats.get("meet_support",    0) * MEET_SUPPORT_POINTS
        + stats.get("manager_actions", 0) * MANAGER_ACTION_POINTS
        + stats.get("issues_reported", 0) * ISSUE_REPORT_POINTS
        + stats.get("warnings_filed",  0) * WARNING_FILED_POINTS
    )

def _ranked(managers: dict) -> list:
    rows = list(managers.values())
    for r in rows:
        r["score"] = _score(r)
    rows.sort(
        key=lambda x: (x["score"], x.get("recruitment", 0), x.get("meet_support", 0)),
        reverse=True,
    )
    return rows

# =========================================================
# COG
# =========================================================

class ManagerSeasonSystem(commands.Cog, name="ManagerSeasonSystem"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        _load(STATE_FILE,  {"channel_id": SEASON_PANEL_CHANNEL_ID, "message_id": None})
        _load(STATS_FILE,  {"managers": {}})
        _load(SEASON_FILE, {
            "season_number": 1,
            "last_reset_utc": None,
            "last_winner_id": None,
            "last_winner_name": None,
            "promotion_announced": [],
        })
        if ENABLE_AUTO_WEEKLY_RESET:
            self.weekly_reset_loop.start()

    def cog_unload(self):
        if ENABLE_AUTO_WEEKLY_RESET:
            self.weekly_reset_loop.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        print("[ManagerSeasonSystem] Cog ready.")

    # ── data helpers ─────────────────────────────────────────

    def _get_stats(self) -> dict:
        return _load(STATS_FILE, {"managers": {}})

    def _set_stats(self, data: dict):
        _save(STATS_FILE, data)

    def _get_meta(self) -> dict:
        return _load(SEASON_FILE, {
            "season_number": 1,
            "last_reset_utc": None,
            "last_winner_id": None,
            "last_winner_name": None,
            "promotion_announced": [],
        })

    def _set_meta(self, data: dict):
        _save(SEASON_FILE, data)

    # ── embed builders ───────────────────────────────────────

    def build_main_embed(self) -> discord.Embed:
        data  = self._get_stats()
        meta  = self._get_meta()
        rows  = _ranked(data.get("managers", {}))

        embed = discord.Embed(
            title=PANEL_TITLE,
            description=PANEL_DESCRIPTION,
            color=discord.Color.blurple(),
        )
        embed.add_field(name="📅 Current Season",        value=f"Week **{meta.get('season_number', 1)}**", inline=True)
        embed.add_field(name="📈 Promotion Threshold",   value=f"**{PROMOTION_SUGGESTION_SCORE} pts**",    inline=True)
        embed.add_field(name="🏅 Last Week's Winner",
                        value=meta.get("last_winner_name") or "None yet", inline=True)

        if rows:
            medals = ["🥇", "🥈", "🥉"]
            lines  = []
            for idx, item in enumerate(rows[:10], start=1):
                prefix = medals[idx - 1] if idx <= 3 else f"**#{idx}**"
                near_promo = " 🔔" if item["score"] >= PROMOTION_SUGGESTION_SCORE else ""
                lines.append(
                    f"{prefix} <@{item['member_id']}> — **{item['score']} pts**{near_promo}"
                    f"  `R:{item['recruitment']} MS:{item['meet_support']}"
                    f" A:{item['manager_actions']} I:{item['issues_reported']}"
                    f" W:{item['warnings_filed']}`"
                )
            embed.add_field(name="🏆 Season Leaderboard", value="\n".join(lines), inline=False)
        else:
            embed.add_field(name="🏆 Season Leaderboard",
                            value="No season stats recorded yet this week.", inline=False)

        embed.add_field(
            name="📊 Scoring",
            value=(
                f"Recruitment = **{RECRUITMENT_POINTS} pts** | "
                f"Meet Support = **{MEET_SUPPORT_POINTS} pts** | "
                f"Manager Actions = **{MANAGER_ACTION_POINTS} pts** | "
                f"Issues = **{ISSUE_REPORT_POINTS} pt** | "
                f"Warnings = **{WARNING_FILED_POINTS} pt**"
            ),
            inline=False,
        )
        embed.set_footer(text=FOOTER_TEXT)
        return embed

    def build_profile_embed(self, member: discord.Member) -> discord.Embed:
        data  = self._get_stats()
        stats = data["managers"].get(str(member.id), _blank(member.id, str(member)))
        score = _score(stats)
        rows  = _ranked(data.get("managers", {}))
        rank  = next((i + 1 for i, r in enumerate(rows) if str(r["member_id"]) == str(member.id)), None)
        meta  = self._get_meta()

        embed = discord.Embed(
            title=f"📊 Season Profile  •  {member.display_name}",
            description=f"Week **{meta.get('season_number', 1)}** stats",
            color=discord.Color.green(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="🏅 Season Rank",     value=f"#{rank}" if rank else "Unranked", inline=True)
        embed.add_field(name="⭐ Score",            value=str(score),                          inline=True)
        embed.add_field(name="🔔 Promo Status",
                        value="✅ Threshold reached!" if score >= PROMOTION_SUGGESTION_SCORE else f"{PROMOTION_SUGGESTION_SCORE - score} pts needed",
                        inline=True)
        embed.add_field(name="📣 Recruitment",      value=str(stats.get("recruitment",    0)), inline=True)
        embed.add_field(name="🤝 Meet Support",     value=str(stats.get("meet_support",   0)), inline=True)
        embed.add_field(name="⚙️ Manager Actions",  value=str(stats.get("manager_actions",0)), inline=True)
        embed.add_field(name="🔎 Issues Reported",  value=str(stats.get("issues_reported",0)), inline=True)
        embed.add_field(name="⚠️ Warnings Filed",   value=str(stats.get("warnings_filed", 0)), inline=True)
        embed.set_footer(text=FOOTER_TEXT)
        return embed

    # ── panel post/refresh ───────────────────────────────────

    async def post_or_refresh_panel(self) -> bool:
        state      = _load(STATE_FILE, {"channel_id": SEASON_PANEL_CHANNEL_ID, "message_id": None})
        channel_id = state.get("channel_id", SEASON_PANEL_CHANNEL_ID)
        message_id = state.get("message_id")

        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception as e:
                print(f"[ManagerSeasonSystem] Could not access channel: {e}")
                return False

        embed = self.build_main_embed()

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
            print(f"[ManagerSeasonSystem] Failed to post panel: {e}")
            return False

    # ── stat adjustment ──────────────────────────────────────

    async def adjust_stats(self, member: discord.Member, **deltas) -> dict:
        data = self._get_stats()
        key  = str(member.id)
        if key not in data["managers"]:
            data["managers"][key] = _blank(member.id, str(member))
        stats = data["managers"][key]
        stats["name"] = str(member)
        for field, delta in deltas.items():
            stats[field] = max(0, stats.get(field, 0) + delta)
        self._set_stats(data)
        await self._check_promotion(member, stats)
        await self.post_or_refresh_panel()
        return stats

    async def _check_promotion(self, member: discord.Member, stats: dict):
        score    = _score(stats)
        meta     = self._get_meta()
        announced = set(meta.get("promotion_announced", []))

        if score < PROMOTION_SUGGESTION_SCORE or str(member.id) in announced:
            return

        if PROMOTION_LOG_CHANNEL_ID:
            ch = self.bot.get_channel(PROMOTION_LOG_CHANNEL_ID)
            if ch:
                embed = discord.Embed(
                    title="📈 Promotion Suggestion",
                    description=(
                        f"{member.mention} has hit the promotion threshold this week.\n\n"
                        f"**Score:** {score} pts  |  **Threshold:** {PROMOTION_SUGGESTION_SCORE} pts"
                    ),
                    color=discord.Color.gold(),
                )
                embed.add_field(name="📣 Recruitment",     value=str(stats.get("recruitment",    0)), inline=True)
                embed.add_field(name="🤝 Meet Support",    value=str(stats.get("meet_support",   0)), inline=True)
                embed.add_field(name="⚙️ Manager Actions", value=str(stats.get("manager_actions",0)), inline=True)
                embed.add_field(name="🔎 Issues Reported", value=str(stats.get("issues_reported",0)), inline=True)
                embed.add_field(name="⚠️ Warnings Filed",  value=str(stats.get("warnings_filed", 0)), inline=True)
                embed.set_footer(text=FOOTER_TEXT)
                await ch.send(embed=embed)

        announced.add(str(member.id))
        meta["promotion_announced"] = list(announced)
        self._set_meta(meta)

    # ── end week logic ───────────────────────────────────────

    async def end_week(self, guild: discord.Guild) -> str:
        data  = self._get_stats()
        rows  = _ranked(data.get("managers", {}))
        meta  = self._get_meta()
        week  = meta.get("season_number", 1)

        winner_text   = f"No stats were recorded this week (Week {week})."
        winner_member = None

        if rows:
            winner        = rows[0]
            winner_text   = (
                f"<@{winner['member_id']}> won **Week {week}** "
                f"with **{winner['score']} pts**! 🎉"
            )
            winner_member = guild.get_member(winner["member_id"])
            meta["last_winner_id"]   = winner["member_id"]
            meta["last_winner_name"] = winner["name"]

            if PROMOTION_LOG_CHANNEL_ID:
                ch = self.bot.get_channel(PROMOTION_LOG_CHANNEL_ID)
                if ch:
                    embed = discord.Embed(
                        title=f"🏆 Week {week} Results",
                        description=winner_text,
                        color=discord.Color.gold(),
                    )
                    medals = ["🥇", "🥈", "🥉"]
                    top3   = "\n".join(
                        f"{medals[i]} <@{r['member_id']}> — **{r['score']} pts**"
                        for i, r in enumerate(rows[:3])
                    )
                    embed.add_field(name="Top 3", value=top3, inline=False)
                    embed.set_footer(text=FOOTER_TEXT)
                    await ch.send(embed=embed)

        if SEASON_WINNER_ROLE_ID and winner_member:
            role = guild.get_role(SEASON_WINNER_ROLE_ID)
            if role:
                try:
                    for m in role.members:
                        await m.remove_roles(role, reason="Weekly season reset")
                    await winner_member.add_roles(role, reason=f"Week {week} winner")
                except Exception:
                    pass

        if PROMOTION_TARGET_ROLE_ID and winner_member:
            role = guild.get_role(PROMOTION_TARGET_ROLE_ID)
            if role and role not in winner_member.roles:
                try:
                    await winner_member.add_roles(role, reason="Season auto-promotion")
                except Exception:
                    pass

        meta["season_number"]        = week + 1
        meta["last_reset_utc"]       = datetime.now(timezone.utc).isoformat()
        meta["promotion_announced"]  = []
        self._set_meta(meta)
        self._set_stats({"managers": {}})
        await self.post_or_refresh_panel()
        return winner_text

    # ── auto weekly reset loop ───────────────────────────────

    @tasks.loop(minutes=30)
    async def weekly_reset_loop(self):
        now = datetime.now(timezone.utc)
        if now.weekday() != RESET_WEEKDAY or now.hour != RESET_HOUR_UTC:
            return
        meta       = self._get_meta()
        last_reset = meta.get("last_reset_utc")
        if last_reset:
            try:
                if datetime.fromisoformat(last_reset).date() == now.date():
                    return
            except Exception:
                pass
        guild = self.bot.get_guild(GUILD_ID)
        if guild:
            await self.end_week(guild)

    @weekly_reset_loop.before_loop
    async def before_weekly_loop(self):
        await self.bot.wait_until_ready()

    # =========================================================
    # PREFIX COMMANDS
    # =========================================================

    @commands.command(name="seasonrefresh")
    @commands.has_permissions(manage_guild=True)
    async def season_refresh(self, ctx: commands.Context):
        """Post or refresh the manager season panel."""
        ok = await self.post_or_refresh_panel()
        await ctx.send("✅ Season panel refreshed." if ok else "❌ Failed.", delete_after=8)
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="seasonprofile")
    @commands.has_permissions(manage_guild=True)
    async def season_profile(self, ctx: commands.Context, member: discord.Member):
        """View a manager's season profile.  Usage: !seasonprofile @member"""
        await ctx.send(embed=self.build_profile_embed(member))

    @commands.command(name="seasonadd")
    @commands.has_permissions(manage_guild=True)
    async def season_add(self, ctx: commands.Context, member: discord.Member, stat: str, amount: int = 1):
        """Add to a manager's season stat.
        Usage: !seasonadd @member <stat> [amount]
        Stats: r  ms  a  i  w
        """
        field = VALID_STATS.get(stat.lower())
        if not field:
            await ctx.send("❌ Unknown stat. Use: `r` `ms` `a` `i` `w`", delete_after=10)
            return
        if amount <= 0:
            await ctx.send("❌ Amount must be positive.", delete_after=8)
            return
        stats      = await self.adjust_stats(member, **{field: amount})
        label, pts = STAT_LABELS[field]
        score      = _score(stats)
        await ctx.send(
            f"✅ Added **{amount}** {label} (+{amount * pts} pts) to {member.mention}. "
            f"Season score: **{score} pts**.",
            delete_after=10,
        )
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="seasonremove")
    @commands.has_permissions(manage_guild=True)
    async def season_remove(self, ctx: commands.Context, member: discord.Member, stat: str, amount: int = 1):
        """Remove from a manager's season stat.  Usage: !seasonremove @member <stat> [amount]"""
        field = VALID_STATS.get(stat.lower())
        if not field:
            await ctx.send("❌ Unknown stat. Use: `r` `ms` `a` `i` `w`", delete_after=10)
            return
        if amount <= 0:
            await ctx.send("❌ Amount must be positive.", delete_after=8)
            return
        stats     = await self.adjust_stats(member, **{field: -amount})
        label, _  = STAT_LABELS[field]
        score     = _score(stats)
        await ctx.send(
            f"✅ Removed **{amount}** {label} from {member.mention}. "
            f"Season score: **{score} pts**.",
            delete_after=10,
        )
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="seasonendweek")
    @commands.has_permissions(manage_guild=True)
    async def season_end_week(self, ctx: commands.Context):
        """End the current week — announces winner, resets all season stats, advances season number."""
        if not ctx.guild:
            await ctx.send("Must be used in a server.", delete_after=8)
            return
        await ctx.send("⏳ Ending the week...", delete_after=5)
        winner_text = await self.end_week(ctx.guild)
        await ctx.send(f"✅ Week ended. {winner_text}")

    @commands.command(name="seasonreset")
    @commands.has_permissions(administrator=True)
    async def season_reset(self, ctx: commands.Context):
        """Reset season stats without announcing a winner. Requires Administrator."""
        meta                        = self._get_meta()
        meta["season_number"]       = meta.get("season_number", 1) + 1
        meta["last_reset_utc"]      = datetime.now(timezone.utc).isoformat()
        meta["promotion_announced"] = []
        self._set_meta(meta)
        self._set_stats({"managers": {}})
        await self.post_or_refresh_panel()
        await ctx.send(f"✅ Season stats silently reset. Now on Week **{meta['season_number']}**.", delete_after=10)
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="seasoninfo")
    @commands.has_permissions(manage_guild=True)
    async def season_info(self, ctx: commands.Context):
        """Show current season number and last reset time."""
        meta  = self._get_meta()
        week  = meta.get("season_number", 1)
        reset = meta.get("last_reset_utc", "Never")
        prev  = meta.get("last_winner_name", "None")
        embed = discord.Embed(
            title="📅 Season Info",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Current Week", value=str(week),  inline=True)
        embed.add_field(name="Last Winner",  value=prev,        inline=True)
        embed.add_field(name="Last Reset",   value=reset[:19] if reset != "Never" else "Never", inline=True)
        embed.set_footer(text=FOOTER_TEXT)
        await ctx.send(embed=embed)

    @commands.command(name="seasonhelp")
    @commands.has_permissions(manage_guild=True)
    async def season_help(self, ctx: commands.Context):
        """Show all manager season commands."""
        embed = discord.Embed(
            title="📋 Manager Season Commands",
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="Panel",
            value="`!seasonrefresh` — Post / refresh the season panel",
            inline=False,
        )
        embed.add_field(
            name="Stats",
            value=(
                "`!seasonprofile @m` — View a manager's season stats\n"
                "`!seasonadd @m <stat> [n]` — Add to a season stat\n"
                "`!seasonremove @m <stat> [n]` — Remove from a season stat\n"
            ),
            inline=False,
        )
        embed.add_field(
            name="Season Control",
            value=(
                "`!seasonendweek` — End week, announce winner, reset stats\n"
                "`!seasonreset` — Silent reset *(Admin only)*\n"
                "`!seasoninfo` — Show current week & last reset\n"
            ),
            inline=False,
        )
        embed.add_field(
            name="Stat Aliases",
            value="`r` recruit  |  `ms` meet support  |  `a` actions  |  `i` issues  |  `w` warnings",
            inline=False,
        )
        embed.add_field(
            name="🔔 Promotion Threshold",
            value=f"Managers that hit **{PROMOTION_SUGGESTION_SCORE} pts** in a week get flagged in staff-logs automatically.",
            inline=False,
        )
        embed.set_footer(text=FOOTER_TEXT)
        await ctx.send(embed=embed)


# =========================================================
# SETUP
# =========================================================

async def setup(bot: commands.Bot):
    await bot.add_cog(ManagerSeasonSystem(bot))
