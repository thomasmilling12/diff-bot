"""
diff_smart_features.py
══════════════════════
Three intelligence upgrades for DIFF Meets:

  1. Smart Moderation Messages  — !diff_warn
     Branded, context-aware warnings that escalate in tone per count.

  2. Insights Dashboard         — !diff_insights
     Real server analytics pulled from the roll call DB + member data.

  3. Color Lab Ticket Assistant — auto-reply
     Instant expert reply when a member opens a color lab ticket.
"""
from __future__ import annotations

import random
import sqlite3
import sys
from datetime import datetime, timezone

import discord
from discord.ext import commands

print("[SmartFeatures] Module loading...")

# ─── Constants ─────────────────────────────────────────────────────────────────
GUILD_ID             = 850386896509337710
RC_DB_PATH           = "diff_data/diff_rollcall.db"
COLOR_LAB_CATEGORY   = "color-"        # ticket channel name prefix

LEADER_ROLE_ID   = 850391095845584937
CO_LEADER_ID     = 850391378559238235
MANAGER_ROLE_ID  = 990011447193006101
COLOR_TEAM_ID    = 1115495008670330902
STAFF_ROLES      = {LEADER_ROLE_ID, CO_LEADER_ID, MANAGER_ROLE_ID}

DIFF_LOGO = (
    "https://media.discordapp.net/attachments/1107375326625005719/"
    "1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm="
    "2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
    "&=&format=webp&quality=lossless&width=1376&height=917"
)


def _main():
    return sys.modules["__main__"]


def _is_staff(member: discord.Member) -> bool:
    return member.guild_permissions.administrator or any(
        r.id in STAFF_ROLES for r in member.roles
    )


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ══════════════════════════════════════════════════════════════════════════════
# 1. SMART MODERATION MESSAGES
# ══════════════════════════════════════════════════════════════════════════════

# Keyword → category mapping (checked in order)
_MOD_KEYWORD_MAP = {
    "build":     "build",
    "car":       "build",
    "stance":    "build",
    "fitment":   "build",
    "wheel":     "build",
    "ride":      "build",
    "stock":     "build",
    "lowered":   "build",
    "slammed":   "build",
    "attitude":  "conduct",
    "disrespect":"conduct",
    "rude":      "conduct",
    "toxic":     "conduct",
    "harass":    "conduct",
    "drama":     "conduct",
    "beef":      "conduct",
    "argue":     "conduct",
    "argue":     "conduct",
    "spam":      "spam",
    "flood":     "spam",
    "advertis":  "spam",
    "promote":   "spam",
    "no-show":   "noshow",
    "noshow":    "noshow",
    "miss":      "noshow",
    "absent":    "noshow",
    "show":      "noshow",
    "late":      "noshow",
    "color":     "color",
    "colour":    "color",
    "jacket":    "color",
    "hex":       "color",
    "rule":      "rules",
    "policy":    "rules",
}

_MOD_MESSAGES = {
    "build": [
        "❌ Your build doesn't meet DIFF standards. Stance, fitment, and presentation matter here.",
        "⚠️ DIFF is a clean, quality-focused community. Your current build setup needs work before the next meet.",
        "🚫 Build quality is non-negotiable at DIFF. Review the meet rules and clean it up.",
        "❌ That setup isn't hitting DIFF standards. Lowered, fitted, presentable — that's the bar.",
    ],
    "conduct": [
        "⚠️ Keep it respectful. DIFF is a community — drama and toxicity don't belong here.",
        "❌ Conduct like this won't be tolerated. One community, one standard.",
        "🚫 Disrespect toward members is a serious violation. Next offense results in removal.",
        "⚠️ DIFF standards apply off the road too. How you carry yourself matters.",
    ],
    "spam": [
        "⚠️ Keep it clean in the channels. Spam and unsolicited promotion isn't welcome.",
        "❌ Flooding channels disrupts the community. Keep your posts relevant and intentional.",
        "🚫 Self-promotion and spam violate DIFF rules. Use the right channels or don't post it.",
    ],
    "noshow": [
        "⚠️ No-shows are tracked. If you RSVP'd and didn't show, that counts against your record.",
        "❌ Commitment matters at DIFF. Repeated no-shows without notice will affect your standing.",
        "🚫 Your attendance record has been flagged. Let staff know in advance if you can't make it.",
    ],
    "color": [
        "⚠️ Color submissions must match DIFF crew standards. Review the color guidelines before resubmitting.",
        "❌ That color/jacket doesn't meet the DIFF palette requirements. Coordinate with the color team.",
        "🚫 Unapproved color usage at a meet is a violation. Stick to your approved crew setup.",
    ],
    "rules": [
        "⚠️ DIFF has clear rules for a reason. Please review them — ignorance isn't an excuse.",
        "❌ This is a rule violation. You're expected to know and follow DIFF's standards.",
        "🚫 Repeated rule violations lead to removal. This is your warning.",
    ],
    "general": [
        "⚠️ This behavior doesn't meet DIFF standards. Consider this a formal warning.",
        "❌ DIFF holds every member to a high standard. This violation has been noted.",
        "🚫 You've been flagged for behavior that doesn't align with the DIFF community.",
        "⚠️ Staff have noted this violation. Fix it before your next meet.",
    ],
}

