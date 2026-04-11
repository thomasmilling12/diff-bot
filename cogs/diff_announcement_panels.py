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
LOG_CHANNEL_ID         = 1485265848099799163
REMINDER_DELAY_MINUTES = 15

STAFF_ROLE_IDS: set[int] = {
    850391095845584937,
    850391378559238235,
    990011447193006101,
}

CREW_PANEL_TAG    = "DIFF_CREW_ANNOUNCE_PANEL_V2"
GENERAL_PANEL_TAG = "DIFF_GENERAL_ANNOUNCE_PANEL_V1"

DATA_DIR           = "diff_data"
CREW_PANEL_FILE    = os.path.join(DATA_DIR, "crew_announce_panel.json")
GENERAL_PANEL_FILE = os.path.join(DATA_DIR, "general_announce_panel.json")
TRACKING_FILE      = os.path.join(DATA_DIR, "announcement_tracking.json")

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


def _role_label(member: discord.Member) -> str:
    for role in reversed(member.roles):
        if role.id in STAFF_ROLE_IDS:
            return f" ({role.name})"
    return ""


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


def _latest_record() -> Optional[dict]:
    data = _load_tracking()["announcements"]
    if not data:
        return None
    latest_key = max(data.keys(), key=lambda k: data[k].get("created_at", ""))
    return data[latest_key]


