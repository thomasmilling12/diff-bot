from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import discord
from discord.ext import commands, tasks

GUILD_ID               = 850386896509337710
WELCOME_POST_CHANNEL_ID = 1486006000808103986
RULES_CHANNEL_ID       = 1047161846257438743
JOIN_MEETS_HUB_CHANNEL_ID = 1277084633858576406
VERIFICATION_LOG_CHANNEL_ID = 1485265848099799163
VERIFIED_ROLE_ID       = 1141424243616256032
UNVERIFIED_ROLE_ID     = 1486011550916411512
MEET_ANNOUNCEMENT_CHANNEL_ID = 1484768466023223418
UPCOMING_MEET_CHANNEL_ID     = 1485861257708834836
DIFF_HOSTS_CHANNEL_ID        = 1195953265377021952
MEET_INFO_CHANNEL_ID         = 1266933655486332999

REMINDER_AFTER_HOURS        = 2
REMINDER_CHECK_EVERY_MINUTES = 10
SEND_VERIFIED_DM            = True

EMBLEM_FILE_PATH = Path("diff_welcome_emblem.png")
FOOTER_TEXT      = "DIFF • Complete the steps to unlock the meet area"
DB_FILE          = "diff_data/diff_checkin.sqlite3"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def fmt_ts(dt: datetime) -> str:
    return f"<t:{int(dt.timestamp())}:F>"


def weekly_color() -> discord.Color:
    palette = {
        0: discord.Color.from_rgb(88, 101, 242),
        1: discord.Color.from_rgb(235, 69, 90),
        2: discord.Color.from_rgb(46, 204, 113),
        3: discord.Color.from_rgb(241, 196, 15),
        4: discord.Color.from_rgb(155, 89, 182),
        5: discord.Color.from_rgb(26, 188, 156),
        6: discord.Color.from_rgb(230, 126, 34),
    }
    return palette.get(datetime.now().weekday(), discord.Color.blurple())


@dataclass
class ProgressState:
    has_verified_role: bool
    posted_in_join_hub: bool
    cleared_to_enter: bool

    @property
    def complete_count(self) -> int:
        return sum([self.has_verified_role, self.posted_in_join_hub, self.cleared_to_enter])

    def progress_bar(self) -> str:
        done = "█" * self.complete_count
        left = "░" * (3 - self.complete_count)
        return f"{done}{left}  ({self.complete_count}/3)"


