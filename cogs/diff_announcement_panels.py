from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Optional

import discord
from discord.ext import commands

# =========================================================
# CONFIG — Crew Announcement
# =========================================================
CREW_ANNOUNCE_CHANNEL_ID = 990097152044855326
CREW_ROLE_ID             = 886702076552441927

# =========================================================
# CONFIG — General Announcement
# =========================================================
GENERAL_ANNOUNCE_CHANNEL_ID = 1047166622235893911
VIEW_UPDATES_CHANNEL_ID     = GENERAL_ANNOUNCE_CHANNEL_ID
GUILD_ID                    = 850386896509337710

# =========================================================
# CONFIG — Shared
# =========================================================
LOG_CHANNEL_ID = 1485265848099799163
REMINDER_DELAY_MINUTES = 15

STAFF_ROLE_IDS: set[int] = {
    850391095845584937,
    850391378559238235,
    990011447193006101,
}

CREW_PANEL_TAG    = "DIFF_CREW_ANNOUNCE_PANEL_V1"
GENERAL_PANEL_TAG = "DIFF_GENERAL_ANNOUNCE_PANEL_V1"

DATA_DIR              = "diff_data"
CREW_PANEL_FILE       = os.path.join(DATA_DIR, "crew_announce_panel.json")
GENERAL_PANEL_FILE    = os.path.join(DATA_DIR, "general_announce_panel.json")
TRACKING_FILE         = os.path.join(DATA_DIR, "announcement_tracking.json")

DIFF_LOGO_URL = (
    "https://media.discordapp.net/attachments/1107375326625005719/"
    "1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm="
    "2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
    "&=&format=webp&quality=lossless&width=1376&height=917"
)


# =========================================================
# HELPERS — General
# =========================================================
def _load_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def _get_saved_msg_id(path: str) -> Optional[int]:
    v = _load_json(path).get("panel_message_id")
    return int(v) if v else None


def _save_msg_id(path: str, msg_id: int) -> None:
    data = _load_json(path)
    data["panel_message_id"] = msg_id
    _save_json(path, data)


