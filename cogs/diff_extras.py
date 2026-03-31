"""
cogs/diff_extras.py
────────────────────────────────
Three new community features for DIFF Meets.

 1.  Post-Meet Photo Board  (!openphotomeet, !closephotomeet)
      - Staff opens a timed submission window in the meet channel
      - Members post screenshots; bot collects them
      - When window closes, gallery embed posted with 🏆 vote buttons
      - After vote period, winner announced

 2.  Meet Wrapup            (!meetwrapup @host <name> [car_class])
      - Auto-posts a public recap embed to the recap channel
      - DMs every checked-in attendee a ⭐ star-rating button embed
      - Ratings saved; average surfaced on the host's record

 3.  Crew Roster Panel      (!crewroster)
      - Posts / refreshes a live embed listing all DIFF members by rank
      - Leaders → Co-Leaders → Managers → Hosts → Crew member count
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands

# ── Timezone ──────────────────────────────────────────────────────────────────
_EST = ZoneInfo("America/New_York")


def _now() -> datetime:
    return datetime.now(_EST)


# ── Main-bot globals ──────────────────────────────────────────────────────────
def _main():
    return sys.modules.get("__main__")


def _get(name, default=None):
    m = _main()
    return getattr(m, name, default) if m else default


def _GUILD_ID()       -> int: return _get("GUILD_ID",               0)
def _LOGO()           -> str: return _get("DIFF_LOGO_URL",          "")
def _BANNER()         -> str: return _get("DIFF_BANNER_URL",        "")
def _RECAP_CH()       -> int: return _get("RECAP_CHANNEL_ID",       0)
def _STAFF_LOGS()     -> int: return _get("STAFF_LOGS_CHANNEL_ID",  0)
def _LEADER()         -> int: return _get("LEADER_ROLE_ID",         0)
def _CO_LEADER()      -> int: return _get("CO_LEADER_ROLE_ID",      0)
def _MANAGER()        -> int: return _get("MANAGER_ROLE_ID",        0)
def _HOST()           -> int: return _get("HOST_ROLE_ID",           0)
def _CREW()           -> int: return _get("CREW_MEMBER_ROLE_ID",    0)
def _MEETS_FILE()     -> str: return _get("MEETS_FILE", "diff_data/diff_meet_records.json")

# ── Data paths ────────────────────────────────────────────────────────────────
_DATA               = "diff_data"
_BOARD_FILE         = os.path.join(_DATA, "diff_photo_board.json")
_RATINGS_FILE       = os.path.join(_DATA, "diff_wrapup_ratings.json")
_ROSTER_FILE        = os.path.join(_DATA, "diff_roster_panel.json")


# ── JSON helpers ──────────────────────────────────────────────────────────────
def _load(path: str, default=None):
    if default is None:
        default = {}
    os.makedirs(_DATA, exist_ok=True)
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save(path: str, data) -> None:
    os.makedirs(_DATA, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ── Staff check ───────────────────────────────────────────────────────────────
def _is_staff(member: discord.Member) -> bool:
    staff_ids = {_LEADER(), _CO_LEADER(), _MANAGER(), _HOST()}
    return (
        member.guild_permissions.administrator
        or any(r.id in staff_ids for r in member.roles)
    )


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE 1 — POST-MEET PHOTO BOARD
# ══════════════════════════════════════════════════════════════════════════════

class _VoteButton(discord.ui.Button):
    """A 🏆 button on a gallery photo. Each user gets one vote per window."""

    def __init__(self, window_id: str, photo_index: int) -> None:
        super().__init__(
            label="🏆 Vote",
            style=discord.ButtonStyle.secondary,
            custom_id=f"diffphoto_vote_{window_id}_{photo_index}",
        )
        self.window_id  = window_id
        self.photo_index = photo_index

    async def callback(self, interaction: discord.Interaction) -> None:
        uid = str(interaction.user.id)
        board = _load(_BOARD_FILE)
        window = board.get(self.window_id)
        if not window or window.get("gallery_closed"):
            await interaction.response.send_message(
                "This voting window has already closed.", ephemeral=True
            )
            return

        voters = window.setdefault("voters", {})
        if uid in voters:
            await interaction.response.send_message(
                "You've already voted in this photo window.", ephemeral=True
            )
            return

        voters[uid] = self.photo_index
        photos = window.setdefault("photos", [])
        if self.photo_index < len(photos):
            photos[self.photo_index]["votes"] = photos[self.photo_index].get("votes", 0) + 1
        _save(_BOARD_FILE, board)
        await interaction.response.send_message("✅ Vote recorded — thanks!", ephemeral=True)


class _VoteView(discord.ui.View):
    def __init__(self, window_id: str, photo_index: int) -> None:
        super().__init__(timeout=None)
        self.add_item(_VoteButton(window_id, photo_index))


# ── Background task registry (window_id → asyncio.Task) ─────────────────────
_photo_tasks: dict[str, asyncio.Task] = {}


async def _run_photo_window(
    bot: commands.Bot,
    window_id: str,
    channel_id: int,
    submit_seconds: int,
    vote_seconds: int,
) -> None:
    """Background task: wait → close submissions → wait → announce winner."""
    await asyncio.sleep(submit_seconds)

    board = _load(_BOARD_FILE)
    window = board.get(window_id)
    if not window or window.get("closed"):
        return

    window["closed"] = True
    _save(_BOARD_FILE, board)

    channel = bot.get_channel(channel_id)
    photos  = window.get("photos", [])

    if not photos:
        if isinstance(channel, discord.TextChannel):
            await channel.send(
                "📷 Photo submission window closed — no photos were submitted this time."
            )
        return

    gallery_msgs: list[int] = []
    if isinstance(channel, discord.TextChannel):
        await channel.send(
            f"📸 **Submission window closed!** {len(photos)} photo(s) collected.\n"
            f"Vote on your favourite with the 🏆 button below. "
            f"Voting ends in **{vote_seconds // 60}m**."
        )
        for i, photo in enumerate(photos):
            submitter_mention = f"<@{photo['user_id']}>"
            embed = discord.Embed(
                description=f"📸 Photo **#{i + 1}** submitted by {submitter_mention}",
                color=discord.Color.gold(),
            )
            embed.set_image(url=photo["url"])
            embed.set_footer(text=f"DIFF Meets • Photo Board • Window {window_id}")
            msg = await channel.send(embed=embed, view=_VoteView(window_id, i))
            gallery_msgs.append(msg.id)

    board = _load(_BOARD_FILE)
    window = board.get(window_id, window)
    window["gallery_msgs"] = gallery_msgs
    _save(_BOARD_FILE, board)

    await asyncio.sleep(vote_seconds)

    board  = _load(_BOARD_FILE)
    window = board.get(window_id, {})
    window["gallery_closed"] = True
    _save(_BOARD_FILE, board)

    photos = window.get("photos", [])
    if not photos:
        return

    winner_idx = max(range(len(photos)), key=lambda i: photos[i].get("votes", 0))
    winner     = photos[winner_idx]
    top_votes  = winner.get("votes", 0)

    if isinstance(channel, discord.TextChannel):
        if top_votes == 0:
            await channel.send("🏆 Voting closed — no votes were cast. Everyone's a winner! 🚗")
        else:
            embed = discord.Embed(
                title="🏆 Photo Board Winner!",
                description=(
                    f"Congratulations to <@{winner['user_id']}> for winning this meet's photo competition!\n\n"
                    f"**{top_votes}** vote(s) · Photo #{winner_idx + 1}"
                ),
                color=discord.Color.gold(),
                timestamp=_now(),
            )
            embed.set_image(url=winner["url"])
            embed.set_footer(text="DIFF Meets • Photo Board")
            await channel.send(embed=embed)

    _photo_tasks.pop(window_id, None)


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE 2 — MEET WRAPUP (ratings)
# ══════════════════════════════════════════════════════════════════════════════

class _StarButton(discord.ui.Button):
    def __init__(self, stars: int, meet_id: str) -> None:
        super().__init__(
            label="⭐" * stars,
            style=discord.ButtonStyle.secondary,
            custom_id=f"diffrating_{meet_id}_{stars}",
        )
        self.stars   = stars
        self.meet_id = meet_id

    async def callback(self, interaction: discord.Interaction) -> None:
        uid = str(interaction.user.id)
        ratings = _load(_RATINGS_FILE)
        meet    = ratings.setdefault(self.meet_id, {"ratings": {}, "host_id": None})
        if uid in meet.get("ratings", {}):
            await interaction.response.send_message(
                "You've already rated this meet — thanks!", ephemeral=True
            )
            return
        meet.setdefault("ratings", {})[uid] = self.stars
        _save(_RATINGS_FILE, ratings)
        for child in self.view.children:
            child.disabled = True  # type: ignore[union-attr]
        try:
            await interaction.message.edit(view=self.view)
        except Exception:
            pass
        stars_str = "\u2b50" * self.stars
        await interaction.response.send_message(
            f"{stars_str} Thanks for rating this meet! Your feedback helps the host improve.",
            ephemeral=True,
        )


class _RatingView(discord.ui.View):
    def __init__(self, meet_id: str) -> None:
        super().__init__(timeout=None)
        for s in range(1, 6):
            self.add_item(_StarButton(s, meet_id))


# ══════════════════════════════════════════════════════════════════════════════
# MAIN COG
# ══════════════════════════════════════════════════════════════════════════════

class DiffExtras(commands.Cog):
    """Photo Board · Meet Wrapup · Crew Roster"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._re_register_votes()

    def _re_register_votes(self) -> None:
        """Re-attach persistent vote views after restart."""
        board = _load(_BOARD_FILE)
        for wid, window in board.items():
            if window.get("gallery_closed"):
                continue
            for i in range(len(window.get("photos", []))):
                self.bot.add_view(_VoteView(wid, i))

    def _is_staff(self, ctx: commands.Context) -> bool:
        if not isinstance(ctx.author, discord.Member):
            return False
        return _is_staff(ctx.author)

    async def _del(self, ctx: commands.Context) -> None:
        try:
            await ctx.message.delete()
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────────────────────
    # on_message — collect photo submissions
    # ──────────────────────────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        board = _load(_BOARD_FILE)
        for wid, window in board.items():
            if window.get("closed"):
                continue
            if window.get("channel_id") != message.channel.id:
                continue
            for att in message.attachments:
                if att.content_type and att.content_type.startswith("image"):
                    window.setdefault("photos", []).append(
                        {
                            "user_id": message.author.id,
                            "url":     att.url,
                            "votes":   0,
                        }
                    )
                    _save(_BOARD_FILE, board)
                    try:
                        await message.add_reaction("📸")
                    except Exception:
                        pass
                    break

    # ──────────────────────────────────────────────────────────────────────────
    # 1a. !openphotomeet
    # ──────────────────────────────────────────────────────────────────────────

    @commands.command(name="openphotomeet")
    async def openphotomeet(
        self,
        ctx: commands.Context,
        submit_minutes: int = 30,
        vote_minutes: int = 30,
    ) -> None:
        """Open a photo submission window in this channel. Staff only.
        Usage: !openphotomeet [submit_minutes=30] [vote_minutes=30]"""
        if not self._is_staff(ctx):
            return await ctx.send("❌ Staff only.", delete_after=8)
        await self._del(ctx)

        board = _load(_BOARD_FILE)
        for wid, window in board.items():
            if window.get("channel_id") == ctx.channel.id and not window.get("closed"):
                return await ctx.send(
                    "⚠️ There's already an active photo window in this channel. "
                    "Use `!closephotomeet` first.",
                    delete_after=12,
                )

        window_id = f"{ctx.channel.id}_{int(_now().timestamp())}"
        board[window_id] = {
            "channel_id":     ctx.channel.id,
            "opened_by":      ctx.author.id,
            "submit_minutes": submit_minutes,
            "vote_minutes":   vote_minutes,
            "photos":         [],
            "voters":         {},
            "closed":         False,
            "gallery_closed": False,
        }
        _save(_BOARD_FILE, board)

        embed = discord.Embed(
            title="📸 Photo Submission Window — OPEN!",
            description=(
                f"Send your best screenshot from tonight's meet right here in this channel!\n\n"
                f"🕐 **Submissions close in:** {submit_minutes} minute(s)\n"
                f"🏆 **Voting opens** immediately after and runs for {vote_minutes} minute(s)\n\n"
                "One photo per person · Must be an in-game screenshot · No edits"
            ),
            color=discord.Color.gold(),
            timestamp=_now(),
        )
        embed.set_thumbnail(url=_LOGO())
        embed.set_footer(text="DIFF Meets • Photo Board")
        await ctx.send(embed=embed)

        task = asyncio.create_task(
            _run_photo_window(
                self.bot,
                window_id,
                ctx.channel.id,
                submit_minutes * 60,
                vote_minutes * 60,
            )
        )
        _photo_tasks[window_id] = task

    # ──────────────────────────────────────────────────────────────────────────
    # 1b. !closephotomeet
    # ──────────────────────────────────────────────────────────────────────────

    @commands.command(name="closephotomeet")
    async def closephotomeet(self, ctx: commands.Context) -> None:
        """Manually close the active photo submission window in this channel. Staff only."""
        if not self._is_staff(ctx):
            return await ctx.send("❌ Staff only.", delete_after=8)
        await self._del(ctx)

        board = _load(_BOARD_FILE)
        active_wid: Optional[str] = None
        for wid, window in board.items():
            if window.get("channel_id") == ctx.channel.id and not window.get("closed"):
                active_wid = wid
                break

        if not active_wid:
            return await ctx.send("⚠️ No active photo window in this channel.", delete_after=10)

        task = _photo_tasks.pop(active_wid, None)
        if task and not task.done():
            task.cancel()

        window = board[active_wid]
        window["closed"] = True
        _save(_BOARD_FILE, board)

        photos = window.get("photos", [])
        vote_minutes = window.get("vote_minutes", 30)

        if not photos:
            return await ctx.send(
                "📷 Photo window closed — no submissions were received.", delete_after=15
            )

        await ctx.send(
            f"📸 Submission window manually closed. {len(photos)} photo(s) collected.\n"
            f"Voting starts now and runs for **{vote_minutes}m**."
        )

        task = asyncio.create_task(
            _run_photo_window(
                self.bot,
                active_wid,
                ctx.channel.id,
                0,
                vote_minutes * 60,
            )
        )
        _photo_tasks[active_wid] = task

    # ──────────────────────────────────────────────────────────────────────────
    # 2. !meetwrapup
    # ──────────────────────────────────────────────────────────────────────────

    @commands.command(name="meetwrapup")
    async def meetwrapup(
        self,
        ctx: commands.Context,
        host: discord.Member,
        *,
        meet_name: str,
    ) -> None:
        """Auto-post a recap and DM attendees a star-rating prompt. Staff only.
        Usage: !meetwrapup @host <meet_name>"""
        if not self._is_staff(ctx):
            return await ctx.send("❌ Staff only.", delete_after=8)
        await self._del(ctx)

        now     = _now()
        meet_id = f"{int(now.timestamp())}_{host.id}"

        ratings = _load(_RATINGS_FILE)
        ratings[meet_id] = {"ratings": {}, "host_id": host.id, "meet_name": meet_name}
        _save(_RATINGS_FILE, ratings)

        recap_ch = ctx.guild.get_channel(_RECAP_CH()) if ctx.guild else None

        checked_in: list[int] = []
        meets = _load(_MEETS_FILE())
        for _mid, meet in meets.items():
            if meet_name.lower() in (_mid.lower() + " " + meet.get("title", "").lower()):
                checked_in = [int(uid) for uid in meet.get("checked_in", [])]
                break

        if not checked_in and ctx.guild:
            attender_role = ctx.guild.get_role(_get("MEET_ATTENDER_ROLE_ID", 0) or 0)
            if attender_role:
                checked_in = [m.id for m in attender_role.members]

        avg_str = "No ratings yet"
        embed = discord.Embed(
            title=f"🏁 Meet Recap — {meet_name}",
            color=discord.Color.green(),
            timestamp=now,
        )
        embed.set_thumbnail(url=_LOGO())
        embed.set_image(url=_BANNER())
        embed.add_field(name="🎮 Host",       value=host.mention,          inline=True)
        embed.add_field(name="🚗 Attendees",  value=str(len(checked_in)) or "—", inline=True)
        embed.add_field(name="⭐ Avg Rating", value=avg_str,               inline=True)
        embed.add_field(
            name="📋 Summary",
            value=(
                f"Thanks to everyone who attended **{meet_name}**!\n"
                "Check your DMs to rate tonight's meet — your feedback helps the host improve. 💬"
            ),
            inline=False,
        )
        embed.set_footer(
            text=f"DIFF Meets • Recap posted by {ctx.author.display_name} • {now.strftime('%b %d, %Y %-I:%M %p EST')}"
        )

        target = isinstance(recap_ch, discord.TextChannel) and recap_ch or ctx.channel
        await target.send(embed=embed)
        if target != ctx.channel:
            await ctx.send(f"✅ Recap posted in {target.mention}.", delete_after=8)

        rating_embed = discord.Embed(
            title=f"⭐ Rate Tonight's Meet — {meet_name}",
            description=(
                f"**Host:** {host.display_name}\n\n"
                "How would you rate tonight's meet?\n"
                "Tap a star rating below — it takes 2 seconds and really helps!\n\n"
                "⭐ = Poor &nbsp;&nbsp; ⭐⭐⭐ = Good &nbsp;&nbsp; ⭐⭐⭐⭐⭐ = Amazing"
            ),
            color=discord.Color.gold(),
            timestamp=now,
        )
        rating_embed.set_thumbnail(url=_LOGO())
        rating_embed.set_footer(text="DIFF Meets • Meet Rating • One vote per person")

        view = _RatingView(meet_id)
        dmed = 0
        failed = 0
        for uid in checked_in:
            member = ctx.guild.get_member(uid) if ctx.guild else None
            if not member or member.bot:
                continue
            try:
                await member.send(embed=rating_embed, view=view)
                dmed += 1
            except discord.Forbidden:
                failed += 1
            except Exception:
                failed += 1

        status = f"✅ Wrapup complete — {dmed} rating DM(s) sent"
        if failed:
            status += f", {failed} failed (DMs closed)"
        await ctx.send(status, delete_after=15)

        log_ch = ctx.guild.get_channel(_STAFF_LOGS()) if ctx.guild else None
        if isinstance(log_ch, discord.TextChannel):
            log_embed = discord.Embed(
                title="📋 Meet Wrapup Triggered",
                color=discord.Color.blue(),
                timestamp=now,
            )
            log_embed.add_field(name="Meet",     value=meet_name,           inline=True)
            log_embed.add_field(name="Host",     value=host.mention,        inline=True)
            log_embed.add_field(name="DMs Sent", value=str(dmed),           inline=True)
            log_embed.add_field(name="Staff",    value=ctx.author.mention,  inline=True)
            log_embed.set_footer(text="DIFF Meets • Meet Wrapup")
            try:
                await log_ch.send(embed=log_embed)
            except Exception:
                pass

    # ──────────────────────────────────────────────────────────────────────────
    # 2b. !wrapupratings — show ratings for a recent wrapup
    # ──────────────────────────────────────────────────────────────────────────

    @commands.command(name="wrapupratings")
    async def wrapupratings(self, ctx: commands.Context, *, meet_name: str = "") -> None:
        """Show collected ratings for a recent meet wrapup. Staff only."""
        if not self._is_staff(ctx):
            return await ctx.send("❌ Staff only.", delete_after=8)
        await self._del(ctx)

        ratings = _load(_RATINGS_FILE)
        if not ratings:
            return await ctx.send("No wrapup ratings on record yet.", delete_after=10)

        if meet_name:
            matches = {
                mid: data for mid, data in ratings.items()
                if meet_name.lower() in data.get("meet_name", "").lower()
            }
        else:
            matches = ratings

        if not matches:
            return await ctx.send(f"No ratings found for `{meet_name}`.", delete_after=10)

        sorted_meets = sorted(matches.items(), key=lambda x: x[0], reverse=True)[:5]
        embed = discord.Embed(
            title="⭐ Meet Wrapup Ratings",
            color=discord.Color.gold(),
            timestamp=_now(),
        )
        embed.set_thumbnail(url=_LOGO())

        for mid, data in sorted_meets:
            r = data.get("ratings", {})
            host_id  = data.get("host_id")
            name     = data.get("meet_name", mid)
            if r:
                avg  = sum(r.values()) / len(r)
                avg_str = f"{'⭐' * round(avg)} ({avg:.1f}/5, {len(r)} vote(s))"
            else:
                avg_str = "No votes yet"
            embed.add_field(
                name=f"🏁 {name}",
                value=f"Host: <@{host_id}>\nRating: {avg_str}",
                inline=False,
            )

        embed.set_footer(text="DIFF Meets • Wrapup Ratings")
        await ctx.send(embed=embed)

    # ──────────────────────────────────────────────────────────────────────────
    # 3. !crewroster
    # ──────────────────────────────────────────────────────────────────────────

    @commands.command(name="crewroster")
    async def crewroster(self, ctx: commands.Context) -> None:
        """Post or refresh the DIFF crew roster embed. Staff only."""
        if not self._is_staff(ctx):
            return await ctx.send("❌ Staff only.", delete_after=8)
        await self._del(ctx)

        if not ctx.guild:
            return

        await ctx.send("⏳ Building roster…", delete_after=5)

        role_tiers = [
            (_LEADER(),    "👑 Leader"),
            (_CO_LEADER(), "🔱 Co-Leader"),
            (_MANAGER(),   "🛠️ Manager"),
            (_HOST(),      "🎙️ Host"),
        ]

        crew_role_id  = _CREW()
        crew_role     = ctx.guild.get_role(crew_role_id) if crew_role_id else None
        crew_count    = len(crew_role.members) if crew_role else 0

        now   = _now()
        embed = discord.Embed(
            title="🏁 DIFF Meets — Crew Roster",
            description="*Active staff and crew members of Different Meets.*",
            color=discord.Color.from_str("#0F3460"),
            timestamp=now,
        )
        embed.set_thumbnail(url=_LOGO())

        total_staff = 0
        for role_id, label in role_tiers:
            role = ctx.guild.get_role(role_id) if role_id else None
            if not role or not role.members:
                embed.add_field(name=label, value="_None_", inline=True)
                continue
            members = sorted(role.members, key=lambda m: m.display_name.lower())
            total_staff += len(members)
            lines = "\n".join(f"• {m.mention}" for m in members[:15])
            if len(members) > 15:
                lines += f"\n*+{len(members) - 15} more*"
            embed.add_field(name=f"{label} ({len(members)})", value=lines, inline=True)

        embed.add_field(
            name=f"🚗 Crew Members ({crew_count})",
            value=(
                f"**{crew_count}** verified crew member(s).\n"
                f"See <#{ctx.channel.id}> for applications."
            ),
            inline=False,
        )
        embed.add_field(
            name="📊 Totals",
            value=(
                f"Staff: **{total_staff}** · "
                f"Crew: **{crew_count}** · "
                f"Total: **{total_staff + crew_count}**"
            ),
            inline=False,
        )
        embed.set_footer(
            text=f"DIFF Meets • Last updated {now.strftime('%b %d, %Y %-I:%M %p EST')}"
        )

        roster_state = _load(_ROSTER_FILE)
        channel_id   = roster_state.get("channel_id")
        message_id   = roster_state.get("message_id")

        target_msg: Optional[discord.Message] = None
        if channel_id and message_id:
            ch = ctx.guild.get_channel(int(channel_id))
            if isinstance(ch, discord.TextChannel):
                try:
                    target_msg = await ch.fetch_message(int(message_id))
                except Exception:
                    target_msg = None

        if target_msg:
            await target_msg.edit(embed=embed)
            await ctx.send(
                f"✅ Crew roster refreshed in {target_msg.channel.mention}.", delete_after=8
            )
        else:
            msg = await ctx.channel.send(embed=embed)
            _save(_ROSTER_FILE, {"channel_id": ctx.channel.id, "message_id": msg.id})
            await ctx.send("✅ Crew roster posted.", delete_after=8)


# ══════════════════════════════════════════════════════════════════════════════
# SETUP
# ══════════════════════════════════════════════════════════════════════════════

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DiffExtras(bot))
