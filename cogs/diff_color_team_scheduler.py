import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

import discord
from discord.ext import commands

# =========================================================
# CONFIG
# =========================================================

COLOR_CHANNEL_ID = 1485453653916520549
COLOR_ROLE_ID    = 1115495008670330902

MANAGER_ROLE_IDS: Set[int] = {
    990011447193006101,  # Manager
}

TIME_SLOTS = [
    "Tonight - 8:00 PM EST",
    "Tomorrow - 7:00 PM EST",
    "Tomorrow - 9:00 PM EST",
    "This Weekend - 8:00 PM EST",
]

REMINDER_DELAY_MINUTES = 60
VOTING_CLOSE_MINUTES   = 180
PANEL_TITLE            = "DIFF Color Team Update"
PANEL_FOOTER           = "DIFF Color Team"
EMBED_COLOR            = 0xF59E0B


# =========================================================
# SESSION STATE
# =========================================================

@dataclass
class SessionState:
    panel_message_id: Optional[int]       = None
    available:        Set[int]             = field(default_factory=set)
    not_available:    Set[int]             = field(default_factory=set)
    time_votes:       Dict[int, str]       = field(default_factory=dict)
    reminder_task:    Optional[asyncio.Task] = None
    finalize_task:    Optional[asyncio.Task] = None
    is_closed:        bool                 = False
    chosen_time:      Optional[str]        = None


# =========================================================
# VIEWS
# =========================================================

