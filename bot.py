import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from threading import Thread

from flask import Flask
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import commands

# =========================
# KEEP ALIVE FOR REPLIT
# =========================
app = Flask("")


@app.route("/")
def home():
    return "Bot is alive!"


def run_web():
    app.run(host="0.0.0.0", port=3000)


def keep_alive():
    t = Thread(target=run_web, daemon=True)
    t.start()


# =========================
# LOAD ENV
# =========================
load_dotenv()
TOKEN = os.getenv("TOKEN")

# =========================
# CONFIG
# =========================
GUILD_ID = 850386896509337710

DIFF_LOGO_URL = "https://media.discordapp.net/attachments/1107375326625005719/1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm=2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a&=&format=webp&quality=lossless&width=1376&height=917"
DIFF_BANNER_URL = DIFF_LOGO_URL

DATA_FILE = "diff_data.json"

MEET_INFO_CHANNEL_ID = 1266933655486332999
DIFF_HOSTS_CHANNEL_ID = 1195953265377021952
MEET_RULES_CHANNEL_ID = 1047178448776474644
UPCOMING_MEET_CHANNEL_ID = 1047178296191885402
JOIN_MEETS_CHANNEL_ID = 1277084633858576406
SUPPORT_TICKETS_CHANNEL_ID = 1156363575150002226

MEET_ANNOUNCEMENT_CHANNEL_ID = 1484768466023223418
RULES_CHANNEL_ID = 1047161846257438743

RULES_BTN_UPCOMING_MEETS_ID = 1047178296191885402
RULES_BTN_JOIN_MEETS_ID = 1277084633858576406
RULES_BTN_MEET_RULES_ID = 1047178448776474644
RULES_BTN_SUPPORT_ID = 1156363575150002226

VERIFIED_ROLE_ID = 1141424243616256032

HIERARCHY_CHANNEL_ID = 1195941548240687266

LEADER_ROLE_ID = 850391095845584937
CO_LEADER_ROLE_ID = 850391378559238235
MANAGER_ROLE_ID = 990011447193006101
HOST_ROLE_ID = 1055823929358430248
DESIGNER_TEAM_ROLE_ID = 1128901233160245278
CONTENT_TEAM_ROLE_ID = 1110037666147336293
COLOR_TEAM_ROLE_ID = 1115495008670330902
CREW_MEMBER_ROLE_ID = 886702076552441927

CREW_PANEL_CHANNEL_ID = 1103847009653358612
CREW_APPLICATIONS_CHANNEL_ID = 1485238837943734373

APPLICATION_TRACKER_CHANNEL_ID = 1485250394522386536
APPLICATION_REVIEW_CHANNEL_ID = 1485250641294131280
APPLICATION_INFO_REQUEST_CHANNEL_ID = 1485250641294131280
APPLICATION_TICKET_CATEGORY_ID = 1328457973583839282
MIN_GARAGE_PHOTOS = 10
GARAGE_TIMEOUT_HOURS = 24
APPROVED_MEMBER_ROLE_ID = CREW_MEMBER_ROLE_ID
APPLICATIONS_FILE = "diff_applications_full.json"

# =========================
# DISCORD SETUP
# =========================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# DATA
# =========================
def load_data():
    default_data = {
        "status_channel_id": 1195953265377021952,
        "panel_message_id": None,
        "meet_info_message_id": None,
        "hierarchy_message_id": None,
        "hierarchy_message_ids": [],
        "rules_message_ids": [],
        "crew_panel_message_id": None,
        "host_role_id": None,
        "meet_ping_role_id": None,
        "warnings": {},
        "hosts": [
            {"discord_id": 708024998228525167, "name": "Frostyy2003", "profile_url": "https://profile.playstation.com/Frostyy2003"},
            {"discord_id": 747199066525663235, "name": "BriMedia", "profile_url": "https://profile.playstation.com/BriMedia"},
            {"discord_id": 581563227402665984, "name": "Trlioz", "profile_url": "https://profile.playstation.com/Trlioz"},
            {"discord_id": 380049668178182154, "name": "FRDanjay016", "profile_url": "https://profile.playstation.com/FRDanjay016"},
            {"discord_id": 343488362331635714, "name": "honda3wheelers", "profile_url": "https://profile.playstation.com/honda3wheelers"},
            {"discord_id": 612129213000187914, "name": "TheeDarkBullet", "profile_url": "https://profile.playstation.com/TheeDarkBullet"},
            {"discord_id": 1000988147880054894, "name": "GtTamal3z", "profile_url": "https://profile.playstation.com/GtTamal3z"},
            {"discord_id": 1252445906901532692, "name": "Tso_Kyng", "profile_url": "https://profile.playstation.com/Tso_Kyng"},
            {"discord_id": 700021323279368262, "name": "SpMex0322", "profile_url": "https://profile.playstation.com/SpMex0322"},
        ],
    }

    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4)
        return default_data

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    loaded.setdefault("status_channel_id", 1195953265377021952)
    loaded.setdefault("panel_message_id", None)
    loaded.setdefault("host_role_id", None)
    loaded.setdefault("meet_info_message_id", None)
    loaded.setdefault("hierarchy_message_id", None)
    loaded.setdefault("hierarchy_message_ids", [])
    loaded.setdefault("rules_message_ids", [])
    loaded.setdefault("crew_panel_message_id", None)
    loaded.setdefault("meet_ping_role_id", None)
    loaded.setdefault("warnings", {})
    loaded.setdefault("hosts", default_data["hosts"])
    return loaded


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


data = load_data()
status_message_id = data.get("panel_message_id")