class CheckInDB:
    def __init__(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._setup()

    def _setup(self) -> None:
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS member_checkin (
                user_id INTEGER PRIMARY KEY,
                joined_at TEXT,
                posted_in_join_hub INTEGER DEFAULT 0,
                posted_in_join_hub_at TEXT,
                verified_at TEXT,
                reminder_sent INTEGER DEFAULT 0,
                reminder_sent_at TEXT
            )
        """)
        self.conn.commit()

    def upsert_join(self, user_id: int) -> None:
        self.conn.execute("""
            INSERT INTO member_checkin (user_id, joined_at, posted_in_join_hub, reminder_sent)
            VALUES (?, ?, 0, 0)
            ON CONFLICT(user_id) DO UPDATE SET
                joined_at=excluded.joined_at,
                posted_in_join_hub=0,
                posted_in_join_hub_at=NULL,
                verified_at=NULL,
                reminder_sent=0,
                reminder_sent_at=NULL
        """, (user_id, utcnow().isoformat()))
        self.conn.commit()

    def mark_join_hub_post(self, user_id: int) -> None:
        self.conn.execute("""
            INSERT INTO member_checkin (user_id, joined_at, posted_in_join_hub, posted_in_join_hub_at)
            VALUES (?, ?, 1, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                posted_in_join_hub=1,
                posted_in_join_hub_at=excluded.posted_in_join_hub_at
        """, (user_id, utcnow().isoformat(), utcnow().isoformat()))
        self.conn.commit()

    def mark_verified(self, user_id: int) -> None:
        self.conn.execute("""
            INSERT INTO member_checkin (user_id, joined_at, verified_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET verified_at=excluded.verified_at
        """, (user_id, utcnow().isoformat(), utcnow().isoformat()))
        self.conn.commit()

    def clear_verified(self, user_id: int) -> None:
        self.conn.execute("UPDATE member_checkin SET verified_at=NULL WHERE user_id=?", (user_id,))
        self.conn.commit()

    def mark_reminder_sent(self, user_id: int) -> None:
        self.conn.execute(
            "UPDATE member_checkin SET reminder_sent=1, reminder_sent_at=? WHERE user_id=?",
            (utcnow().isoformat(), user_id),
        )
        self.conn.commit()

    def get_row(self, user_id: int):
        return self.conn.execute(
            "SELECT * FROM member_checkin WHERE user_id=?", (user_id,)
        ).fetchone()

    def reminder_candidates(self):
        threshold = (utcnow() - timedelta(hours=REMINDER_AFTER_HOURS)).isoformat()
        return self.conn.execute("""
            SELECT * FROM member_checkin
            WHERE reminder_sent=0 AND verified_at IS NULL
              AND joined_at IS NOT NULL AND joined_at <= ?
        """, (threshold,)).fetchall()


class CheckInHelpSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            custom_id="diff_checkin_help_select_v1",
            placeholder="📋 Need help? — choose an option...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Check My Progress",
                    value="progress",
                    emoji="📊",
                    description="See which check-in steps you've completed.",
                ),
                discord.SelectOption(
                    label="How does check-in work?",
                    value="howto",
                    emoji="❓",
                    description="A detailed walkthrough of the 3 steps.",
                ),
                discord.SelectOption(
                    label="What is DIFF Meets?",
                    value="about",
                    emoji="🏁",
                    description="Learn about Different Meets and what we're about.",
                ),
                discord.SelectOption(
                    label="Why is my access locked?",
                    value="locked",
                    emoji="🔒",
                    description="Understand why you can't see the meet area yet.",
                ),
            ],
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("This only works inside the server.", ephemeral=True)
            return

        selected = self.values[0]

        if selected == "progress":
            cog: DiffWelcomeJoinSystem = interaction.client.cogs.get("DiffWelcomeJoinSystem")
            if cog is None:
                await interaction.response.send_message("System temporarily unavailable.", ephemeral=True)
                return
            state = cog.get_progress_state(interaction.user)
            embed = cog.build_progress_embed(interaction.user, state)
            await interaction.response.send_message(embed=embed, ephemeral=True)

        elif selected == "howto":
            embed = discord.Embed(
                title="❓ How Does Check-In Work?",
                description=(
                    "Completing your check-in gives you full access to the DIFF server. "
                    "There are **3 steps** — here's what each one means.\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━"
                ),
                color=discord.Color.blue(),
                timestamp=utcnow(),
            )
            embed.add_field(
                name="🔴 Step 1 — Read the Rules",
                value=(
                    f"Head to <#{RULES_CHANNEL_ID}> and read through the server rules.\n"
                    "Once you accept them, you'll receive the **Verified** role automatically."
                ),
                inline=False,
            )
            embed.add_field(
                name="🔵 Step 2 — Verify Your Identity",
                value=(
                    f"Go to <#{JOIN_MEETS_HUB_CHANNEL_ID}> and follow the instructions there.\n"
                    "This step confirms you're a real person and ready to join."
                ),
                inline=False,
            )
            embed.add_field(
                name="🟢 Step 3 — Get Cleared to Enter",
                value=(
                    "After steps 1 and 2, staff will verify your check-in and grant you full access.\n"
                    "This usually happens quickly — check back in a few minutes."
                ),
                inline=False,
            )
            embed.set_footer(text="Different Meets • Check-In Guide")
            await interaction.response.send_message(embed=embed, ephemeral=True)

        elif selected == "about":
            embed = discord.Embed(
                title="🏁 About Different Meets (DIFF)",
                description=(
                    "**Different Meets** is a structured, community-driven **PS5 GTA car meet crew** "
                    "built on realism, quality builds, and consistency.\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━"
                ),
                color=discord.Color.gold(),
                timestamp=utcnow(),
            )
            embed.add_field(
                name="🚗 Who We Are",
                value=(
                    "DIFF has been running since **August 2020**. We moved to PS5 in 2022 and "
                    "have grown into one of the most organised car meet communities on PlayStation."
                ),
                inline=False,
            )
            embed.add_field(
                name="📅 What We Do",
                value=(
                    "• Weekly crew meets with structured hosting\n"
                    "• Weekly crew color changes voted by the community\n"
                    "• Monthly crew-wide meetings\n"
                    "• Crew collaborations and community events"
                ),
                inline=False,
            )
            embed.add_field(
                name="✅ What We Expect",
                value=(
                    "• 18+ only\n"
                    "• Clean, realistic cars\n"
                    "• Active on Discord and in-game\n"
                    "• Professional and respectful conduct"
                ),
                inline=False,
            )
            embed.set_footer(text="Different Meets • About")
            await interaction.response.send_message(embed=embed, ephemeral=True)

        elif selected == "locked":
            embed = discord.Embed(
                title="🔒 Why Is My Access Locked?",
                description=(
                    "New members go through a quick verification process before getting full access. "
                    "This keeps DIFF a safe, quality community.\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "Your access will unlock **automatically** once you complete all 3 check-in steps:\n\n"
                    f"🔴 Read rules in <#{RULES_CHANNEL_ID}>\n"
                    f"🔵 Verify in <#{JOIN_MEETS_HUB_CHANNEL_ID}>\n"
                    "🟢 Wait for staff clearance\n\n"
                    "Select **Check My Progress** above to see which steps are done."
                ),
                color=discord.Color.red(),
                timestamp=utcnow(),
            )
            embed.set_footer(text="Different Meets • Access Info")
            await interaction.response.send_message(embed=embed, ephemeral=True)


class CheckInView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        # Row 0: help dropdown
        self.add_item(CheckInHelpSelect())

        # Row 1: quick-link buttons
        self.add_item(discord.ui.Button(
            label="Go to #rules",
            style=discord.ButtonStyle.link,
            url=f"https://discord.com/channels/{GUILD_ID}/{RULES_CHANNEL_ID}",
            emoji="📘",
            row=1,
        ))
        self.add_item(discord.ui.Button(
            label="Go to #joinmeets",
            style=discord.ButtonStyle.link,
            url=f"https://discord.com/channels/{GUILD_ID}/{JOIN_MEETS_HUB_CHANNEL_ID}",
            emoji="🏁",
            row=1,
        ))


class DiffWelcomeJoinSystem(commands.Cog):
    _DEDUP_TTL = 30  # seconds

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = CheckInDB(DB_FILE)
        self.reminder_loop.start()
        self._join_dedup:   dict[int, float] = {}
        self._verify_dedup: dict[int, float] = {}

    async def cog_load(self) -> None:
        self.bot.add_view(CheckInView())

    def cog_unload(self) -> None:
        self.reminder_loop.cancel()

    def verified_role(self, guild: discord.Guild) -> Optional[discord.Role]:
        return guild.get_role(VERIFIED_ROLE_ID)

    def unverified_role(self, guild: discord.Guild) -> Optional[discord.Role]:
        return guild.get_role(UNVERIFIED_ROLE_ID)

    def get_progress_state(self, member: discord.Member) -> ProgressState:
        row = self.db.get_row(member.id)
        posted = bool(row["posted_in_join_hub"]) if row else False
        has_verified = any(r.id == VERIFIED_ROLE_ID for r in member.roles)
        return ProgressState(has_verified, posted, has_verified)

    def build_progress_embed(self, member: discord.Member, state: ProgressState) -> discord.Embed:
        embed = discord.Embed(
            title="📊 Your DIFF Check-In Progress",
            description=f"**Progress:** `{state.progress_bar()}`",
            color=weekly_color(),
            timestamp=utcnow(),
        )
        embed.add_field(
            name="Step 1 — Read Rules",
            value="✅ Complete" if state.has_verified_role else "⏳ Pending",
            inline=False,
        )
        embed.add_field(
            name="Step 2 — Posted in Join Meets Hub",
            value="✅ Complete" if state.posted_in_join_hub else "⏳ Pending",
            inline=False,
        )
        embed.add_field(
            name="Step 3 — Cleared to Enter",
            value="✅ Complete" if state.cleared_to_enter else "⏳ Pending — awaiting staff verification",
            inline=False,
        )
        embed.set_footer(text=f"Member: {member}")
        return embed

    async def _send_checkin_panel(self, channel: discord.TextChannel, member: discord.Member):
        embed = discord.Embed(
            title="🏁 DIFF Check-In Required",
            description=(
                f"Welcome to **Different Meets**, {member.mention}! "
                "Before you can access the meet area, complete the 3 steps below.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=weekly_color(),
            timestamp=utcnow(),
        )
        embed.add_field(
            name="🔴 Step 1 — Read the Rules",
            value=f"Go to <#{RULES_CHANNEL_ID}> and read through the rules to receive the **Verified** role.",
            inline=False,
        )
        embed.add_field(
            name="🔵 Step 2 — Verify Your Identity",
            value=f"Head to <#{JOIN_MEETS_HUB_CHANNEL_ID}> and complete the verification process.",
            inline=False,
        )
        embed.add_field(
            name="🟢 Step 3 — Get Cleared",
            value="Once both steps are done, staff will clear you for full server access.",
            inline=False,
        )
        embed.add_field(
            name="🔒 Access Status",
            value="**Locked** — complete all steps to unlock the meet area, chats, and events.",
            inline=False,
        )
        embed.set_footer(text=FOOTER_TEXT)

        file = None
        if EMBLEM_FILE_PATH.exists():
            file = discord.File(EMBLEM_FILE_PATH, filename="diff_welcome_emblem.png")
            embed.set_image(url="attachment://diff_welcome_emblem.png")

        view = CheckInView()
        try:
            if file:
                await channel.send(content=member.mention, embed=embed, file=file, view=view,
                                   allowed_mentions=discord.AllowedMentions(users=True))
            else:
                await channel.send(content=member.mention, embed=embed, view=view,
                                   allowed_mentions=discord.AllowedMentions(users=True))
            if member != channel.guild.me:
                self.db.mark_join_hub_post(member.id)
        except Exception as e:
            print(f"[DiffWelcomeJoinSystem] Failed to send check-in panel: {e}")

    async def _log(
        self,
        guild: discord.Guild,
        text: str,
        color: Optional[discord.Color] = None,
        title: str = "📊 DIFF Verification Tracker",
        member: Optional[discord.Member] = None,
    ):
        ch = guild.get_channel(VERIFICATION_LOG_CHANNEL_ID)
        if not isinstance(ch, discord.TextChannel):
            return
        embed = discord.Embed(
            title=title,
            description=text,
            color=color or weekly_color(),
            timestamp=utcnow(),
        )
        if member:
            embed.set_author(
                name=f"{member.display_name} ({member})",
                icon_url=member.display_avatar.url,
            )
        embed.set_footer(text="DIFF Meets • Verification Tracker")
        try:
            await ch.send(embed=embed)
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_ready(self):
        print("[DiffWelcomeJoinSystem] Cog ready.")
        flag = Path("diff_data/send_welcome_preview.flag")
        if flag.exists():
            flag.unlink()
            guild = self.bot.get_guild(GUILD_ID)
            if guild and guild.me:
                ch = guild.get_channel(WELCOME_POST_CHANNEL_ID)
                if isinstance(ch, discord.TextChannel):
                    await self._send_checkin_panel(ch, guild.me)
                    print("[DiffWelcomeJoinSystem] Preview sent.")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id != GUILD_ID:
            return

        # Guard against duplicate events caused by Discord replaying gateway
        # events after the bot reconnects following a Pi freeze.
        now_ts = time.monotonic()
        if now_ts - self._join_dedup.get(member.id, 0) < self._DEDUP_TTL:
            print(f"[DiffWelcomeJoinSystem] Skipping duplicate join event for {member} (dedup).")
            return
        self._join_dedup[member.id] = now_ts

        self.db.upsert_join(member.id)

        unverified = self.unverified_role(member.guild)
        verified = self.verified_role(member.guild)
        if unverified and (not verified or verified not in member.roles):
            if unverified not in member.roles:
                try:
                    await member.add_roles(unverified, reason="DIFF auto check-in — pending verification")
                except discord.Forbidden:
                    pass

        ch = member.guild.get_channel(WELCOME_POST_CHANNEL_ID)
        if ch is None:
            try:
                ch = await self.bot.fetch_channel(WELCOME_POST_CHANNEL_ID)
            except Exception as e:
                print(f"[DiffWelcomeJoinSystem] Could not fetch welcome channel: {e}")
                ch = None
        if isinstance(ch, discord.TextChannel):
            await self._send_checkin_panel(ch, member)
        else:
            print(f"[DiffWelcomeJoinSystem] Welcome channel {WELCOME_POST_CHANNEL_ID} not found for {member}")

        await self._log(
            member.guild,
            f"{member.mention} entered the DIFF check-in flow.\n"
            f"Account created: {discord.utils.format_dt(member.created_at, style='D')} "
            f"({discord.utils.format_dt(member.created_at, style='R')})",
            discord.Color.orange(),
            title="🚪 Entered Check-in Flow",
            member=member,
        )

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if after.guild.id != GUILD_ID:
            return

        before_verified = any(r.id == VERIFIED_ROLE_ID for r in before.roles)
        after_verified  = any(r.id == VERIFIED_ROLE_ID for r in after.roles)

        if not before_verified and after_verified:
            now_ts = time.monotonic()
            if now_ts - self._verify_dedup.get(after.id, 0) < self._DEDUP_TTL:
                print(f"[DiffWelcomeJoinSystem] Skipping duplicate verified event for {after} (dedup).")
                return
            self._verify_dedup[after.id] = now_ts
            self.db.mark_verified(after.id)
            unverified = self.unverified_role(after.guild)
            if unverified and unverified in after.roles:
                try:
                    await after.remove_roles(unverified, reason="DIFF verified — access unlocked")
                except discord.Forbidden:
                    pass

            await self._log(
                after.guild,
                f"{after.mention} has been **verified** and cleared to enter the server.",
                discord.Color.green(),
                title="✅ Member Verified",
                member=after,
            )

            if SEND_VERIFIED_DM:
                try:
                    embed = discord.Embed(
                        title="✅ You're Cleared to Enter",
                        description=(
                            f"You have been verified in **Different Meets** and now have full access to the community.\n\n"
                            f"Welcome to the meet — see you on the track! 🚗"
                        ),
                        color=discord.Color.green(),
                        timestamp=utcnow(),
                    )
                    embed.add_field(
                        name="📅 Find the Meets",
                        value=(
                            f"• <#{MEET_ANNOUNCEMENT_CHANNEL_ID}> — official meet announcements\n"
                            f"• <#{UPCOMING_MEET_CHANNEL_ID}> — upcoming scheduled meets\n"
                            f"• <#{MEET_INFO_CHANNEL_ID}> — meet rules & info\n"
                            f"• <#{DIFF_HOSTS_CHANNEL_ID}> — host schedule"
                        ),
                        inline=False,
                    )
                    embed.add_field(
                        name="🎮 Next Step",
                        value=f"Head to <#{JOIN_MEETS_HUB_CHANNEL_ID}> to complete your PS5 setup and get your platform role.",
                        inline=False,
                    )
                    embed.set_footer(text="DIFF Meets • PlayStation GTA Car Meets")
                    await after.send(embed=embed)
                except discord.Forbidden:
                    pass

        elif before_verified and not after_verified:
            self.db.clear_verified(after.id)
            await self._log(
                after.guild,
                f"{after.mention} had the **Verified** role removed.",
                discord.Color.red(),
                title="⚠️ Verification Removed",
                member=after,
            )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        if message.guild.id != GUILD_ID:
            return
        if message.channel.id == JOIN_MEETS_HUB_CHANNEL_ID:
            self.db.mark_join_hub_post(message.author.id)
            author = message.author if isinstance(message.author, discord.Member) else None
            await self._log(
                message.guild,
                f"{message.author.mention} posted in <#{JOIN_MEETS_HUB_CHANNEL_ID}> — check-in step completed.",
                discord.Color.blue(),
                title="📝 Posted in Join Hub",
                member=author,
            )

    @tasks.loop(minutes=REMINDER_CHECK_EVERY_MINUTES)
    async def reminder_loop(self):
        await self.bot.wait_until_ready()
        guild = self.bot.get_guild(GUILD_ID)
        if guild is None:
            return
        verified_role = self.verified_role(guild)
        for row in self.db.reminder_candidates():
            member = guild.get_member(int(row["user_id"]))
            if member is None:
                continue
            if verified_role and verified_role in member.roles:
                self.db.mark_verified(member.id)
                continue
            try:
                embed = discord.Embed(
                    title="🔔 DIFF Check-In Reminder",
                    description=(
                        f"Hey {member.display_name}, you still haven't finished your DIFF check-in.\n\n"
                        "Complete the steps below to get full access to the server:\n\n"
                        f"🔴 **Step 1 —** Read the rules in <#{RULES_CHANNEL_ID}> to receive the **Verified** role\n"
                        f"🔵 **Step 2 —** Verify your identity in <#{JOIN_MEETS_HUB_CHANNEL_ID}>\n"
                        "🟢 **Step 3 —** Once verified, you'll be cleared to enter the meet area\n\n"
                        "━━━━━━━━━━━━━━━━━━━━━━\n"
                        "Use the **Check My Progress** button in the welcome channel to track your status."
                    ),
                    color=discord.Color.orange(),
                    timestamp=utcnow(),
                )
                embed.set_footer(text="Different Meets • Verification System")
                await member.send(embed=embed)
                self.db.mark_reminder_sent(member.id)
                await self._log(
                    guild,
                    f"{member.mention} was sent a check-in reminder DM.",
                    discord.Color.gold(),
                    title="📨 Reminder DM Sent",
                    member=member,
                )
            except discord.Forbidden:
                self.db.mark_reminder_sent(member.id)

    @commands.command(name="previewwelcome")
    @commands.has_permissions(manage_guild=True)
    async def previewwelcome(self, ctx: commands.Context):
        ch = ctx.guild.get_channel(WELCOME_POST_CHANNEL_ID)
        if not isinstance(ch, discord.TextChannel):
            await ctx.send("Welcome post channel not found.", ephemeral=True)
            return
        await self._send_checkin_panel(ch, ctx.author)
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="checkinprogress")
    @commands.has_permissions(manage_guild=True)
    async def checkinprogress(self, ctx: commands.Context, member: discord.Member):
        state = self.get_progress_state(member)
        embed = self.build_progress_embed(member, state)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(DiffWelcomeJoinSystem(bot))