_ESCALATION_LINES = {
    1: ("⚠️ First Warning", discord.Color.yellow(),
        "This is your first warning. We expect better — correct this before your next meet."),
    2: ("🔶 Second Warning", discord.Color.orange(),
        "Two warnings on record. This is serious. One more violation puts your membership at risk."),
    3: ("🚨 Final Warning", discord.Color.red(),
        "Three warnings. You're one step from removal. We don't issue this lightly — act accordingly."),
}
_ESCALATION_DEFAULT = ("🚫 Repeat Offender", discord.Color.dark_red(),
    "Your warning history is significant. Further violations will result in immediate removal from DIFF.")


def _classify_reason(reason: str) -> str:
    lower = reason.lower()
    for kw, cat in _MOD_KEYWORD_MAP.items():
        if kw in lower:
            return cat
    return "general"


def _pick_mod_message(category: str) -> str:
    pool = _MOD_MESSAGES.get(category, _MOD_MESSAGES["general"])
    return random.choice(pool)


def _build_warn_embed(
    member: discord.Member,
    moderator: discord.Member,
    reason: str,
    total: int,
) -> discord.Embed:
    category = _classify_reason(reason)
    branded_msg = _pick_mod_message(category)

    if total in _ESCALATION_LINES:
        badge, color, esc_text = _ESCALATION_LINES[total]
    else:
        badge, color, esc_text = _ESCALATION_DEFAULT

    embed = discord.Embed(
        title=f"{badge} — DIFF Warning Issued",
        description=branded_msg,
        color=color,
        timestamp=_utc_now(),
    )
    embed.add_field(name="👤 Member",     value=member.mention,    inline=True)
    embed.add_field(name="🛡️ Staff",      value=moderator.mention, inline=True)
    embed.add_field(name="📋 Warnings",   value=f"**{total}** on record", inline=True)
    embed.add_field(name="📝 Reason",     value=reason,            inline=False)
    embed.add_field(name="📣 Notice",     value=esc_text,          inline=False)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="DIFF Meets • Moderation System")
    return embed


def _build_dm_embed(
    reason: str,
    total: int,
    guild_name: str,
) -> discord.Embed:
    if total in _ESCALATION_LINES:
        badge, color, esc_text = _ESCALATION_LINES[total]
    else:
        badge, color, esc_text = _ESCALATION_DEFAULT

    embed = discord.Embed(
        title=f"⚠️ You received a warning in {guild_name}",
        description=(
            f"**Reason:** {reason}\n\n"
            f"**Total warnings on record:** {total}\n\n"
            f"{esc_text}"
        ),
        color=color,
        timestamp=_utc_now(),
    )
    embed.set_footer(text="DIFF Meets • You can appeal via a support ticket if you believe this is unfair.")
    return embed


# ══════════════════════════════════════════════════════════════════════════════
# 2. INSIGHTS DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