# =========================
# APPLICATION STORAGE
# =========================
def load_apps():
    if not os.path.exists(APPLICATIONS_FILE):
        return {"last_id": 0, "applications": {}}
    with open(APPLICATIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_apps(app_data):
    with open(APPLICATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(app_data, f, indent=2)


def create_next_app_id():
    app_data = load_apps()
    app_data["last_id"] += 1
    new_id = str(app_data["last_id"]).zfill(4)
    save_apps(app_data)
    return new_id


def get_app(app_id: str):
    return load_apps()["applications"].get(app_id)


def save_app(app_id: str, payload: dict):
    app_data = load_apps()
    app_data["applications"][app_id] = payload
    save_apps(app_data)


def update_app(app_id: str, **updates):
    app_data = load_apps()
    if app_id in app_data["applications"]:
        app_data["applications"][app_id].update(updates)
        save_apps(app_data)


# =========================
# HELPERS
# =========================
def utc_now():
    return datetime.utcnow()


def make_status_emoji(status: str) -> str:
    return {
        "Pending": "🟡 Pending",
        "More Info Requested": "🟠 More Info Requested",
        "Timed Out": "⏰ Timed Out",
        "Approved": "🟢 Approved",
        "Denied": "🔴 Denied",
        "Closed": "⚫ Closed",
    }.get(status, status)


def count_message_attachments(messages) -> int:
    total = 0
    for msg in messages:
        total += len(msg.attachments)
    return total


def is_staff_reviewer(member: discord.Member) -> bool:
    allowed = {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID}
    return any(role.id in allowed for role in member.roles)


async def safe_dm(user, message: str):
    try:
        await user.send(message)
    except Exception:
        pass


def build_review_embed(app_id: str, applicant, answers: dict, ticket_channel_id=None):
    embed = discord.Embed(
        title=f"DIFF Application #{app_id}",
        description="Staff: review the application and check the garage ticket before making a decision.",
        color=discord.Color.blurple(),
        timestamp=utc_now(),
    )
    embed.set_author(name=str(applicant), icon_url=applicant.display_avatar.url)
    embed.add_field(name="Applicant", value=f"{applicant.mention}\n`{applicant.id}`", inline=False)
    embed.add_field(name="Gamertag", value=answers.get("gamertag", "N/A"), inline=True)
    embed.add_field(name="Age", value=answers.get("age", "N/A"), inline=True)
    embed.add_field(name="Timezone", value=answers.get("timezone", "N/A"), inline=True)
    embed.add_field(name="GTA Rank", value=answers.get("gta_rank", "N/A"), inline=True)
    embed.add_field(name="How They Heard", value=answers.get("how_heard", "N/A"), inline=True)
    embed.add_field(name="Days Available", value=answers.get("days_available", "N/A"), inline=True)
    embed.add_field(name="Personal Skills", value=answers.get("personal_skills", "N/A"), inline=False)
    embed.add_field(name="DIFF Meet Experience", value=answers.get("meet_experience", "N/A"), inline=False)
    embed.add_field(name="Former Crews", value=answers.get("former_crews", "N/A"), inline=False)
    embed.add_field(name="Why They Should Join", value=answers.get("why_join", "N/A"), inline=False)
    embed.add_field(name="What They Bring", value=answers.get("what_bring", "N/A"), inline=False)
    if answers.get("comments"):
        embed.add_field(name="Comments", value=answers["comments"], inline=False)
    if ticket_channel_id:
        embed.add_field(name="Garage Ticket", value=f"<#{ticket_channel_id}>", inline=False)
    embed.set_footer(text="Status: Pending Review")
    return embed


def build_tracker_embed(app_id: str, applicant, answers: dict, status: str, reviewer_text: str = "Not reviewed yet"):
    color_map = {"Approved": discord.Color.green(), "Denied": discord.Color.red(), "Closed": discord.Color.dark_grey()}
    embed = discord.Embed(
        title=f"Application Tracker #{app_id}",
        description="DIFF application progress",
        color=color_map.get(status, discord.Color.orange()),
        timestamp=utc_now(),
    )
    embed.add_field(name="User", value=applicant.mention, inline=True)
    embed.add_field(name="Gamertag", value=answers.get("gamertag", "N/A"), inline=True)
    embed.add_field(name="Status", value=make_status_emoji(status), inline=True)
    embed.add_field(name="Reviewed By", value=reviewer_text, inline=False)
    embed.set_footer(text=f"Applicant ID: {applicant.id}")
    return embed


def build_denied_result_embed(custom_deny_reason: str):
    embed = discord.Embed(
        title="DIFF Application Result",
        description=(
            "Thank you for applying to Different Meets (DIFF).\n\n"
            "After careful review, your application has been denied at this time.\n\n"
            f"**Reason:**\n{custom_deny_reason}\n\n"
            "Our decisions are based on crew standards, activity, realism, and overall community fit.\n\n"
            "🔄 **Need Clarification?**\n\n"
            "If you would like more details about this decision or guidance on how to improve, "
            "you may use the button below to request additional feedback from our staff team.\n\n"
            "**Please note:**\n"
            "• This is not an appeal button\n"
            "• Spamming requests may result in restricted access\n"
            "• Staff responses may take time depending on availability\n\n"
            "We appreciate your interest in DIFF."
        ),
        color=discord.Color.red(),
        timestamp=utc_now(),
    )
    return embed


# =========================
# STAFF REPLY PANEL (posted in staff channel when applicant requests more info)
# =========================
STAFF_REPLY_RESPONSES = {
    "build": (
        "Thank you for requesting more information regarding your application.\n\n"
        "After further review, one of the main concerns was your vehicle build quality. At DIFF, we look for clean, realistic, "
        "and well-put-together builds that align with our crew standards.\n\n"
        "We recommend improving overall realism, presentation, and attention to detail before applying again. "
        "Once those areas are stronger, you are welcome to reapply."
    ),
    "activity": (
        "Thank you for reaching out.\n\n"
        "At this time, one of the main reasons for denial was activity and availability. DIFF expects members to remain active "
        "in Discord, communicate consistently, and attend meets regularly, especially on weekends.\n\n"
        "We recommend applying again once your schedule and availability better match our crew expectations."
    ),
    "effort": (
        "Thank you for requesting clarification.\n\n"
        "After reviewing your application again, we felt the overall effort and detail in your responses did not give us enough "
        "information to move forward confidently.\n\n"
        "When applying to DIFF, we expect thoughtful and complete answers that reflect seriousness, effort, and interest in joining "
        "the crew. You are welcome to reapply with stronger responses in the future."
    ),
    "knowledge": (
        "Thank you for reaching out for more information.\n\n"
        "One of the concerns with your application was a lack of demonstrated car knowledge. DIFF values members who have a real "
        "interest in cars and a solid understanding of car culture, builds, and meet standards.\n\n"
        "We encourage you to continue learning and become more familiar with the community before reapplying."
    ),
    "fit": (
        "Thank you for your request.\n\n"
        "After further consideration, we do not believe your application showed the overall fit we are looking for in DIFF. "
        "Our crew prioritizes realism, consistency, maturity, and strong community presence.\n\n"
        "This decision is based on overall alignment with our standards and environment. We appreciate your interest and wish you "
        "the best moving forward."
    ),
    "requirements": (
        "Thank you for following up.\n\n"
        "Your application was denied because one or more of the listed DIFF recruitment requirements were not met at this time. "
        "These requirements are in place to maintain quality and consistency across the crew.\n\n"
        "Please review the posted requirements carefully, and once you fully meet them, you are welcome to submit a new application."
    ),
    "later": (
        "Thank you for reaching out.\n\n"
        "At this time, we are not moving forward with your application, but this is not necessarily a permanent decision. "
        "We believe there is potential, but more improvement is needed before joining DIFF.\n\n"
        "Take some time to strengthen the areas mentioned, and you are welcome to reapply in the future."
    ),
    "custom": (
        "Thank you for requesting more information regarding your application.\n\n"
        "After further review, here is additional clarification from staff:\n\n"
        "[Staff: edit this message before sending — use `/staffreplypanel` or re-post manually]\n\n"
        "Please take this feedback into consideration before applying again."
    ),
}

STAFF_REPLY_OPTIONS = [
    discord.SelectOption(label="Build Quality", description="Vehicle build does not meet DIFF realism standards", value="build"),
    discord.SelectOption(label="Activity / Availability", description="Applicant may not be active enough for DIFF expectations", value="activity"),
    discord.SelectOption(label="Application Effort", description="Responses were too brief or lacked effort", value="effort"),
    discord.SelectOption(label="Car Knowledge", description="Applicant did not show enough car knowledge", value="knowledge"),
    discord.SelectOption(label="Community Fit", description="Applicant may not be the right fit for DIFF", value="fit"),
    discord.SelectOption(label="Requirements Not Met", description="Applicant does not meet one or more listed requirements", value="requirements"),
    discord.SelectOption(label="Reapply Later", description="Not accepted now, but may have potential later", value="later"),
    discord.SelectOption(label="Custom Response", description="Staff writes their own response", value="custom"),
]


class StaffReplyDropdown(discord.ui.Select):
    def __init__(self, applicant_id: int, app_id: str):
        self.applicant_id = applicant_id
        self.app_id = app_id
        super().__init__(placeholder="Choose a response category...", min_values=1, max_values=1, options=STAFF_REPLY_OPTIONS)

    async def callback(self, interaction: discord.Interaction):
        reply = STAFF_REPLY_RESPONSES.get(self.values[0], "No response found.")
        if not interaction.guild:
            return await interaction.response.send_message("This only works inside the server.", ephemeral=True)
        if not is_staff_reviewer(interaction.user):
            return await interaction.response.send_message("Only staff can use this panel.", ephemeral=True)
        applicant = interaction.guild.get_member(self.applicant_id)
        if applicant is None:
            return await interaction.response.send_message("Could not find the applicant in the server.", ephemeral=True)
        dm_ok = True
        try:
            await applicant.send(f"**DIFF Application #{self.app_id} — Staff Response**\n\n{reply}")
        except Exception:
            dm_ok = False
        try:
            await interaction.channel.send(
                f"📩 Staff reply sent to {applicant.mention} (App **#{self.app_id}**):\n\n{reply}"
            )
        except Exception:
            pass
        if dm_ok:
            await interaction.response.send_message(f"✅ Reply sent to {applicant.mention} via DM.", ephemeral=True)
        else:
            await interaction.response.send_message(
                f"⚠️ Could not DM {applicant.mention} (DMs may be off), but the reply was posted in this channel.",
                ephemeral=True,
            )


class StaffReplyView(discord.ui.View):
    def __init__(self, applicant_id: int, app_id: str):
        super().__init__(timeout=None)
        self.add_item(StaffReplyDropdown(applicant_id=applicant_id, app_id=app_id))


# Auto-detect version — used by /staffreplypanel command in any ticket channel
class AutoStaffReplyDropdown(discord.ui.Select):
    def __init__(self, target_user: discord.Member):
        self.target_user = target_user
        super().__init__(placeholder="Choose a response category...", min_values=1, max_values=1, options=STAFF_REPLY_OPTIONS)

    async def callback(self, interaction: discord.Interaction):
        reply = STAFF_REPLY_RESPONSES.get(self.values[0], "No response found.")
        if not is_staff_reviewer(interaction.user):
            return await interaction.response.send_message("Only staff can use this panel.", ephemeral=True)
        dm_ok = True
        try:
            await self.target_user.send(f"**DIFF Staff Response**\n\n{reply}")
        except Exception:
            dm_ok = False
        try:
            await interaction.channel.send(
                f"📩 Staff reply sent to {self.target_user.mention}:\n\n{reply}"
            )
        except Exception:
            pass
        if dm_ok:
            await interaction.response.send_message(f"✅ Reply sent to {self.target_user.mention} via DM.", ephemeral=True)
        else:
            await interaction.response.send_message(
                f"⚠️ Could not DM {self.target_user.mention} (DMs may be off), but the reply was posted in this channel.",
                ephemeral=True,
            )


class AutoStaffReplyView(discord.ui.View):
    def __init__(self, target_user: discord.Member):
        super().__init__(timeout=300)
        self.add_item(AutoStaffReplyDropdown(target_user=target_user))


class RespondButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Respond", style=discord.ButtonStyle.green, custom_id="diff_staff_respond_btn")

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Server only.", ephemeral=True)
        if not is_staff_reviewer(interaction.user):
            return await interaction.response.send_message("Only staff can use this.", ephemeral=True)
        ticket_owner = None
        async for msg in interaction.channel.history(limit=20):
            if not msg.author.bot:
                ticket_owner = interaction.guild.get_member(msg.author.id)
                break
        if ticket_owner is None:
            return await interaction.response.send_message(
                "❌ Could not detect the ticket owner. Make sure they have sent a message in this channel.",
                ephemeral=True,
            )
        await interaction.response.send_message(
            f"Replying to {ticket_owner.mention}. Select a response below:",
            view=AutoStaffReplyView(target_user=ticket_owner),
            ephemeral=True,
        )


class RespondButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RespondButton())


# =========================
# DENIED RESULT VIEW (sent to applicant via DM)
# =========================
class DeniedResultView(discord.ui.View):
    def __init__(self, app_id: str, applicant_id: int):
        super().__init__(timeout=None)
        self.app_id = app_id
        self.applicant_id = applicant_id

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger, emoji="❌", custom_id="diff_denied_close")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view=None)

    @discord.ui.button(label="Request More Info", style=discord.ButtonStyle.primary, emoji="🔄", custom_id="diff_denied_request_more_info")
    async def request_more_info_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        record = get_app(self.app_id)
        if not record:
            return await interaction.response.send_message("Application record not found.", ephemeral=True)
        if interaction.user.id != self.applicant_id:
            return await interaction.response.send_message("Only the applicant can use this button.", ephemeral=True)
        if record.get("denied_info_requested"):
            return await interaction.response.send_message(
                "You already requested more information for this denied application. Please wait for staff to respond.",
                ephemeral=True,
            )
        update_app(
            self.app_id,
            denied_info_requested=True,
            denied_info_requested_at=utc_now().isoformat(),
        )
        guild = interaction.guild
        if guild:
            info_channel = guild.get_channel(APPLICATION_INFO_REQUEST_CHANNEL_ID)
            if isinstance(info_channel, discord.TextChannel):
                deny_reason = record.get("deny_reason") or record.get("decision_reason") or "No reason saved."
                embed = discord.Embed(
                    title="📩 Info Request – Denied Application",
                    color=discord.Color.orange(),
                    timestamp=utc_now(),
                )
                embed.add_field(name="User", value=f"<@{self.applicant_id}>", inline=True)
                embed.add_field(name="User ID", value=str(self.applicant_id), inline=True)
                embed.add_field(name="Application ID", value=f"#{self.app_id}", inline=True)
                embed.add_field(name="Original Deny Reason", value=deny_reason, inline=False)
                embed.add_field(name="Status", value="User is requesting additional clarification.", inline=False)
                try:
                    await info_channel.send(embed=embed)
                    reply_embed = discord.Embed(
                        title="📩 DIFF Staff Response Panel",
                        description=(
                            f"Use the dropdown below to send a pre-written reply to <@{self.applicant_id}> (Application **#{self.app_id}**).\n"
                            "The selected response will be sent directly to their DMs."
                        ),
                        color=discord.Color.blue(),
                    )
                    await info_channel.send(embed=reply_embed, view=StaffReplyView(applicant_id=self.applicant_id, app_id=self.app_id))
                except Exception:
                    pass
        await interaction.response.send_message(
            "Your request for more information has been sent to DIFF staff. Please wait for a response.",
            ephemeral=True,
        )


# =========================
# APPLICATION REVIEW VIEW
# =========================
class ReviewView(discord.ui.View):
    def __init__(self, app_id: str, applicant_id: int):
        super().__init__(timeout=None)
        self.app_id = app_id
        self.applicant_id = applicant_id

    async def _check_photos(self, interaction: discord.Interaction, record: dict) -> bool:
        ticket_channel = interaction.guild.get_channel(record.get("ticket_channel_id")) if record.get("ticket_channel_id") else None
        if not isinstance(ticket_channel, discord.TextChannel):
            await interaction.response.send_message("Garage ticket channel could not be found.", ephemeral=True)
            return False
        messages = [m async for m in ticket_channel.history(limit=200)]
        photo_count = count_message_attachments(messages)
        if photo_count < MIN_GARAGE_PHOTOS:
            await interaction.response.send_message(
                f"This applicant only has **{photo_count}** uploaded file(s). Minimum required is **{MIN_GARAGE_PHOTOS}** before making a decision.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success, custom_id="diff_review_accept")
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Server only.", ephemeral=True)
        if not is_staff_reviewer(interaction.user):
            return await interaction.response.send_message("Only Leader, Co-Leader, or Manager can approve applications.", ephemeral=True)
        record = get_app(self.app_id)
        if not record:
            return await interaction.response.send_message("Application record not found.", ephemeral=True)
        if record.get("status") not in {"Pending", "More Info Requested"}:
            return await interaction.response.send_message("This application has already been reviewed.", ephemeral=True)
        if not await self._check_photos(interaction, record):
            return
        applicant = interaction.guild.get_member(self.applicant_id)
        if applicant is None:
            return await interaction.response.send_message("Applicant is no longer in the server.", ephemeral=True)
        approved_role = interaction.guild.get_role(APPROVED_MEMBER_ROLE_ID)
        if approved_role:
            try:
                await applicant.add_roles(approved_role, reason=f"DIFF application #{self.app_id} approved by {interaction.user}")
            except discord.Forbidden:
                return await interaction.response.send_message("I don't have permission to assign that role.", ephemeral=True)
        await self._finalize(interaction, "Approved", interaction.user, close_ticket=True)
        await safe_dm(applicant, f"Your DIFF application **#{self.app_id}** was **approved**. Welcome to DIFF! 🎉")

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger, custom_id="diff_review_deny")
    async def deny_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Server only.", ephemeral=True)
        if not is_staff_reviewer(interaction.user):
            return await interaction.response.send_message("Only Leader, Co-Leader, or Manager can deny applications.", ephemeral=True)
        record = get_app(self.app_id)
        if not record:
            return await interaction.response.send_message("Application record not found.", ephemeral=True)
        if record.get("status") not in {"Pending", "More Info Requested"}:
            return await interaction.response.send_message("This application has already been reviewed.", ephemeral=True)
        if not await self._check_photos(interaction, record):
            return
        await interaction.response.send_modal(DenyReasonModal(self.app_id, self.applicant_id, self))

    @discord.ui.button(label="Request More Info", style=discord.ButtonStyle.secondary, custom_id="diff_review_more_info")
    async def more_info_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Server only.", ephemeral=True)
        if not is_staff_reviewer(interaction.user):
            return await interaction.response.send_message("Only Leader, Co-Leader, or Manager can request more info.", ephemeral=True)
        record = get_app(self.app_id)
        if not record:
            return await interaction.response.send_message("Application record not found.", ephemeral=True)
        if record.get("status") not in {"Pending", "More Info Requested"}:
            return await interaction.response.send_message("This application has already been reviewed.", ephemeral=True)
        await interaction.response.send_modal(RequestMoreInfoModal(self.app_id, self.applicant_id, self))

    async def _finalize(self, interaction: discord.Interaction, new_status: str, reviewer: discord.Member, close_ticket: bool):
        for child in self.children:
            child.disabled = True
        record = get_app(self.app_id)
        if not record:
            return
        update_app(
            self.app_id,
            status=new_status,
            reviewed_by=str(reviewer),
            reviewed_by_id=reviewer.id,
            reviewed_at=utc_now().isoformat(),
            decision_reason=record.get("deny_reason") if new_status == "Denied" else record.get("decision_reason"),
        )
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green() if new_status == "Approved" else discord.Color.red()
        embed.set_footer(text=f"Status: {new_status} • Reviewed by {reviewer}")
        embed.timestamp = utc_now()
        await interaction.response.edit_message(embed=embed, view=self)
        guild = interaction.guild
        if guild:
            tracker_channel = guild.get_channel(APPLICATION_TRACKER_CHANNEL_ID)
            if tracker_channel and record.get("tracker_message_id"):
                try:
                    tracker_msg = await tracker_channel.fetch_message(record["tracker_message_id"])
                    try:
                        applicant = guild.get_member(record["user_id"]) or await guild.fetch_member(record["user_id"])
                    except Exception:
                        applicant = None
                    if applicant:
                        tracker_embed = build_tracker_embed(self.app_id, applicant, record, new_status, reviewer.mention)
                        await tracker_msg.edit(embed=tracker_embed)
                except Exception:
                    pass
            if close_ticket and record.get("ticket_channel_id"):
                ticket_ch = guild.get_channel(record["ticket_channel_id"])
                if isinstance(ticket_ch, discord.TextChannel):
                    try:
                        await ticket_ch.send(embed=discord.Embed(
                            title="Application Decision",
                            description=f"This application has been **{new_status.lower()}**. This ticket will now be closed.",
                            color=discord.Color.green() if new_status == "Approved" else discord.Color.red(),
                            timestamp=utc_now(),
                        ))
                    except Exception:
                        pass
                    try:
                        await ticket_ch.edit(name=f"closed-{ticket_ch.name[:80]}")
                    except Exception:
                        pass
                    try:
                        await ticket_ch.set_permissions(guild.default_role, view_channel=False)
                    except Exception:
                        pass
                    try:
                        applicant_member = guild.get_member(record["user_id"])
                        if applicant_member:
                            await ticket_ch.set_permissions(applicant_member, overwrite=None)
                    except Exception:
                        pass
                    update_app(self.app_id, ticket_closed=True, closed_at=utc_now().isoformat())