def _is_staff(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    return any(r.id in STAFF_ROLE_IDS for r in member.roles)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# =========================================================
# HELPERS — Tracking
# =========================================================
def _load_tracking() -> dict:
    data = _load_json(TRACKING_FILE)
    if "announcements" not in data:
        data["announcements"] = {}
    return data


def _get_record(message_id: int) -> Optional[dict]:
    return _load_tracking()["announcements"].get(str(message_id))


def _upsert_record(message_id: int, record: dict) -> None:
    data = _load_tracking()
    data["announcements"][str(message_id)] = record
    _save_json(TRACKING_FILE, data)


def _build_stats_embed(guild: discord.Guild, message_id: int, record: dict) -> discord.Embed:
    acknowledged = len(record.get("acknowledged", {}))
    interested   = len(record.get("interested", {}))
    reminders    = len(record.get("remind_me", {}))
    total        = sum(1 for m in guild.members if not m.bot)
    pending      = max(total - acknowledged, 0)

    embed = discord.Embed(
        title="📊 DIFF Announcement Tracking",
        color=discord.Color.blurple(),
        timestamp=datetime.now(timezone.utc),
        description=f"Stats for: **{record.get('title', 'Untitled')}**",
    )
    embed.add_field(name="✅ Acknowledged", value=str(acknowledged), inline=True)
    embed.add_field(name="🔥 Interested",   value=str(interested),   inline=True)
    embed.add_field(name="⏰ Remind Me",    value=str(reminders),    inline=True)
    embed.add_field(name="⏳ Pending",      value=str(pending),      inline=True)
    embed.set_footer(text="DIFF Announcement System")
    return embed


async def _schedule_dm_reminder(
    user: discord.User | discord.Member,
    guild: discord.Guild,
    title: str,
    jump_url: str,
    log_channel_id: int,
) -> None:
    await asyncio.sleep(REMINDER_DELAY_MINUTES * 60)
    ch = guild.get_channel(log_channel_id)
    try:
        embed = discord.Embed(
            title="⏰ DIFF Reminder",
            description=(
                f"You asked to be reminded about **{title}**.\n\n"
                f"Check the latest update here:\n{jump_url}"
            ),
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_footer(text="DIFF Announcement System")
        await user.send(embed=embed)
        if isinstance(ch, discord.TextChannel):
            await ch.send(f"⏰ Sent reminder DM to {user.mention} for **{title}**.")
    except discord.Forbidden:
        if isinstance(ch, discord.TextChannel):
            await ch.send(f"⚠️ Could not DM {user.mention} (DMs closed) for **{title}**.")
    except discord.HTTPException:
        pass


async def _ensure_panel(
    bot: commands.Bot,
    channel_id: int,
    panel_file: str,
    panel_tag: str,
    panel_embed: discord.Embed,
    panel_view: discord.ui.View,
    label: str,
) -> None:
    channel = bot.get_channel(channel_id)
    if not isinstance(channel, discord.TextChannel):
        try:
            channel = await bot.fetch_channel(channel_id)
        except Exception:
            channel = None
    if not isinstance(channel, discord.TextChannel):
        print(f"[AnnouncePanels] {label} channel {channel_id} not found.")
        return

    saved_id = _get_saved_msg_id(panel_file)
    if saved_id:
        try:
            msg = await channel.fetch_message(saved_id)
            await msg.edit(embed=panel_embed, view=panel_view)
            print(f"[AnnouncePanels] {label} panel refreshed.")
            return
        except discord.NotFound:
            pass
        except Exception as e:
            print(f"[AnnouncePanels] {label} edit failed: {e}")

    try:
        async for msg in channel.history(limit=50):
            if (
                msg.author == bot.user
                and msg.embeds
                and panel_tag in (msg.embeds[0].footer.text or "")
            ):
                try:
                    await msg.delete()
                except Exception:
                    pass
    except Exception:
        pass

    try:
        new_msg = await channel.send(embed=panel_embed, view=panel_view)
        _save_msg_id(panel_file, new_msg.id)
        print(f"[AnnouncePanels] {label} panel posted: {new_msg.id}")
    except Exception as e:
        print(f"[AnnouncePanels] {label} post failed: {e}")


# =========================================================
# ANNOUNCEMENT TRACKING BUTTONS (attached to posted announcements)
# =========================================================
class AnnouncementButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Acknowledge",
        style=discord.ButtonStyle.success,
        emoji="✅",
        custom_id="diff_announce_acknowledge_v1",
    )
    async def acknowledge(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not interaction.message:
            return
        record = _get_record(interaction.message.id)
        if not record:
            return await interaction.response.send_message(
                "This announcement is not tracked.", ephemeral=True
            )
        uid = str(interaction.user.id)
        if uid not in record["acknowledged"]:
            record["acknowledged"][uid] = _utc_now()
            _upsert_record(interaction.message.id, record)
            log_ch = interaction.guild.get_channel(LOG_CHANNEL_ID)
            if isinstance(log_ch, discord.TextChannel):
                try:
                    await log_ch.send(
                        f"✅ {interaction.user.mention} acknowledged **{record['title']}**."
                    )
                except Exception:
                    pass
        await interaction.response.send_message(
            "✅ You have acknowledged this announcement.", ephemeral=True
        )

    @discord.ui.button(
        label="Remind Me",
        style=discord.ButtonStyle.secondary,
        emoji="⏰",
        custom_id="diff_announce_remind_v1",
    )
    async def remind_me(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not interaction.message:
            return
        record = _get_record(interaction.message.id)
        if not record:
            return await interaction.response.send_message(
                "This announcement is not tracked.", ephemeral=True
            )
        uid = str(interaction.user.id)
        record["remind_me"][uid] = _utc_now()
        _upsert_record(interaction.message.id, record)

        asyncio.create_task(
            _schedule_dm_reminder(
                interaction.user,
                interaction.guild,
                record["title"],
                interaction.message.jump_url,
                LOG_CHANNEL_ID,
            )
        )

        log_ch = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if isinstance(log_ch, discord.TextChannel):
            try:
                await log_ch.send(
                    f"⏰ {interaction.user.mention} set a reminder for **{record['title']}**."
                )
            except Exception:
                pass

        await interaction.response.send_message(
            f"⏰ Got it — I'll DM you a reminder in **{REMINDER_DELAY_MINUTES} minutes**.",
            ephemeral=True,
        )

    @discord.ui.button(
        label="Interested",
        style=discord.ButtonStyle.primary,
        emoji="🔥",
        custom_id="diff_announce_interested_v1",
    )
    async def interested(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not interaction.message:
            return
        record = _get_record(interaction.message.id)
        if not record:
            return await interaction.response.send_message(
                "This announcement is not tracked.", ephemeral=True
            )
        uid = str(interaction.user.id)
        if uid not in record["interested"]:
            record["interested"][uid] = _utc_now()
            _upsert_record(interaction.message.id, record)
            log_ch = interaction.guild.get_channel(LOG_CHANNEL_ID)
            if isinstance(log_ch, discord.TextChannel):
                try:
                    await log_ch.send(
                        f"🔥 {interaction.user.mention} marked Interested on **{record['title']}**."
                    )
                except Exception:
                    pass
        await interaction.response.send_message("🔥 Marked as interested.", ephemeral=True)

    @discord.ui.button(
        label="View Updates",
        style=discord.ButtonStyle.link,
        url=f"https://discord.com/channels/{GUILD_ID}/{VIEW_UPDATES_CHANNEL_ID}",
        emoji="📍",
    )
    async def view_updates(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass


# =========================================================
# CREW ANNOUNCEMENT MODAL + VIEW
# =========================================================
class CrewAnnouncementModal(discord.ui.Modal, title="Create Crew Announcement"):
    title_input = discord.ui.TextInput(
        label="Announcement Title",
        placeholder="Example: Saturday Meet Update",
        max_length=100, required=True,
    )
    message_input = discord.ui.TextInput(
        label="Announcement Message",
        placeholder="Type the full crew announcement here...",
        style=discord.TextStyle.paragraph, max_length=2000, required=True,
    )
    footer_input = discord.ui.TextInput(
        label="Sign-Off (optional)",
        placeholder="e.g. DIFF Management Team  or  DIFF Leadership",
        max_length=100, required=False,
    )

    def __init__(self, cog: "AnnouncementPanelsCog"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction) -> None:
        member = interaction.user
        if not isinstance(member, discord.Member) or not _is_staff(member):
            return await interaction.response.send_message(
                "Only staff can post crew announcements.", ephemeral=True
            )

        channel = interaction.client.get_channel(CREW_ANNOUNCE_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message(
                "Crew announcement channel not found.", ephemeral=True
            )

        sign_off = str(self.footer_input).strip() or "DIFF Management Team"

        # Build author label: display name + highest staff role
        role_label = ""
        for role in reversed(member.roles):
            if role.id in STAFF_ROLE_IDS:
                role_label = f" ({role.name})"
                break

        embed = discord.Embed(
            title=str(self.title_input),
            description=str(self.message_input),
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_author(
            name=f"Posted by {member.display_name}{role_label}",
            icon_url=member.display_avatar.url if member.display_avatar else None,
        )
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.set_footer(text=sign_off)

        crew_role = interaction.guild.get_role(CREW_ROLE_ID) if interaction.guild else None
        ping = crew_role.mention if crew_role else ""

        await channel.send(
            content=ping,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True),
        )
        await interaction.response.send_message(
            "Crew announcement posted successfully.", ephemeral=True
        )
        await self.cog.log_action(
            interaction.guild,
            f"📢 Crew announcement `{str(self.title_input)}` posted by {member.mention}"
        )


class CrewAnnouncePanelView(discord.ui.View):
    def __init__(self, cog: "AnnouncementPanelsCog"):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Make Crew Announcement", emoji="📣",
                       style=discord.ButtonStyle.danger,
                       custom_id="diff_crew_announce_create_v1")
    async def make_crew_announcement(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user
        if not isinstance(member, discord.Member) or not _is_staff(member):
            return await interaction.response.send_message(
                "Only staff can use this button.", ephemeral=True
            )
        await interaction.response.send_modal(CrewAnnouncementModal(self.cog))

    @discord.ui.button(label="Refresh Panel", emoji="♻️",
                       style=discord.ButtonStyle.secondary,
                       custom_id="diff_crew_announce_refresh_v1")
    async def refresh_crew_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user
        if not isinstance(member, discord.Member) or not _is_staff(member):
            return await interaction.response.send_message(
                "Only staff can refresh this panel.", ephemeral=True
            )
        await interaction.response.defer(ephemeral=True)
        await self.cog.ensure_crew_panel()
        await interaction.followup.send("Crew announcement panel refreshed.", ephemeral=True)


# =========================================================
# GENERAL ANNOUNCEMENT MODAL + SMART-PING VIEW
# =========================================================
class GeneralAnnouncementModal(discord.ui.Modal, title="Create General Announcement"):
    title_input = discord.ui.TextInput(
        label="Announcement Title",
        placeholder="Example: Server Update",
        max_length=100, required=True,
    )
    message_input = discord.ui.TextInput(
        label="Announcement Message",
        placeholder="Type the full announcement here...",
        style=discord.TextStyle.paragraph, max_length=2000, required=True,
    )
    footer_input = discord.ui.TextInput(
        label="Footer Text (optional)",
        placeholder="Example: DIFF Staff Team",
        max_length=100, required=False,
    )

    def __init__(self, cog: "AnnouncementPanelsCog", ping_mode: str):
        super().__init__()
        self.cog       = cog
        self.ping_mode = ping_mode

    async def on_submit(self, interaction: discord.Interaction) -> None:
        member = interaction.user
        if not isinstance(member, discord.Member) or not _is_staff(member):
            return await interaction.response.send_message(
                "Only staff can post general announcements.", ephemeral=True
            )

        channel = interaction.client.get_channel(GENERAL_ANNOUNCE_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message(
                "General announcement channel not found.", ephemeral=True
            )

        footer = str(self.footer_input).strip() or "DIFF General Announcement System"
        title  = str(self.title_input)

        embed = discord.Embed(
            title=title,
            description=str(self.message_input),
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_author(
            name=f"Posted by {member.display_name}",
            icon_url=member.display_avatar.url if member.display_avatar else None,
        )
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.add_field(
            name="Quick Actions",
            value="Use the buttons below to acknowledge, get a reminder, or mark interest.",
            inline=False,
        )
        embed.set_footer(text=footer)

        if self.ping_mode == "everyone":
            content          = "@everyone"
            allowed_mentions = discord.AllowedMentions(everyone=True)
        elif self.ping_mode == "here":
            content          = "@here"
            allowed_mentions = discord.AllowedMentions(everyone=True)
        elif self.ping_mode == "crew":
            crew_role        = interaction.guild.get_role(CREW_ROLE_ID) if interaction.guild else None
            content          = crew_role.mention if crew_role else None
            allowed_mentions = discord.AllowedMentions(roles=True)
        else:
            content          = None
            allowed_mentions = discord.AllowedMentions.none()

        tracking_view = AnnouncementButtons()
        msg = await channel.send(
            content=content,
            embed=embed,
            view=tracking_view,
            allowed_mentions=allowed_mentions,
        )

        record = {
            "title":       title,
            "channel_id":  channel.id,
            "message_id":  msg.id,
            "message_url": msg.jump_url,
            "created_by":  interaction.user.id,
            "created_at":  _utc_now(),
            "acknowledged": {},
            "remind_me":    {},
            "interested":   {},
        }
        _upsert_record(msg.id, record)

        stats_embed = _build_stats_embed(interaction.guild, msg.id, record)
        log_ch = interaction.guild.get_channel(LOG_CHANNEL_ID) if interaction.guild else None
        if isinstance(log_ch, discord.TextChannel):
            try:
                await log_ch.send(
                    content=f"📢 General announcement **{title}** posted by {member.mention} (ping: {self.ping_mode})\n{msg.jump_url}",
                    embed=stats_embed,
                )
            except Exception:
                pass

        await interaction.response.send_message(
            f"✅ Announcement posted in {channel.mention} with **{self.ping_mode}** ping.",
            ephemeral=True,
        )


class _PingSelect(discord.ui.Select):
    def __init__(self, cog: "AnnouncementPanelsCog"):
        super().__init__(
            placeholder="Choose ping type then post announcement…",
            min_values=1,
            max_values=1,
            custom_id="diff_general_announce_ping_select_v1",
            options=[
                discord.SelectOption(label="Ping @everyone",  value="everyone", emoji="📣",
                                     description="Notify all server members"),
                discord.SelectOption(label="Ping @here",      value="here",     emoji="📍",
                                     description="Notify online members only"),
                discord.SelectOption(label="Ping Crew Role",  value="crew",     emoji="👥",
                                     description="Notify crew members"),
                discord.SelectOption(label="No Ping",         value="none",     emoji="🔕",
                                     description="Post without any ping"),
            ],
        )
        self.cog = cog

    async def callback(self, interaction: discord.Interaction) -> None:
        member = interaction.user
        if not isinstance(member, discord.Member) or not _is_staff(member):
            return await interaction.response.send_message(
                "Only staff can use this panel.", ephemeral=True
            )
        await interaction.response.send_modal(
            GeneralAnnouncementModal(self.cog, self.values[0])
        )


class GeneralAnnouncePanelView(discord.ui.View):
    def __init__(self, cog: "AnnouncementPanelsCog"):
        super().__init__(timeout=None)
        self.cog = cog
        self.add_item(_PingSelect(cog))

    @discord.ui.button(label="Refresh Panel", emoji="♻️",
                       style=discord.ButtonStyle.secondary,
                       custom_id="diff_general_announce_refresh_v1")
    async def refresh_general_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user
        if not isinstance(member, discord.Member) or not _is_staff(member):
            return await interaction.response.send_message(
                "Only staff can refresh this panel.", ephemeral=True
            )
        await interaction.response.defer(ephemeral=True)
        await self.cog.ensure_general_panel()
        await interaction.followup.send("General announcement panel refreshed.", ephemeral=True)


# =========================================================
# COG
# =========================================================
class AnnouncementPanelsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot          = bot
        self.crew_view    = CrewAnnouncePanelView(self)
        self.general_view = GeneralAnnouncePanelView(self)
        self.bot.add_view(self.crew_view)
        self.bot.add_view(self.general_view)
        self.bot.add_view(AnnouncementButtons())

    async def log_action(self, guild: Optional[discord.Guild], message: str) -> None:
        if not guild:
            return
        ch = guild.get_channel(LOG_CHANNEL_ID)
        if isinstance(ch, discord.TextChannel):
            try:
                await ch.send(message)
            except Exception:
                pass

    def _crew_panel_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="📢 DIFF Crew Announcement Center",
            description=(
                "Use the **Make Crew Announcement** button below to post an official announcement.\n"
                "The bot will ping **Crew Members** automatically."
            ),
            color=discord.Color.dark_red(),
        )
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.add_field(
            name="📋 Posting Guidelines",
            value=(
                "• Keep announcements clear and important\n"
                "• Use short, descriptive titles\n"
                "• Avoid spam or duplicate posts\n"
                "• Staff use only — crew will be pinged"
            ),
            inline=False,
        )
        embed.set_footer(text=f"DIFF Crew Announcements  |  {CREW_PANEL_TAG}")
        embed.timestamp = datetime.now(timezone.utc)
        return embed

    def _general_panel_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="📢 DIFF General Announcement Center",
            color=discord.Color.dark_blue(),
            description=(
                "**Staff General Announcement Panel**\n\n"
                "Use the dropdown below to choose a ping type, then fill in your announcement.\n\n"
                "**Ping Options:**\n"
                "📣 **Ping @everyone** — notify all server members\n"
                "📍 **Ping @here** — notify online members only\n"
                "👥 **Ping Crew Role** — notify crew members\n"
                "🔕 **No Ping** — post without any ping\n\n"
                "**Each announcement includes tracking buttons:**\n"
                "✅ Acknowledge  ⏰ Remind Me  🔥 Interested  📍 View Updates\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Staff use only\n"
                "━━━━━━━━━━━━━━━━━━━━━━"
            ),
        )
        embed.add_field(
            name="📋 Staff Commands",
            value=(
                "`!refresh_general_announce_panel` — Refresh this panel\n"
                "`!announcement_stats <message_id>` — View tracking stats\n"
                "`!refresh_announcement_stats <message_id>` — Post stats to log"
            ),
            inline=False,
        )
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.set_footer(text=GENERAL_PANEL_TAG)
        return embed

    async def ensure_crew_panel(self) -> None:
        await _ensure_panel(
            self.bot, CREW_ANNOUNCE_CHANNEL_ID, CREW_PANEL_FILE,
            CREW_PANEL_TAG, self._crew_panel_embed(), self.crew_view, "Crew Announce",
        )

    async def ensure_general_panel(self) -> None:
        await _ensure_panel(
            self.bot, GENERAL_ANNOUNCE_CHANNEL_ID, GENERAL_PANEL_FILE,
            GENERAL_PANEL_TAG, self._general_panel_embed(), self.general_view, "General Announce",
        )

    @commands.Cog.listener()
    async def on_ready(self):
        await self.ensure_crew_panel()
        await self.ensure_general_panel()
        print("[AnnouncePanels] Cog ready.")

    @commands.command(name="refresh_crew_announce_panel")
    @commands.has_permissions(manage_guild=True)
    async def cmd_refresh_crew(self, ctx: commands.Context):
        await self.ensure_crew_panel()
        await ctx.send("Crew announcement panel refreshed.", delete_after=8)

    @commands.command(name="refresh_general_announce_panel")
    @commands.has_permissions(manage_guild=True)
    async def cmd_refresh_general(self, ctx: commands.Context):
        await self.ensure_general_panel()
        await ctx.send("General announcement panel refreshed.", delete_after=8)

    @commands.command(name="announcement_stats")
    @commands.has_permissions(manage_guild=True)
    async def cmd_announcement_stats(self, ctx: commands.Context, message_id: int):
        record = _get_record(message_id)
        if not record:
            return await ctx.send("No tracked announcement found for that message ID.", delete_after=10)
        embed = _build_stats_embed(ctx.guild, message_id, record)
        await ctx.send(embed=embed)

    @commands.command(name="refresh_announcement_stats")
    @commands.has_permissions(manage_guild=True)
    async def cmd_refresh_stats(self, ctx: commands.Context, message_id: int):
        record = _get_record(message_id)
        if not record:
            return await ctx.send("No tracked announcement found for that message ID.", delete_after=10)
        embed = _build_stats_embed(ctx.guild, message_id, record)
        log_ch = ctx.guild.get_channel(LOG_CHANNEL_ID)
        if isinstance(log_ch, discord.TextChannel):
            await log_ch.send(content="📊 Refreshed announcement stats:", embed=embed)
        await ctx.send("✅ Stats sent to the log channel.", delete_after=8)


# =========================================================
# SETUP
# =========================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(AnnouncementPanelsCog(bot))