class TimeVoteSelect(discord.ui.Select):
    def __init__(self, cog: "ColorTeamSchedulerCog"):
        self.cog = cog
        options = [
            discord.SelectOption(label=slot, description=f"Vote for {slot}")
            for slot in TIME_SLOTS[:25]
        ]
        super().__init__(
            placeholder="Pick your best session time...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="diff_color_team_time_vote_select",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        state = self.cog.state
        if state.is_closed:
            await interaction.response.send_message(
                "This availability check has already been closed.", ephemeral=True
            )
            return

        if COLOR_ROLE_ID:
            if not isinstance(interaction.user, discord.Member):
                await interaction.response.send_message("This can only be used in a server.", ephemeral=True)
                return
            role_ids = {r.id for r in interaction.user.roles}
            if COLOR_ROLE_ID not in role_ids and not _user_is_manager(interaction.user):
                await interaction.response.send_message("Only Color Team members can vote.", ephemeral=True)
                return

        uid      = interaction.user.id
        selected = self.values[0]
        state.time_votes[uid] = selected
        state.available.add(uid)
        state.not_available.discard(uid)

        await self.cog.refresh_panel(interaction.client)
        await interaction.response.send_message(
            f"Your time vote has been saved: **{selected}**", ephemeral=True
        )


class AvailabilityView(discord.ui.View):
    def __init__(self, cog: "ColorTeamSchedulerCog"):
        super().__init__(timeout=None)
        self.cog = cog
        self.add_item(TimeVoteSelect(cog))

    @discord.ui.button(
        label="Available",
        style=discord.ButtonStyle.success,
        emoji="✅",
        custom_id="diff_color_team_available_btn",
    )
    async def available_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        state = self.cog.state
        if state.is_closed:
            await interaction.response.send_message(
                "This availability check has already been closed.", ephemeral=True
            )
            return
        if COLOR_ROLE_ID and isinstance(interaction.user, discord.Member):
            role_ids = {r.id for r in interaction.user.roles}
            if COLOR_ROLE_ID not in role_ids and not _user_is_manager(interaction.user):
                await interaction.response.send_message("Only Color Team members can respond.", ephemeral=True)
                return

        uid = interaction.user.id
        state.available.add(uid)
        state.not_available.discard(uid)

        await self.cog.refresh_panel(interaction.client)
        await interaction.response.send_message("You are marked as **Available** ✅.", ephemeral=True)

    @discord.ui.button(
        label="Not Available",
        style=discord.ButtonStyle.danger,
        emoji="❌",
        custom_id="diff_color_team_not_available_btn",
    )
    async def not_available_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        state = self.cog.state
        if state.is_closed:
            await interaction.response.send_message(
                "This availability check has already been closed.", ephemeral=True
            )
            return
        if COLOR_ROLE_ID and isinstance(interaction.user, discord.Member):
            role_ids = {r.id for r in interaction.user.roles}
            if COLOR_ROLE_ID not in role_ids and not _user_is_manager(interaction.user):
                await interaction.response.send_message("Only Color Team members can respond.", ephemeral=True)
                return

        uid = interaction.user.id
        state.not_available.add(uid)
        state.available.discard(uid)
        state.time_votes.pop(uid, None)

        await self.cog.refresh_panel(interaction.client)
        await interaction.response.send_message("You are marked as **Not Available** ❌.", ephemeral=True)

    @discord.ui.button(
        label="Close & Pick Best Time",
        style=discord.ButtonStyle.primary,
        emoji="📊",
        custom_id="diff_color_team_close_btn",
    )
    async def close_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if not isinstance(interaction.user, discord.Member) or not _user_is_manager(interaction.user):
            await interaction.response.send_message("Only managers can close this check-in.", ephemeral=True)
            return
        await self.cog.finalize_best_time(interaction.client, manual=True)
        await interaction.response.send_message(
            "✅ Availability check closed and best time selected.", ephemeral=True
        )


# =========================================================
# HELPERS
# =========================================================

def _user_is_manager(member: discord.Member) -> bool:
    if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
        return True
    return any(role.id in MANAGER_ROLE_IDS for role in member.roles)


# =========================================================
# COG
# =========================================================

class ColorTeamSchedulerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot   = bot
        self.state = SessionState()
        self.bot.add_view(AvailabilityView(self))

    @commands.Cog.listener()
    async def on_ready(self):
        if getattr(self.bot, "_diff_color_team_scheduler_ready", False):
            return
        self.bot._diff_color_team_scheduler_ready = True
        print("[ColorTeamScheduler] Cog ready.")

    # ----------------------------------------------------------
    # EMBED BUILDER
    # ----------------------------------------------------------

    def build_embed(self, guild: discord.Guild) -> discord.Embed:
        state = self.state
        role  = guild.get_role(COLOR_ROLE_ID)

        available_mentions = [
            guild.get_member(uid).mention
            for uid in state.available
            if guild.get_member(uid)
        ]
        not_available_mentions = [
            guild.get_member(uid).mention
            for uid in state.not_available
            if guild.get_member(uid)
        ]

        vote_counts: Dict[str, int] = {slot: 0 for slot in TIME_SLOTS}
        for uid, slot in state.time_votes.items():
            if uid in state.available and slot in vote_counts:
                vote_counts[slot] += 1

        best_time      = self.calculate_best_time()
        best_time_text = best_time if best_time else "No winning time yet"

        waiting_on: List[str] = []
        if role:
            for member in role.members:
                if member.bot:
                    continue
                if member.id not in state.available and member.id not in state.not_available:
                    waiting_on.append(member.mention)

        description = (
            "We've made updates to the system, layout, and workflow.\n\n"
            "Please mark your availability and vote for the best walkthrough time below."
        )
        if state.is_closed and state.chosen_time:
            description += f"\n\n**Chosen session time:** {state.chosen_time}"

        embed = discord.Embed(
            title=f"🎨 {PANEL_TITLE}",
            description=description,
            color=EMBED_COLOR,
        )
        embed.add_field(
            name="✅ Available",
            value="\n".join(available_mentions) if available_mentions else "No responses yet",
            inline=False,
        )
        embed.add_field(
            name="❌ Not Available",
            value="\n".join(not_available_mentions) if not_available_mentions else "No responses yet",
            inline=False,
        )
        vote_lines = [f"**{slot}** — {vote_counts[slot]} vote(s)" for slot in TIME_SLOTS]
        embed.add_field(name="📊 Time Voting", value="\n".join(vote_lines), inline=False)
        embed.add_field(name="🧠 Current Best Time", value=best_time_text, inline=False)
        embed.add_field(
            name="⏳ Waiting On",
            value="\n".join(waiting_on[:20]) if waiting_on else "Everyone has responded",
            inline=False,
        )
        embed.set_footer(text=PANEL_FOOTER)
        return embed

    def calculate_best_time(self) -> Optional[str]:
        state       = self.state
        vote_counts: Dict[str, int] = {slot: 0 for slot in TIME_SLOTS}
        for uid, slot in state.time_votes.items():
            if uid in state.available and slot in vote_counts:
                vote_counts[slot] += 1
        highest = max(vote_counts.values(), default=0)
        if highest <= 0:
            return None
        for slot in TIME_SLOTS:
            if vote_counts[slot] == highest:
                return slot
        return None

    # ----------------------------------------------------------
    # PANEL REFRESH
    # ----------------------------------------------------------

    async def refresh_panel(self, client: discord.Client) -> None:
        channel = client.get_channel(COLOR_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            try:
                channel = await client.fetch_channel(COLOR_CHANNEL_ID)
            except Exception:
                return
        if not isinstance(channel, discord.TextChannel):
            return
        if not self.state.panel_message_id:
            return
        try:
            msg = await channel.fetch_message(self.state.panel_message_id)
        except discord.NotFound:
            return
        except Exception:
            return
        embed = self.build_embed(channel.guild)
        view  = None if self.state.is_closed else AvailabilityView(self)
        await msg.edit(embed=embed, view=view)

    # ----------------------------------------------------------
    # DM REMINDERS
    # ----------------------------------------------------------

    async def send_dm_reminders(self) -> None:
        await asyncio.sleep(REMINDER_DELAY_MINUTES * 60)
        channel = self.bot.get_channel(COLOR_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            return
        guild = channel.guild
        role  = guild.get_role(COLOR_ROLE_ID)
        if role is None:
            return
        for member in role.members:
            if member.bot:
                continue
            if member.id in self.state.available or member.id in self.state.not_available:
                continue
            try:
                await member.send(
                    f"Hey {member.display_name}, DIFF Color Team is checking availability for a walkthrough session. "
                    f"Please respond in **#{channel.name}** when you can."
                )
            except discord.Forbidden:
                pass

    # ----------------------------------------------------------
    # AUTO FINALIZE
    # ----------------------------------------------------------

    async def finalize_after_timer(self) -> None:
        await asyncio.sleep(VOTING_CLOSE_MINUTES * 60)
        await self.finalize_best_time(self.bot, manual=False)

    async def finalize_best_time(self, client: discord.Client, manual: bool = False) -> None:
        if self.state.is_closed:
            return

        self.state.is_closed   = True
        self.state.chosen_time = self.calculate_best_time()

        channel = client.get_channel(COLOR_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            return

        await self.refresh_panel(client)

        if self.state.chosen_time:
            text = (
                f"📅 **Best session time selected: {self.state.chosen_time}**\n"
                f"Thanks to everyone who responded."
            )
        else:
            text = (
                "📅 The availability check has been closed. "
                "Not enough time votes to auto-pick a session time."
            )
        if manual:
            text = "✅ " + text

        await channel.send(text)

    # ----------------------------------------------------------
    # POST / REFRESH PANEL
    # ----------------------------------------------------------

    async def post_or_refresh_panel(self, ctx: commands.Context) -> None:
        channel = self.bot.get_channel(COLOR_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            try:
                channel = await self.bot.fetch_channel(COLOR_CHANNEL_ID)
            except Exception as e:
                raise RuntimeError(f"Color Team channel not found: {e}")
        if not isinstance(channel, discord.TextChannel):
            raise RuntimeError("Color Team channel is not a text channel.")

        if self.state.reminder_task and not self.state.reminder_task.done():
            self.state.reminder_task.cancel()
        if self.state.finalize_task and not self.state.finalize_task.done():
            self.state.finalize_task.cancel()

        self.state = SessionState()

        async for msg in channel.history(limit=25):
            if msg.author.id == self.bot.user.id and msg.embeds:
                if PANEL_TITLE in (msg.embeds[0].title or ""):
                    try:
                        await msg.delete()
                    except discord.HTTPException:
                        pass
                    break

        embed = self.build_embed(channel.guild)
        view  = AvailabilityView(self)

        panel_message = await channel.send(
            content=f"<@&{COLOR_ROLE_ID}>",
            embed=embed,
            view=view,
            allowed_mentions=discord.AllowedMentions(roles=True, users=False, everyone=False),
        )
        self.state.panel_message_id = panel_message.id

        self.state.reminder_task = self.bot.loop.create_task(self.send_dm_reminders())
        self.state.finalize_task = self.bot.loop.create_task(self.finalize_after_timer())

    # ----------------------------------------------------------
    # COMMANDS
    # ----------------------------------------------------------

    @commands.command(name="colorcheck")
    @commands.guild_only()
    async def colorcheck(self, ctx: commands.Context) -> None:
        if not isinstance(ctx.author, discord.Member) or not _user_is_manager(ctx.author):
            await ctx.reply("Only managers can post this panel.", mention_author=False, delete_after=8)
            return
        try:
            await self.post_or_refresh_panel(ctx)
        except Exception as e:
            await ctx.reply(f"Could not post the panel: {e}", mention_author=False)
            return
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="colorcheckclose")
    @commands.guild_only()
    async def colorcheckclose(self, ctx: commands.Context) -> None:
        if not isinstance(ctx.author, discord.Member) or not _user_is_manager(ctx.author):
            await ctx.reply("Only managers can close this panel.", mention_author=False, delete_after=8)
            return
        await self.finalize_best_time(self.bot, manual=True)
        await ctx.send("✅ Availability check closed.", delete_after=8)
        try:
            await ctx.message.delete()
        except Exception:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(ColorTeamSchedulerCog(bot))