# =========================
# REQUEST MORE INFO MODAL
# =========================
class RequestMoreInfoModal(discord.ui.Modal, title="Request More Info"):
    message = discord.ui.TextInput(
        label="What info/photos do they need to add?",
        placeholder="Example: Please upload 10 clear garage photos and a few closeups of your main builds.",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=True,
    )

    def __init__(self, app_id: str, applicant_id: int, review_view: "ReviewView"):
        super().__init__()
        self.app_id = app_id
        self.applicant_id = applicant_id
        self.review_view = review_view

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Server only.", ephemeral=True)
        record = get_app(self.app_id)
        if not record:
            return await interaction.response.send_message("Application record not found.", ephemeral=True)
        update_app(
            self.app_id,
            status="More Info Requested",
            reviewed_by=str(interaction.user),
            reviewed_by_id=interaction.user.id,
            reviewed_at=utc_now().isoformat(),
            more_info_request=str(self.message),
        )
        embed = interaction.message.embeds[0] if interaction.message and interaction.message.embeds else None
        if embed:
            embed.color = discord.Color.orange()
            embed.set_footer(text=f"Status: More Info Requested • Reviewed by {interaction.user}")
            embed.timestamp = utc_now()
            await interaction.message.edit(embed=embed, view=self.review_view)
        applicant = interaction.guild.get_member(self.applicant_id)
        ticket_channel = interaction.guild.get_channel(record.get("ticket_channel_id")) if record.get("ticket_channel_id") else None
        if isinstance(ticket_channel, discord.TextChannel):
            await ticket_channel.send(embed=discord.Embed(
                title="Staff Requested More Info",
                description=(
                    f"{applicant.mention if applicant else 'Applicant'}, staff needs more from you before they can decide.\n\n"
                    f"**Request:**\n{self.message}"
                ),
                color=discord.Color.orange(),
                timestamp=utc_now(),
            ))
        if applicant:
            await safe_dm(
                applicant,
                f"DIFF application **#{self.app_id}** needs more info/photos before staff can decide.\n\nRequest:\n{self.message}",
            )
        tracker_channel = interaction.guild.get_channel(APPLICATION_TRACKER_CHANNEL_ID)
        if isinstance(tracker_channel, discord.TextChannel) and record.get("tracker_message_id"):
            try:
                tracker_msg = await tracker_channel.fetch_message(record["tracker_message_id"])
                tracker_embed = build_tracker_embed(
                    self.app_id,
                    applicant or interaction.user,
                    record,
                    "More Info Requested",
                    interaction.user.mention,
                )
                await tracker_msg.edit(embed=tracker_embed)
            except Exception:
                pass
        await interaction.response.send_message("Requested more info from the applicant.", ephemeral=True)


# =========================
# DENY REASON MODAL
# =========================
class DenyReasonModal(discord.ui.Modal, title="Deny Application"):
    reason = discord.ui.TextInput(
        label="Reason for denial",
        placeholder="Explain why the application is being denied.",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=True,
    )

    def __init__(self, app_id: str, applicant_id: int, review_view: "ReviewView"):
        super().__init__()
        self.app_id = app_id
        self.applicant_id = applicant_id
        self.review_view = review_view

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Server only.", ephemeral=True)
        record = get_app(self.app_id)
        if not record:
            return await interaction.response.send_message("Application record not found.", ephemeral=True)
        deny_reason = str(self.reason)
        update_app(
            self.app_id,
            deny_reason=deny_reason,
            denied_info_requested=False,
            denied_info_requested_at=None,
        )
        await self.review_view._finalize(interaction, "Denied", interaction.user, close_ticket=True)
        applicant = interaction.guild.get_member(self.applicant_id)
        denied_embed = build_denied_result_embed(deny_reason)
        denied_view = DeniedResultView(self.app_id, self.applicant_id)
        if applicant:
            try:
                await applicant.send(embed=denied_embed, view=denied_view)
            except Exception:
                await safe_dm(applicant, f"Your DIFF application **#{self.app_id}** was denied.\n\nReason: {deny_reason}")
        ticket_channel = interaction.guild.get_channel(record.get("ticket_channel_id")) if record.get("ticket_channel_id") else None
        if isinstance(ticket_channel, discord.TextChannel):
            try:
                await ticket_channel.send(embed=denied_embed)
            except Exception:
                pass


# =========================
# HELPERS (CONTINUED)
# =========================
def get_activity(member: discord.Member) -> str:
    if member.activity and getattr(member.activity, "name", None):
        return member.activity.name
    return "Idle"


def build_channel_link(guild_id: int, channel_id: int) -> str:
    return f"https://discord.com/channels/{guild_id}/{channel_id}"


def is_host_or_admin(interaction: discord.Interaction) -> bool:
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        return False
    if interaction.user.guild_permissions.administrator:
        return True
    host_role_id = data.get("host_role_id")
    if host_role_id is None:
        return False
    return any(role.id == host_role_id for role in interaction.user.roles)



def get_warning_count(member_id: int) -> int:
    return len(data.get("warnings", {}).get(str(member_id), []))


def add_warning(member_id: int, moderator_id: int, reason: str):
    warnings = data.setdefault("warnings", {})
    member_warnings = warnings.setdefault(str(member_id), [])
    member_warnings.append(
        {
            "reason": reason,
            "moderator_id": moderator_id,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        }
    )
    save_data(data)


def clear_warnings_for_member(member_id: int):
    warnings = data.setdefault("warnings", {})
    warnings[str(member_id)] = []
    save_data(data)



def get_member_status_emoji(member: discord.Member) -> str:
    if member.status == discord.Status.online:
        return "🟢"
    if member.status == discord.Status.idle:
        return "🌙"
    if member.status == discord.Status.dnd:
        return "⛔"
    return "⚫"


def sort_members_for_hierarchy(members):
    status_order = {
        discord.Status.online: 0,
        discord.Status.idle: 1,
        discord.Status.dnd: 2,
        discord.Status.offline: 3,
    }
    return sorted(
        members,
        key=lambda m: (
            status_order.get(m.status, 4),
            m.display_name.lower(),
        ),
    )


def format_role_member_lines(role: discord.Role) -> str:
    members = sort_members_for_hierarchy(role.members)
    header = role.mention

    if not members:
        return f"{header}\nNo members assigned yet."

    lines = [f"{get_member_status_emoji(member)} {member.mention}" for member in members]
    value = header + "\n" + "\n".join(lines)

    if len(value) <= 1024:
        return value

    trimmed_lines = []
    current_len = 0
    for line in lines:
        extra = len(line) + (1 if trimmed_lines else 0)
        if current_len + extra > 990:
            break
        trimmed_lines.append(line)
        current_len += extra

    remaining = len(lines) - len(trimmed_lines)
    if remaining > 0:
        trimmed_lines.append(f"…and {remaining} more")

    return header + "\n" + "\n".join(trimmed_lines)


def build_hierarchy_embeds(guild: discord.Guild):
    role_sections = [
        ("👑 Leadership", [
            (LEADER_ROLE_ID, "👑 Leader"),
            (CO_LEADER_ROLE_ID, "🛡️ Co-Leader"),
            (MANAGER_ROLE_ID, "🔴 Managers"),
        ]),
        ("🏁 Meet Operations", [
            (HOST_ROLE_ID, "🏁 Meet Hosts"),
        ]),
        ("🎨 Creative Teams", [
            (DESIGNER_TEAM_ROLE_ID, "🎨 Designer Team"),
            (CONTENT_TEAM_ROLE_ID, "📸 Content Team"),
            (COLOR_TEAM_ROLE_ID, "🌈 Color Team"),
        ]),
    ]

    panel_descriptions = [
        "Server staff.",
        "Live member list.",
        f"Need help? Open <#{SUPPORT_TICKETS_CHANNEL_ID}>.",
    ]

    embeds = []
    for index, (section_title, entries) in enumerate(role_sections):
        embed = discord.Embed(
            title="🏆 DIFF SERVER HIERARCHY",
            description=panel_descriptions[index] if index < len(panel_descriptions) else "Server staff and teams.",
            color=0xC9A227,
        )
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.set_image(url=DIFF_BANNER_URL)
        embed.add_field(
            name=section_title,
            value="━━━━━━━━━━━━━━━━━━━━",
            inline=False,
        )

        for role_id, label in entries:
            role = guild.get_role(role_id)
            if role is None:
                embed.add_field(
                    name=label,
                    value="Role not found.",
                    inline=False,
                )
                continue

            embed.add_field(
                name="\u200b",
                value=format_role_member_lines(role),
                inline=False,
            )

        embed.set_footer(
            text=f"DIFF Meets • Last updated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
        )
        embeds.append(embed)

    return embeds


async def cleanup_extra_hierarchy_messages(channel: discord.TextChannel, keep_ids: list[int]):
    try:
        async for msg in channel.history(limit=50):
            if msg.author != bot.user:
                continue
            if msg.id in keep_ids:
                continue
            if msg.embeds and any(embed.title == "🏆 DIFF SERVER HIERARCHY" for embed in msg.embeds):
                try:
                    await msg.delete()
                except Exception:
                    pass
            elif msg.content and "DIFF Hierarchy Panel" in msg.content:
                try:
                    await msg.delete()
                except Exception:
                    pass
    except Exception:
        pass


async def find_existing_hierarchy_messages(channel: discord.TextChannel, expected_count: int):
    found = []
    try:
        async for msg in channel.history(limit=50, oldest_first=True):
            if msg.author != bot.user:
                continue
            if msg.embeds and any(embed.title == "🏆 DIFF SERVER HIERARCHY" for embed in msg.embeds):
                found.append(msg)
                if len(found) == expected_count:
                    break
    except Exception:
        return []
    return found


async def find_existing_status_panel_message(channel: discord.TextChannel):
    try:
        async for msg in channel.history(limit=50, oldest_first=True):
            if msg.author != bot.user:
                continue
            if msg.embeds and any(embed.title == "🏁 DIFF Meets Crew" for embed in msg.embeds):
                return msg
    except Exception:
        return None
    return None