def _build_stats_embed(guild: discord.Guild, message_id: int, record: dict) -> discord.Embed:
    acknowledged = len(record.get("acknowledged", {}))
    interested   = len(record.get("interested", {}))
    reminders    = len(record.get("remind_me", {}))
    total        = sum(1 for m in guild.members if not m.bot)
    pending      = max(total - acknowledged, 0)

    embed = discord.Embed(
        title="📊 Announcement Tracking Stats",
        color=discord.Color.blurple(),
        timestamp=datetime.now(timezone.utc),
        description=f"**{record.get('title', 'Untitled')}**",
    )
    embed.add_field(name="✅ Acknowledged", value=str(acknowledged), inline=True)
    embed.add_field(name="🔥 Interested",   value=str(interested),   inline=True)
    embed.add_field(name="⏰ Remind Me",    value=str(reminders),    inline=True)
    embed.add_field(name="⏳ Pending",      value=str(pending),      inline=True)
    embed.add_field(name="👥 Total Members", value=str(total),       inline=True)
    if record.get("message_url"):
        embed.add_field(name="📌 Jump To", value=f"[View Announcement]({record['message_url']})", inline=True)
    embed.set_thumbnail(url=DIFF_LOGO_URL)
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
        embed.set_thumbnail(url=DIFF_LOGO_URL)
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
                and ("DIFF_CREW_ANNOUNCE_PANEL" in (msg.embeds[0].footer.text or "")
                     or panel_tag in (msg.embeds[0].footer.text or ""))
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
class _AcknowledgeBtn(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Acknowledge", style=discord.ButtonStyle.success, emoji="✅",
            custom_id="diff_announce_acknowledge_v1",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
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


class _RemindMeBtn(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Remind Me", style=discord.ButtonStyle.secondary, emoji="⏰",
            custom_id="diff_announce_remind_v1",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
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


class _InterestedBtn(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Interested", style=discord.ButtonStyle.primary, emoji="🔥",
            custom_id="diff_announce_interested_v1",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
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


class AnnouncementButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(
            label="View Updates",
            style=discord.ButtonStyle.link,
            url=f"https://discord.com/channels/{GUILD_ID}/{VIEW_UPDATES_CHANNEL_ID}",
            emoji="📍",
        ))
        self.add_item(_AcknowledgeBtn())
        self.add_item(_RemindMeBtn())
        self.add_item(_InterestedBtn())


# =========================================================
# CREW ANNOUNCEMENT MODALS
# =========================================================
class CrewAnnouncementModal(discord.ui.Modal, title="Post Crew Announcement"):
    title_input = discord.ui.TextInput(
        label="Announcement Title",
        placeholder="Example: Saturday Meet Update",
        max_length=100, required=True,
    )
    message_input = discord.ui.TextInput(
        label="Announcement Message",
        placeholder="Type the full crew announcement here…",
        style=discord.TextStyle.paragraph, max_length=2000, required=True,
    )
    footer_input = discord.ui.TextInput(
        label="Sign-Off",
        placeholder="DIFF Management Team  /  DIFF Leadership",
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
        title    = str(self.title_input).strip()

        embed = discord.Embed(
            title=title,
            description=str(self.message_input),
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_author(
            name=f"Posted by {member.display_name}{_role_label(member)}",
            icon_url=member.display_avatar.url if member.display_avatar else None,
        )
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.set_footer(text=sign_off)

        crew_role = interaction.guild.get_role(CREW_ROLE_ID) if interaction.guild else None
        ping      = crew_role.mention if crew_role else ""

        tracking_view = AnnouncementButtons()
        msg = await channel.send(
            content=ping,
            embed=embed,
            view=tracking_view,
            allowed_mentions=discord.AllowedMentions(roles=True),
        )

        record = {
            "title":        title,
            "type":         "crew",
            "channel_id":   channel.id,
            "message_id":   msg.id,
            "message_url":  msg.jump_url,
            "created_by":   interaction.user.id,
            "created_at":   _utc_now(),
            "acknowledged": {},
            "remind_me":    {},
            "interested":   {},
        }
        _upsert_record(msg.id, record)

        await interaction.response.send_message(
            f"Crew announcement posted in {channel.mention}.", ephemeral=True
        )
        await self.cog.log_action(
            interaction.guild,
            f"📢 Crew announcement **{title}** posted by {member.mention} — {msg.jump_url}",
        )


class CrewQuickPingModal(discord.ui.Modal, title="Quick Crew Ping"):
    message_input = discord.ui.TextInput(
        label="Message",
        placeholder="A short, important message for the crew…",
        style=discord.TextStyle.paragraph, max_length=800, required=True,
    )

    def __init__(self, cog: "AnnouncementPanelsCog"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction) -> None:
        member = interaction.user
        if not isinstance(member, discord.Member) or not _is_staff(member):
            return await interaction.response.send_message(
                "Only staff can send crew pings.", ephemeral=True
            )

        channel = interaction.client.get_channel(CREW_ANNOUNCE_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message(
                "Crew announcement channel not found.", ephemeral=True
            )

        crew_role = interaction.guild.get_role(CREW_ROLE_ID) if interaction.guild else None
        ping      = crew_role.mention if crew_role else ""

        embed = discord.Embed(
            description=f"**📌 Quick Update from Staff**\n\n{str(self.message_input)}",
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_author(
            name=f"{member.display_name}{_role_label(member)}",
            icon_url=member.display_avatar.url if member.display_avatar else None,
        )
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.set_footer(text="DIFF Crew • Quick Update")

        await channel.send(
            content=ping,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True),
        )
        await interaction.response.send_message("Quick ping sent.", ephemeral=True)
        await self.cog.log_action(
            interaction.guild,
            f"⚡ Quick crew ping sent by {member.mention}",
        )


# =========================================================
# CREW PANEL DROPDOWN
# =========================================================
class _CrewAnnounceSelect(discord.ui.Select):
    def __init__(self, cog: "AnnouncementPanelsCog"):
        super().__init__(
            custom_id="diff_crew_announce_select_v2",
            placeholder="📢 Select an action…",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Post Crew Announcement",
                    value="announce",
                    emoji="📣",
                    description="Post a full embed announcement to Crew Members.",
                ),
                discord.SelectOption(
                    label="Quick Crew Ping",
                    value="quick",
                    emoji="⚡",
                    description="Send a short update without a title — fast and direct.",
                ),
                discord.SelectOption(
                    label="Posting Guidelines",
                    value="guidelines",
                    emoji="📋",
                    description="View best practices for crew announcements.",
                ),
                discord.SelectOption(
                    label="Latest Announcement Stats",
                    value="stats",
                    emoji="📊",
                    description="See acknowledgement tracking for the latest announcement.",
                ),
            ],
            row=0,
        )
        self.cog = cog

    async def callback(self, interaction: discord.Interaction) -> None:
        member = interaction.user
        if not isinstance(member, discord.Member) or not _is_staff(member):
            return await interaction.response.send_message(
                "Staff only.", ephemeral=True
            )

        selected = self.values[0]

        if selected == "announce":
            await interaction.response.send_modal(CrewAnnouncementModal(self.cog))

        elif selected == "quick":
            await interaction.response.send_modal(CrewQuickPingModal(self.cog))

        elif selected == "guidelines":
            embed = discord.Embed(
                title="📋 Crew Announcement Guidelines",
                description="Follow these when posting to keep the crew channel clean and credible.",
                color=discord.Color.dark_red(),
            )
            embed.add_field(
                name="✅ Do",
                value=(
                    "› Use clear, descriptive titles\n"
                    "› Keep the message focused and to the point\n"
                    "› Include all relevant info (dates, times, links)\n"
                    "› Use Quick Ping for short updates, full Announcement for detailed posts\n"
                    "› Sign off with your team name"
                ),
                inline=False,
            )
            embed.add_field(
                name="❌ Don't",
                value=(
                    "› Post duplicate or near-identical announcements\n"
                    "› Use crew ping for non-important messages\n"
                    "› Leave the sign-off blank for official posts\n"
                    "› Post personal messages in this channel"
                ),
                inline=False,
            )
            embed.add_field(
                name="📌 Ping Rules",
                value=(
                    "**Full Announcement** — always pings @Crew Members\n"
                    "**Quick Ping** — always pings @Crew Members\n"
                    "Only post if the content is relevant to the whole crew."
                ),
                inline=False,
            )
            embed.set_thumbnail(url=DIFF_LOGO_URL)
            embed.set_footer(text="DIFF Crew Announcements • Guidelines")
            await interaction.response.send_message(embed=embed, ephemeral=True)

        elif selected == "stats":
            record = _latest_record()
            if not record:
                return await interaction.response.send_message(
                    "No tracked announcements found yet.", ephemeral=True
                )
            embed = _build_stats_embed(interaction.guild, record["message_id"], record)
            await interaction.response.send_message(embed=embed, ephemeral=True)


# =========================================================
# CREW PANEL VIEW  (persistent)
# =========================================================
class _CrewAnnounceCreateBtn(discord.ui.Button):
    def __init__(self, cog: "AnnouncementPanelsCog"):
        super().__init__(
            label="Post Announcement", emoji="📣",
            style=discord.ButtonStyle.danger,
            custom_id="diff_crew_announce_create_v1",
            row=1,
        )
        self.cog = cog

    async def callback(self, interaction: discord.Interaction) -> None:
        member = interaction.user
        if not isinstance(member, discord.Member) or not _is_staff(member):
            return await interaction.response.send_message(
                "Only staff can use this button.", ephemeral=True
            )
        await interaction.response.send_modal(CrewAnnouncementModal(self.cog))


class _CrewAnnounceQuickBtn(discord.ui.Button):
    def __init__(self, cog: "AnnouncementPanelsCog"):
        super().__init__(
            label="Quick Ping", emoji="⚡",
            style=discord.ButtonStyle.secondary,
            custom_id="diff_crew_announce_quick_v1",
            row=1,
        )
        self.cog = cog

    async def callback(self, interaction: discord.Interaction) -> None:
        member = interaction.user
        if not isinstance(member, discord.Member) or not _is_staff(member):
            return await interaction.response.send_message(
                "Only staff can use this button.", ephemeral=True
            )
        await interaction.response.send_modal(CrewQuickPingModal(self.cog))


class CrewAnnouncePanelView(discord.ui.View):
    def __init__(self, cog: "AnnouncementPanelsCog"):
        super().__init__(timeout=None)
        self.cog = cog
        self.add_item(_CrewAnnounceSelect(cog))
        self.add_item(_CrewAnnounceCreateBtn(cog))
        self.add_item(_CrewAnnounceQuickBtn(cog))


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
            name=f"Posted by {member.display_name}{_role_label(member)}",
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
            "title":        title,
            "type":         "general",
            "channel_id":   channel.id,
            "message_id":   msg.id,
            "message_url":  msg.jump_url,
            "created_by":   interaction.user.id,
            "created_at":   _utc_now(),
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


class _GeneralRefreshBtn(discord.ui.Button):
    def __init__(self, cog: "AnnouncementPanelsCog"):
        super().__init__(
            label="Refresh Panel", emoji="♻️",
            style=discord.ButtonStyle.secondary,
            custom_id="diff_general_announce_refresh_v1",
        )
        self.cog = cog

    async def callback(self, interaction: discord.Interaction) -> None:
        member = interaction.user
        if not isinstance(member, discord.Member) or not _is_staff(member):
            return await interaction.response.send_message(
                "Only staff can refresh this panel.", ephemeral=True
            )
        await interaction.response.defer(ephemeral=True)
        await self.cog.ensure_general_panel()
        await interaction.followup.send("General announcement panel refreshed.", ephemeral=True)


class GeneralAnnouncePanelView(discord.ui.View):
    def __init__(self, cog: "AnnouncementPanelsCog"):
        super().__init__(timeout=None)
        self.cog = cog
        self.add_item(_PingSelect(cog))
        self.add_item(_GeneralRefreshBtn(cog))


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
            title="📢 DIFF Crew Announcement Centre",
            description=(
                "Staff-only announcement panel for **Crew Members**.\n"
                "Use the dropdown for all options, or the quick buttons below.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=discord.Color.dark_red(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(
            name="📣 Full Announcement",
            value="Formal embed with title, message, and sign-off. Pings @Crew Members.",
            inline=True,
        )
        embed.add_field(
            name="⚡ Quick Ping",
            value="Short urgent message without a title. Faster to post, same crew ping.",
            inline=True,
        )
        embed.add_field(
            name="📊 Tracking",
            value="Crew announcements include Acknowledge, Remind Me, and Interested buttons.",
            inline=False,
        )
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.set_footer(text=f"DIFF Crew Announcements  |  {CREW_PANEL_TAG}")
        return embed

    def _general_panel_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="📢 DIFF General Announcement Centre",
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