def _rc_query(sql: str, params: tuple = ()) -> list:
    try:
        conn = sqlite3.connect(RC_DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[SmartFeatures] DB error: {e}")
        return []


def _pct(part: int, total: int) -> str:
    if total == 0:
        return "—"
    return f"{part / total * 100:.0f}%"


def _reliability_grade(attended: int, rsvp_yes: int) -> str:
    if rsvp_yes == 0:
        return "No RSVPs"
    rate = attended / rsvp_yes
    if rate >= 0.9:
        return "🟢 Elite"
    if rate >= 0.7:
        return "🟡 Solid"
    if rate >= 0.5:
        return "🟠 Inconsistent"
    return "🔴 No-Show Risk"


def _generate_insight(stats: dict) -> str:
    """Return a plain-language insight string based on server stats."""
    lines = []
    total_rsvp   = stats.get("total_rsvp", 0)
    total_attend = stats.get("total_attended", 0)
    total_noshow = stats.get("total_noshow", 0)
    unique_rsvp  = stats.get("unique_rsvpers", 0)
    unique_att   = stats.get("unique_attendees", 0)

    if total_rsvp > 0:
        show_rate = total_attend / total_rsvp * 100
        if show_rate >= 75:
            lines.append(f"📈 Strong turnout — **{show_rate:.0f}%** of RSVPs actually showed up.")
        elif show_rate >= 50:
            lines.append(f"⚠️ Moderate attendance — **{show_rate:.0f}%** show-up rate. "
                         "Consider sending earlier reminders.")
        else:
            lines.append(f"🔴 Low turnout — only **{show_rate:.0f}%** of RSVPs attended. "
                         "No-show enforcement may improve this.")

    if total_noshow > 0 and total_rsvp > 0:
        noshow_pct = total_noshow / total_rsvp * 100
        if noshow_pct > 25:
            lines.append(f"🚫 **{noshow_pct:.0f}%** of yes-RSVPs were no-shows — "
                         "consider a strike policy.")

    if unique_rsvp > 0 and unique_att > 0:
        engagement = unique_att / unique_rsvp * 100
        if engagement >= 80:
            lines.append("💪 Your active members are highly engaged and showing up consistently.")
        elif engagement < 50:
            lines.append("📣 Many RSVPers never attend — try a #roll-call-reminder ping 30 min before meets.")

    if not lines:
        lines.append("📊 Not enough finalized meets yet to generate deep insights. "
                     "Finalize attendance after each meet to unlock analytics.")
    return "\n".join(lines)


async def _build_insights_embed(guild: discord.Guild) -> discord.Embed:
    embed = discord.Embed(
        title="📊 DIFF Meets — Server Insights",
        description="Real-time analytics from your roll call system.",
        color=0x5865F2,
        timestamp=_utc_now(),
    )
    embed.set_thumbnail(url=DIFF_LOGO)

    # ── Aggregate stats ───────────────────────────────────────────────────────
    agg = _rc_query(
        """SELECT
             SUM(yes_count)     AS total_yes,
             SUM(maybe_count)   AS total_maybe,
             SUM(no_count)      AS total_no,
             SUM(attended_count)AS total_attended,
             SUM(no_show_count) AS total_noshow,
             COUNT(*)           AS unique_rsvpers
           FROM attendance_stats
           WHERE guild_id = ?""",
        (GUILD_ID,)
    )
    row = agg[0] if agg else {}
    total_yes      = row.get("total_yes")      or 0
    total_maybe    = row.get("total_maybe")    or 0
    total_no       = row.get("total_no")       or 0
    total_attended = row.get("total_attended") or 0
    total_noshow   = row.get("total_noshow")   or 0
    unique_rsvpers = row.get("unique_rsvpers") or 0

    total_rsvp = total_yes + total_maybe + total_no

    embed.add_field(
        name="📋 All-Time RSVP Totals",
        value=(
            f"✅ Yes: **{total_yes}**\n"
            f"❓ Maybe: **{total_maybe}**\n"
            f"❌ No: **{total_no}**\n"
            f"👥 Unique RSVPers: **{unique_rsvpers}**"
        ),
        inline=True,
    )
    embed.add_field(
        name="🏁 Attendance",
        value=(
            f"✔️ Attended: **{total_attended}**\n"
            f"👻 No-Shows: **{total_noshow}**\n"
            f"📊 Show Rate: **{_pct(total_attended, total_yes)}**"
        ),
        inline=True,
    )

    # ── Top 5 most reliable members ───────────────────────────────────────────
    top_members = _rc_query(
        """SELECT user_id, yes_count, attended_count, no_show_count
           FROM attendance_stats
           WHERE guild_id = ? AND yes_count > 0
           ORDER BY attended_count DESC LIMIT 5""",
        (GUILD_ID,)
    )
    if top_members:
        lines = []
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for i, m in enumerate(top_members):
            grade = _reliability_grade(m["attended_count"], m["yes_count"])
            lines.append(
                f"{medals[i]} <@{m['user_id']}> — "
                f"**{m['attended_count']}** attended · {grade}"
            )
        embed.add_field(
            name="🏆 Most Reliable Attendees",
            value="\n".join(lines),
            inline=False,
        )
    else:
        embed.add_field(
            name="🏆 Most Reliable Attendees",
            value="No finalized attendance data yet.",
            inline=False,
        )

    # ── No-show watch list (top 3 worst) ─────────────────────────────────────
    noshow_risk = _rc_query(
        """SELECT user_id, yes_count, no_show_count
           FROM attendance_stats
           WHERE guild_id = ? AND no_show_count >= 2
           ORDER BY no_show_count DESC LIMIT 3""",
        (GUILD_ID,)
    )
    if noshow_risk:
        lines = [
            f"⚠️ <@{r['user_id']}> — **{r['no_show_count']}** no-shows / {r['yes_count']} RSVPs"
            for r in noshow_risk
        ]
        embed.add_field(
            name="👻 No-Show Watch List",
            value="\n".join(lines),
            inline=False,
        )

    # ── Current meet snapshot ─────────────────────────────────────────────────
    meets = _rc_query(
        "SELECT meet_number, is_finalized FROM rollcall_meets WHERE guild_id = ?",
        (GUILD_ID,)
    )
    if meets:
        finalized = sum(1 for m in meets if m["is_finalized"])
        pending   = len(meets) - finalized
        embed.add_field(
            name="📅 Current Meet Cycle",
            value=f"**{finalized}** finalized · **{pending}** still pending",
            inline=True,
        )

    # ── Smart insight ─────────────────────────────────────────────────────────
    insight_text = _generate_insight({
        "total_rsvp":       total_rsvp,
        "total_attended":   total_attended,
        "total_noshow":     total_noshow,
        "unique_rsvpers":   unique_rsvpers,
        "unique_attendees": len(top_members),
    })
    embed.add_field(
        name="🧠 Smart Insight",
        value=insight_text,
        inline=False,
    )

    embed.set_footer(text="DIFF Meets • Insights Dashboard • Data from roll call system")
    return embed


# ══════════════════════════════════════════════════════════════════════════════
# 3. COLOR LAB TICKET ASSISTANT
# ══════════════════════════════════════════════════════════════════════════════

_FINISH_TIPS = {
    "matte":    "Matte finishes look sharp when paired with flat or satin black accents — avoid glossy chrome.",
    "gloss":    "Gloss works with most wheel finishes. Deep-dish or mesh wheels with a polished lip look clean.",
    "metallic": "Metallic paint pops best in natural light — consider a subtle gloss or chrome accent piece.",
    "satin":    "Satin is versatile. It bridges the gap between matte and gloss — great for a subtle, premium look.",
    "chrome":   "Chrome is bold — keep everything else minimal. One chrome element goes a long way.",
    "pearl":    "Pearl finishes shift in light — they pair best with clean, minimal bodywork and matching trim.",
    "flat":     "Flat finishes have an aggressive look — pair with matte black hardware for a cohesive build.",
}

_RIM_ADVICE = [
    "Darker rims (gunmetal, gloss black) complement most mid-tone body colors and keep the look aggressive.",
    "For lighter body colors, go with bronze, gold, or a polished finish to add warmth.",
    "Two-tone wheels (polished lip + dark dish) add depth without clashing with most paint.",
    "Avoid matching your rim color exactly to your body — contrast is what makes a build stand out.",
]

_STANCE_TIPS = [
    "A slight drop makes a massive visual difference — even 1–2 inches tightens the wheel gap significantly.",
    "Flush fitment (wheel edge level with the fender lip) is the DIFF standard for a clean look.",
    "Negative camber adds visual flair but can affect handling — keep it tasteful, not extreme.",
    "If your car sits high, coilovers or lowering springs should be your first upgrade for meets.",
]

_GENERAL_COLOR_TIPS = [
    "Keep your color crew-consistent — coordinate with your leader before finalizing a new primary color.",
    "Crew jacket colors are non-negotiable at meets — confirm your hex code with the color team first.",
    "Less is more: pick one accent color and stick with it throughout the build.",
    "Reference real-world car photos when choosing shades — GTA's palette can look different in daylight.",
]


def _build_color_assistant_embed(
    member: discord.Member,
    channel: discord.TextChannel,
) -> discord.Embed:
    """Build an instant reply embed for a new color lab ticket."""

    # Try to extract submission details from the channel's pinned/first bot embed
    finish_tip = None
    for kw, tip in _FINISH_TIPS.items():
        if kw in channel.name.lower() or kw in (channel.topic or "").lower():
            finish_tip = tip
            break

    rim_tip    = random.choice(_RIM_ADVICE)
    stance_tip = random.choice(_STANCE_TIPS)
    color_tip  = random.choice(_GENERAL_COLOR_TIPS)

    embed = discord.Embed(
        title="🎨 Color Lab — Instant Style Guide",
        description=(
            f"Hey {member.mention}! Your color request has been received. "
            "While the Color Team reviews it, here's some expert guidance to set your build up right:"
        ),
        color=0x8F7CFF,
        timestamp=_utc_now(),
    )

    if finish_tip:
        embed.add_field(name="✨ Finish Advice", value=finish_tip, inline=False)

    embed.add_field(name="🔵 Rim & Wheel Pairing", value=rim_tip,    inline=False)
    embed.add_field(name="📐 Stance & Fitment",    value=stance_tip, inline=False)
    embed.add_field(name="🎯 Color Strategy",       value=color_tip,  inline=False)

    embed.add_field(
        name="⏳ What Happens Next",
        value=(
            "The Color Team will review your submission and reply here with feedback or approval.\n"
            "Please have **reference photos** ready if asked — real-world examples help a lot."
        ),
        inline=False,
    )

    embed.set_thumbnail(url=DIFF_LOGO)
    embed.set_footer(text="DIFF Meets • Color Lab Assistant • Powered by Color Team expertise")
    return embed


# ══════════════════════════════════════════════════════════════════════════════
# COG
# ══════════════════════════════════════════════════════════════════════════════

class SmartFeaturesCog(commands.Cog, name="SmartFeatures"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._color_replied: set[int] = set()   # channel IDs already auto-replied
        print("[SmartFeatures] Cog ready.")

    # ── 1. Smart Warning ──────────────────────────────────────────────────────

    @commands.command(name="diff_warn")
    @commands.has_permissions(manage_messages=True)
    async def diff_warn(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "Violation of DIFF community standards",
    ) -> None:
        """Issue a branded, escalating warning to a member."""
        if member.bot:
            return await ctx.send("You can't warn bots.", delete_after=5)

        m = _main()
        try:
            m.add_warning(member.id, ctx.author.id, reason)
            total = m.get_warning_count(member.id)
        except Exception as e:
            return await ctx.send(f"Warning recorded locally. (DB hook error: {e})", delete_after=10)

        pub_embed = _build_warn_embed(member, ctx.author, reason, total)
        await ctx.send(embed=pub_embed)

        try:
            dm_embed = _build_dm_embed(reason, total, ctx.guild.name if ctx.guild else "DIFF")
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass

        # Clean up the command invocation
        try:
            await ctx.message.delete()
        except Exception:
            pass

    # ── 2. Insights Dashboard ─────────────────────────────────────────────────

    @commands.command(name="diff_insights")
    @commands.has_permissions(manage_messages=True)
    async def diff_insights(self, ctx: commands.Context) -> None:
        """Show the DIFF server insights dashboard (staff only)."""
        async with ctx.typing():
            embed = await _build_insights_embed(ctx.guild)
        await ctx.send(embed=embed)

    # ── 3. Color Lab Ticket Assistant ─────────────────────────────────────────

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        if not isinstance(message.channel, discord.TextChannel):
            return

        ch = message.channel
        # Only fire in color-* ticket channels
        if not ch.name.startswith(COLOR_LAB_CATEGORY):
            return

        # Don't reply twice in the same channel
        if ch.id in self._color_replied:
            return

        # Skip staff messages — only react to the first applicant post
        member = message.author
        if not isinstance(member, discord.Member):
            return
        if _is_staff(member):
            return

        self._color_replied.add(ch.id)

        embed = _build_color_assistant_embed(member, ch)
        try:
            await ch.send(
                content=member.mention,
                embed=embed,
                allowed_mentions=discord.AllowedMentions(users=True),
            )
            print(f"[SmartFeatures] Color assistant reply sent in #{ch.name}")
        except Exception as e:
            print(f"[SmartFeatures] Color assistant send error: {e}")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        self._color_replied.discard(channel.id)


print("[SmartFeatures] Module loaded OK.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SmartFeaturesCog(bot))