async def cleanup_extra_status_panel_messages(channel: discord.TextChannel, keep_id: int | None):
    try:
        async for msg in channel.history(limit=50):
            if msg.author != bot.user:
                continue
            if keep_id and msg.id == keep_id:
                continue
            if msg.embeds and any(embed.title == "🏁 DIFF Meets Crew" for embed in msg.embeds):
                try:
                    await msg.delete()
                except Exception:
                    pass
    except Exception:
        pass


def build_hierarchy_support_view() -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(
        label="Support Tickets",
        style=discord.ButtonStyle.link,
        emoji="🎟️",
        url=build_channel_link(GUILD_ID, SUPPORT_TICKETS_CHANNEL_ID),
    ))
    return view


async def post_or_refresh_hierarchy_panel(guild: discord.Guild):
    channel = guild.get_channel(HIERARCHY_CHANNEL_ID)
    if channel is None:
        return False, "Hierarchy channel not found."

    embeds = build_hierarchy_embeds(guild)
    support_view = build_hierarchy_support_view()
    hierarchy_message_ids = data.get("hierarchy_message_ids", [])

    saved_messages = []
    if hierarchy_message_ids:
        for message_id in hierarchy_message_ids:
            try:
                msg = await channel.fetch_message(message_id)
                saved_messages.append(msg)
            except discord.NotFound:
                saved_messages = []
                break

    if saved_messages and len(saved_messages) == len(embeds):
        for i, (msg, embed) in enumerate(zip(saved_messages, embeds)):
            is_last = i == len(embeds) - 1
            await msg.edit(
                content="## DIFF Hierarchy Panel" if i == 0 else None,
                embed=embed,
                view=support_view if is_last else discord.ui.View(),
            )
        await cleanup_extra_hierarchy_messages(channel, [msg.id for msg in saved_messages])
        return True, channel.mention

    # recover old single-id storage if present
    legacy_message_id = data.get("hierarchy_message_id")
    if not saved_messages and legacy_message_id:
        try:
            legacy_message = await channel.fetch_message(legacy_message_id)
            saved_messages = [legacy_message]
        except discord.NotFound:
            saved_messages = []

    if saved_messages:
        for msg in saved_messages:
            try:
                await msg.delete()
            except Exception:
                pass

    new_ids = []
    for index, embed in enumerate(embeds):
        content = "## DIFF Hierarchy Panel" if index == 0 else None
        is_last = index == len(embeds) - 1
        msg = await channel.send(content=content, embed=embed, view=support_view if is_last else None)
        new_ids.append(msg.id)

    data["hierarchy_message_ids"] = new_ids
    data["hierarchy_message_id"] = new_ids[0] if new_ids else None
    save_data(data)
    await cleanup_extra_hierarchy_messages(channel, new_ids)
    return True, channel.mention


async def _auto_refresh_hierarchy_panel(guild: discord.Guild):
    await asyncio.sleep(15)
    hierarchy_message_ids = data.get("hierarchy_message_ids", [])
    if not hierarchy_message_ids:
        return
    channel = guild.get_channel(HIERARCHY_CHANNEL_ID)
    if channel is None:
        return
    embeds = build_hierarchy_embeds(guild)
    support_view = build_hierarchy_support_view()
    saved_messages = []
    for message_id in hierarchy_message_ids:
        try:
            msg = await channel.fetch_message(message_id)
            saved_messages.append(msg)
        except discord.NotFound:
            return
    if len(saved_messages) != len(embeds):
        return
    for i, (msg, embed) in enumerate(zip(saved_messages, embeds)):
        is_last = i == len(embeds) - 1
        try:
            await msg.edit(
                content="## DIFF Hierarchy Panel" if i == 0 else None,
                embed=embed,
                view=support_view if is_last else discord.ui.View(),
            )
        except Exception:
            pass


def build_status_embed(guild: discord.Guild) -> discord.Embed:
    embed = discord.Embed(
        title="🏁 DIFF Meets Crew",
        description="**Live Host Activity Board**\nStay connected. Stay active.",
        color=0xC9A227,
    )
    embed.set_thumbnail(url=DIFF_LOGO_URL)
    embed.set_image(url=DIFF_BANNER_URL)

    gta_hosts = []
    online_hosts = []
    offline_hosts = []

    for host in data["hosts"]:
        member = guild.get_member(host["discord_id"])

        if member:
            is_online = member.status != discord.Status.offline
            activity = get_activity(member)
            name = member.display_name
        else:
            is_online = False
            activity = "Offline"
            name = host["name"]

        line = f"**{name}**\n🎮 `{activity}`\n🔗 [View Profile]({host['profile_url']})"
        activity_lower = activity.lower()

        if is_online:
            if "grand theft auto" in activity_lower or "gta" in activity_lower:
                gta_hosts.append(f"🟢 {line}")
            else:
                online_hosts.append(f"🟡 {line}")
        else:
            offline_hosts.append(f"🔴 {line}")

    if gta_hosts:
        embed.add_field(name="🎮 In GTA Right Now", value="\n\n".join(gta_hosts), inline=False)
    if online_hosts:
        embed.add_field(name="🟡 Online Elsewhere", value="\n\n".join(online_hosts), inline=False)
    if offline_hosts:
        embed.add_field(name="🔴 Parked", value="\n\n".join(offline_hosts), inline=False)

    embed.set_footer(text=f"DIFF Meets • EST. 2020 • {datetime.utcnow().strftime('%H:%M:%S UTC')}")
    return embed


def build_meet_info_embed() -> discord.Embed:
    meet_rules_mention = f"<#{MEET_RULES_CHANNEL_ID}>"
    join_meets_mention = f"<#{JOIN_MEETS_CHANNEL_ID}>"
    upcoming_meet_mention = f"<#{UPCOMING_MEET_CHANNEL_ID}>"
    support_tickets_mention = f"<#{SUPPORT_TICKETS_CHANNEL_ID}>"
    diff_hosts_mention = f"<#{DIFF_HOSTS_CHANNEL_ID}>"

    embed = discord.Embed(
        title="📘 DIFF Meets | Meet Info",
        description=(
            "Below is the following info during the meets.\n"
            "Please make sure you understand the rules before joining.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "**🎙 Voice Channel**\n"
            "▢ When joining the voice channel, please look at the channel name to make sure you are in the right session.\n"
            "▢ **ALL HOSTS HAVE THE PERMS TO MUTE & KICK MEMBERS FROM THEIR VC IF THEY ARE TALKING OVER THE HOST OR BREAKING ANY CAR MEET RULES.**\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "**🛠 Report Another Player**\n"
            f"▢ If you are having an issue with someone during the meet or discord server, please do not hesitate to create a ticket found at {support_tickets_mention} for assistance by the DIFF Management team.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "**⚠️ Warnings & Ban Appeals**\n"
            f"▢ Warnings will be given if you break any rules found at {meet_rules_mention}.\n"
            "▢ After your second warning you will be banned from the server and meets.\n\n"
            "▢ Once banned, you will receive a DM from a Crew Manager stating that you have been banned from our server which will include the reason.\n\n"
            "▢ Ban Appeals: you can appeal your ban after 30 days. Members of the Hosts & Management team vote on your appeal.\n"
            "▢ We believe this is a very simple, clear, and fair system.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "**🚗 How to Join the Meets**\n"
            "▢ All new members must be in our discord server.\n"
            "▢ Your discord name must match your PSN.\n"
            f"▢ Once you have completed the steps found at {join_meets_mention}, please note this is to gain access to the server and change your discord name.\n"
            f"▢ When the meets are happening, you must add the hosts found at {diff_hosts_mention} and check updates in {upcoming_meet_mention}.\n"
            "▢ They will only add you back if you send a screen recording of your garages."
        ),
        color=0xC9A227,
    )
    embed.set_thumbnail(url=DIFF_LOGO_URL)
    embed.set_image(url=DIFF_BANNER_URL)
    embed.set_footer(text="DIFF Meets • Read everything before joining")
    return embed


def build_meet_info_view(guild_id: int) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(label="Meet Rules", style=discord.ButtonStyle.link, emoji="📜", url=build_channel_link(guild_id, MEET_RULES_CHANNEL_ID)))
    view.add_item(discord.ui.Button(label="Join Meets", style=discord.ButtonStyle.link, emoji="📥", url=build_channel_link(guild_id, JOIN_MEETS_CHANNEL_ID)))
    view.add_item(discord.ui.Button(label="Upcoming Meet", style=discord.ButtonStyle.link, emoji="📅", url=build_channel_link(guild_id, UPCOMING_MEET_CHANNEL_ID)))
    view.add_item(discord.ui.Button(label="Support Tickets", style=discord.ButtonStyle.link, emoji="🎟️", url=build_channel_link(guild_id, SUPPORT_TICKETS_CHANNEL_ID)))
    view.add_item(discord.ui.Button(label="Hosts", style=discord.ButtonStyle.link, emoji="👥", url=build_channel_link(guild_id, DIFF_HOSTS_CHANNEL_ID)))
    return view


def get_rules_embed():
    embed = discord.Embed(
        title="💙🚗 DIFF MEETS • OFFICIAL RULES 🚗💙",
        description=(
            "Please make sure you follow all DIFF Meet rules and guidelines when attending DIFF car meets.\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📜 **DIFF RULES**\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        color=discord.Color.gold(),
    )
    embed.set_thumbnail(url=DIFF_LOGO_URL)
    embed.set_image(url=DIFF_BANNER_URL)

    rules_part1 = (
        "🚫 **1.** No weaponized or armored vehicles allowed.\n\n"
        "🚫 **2.** No passing or overtaking on cruises.\n\n"
        "🚫 **3.** No drifting or burnouts at the meet spot.\n\n"
        "🚫 **4.** No excessive revving or honking.\n\n"
        "🚫 **5.** No harassment or bullying.\n"
        "→ Keep negative feedback to yourself.\n\n"
        "✅ **6.** If you are lagging, go into passive mode and head to the back of the cruise.\n\n"
        "🚫 **7.** If you want to stance your vehicle, do it at least 3 blocks away and call Lester.\n\n"
        "🚫 **8.** No guns or weapons during the car meet.\n\n"
        "✅ **9.** Be respectful to the host and DIFF crew members at all times."
    )

    rules_part2 = (
        "🚫 **10.** Do not stand on your vehicle or another meet-attendee's vehicle.\n\n"
        "✅ **11.** Stay in game chat at all times.\n\n"
        "🚫 **12.** Stay ground-level at all times.\n"
        "→ No roofs or ladders.\n\n"
        "✅ **13.** Make sure you are aware of the car class chosen for the meet.\n\n"
        "✅ **14.** If you have an issue during the meet, ask a DIFF member for assistance.\n\n"
        "🚫 **15.** If you fly to the meet, land at least 10 blocks away and land the aircraft.\n\n"
        "🚫 **16.** No modded cars or riced-out builds during DIFF meets.\n\n"
        "🚫 **17.** No CEO is allowed.\n"
        "→ Use Motorcycle Club only during the meet.\n\n"
        "🔴 **Failure to follow these rules puts you at risk of getting blocked and banned from future DIFF Car Meets.**"
    )

    embed.add_field(name="📜 Rules (1/2)", value=rules_part1, inline=False)
    embed.add_field(name="📜 Rules (2/2)", value=rules_part2, inline=False)
    embed.set_footer(text="Press the green button below if you understand and accept the rules.")
    return embed




def get_discord_rules_embed():
    embed = discord.Embed(
        title="💬🛡️ DIFF DISCORD • SERVER RULES 🛡️💬",
        description=(
            "Follow these rules to keep the server clean, respectful, and enjoyable.\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💬 **DISCORD RULES**\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        color=discord.Color.blue(),
    )

    embed.set_thumbnail(url=DIFF_LOGO_URL)
    embed.set_image(url=DIFF_BANNER_URL)

    rules_part1 = (
        "🚫 **1. No spamming or flooding chats**\n"
        "↳ Keep messages readable\n\n"
        "🚫 **2. No self-promo without permission**\n"
        "↳ Ask staff first\n\n"
        "🚫 **3. No hate speech, racism, or discrimination**\n"
        "↳ Zero tolerance\n\n"
        "🚫 **4. No NSFW content**\n"
        "↳ Keep it clean\n\n"
        "🚫 **5. No impersonation of staff or members**\n\n"
        "🚫 **6. Do not argue with staff publicly**\n"
        "↳ Use tickets instead"
    )

    rules_part2 = (
        "✅ **7. Use the correct channels**\n\n"
        "✅ **8. Respect everyone in the server**\n\n"
        "🚫 **9. No leaking personal information**\n\n"
        "🚫 **10. No trolling or baiting drama**\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🔴 **Violations may result in:**\n"
        "• Warnings\n"
        "• Mutes\n"
        "• Kicks\n"
        "• Permanent bans"
    )

    embed.add_field(name="📜 Rules (1/2)", value=rules_part1, inline=False)
    embed.add_field(name="📜 Rules (2/2)", value=rules_part2, inline=False)
    embed.set_footer(text="DIFF Meets • Keep it clean • Keep it respectful")
    return embed



def get_bannable_offenses_embed():
    embed = discord.Embed(
        title="🚫⚠️ DIFF • BANNABLE OFFENSES ⚠️🚫",
        description=(
            "These actions can lead to instant removal, severe punishment, or permanent bans depending on the situation.\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🚫 **BANNABLE OFFENSES**\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        color=discord.Color.red(),
    )
    embed.set_thumbnail(url=DIFF_LOGO_URL)
    embed.set_image(url=DIFF_BANNER_URL)

    offenses_part1 = (
        "🚫 **1. Repeated harassment or bullying**\n"
        "↳ Targeted disrespect will not be tolerated\n\n"
        "🚫 **2. Hate speech, slurs, or discrimination**\n\n"
        "🚫 **3. Threats, doxxing, or leaking private info**\n\n"
        "🚫 **4. Ban evasion**\n"
        "↳ Including helping others evade punishment\n\n"
        "🚫 **5. Repeated trolling or raid behavior**"
    )

    offenses_part2 = (
        "🚫 **6. Staff impersonation or fake authority claims**\n\n"
        "🚫 **7. Major meet disruption after warnings**\n"
        "↳ Crashing meets, griefing, repeated rule breaking\n\n"
        "🚫 **8. Posting NSFW or severely inappropriate content**\n\n"
        "🚫 **9. Scamming, malicious links, or harmful behavior**\n\n"
        "🔴 **Punishment may be instant depending on severity and staff review.**"
    )

    embed.add_field(name="🚫 Offenses (1/2)", value=offenses_part1, inline=False)
    embed.add_field(name="🚫 Offenses (2/2)", value=offenses_part2, inline=False)
    embed.set_footer(text="DIFF Meets • Serious violations can result in a permanent ban")
    return embed




class RulesAcceptView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id

    @discord.ui.button(
        label="✅ I Understand & Accept",
        style=discord.ButtonStyle.success,
        custom_id="diff_rules_accept_button",
    )
    async def accept_rules(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            await interaction.response.send_message("Use this in the server.", ephemeral=True)
            return

        role = interaction.guild.get_role(VERIFIED_ROLE_ID)
        if role is None:
            await interaction.response.send_message("Verified role not found.", ephemeral=True)
            return

        member = interaction.guild.get_member(interaction.user.id)
        if member is None:
            await interaction.response.send_message("Member not found.", ephemeral=True)
            return

        if role in member.roles:
            await interaction.response.send_message("You already accepted the rules.", ephemeral=True)
            return

        try:
            await member.add_roles(role, reason="Accepted DIFF rules")
        except discord.Forbidden:
            await interaction.response.send_message(
                "I couldn't assign the Verified role. Make sure my bot role is above it and I have Manage Roles.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            "✅ You accepted the rules and got the Verified role. Welcome to DIFF Meets.",
            ephemeral=True,
        )


# =========================
# RSVP VIEW
# =========================
class RSVPView(discord.ui.View):
    def __init__(self, host_user_id: int):
        super().__init__(timeout=None)
        self.host_user_id = host_user_id
        self.pulling_up_ids = set()
        self.maybe_ids = set()
        self.cant_make_it_ids = set()

    def _format_mentions(self, user_ids):
        if not user_ids:
            return "None"
        return ", ".join(f"<@{uid}>" for uid in user_ids)

    def _update_embed(self, embed: discord.Embed):
        tracker_text = (
            f"✅ Pulling Up: **{len(self.pulling_up_ids)}**\n"
            f"🤔 Maybe: **{len(self.maybe_ids)}**\n"
            f"❌ Can't Make It: **{len(self.cant_make_it_ids)}**\n\n"
            f"**Pulling Up:** {self._format_mentions(self.pulling_up_ids)}\n"
            f"**Maybe:** {self._format_mentions(self.maybe_ids)}\n"
            f"**Can't Make It:** {self._format_mentions(self.cant_make_it_ids)}"
        )
        for i, field in enumerate(embed.fields):
            if field.name == "📊 RSVP Tracker":
                embed.set_field_at(i, name="📊 RSVP Tracker", value=tracker_text, inline=False)
                break
        else:
            embed.add_field(name="📊 RSVP Tracker", value=tracker_text, inline=False)

    @discord.ui.button(label="Pulling Up", style=discord.ButtonStyle.success, emoji="✅")
    async def pulling_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        self.maybe_ids.discard(user_id)
        self.cant_make_it_ids.discard(user_id)
        self.pulling_up_ids.add(user_id)

        if interaction.message and interaction.message.embeds:
            embed = interaction.message.embeds[0]
            self._update_embed(embed)
            await interaction.message.edit(embed=embed, view=self)

        await interaction.response.send_message("You’re marked as pulling up.", ephemeral=True)

    @discord.ui.button(label="Maybe", style=discord.ButtonStyle.secondary, emoji="🤔")
    async def maybe(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        self.pulling_up_ids.discard(user_id)
        self.cant_make_it_ids.discard(user_id)
        self.maybe_ids.add(user_id)

        if interaction.message and interaction.message.embeds:
            embed = interaction.message.embeds[0]
            self._update_embed(embed)
            await interaction.message.edit(embed=embed, view=self)

        await interaction.response.send_message("You’re marked as maybe.", ephemeral=True)

    @discord.ui.button(label="Can't Make It", style=discord.ButtonStyle.danger, emoji="❌")
    async def cant_make_it(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        self.pulling_up_ids.discard(user_id)
        self.maybe_ids.discard(user_id)
        self.cant_make_it_ids.add(user_id)

        if interaction.message and interaction.message.embeds:
            embed = interaction.message.embeds[0]
            self._update_embed(embed)
            await interaction.message.edit(embed=embed, view=self)

        await interaction.response.send_message("You’re marked as not making it.", ephemeral=True)

    @discord.ui.button(label="End Meet", style=discord.ButtonStyle.primary, emoji="🏁")
    async def end_meet_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user if isinstance(interaction.user, discord.Member) else None

        allowed = False
        if member and member.guild_permissions.administrator:
            allowed = True
        elif member and member.id == self.host_user_id:
            allowed = True
        elif member:
            host_role_id = data.get("host_role_id")
            if host_role_id is not None:
                allowed = any(role.id == host_role_id for role in member.roles)

        if not allowed:
            await interaction.response.send_message("Only the host or a server admin can end this meet.", ephemeral=True)
            return

        if interaction.message and interaction.message.embeds:
            embed = interaction.message.embeds[0]
            clean_title = embed.title.replace("🚗 ", "").replace("🏁 ", "").replace(" — CLOSED", "")
            embed.color = 0x808080
            embed.title = f"🏁 {clean_title} — CLOSED"
            embed.set_footer(text=f"Meet ended by {interaction.user.display_name}")

            for child in self.children:
                if isinstance(child, discord.ui.Button) and child.style != discord.ButtonStyle.link:
                    child.disabled = True

            await interaction.message.edit(embed=embed, view=self)

        await interaction.response.send_message("Meet closed.", ephemeral=True)


# =========================
# CREW PANEL
# =========================

_application_data = {}  # user_id -> {"step1": {...}, "step2": {...}}


class CrewAppStep1Modal(discord.ui.Modal, title="DIFF Crew Application — Part 1 of 3"):
    age = discord.ui.TextInput(label="How old are you?", required=True, max_length=3)
    timezone = discord.ui.TextInput(label="What timezone do you live in?", placeholder="e.g. Eastern, Central, Pacific, GMT", required=True, max_length=100)
    gamertag = discord.ui.TextInput(label="PlayStation or PC Gamertag", required=True, max_length=100)
    discord_name = discord.ui.TextInput(label="Discord Name", required=True, max_length=100)
    gta_rank = discord.ui.TextInput(label="What is your GTA Rank?", required=True, max_length=50)

    async def on_submit(self, interaction: discord.Interaction):
        _application_data[interaction.user.id] = {
            "step1": {
                "age": self.age.value,
                "timezone": self.timezone.value,
                "gamertag": self.gamertag.value,
                "discord_name": self.discord_name.value,
                "gta_rank": self.gta_rank.value,
            }
        }
        await interaction.response.send_message(
            "✅ Part 1 saved! Click below to continue.",
            view=CrewAppStep2View(),
            ephemeral=True
        )


class CrewAppStep2View(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="Continue to Part 2", style=discord.ButtonStyle.primary, emoji="▶️")
    async def go_step2(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in _application_data:
            await interaction.response.send_message("Session expired. Please start over by clicking Crew Application again.", ephemeral=True)
            return
        await interaction.response.send_modal(CrewAppStep2Modal())


class CrewAppStep2Modal(discord.ui.Modal, title="DIFF Crew Application — Part 2 of 3"):
    how_heard = discord.ui.TextInput(label="How did you hear about us?", placeholder="Community Advertisement, From a Friend, or Attending a Car Meet", required=True, max_length=200)
    days_available = discord.ui.TextInput(label="Days you are most available", placeholder="e.g. Monday, Wednesday, Friday, Saturday", required=True, max_length=200)
    personal_skills = discord.ui.TextInput(label="Describe your personal skills", style=discord.TextStyle.paragraph, required=True, max_length=500)
    meet_experience = discord.ui.TextInput(label="Previous DIFF meet experience", style=discord.TextStyle.paragraph, required=True, max_length=500)
    former_crews = discord.ui.TextInput(label="Former crew(s) & how long (months)", placeholder="e.g. Midnight Meet Crews - 6 months", style=discord.TextStyle.paragraph, required=True, max_length=300)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id not in _application_data:
            await interaction.response.send_message("Session expired. Please start over by clicking Crew Application again.", ephemeral=True)
            return
        _application_data[interaction.user.id]["step2"] = {
            "how_heard": self.how_heard.value,
            "days_available": self.days_available.value,
            "personal_skills": self.personal_skills.value,
            "meet_experience": self.meet_experience.value,
            "former_crews": self.former_crews.value,
        }
        await interaction.response.send_message(
            "✅ Part 2 saved! Click below to continue.",
            view=CrewAppStep3View(),
            ephemeral=True
        )


class CrewAppStep3View(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="Continue to Part 3", style=discord.ButtonStyle.primary, emoji="▶️")
    async def go_step3(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in _application_data:
            await interaction.response.send_message("Session expired. Please start over by clicking Crew Application again.", ephemeral=True)
            return
        await interaction.response.send_modal(CrewAppStep3Modal())


class CrewAppStep3Modal(discord.ui.Modal, title="DIFF Crew Application — Part 3 of 3"):
    why_join = discord.ui.TextInput(label="Why do you have potential to join DIFF?", style=discord.TextStyle.paragraph, required=True, max_length=500)
    what_bring = discord.ui.TextInput(label="What can you bring to the crew?", placeholder="e.g. Car Photography, Content Creation, Crew Colors", style=discord.TextStyle.paragraph, required=True, max_length=300)
    understand = discord.ui.TextInput(label='Type "I Understand" to confirm', placeholder="I Understand", required=True, max_length=20)
    comments = discord.ui.TextInput(label="Questions, comments, or concerns?", style=discord.TextStyle.paragraph, required=False, max_length=500)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id not in _application_data:
            await interaction.response.send_message("Session expired. Please start over by clicking Crew Application again.", ephemeral=True)
            return
        if self.understand.value.strip().lower() != "i understand":
            await interaction.response.send_message('❌ You must type "I Understand" exactly to submit. Please try again.', ephemeral=True)
            return
        app = _application_data.pop(interaction.user.id)
        s1 = app["step1"]
        s2 = app["step2"]
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("This can only be used inside the server.", ephemeral=True)
            return
        review_channel = guild.get_channel(APPLICATION_REVIEW_CHANNEL_ID)
        tracker_channel = guild.get_channel(APPLICATION_TRACKER_CHANNEL_ID)
        category = guild.get_channel(APPLICATION_TICKET_CATEGORY_ID)
        if not isinstance(review_channel, discord.TextChannel):
            await interaction.response.send_message("❌ Staff review channel not configured. Contact an admin.", ephemeral=True)
            return
        if not isinstance(tracker_channel, discord.TextChannel):
            await interaction.response.send_message("❌ Tracker channel not configured. Contact an admin.", ephemeral=True)
            return
        if not isinstance(category, discord.CategoryChannel):
            await interaction.response.send_message("❌ Ticket category not configured. Contact an admin.", ephemeral=True)
            return
        answers = {
            "age": s1["age"],
            "timezone": s1["timezone"],
            "gamertag": s1["gamertag"],
            "discord_name": s1["discord_name"],
            "gta_rank": s1["gta_rank"],
            "how_heard": s2["how_heard"],
            "days_available": s2["days_available"],
            "personal_skills": s2["personal_skills"],
            "meet_experience": s2["meet_experience"],
            "former_crews": s2["former_crews"],
            "why_join": self.why_join.value,
            "what_bring": self.what_bring.value,
            "comments": self.comments.value or "",
        }
        app_id = create_next_app_id()
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, read_message_history=True),
        }
        for role_id in [LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID]:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        ticket_name = f"garage-{app_id}-{interaction.user.name}".lower().replace(" ", "-")[:95]
        try:
            ticket_channel = await guild.create_text_channel(
                name=ticket_name,
                category=category,
                overwrites=overwrites,
                topic=f"DIFF Garage Ticket for Application #{app_id} | User ID: {interaction.user.id}",
            )
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to create ticket channels. Contact an admin.", ephemeral=True)
            return
        ticket_embed = discord.Embed(
            title=f"Garage Submission Ticket #{app_id}",
            description=(
                f"Welcome {interaction.user.mention}.\n\n"
                f"**Next step:** Upload at least **{MIN_GARAGE_PHOTOS} clear garage/car photos** in this ticket.\n\n"
                f"Applications automatically time out if the required photos are not uploaded within **{GARAGE_TIMEOUT_HOURS} hours**.\n\n"
                "Staff will review:\n"
                "• Your application answers\n"
                "• Your overall garage quality\n"
                "• Build realism / cleanliness\n\n"
                "Once staff finishes reviewing, this ticket will be closed automatically."
            ),
            color=discord.Color.blue(),
            timestamp=utc_now(),
        )
        await ticket_channel.send(content=interaction.user.mention, embed=ticket_embed)
        review_embed = build_review_embed(app_id, interaction.user, answers, ticket_channel.id)
        review_view = ReviewView(app_id=app_id, applicant_id=interaction.user.id)
        review_message = await review_channel.send(embed=review_embed, view=review_view)
        tracker_embed = build_tracker_embed(app_id, interaction.user, answers, "Pending")
        tracker_message = await tracker_channel.send(embed=tracker_embed)
        save_app(app_id, {
            "app_id": app_id,
            "user_id": interaction.user.id,
            "username": str(interaction.user),
            **answers,
            "status": "Pending",
            "submitted_at": utc_now().isoformat(),
            "review_channel_id": review_channel.id,
            "review_message_id": review_message.id,
            "tracker_channel_id": tracker_channel.id,
            "tracker_message_id": tracker_message.id,
            "ticket_channel_id": ticket_channel.id,
            "ticket_channel_name": ticket_channel.name,
            "reviewed_by": None,
            "reviewed_at": None,
            "ticket_closed": False,
        })
        await interaction.response.send_message(
            f"✅ Your application **#{app_id}** has been submitted!\n"
            f"A private garage ticket has been created: {ticket_channel.mention}\n\n"
            "Please upload clear pictures of your cars there. Staff will review your application and garage, then reach out with a decision. Good luck!",
            ephemeral=True,
        )


class CrewPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Crew Requirements", emoji="📋", style=discord.ButtonStyle.primary, custom_id="crew_requirements_btn")
    async def crew_requirements(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📋 DIFF Crew Requirements",
            description=(
                "ALL MEMBERS MUST BE 18+ BEFORE JOINING DIFF\n\n"
                "■ Clean & realistic builds only (no modded/riced cars)\n"
                "■ Must have interest in cars\n"
                "■ Must know Discord & stay active\n"
                "■ Working headset required\n"
                "■ Must rep DIFF at meets\n"
                "■ Attend at least 1 meet per weekend\n\n"
                "If you do not meet these requirements your application will be denied.\n\n"
                "**What DIFF Offers:**\n"
                "■ Weekly crew colors\n"
                "■ Monthly meetings\n"
                "■ Events on other games\n"
                "■ Crew collaborations\n\n"
                "**Crew Positions:**\n"
                "■ Color Team\n"
                "■ Meet Host (30 days required)\n"
                "■ Designer Team\n"
                "■ Content Creators\n"
                "■ Crew Managers"
            ),
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Crew Process", emoji="🔄", style=discord.ButtonStyle.secondary, custom_id="crew_process_btn")
    async def crew_process(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔄 DIFF Crew Process",
            description=(
                "Step 1: Attend 3–5 meets before applying\n"
                "Step 2: Submit your application\n"
                "Step 3: Staff reviews your application\n"
                "Step 4: If selected, you will be contacted for a Discord interview\n"
                "Step 5: Final decision from management\n\n"
                "**IMPORTANT:**\n"
                "■ Interviews are done via Discord VC\n"
                "■ Must be 18+ to apply"
            ),
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Crew Application", emoji="📝", style=discord.ButtonStyle.success, custom_id="crew_application_btn")
    async def crew_application(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CrewAppStep1Modal())


async def send_or_refresh_crew_panel(guild: discord.Guild):
    channel = guild.get_channel(CREW_PANEL_CHANNEL_ID)
    if channel is None:
        return False, "Crew panel channel not found."

    embed = discord.Embed(
        title="🏁 How to Join DIFF",
        description=(
            "Welcome to Different Meets (DIFF) — a structured and community-driven car meet crew focused on realism, quality builds, and consistency.\n\n"
            "We're looking for dedicated members who are passionate about cars, understand proper meet etiquette, and want to be part of an organized and growing community."
        ),
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=DIFF_LOGO_URL)
    embed.set_image(url=DIFF_BANNER_URL)

    crew_panel_msg_id = data.get("crew_panel_message_id")
    target_message = None

    if crew_panel_msg_id:
        try:
            target_message = await channel.fetch_message(crew_panel_msg_id)
        except discord.NotFound:
            target_message = None

    if target_message is None:
        async for msg in channel.history(limit=20):
            if msg.author == guild.me and msg.embeds and msg.embeds[0].title in ("🏁 DIFF Crew Recruitment", "🏁 How to Join DIFF"):
                target_message = msg
                break

    if target_message is not None:
        await target_message.edit(embed=embed, view=CrewPanelView())
    else:
        target_message = await channel.send(embed=embed, view=CrewPanelView())

    data["crew_panel_message_id"] = target_message.id
    save_data(data)
    return True, channel.mention


# =========================
# EVENTS
# =========================
@bot.event
async def on_ready():
    global status_message_id

    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"Sync error: {e}")

    try:
        bot.add_view(RulesAcceptView(GUILD_ID))
        bot.add_view(CrewPanelView())
        bot.add_view(ReviewView(app_id="0000", applicant_id=0))
        bot.add_view(DeniedResultView(app_id="0000", applicant_id=0))
        bot.add_view(RespondButtonView())
    except Exception as e:
        print(f"View registration warning: {e}")

    bot.loop.create_task(application_timeout_loop())

    status_message_id = data.get("panel_message_id")


# =========================
# APPLICATION TIMEOUT LOOP
# =========================
async def application_timeout_loop():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            app_data = load_apps()
            for app_id, record in app_data.get("applications", {}).items():
                if record.get("status") not in {"Pending", "More Info Requested"}:
                    continue
                submitted_at = record.get("submitted_at")
                if not submitted_at:
                    continue
                try:
                    submitted_dt = datetime.fromisoformat(submitted_at)
                except Exception:
                    continue
                if utc_now() - submitted_dt < timedelta(hours=GARAGE_TIMEOUT_HOURS):
                    continue
                guild = bot.get_guild(GUILD_ID)
                if not guild:
                    continue
                ticket_channel = guild.get_channel(record.get("ticket_channel_id")) if record.get("ticket_channel_id") else None
                photo_count = 0
                if isinstance(ticket_channel, discord.TextChannel):
                    messages = [m async for m in ticket_channel.history(limit=200)]
                    photo_count = count_message_attachments(messages)
                if photo_count >= MIN_GARAGE_PHOTOS:
                    continue
                update_app(
                    app_id,
                    status="Timed Out",
                    reviewed_at=utc_now().isoformat(),
                    decision_reason=f"Timed out before uploading the required {MIN_GARAGE_PHOTOS} garage photos.",
                    ticket_closed=True,
                    closed_at=utc_now().isoformat(),
                )
                applicant = guild.get_member(record["user_id"])
                if applicant:
                    await safe_dm(
                        applicant,
                        f"Your DIFF application **#{app_id}** timed out because the required **{MIN_GARAGE_PHOTOS}** garage photos "
                        f"were not uploaded within **{GARAGE_TIMEOUT_HOURS} hours**.",
                    )
                tracker_channel = guild.get_channel(APPLICATION_TRACKER_CHANNEL_ID)
                if isinstance(tracker_channel, discord.TextChannel) and record.get("tracker_message_id"):
                    try:
                        tracker_msg = await tracker_channel.fetch_message(record["tracker_message_id"])
                        tracker_embed = build_tracker_embed(
                            app_id,
                            applicant or guild.me,
                            record,
                            "Timed Out",
                            "System Auto Timeout",
                        )
                        await tracker_msg.edit(embed=tracker_embed)
                    except Exception:
                        pass
                if isinstance(ticket_channel, discord.TextChannel):
                    try:
                        await ticket_channel.send(embed=discord.Embed(
                            title="Application Timed Out",
                            description=(
                                f"This application timed out because at least **{MIN_GARAGE_PHOTOS}** garage photos "
                                f"were not uploaded within **{GARAGE_TIMEOUT_HOURS} hours**."
                            ),
                            color=discord.Color.dark_orange(),
                            timestamp=utc_now(),
                        ))
                    except Exception:
                        pass
                    try:
                        await ticket_channel.edit(name=f"closed-{ticket_channel.name[:80]}")
                    except Exception:
                        pass
                    try:
                        await ticket_channel.set_permissions(guild.default_role, view_channel=False)
                    except Exception:
                        pass
                    if applicant:
                        try:
                            await ticket_channel.set_permissions(applicant, overwrite=None)
                        except Exception:
                            pass
        except Exception:
            pass
        await asyncio.sleep(600)


# =========================
_panel_refresh_task = None
_hierarchy_refresh_task = None


async def _auto_refresh_status_panel(guild: discord.Guild):
    await asyncio.sleep(15)
    channel_id = data.get("status_channel_id")
    if not channel_id:
        return
    channel = guild.get_channel(channel_id)
    if channel is None:
        return
    embed = build_status_embed(guild)
    msg_id = data.get("panel_message_id")
    target_message = None
    if msg_id:
        try:
            target_message = await channel.fetch_message(msg_id)
        except discord.NotFound:
            target_message = None
    if target_message is None:
        target_message = await find_existing_status_panel_message(channel)
    if target_message is not None:
        try:
            await target_message.edit(embed=embed)
        except Exception:
            pass


@bot.event
async def on_presence_update(before: discord.Member, after: discord.Member):
    global _panel_refresh_task, _hierarchy_refresh_task
    if after.guild.id != GUILD_ID:
        return
    if before.status == after.status and before.activity == after.activity:
        return
    if _panel_refresh_task is not None and not _panel_refresh_task.done():
        _panel_refresh_task.cancel()
    _panel_refresh_task = asyncio.ensure_future(_auto_refresh_status_panel(after.guild))
    if _hierarchy_refresh_task is not None and not _hierarchy_refresh_task.done():
        _hierarchy_refresh_task.cancel()
    _hierarchy_refresh_task = asyncio.ensure_future(_auto_refresh_hierarchy_panel(after.guild))


# =========================
# START MEET MODAL
# =========================
class StartMeetModal(discord.ui.Modal, title="Start a DIFF Meet"):
    meet_title = discord.ui.TextInput(label="Meet Title", placeholder="Different Meets Saturday Night", max_length=100)
    theme = discord.ui.TextInput(label="Theme / Meet Type", placeholder="Clean JDM / Drift / Muscle / Show Meet", max_length=100)
    location = discord.ui.TextInput(label="Location", placeholder="LS Car Meet / Airport / Vinewood", max_length=100)
    meet_time = discord.ui.TextInput(label="Time", placeholder="8:30 PM EST", max_length=50)
    details = discord.ui.TextInput(
        label="Restrictions / Weather / Notes",
        style=discord.TextStyle.paragraph,
        placeholder="JDM only | Clear skies | Add hosts and send garage clip | No burnouts",
        required=False,
        max_length=400,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if interaction.guild is None:
            await interaction.followup.send("Use this in the server.", ephemeral=True)
            return

        channel = await bot.fetch_channel(MEET_ANNOUNCEMENT_CHANNEL_ID)

        ping_role_id = data.get("meet_ping_role_id")
        role_mention = f"<@&{ping_role_id}>" if ping_role_id else None

        embed = discord.Embed(
            title=f"🚗 {self.meet_title.value}",
            description=(
                f"**Theme / Type:** {self.theme.value}\n"
                f"**Location:** {self.location.value}\n"
                f"**Time:** {self.meet_time.value}\n\n"
                f"{self.details.value or 'Pull up clean and follow the rules.'}\n\n"
                f"📍 Check <#{MEET_RULES_CHANNEL_ID}> before joining\n"
                f"📥 Join steps: <#{JOIN_MEETS_CHANNEL_ID}>\n"
                f"📅 Meet updates: <#{UPCOMING_MEET_CHANNEL_ID}>"
            ),
            color=0xC9A227,
        )
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.set_image(url=DIFF_BANNER_URL)
        embed.set_footer(text=f"Hosted by {interaction.user.display_name}")
        embed.add_field(
            name="📊 RSVP Tracker",
            value=(
                "✅ Pulling Up: **0**\n"
                "🤔 Maybe: **0**\n"
                "❌ Can't Make It: **0**\n\n"
                "**Pulling Up:** None\n"
                "**Maybe:** None\n"
                "**Can't Make It:** None"
            ),
            inline=False,
        )

        view = RSVPView(host_user_id=interaction.user.id)
        view.add_item(discord.ui.Button(label="Meet Rules", style=discord.ButtonStyle.link, emoji="📜", url=build_channel_link(interaction.guild.id, MEET_RULES_CHANNEL_ID)))
        view.add_item(discord.ui.Button(label="Join Meets", style=discord.ButtonStyle.link, emoji="📥", url=build_channel_link(interaction.guild.id, JOIN_MEETS_CHANNEL_ID)))
        view.add_item(discord.ui.Button(label="Upcoming Meet", style=discord.ButtonStyle.link, emoji="📅", url=build_channel_link(interaction.guild.id, UPCOMING_MEET_CHANNEL_ID)))
        view.add_item(discord.ui.Button(label="Hosts", style=discord.ButtonStyle.link, emoji="👥", url=build_channel_link(interaction.guild.id, DIFF_HOSTS_CHANNEL_ID)))

        await channel.send(content=role_mention if role_mention else None, embed=embed, view=view)
        await interaction.followup.send(f"✅ Meet posted in <#{MEET_ANNOUNCEMENT_CHANNEL_ID}>", ephemeral=True)


# =========================
# SLASH COMMANDS
# =========================
@bot.tree.command(name="ping", description="Check if the bot is online")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong 🏓")


@bot.tree.command(name="panel", description="Show the DIFF host panel")
async def panel(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message("Use this command in the server.", ephemeral=True)
        return
    embed = build_status_embed(interaction.guild)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="postpanel", description="Post or refresh the saved live panel")
@app_commands.checks.has_permissions(administrator=True)
async def postpanel(interaction: discord.Interaction):
    global status_message_id

    if interaction.guild is None:
        await interaction.response.send_message("Use this command in the server.", ephemeral=True)
        return

    channel_id = data.get("status_channel_id")
    channel = interaction.guild.get_channel(channel_id)
    if channel is None:
        await interaction.response.send_message("Status channel not found.", ephemeral=True)
        return

    embed = build_status_embed(interaction.guild)
    target_message = None

    if status_message_id:
        try:
            target_message = await channel.fetch_message(status_message_id)
        except discord.NotFound:
            target_message = None

    if target_message is None:
        target_message = await find_existing_status_panel_message(channel)

    if target_message is None:
        target_message = await channel.send(embed=embed)
    else:
        await target_message.edit(embed=embed)

    data["panel_message_id"] = target_message.id
    save_data(data)
    status_message_id = target_message.id
    await cleanup_extra_status_panel_messages(channel, target_message.id)
    await interaction.response.send_message(f"Panel saved in {channel.mention}.", ephemeral=True)


@bot.tree.command(name="listhosts", description="Show all saved DIFF hosts")
async def listhosts(interaction: discord.Interaction):
    if not data["hosts"]:
        await interaction.response.send_message("No hosts saved.", ephemeral=True)
        return

    lines = [f"{i}. **{host['name']}**" for i, host in enumerate(data["hosts"], start=1)]
    embed = discord.Embed(title="📋 DIFF Saved Hosts", description="\n".join(lines), color=0xC9A227)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="refreshpanel", description="Refresh the saved live panel")
@app_commands.checks.has_permissions(administrator=True)
async def refreshpanel(interaction: discord.Interaction):
    global status_message_id

    if interaction.guild is None:
        await interaction.response.send_message("Use this command in the server.", ephemeral=True)
        return

    channel_id = data.get("status_channel_id")
    channel = interaction.guild.get_channel(channel_id)
    if channel is None:
        await interaction.response.send_message("Status channel not found.", ephemeral=True)
        return

    embed = build_status_embed(interaction.guild)
    target_message = None

    if status_message_id:
        try:
            target_message = await channel.fetch_message(status_message_id)
        except discord.NotFound:
            target_message = None

    if target_message is None:
        target_message = await find_existing_status_panel_message(channel)

    if target_message is None:
        target_message = await channel.send(embed=embed)
    else:
        await target_message.edit(embed=embed)

    data["panel_message_id"] = target_message.id
    save_data(data)
    status_message_id = target_message.id
    await cleanup_extra_status_panel_messages(channel, target_message.id)
    await interaction.response.send_message(f"Panel refreshed in {channel.mention}.", ephemeral=True)


@refreshpanel.error
@postpanel.error
async def panel_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.MissingPermissions):
        msg = "You need administrator permissions to use that command."
    else:
        msg = f"Command error: {error}"

    if interaction.response.is_done():
        await interaction.followup.send(msg, ephemeral=True)
    else:
        await interaction.response.send_message(msg, ephemeral=True)


@bot.tree.command(name="addhost", description="Add a DIFF host")
@app_commands.checks.has_permissions(administrator=True)
async def addhost(interaction: discord.Interaction, member: discord.Member, profile_url: str):
    for host in data["hosts"]:
        if host["discord_id"] == member.id:
            await interaction.response.send_message("That host is already in the list.", ephemeral=True)
            return

    data["hosts"].append({"discord_id": member.id, "name": member.display_name, "profile_url": profile_url})
    save_data(data)
    await interaction.response.send_message(f"Added **{member.display_name}** to the DIFF host list.", ephemeral=True)


@bot.tree.command(name="removehost", description="Remove a DIFF host")
@app_commands.checks.has_permissions(administrator=True)
async def removehost(interaction: discord.Interaction, member: discord.Member):
    before = len(data["hosts"])
    data["hosts"] = [host for host in data["hosts"] if host["discord_id"] != member.id]
    save_data(data)

    if len(data["hosts"]) == before:
        await interaction.response.send_message("That host was not found.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Removed **{member.display_name}** from the DIFF host list.", ephemeral=True)


@bot.tree.command(name="sendmeetinfo", description="Post or update the DIFF meet info panel")
@app_commands.checks.has_permissions(administrator=True)
async def sendmeetinfo(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message("Use this in the server.", ephemeral=True)
        return

    channel = interaction.guild.get_channel(MEET_INFO_CHANNEL_ID)
    if channel is None:
        await interaction.response.send_message("Meet info channel not found.", ephemeral=True)
        return

    embed = build_meet_info_embed()
    view = build_meet_info_view(interaction.guild.id)
    meet_info_message_id = data.get("meet_info_message_id")

    try:
        if meet_info_message_id:
            try:
                message = await channel.fetch_message(meet_info_message_id)
                await message.edit(embed=embed, view=view)
                await interaction.response.send_message(f"Meet info panel updated in {channel.mention}.", ephemeral=True)
                return
            except discord.NotFound:
                data["meet_info_message_id"] = None
                save_data(data)

        new_message = await channel.send(embed=embed, view=view)
        data["meet_info_message_id"] = new_message.id
        save_data(data)
        await interaction.response.send_message(f"Meet info panel posted in {channel.mention}.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error posting meet info panel: {e}", ephemeral=True)


@sendmeetinfo.error
async def sendmeetinfo_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.MissingPermissions):
        msg = "You need administrator permissions to use that command."
    else:
        msg = f"Command error: {error}"

    if interaction.response.is_done():
        await interaction.followup.send(msg, ephemeral=True)
    else:
        await interaction.response.send_message(msg, ephemeral=True)


@bot.tree.command(name="refreshrules", description="Post or refresh all rules panels in the rules channel")
@app_commands.checks.has_permissions(administrator=True)
async def refreshrules(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message("Use this in the server.", ephemeral=True)
        return

    channel = interaction.guild.get_channel(RULES_CHANNEL_ID)
    if channel is None:
        await interaction.response.send_message("Rules channel not found.", ephemeral=True)
        return

    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return

    panels = [
        (get_rules_embed(), None),
        (get_discord_rules_embed(), None),
        (get_bannable_offenses_embed(), RulesAcceptView(interaction.guild.id)),
    ]

    saved_ids = data.get("rules_message_ids", [])
    saved_messages = []
    if len(saved_ids) == len(panels):
        for msg_id in saved_ids:
            try:
                msg = await channel.fetch_message(msg_id)
                saved_messages.append(msg)
            except discord.NotFound:
                saved_messages = []
                break

    if len(saved_messages) == len(panels):
        for msg, (embed, view) in zip(saved_messages, panels):
            await msg.edit(embed=embed, view=view or discord.ui.View())
    else:
        for msg in saved_messages:
            try:
                await msg.delete()
            except Exception:
                pass
        saved_messages = []
        for embed, view in panels:
            msg = await channel.send(embed=embed, view=view or discord.ui.View())
            saved_messages.append(msg)
        data["rules_message_ids"] = [msg.id for msg in saved_messages]
        save_data(data)

    try:
        await interaction.followup.send(f"Rules panels refreshed in {channel.mention}.", ephemeral=True)
    except discord.NotFound:
        pass


@refreshrules.error
async def refreshrules_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.MissingPermissions):
        msg = "You need administrator permissions to use that command."
    else:
        msg = f"Command error: {error}"
    try:
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
    except discord.NotFound:
        pass


@bot.tree.command(name="refreshcrewpanel", description="Post or refresh the crew recruitment panel")
@app_commands.checks.has_permissions(administrator=True)
async def refreshcrewpanel(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message("Use this in the server.", ephemeral=True)
        return
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return
    ok, result = await send_or_refresh_crew_panel(interaction.guild)
    try:
        if ok:
            await interaction.followup.send(f"Crew panel refreshed in {result}.", ephemeral=True)
        else:
            await interaction.followup.send(result, ephemeral=True)
    except discord.NotFound:
        pass


@refreshcrewpanel.error
async def refreshcrewpanel_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.MissingPermissions):
        msg = "You need administrator permissions to use that command."
    else:
        msg = f"Command error: {error}"
    try:
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
    except discord.NotFound:
        pass


@bot.tree.command(name="sethostrole", description="Set the DIFF host role")
@app_commands.checks.has_permissions(administrator=True)
async def sethostrole(interaction: discord.Interaction, role: discord.Role):
    data["host_role_id"] = role.id
    save_data(data)
    await interaction.response.send_message(f"Host role set to {role.mention}", ephemeral=True)


@sethostrole.error
async def sethostrole_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.MissingPermissions):
        msg = "You need administrator permissions to use that command."
    else:
        msg = f"Command error: {error}"

    if interaction.response.is_done():
        await interaction.followup.send(msg, ephemeral=True)
    else:
        await interaction.response.send_message(msg, ephemeral=True)


@bot.tree.command(name="setmeetpingrole", description="Set the role to ping for meet announcements")
@app_commands.checks.has_permissions(administrator=True)
async def setmeetpingrole(interaction: discord.Interaction, role: discord.Role):
    data["meet_ping_role_id"] = role.id
    save_data(data)
    await interaction.response.send_message(f"Meet ping role set to {role.mention}", ephemeral=True)


@setmeetpingrole.error
async def setmeetpingrole_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.MissingPermissions):
        msg = "You need administrator permissions to use that command."
    else:
        msg = f"Command error: {error}"

    if interaction.response.is_done():
        await interaction.followup.send(msg, ephemeral=True)
    else:
        await interaction.response.send_message(msg, ephemeral=True)


@bot.tree.command(name="startmeet", description="Open the meet announcement form")
async def startmeet(interaction: discord.Interaction):
    if not is_host_or_admin(interaction):
        await interaction.response.send_message("You need the Host role or admin permissions to use this command.", ephemeral=True)
        return
    if interaction.guild is None:
        await interaction.response.send_message("Use this in the server.", ephemeral=True)
        return
    await interaction.response.send_modal(StartMeetModal())


@bot.tree.command(name="endmeet", description="Post a meet closed message")
async def endmeet(
    interaction: discord.Interaction,
    message: str = "I Appreciate everyone for pulling up tonight. Meet is officially closed. Safe travels and see y’all at the next one. 💯",
):
    if not is_host_or_admin(interaction):
        await interaction.response.send_message("You need the Host role or admin permissions to use this command.", ephemeral=True)
        return

    embed = discord.Embed(title="🏁 Meet Closed", description=message, color=0xC9A227)
    embed.set_thumbnail(url=DIFF_LOGO_URL)
    embed.set_footer(text=f"Closed by {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="hostpanel", description="Show current bot host role setup")
async def hostpanel(interaction: discord.Interaction):
    host_role_id = data.get("host_role_id")
    role_text = f"<@&{host_role_id}>" if host_role_id else "Not set"

    ping_role_id = data.get("meet_ping_role_id")
    ping_role_text = f"<@&{ping_role_id}>" if ping_role_id else "Not set"

    embed = discord.Embed(
        title="🎛️ DIFF Host Setup",
        description=(
            f"**Host Role:** {role_text}\n"
            f"**Meet Ping Role:** {ping_role_text}\n"
            f"**Meet Announcement Channel:** <#{MEET_ANNOUNCEMENT_CHANNEL_ID}>"
        ),
        color=0xC9A227,
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="meethistory", description="Show the latest messages in the extra-meets channel")
@app_commands.checks.has_permissions(administrator=True)
async def meethistory(interaction: discord.Interaction, amount: app_commands.Range[int, 1, 10] = 5):
    if interaction.guild is None:
        await interaction.response.send_message("Use this in the server.", ephemeral=True)
        return

    channel = interaction.guild.get_channel(MEET_ANNOUNCEMENT_CHANNEL_ID)
    if channel is None:
        await interaction.response.send_message("extra-meets channel not found.", ephemeral=True)
        return

    lines = []
    async for msg in channel.history(limit=amount):
        if msg.author == bot.user:
            lines.append(f"• {msg.created_at.strftime('%Y-%m-%d %H:%M UTC')} — [Jump]({msg.jump_url})")

    if not lines:
        await interaction.response.send_message("No recent bot meet posts found.", ephemeral=True)
        return

    embed = discord.Embed(title="📜 Recent Meet Posts", description="\n".join(lines), color=0xC9A227)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@meethistory.error
async def meethistory_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.MissingPermissions):
        msg = "You need administrator permissions to use that command."
    else:
        msg = f"Command error: {error}"

    if interaction.response.is_done():
        await interaction.followup.send(msg, ephemeral=True)
    else:
        await interaction.response.send_message(msg, ephemeral=True)






@bot.tree.command(name="warn", description="Warn a member and log it")
@app_commands.checks.has_permissions(administrator=True)
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    if interaction.guild is None:
        await interaction.response.send_message("Use this in the server.", ephemeral=True)
        return

    if member.bot:
        await interaction.response.send_message("You can't warn bots.", ephemeral=True)
        return

    add_warning(member.id, interaction.user.id, reason)
    total_warnings = get_warning_count(member.id)

    embed = discord.Embed(
        title="⚠️ Member Warned",
        description=(
            f"**Member:** {member.mention}\n"
            f"**Reason:** {reason}\n"
            f"**Warned By:** {interaction.user.mention}\n"
            f"**Total Warnings:** {total_warnings}"
        ),
        color=discord.Color.orange(),
    )
    embed.set_thumbnail(url=DIFF_LOGO_URL)
    embed.set_footer(text="DIFF Warning System")

    await interaction.response.send_message(embed=embed)

    try:
        dm_embed = discord.Embed(
            title="⚠️ You received a warning in DIFF Meets",
            description=(
                f"**Reason:** {reason}\n"
                f"**Total Warnings:** {total_warnings}\n\n"
                "Please correct the behavior to avoid stronger punishment."
            ),
            color=discord.Color.orange(),
        )
        dm_embed.set_thumbnail(url=DIFF_LOGO_URL)
        await member.send(embed=dm_embed)
    except discord.Forbidden:
        pass


@bot.tree.command(name="warnings", description="Check a member's warnings")
@app_commands.checks.has_permissions(administrator=True)
async def warnings(interaction: discord.Interaction, member: discord.Member):
    member_warnings = data.get("warnings", {}).get(str(member.id), [])

    if not member_warnings:
        await interaction.response.send_message(f"{member.mention} has no warnings.", ephemeral=True)
        return

    lines = []
    for index, entry in enumerate(member_warnings[-10:], start=1):
        lines.append(
            f"**{index}.** {entry['reason']}\n"
            f"→ By <@{entry['moderator_id']}> on {entry['timestamp']}"
        )

    embed = discord.Embed(
        title=f"⚠️ Warning History • {member.display_name}",
        description="\n\n".join(lines),
        color=discord.Color.orange(),
    )
    embed.set_thumbnail(url=DIFF_LOGO_URL)
    embed.set_footer(text=f"Total warnings: {len(member_warnings)}")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="clearwarnings", description="Clear all warnings for a member")
@app_commands.checks.has_permissions(administrator=True)
async def clearwarnings(interaction: discord.Interaction, member: discord.Member):
    clear_warnings_for_member(member.id)

    embed = discord.Embed(
        title="✅ Warnings Cleared",
        description=f"All warnings for {member.mention} have been cleared.",
        color=discord.Color.green(),
    )
    embed.set_thumbnail(url=DIFF_LOGO_URL)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@clearwarnings.error
@warnings.error
@warn.error
async def moderation_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.MissingPermissions):
        msg = "You need administrator permissions to use that command."
    else:
        msg = f"Command error: {error}"

    if interaction.response.is_done():
        await interaction.followup.send(msg, ephemeral=True)
    else:
        await interaction.response.send_message(msg, ephemeral=True)





@bot.tree.command(name="posthierarchy", description="Post or refresh the DIFF hierarchy panel")
@app_commands.checks.has_permissions(administrator=True)
async def posthierarchy(interaction: discord.Interaction):
    if interaction.guild is None:
        try:
            await interaction.response.send_message("Use this in the server.", ephemeral=True)
        except discord.NotFound:
            pass
        return

    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return

    ok, result = await post_or_refresh_hierarchy_panel(interaction.guild)
    try:
        if ok:
            await interaction.followup.send(f"Hierarchy panel posted or refreshed in {result}.", ephemeral=True)
        else:
            await interaction.followup.send(result, ephemeral=True)
    except discord.NotFound:
        pass


@bot.tree.command(name="refreshhierarchy", description="Refresh the DIFF hierarchy panel")
@app_commands.checks.has_permissions(administrator=True)
async def refreshhierarchy(interaction: discord.Interaction):
    if interaction.guild is None:
        try:
            await interaction.response.send_message("Use this in the server.", ephemeral=True)
        except discord.NotFound:
            pass
        return

    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return

    ok, result = await post_or_refresh_hierarchy_panel(interaction.guild)
    try:
        if ok:
            await interaction.followup.send(f"Hierarchy panel refreshed in {result}.", ephemeral=True)
        else:
            await interaction.followup.send(result, ephemeral=True)
    except discord.NotFound:
        pass


@posthierarchy.error
@refreshhierarchy.error
async def hierarchy_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.MissingPermissions):
        msg = "You need administrator permissions to use that command."
    else:
        msg = f"Command error: {error}"

    try:
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
    except discord.NotFound:
        pass

# =========================
# APPLICATION COMMANDS
# =========================
@bot.tree.command(name="application_lookup", description="Look up a DIFF application by ID (staff only)")
@app_commands.describe(application_id="Application ID, e.g. 0001")
async def application_lookup(interaction: discord.Interaction, application_id: str):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Only Leader, Co-Leader, or Manager can use this command.", ephemeral=True)
    record = get_app(application_id)
    if not record:
        return await interaction.response.send_message(f"No application found with ID #{application_id}.", ephemeral=True)
    embed = discord.Embed(title=f"Application Lookup #{application_id}", color=discord.Color.blurple(), timestamp=utc_now())
    embed.add_field(name="Username", value=record.get("username", "N/A"), inline=True)
    embed.add_field(name="User ID", value=str(record.get("user_id", "N/A")), inline=True)
    embed.add_field(name="Status", value=make_status_emoji(record.get("status", "N/A")), inline=True)
    embed.add_field(name="Gamertag", value=record.get("gamertag", "N/A"), inline=True)
    embed.add_field(name="Age", value=record.get("age", "N/A"), inline=True)
    embed.add_field(name="Reviewed By", value=record.get("reviewed_by") or "Not reviewed", inline=True)
    embed.add_field(name="Ticket Channel", value=f"<#{record['ticket_channel_id']}>" if record.get("ticket_channel_id") else "N/A", inline=False)
    embed.add_field(name="Submitted", value=record.get("submitted_at", "N/A"), inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="application_stats", description="View DIFF application totals (staff only)")
async def application_stats(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Only Leader, Co-Leader, or Manager can use this command.", ephemeral=True)
    app_data = load_apps()
    apps = list(app_data.get("applications", {}).values())
    pending = sum(1 for a in apps if a.get("status") == "Pending")
    approved = sum(1 for a in apps if a.get("status") == "Approved")
    denied = sum(1 for a in apps if a.get("status") == "Denied")
    embed = discord.Embed(title="DIFF Application Stats", color=discord.Color.blue(), timestamp=utc_now())
    embed.add_field(name="Total", value=str(len(apps)), inline=True)
    embed.add_field(name="🟡 Pending", value=str(pending), inline=True)
    embed.add_field(name="🟢 Approved", value=str(approved), inline=True)
    embed.add_field(name="🔴 Denied", value=str(denied), inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="staffreplypanel", description="Post a staff response panel in the current channel (staff only)")
async def staffreplypanel(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Only Leader, Co-Leader, or Manager can use this command.", ephemeral=True)
    embed = discord.Embed(
        title="📩 DIFF Staff Response System",
        description=(
            "Click **Respond** below to auto-detect the ticket user and choose a pre-written reply.\n"
            "The reply will be sent to their DMs and posted in this channel."
        ),
        color=discord.Color.blue(),
    )
    await interaction.channel.send(embed=embed, view=RespondButtonView())
    await interaction.response.send_message("✅ Staff reply panel posted.", ephemeral=True)


# =========================
# START BOT
# =========================
if not TOKEN:
    raise ValueError("TOKEN not found.")

keep_alive()

async def run_bot():
    delay = 60
    try:
        await bot.start(TOKEN)
    except discord.errors.HTTPException as e:
        if e.status == 429:
            print(f"[Rate limited by Discord] Waiting {delay}s before retrying...")
        else:
            print(f"[HTTP error] {e} — retrying in {delay}s")
    except Exception as e:
        print(f"[Connection error] {e} — retrying in {delay}s")
    finally:
        try:
            if not bot.is_closed():
                await bot.close()
        except Exception:
            pass

asyncio.run(run_bot())

print(f"[Restarting process in 60s...]")
import time
time.sleep(60)
os.execv(sys.executable, [sys.executable] + sys.argv)
