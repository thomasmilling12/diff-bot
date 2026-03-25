
import asyncio
import hashlib
import io
import json
import os
import random
import re
import sqlite3
import sys
import traceback
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional, Set
from zoneinfo import ZoneInfo
import subprocess
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import commands, tasks

try:
    import aiohttp
except Exception:
    aiohttp = None

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

# =========================
# KEEP ALIVE FOR REPLIT
# =========================
def keep_alive():
    subprocess.Popen(
        ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "120", "web:app"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


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
MEET_RULES_CHANNEL_ID = 1047161846257438743
UPCOMING_MEET_CHANNEL_ID = 1485861257708834836
JOIN_MEETS_CHANNEL_ID = 1277084633858576406
SUPPORT_TICKETS_CHANNEL_ID = 1156363575150002226

MEET_ANNOUNCEMENT_CHANNEL_ID = 1484768466023223418
RULES_CHANNEL_ID = 1047161846257438743

RULES_BTN_UPCOMING_MEETS_ID = 1485861257708834836
RULES_BTN_JOIN_MEETS_ID = 1277084633858576406
RULES_BTN_MEET_RULES_ID = 1047161846257438743
RULES_BTN_SUPPORT_ID = 1156363575150002226

VERIFIED_ROLE_ID   = 1141424243616256032
UNVERIFIED_ROLE_ID = 1486011550916411512

HIERARCHY_CHANNEL_ID = 1195941548240687266

LEADER_ROLE_ID = 850391095845584937
CO_LEADER_ROLE_ID = 850391378559238235
MANAGER_ROLE_ID = 990011447193006101
HOST_ROLE_ID = 1055823929358430248
DESIGNER_TEAM_ROLE_ID = 1128901233160245278
CONTENT_TEAM_ROLE_ID = 1110037666147336293
COLOR_TEAM_ROLE_ID = 1115495008670330902
CREW_MEMBER_ROLE_ID = 886702076552441927
PS5_ROLE_ID = 1485668852921798849
NOTIFY_ROLE_ID = 1138691141009674260
JOIN_WELCOME_CHANNEL_ID = 1047335231826436166
_JOIN_UNLOCK_CHANNEL_IDS: tuple[int, ...] = (
    1485861257708834836,
    1047178360431841362,
    1484768466023223418,
)

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
STAFF_DASHBOARD_CHANNEL_ID = 1485273802391814224
CREW_CANDIDATE_ROLE_ID = 1485826950646988821
ACTIVE_ROLE_ID = 1485826613206847650
ELITE_ROLE_ID = 1485826784132857958
STRIKE_1_ROLE_ID = 990105742663106570
STRIKE_2_ROLE_ID = 990105837223698443
STRIKE_3_ROLE_ID = 990106011664793600
WARNING_1_ROLE_ID = 1266950150123950091
RECAP_CHANNEL_ID = 1485829235258953928
SEASON_CHANNEL_ID = 0
HOST_RSVP_CHANNEL_ID = 1485830232270307410
HOST_HUB_CHANNEL_ID = 1485840926612918383
HOST_PERFORMANCE_CHANNEL_ID = 1134690348220825730
MEET_FLOW_CHANNEL_ID = 1485684577073758378
BLACKLIST_CHANNEL_ID = 1057016810261712938
IG_CONTENT_CHANNEL_ID = 1485830678980333568
TOP1_ROLE_ID = 1485828728683757669
TOP2_ROLE_ID = 1485828776838303955
TOP3_ROLE_ID = 1485828874943074434
SEASON_FILE = os.path.join("diff_data", "diff_seasons.json")
FINAL_TIER_FILE = os.path.join("diff_data", "diff_final_tier.json")
PHOTO_HASHES_FILE = os.path.join("diff_data", "diff_photo_hashes.json")
CREW_PINGED_FILE = os.path.join("diff_data", "diff_crew_pinged.json")
MEMBER_DATABASE_CHANNEL_ID = 1485274945473871903
REAPPLY_COOLDOWN_DAYS = 14
DATA_FOLDER = "diff_data"
COOLDOWN_FILE = os.path.join(DATA_FOLDER, "diff_reapply_cooldowns.json")
MEMBER_DB_FILE = os.path.join(DATA_FOLDER, "diff_member_database.json")
STAFF_LOGS_CHANNEL_ID = 1485265848099799163
MEET_ATTENDANCE_CHANNEL_ID = 1089579004517953546
LEADERBOARD_CHANNEL_ID = 1485282044392243290
ACTIVITY_FILE = os.path.join(DATA_FOLDER, "diff_activity_stats.json")
REPUTATION_FILE = os.path.join(DATA_FOLDER, "diff_reputation_stats.json")
MEETS_FILE = os.path.join(DATA_FOLDER, "diff_meet_records.json")
HOST_PROMOTION_ATTENDED = 6
HOST_PROMOTION_HOSTED = 2
HOST_PROMOTION_REPUTATION = 15
MANAGER_PROMOTION_ATTENDED = 14
MANAGER_PROMOTION_HOSTED = 5
MANAGER_PROMOTION_REPUTATION = 35
LEADER_PROMOTION_ATTENDED = 28
LEADER_PROMOTION_HOSTED = 10
LEADER_PROMOTION_REPUTATION = 65
MEET_ATTENDER_ROLE_ID = 850392317751066705
MEET_ATTENDANCE_REP = 2
ROLL_CALL_CHANNEL_ID = 1047338695352664165
_OFFICIAL_MEET_CHANNEL_ID = 1485870611069796374
_OFFICIAL_MEET_TZ = "America/New_York"
SUPPORT_CHANNEL_ID = 1156363575150002226
ACTIVITY_MEETS_FILE = os.path.join(DATA_FOLDER, "diff_activity_meets.json")
DIFF_PANEL_CHANNEL_ID = 1103086800458760262
DIFF_PANEL_STATE_FILE = os.path.join(DATA_FOLDER, "diff_panel_state.json")
INTERVIEW_PANEL_CHANNEL_ID = 1103849042296963112
INTERVIEW_PANEL_FILE = os.path.join(DATA_FOLDER, "diff_interview_panel.json")
INTERVIEW_OUTCOME_FILE = os.path.join(DATA_FOLDER, "diff_interview_outcome_panel.json")
TICKET_APP_BRIDGE_FILE = os.path.join(DATA_FOLDER, "diff_ticket_app_bridge.json")
COLOR_OPS_STATE_FILE = os.path.join(DATA_FOLDER, "diff_color_ops_state.json")
INTERVIEW_OUTCOME_LOG_CHANNEL_ID = STAFF_LOGS_CHANNEL_ID
INTERVIEW_OUTCOME_ALLOWED_ROLES = {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID}
INTERVIEW_OUTCOME_ONBOARDING_CHANNEL_ID = INTERVIEW_PANEL_CHANNEL_ID
INTERVIEW_OUTCOME_AUTO_CLOSE = True
INTERVIEW_OUTCOME_CLOSE_DELAY = 10
FUS_DM_ON_INTERVIEW = True
FUS_DM_ON_APPROVAL = True
FUS_DM_ON_DENIAL = True
FUS_AUTO_CLOSE_ENABLED = False
FUS_AUTO_CLOSE_DELAY_SECONDS = 30
FUS_TICKET_KEYWORDS = ("ticket", "application", "app", "apply")

DIFF_LOGO = "https://media.discordapp.net/attachments/1107375326625005719/1484949205331083375/content.png"
DIFF_BANNER = "https://media.discordapp.net/attachments/1107375326625005719/1484949205331083375/content.png"
LEADER_JACKET = "https://media.discordapp.net/attachments/1124435756774084659/1339471600092975126/IMG_1521.jpg"
CREW_JACKETS = [
    "https://media.discordapp.net/attachments/1124435756774084659/1339471609328832572/IMG_1520.jpg",
    "https://media.discordapp.net/attachments/1124435756774084659/1339471616152834068/IMG_1519.jpg",
    "https://media.discordapp.net/attachments/1124435756774084659/1339471775314088050/IMG_1518.jpg",
    "https://media.discordapp.net/attachments/1124435756774084659/1339471807610097766/IMG_1517.jpg",
    "https://media.discordapp.net/attachments/1124435756774084659/1339471812328947775/IMG_1516.jpg",
    "https://media.discordapp.net/attachments/1124435756774084659/1339471817601187933/IMG_1515.jpg",
    "https://media.discordapp.net/attachments/1124435756774084659/1339471823922003978/IMG_1514.jpg",
    "https://media.discordapp.net/attachments/1124435756774084659/1339471829911208006/IMG_1513.jpg",
    "https://media.discordapp.net/attachments/1124435756774084659/1339471835426717747/IMG_1512.jpg",
    "https://media.discordapp.net/attachments/1124435756774084659/1339471845308497960/IMG_1511.jpg",
    "https://media.discordapp.net/attachments/1124435756774084659/1339471868553465926/IMG_1510.jpg",
    "https://media.discordapp.net/attachments/1124435756774084659/1339471877910954035/IMG_1509.jpg",
    "https://media.discordapp.net/attachments/1124435756774084659/1339471885280346205/IMG_1508.jpg",
    "https://media.discordapp.net/attachments/1124435756774084659/1339471893563965473/IMG_1507.jpg",
]
ALT_JACKET = "https://media.discordapp.net/attachments/1124435756774084659/1346631821521195008/IMG_8887.png"
ROLL_CALL_URL = f"https://discord.com/channels/{GUILD_ID}/1047338695352664165"
COLOR_CHANNEL_URL = f"https://discord.com/channels/{GUILD_ID}/1108181679308283965"

# =========================
# DISCORD SETUP
# =========================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)


async def _setup_hook():
    await bot.load_extension("cogs.partner_expansion")
    await bot.load_extension("cogs.partner_request_system")
    await bot.load_extension("cogs.diff_welcome_join")
    await bot.load_extension("cogs.diff_feedback_system")
    await bot.load_extension("cogs.diff_manager_hub")
    await bot.load_extension("cogs.diff_manager_season")
    await bot.load_extension("cogs.diff_manager_writeups")
    await bot.load_extension("cogs.diff_full_moderation")
    await bot.load_extension("cogs.diff_staff_dashboard")
    await bot.load_extension("cogs.diff_next_level_moderation")
    await bot.load_extension("cogs.diff_memes_panel")
    await bot.load_extension("cogs.diff_irl_car_photos_panel")
    await bot.load_extension("cogs.diff_car_photos_panel")
    await bot.load_extension("cogs.diff_content_support_panel")
    await bot.load_extension("cogs.diff_case_system")
    await bot.load_extension("cogs.diff_meet_channel_panel")
    await bot.load_extension("cogs.diff_meet_host_system")
    await bot.load_extension("cogs.diff_marketplace")

bot.setup_hook = _setup_hook


@bot.command(name="fixunverified")
@commands.has_permissions(manage_roles=True)
async def fix_unverified(ctx: commands.Context):
    """Strips Unverified role from anyone who already has Verified. Usage: !fixunverified"""
    guild = ctx.guild
    verified_role   = guild.get_role(VERIFIED_ROLE_ID)
    unverified_role = guild.get_role(UNVERIFIED_ROLE_ID)
    if not verified_role or not unverified_role:
        await ctx.send("❌ Could not find Verified or Unverified role.", delete_after=10)
        return
    msg = await ctx.send("🔄 Scanning members...")
    fixed = 0
    async for member in guild.fetch_members(limit=None):
        if verified_role in member.roles and unverified_role in member.roles:
            try:
                await member.remove_roles(unverified_role, reason="!fixunverified — already verified")
                fixed += 1
            except discord.HTTPException:
                pass
    await msg.edit(content=f"✅ Done. Removed Unverified from **{fixed}** member(s).")


# Global view error handler — ensures every button/select in every view
# always sends a response even when an unhandled exception occurs,
# preventing the "This interaction failed" red error message.
async def _global_view_on_error(
    self: discord.ui.View,
    interaction: discord.Interaction,
    error: Exception,
    item: discord.ui.Item,
) -> None:
    import traceback
    print(f"[ViewError] {type(self).__name__} / {getattr(item, 'custom_id', item)} → {error}")
    traceback.print_exc()
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "Something went wrong. Please try again or contact staff.", ephemeral=True
            )
        else:
            await interaction.followup.send(
                "Something went wrong. Please try again or contact staff.", ephemeral=True
            )
    except Exception:
        pass

discord.ui.View.on_error = _global_view_on_error  # type: ignore


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
# RECRUITMENT EXPANSION — HELPERS
# =========================

def _ensure_diff_data():
    os.makedirs(DATA_FOLDER, exist_ok=True)
    for path in [COOLDOWN_FILE, MEMBER_DB_FILE]:
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=2)


def _load_diff_json(path: str) -> dict:
    _ensure_diff_data()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_diff_json(path: str, data: dict):
    _ensure_diff_data()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def build_diff_member_name(name: str) -> str:
    clean = re.sub(r"\s+", " ", name).strip()
    return f"🅳🅸🅵🅵 - {clean} (Member)"


def set_reapply_cooldown(user_id: int):
    data = _load_diff_json(COOLDOWN_FILE)
    expires_at = (datetime.utcnow() + timedelta(days=REAPPLY_COOLDOWN_DAYS)).isoformat()
    data[str(user_id)] = {"expires_at": expires_at, "set_at": datetime.utcnow().isoformat()}
    _save_diff_json(COOLDOWN_FILE, data)


def clear_reapply_cooldown(user_id: int):
    data = _load_diff_json(COOLDOWN_FILE)
    data.pop(str(user_id), None)
    _save_diff_json(COOLDOWN_FILE, data)


def get_reapply_cooldown_text(user_id: int):
    data = _load_diff_json(COOLDOWN_FILE)
    entry = data.get(str(user_id))
    if not entry:
        return None
    try:
        expires_at = datetime.fromisoformat(entry["expires_at"])
    except Exception:
        return None
    now = datetime.utcnow()
    if expires_at <= now:
        data.pop(str(user_id), None)
        _save_diff_json(COOLDOWN_FILE, data)
        return None
    delta = expires_at - now
    return f"{delta.days}d {delta.seconds // 3600}h remaining"


async def add_member_to_database(
    guild: discord.Guild,
    member: discord.Member,
    accepted_by: discord.Member = None,
    nickname: str = None,
):
    data = _load_diff_json(MEMBER_DB_FILE)
    data[str(member.id)] = {
        "user_id": member.id,
        "username": str(member),
        "display_name": member.display_name,
        "nickname": nickname or member.nick,
        "joined_diff_at": datetime.utcnow().isoformat(),
        "accepted_by_id": accepted_by.id if accepted_by else None,
        "accepted_by_name": str(accepted_by) if accepted_by else None,
    }
    _save_diff_json(MEMBER_DB_FILE, data)
    db_channel = guild.get_channel(MEMBER_DATABASE_CHANNEL_ID)
    if isinstance(db_channel, discord.TextChannel):
        embed = discord.Embed(title="DIFF Member Added", color=discord.Color.green(), timestamp=utc_now())
        embed.add_field(name="Member", value=f"{member.mention} (`{member.id}`)", inline=False)
        embed.add_field(name="Name", value=nickname or member.display_name, inline=False)
        if accepted_by:
            embed.add_field(name="Accepted By", value=accepted_by.mention, inline=False)
        try:
            await db_channel.send(embed=embed)
        except Exception:
            pass


def _score_text(text: str) -> int:
    t = (text or "").strip()
    if not t:
        return 0
    if len(t) < 20:
        return 1
    if len(t) < 60:
        return 2
    if len(t) < 120:
        return 3
    if len(t) < 220:
        return 4
    return 5


def _keyword_bonus(text: str, keywords: list) -> int:
    text_low = (text or "").lower()
    hits = sum(1 for k in keywords if k.lower() in text_low)
    return 2 if hits >= 4 else (1 if hits >= 2 else 0)


def generate_application_score(answers: dict) -> dict:
    scores = {
        "Build / Skills": min(5, _score_text(answers.get("personal_skills", "")) + _keyword_bonus(
            answers.get("personal_skills", ""),
            ["clean", "realistic", "fitment", "stance", "wheels", "detail", "photography", "content", "tasteful"],
        )),
        "Availability": min(5, _score_text(answers.get("days_available", "")) + _keyword_bonus(
            answers.get("days_available", ""),
            ["weekends", "daily", "active", "available", "consistent", "discord", "meets"],
        )),
        "Meet Experience": min(5, _score_text(answers.get("meet_experience", "")) + _keyword_bonus(
            answers.get("meet_experience", ""),
            ["jdm", "stance", "oem", "realistic", "car", "meet", "community", "crew", "diff"],
        )),
        "Why Join": min(5, _score_text(answers.get("why_join", "")) + _keyword_bonus(
            answers.get("why_join", ""),
            ["community", "realism", "meets", "cars", "crew", "growth", "active", "diff"],
        )),
        "What They Bring": min(5, _score_text(answers.get("what_bring", "")) + _keyword_bonus(
            answers.get("what_bring", ""),
            ["photography", "content", "creation", "event", "organize", "media", "editing"],
        )),
    }
    total = sum(scores.values())
    if total >= 21:
        suggestion, color = "✅ Strong Accept", 0x2ecc71
    elif total >= 14:
        suggestion, color = "🟡 Review Manually", 0xf1c40f
    else:
        suggestion, color = "❌ Likely Deny", 0xe74c3c
    weak = [k for k, v in scores.items() if v <= 2]
    return {"scores": scores, "total": total, "max_total": 25, "suggestion": suggestion, "color": color, "weak": weak}


def build_score_embed(app_id: str, applicant, score_data: dict) -> discord.Embed:
    embed = discord.Embed(
        title=f"📊 Auto Score — Application #{app_id}",
        color=discord.Color(score_data["color"]),
        timestamp=utc_now(),
    )
    embed.set_author(name=str(applicant), icon_url=applicant.display_avatar.url)
    lines = "\n".join(f"**{k}:** {v}/5" for k, v in score_data["scores"].items())
    lines += f"\n\n**Total:** {score_data['total']}/{score_data['max_total']}"
    lines += f"\n**Suggestion:** {score_data['suggestion']}"
    embed.add_field(name="Breakdown", value=lines, inline=False)
    if score_data["weak"]:
        embed.add_field(name="Weak Areas", value="\n".join(f"• {k}" for k in score_data["weak"])[:1024], inline=False)
    embed.set_footer(text="Staff eyes only — auto-generated score")
    return embed


def get_app_by_ticket_channel(channel_id: int):
    app_data = load_apps()
    for app_id, record in app_data["applications"].items():
        if record.get("ticket_channel_id") == channel_id:
            return app_id, record
    return None, None


async def detect_ticket_applicant(channel: discord.TextChannel):
    guild = channel.guild
    topic = channel.topic or ""
    m = re.search(r"User ID:\s*(\d{17,20})", topic, re.I)
    if m:
        user_id = int(m.group(1))
        member = guild.get_member(user_id)
        if member:
            return member
        try:
            return await guild.fetch_member(user_id)
        except Exception:
            pass
    try:
        async for msg in channel.history(limit=50, oldest_first=True):
            if not msg.author.bot:
                return guild.get_member(msg.author.id) or msg.author
    except Exception:
        pass
    return None


def build_dashboard_embed() -> discord.Embed:
    cooldowns = _load_diff_json(COOLDOWN_FILE)
    members = _load_diff_json(MEMBER_DB_FILE)
    app_data = load_apps()
    apps = app_data.get("applications", {})
    now = datetime.utcnow()
    active_cds = 0
    for e in cooldowns.values():
        try:
            if datetime.fromisoformat(e["expires_at"]) > now:
                active_cds += 1
        except Exception:
            pass
    embed = discord.Embed(
        title="DIFF Staff Recruitment Dashboard",
        description="Live snapshot of the DIFF application system.",
        color=discord.Color.blurple(),
        timestamp=utc_now(),
    )
    embed.add_field(name="Total Applications", value=str(len(apps)), inline=True)
    embed.add_field(name="Pending", value=str(sum(1 for a in apps.values() if a.get("status") == "Pending")), inline=True)
    embed.add_field(name="Approved", value=str(sum(1 for a in apps.values() if a.get("status") == "Approved")), inline=True)
    embed.add_field(name="Denied", value=str(sum(1 for a in apps.values() if a.get("status") == "Denied")), inline=True)
    embed.add_field(name="Timed Out", value=str(sum(1 for a in apps.values() if a.get("status") == "Timed Out")), inline=True)
    embed.add_field(name="Active Cooldowns", value=str(active_cds), inline=True)
    embed.add_field(name="Members Logged", value=str(len(members)), inline=True)
    embed.set_footer(text="DIFF Staff Only")
    return embed


# =========================
# ACTIVITY + RANK SYSTEM — HELPERS
# =========================

def _ensure_activity_files():
    os.makedirs(DATA_FOLDER, exist_ok=True)
    for path in [ACTIVITY_FILE, REPUTATION_FILE, MEETS_FILE]:
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=2)


def _load_activity_json(path: str) -> dict:
    _ensure_activity_files()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_activity_json(path: str, data: dict):
    _ensure_activity_files()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_user_stats(user_id: int) -> dict:
    data = _load_activity_json(ACTIVITY_FILE)
    return data.get(str(user_id), {"meets_attended": 0, "meets_hosted": 0, "last_updated": None, "username": None})


def save_user_stats(user_id: int, stats: dict):
    data = _load_activity_json(ACTIVITY_FILE)
    data[str(user_id)] = stats
    _save_activity_json(ACTIVITY_FILE, data)


def get_user_reputation(user_id: int) -> dict:
    data = _load_activity_json(REPUTATION_FILE)
    return data.get(str(user_id), {"reputation": 0, "positive_notes": [], "negative_notes": [], "last_updated": None, "username": None})


def save_user_reputation(user_id: int, rep: dict):
    data = _load_activity_json(REPUTATION_FILE)
    data[str(user_id)] = rep
    _save_activity_json(REPUTATION_FILE, data)


def current_rank_name(member: discord.Member) -> str:
    role_ids = {role.id for role in member.roles}
    if LEADER_ROLE_ID in role_ids:
        return "Leader"
    if CO_LEADER_ROLE_ID in role_ids:
        return "Co Leader"
    if MANAGER_ROLE_ID in role_ids:
        return "Manager"
    if HOST_ROLE_ID in role_ids:
        return "Host"
    if CREW_MEMBER_ROLE_ID in role_ids:
        return "Crew Member"
    return "Unranked"


def check_promotion_eligibility(member: discord.Member):
    stats = get_user_stats(member.id)
    rep = get_user_reputation(member.id)
    current = current_rank_name(member)
    thresholds = {
        "Crew Member": (HOST_PROMOTION_ATTENDED, HOST_PROMOTION_HOSTED, HOST_PROMOTION_REPUTATION, "Host"),
        "Host": (MANAGER_PROMOTION_ATTENDED, MANAGER_PROMOTION_HOSTED, MANAGER_PROMOTION_REPUTATION, "Manager"),
        "Manager": (LEADER_PROMOTION_ATTENDED, LEADER_PROMOTION_HOSTED, LEADER_PROMOTION_REPUTATION, "Leader"),
    }
    if current not in thresholds:
        return None
    req_att, req_host, req_rep, next_rank = thresholds[current]
    eligible = (
        stats["meets_attended"] >= req_att and
        stats["meets_hosted"] >= req_host and
        rep["reputation"] >= req_rep
    )
    return {
        "current_role": current, "suggested_role": next_rank, "eligible": eligible,
        "required_attended": req_att, "required_hosted": req_host, "required_reputation": req_rep,
        "stats": stats, "reputation": rep["reputation"],
    }


async def maybe_post_promotion_suggestion(guild: discord.Guild, member: discord.Member):
    result = check_promotion_eligibility(member)
    if not result or not result["eligible"]:
        return
    channel = guild.get_channel(STAFF_LOGS_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        return
    embed = discord.Embed(title="📈 Promotion Suggestion", color=discord.Color.gold(), timestamp=utc_now())
    embed.add_field(name="Member", value=member.mention, inline=False)
    embed.add_field(name="Current Role", value=result["current_role"], inline=False)
    embed.add_field(name="Suggested Role", value=result["suggested_role"], inline=False)
    embed.add_field(
        name="Stats",
        value=f"• Meets Attended: {result['stats']['meets_attended']}\n• Meets Hosted: {result['stats']['meets_hosted']}\n• Reputation: {result['reputation']}",
        inline=False,
    )
    await channel.send(embed=embed)


async def record_meet_attendance(guild: discord.Guild, member: discord.Member, meet_name: str, host_member: discord.Member = None):
    stats = get_user_stats(member.id)
    stats["meets_attended"] += 1
    stats["last_updated"] = datetime.utcnow().isoformat()
    stats["username"] = str(member)
    save_user_stats(member.id, stats)
    role_ids = {role.id for role in member.roles}
    if MEET_ATTENDER_ROLE_ID in role_ids:
        await update_member_reputation(guild, member, MEET_ATTENDANCE_REP, f"Attended meet: {meet_name}", given_by=None)
    await maybe_post_promotion_suggestion(guild, member)
    logs_ch = guild.get_channel(STAFF_LOGS_CHANNEL_ID)
    if isinstance(logs_ch, discord.TextChannel):
        embed = discord.Embed(title="✅ Meet Attendance Recorded", color=discord.Color.blue(), timestamp=utc_now())
        embed.add_field(name="Member", value=member.mention, inline=False)
        embed.add_field(name="Meet", value=meet_name, inline=False)
        embed.add_field(name="Host", value=host_member.mention if host_member else "Unknown", inline=False)
        embed.add_field(name="Total Attended", value=str(stats["meets_attended"]), inline=False)
        embed.add_field(name="Rep Awarded", value=f"+{MEET_ATTENDANCE_REP}" if MEET_ATTENDER_ROLE_ID in role_ids else "None (no attender role)", inline=False)
        try:
            await logs_ch.send(embed=embed)
        except Exception:
            pass


async def record_meet_host(guild: discord.Guild, host_member: discord.Member, meet_name: str):
    stats = get_user_stats(host_member.id)
    stats["meets_hosted"] += 1
    stats["last_updated"] = datetime.utcnow().isoformat()
    stats["username"] = str(host_member)
    save_user_stats(host_member.id, stats)
    await maybe_post_promotion_suggestion(guild, host_member)
    logs_ch = guild.get_channel(STAFF_LOGS_CHANNEL_ID)
    if isinstance(logs_ch, discord.TextChannel):
        embed = discord.Embed(title="🎤 Meet Host Recorded", color=discord.Color.purple(), timestamp=utc_now())
        embed.add_field(name="Host", value=host_member.mention, inline=False)
        embed.add_field(name="Meet", value=meet_name, inline=False)
        embed.add_field(name="Total Hosted", value=str(stats["meets_hosted"]), inline=False)
        try:
            await logs_ch.send(embed=embed)
        except Exception:
            pass


async def update_member_reputation(guild: discord.Guild, member: discord.Member, amount: int, note: str, given_by: discord.Member = None):
    rep = get_user_reputation(member.id)
    rep["reputation"] += amount
    rep["last_updated"] = datetime.utcnow().isoformat()
    rep["username"] = str(member)
    note_entry = {"amount": amount, "note": note, "given_by": str(given_by) if given_by else None, "created_at": datetime.utcnow().isoformat()}
    if amount >= 0:
        rep["positive_notes"].append(note_entry)
        rep["positive_notes"] = rep["positive_notes"][-25:]
    else:
        rep["negative_notes"].append(note_entry)
        rep["negative_notes"] = rep["negative_notes"][-25:]
    save_user_reputation(member.id, rep)
    await maybe_post_promotion_suggestion(guild, member)
    logs_ch = guild.get_channel(STAFF_LOGS_CHANNEL_ID)
    if isinstance(logs_ch, discord.TextChannel):
        title = "🏆 Reputation Added" if amount >= 0 else "⚠️ Reputation Removed"
        color = discord.Color.green() if amount >= 0 else discord.Color.red()
        embed = discord.Embed(title=title, color=color, timestamp=utc_now())
        embed.add_field(name="Member", value=member.mention, inline=False)
        embed.add_field(name="Change", value=f"{amount:+}", inline=False)
        embed.add_field(name="New Total", value=str(rep["reputation"]), inline=False)
        embed.add_field(name="Reason", value=note[:1024], inline=False)
        if given_by:
            embed.add_field(name="Updated By", value=given_by.mention, inline=False)
        try:
            await logs_ch.send(embed=embed)
        except Exception:
            pass


def build_leaderboard_lines(guild: discord.Guild) -> list:
    activity = _load_activity_json(ACTIVITY_FILE)
    reputation = _load_activity_json(REPUTATION_FILE)
    rows = []
    for user_id, stats in activity.items():
        rep_value = reputation.get(user_id, {}).get("reputation", 0)
        attended = stats.get("meets_attended", 0)
        hosted = stats.get("meets_hosted", 0)
        score = (attended * 2) + (hosted * 5) + rep_value
        rows.append({"user_id": int(user_id), "attended": attended, "hosted": hosted, "reputation": rep_value, "score": score})
    rows.sort(key=lambda x: x["score"], reverse=True)
    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for idx, row in enumerate(rows[:10], start=1):
        member = guild.get_member(row["user_id"])
        name = member.mention if member else f"<@{row['user_id']}>"
        badge = medals[idx - 1] if idx <= 3 else f"#{idx}"
        lines.append(f"{badge} {name}\nAttended: {row['attended']} | Hosted: {row['hosted']} | Rep: {row['reputation']} | Score: {row['score']}")
    return lines if lines else ["No activity data yet."]


def _get_most_improved() -> dict | None:
    best = None
    best_gain = 0
    for entry in _rsvp_leaderboard.values():
        current = int(entry.get("attendance_count", 0))
        last = int(entry.get("last_attendance_count", 0))
        gain = current - last
        if gain > best_gain:
            best_gain = gain
            best = entry
    return best if best_gain > 0 else None


def build_leaderboard_embed(guild: discord.Guild) -> discord.Embed:
    top_all = sorted(
        _rsvp_leaderboard.values(),
        key=lambda x: (int(x.get("attendance_count", 0)), int(x.get("hosted_count", 0))),
        reverse=True,
    )[:10]
    top3 = top_all[:3]
    rest = top_all[3:]
    medals = ["🥇", "🥈", "🥉"]

    top_lines = []
    for i, entry in enumerate(top3):
        top_lines.append(f"{medals[i]} **#{i+1}** <@{entry['user_id']}> — **{entry.get('attendance_count', 0)}** meet(s)")

    rest_lines = []
    for idx, entry in enumerate(rest, start=4):
        rest_lines.append(f"📌 **#{idx}** <@{entry['user_id']}> — **{entry.get('attendance_count', 0)}** meet(s)")
    if not rest_lines:
        rest_lines = ["No additional members ranked yet."]

    improved = _get_most_improved()
    if improved:
        gain = int(improved.get("attendance_count", 0)) - int(improved.get("last_attendance_count", 0))
        improved_line = f"📈 **Most Improved:** <@{improved['user_id']}> (**+{gain}** this week)"
    else:
        improved_line = "📈 **Most Improved:** No improvement data yet"

    sep = "━━━━━━━━━━━━━━━━━━━━━━"
    desc_parts = [
        "📊 **Most active DIFF members**",
        "",
        sep,
        *top_lines,
        sep,
        *rest_lines,
        sep,
        improved_line,
        "",
        "Stay active, stay consistent, and represent DIFF the right way.",
    ]
    embed = discord.Embed(
        title="🏆 DIFF Weekly Leaderboard",
        description="\n".join(desc_parts),
        color=discord.Color.from_rgb(17, 17, 17),
        timestamp=utc_now(),
    )
    embed.set_footer(text="Different Meets • Weekly Activity Panel")
    return embed


def build_member_stats_embed(member: discord.Member) -> discord.Embed:
    stats = get_user_stats(member.id)
    rep = get_user_reputation(member.id)
    result = check_promotion_eligibility(member)
    embed = discord.Embed(title=f"Activity Stats — {member.display_name}", color=discord.Color.blue(), timestamp=utc_now())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Current Rank", value=current_rank_name(member), inline=True)
    embed.add_field(name="Meets Attended", value=str(stats["meets_attended"]), inline=True)
    embed.add_field(name="Meets Hosted", value=str(stats["meets_hosted"]), inline=True)
    embed.add_field(name="Reputation", value=str(rep["reputation"]), inline=True)
    if result:
        next_rank = result["suggested_role"]
        progress = (
            f"**→ {next_rank}**\n"
            f"Attended: {stats['meets_attended']}/{result['required_attended']}\n"
            f"Hosted: {stats['meets_hosted']}/{result['required_hosted']}\n"
            f"Reputation: {rep['reputation']}/{result['required_reputation']}"
        )
        embed.add_field(name="Next Promotion Progress", value=progress, inline=False)
        if result["eligible"]:
            embed.add_field(name="✅ Eligible for Promotion", value=f"This member meets all thresholds for **{next_rank}**.", inline=False)
    return embed


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
        em = discord.Embed(
            description=message,
            color=discord.Color.dark_blue(),
        )
        em.set_author(name="Different Meets", icon_url=DIFF_LOGO_URL)
        em.set_thumbnail(url=DIFF_LOGO_URL)
        await user.send(embed=em)
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
            dm_em = discord.Embed(
                title="DIFF Staff Response",
                description=reply,
                color=discord.Color.dark_blue(),
            )
            dm_em.set_author(name="Different Meets", icon_url=DIFF_LOGO_URL)
            dm_em.set_thumbnail(url=DIFF_LOGO_URL)
            await self.target_user.send(embed=dm_em)
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

        try:
            tab_state = _tab_load()
            ticket_key = str(interaction.channel.id)
            linked_member_id = tab_state.get("ticket_links", {}).get(ticket_key, {}).get("member_id")
            if linked_member_id:
                ticket_owner = interaction.guild.get_member(int(linked_member_id))
                if ticket_owner is None:
                    try:
                        ticket_owner = await interaction.guild.fetch_member(int(linked_member_id))
                    except Exception:
                        ticket_owner = None
        except Exception:
            pass

        if ticket_owner is None:
            try:
                detected = _fus_detect_applicant(interaction.channel)
                if detected:
                    ticket_owner = detected
            except Exception:
                pass

        if ticket_owner is None:
            async for msg in interaction.channel.history(limit=20):
                if not msg.author.bot:
                    ticket_owner = interaction.guild.get_member(msg.author.id)
                    break

        if ticket_owner is None:
            return await interaction.response.send_message(
                "❌ Could not detect the ticket owner. Try linking them first with `/setup-application-ticket` or ask them to send a message in this channel.",
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

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        traceback.print_exception(type(error), error, error.__traceback__)
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
            else:
                await interaction.followup.send("Something went wrong. Please try again.", ephemeral=True)
        except Exception:
            pass

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
        await interaction.response.defer(ephemeral=True)
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
        await interaction.followup.send(
            "Your request for more information has been sent to DIFF staff. Please wait for a response.",
            ephemeral=True,
        )


# =========================
# APPLICATION REVIEW VIEW
# =========================
class ReviewView(discord.ui.View):
    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        traceback.print_exception(type(error), error, error.__traceback__)
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
            else:
                await interaction.followup.send("Something went wrong. Please try again.", ephemeral=True)
        except Exception:
            pass

    def __init__(self, app_id: str, applicant_id: int):
        super().__init__(timeout=None)
        self.app_id = app_id
        self.applicant_id = applicant_id

    async def _fetch_photo_count(self, guild: discord.Guild, record: dict) -> tuple[int, bool]:
        """Returns (photo_count, channel_found). No interaction responses."""
        ch_id = record.get("ticket_channel_id")
        if not ch_id:
            return 0, False
        ticket_channel = guild.get_channel(ch_id)
        if not isinstance(ticket_channel, discord.TextChannel):
            return 0, False
        messages = [m async for m in ticket_channel.history(limit=200)]
        return count_message_attachments(messages), True

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
        await interaction.response.defer()
        photo_count, ch_found = await self._fetch_photo_count(interaction.guild, record)
        if not ch_found:
            return await interaction.followup.send("Garage ticket channel could not be found.", ephemeral=True)
        if photo_count < MIN_GARAGE_PHOTOS:
            return await interaction.followup.send(
                f"This applicant only has **{photo_count}** uploaded file(s). Minimum required is **{MIN_GARAGE_PHOTOS}** before making a decision.",
                ephemeral=True,
            )
        applicant = interaction.guild.get_member(self.applicant_id)
        if applicant is None:
            return await interaction.followup.send("Applicant is no longer in the server.", ephemeral=True)
        approved_role = interaction.guild.get_role(APPROVED_MEMBER_ROLE_ID)
        if approved_role:
            try:
                await applicant.add_roles(approved_role, reason=f"DIFF application #{self.app_id} approved by {interaction.user}")
            except discord.Forbidden:
                await interaction.followup.send("I don't have permission to assign that role.", ephemeral=True)
                return
        await self._finalize(interaction, "Approved", interaction.user, close_ticket=True)
        await safe_dm(applicant, f"Your DIFF application **#{self.app_id}** was **approved**. Welcome to DIFF! 🎉")
        clear_reapply_cooldown(applicant.id)
        final_name = build_diff_member_name(applicant.display_name)
        try:
            await applicant.edit(nick=final_name, reason=f"DIFF application #{self.app_id} approved")
        except Exception:
            pass
        await add_member_to_database(interaction.guild, applicant, accepted_by=interaction.user, nickname=final_name)
        dashboard_ch = interaction.guild.get_channel(STAFF_DASHBOARD_CHANNEL_ID)
        if isinstance(dashboard_ch, discord.TextChannel):
            dash_embed = discord.Embed(title="DIFF Application Accepted", color=discord.Color.green(), timestamp=utc_now())
            dash_embed.add_field(name="Applicant", value=f"{applicant.mention} (`{applicant.id}`)", inline=False)
            dash_embed.add_field(name="Accepted By", value=interaction.user.mention, inline=False)
            dash_embed.add_field(name="Final Name", value=final_name, inline=False)
            try:
                await dashboard_ch.send(embed=dash_embed)
            except Exception:
                pass

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
        embed = interaction.message.embeds[0] if interaction.message and interaction.message.embeds else discord.Embed()
        embed.color = discord.Color.green() if new_status == "Approved" else discord.Color.red()
        embed.set_footer(text=f"Status: {new_status} • Reviewed by {reviewer}")
        embed.timestamp = utc_now()
        if interaction.response.is_done():
            try:
                await interaction.edit_original_response(embed=embed, view=self)
            except discord.HTTPException:
                pass
        else:
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
        set_reapply_cooldown(self.applicant_id)
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
        dashboard_ch = interaction.guild.get_channel(STAFF_DASHBOARD_CHANNEL_ID)
        if isinstance(dashboard_ch, discord.TextChannel):
            dash_embed = discord.Embed(title="DIFF Application Denied", color=discord.Color.red(), timestamp=utc_now())
            dash_embed.add_field(name="Applicant", value=f"<@{self.applicant_id}> (`{self.applicant_id}`)", inline=False)
            dash_embed.add_field(name="Denied By", value=interaction.user.mention, inline=False)
            dash_embed.add_field(name="Reason", value=deny_reason[:1024], inline=False)
            dash_embed.add_field(name="Reapply Cooldown", value=f"{REAPPLY_COOLDOWN_DAYS} days", inline=False)
            try:
                await dashboard_ch.send(embed=dash_embed)
            except Exception:
                pass


# =========================
# RECRUITMENT EXPANSION — TICKET VIEW
# =========================

class TicketAcceptModal(discord.ui.Modal, title="Accept Applicant"):
    member_name = discord.ui.TextInput(
        label="Name after 🅳🅸🅵🅵 -",
        placeholder="e.g. Frostyy2003",
        max_length=24,
    )

    async def on_submit(self, interaction: discord.Interaction):
        if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
            return await interaction.response.send_message("❌ Staff only.", ephemeral=True)
        if not isinstance(interaction.channel, discord.TextChannel):
            return await interaction.response.send_message("❌ Ticket channels only.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        applicant = await detect_ticket_applicant(interaction.channel)
        if not isinstance(applicant, discord.Member):
            return await interaction.followup.send("❌ Could not detect applicant in this ticket.", ephemeral=True)
        app_id, record = get_app_by_ticket_channel(interaction.channel.id)
        if not record:
            return await interaction.followup.send("❌ No application record linked to this ticket.", ephemeral=True)
        if record.get("status") not in {"Pending", "More Info Requested"}:
            return await interaction.followup.send("❌ This application has already been decided.", ephemeral=True)
        guild = interaction.guild
        approved_role = guild.get_role(APPROVED_MEMBER_ROLE_ID)
        if approved_role:
            try:
                await applicant.add_roles(approved_role, reason=f"DIFF #{app_id} accepted via ticket by {interaction.user}")
            except Exception:
                pass
        final_name = build_diff_member_name(str(self.member_name))
        try:
            await applicant.edit(nick=final_name, reason=f"DIFF #{app_id} accepted")
        except Exception:
            pass
        clear_reapply_cooldown(applicant.id)
        await add_member_to_database(guild, applicant, accepted_by=interaction.user, nickname=final_name)
        update_app(app_id, status="Approved", reviewed_by=str(interaction.user), reviewed_by_id=interaction.user.id, reviewed_at=utc_now().isoformat())
        try:
            review_ch = guild.get_channel(record.get("review_channel_id"))
            if isinstance(review_ch, discord.TextChannel) and record.get("review_message_id"):
                review_msg = await review_ch.fetch_message(record["review_message_id"])
                emb = review_msg.embeds[0]
                emb.color = discord.Color.green()
                emb.set_footer(text=f"Status: Approved • Reviewed by {interaction.user}")
                emb.timestamp = utc_now()
                await review_msg.edit(embed=emb, view=None)
        except Exception:
            pass
        try:
            tracker_ch = guild.get_channel(record.get("tracker_channel_id"))
            if isinstance(tracker_ch, discord.TextChannel) and record.get("tracker_message_id"):
                tracker_msg = await tracker_ch.fetch_message(record["tracker_message_id"])
                answers = {k: record.get(k, "N/A") for k in ("gamertag", "days_available", "why_join")}
                t_emb = build_tracker_embed(app_id, applicant, answers, "Approved", interaction.user.mention)
                await tracker_msg.edit(embed=t_emb)
        except Exception:
            pass
        try:
            await applicant.send(f"✅ Your DIFF application **#{app_id}** was **approved**. Welcome to DIFF! 🎉\nYour server name has been set to: `{final_name}`")
        except Exception:
            pass
        try:
            await interaction.channel.send(embed=discord.Embed(
                title="Application Accepted",
                description=f"{applicant.mention} has been accepted by {interaction.user.mention}.\nName: `{final_name}`",
                color=discord.Color.green(),
                timestamp=utc_now(),
            ))
        except Exception:
            pass
        dashboard_ch = guild.get_channel(STAFF_DASHBOARD_CHANNEL_ID)
        if isinstance(dashboard_ch, discord.TextChannel):
            dash = discord.Embed(title="DIFF Application Accepted", color=discord.Color.green(), timestamp=utc_now())
            dash.add_field(name="Applicant", value=f"{applicant.mention} (`{applicant.id}`)", inline=False)
            dash.add_field(name="Accepted By", value=interaction.user.mention, inline=False)
            dash.add_field(name="Final Name", value=final_name, inline=False)
            try:
                await dashboard_ch.send(embed=dash)
            except Exception:
                pass
        try:
            await interaction.channel.edit(name=f"closed-{interaction.channel.name[:80]}")
            await interaction.channel.set_permissions(guild.default_role, view_channel=False)
            if applicant in guild.members:
                await interaction.channel.set_permissions(applicant, view_channel=False)
        except Exception:
            pass
        await interaction.followup.send("✅ Applicant accepted, ticket closed.", ephemeral=True)


class TicketDenyModal(discord.ui.Modal, title="Deny Applicant"):
    reason = discord.ui.TextInput(
        label="Denial reason",
        style=discord.TextStyle.paragraph,
        placeholder="Explain why the applicant was denied...",
        max_length=1000,
    )

    async def on_submit(self, interaction: discord.Interaction):
        if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
            return await interaction.response.send_message("❌ Staff only.", ephemeral=True)
        if not isinstance(interaction.channel, discord.TextChannel):
            return await interaction.response.send_message("❌ Ticket channels only.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        applicant = await detect_ticket_applicant(interaction.channel)
        if not applicant:
            return await interaction.followup.send("❌ Could not detect applicant in this ticket.", ephemeral=True)
        app_id, record = get_app_by_ticket_channel(interaction.channel.id)
        if not record:
            return await interaction.followup.send("❌ No application record linked to this ticket.", ephemeral=True)
        if record.get("status") not in {"Pending", "More Info Requested"}:
            return await interaction.followup.send("❌ This application has already been decided.", ephemeral=True)
        guild = interaction.guild
        deny_reason = str(self.reason)
        set_reapply_cooldown(applicant.id)
        update_app(app_id, status="Denied", deny_reason=deny_reason, reviewed_by=str(interaction.user), reviewed_by_id=interaction.user.id, reviewed_at=utc_now().isoformat())
        try:
            review_ch = guild.get_channel(record.get("review_channel_id"))
            if isinstance(review_ch, discord.TextChannel) and record.get("review_message_id"):
                review_msg = await review_ch.fetch_message(record["review_message_id"])
                emb = review_msg.embeds[0]
                emb.color = discord.Color.red()
                emb.set_footer(text=f"Status: Denied • Reviewed by {interaction.user}")
                emb.timestamp = utc_now()
                await review_msg.edit(embed=emb, view=None)
        except Exception:
            pass
        try:
            tracker_ch = guild.get_channel(record.get("tracker_channel_id"))
            if isinstance(tracker_ch, discord.TextChannel) and record.get("tracker_message_id"):
                tracker_msg = await tracker_ch.fetch_message(record["tracker_message_id"])
                answers = {k: record.get(k, "N/A") for k in ("gamertag", "days_available", "why_join")}
                t_emb = build_tracker_embed(app_id, applicant, answers, "Denied", interaction.user.mention)
                await tracker_msg.edit(embed=t_emb)
        except Exception:
            pass
        denied_embed = build_denied_result_embed(deny_reason)
        denied_view = DeniedResultView(app_id, applicant.id if hasattr(applicant, "id") else 0)
        try:
            await applicant.send(embed=denied_embed, view=denied_view)
        except Exception:
            try:
                await applicant.send(f"Your DIFF application **#{app_id}** was denied.\n\nReason: {deny_reason}")
            except Exception:
                pass
        try:
            await interaction.channel.send(embed=denied_embed)
        except Exception:
            pass
        dashboard_ch = guild.get_channel(STAFF_DASHBOARD_CHANNEL_ID)
        if isinstance(dashboard_ch, discord.TextChannel):
            dash = discord.Embed(title="DIFF Application Denied", color=discord.Color.red(), timestamp=utc_now())
            dash.add_field(name="Applicant", value=f"{applicant.mention} (`{applicant.id}`)", inline=False)
            dash.add_field(name="Denied By", value=interaction.user.mention, inline=False)
            dash.add_field(name="Reason", value=deny_reason[:1024], inline=False)
            dash.add_field(name="Reapply Cooldown", value=f"{REAPPLY_COOLDOWN_DAYS} days", inline=False)
            try:
                await dashboard_ch.send(embed=dash)
            except Exception:
                pass
        try:
            await interaction.channel.edit(name=f"closed-{interaction.channel.name[:80]}")
            await interaction.channel.set_permissions(guild.default_role, view_channel=False)
            if isinstance(applicant, discord.Member):
                await interaction.channel.set_permissions(applicant, view_channel=False)
        except Exception:
            pass
        await interaction.followup.send("✅ Applicant denied, ticket closed.", ephemeral=True)


class TicketRespondModal(discord.ui.Modal, title="Respond to Applicant"):
    reply = discord.ui.TextInput(
        label="Staff response",
        style=discord.TextStyle.paragraph,
        placeholder="Write your response here...",
        max_length=1500,
    )

    async def on_submit(self, interaction: discord.Interaction):
        if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
            return await interaction.response.send_message("❌ Staff only.", ephemeral=True)
        if not isinstance(interaction.channel, discord.TextChannel):
            return await interaction.response.send_message("❌ Ticket channels only.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        applicant = await detect_ticket_applicant(interaction.channel)
        if not applicant:
            return await interaction.followup.send("❌ Could not detect applicant in this ticket.", ephemeral=True)
        message_text = str(self.reply)
        dm_sent = False
        try:
            await applicant.send(message_text)
            dm_sent = True
        except Exception:
            pass
        try:
            await interaction.channel.send(f"📩 Staff response sent to {applicant.mention} by {interaction.user.mention}.\n\n{message_text}")
        except Exception:
            pass
        await interaction.followup.send(f"✅ Response sent (DM delivered: {dm_sent}).", ephemeral=True)


class TicketAcceptButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Accept", emoji="✅", style=discord.ButtonStyle.success, custom_id="diff_ticket_accept")

    async def callback(self, interaction: discord.Interaction):
        if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
            return await interaction.response.send_message("❌ Staff only.", ephemeral=True)
        await interaction.response.send_modal(TicketAcceptModal())


class TicketDenyButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Deny", emoji="❌", style=discord.ButtonStyle.danger, custom_id="diff_ticket_deny")

    async def callback(self, interaction: discord.Interaction):
        if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
            return await interaction.response.send_message("❌ Staff only.", ephemeral=True)
        await interaction.response.send_modal(TicketDenyModal())


class TicketRespondButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Respond", emoji="📩", style=discord.ButtonStyle.primary, custom_id="diff_ticket_respond")

    async def callback(self, interaction: discord.Interaction):
        if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
            return await interaction.response.send_message("❌ Staff only.", ephemeral=True)
        await interaction.response.send_modal(TicketRespondModal())


class TicketCloseButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Close Ticket", emoji="🔒", style=discord.ButtonStyle.secondary, custom_id="diff_ticket_close")

    async def callback(self, interaction: discord.Interaction):
        if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
            return await interaction.response.send_message("❌ Staff only.", ephemeral=True)
        if not isinstance(interaction.channel, discord.TextChannel):
            return await interaction.response.send_message("❌ Ticket channels only.", ephemeral=True)
        await interaction.response.send_message("🔒 Closing ticket in 5 seconds...", ephemeral=True)
        await asyncio.sleep(5)
        try:
            await interaction.channel.edit(name=f"closed-{interaction.channel.name[:80]}")
            await interaction.channel.set_permissions(interaction.guild.default_role, view_channel=False)
        except Exception:
            pass


class DIFFRecruitmentTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketAcceptButton())
        self.add_item(TicketDenyButton())
        self.add_item(TicketRespondButton())
        self.add_item(TicketCloseButton())


class DashboardRefreshButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Refresh", emoji="📊", style=discord.ButtonStyle.primary, custom_id="diff_dashboard_refresh")

    async def callback(self, interaction: discord.Interaction):
        if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
            return await interaction.response.send_message("❌ Staff only.", ephemeral=True)
        await interaction.response.edit_message(embed=build_dashboard_embed(), view=DIFFDashboardView())


class DIFFDashboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(DashboardRefreshButton())


# =========================
# ACTIVITY + RANK SYSTEM — VIEWS
# =========================

class MeetAttendancePanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Post Attendance", emoji="📊", style=discord.ButtonStyle.primary, custom_id="diff_post_attendance_button")
    async def post_attendance(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MeetAttendanceModal())


class MeetAttendanceModal(discord.ui.Modal, title="DIFF Meet Attendance"):
    host_name = discord.ui.TextInput(label="Host Name", placeholder="@HostName or staff name", max_length=60)
    meet_name = discord.ui.TextInput(label="Meet Name", placeholder="Tire Lettering Meet", max_length=100)
    meet_date = discord.ui.TextInput(label="Date", placeholder="Feb 7, 2026", max_length=40)
    total_players = discord.ui.TextInput(label="Total Players in Lobby", placeholder="20", max_length=10)
    diff_members_present = discord.ui.TextInput(label="DIFF Members Present", placeholder="Count or estimate", max_length=20)

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("❌ Server only.", ephemeral=True)
        attendance_channel = interaction.guild.get_channel(MEET_ATTENDANCE_CHANNEL_ID)
        if not isinstance(attendance_channel, discord.TextChannel):
            return await interaction.response.send_message("❌ Attendance channel not found.", ephemeral=True)
        try:
            total_players_value = int(str(self.total_players))
        except Exception:
            total_players_value = 0
        embed = discord.Embed(title="📊 DIFF Meet Attendance", color=discord.Color.blue(), timestamp=utc_now())
        embed.add_field(name="Host", value=str(self.host_name), inline=False)
        embed.add_field(name="Meet Name", value=str(self.meet_name), inline=False)
        embed.add_field(name="Date", value=str(self.meet_date), inline=False)
        embed.add_field(name="Total Players in Lobby", value=str(total_players_value), inline=False)
        embed.add_field(name="DIFF Members Present", value=str(self.diff_members_present), inline=False)
        embed.add_field(name="Screenshot", value="📸 Attach lobby screenshot below", inline=False)
        embed.set_footer(text=f"Submitted by {interaction.user}")
        await attendance_channel.send(embed=embed)
        data = _load_activity_json(MEETS_FILE)
        record_id = f"{interaction.guild.id}-{int(datetime.utcnow().timestamp())}"
        data[record_id] = {
            "host_name": str(self.host_name),
            "meet_name": str(self.meet_name),
            "meet_date": str(self.meet_date),
            "total_players": total_players_value,
            "diff_present": str(self.diff_members_present),
            "submitted_by_id": interaction.user.id,
            "submitted_by": str(interaction.user),
            "created_at": datetime.utcnow().isoformat(),
        }
        _save_activity_json(MEETS_FILE, data)
        await interaction.response.send_message("✅ Meet attendance posted.", ephemeral=True)


class RefreshLeaderboardButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Refresh", emoji="🏁", style=discord.ButtonStyle.success, custom_id="diff_refresh_leaderboard_button")

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("❌ Guild not found.", ephemeral=True)
        embed = build_leaderboard_embed(interaction.guild)
        await interaction.response.edit_message(embed=embed, view=LeaderboardView())


class LeaderboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RefreshLeaderboardButton())


CREW_HUB_STATE_FILE = os.path.join(DATA_FOLDER, "diff_crew_hub_state.json")


def _build_crew_hub_embed() -> discord.Embed:
    entries = list(_rsvp_leaderboard.values())
    total_tracked = len(entries)
    active = sum(1 for e in entries if int(e.get("attendance_count", 0)) > 0)
    total_attendance = sum(int(e.get("attendance_count", 0)) for e in entries)
    total_hosted = sum(int(e.get("hosted_count", 0)) for e in entries)

    try:
        apps = _load_diff_json(APPLICATIONS_FILE) if os.path.exists(APPLICATIONS_FILE) else {}
        completed_apps = sum(1 for a in apps.values() if a.get("status") == "Approved")
    except Exception:
        completed_apps = 0

    top3 = sorted(entries, key=lambda x: (int(x.get("attendance_count", 0)), int(x.get("hosted_count", 0))), reverse=True)[:3]
    medals = ["🥇", "🥈", "🥉"]
    top_lines = [f"{medals[i]} <@{e['user_id']}> — {e.get('attendance_count', 0)} meet(s)" for i, e in enumerate(top3)] or ["No top members yet."]

    improved = _get_most_improved()
    if improved:
        gain = int(improved.get("attendance_count", 0)) - int(improved.get("last_attendance_count", 0))
        improved_text = f"<@{improved['user_id']}> (+{gain} this week)"
    else:
        improved_text = "No data yet"

    sep = "━━━━━━━━━━━━━━━━━━━━━━"
    desc_parts = [
        "📌 **Live DIFF activity snapshot**",
        "",
        sep,
        f"👥 **Tracked Members:** {total_tracked}",
        f"🔥 **Active Members:** {active}",
        f"✅ **Total Attendance Logged:** {total_attendance}",
        f"🏁 **Total Meets Hosted:** {total_hosted}",
        f"📋 **Approved Crew Members:** {completed_apps}",
        f"🚀 **Most Improved:** {improved_text}",
        sep,
        "",
        "🏆 **Top 3 Right Now**",
        *top_lines,
        "",
        "Path: **Join → Attend → Get noticed → Crew invite**",
    ]
    embed = discord.Embed(
        title="📊 DIFF Crew Hub Stats",
        description="\n".join(desc_parts),
        color=discord.Color.from_rgb(17, 17, 17),
        timestamp=utc_now(),
    )
    embed.set_footer(text="Different Meets • Crew Hub Stats")
    return embed


class CrewHubRefreshButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Refresh Stats", emoji="📊", style=discord.ButtonStyle.secondary, custom_id="diff_crew_hub_refresh")

    async def callback(self, interaction: discord.Interaction) -> None:
        embed = _build_crew_hub_embed()
        await interaction.response.edit_message(embed=embed, view=CrewHubView())


class CrewHubView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CrewHubRefreshButton())


# =========================
# NOTIFY PANEL — MEMBER SELF-SERVE ROLE TOGGLE
# =========================

def _photo_hashes_load() -> dict:
    try:
        if os.path.exists(PHOTO_HASHES_FILE):
            with open(PHOTO_HASHES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _photo_hashes_save(data: dict) -> None:
    os.makedirs(os.path.dirname(PHOTO_HASHES_FILE), exist_ok=True)
    with open(PHOTO_HASHES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _crew_pinged_load() -> set:
    try:
        if os.path.exists(CREW_PINGED_FILE):
            with open(CREW_PINGED_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
    except Exception:
        pass
    return set()


def _crew_pinged_save(data: set) -> None:
    os.makedirs(os.path.dirname(CREW_PINGED_FILE), exist_ok=True)
    with open(CREW_PINGED_FILE, "w", encoding="utf-8") as f:
        json.dump(list(data), f, indent=2)


def _attachment_hash(attachment: discord.Attachment) -> str:
    raw = f"{attachment.filename}|{attachment.size}|{attachment.content_type or ''}|{attachment.url}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# =========================
# FINAL TIER — DATA HELPERS
# =========================

def _ft_load() -> dict:
    try:
        if os.path.exists(FINAL_TIER_FILE):
            with open(FINAL_TIER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"users": {}, "meets": [], "hosts": {}, "recaps": []}


def _ft_save(data: dict) -> None:
    os.makedirs(os.path.dirname(FINAL_TIER_FILE), exist_ok=True)
    with open(FINAL_TIER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _ft_ensure_user(user_id: int) -> dict:
    data = _ft_load()
    key = str(user_id)
    users = data.setdefault("users", {})
    if key not in users:
        users[key] = {
            "behaviorScore": 10,
            "notes": [],
            "hostedMeets": 0,
            "hostAttendanceTotal": 0,
            "rank": "Member",
            "leaderboardEligible": True,
            "crewInviteEligible": False,
        }
        _ft_save(data)
    return data


def _ft_get_user(data: dict, user_id: int) -> dict:
    return data["users"].setdefault(str(user_id), {
        "behaviorScore": 10,
        "notes": [],
        "hostedMeets": 0,
        "hostAttendanceTotal": 0,
        "rank": "Member",
        "leaderboardEligible": True,
        "crewInviteEligible": False,
    })


def _ft_get_strike_count(member: discord.Member) -> int:
    role_ids = {r.id for r in member.roles}
    if STRIKE_3_ROLE_ID in role_ids:
        return 3
    if STRIKE_2_ROLE_ID in role_ids:
        return 2
    if STRIKE_1_ROLE_ID in role_ids:
        return 1
    return 0


def _ft_get_warning_count(member: discord.Member) -> int:
    return 1 if any(r.id == WARNING_1_ROLE_ID for r in member.roles) else 0


def _ft_compute_rank(attendance: int, behavior: int, strikes: int) -> str:
    if strikes >= 3:
        return "Restricted"
    if attendance >= 8 and behavior >= 8 and strikes == 0:
        return "Crew Candidate"
    if attendance >= 5 and behavior >= 7 and strikes <= 1:
        return "Elite"
    if attendance >= 2 and behavior >= 6 and strikes <= 2:
        return "Active"
    return "Member"


async def _ft_refresh_progression(member: discord.Member) -> tuple[str, bool, bool]:
    data = _ft_ensure_user(member.id)
    ft_user = _ft_get_user(data, member.id)

    attendance = int(_rsvp_leaderboard.get(str(member.id), {}).get("attendance_count", 0))
    behavior = int(ft_user.get("behaviorScore", 10) or 10)
    strikes = _ft_get_strike_count(member)

    rank = _ft_compute_rank(attendance, behavior, strikes)
    lb_eligible = strikes < 3
    crew_eligible = (rank == "Crew Candidate" and strikes == 0)

    ft_user["rank"] = rank
    ft_user["leaderboardEligible"] = lb_eligible
    ft_user["crewInviteEligible"] = crew_eligible
    _ft_save(data)

    guild_roles = {r.id: r for r in member.guild.roles}
    controlled = [r for rid in [ACTIVE_ROLE_ID, ELITE_ROLE_ID, CREW_CANDIDATE_ROLE_ID] if rid for r in [guild_roles.get(rid)] if r and r in member.roles]
    to_add_id = {
        "Active": ACTIVE_ROLE_ID,
        "Elite": ELITE_ROLE_ID,
        "Crew Candidate": CREW_CANDIDATE_ROLE_ID,
    }.get(rank, 0)
    to_add = [guild_roles[to_add_id]] if to_add_id and to_add_id in guild_roles else []

    try:
        if controlled:
            await member.remove_roles(*controlled, reason="DIFF tier progression")
        if to_add:
            await member.add_roles(*to_add, reason="DIFF tier progression")
    except Exception:
        pass

    return rank, lb_eligible, crew_eligible


async def _ft_auto_progression_loop() -> None:
    await bot.wait_until_ready()
    while not bot.is_closed():
        await asyncio.sleep(43200)
        guild = bot.get_guild(GUILD_ID)
        if guild:
            for member in guild.members:
                if not member.bot:
                    try:
                        await _ft_refresh_progression(member)
                    except Exception:
                        pass


# =========================
# SEASON SYSTEM
# =========================

try:
    from PIL import Image, ImageDraw, ImageFont
    _PIL_AVAILABLE = True
except Exception:
    _PIL_AVAILABLE = False

_SEASON_BANNER_PATH = os.path.join("diff_data", "season_banner.png")
_SEASON_CAPTION_PATH = os.path.join("diff_data", "season_caption.txt")
_DEJAVU_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_DEJAVU = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def _ig_font(size: int):
    for path in [_DEJAVU_BOLD, _DEJAVU]:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _season_build_ig_caption_full(winners: list[tuple[int, int]], month_label: str) -> str:
    medals = ["🥇", "🥈", "🥉"]
    lines = [
        "🏁 DIFF SEASON RESULTS",
        month_label,
        "",
    ]
    for i, (uid, score) in enumerate(winners[:3]):
        lines.append(f"{medals[i]} <@{uid}> — {score} meets")
    lines += [
        "",
        "Consistency gets noticed.",
        "Attendance matters.",
        "Respect the system and keep showing up.",
        "",
        "#DIFF #DifferentMeets #GTACarMeets #CarMeet #PS5 #GTAOnline",
    ]
    return "\n".join(lines)


def _season_generate_banner(winners: list[tuple[int, int]], month_label: str) -> str | None:
    if not _PIL_AVAILABLE:
        return None
    os.makedirs("diff_data", exist_ok=True)
    try:
        width, height = 1600, 900
        img = Image.new("RGB", (width, height), (12, 12, 12))
        draw = ImageDraw.Draw(img)

        draw.rectangle((0, 0, width, 120), fill=(18, 18, 18))
        draw.rectangle((0, height - 90, width, height), fill=(18, 18, 18))
        draw.rectangle((70, 180, width - 70, 190), fill=(45, 45, 45))
        draw.rectangle((70, 710, width - 70, 720), fill=(45, 45, 45))

        title_font = _ig_font(64)
        sub_font = _ig_font(36)
        winner_font = _ig_font(52)
        small_font = _ig_font(28)

        draw.text((80, 35), "DIFF SEASON WINNERS", font=title_font, fill=(255, 255, 255))
        draw.text((80, 115), month_label, font=sub_font, fill=(190, 190, 190))

        medals_text = ["1ST", "2ND", "3RD"]
        medal_colors = [(255, 215, 0), (192, 192, 192), (205, 127, 50)]
        y_positions = [240, 390, 540]

        for i, (uid, score) in enumerate(winners[:3]):
            y = y_positions[i]
            draw.rounded_rectangle(
                (120, y, width - 120, y + 110),
                radius=22,
                fill=(24, 24, 24),
                outline=(70, 70, 70),
                width=2,
            )
            draw.text((160, y + 22), medals_text[i], font=winner_font, fill=medal_colors[i])
            draw.text((340, y + 22), f"Member {uid}", font=winner_font, fill=(255, 255, 255))
            draw.text((width - 380, y + 32), f"{score} meets", font=sub_font, fill=(220, 220, 220))

        draw.text((80, 750), "Stay active. Stay consistent. Represent DIFF the right way.", font=small_font, fill=(180, 180, 180))
        img.save(_SEASON_BANNER_PATH)
        return _SEASON_BANNER_PATH
    except Exception as e:
        print(f"[Season] Banner generation failed: {e}")
        return None


async def _season_post_ig_content(guild: discord.Guild, winners: list[tuple[int, int]], month_label: str) -> None:
    caption = _season_build_ig_caption_full(winners, month_label)
    try:
        os.makedirs("diff_data", exist_ok=True)
        with open(_SEASON_CAPTION_PATH, "w", encoding="utf-8") as f:
            f.write(caption)
    except Exception:
        pass

    banner_path = _season_generate_banner(winners, month_label)

    channel = guild.get_channel(IG_CONTENT_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        try:
            channel = await guild.fetch_channel(IG_CONTENT_CHANNEL_ID)
        except Exception:
            channel = None
    if not isinstance(channel, discord.TextChannel):
        return

    embed = discord.Embed(
        title="📸 Season Winner Content",
        description="\n".join([
            "**Instagram Caption**",
            "",
            caption[:3800] if len(caption) > 3800 else caption,
        ]),
        color=discord.Color.dark_gold(),
        timestamp=utc_now(),
    )
    embed.set_footer(text="Different Meets • Season IG Content")

    files = []
    if banner_path and os.path.exists(banner_path):
        files.append(discord.File(banner_path, filename="season_banner.png"))
        embed.set_image(url="attachment://season_banner.png")

    try:
        await channel.send(embed=embed, files=files)
    except Exception as e:
        print(f"[Season] IG post failed: {e}")


def _season_load() -> dict:
    try:
        if os.path.exists(SEASON_FILE):
            with open(SEASON_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"history": [], "last_ran_month": None}


def _season_save(data: dict) -> None:
    os.makedirs(os.path.dirname(SEASON_FILE), exist_ok=True)
    with open(SEASON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _season_get_top3() -> list[tuple[int, int]]:
    ranked = sorted(
        _rsvp_leaderboard.values(),
        key=lambda x: int(x.get("attendance_count", 0)),
        reverse=True,
    )[:3]
    return [(int(e["user_id"]), int(e.get("attendance_count", 0))) for e in ranked]


def _season_build_embed(winners: list[tuple[int, int]], month_label: str) -> discord.Embed:
    medals = ["🥇", "🥈", "🥉"]
    lines = [f"{medals[i]} <@{uid}> — **{score}** meet(s)" for i, (uid, score) in enumerate(winners)]
    embed = discord.Embed(
        title=f"🏁 DIFF Season Results — {month_label}",
        description="\n".join(lines) + "\n\nTop performers of the month. Stay active. Stay consistent.",
        color=discord.Color.gold(),
        timestamp=utc_now(),
    )
    embed.set_footer(text="Different Meets • Monthly Season Results")
    return embed



async def _season_give_rewards(guild: discord.Guild, winners: list[tuple[int, int]]) -> None:
    top_role_ids = [TOP1_ROLE_ID, TOP2_ROLE_ID, TOP3_ROLE_ID]
    all_reward_roles = [guild.get_role(rid) for rid in top_role_ids if rid]

    for i, (uid, _) in enumerate(winners):
        member = guild.get_member(uid)
        if not member:
            continue
        try:
            existing = [r for r in all_reward_roles if r and r in member.roles]
            if existing:
                await member.remove_roles(*existing, reason="DIFF season reset")
        except Exception:
            pass
        role = guild.get_role(top_role_ids[i]) if i < len(top_role_ids) else None
        if role:
            try:
                await member.add_roles(role, reason="DIFF season winner")
            except Exception:
                pass


def _season_reset_attendance() -> None:
    for entry in _rsvp_leaderboard.values():
        entry["last_attendance_count"] = int(entry.get("attendance_count", 0))
        entry["attendance_count"] = 0
    _rsvp_save_all()


async def _season_run(guild: discord.Guild) -> None:
    winners = _season_get_top3()
    if not winners:
        return

    now = datetime.now(timezone.utc)
    month_label = now.strftime("%B %Y")

    post_ch_id = SEASON_CHANNEL_ID or LEADERBOARD_CHANNEL_ID
    post_ch = guild.get_channel(post_ch_id)
    if isinstance(post_ch, discord.TextChannel):
        try:
            await post_ch.send(embed=_season_build_embed(winners, month_label))
        except Exception:
            pass

    await _season_give_rewards(guild, winners)

    await _season_post_ig_content(guild, winners, month_label)

    season_data = _season_load()
    season_data.setdefault("history", []).append({
        "month": month_label,
        "date": now.isoformat(),
        "winners": [{"user_id": uid, "score": score} for uid, score in winners],
    })
    season_data["last_ran_month"] = now.strftime("%Y-%m")
    _season_save(season_data)

    _season_reset_attendance()


async def _season_loop() -> None:
    await bot.wait_until_ready()
    while not bot.is_closed():
        await asyncio.sleep(3600)
        try:
            now = datetime.now(timezone.utc)
            if now.day == 1 and now.hour == 12:
                season_data = _season_load()
                current_month = now.strftime("%Y-%m")
                if season_data.get("last_ran_month") != current_month:
                    guild = bot.get_guild(GUILD_ID)
                    if guild:
                        await _season_run(guild)
        except Exception as e:
            print(f"[Season] Loop error: {e}")


# =========================
# HOST RSVP SYSTEM
# =========================

_HRSVP_FILE = os.path.join("diff_data", "diff_host_rsvp.json")
_HRSVP_DAYS = ["Meet 1", "Meet 2", "Meet 3"]


def _hrsvp_load() -> dict:
    if os.path.exists(_HRSVP_FILE):
        try:
            with open(_HRSVP_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {day: {"yes": [], "no": [], "maybe": []} for day in _HRSVP_DAYS}


def _hrsvp_save(data: dict) -> None:
    os.makedirs("diff_data", exist_ok=True)
    with open(_HRSVP_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _hrsvp_reset() -> dict:
    data = {day: {"yes": [], "no": [], "maybe": []} for day in _HRSVP_DAYS}
    _hrsvp_save(data)
    return data


def _hrsvp_build_embed() -> discord.Embed:
    data = _hrsvp_load()
    desc = [
        "📅 **DIFF Host Availability — Meet Schedule**",
        "*Hosts, mark your availability below.*",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━",
    ]
    for day in _HRSVP_DAYS:
        d = data.get(day, {"yes": [], "no": [], "maybe": []})
        yes_tags = " ".join(f"<@{u}>" for u in d["yes"]) or "—"
        no_count = len(d["no"])
        maybe_tags = " ".join(f"<@{u}>" for u in d["maybe"]) or "—"
        desc.append(f"**{day}**")
        desc.append(f"✅ `{len(d['yes'])}` → {yes_tags}")
        if no_count:
            desc.append(f"❌ `{no_count}` unavailable")
        desc.append(f"❓ `{len(d['maybe'])}` → {maybe_tags}")
        desc.append("")
    desc.append("━━━━━━━━━━━━━━━━━━━━━━")
    desc.append("🌐 Convert times: https://hammertime.cyou/en")
    embed = discord.Embed(
        description="\n".join(desc),
        color=discord.Color.dark_gray(),
        timestamp=utc_now(),
    )
    embed.set_footer(text="Different Meets • Host Availability")
    return embed


class HostRSVPView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for day in _HRSVP_DAYS:
            self.add_item(_HostRSVPBtn(day, "yes",   "✅", discord.ButtonStyle.success))
            self.add_item(_HostRSVPBtn(day, "no",    "❌", discord.ButtonStyle.danger))
            self.add_item(_HostRSVPBtn(day, "maybe", "❓", discord.ButtonStyle.secondary))


class _HostRSVPBtn(discord.ui.Button):
    def __init__(self, day: str, choice: str, emoji: str, style: discord.ButtonStyle):
        super().__init__(
            label=day,
            emoji=emoji,
            style=style,
            custom_id=f"hrsvp_{day.replace(' ', '_')}_{choice}",
        )
        self.day = day
        self.choice = choice

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user:
            await interaction.response.defer()
            return
        has_host = any(r.id == HOST_ROLE_ID for r in getattr(interaction.user, "roles", []))
        if not has_host:
            await interaction.response.send_message("Only hosts can use this panel.", ephemeral=True)
            return
        data = _hrsvp_load()
        uid = str(interaction.user.id)
        for c in ("yes", "no", "maybe"):
            lst = data.setdefault(self.day, {"yes": [], "no": [], "maybe": []}).get(c, [])
            if uid in lst:
                lst.remove(uid)
        data[self.day].setdefault(self.choice, []).append(uid)
        _hrsvp_save(data)
        await _hrsvp_update_panel(interaction.client)
        label_map = {"yes": "✅ Available", "no": "❌ Unavailable", "maybe": "❓ Maybe"}
        await interaction.response.send_message(
            f"**{self.day}**: marked as **{label_map[self.choice]}**", ephemeral=True
        )


def _hrsvp_is_rsvp_msg(msg: discord.Message, bot_id: int) -> bool:
    if msg.author.id != bot_id:
        return False
    for row in msg.components:
        for child in row.children:
            cid = getattr(child, "custom_id", "") or ""
            if cid.startswith("hrsvp_"):
                return True
    return False


async def _hrsvp_update_panel(bot_client) -> None:
    channel = bot_client.get_channel(HOST_RSVP_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        try:
            channel = await bot_client.fetch_channel(HOST_RSVP_CHANNEL_ID)
        except Exception:
            return
    if not isinstance(channel, discord.TextChannel):
        return
    embed = _hrsvp_build_embed()
    view = HostRSVPView()
    async for msg in channel.history(limit=25):
        if _hrsvp_is_rsvp_msg(msg, bot_client.user.id):
            try:
                await msg.edit(embed=embed, view=view)
            except Exception:
                pass
            return
    try:
        await channel.send(
            content=f"<@&{HOST_ROLE_ID}>",
            embed=embed,
            view=view,
        )
    except Exception as e:
        print(f"[HostRSVP] Panel send failed: {e}")


# =========================
# AUTO SCHEDULE BUILDER
# =========================

_ASCHED_FILE = os.path.join("diff_data", "diff_auto_schedule.json")
_ASCHED_REFRESH_ID = "diff_auto_sched_refresh"
_ASCHED_REBUILD_ID = "diff_auto_sched_rebuild"
_ASCHED_DEFAULT_TEMPLATE = {day: {"class": "TBD", "time": "TBD"} for day in _HRSVP_DAYS}
_ASCHED_ANNOUNCE_CHANNEL_ID = 1485861257708834836


def _asched_default() -> dict:
    return {
        "days": {
            day: {
                "class": _ASCHED_DEFAULT_TEMPLATE[day]["class"],
                "time": _ASCHED_DEFAULT_TEMPLATE[day]["time"],
                "host_id": None,
                "host_status": "unassigned",
            }
            for day in _HRSVP_DAYS
        },
        "updated_at": None,
    }


def _asched_load() -> dict:
    if os.path.exists(_ASCHED_FILE):
        try:
            with open(_ASCHED_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return _asched_default()


def _asched_save(data: dict) -> None:
    os.makedirs("diff_data", exist_ok=True)
    with open(_ASCHED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _asched_pick_host(day: str, rsvp: dict, assigned_counts: dict) -> tuple[str | None, str]:
    day_data = rsvp.get(day, {})
    yes_hosts = list(day_data.get("yes", []))
    maybe_hosts = list(day_data.get("maybe", []))
    if yes_hosts:
        yes_hosts.sort(key=lambda uid: assigned_counts.get(uid, 0))
        chosen = yes_hosts[0]
        assigned_counts[chosen] = assigned_counts.get(chosen, 0) + 1
        return chosen, "yes"
    if maybe_hosts:
        maybe_hosts.sort(key=lambda uid: assigned_counts.get(uid, 0))
        chosen = maybe_hosts[0]
        assigned_counts[chosen] = assigned_counts.get(chosen, 0) + 1
        return chosen, "maybe"
    return None, "none"


def _asched_build() -> dict:
    rsvp = _hrsvp_load()
    schedule = _asched_load()
    assigned_counts: dict = {}
    for day in _HRSVP_DAYS:
        host_id, host_status = _asched_pick_host(day, rsvp, assigned_counts)
        schedule["days"].setdefault(day, {})["host_id"] = int(host_id) if host_id else None
        schedule["days"][day]["host_status"] = host_status
    schedule["updated_at"] = utc_now().isoformat()
    _asched_save(schedule)
    return schedule


def _asched_build_embed() -> discord.Embed:
    schedule = _asched_load()
    lines = [
        "📋 **DIFF Auto Meet Host Schedule**",
        "*Built automatically from host availability responses.*",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━",
    ]
    for day in _HRSVP_DAYS:
        entry = schedule["days"].get(day, {})
        host_id = entry.get("host_id")
        host_status = entry.get("host_status", "none")
        if host_id:
            host_str = f"<@{host_id}>" + (" *(maybe)*" if host_status == "maybe" else "")
        else:
            host_str = "*No host assigned*"
        lines += [
            f"**{day}**",
            f"🎮 Class: {entry.get('class', 'TBD')}",
            f"🕒 Time: {entry.get('time', 'TBD')}",
            f"👤 Host: {host_str}",
            "",
        ]
    lines += [
        "━━━━━━━━━━━━━━━━━━━━━━",
        "🌐 Time conversion: https://hammertime.cyou/en",
        "⚠ Schedule may be adjusted by leadership.",
    ]
    embed = discord.Embed(
        description="\n".join(lines),
        color=discord.Color.blurple(),
        timestamp=utc_now(),
    )
    embed.set_author(name="Different Meets")
    embed.set_footer(text="DIFF • Auto Host Schedule Builder")
    return embed


class _ASchedAnnounceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Notify", emoji="🔔", style=discord.ButtonStyle.danger, custom_id="diff_asched_announce:notify")
    async def notify_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_staff = any(
            r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID, HOST_ROLE_ID}
            for r in getattr(interaction.user, "roles", [])
        )
        if not is_staff:
            await interaction.response.send_message("Only staff can send schedule notifications.", ephemeral=True)
            return

        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("Could not find guild.", ephemeral=True)
            return

        ping_parts = []
        ps5_role = guild.get_role(PS5_ROLE_ID)
        if ps5_role:
            ping_parts.append(ps5_role.mention)
        notify_role = guild.get_role(NOTIFY_ROLE_ID)
        if notify_role:
            ping_parts.append(notify_role.mention)

        if not ping_parts:
            await interaction.response.send_message("No roles found to ping.", ephemeral=True)
            return

        await interaction.response.send_message("Notification sent.", ephemeral=True)
        try:
            await interaction.channel.send(
                content=" ".join(ping_parts) + " — 📅 **The DIFF Meet Host Schedule has been posted above. Check your meet!**"
            )
        except Exception as e:
            print(f"[AutoSched] Notify ping failed: {e}")


async def _asched_post_finalized(bot_client) -> None:
    channel = bot_client.get_channel(_ASCHED_ANNOUNCE_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        try:
            channel = await bot_client.fetch_channel(_ASCHED_ANNOUNCE_CHANNEL_ID)
        except Exception:
            return
    if not isinstance(channel, discord.TextChannel):
        return

    guild = channel.guild
    ping_parts = []
    ps5_role = guild.get_role(PS5_ROLE_ID)
    if ps5_role:
        ping_parts.append(ps5_role.mention)
    notify_role = guild.get_role(NOTIFY_ROLE_ID)
    if notify_role:
        ping_parts.append(notify_role.mention)
    ping_content = " ".join(ping_parts) if ping_parts else None

    embed = _asched_build_embed()
    embed.title = "📅 DIFF Meet Host Schedule — Finalized"

    try:
        await channel.send(content=ping_content, embed=embed, view=_ASchedAnnounceView())
    except Exception as e:
        print(f"[AutoSched] Announce post failed: {e}")


class AutoScheduleView(discord.ui.View):
    def __init__(self, bot_ref=None):
        super().__init__(timeout=None)
        self._bot_ref = bot_ref

    @discord.ui.button(label="Refresh", emoji="🔄", style=discord.ButtonStyle.secondary, custom_id=_ASCHED_REFRESH_ID)
    async def refresh_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await _asched_update_panel(interaction.client)
        await interaction.response.send_message("Schedule panel refreshed.", ephemeral=True)

    @discord.ui.button(label="Rebuild Schedule", emoji="🧠", style=discord.ButtonStyle.primary, custom_id=_ASCHED_REBUILD_ID)
    async def rebuild_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_staff = any(
            r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID, HOST_ROLE_ID}
            for r in getattr(interaction.user, "roles", [])
        )
        if not is_staff:
            await interaction.response.send_message("Only staff can rebuild the schedule.", ephemeral=True)
            return
        schedule = _asched_build()
        await _asched_update_panel(interaction.client)
        await _asched_post_finalized(interaction.client)
        if interaction.guild:
            rc_meets = []
            for idx, day in enumerate(_HRSVP_DAYS, 1):
                entry = schedule["days"].get(day, {})
                rc_meets.append({
                    "meet_number": idx,
                    "class_name": entry.get("class", "TBD"),
                    "start_time": entry.get("time", "TBD"),
                    "host_id": entry.get("host_id"),
                    "date_text": day,
                    "is_finalized": entry.get("host_id") is not None,
                })
            await _rc_sync_from_schedule(interaction.guild, rc_meets)
        await interaction.response.send_message("Schedule rebuilt and posted to the announcement channel.", ephemeral=True)


def _asched_is_sched_msg(msg: discord.Message, bot_id: int) -> bool:
    if msg.author.id != bot_id:
        return False
    for row in msg.components:
        for child in row.children:
            cid = getattr(child, "custom_id", "") or ""
            if cid in {_ASCHED_REFRESH_ID, _ASCHED_REBUILD_ID}:
                return True
    return False


async def _asched_update_panel(bot_client) -> None:
    channel = bot_client.get_channel(HOST_RSVP_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        try:
            channel = await bot_client.fetch_channel(HOST_RSVP_CHANNEL_ID)
        except Exception:
            return
    if not isinstance(channel, discord.TextChannel):
        return
    embed = _asched_build_embed()
    view = AutoScheduleView(bot_client)
    async for msg in channel.history(limit=25):
        if _asched_is_sched_msg(msg, bot_client.user.id):
            try:
                await msg.edit(embed=embed, view=view)
            except Exception:
                pass
            return
    try:
        await channel.send(embed=embed, view=view)
    except Exception as e:
        print(f"[AutoSched] Panel send failed: {e}")


# =========================
# HOST AUTOMATION DB
# =========================
_HAUTO_DB_PATH = os.path.join("diff_data", "diff_host_automation.db")
_HAUTO_BLACKLIST_POINT_PENALTY = 10
_HAUTO_NO_SHOW_PENALTY = 3
_HAUTO_SUCCESS_POINTS = 5
_HAUTO_ONTIME_BONUS = 2


class _HostAutoDB:
    def __init__(self):
        os.makedirs("diff_data", exist_ok=True)
        self.conn = sqlite3.connect(_HAUTO_DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._setup()

    def _setup(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS blacklist_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER,
                discord_tag TEXT,
                psn TEXT,
                reason TEXT NOT NULL,
                evidence TEXT,
                severity TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                submitted_by_id INTEGER NOT NULL,
                submitted_by_tag TEXT NOT NULL,
                removed_host_role INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS host_points (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                points INTEGER NOT NULL DEFAULT 0,
                penalties INTEGER NOT NULL DEFAULT 0,
                last_updated TEXT NOT NULL,
                PRIMARY KEY (guild_id, user_id)
            )
        """)
        self.conn.commit()

    def add_blacklist(self, guild_id, user_id, discord_tag, psn, reason, evidence,
                      severity, submitted_by_id, submitted_by_tag, removed_host_role):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO blacklist_entries
                (guild_id, user_id, discord_tag, psn, reason, evidence, severity, status,
                 submitted_by_id, submitted_by_tag, removed_host_role, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?)
        """, (guild_id, user_id, discord_tag, psn, reason, evidence, severity,
              submitted_by_id, submitted_by_tag, 1 if removed_host_role else 0,
              datetime.utcnow().isoformat()))
        self.conn.commit()
        return int(cur.lastrowid)

    def is_blacklisted(self, guild_id, user_id):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT 1 FROM blacklist_entries
            WHERE guild_id=? AND user_id=? AND status='active' LIMIT 1
        """, (guild_id, user_id))
        return cur.fetchone() is not None

    def get_active_entry(self, guild_id, user_id):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT * FROM blacklist_entries
            WHERE guild_id=? AND user_id=? AND status='active'
            ORDER BY id DESC LIMIT 1
        """, (guild_id, user_id))
        return cur.fetchone()

    def search(self, guild_id, query):
        like = f"%{query.lower()}%"
        cur = self.conn.cursor()
        cur.execute("""
            SELECT * FROM blacklist_entries
            WHERE guild_id=? AND status='active'
            AND (LOWER(COALESCE(discord_tag,'')) LIKE ?
                 OR LOWER(COALESCE(psn,'')) LIKE ?
                 OR LOWER(COALESCE(reason,'')) LIKE ?
                 OR CAST(COALESCE(user_id,0) AS TEXT) LIKE ?)
            ORDER BY id DESC LIMIT 10
        """, (guild_id, like, like, like, like))
        return cur.fetchall()

    def clear_entry(self, guild_id, entry_id):
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE blacklist_entries SET status='cleared'
            WHERE guild_id=? AND id=? AND status='active'
        """, (guild_id, entry_id))
        self.conn.commit()
        return cur.rowcount > 0

    def adjust_points(self, guild_id, user_id, delta, penalty_delta=0):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO host_points (guild_id, user_id, points, penalties, last_updated)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(guild_id, user_id)
            DO UPDATE SET
                points=points+excluded.points,
                penalties=penalties+excluded.penalties,
                last_updated=excluded.last_updated
        """, (guild_id, user_id, delta, penalty_delta, datetime.utcnow().isoformat()))
        self.conn.commit()
        cur.execute("SELECT points FROM host_points WHERE guild_id=? AND user_id=?",
                    (guild_id, user_id))
        row = cur.fetchone()
        return int(row["points"]) if row else 0

    def top_points(self, guild_id, limit=10):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT user_id, points, penalties FROM host_points
            WHERE guild_id=?
            ORDER BY points DESC, penalties ASC LIMIT ?
        """, (guild_id, limit))
        return cur.fetchall()


_hauto_db = _HostAutoDB()


def host_performance_tier(points: int) -> str:
    if points >= 30:
        return "🟢 Elite Host"
    if points >= 15:
        return "🔵 Active Host"
    if points >= 0:
        return "🟡 Inconsistent"
    return "🔴 At Risk"


async def _hauto_update_leaderboard(guild: discord.Guild) -> None:
    channel = guild.get_channel(LEADERBOARD_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        return
    rows = _hauto_db.top_points(guild.id, 10)
    lines = []
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    for idx, row in enumerate(rows, start=1):
        member = guild.get_member(int(row["user_id"]))
        mention = member.mention if member else f"<@{row['user_id']}>"
        pts = int(row["points"])
        pen = int(row["penalties"])
        tier = host_performance_tier(pts)
        prefix = medals.get(idx, f"**{idx}.**")
        lines.append(f"{prefix} {mention} — {pts} pts | {pen} penalties | {tier}")
    embed = discord.Embed(
        title="🏆 DIFF Host Performance Leaderboard",
        description="\n".join(lines) if lines else "*No host performance data yet.*",
        color=discord.Color.gold(),
        timestamp=datetime.utcnow(),
    )
    embed.set_footer(text="Auto-updated host rankings • DIFF Host System")
    try:
        async for msg in channel.history(limit=10):
            if msg.author.id == bot.user.id and msg.embeds and "Leaderboard" in (msg.embeds[0].title or ""):
                await msg.edit(embed=embed)
                return
        await channel.send(embed=embed)
    except Exception as e:
        print(f"[Leaderboard] update failed: {e}")


# =========================
# HOST CONTROL HUB
# =========================

class _BlacklistModal(discord.ui.Modal, title="🚫 Host Blacklist Submission"):
    user_field = discord.ui.TextInput(label="User (Discord mention, ID, or name)", required=True, max_length=100)
    psn_field = discord.ui.TextInput(label="PSN / GamerTag", required=False, max_length=100)
    reason = discord.ui.TextInput(label="Reason for Blacklisting", style=discord.TextStyle.paragraph, required=True, max_length=1000)
    evidence = discord.ui.TextInput(label="Evidence (links/screenshots)", required=False, max_length=1000)
    severity = discord.ui.TextInput(label="Severity (Warning / Serious / Permanent)", required=True, max_length=50)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        submitter = interaction.user
        if not guild or not isinstance(submitter, discord.Member):
            await interaction.response.send_message("This can only be used in the server.", ephemeral=True)
            return

        raw = self.user_field.value.strip()
        target_member: Optional[discord.Member] = None
        if raw.startswith("<@") and raw.endswith(">"):
            uid_str = "".join(ch for ch in raw if ch.isdigit())
            if uid_str:
                target_member = guild.get_member(int(uid_str))
        elif raw.isdigit():
            target_member = guild.get_member(int(raw))
        else:
            lower = raw.lower()
            for m in guild.members:
                if m.name.lower() == lower or m.display_name.lower() == lower:
                    target_member = m
                    break

        if target_member and _hauto_db.is_blacklisted(guild.id, target_member.id):
            await interaction.response.send_message("That user already has an active blacklist entry.", ephemeral=True)
            return

        removed_host_role = False
        display_text = raw
        user_id_val = None

        if target_member:
            display_text = f"{target_member.mention} ({target_member})"
            user_id_val = target_member.id
            host_role = guild.get_role(HOST_ROLE_ID)
            if host_role and host_role in target_member.roles:
                try:
                    await target_member.remove_roles(host_role, reason="DIFF host blacklist applied")
                    removed_host_role = True
                except Exception:
                    pass

        entry_id = _hauto_db.add_blacklist(
            guild_id=guild.id,
            user_id=user_id_val,
            discord_tag=str(target_member) if target_member else raw,
            psn=self.psn_field.value.strip(),
            reason=self.reason.value.strip(),
            evidence=self.evidence.value.strip(),
            severity=self.severity.value.strip(),
            submitted_by_id=submitter.id,
            submitted_by_tag=str(submitter),
            removed_host_role=removed_host_role,
        )

        if target_member:
            _hauto_db.adjust_points(guild.id, target_member.id, -_HAUTO_BLACKLIST_POINT_PENALTY, 1)

        embed = discord.Embed(
            title=f"🚫 DIFF Host Blacklist Entry #{entry_id}",
            color=discord.Color.red(),
            timestamp=utc_now(),
        )
        embed.add_field(name="👤 User", value=display_text, inline=False)
        embed.add_field(name="🎮 PSN", value=self.psn_field.value.strip() or "Not provided", inline=True)
        embed.add_field(name="📊 Severity", value=self.severity.value.strip(), inline=True)
        embed.add_field(name="📝 Reason", value=self.reason.value.strip()[:1024], inline=False)
        embed.add_field(name="📸 Evidence", value=(self.evidence.value.strip() or "None provided")[:1024], inline=False)
        embed.add_field(name="⚙️ Action Taken", value="Host role removed" if removed_host_role else "Listed / no host role found", inline=False)
        embed.set_footer(text=f"Submitted by {submitter} • Different Meets • Host Blacklist")

        bl_ch = guild.get_channel(BLACKLIST_CHANNEL_ID)
        if isinstance(bl_ch, discord.TextChannel):
            try:
                await bl_ch.send(embed=embed)
            except Exception:
                pass

        log_ch = guild.get_channel(STAFF_LOGS_CHANNEL_ID)
        if isinstance(log_ch, discord.TextChannel):
            try:
                await log_ch.send(f"📌 New blacklist entry #{entry_id} submitted by {submitter.mention}", embed=embed)
            except Exception:
                pass

        await interaction.response.send_message(f"✅ Blacklist entry #{entry_id} submitted successfully.", ephemeral=True)


class _BlacklistSearchModal(discord.ui.Modal, title="🔎 Search Host Blacklist"):
    query = discord.ui.TextInput(label="Name, PSN, Discord ID, or keyword", required=True, max_length=100)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("This can only be used in the server.", ephemeral=True)
            return
        rows = _hauto_db.search(guild.id, self.query.value.strip())
        if not rows:
            await interaction.response.send_message("No active blacklist entries matched that search.", ephemeral=True)
            return
        embed = discord.Embed(
            title="🔎 Host Blacklist Search Results",
            description=f"Showing up to 10 active results for `{self.query.value.strip()}`",
            color=discord.Color.dark_grey(),
            timestamp=utc_now(),
        )
        for row in rows:
            who = row["discord_tag"] or (f"User ID {row['user_id']}" if row["user_id"] else "Unknown")
            embed.add_field(
                name=f"Entry #{row['id']} • {row['severity']}",
                value=(
                    f"**User:** {who}\n"
                    f"**PSN:** {row['psn'] or 'No PSN'}\n"
                    f"**Reason:** {row['reason'][:120]}\n"
                    f"**Date:** {row['created_at'][:10]}"
                ),
                inline=False,
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class _AppealModal(discord.ui.Modal, title="📩 Blacklist Appeal"):
    psn = discord.ui.TextInput(label="Your PSN / Username", required=True, max_length=100)
    reason = discord.ui.TextInput(
        label="Why should this be reviewed?",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000,
    )
    evidence = discord.ui.TextInput(
        label="Evidence (optional)",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=1000,
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        if not guild or not isinstance(user, discord.Member):
            await interaction.response.send_message("This can only be used in the server.", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, attach_files=True, embed_links=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_channels=True, manage_messages=True),
        }
        manager_role = guild.get_role(MANAGER_ROLE_ID)
        if manager_role:
            overwrites[manager_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_messages=True)
        leader_role = guild.get_role(LEADER_ROLE_ID)
        if leader_role:
            overwrites[leader_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_messages=True)

        channel_name = f"appeal-{user.name}".lower().replace(" ", "-")[:90]
        try:
            ticket_ch = await guild.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                reason="DIFF host blacklist appeal ticket",
            )
        except Exception:
            await interaction.response.send_message("Couldn't create appeal ticket channel. Please contact staff directly.", ephemeral=True)
            return

        embed = discord.Embed(
            title="📩 DIFF Host Blacklist Appeal",
            description="A blacklist appeal has been opened for review.",
            color=discord.Color.orange(),
            timestamp=utc_now(),
        )
        embed.add_field(name="👤 User", value=user.mention, inline=False)
        embed.add_field(name="🎮 PSN", value=self.psn.value.strip(), inline=False)
        embed.add_field(name="📋 Appeal Reason", value=self.reason.value.strip(), inline=False)
        embed.add_field(name="📸 Evidence", value=self.evidence.value.strip() or "None provided", inline=False)
        embed.set_footer(text="Different Meets • Blacklist Appeals")

        ping = manager_role.mention if manager_role else "@staff"
        try:
            await ticket_ch.send(content=f"{ping} New blacklist appeal from {user.mention}", embed=embed)
        except Exception:
            pass

        log_ch = guild.get_channel(STAFF_LOGS_CHANNEL_ID)
        if isinstance(log_ch, discord.TextChannel):
            try:
                await log_ch.send(f"📩 Blacklist appeal ticket opened by {user.mention}: {ticket_ch.mention}", embed=embed)
            except Exception:
                pass

        await interaction.response.send_message(f"✅ Your appeal ticket has been created: {ticket_ch.mention}", ephemeral=True)


_HOSTHUB_STATE_FILE = os.path.join("diff_data", "diff_host_hub_state.json")


def _hosthub_get_saved_msg_id() -> int | None:
    try:
        with open(_HOSTHUB_STATE_FILE, "r") as f:
            v = json.load(f).get("message_id")
            return int(v) if v else None
    except Exception:
        return None


def _hosthub_save_msg_id(msg_id: int) -> None:
    os.makedirs("diff_data", exist_ok=True)
    try:
        with open(_HOSTHUB_STATE_FILE, "w") as f:
            json.dump({"message_id": msg_id}, f)
    except Exception:
        pass


def _hosthub_guide_embed() -> discord.Embed:
    e = discord.Embed(title="📘 DIFF Host Guide", description="*Everything a DIFF host needs to run a clean and organized meet.*", color=discord.Color.blurple())
    e.add_field(name="🚗 Before The Meet", value=(
        "• Prepare at least **4 meet locations**\n"
        "• Plan your meet the day before *(route, theme, ideas)*\n"
        "• Promote in advance *(Instagram, PS chats, Discord)*\n"
        "• Check the **blacklist** before starting\n"
        "• Be mindful of who you invite"
    ), inline=False)
    e.add_field(name="⏰ Meet Timeline", value=(
        "**7:30 PM EST** — Crew joins party\n"
        "**7:45 PM EST** — Latest crew join time / Start lobby\n"
        "**7:55 PM EST** — Send early invites\n"
        "**8:00 PM EST** — Open lobby"
    ), inline=False)
    e.add_field(name="👥 Crew Preparation", value=(
        "• Assign roles before the meet\n"
        "• Discuss plans for special moments\n"
        "• Ensure all crew wear DIFF jackets"
    ), inline=False)
    e.add_field(name="📸 During The Meet", value=(
        "• Post lobby picture when full *(names visible)*\n"
        "• Post in **Today's Meet**\n"
        "• Post second poster once live"
    ), inline=False)
    e.add_field(name="✅ Host Standard", value="Stay organized, communicate clearly, and lead properly.", inline=False)
    e.set_footer(text="DIFF Systems • Built for structure • Powered by consistency")
    return e


def _hosthub_roles_embed() -> discord.Embed:
    e = discord.Embed(title="🎯 DIFF Role Assignments", description="*Assign responsibilities to crew members before the meet starts.*", color=discord.Color.blurple())
    e.add_field(name="💬 Message Control", value=(
        "• Sends in-game reminders\n"
        "• Keeps players informed\n"
        "• Examples: *Please join Discord voice.* / *Leave CEO if you're in one.*"
    ), inline=False)
    e.add_field(name="👋 Welcome Team", value=(
        "• Greets players joining\n"
        "• Explains the meet theme\n"
        "• Helps create a clean first impression"
    ), inline=False)
    e.add_field(name="🎨 Theme Check", value=(
        "• Ensures cars match the theme\n"
        "• Keeps the meet clean and consistent\n"
        "• Reminds attendees if adjustments are needed"
    ), inline=False)
    e.add_field(name="🛡️ Support Team", value=(
        "• Manages lobby flow\n"
        "• Assists host with movement between spots\n"
        "• Steps in when the host needs support"
    ), inline=False)
    e.set_footer(text="Use your crew — don't run the meet alone")
    return e


def _hosthub_reminders_embed() -> discord.Embed:
    e = discord.Embed(title="⚠️ DIFF Meet Reminders", description="*Important things every host must remember.*", color=discord.Color.orange())
    e.add_field(name="Reminder List", value=(
        "• Prepare your meet in advance\n"
        "• Always check the blacklist\n"
        "• Be careful who you invite\n"
        "• Use your crew properly\n"
        "• Communicate with your team\n"
        "• Keep promotion consistent\n"
        "• Ensure crew jackets are worn\n"
        "• Stay in control of your meet"
    ), inline=False)
    e.set_footer(text="A clean meet starts with a prepared host")
    return e


def _hosthub_checklist_embed() -> discord.Embed:
    e = discord.Embed(title="📝 DIFF Host Checklist", description="*Quick checklist before and during your meet.*", color=discord.Color.green())
    e.add_field(name="✅ Before The Meet", value=(
        "✔ 4 spots prepared\n✔ Theme decided\n✔ Roles assigned\n"
        "✔ Blacklist checked\n✔ Meet promoted\n✔ Crew in party by 7:30\n"
        "✔ Lobby started by 7:45\n✔ Invites sent by 7:55\n"
        "✔ Lobby open by 8:00\n✔ Crew jackets confirmed"
    ), inline=False)
    e.add_field(name="✅ During The Meet", value=(
        "✔ Welcome players\n✔ Remind theme\n✔ Keep chat active\n"
        "✔ Enforce theme\n✔ Post lobby photo\n"
        "✔ Post in Today's Meet\n✔ Post second poster"
    ), inline=False)
    e.set_footer(text="Stay sharp. Stay organized.")
    return e


def _hosthub_blacklist_embed() -> discord.Embed:
    e = discord.Embed(title="🚫 DIFF Blacklist Reminder", description="*Always review the blacklist before hosting.*", color=discord.Color.red())
    e.add_field(name="Blacklist Rules", value=(
        "• Do **NOT** invite blacklisted players\n"
        "• Check the blacklist before opening lobby\n"
        "• If unsure, ask staff before inviting\n"
        "• Keep the meet safe and controlled"
    ), inline=False)
    e.add_field(name="Host Accountability", value="Failure to follow blacklist rules may result in host penalties.", inline=False)
    e.set_footer(text="Review restrictions before inviting")
    return e


def _hosthub_build_embed() -> discord.Embed:
    embed = discord.Embed(
        title="📍 DIFF Host Control Hub",
        description=(
            "*The all-in-one host hub for DIFF meet leaders.*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "**📘 Host Guide** — Full host rules and expectations\n"
            "**🎯 Role Assignments** — Crew job breakdown\n"
            "**⚠️ Meet Reminders** — Important host reminders\n"
            "**📝 Host Checklist** — Quick prep checklist\n"
            "**🚫 Blacklist Check** — Review restrictions before inviting\n"
            "**🔴 Submit Blacklist** — Report a host violation *(staff only)*\n"
            "**📊 View Blacklist** — Browse all blacklist records\n"
            "**📩 Appeal Blacklist** — Submit an appeal for review\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Stay organized. Lead properly. Represent DIFF the right way.\n\n"
            "— **Different Meets**"
        ),
        color=discord.Color.blurple(),
    )
    embed.set_footer(text="DIFF Host System • Stay prepared • Lead properly • Keep meets clean")
    return embed


class HostHubView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # ── Row 0: reference guides ──
    @discord.ui.button(label="Host Guide", emoji="📘", style=discord.ButtonStyle.primary, custom_id="diff_host_hub:host_guide", row=0)
    async def host_guide_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embed=_hosthub_guide_embed(), ephemeral=True)

    @discord.ui.button(label="Role Assignments", emoji="🎯", style=discord.ButtonStyle.primary, custom_id="diff_host_hub:role_assignments", row=0)
    async def role_assignments_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embed=_hosthub_roles_embed(), ephemeral=True)

    @discord.ui.button(label="Meet Reminders", emoji="⚠️", style=discord.ButtonStyle.secondary, custom_id="diff_host_hub:meet_reminders", row=0)
    async def meet_reminders_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embed=_hosthub_reminders_embed(), ephemeral=True)

    @discord.ui.button(label="Host Checklist", emoji="📝", style=discord.ButtonStyle.success, custom_id="diff_host_hub:host_checklist", row=0)
    async def host_checklist_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embed=_hosthub_checklist_embed(), ephemeral=True)

    @discord.ui.button(label="Blacklist Check", emoji="🚫", style=discord.ButtonStyle.secondary, custom_id="diff_host_hub:blacklist_check", row=0)
    async def blacklist_check_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        bl_view = discord.ui.View()
        bl_view.add_item(discord.ui.Button(
            label="Open Blacklist",
            style=discord.ButtonStyle.link,
            url=f"https://discord.com/channels/850386896509337710/{BLACKLIST_CHANNEL_ID}",
            emoji="🔗",
        ))
        await interaction.response.send_message(embed=_hosthub_blacklist_embed(), view=bl_view, ephemeral=True)

    # ── Row 1: blacklist actions ──
    @discord.ui.button(label="Submit Blacklist", emoji="🔴", style=discord.ButtonStyle.danger, custom_id="diff_host_hub:submit_blacklist", row=1)
    async def submit_blacklist_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_staff = any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID, HOST_ROLE_ID} for r in getattr(interaction.user, "roles", []))
        if not is_staff:
            await interaction.response.send_message("Only staff can submit blacklist entries.", ephemeral=True)
            return
        await interaction.response.send_modal(_BlacklistModal())

    @discord.ui.button(label="Search Blacklist", emoji="🔎", style=discord.ButtonStyle.secondary, custom_id="diff_host_hub:search_blacklist", row=1)
    async def search_blacklist_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(_BlacklistSearchModal())

    @discord.ui.button(label="View Blacklist", emoji="📊", style=discord.ButtonStyle.secondary, custom_id="diff_host_hub:view_blacklist", row=1)
    async def view_blacklist_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"🔗 **Blacklist Records:**\nhttps://discord.com/channels/850386896509337710/{BLACKLIST_CHANNEL_ID}",
            ephemeral=True,
        )

    @discord.ui.button(label="Appeal Blacklist", emoji="📩", style=discord.ButtonStyle.primary, custom_id="diff_host_hub:appeal_blacklist", row=1)
    async def appeal_blacklist_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(_AppealModal())


async def _hosthub_post_or_refresh() -> None:
    channel = bot.get_channel(HOST_HUB_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        try:
            channel = await bot.fetch_channel(HOST_HUB_CHANNEL_ID)
        except Exception:
            return
    if not isinstance(channel, discord.TextChannel):
        return
    embed = _hosthub_build_embed()
    view = HostHubView()
    saved_id = _hosthub_get_saved_msg_id()
    if saved_id:
        try:
            old = await channel.fetch_message(saved_id)
            await old.edit(embed=embed, view=view)
            return
        except Exception:
            pass
    async for msg in channel.history(limit=20):
        if msg.author.id == bot.user.id:
            for row in msg.components:
                for child in row.children:
                    if getattr(child, "custom_id", "").startswith("diff_host_hub:"):
                        try:
                            await msg.edit(embed=embed, view=view)
                            _hosthub_save_msg_id(msg.id)
                        except Exception:
                            pass
                        return
    try:
        new_msg = await channel.send(embed=embed, view=view)
        _hosthub_save_msg_id(new_msg.id)
    except Exception as e:
        print(f"[HostHub] Post failed: {e}")


@bot.command(name="hosthub")
async def _hosthub_cmd(ctx: commands.Context):
    is_staff = any(
        r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID, HOST_ROLE_ID}
        for r in ctx.author.roles
    )
    if not is_staff:
        return
    try:
        await ctx.message.delete()
    except Exception:
        pass
    await _hosthub_post_or_refresh()


@bot.command(name="blacklistsearch")
async def _cmd_blacklistsearch(ctx: commands.Context, *, query: str = ""):
    is_staff = any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID, HOST_ROLE_ID} for r in ctx.author.roles)
    if not is_staff:
        return
    if not query:
        await ctx.send("Usage: `!blacklistsearch <name/psn/id/keyword>`", delete_after=10)
        return
    rows = _hauto_db.search(ctx.guild.id, query)
    if not rows:
        await ctx.send("No active blacklist entries matched that search.", delete_after=15)
        return
    embed = discord.Embed(
        title="🔎 Host Blacklist Search Results",
        description=f"Showing up to 10 active results for `{query}`",
        color=discord.Color.dark_grey(),
        timestamp=datetime.utcnow(),
    )
    for row in rows:
        who = row["discord_tag"] or (f"User ID {row['user_id']}" if row["user_id"] else "Unknown")
        embed.add_field(
            name=f"Entry #{row['id']} • {row['severity']}",
            value=(
                f"**User:** {who}\n"
                f"**PSN:** {row['psn'] or 'No PSN'}\n"
                f"**Reason:** {row['reason'][:120]}\n"
                f"**Date:** {row['created_at'][:10]}"
            ),
            inline=False,
        )
    await ctx.send(embed=embed)


@bot.command(name="clearblacklist")
async def _cmd_clearblacklist(ctx: commands.Context, entry_id: int = 0):
    is_staff = any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID} for r in ctx.author.roles)
    if not is_staff:
        return
    if not entry_id:
        await ctx.send("Usage: `!clearblacklist <entry_id>`", delete_after=10)
        return
    success = _hauto_db.clear_entry(ctx.guild.id, entry_id)
    if not success:
        await ctx.send(f"Active blacklist entry #{entry_id} not found.", delete_after=10)
        return
    embed = discord.Embed(
        title="✅ Host Blacklist Cleared",
        description=f"Blacklist entry #{entry_id} has been cleared.",
        color=discord.Color.green(),
        timestamp=datetime.utcnow(),
    )
    embed.set_footer(text=f"Cleared by {ctx.author}")
    log_ch = ctx.guild.get_channel(STAFF_LOGS_CHANNEL_ID)
    if isinstance(log_ch, discord.TextChannel):
        try:
            await log_ch.send(content=f"Handled by {ctx.author.mention}", embed=embed)
        except Exception:
            pass
    await ctx.send(embed=embed)


@bot.command(name="hostreport")
async def _cmd_hostreport(ctx: commands.Context, host: Optional[discord.Member] = None, *, args: str = ""):
    is_staff = any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID} for r in ctx.author.roles)
    if not is_staff:
        return
    if not host:
        await ctx.send(
            "Usage: `!hostreport @host <meet_name> <attendance> <success|late|no-show> [notes]`\n"
            "Example: `!hostreport @SpMex0322 Meet1 45 success Great meet`",
            delete_after=20,
        )
        return
    parts = args.split(None, 3)
    if len(parts) < 3:
        await ctx.send("Usage: `!hostreport @host <meet_name> <attendance> <status> [notes]`", delete_after=15)
        return
    meet_name = parts[0]
    try:
        attendance = int(parts[1])
    except ValueError:
        await ctx.send("Attendance must be a number.", delete_after=10)
        return
    status = parts[2].lower()
    notes = parts[3] if len(parts) > 3 else None

    point_change = 0
    penalty_change = 0
    if status == "success":
        point_change = _HAUTO_SUCCESS_POINTS
        result_label = "✅ Hosted Successfully"
    elif status == "late":
        point_change = _HAUTO_SUCCESS_POINTS - 1
        result_label = "⏰ Hosted Late"
    elif status == "no-show":
        point_change = -_HAUTO_NO_SHOW_PENALTY
        penalty_change = 1
        result_label = "❌ No-Show"
    else:
        result_label = f"ℹ️ {status}"

    new_total = _hauto_db.adjust_points(ctx.guild.id, host.id, point_change, penalty_change)

    embed = discord.Embed(
        title="📊 DIFF Host Report",
        color=discord.Color.green() if point_change >= 0 else discord.Color.orange(),
        timestamp=datetime.utcnow(),
    )
    embed.add_field(name="Host", value=host.mention, inline=False)
    embed.add_field(name="Meet", value=meet_name, inline=True)
    embed.add_field(name="Attendance", value=str(attendance), inline=True)
    embed.add_field(name="Result", value=result_label, inline=True)
    embed.add_field(name="Points Change", value=f"{point_change:+}", inline=True)
    embed.add_field(name="New Total", value=f"{new_total} pts | {host_performance_tier(new_total)}", inline=True)
    if notes:
        embed.add_field(name="Notes", value=notes, inline=False)
    embed.set_footer(text=f"Submitted by {ctx.author}")

    log_ch = ctx.guild.get_channel(STAFF_LOGS_CHANNEL_ID)
    if isinstance(log_ch, discord.TextChannel):
        try:
            await log_ch.send(embed=embed)
        except Exception:
            pass

    await ctx.send(embed=embed)
    await _hauto_update_leaderboard(ctx.guild)


@bot.command(name="hostpoints")
async def _cmd_hostpoints(ctx: commands.Context, user: Optional[discord.Member] = None, points: int = 0):
    is_staff = any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID} for r in ctx.author.roles)
    if not is_staff:
        return
    if not user:
        await ctx.send("Usage: `!hostpoints @user <+/- amount>`", delete_after=10)
        return
    new_total = _hauto_db.adjust_points(ctx.guild.id, user.id, points)
    await ctx.send(
        f"✅ Updated {user.mention}. Points: **{new_total}** | Tier: **{host_performance_tier(new_total)}**"
    )
    await _hauto_update_leaderboard(ctx.guild)


# =========================
# HOST FLOW SYSTEM
# =========================

_HOSTFLOW_STATE_FILE = os.path.join("diff_data", "diff_host_flow_state.json")
_HOSTFLOW_COOLDOWNS: dict[int, float] = {}
_HOSTFLOW_COOLDOWN_SECS = 5
_HOSTFLOW_ALLOWED_ROLES = {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID, HOST_ROLE_ID}
_HOSTFLOW_PING_ON_START = True
_HOSTFLOW_PING_ON_END = False
_HOSTFLOW_SMART_PING_COOLDOWN = 3600  # seconds (60 min)
_HOSTFLOW_GUILD_PING_TIMES: dict[int, float] = {}


def _hostflow_get_saved_msg_id() -> int | None:
    try:
        with open(_HOSTFLOW_STATE_FILE, "r") as f:
            v = json.load(f).get("message_id")
            return int(v) if v else None
    except Exception:
        return None


def _hostflow_save_msg_id(msg_id: int) -> None:
    os.makedirs("diff_data", exist_ok=True)
    try:
        with open(_HOSTFLOW_STATE_FILE, "w") as f:
            json.dump({"message_id": msg_id}, f)
    except Exception:
        pass


def _hostflow_role_ping(guild: discord.Guild) -> str:
    parts = []
    for rid in (PS5_ROLE_ID, NOTIFY_ROLE_ID):
        role = guild.get_role(rid)
        if role:
            parts.append(role.mention)
    return " ".join(parts)


def _hostflow_start_msg(host_mention: str, guild: discord.Guild) -> str:
    ping = _hostflow_role_ping(guild)
    return (
        f"{ping}\n\n"
        "🔱 __**DIFF Meet Welcome**__ 🔱\n\n"
        "*Hello everyone, welcome to another DIFF Meet.*\n\n"
        f"*Tonight's host is {host_mention}.*\n\n"
        "*If you have any questions or need help during the meet, please contact the host.*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🚗 **Meet Status**\n"
        "*We will be heading out shortly — please get your vehicles ready and positioned properly.*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚠️ **Important Notice**\n"
        "*If you have any problems with another player during the meet, please create a ticket in the DIFF Discord so DIFF Management can handle it properly.*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🚫 __**Meet Rules**__ 🚫\n\n"
        "**☞ No weapons out at any time**\n"
        "**☞ During cruises: single file only — no passing or overtaking**\n"
        "**☞ No harassment, bullying, or unnecessary negativity**\n"
        "**☞ No revving or excessive honking during the meet**\n"
        "**☞ Stance vehicles away from the meet location so police are not attracted**\n"
        "**☞ Stay in Discord voice chat so you know what is going on**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "*Please follow all rules so we can keep the meet clean, realistic, and enjoyable for everyone.*\n\n"
        "— **Different Meets**"
    )


def _hostflow_end_msg(guild: discord.Guild) -> str:
    ping = _hostflow_role_ping(guild)
    return (
        f"{ping}\n\n"
        "📌 __**DIFF Meet Ending**__ 📌\n\n"
        "*Alright everyone, tonight's DIFF Meet has now come to an end.*\n\n"
        "*Thank you all for attending and being a part of tonight's meet.*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💬 **Feedback**\n"
        "*If you enjoyed the meet, please leave feedback in our Discord server.*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📲 **Stay Connected**\n"
        "*Follow us on all platforms:*\n"
        "**@diff_meets** — Instagram, YouTube, TikTok\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🚗 **Interested in Joining DIFF?**\n"
        "*Complete the Crew Application and message a DIFF Crew Manager for more information.*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎮 **Lobby Status**\n"
        "*The lobby is now turning into a chill lobby.*\n"
        "🚫 *No killing — anyone killing will be blocked.*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🌙 *Have a great night, and we hope to see you at the next DIFF Meet.*\n\n"
        "— **Different Meets**"
    )


def _hostflow_voice_script(host_mention: str) -> str:
    return (
        "🎤 __**Host Voice Script**__ 🎤\n\n"
        "**— Start Meet —**\n"
        f"Welcome everyone to tonight's DIFF Meet. I'm {host_mention}, and I'll be hosting tonight.\n\n"
        "We'll be heading out shortly, so please get your cars ready.\n\n"
        "Quick reminder: no weapons, no revving, no honking, no disrespect, and during cruises stay single file with no passing.\n\n"
        "Stay in Discord voice chat so you know what's going on. "
        "If you have any issues during the meet, please open a ticket in the Discord.\n\n"
        "Let's have a clean and smooth meet.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "**— End Meet —**\n"
        "Alright everyone, tonight's meet is now over.\n\n"
        "Thank you all for coming out and being part of DIFF tonight.\n\n"
        "If you enjoyed the meet, please leave us feedback in the Discord and check out our socials at @diff_meets.\n\n"
        "If you're interested in joining DIFF, fill out the crew application and message a DIFF Crew Manager.\n\n"
        "The lobby is now a chill lobby — no killing. Have a great night, everyone."
    )


def _hostflow_log_msg(host_mention: str) -> str:
    now = utc_now()
    return (
        "📊 __**DIFF Host Log**__ 📊\n\n"
        f"**Host:** {host_mention}\n"
        f"**Action:** Meet Ended\n"
        f"**Logged At:** {now.strftime('%I:%M %p')} UTC | {now.strftime('%b %d, %Y')}\n\n"
        "— **Different Meets**"
    )


def _hostflow_panel_embed() -> discord.Embed:
    e = discord.Embed(
        title="📌 DIFF Host Flow System",
        description=(
            "*Use the buttons below to manage your meet flow professionally.*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔱 **Start Meet** — Posts the official DIFF welcome speech\n"
            "📌 **End Meet** — Posts the ending speech and logs your host activity\n"
            "🎤 **Voice Script** — Shows the host scripts to use during meets\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "*Keep hosting clean, organized, and professional.*\n\n"
            "— **Different Meets**"
        ),
        color=discord.Color.blurple(),
    )
    e.set_footer(text="DIFF Host Flow • Stay prepared • Lead properly")
    return e


class HostFlowView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def _check_host(self, interaction: discord.Interaction) -> bool:
        roles = getattr(interaction.user, "roles", [])
        if not any(r.id in _HOSTFLOW_ALLOWED_ROLES for r in roles):
            await interaction.response.send_message("Only hosts can use this panel.", ephemeral=True)
            return False
        now = __import__("asyncio").get_event_loop().time()
        last = _HOSTFLOW_COOLDOWNS.get(interaction.user.id, 0)
        if now - last < _HOSTFLOW_COOLDOWN_SECS:
            remaining = round(_HOSTFLOW_COOLDOWN_SECS - (now - last), 1)
            await interaction.response.send_message(f"Please wait {remaining}s before pressing again.", ephemeral=True)
            return False
        _HOSTFLOW_COOLDOWNS[interaction.user.id] = now
        return True

    @discord.ui.button(label="Start Meet", emoji="🔱", style=discord.ButtonStyle.success, custom_id="diff_hostflow:start_meet")
    async def start_meet_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_host(interaction):
            return
        ch = interaction.client.get_channel(MEET_FLOW_CHANNEL_ID)
        if not isinstance(ch, discord.TextChannel):
            await interaction.response.send_message("Meet channel not found.", ephemeral=True)
            return
        await ch.send(
            _hostflow_start_msg(interaction.user.mention, interaction.guild),
            allowed_mentions=discord.AllowedMentions(roles=True),
        )
        await interaction.response.send_message(f"✅ Welcome speech posted in {ch.mention}.", ephemeral=True)

    @discord.ui.button(label="End Meet", emoji="📌", style=discord.ButtonStyle.danger, custom_id="diff_hostflow:end_meet")
    async def end_meet_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_host(interaction):
            return
        ch = interaction.client.get_channel(MEET_FLOW_CHANNEL_ID)
        if not isinstance(ch, discord.TextChannel):
            await interaction.response.send_message("Meet channel not found.", ephemeral=True)
            return
        await ch.send(
            _hostflow_end_msg(interaction.guild),
            allowed_mentions=discord.AllowedMentions(roles=True),
        )
        log_ch = interaction.client.get_channel(STAFF_LOGS_CHANNEL_ID)
        if isinstance(log_ch, discord.TextChannel):
            await log_ch.send(_hostflow_log_msg(interaction.user.mention))
        await interaction.response.send_message(f"✅ Ending speech posted in {ch.mention} and activity logged.", ephemeral=True)

    @discord.ui.button(label="Voice Script", emoji="🎤", style=discord.ButtonStyle.primary, custom_id="diff_hostflow:voice_script")
    async def voice_script_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_host(interaction):
            return
        await interaction.response.send_message(_hostflow_voice_script(interaction.user.mention), ephemeral=True)

    @discord.ui.button(label="Request Feedback", emoji="📝", style=discord.ButtonStyle.secondary, custom_id="diff_hostflow:request_feedback", row=1)
    async def request_feedback_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_host(interaction):
            return
        ch = interaction.client.get_channel(MEET_FLOW_CHANNEL_ID)
        if not isinstance(ch, discord.TextChannel):
            await interaction.response.send_message("Meet flow channel not found.", ephemeral=True)
            return
        embed = discord.Embed(
            title="📝 Leave Your Meet Feedback",
            description=(
                f"**{interaction.user.display_name}** is requesting feedback from tonight's meet!\n\n"
                "Let us know how it went — your thoughts help us improve every event.\n\n"
                "▢ Rate the meet experience\n"
                "▢ Comment on the host's performance\n"
                "▢ Share suggestions for next time"
            ),
            color=0x1F6FEB,
        )
        embed.set_footer(text="Different Meets • Meet Feedback • All responses are appreciated")
        await ch.send(embed=embed, view=HostFeedbackRequestView())
        await interaction.response.send_message(f"✅ Feedback request posted in {ch.mention}.", ephemeral=True)


class HostFeedbackRequestView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Submit Feedback",
        style=discord.ButtonStyle.primary,
        custom_id="diff_hostflow_feedback_submit",
        emoji="📝",
    )
    async def submit_feedback(self, interaction: discord.Interaction, button: discord.ui.Button):
        from cogs.diff_feedback_system import FeedbackModal
        cog = interaction.client.cogs.get("FeedbackSystem")
        if cog is None:
            await interaction.response.send_message(
                "Feedback system is temporarily unavailable.", ephemeral=True
            )
            return
        await interaction.response.send_modal(FeedbackModal(cog))


async def _hostflow_post_or_refresh() -> None:
    channel = bot.get_channel(HOST_HUB_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        try:
            channel = await bot.fetch_channel(HOST_HUB_CHANNEL_ID)
        except Exception:
            return
    if not isinstance(channel, discord.TextChannel):
        return
    embed = _hostflow_panel_embed()
    view = HostFlowView()
    saved_id = _hostflow_get_saved_msg_id()
    if saved_id:
        try:
            old = await channel.fetch_message(saved_id)
            await old.edit(embed=embed, view=view)
            return
        except Exception:
            pass
    async for msg in channel.history(limit=25):
        if msg.author.id == bot.user.id:
            for row in msg.components:
                for child in row.children:
                    if getattr(child, "custom_id", "").startswith("diff_hostflow:"):
                        try:
                            await msg.edit(embed=embed, view=view)
                            _hostflow_save_msg_id(msg.id)
                        except Exception:
                            pass
                        return
    try:
        new_msg = await channel.send(embed=embed, view=view)
        _hostflow_save_msg_id(new_msg.id)
    except Exception as e:
        print(f"[HostFlow] Post failed: {e}")


@bot.command(name="hostflow")
async def _hostflow_cmd(ctx: commands.Context):
    if not any(r.id in _HOSTFLOW_ALLOWED_ROLES for r in ctx.author.roles):
        return
    try:
        await ctx.message.delete()
    except Exception:
        pass
    await _hostflow_post_or_refresh()


# =========================
# MOBILE UI PANEL PACK
# =========================

_MOBILE_JOIN_ID    = "diff_mobile_join_refresh"
_MOBILE_HOST_ID    = "diff_mobile_host_refresh"
_MOBILE_HUB_ID     = "diff_mobile_hub_refresh"
_MOBILE_LB_ID      = "diff_mobile_lb_refresh"
_MOBILE_SUPPORT_ID = "diff_mobile_support_refresh"


def _mobile_overview() -> dict:
    data = _rsvp_load_all()
    users = list(data.get("users", {}).values())
    return {
        "tracked": len(users),
        "active": len([u for u in users if int(u.get("attendance_count", 0) or 0) > 0]),
        "attendance_total": sum(int(u.get("attendance_count", 0) or 0) for u in users),
    }


def _mobile_lb_top(limit: int = 5) -> list[tuple[int, int]]:
    data = _rsvp_load_all()
    rows = []
    for uid, stats in data.get("users", {}).items():
        rows.append((int(uid), int(stats.get("attendance_count", 0) or 0)))
    rows.sort(key=lambda x: x[1], reverse=True)
    return rows[:limit]


def _mobile_join_embed() -> discord.Embed:
    e = discord.Embed(
        title="🏁 DIFF Join Hub",
        description="\n".join([
            "Tap below to get started.",
            "",
            "🎮 **PlayStation**",
            "Open your join flow",
            "",
            "📸 Clean builds only",
            "📋 Follow all DIFF rules",
        ]),
        color=discord.Color.dark_gray(),
        timestamp=utc_now(),
    )
    e.set_footer(text="Different Meets • Quick Join")
    return e


def _mobile_host_embed() -> discord.Embed:
    e = discord.Embed(
        title="📅 Host Schedule",
        description="\n".join([
            "Check host planning below.",
            "",
            "✅ Yes = available",
            "❌ No = unavailable",
            "❓ Maybe = possible",
            "",
            "🌐 Hammertime for timezones",
            "https://hammertime.cyou/en",
        ]),
        color=discord.Color.dark_gray(),
        timestamp=utc_now(),
    )
    e.set_footer(text="Different Meets • Host Planning")
    return e


def _mobile_hub_embed() -> discord.Embed:
    stats = _mobile_overview()
    e = discord.Embed(
        title="📊 Crew Hub",
        description="\n".join([
            f"👥 **Tracked**: {stats['tracked']}",
            f"🔥 **Active**: {stats['active']}",
            f"📈 **Total Meets**: {stats['attendance_total']}",
            "",
            "Stay active.",
            "Get noticed.",
        ]),
        color=discord.Color.dark_gray(),
        timestamp=utc_now(),
    )
    e.set_footer(text="Different Meets • Live Stats")
    return e


def _mobile_lb_embed() -> discord.Embed:
    top = _mobile_lb_top(5)
    medals = ["🥇", "🥈", "🥉", "📌", "📌"]
    lines = []
    if top:
        for i, (uid, att) in enumerate(top):
            lines.append(f"{medals[i]} <@{uid}>")
            lines.append(f"   {att} meet(s)")
    else:
        lines.append("No leaderboard data yet.")
    e = discord.Embed(
        title="🏆 Leaderboard",
        description="\n".join(lines),
        color=discord.Color.dark_gray(),
        timestamp=utc_now(),
    )
    e.set_footer(text="Different Meets • Top Members")
    return e


def _mobile_support_embed() -> discord.Embed:
    e = discord.Embed(
        title="🛡️ Support Center",
        description="\n".join([
            "Need help with something?",
            "",
            "🚨 Report an issue",
            "⚠ Submit an appeal",
            "🚗 Get car meet support",
            "📩 Apply to DIFF",
            "",
            "Open a ticket in the right channel.",
        ]),
        color=discord.Color.dark_gray(),
        timestamp=utc_now(),
    )
    e.set_footer(text="Different Meets • Help Panel")
    return e


async def _mobile_upsert(bot_client, channel_id: int, embed: discord.Embed, custom_id: str, label: str, emoji: str) -> None:
    if not channel_id:
        return
    channel = bot_client.get_channel(channel_id)
    if not isinstance(channel, discord.TextChannel):
        try:
            channel = await bot_client.fetch_channel(channel_id)
        except Exception:
            return
    if not isinstance(channel, discord.TextChannel):
        return
    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(label=label, emoji=emoji, style=discord.ButtonStyle.secondary, custom_id=custom_id))
    async for msg in channel.history(limit=20):
        if msg.author.id == bot_client.user.id:
            for row in msg.components:
                for child in row.children:
                    if getattr(child, "custom_id", None) == custom_id:
                        try:
                            await msg.edit(embed=embed, view=view)
                        except Exception:
                            pass
                        return
    try:
        await channel.send(embed=embed, view=view)
    except Exception as e:
        print(f"[MobileUI] send failed ({custom_id}): {e}")


class _MobileRefreshView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Refresh Join", emoji="🏁", style=discord.ButtonStyle.secondary, custom_id=_MOBILE_JOIN_ID)
    async def refresh_join(self, interaction: discord.Interaction, button: discord.ui.Button):
        await _mobile_upsert(interaction.client, JOIN_MEETS_CHANNEL_ID, _mobile_join_embed(), _MOBILE_JOIN_ID, "Refresh Join", "🏁")
        await interaction.response.send_message("Join panel refreshed.", ephemeral=True)

    @discord.ui.button(label="Refresh Host", emoji="📅", style=discord.ButtonStyle.secondary, custom_id=_MOBILE_HOST_ID)
    async def refresh_host(self, interaction: discord.Interaction, button: discord.ui.Button):
        await _mobile_upsert(interaction.client, HOST_RSVP_CHANNEL_ID, _mobile_host_embed(), _MOBILE_HOST_ID, "Refresh Host", "📅")
        await interaction.response.send_message("Host panel refreshed.", ephemeral=True)

    @discord.ui.button(label="Refresh Hub", emoji="📊", style=discord.ButtonStyle.secondary, custom_id=_MOBILE_HUB_ID)
    async def refresh_hub(self, interaction: discord.Interaction, button: discord.ui.Button):
        await _mobile_upsert(interaction.client, LEADERBOARD_CHANNEL_ID, _mobile_hub_embed(), _MOBILE_HUB_ID, "Refresh Hub", "📊")
        await interaction.response.send_message("Crew hub refreshed.", ephemeral=True)

    @discord.ui.button(label="Refresh LB", emoji="🏆", style=discord.ButtonStyle.secondary, custom_id=_MOBILE_LB_ID)
    async def refresh_lb(self, interaction: discord.Interaction, button: discord.ui.Button):
        await _mobile_upsert(interaction.client, LEADERBOARD_CHANNEL_ID, _mobile_lb_embed(), _MOBILE_LB_ID, "Refresh Top", "🏆")
        await interaction.response.send_message("Leaderboard refreshed.", ephemeral=True)

    @discord.ui.button(label="Refresh Support", emoji="🛡️", style=discord.ButtonStyle.secondary, custom_id=_MOBILE_SUPPORT_ID)
    async def refresh_support(self, interaction: discord.Interaction, button: discord.ui.Button):
        await _mobile_upsert(interaction.client, SUPPORT_TICKETS_CHANNEL_ID, _mobile_support_embed(), _MOBILE_SUPPORT_ID, "Refresh Help", "🛡️")
        await interaction.response.send_message("Support panel refreshed.", ephemeral=True)


@bot.command(name="postmobilejoin")
async def _pmobile_join(ctx: commands.Context):
    if not any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID} for r in ctx.author.roles):
        return
    try:
        await ctx.message.delete()
    except Exception:
        pass
    await _mobile_upsert(ctx.bot, JOIN_MEETS_CHANNEL_ID, _mobile_join_embed(), _MOBILE_JOIN_ID, "Refresh Join", "🏁")
    await ctx.send("✅ Mobile join panel posted.", delete_after=5)


@bot.command(name="postmobilehost")
async def _pmobile_host(ctx: commands.Context):
    if not any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID} for r in ctx.author.roles):
        return
    try:
        await ctx.message.delete()
    except Exception:
        pass
    await _mobile_upsert(ctx.bot, HOST_RSVP_CHANNEL_ID, _mobile_host_embed(), _MOBILE_HOST_ID, "Refresh Host", "📅")
    await ctx.send("✅ Mobile host panel posted.", delete_after=5)


@bot.command(name="postmobilehub")
async def _pmobile_hub(ctx: commands.Context):
    if not any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID} for r in ctx.author.roles):
        return
    try:
        await ctx.message.delete()
    except Exception:
        pass
    await _mobile_upsert(ctx.bot, LEADERBOARD_CHANNEL_ID, _mobile_hub_embed(), _MOBILE_HUB_ID, "Refresh Hub", "📊")
    await ctx.send("✅ Mobile crew hub panel posted.", delete_after=5)


@bot.command(name="postmobileleaderboard")
async def _pmobile_lb(ctx: commands.Context):
    if not any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID} for r in ctx.author.roles):
        return
    try:
        await ctx.message.delete()
    except Exception:
        pass
    await _mobile_upsert(ctx.bot, LEADERBOARD_CHANNEL_ID, _mobile_lb_embed(), _MOBILE_LB_ID, "Refresh Top", "🏆")
    await ctx.send("✅ Mobile leaderboard panel posted.", delete_after=5)


@bot.command(name="postmobilesupport")
async def _pmobile_support(ctx: commands.Context):
    if not any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID} for r in ctx.author.roles):
        return
    try:
        await ctx.message.delete()
    except Exception:
        pass
    await _mobile_upsert(ctx.bot, SUPPORT_TICKETS_CHANNEL_ID, _mobile_support_embed(), _MOBILE_SUPPORT_ID, "Refresh Help", "🛡️")
    await ctx.send("✅ Mobile support panel posted.", delete_after=5)


def _ft_build_suggestions_embed(guild: discord.Guild) -> discord.Embed:
    data = _ft_load()
    promotion_lines, inactive_lines, best_host_lines = [], [], []

    for uid, ft_user in data.get("users", {}).items():
        member = guild.get_member(int(uid))
        if not member:
            continue
        attendance = int(_rsvp_leaderboard.get(uid, {}).get("attendance_count", 0))
        behavior = int(ft_user.get("behaviorScore", 10) or 10)
        strikes = _ft_get_strike_count(member)
        rank = _ft_compute_rank(attendance, behavior, strikes)
        if rank in ("Elite", "Crew Candidate") and strikes <= 1:
            promotion_lines.append(f"• <@{uid}> — **{rank}** | Att: {attendance} | Behavior: {behavior}/10")

    for uid, entry in _rsvp_leaderboard.items():
        if int(entry.get("attendance_count", 0)) == 0:
            inactive_lines.append(f"• <@{uid}>")

    hosts = []
    for uid, h in data.get("hosts", {}).items():
        hosted = int(h.get("hostedMeets", 0) or 0)
        total = int(h.get("hostAttendanceTotal", 0) or 0)
        avg = round(total / hosted, 1) if hosted > 0 else 0
        if hosted > 0:
            hosts.append((uid, hosted, total, avg))
    hosts.sort(key=lambda x: (x[2], x[1], x[3]), reverse=True)
    for uid, hosted, total, avg in hosts[:5]:
        best_host_lines.append(f"• <@{uid}> — Hosted: **{hosted}** | Total Att: **{total}** | Avg: **{avg}**")

    rsvp_suggestions = []
    for item in _rsvp_promotions[-10:][::-1]:
        rsvp_suggestions.append(
            f"• <@{item['user_id']}> — {item['current_role']} → **{item['suggested_role']}** | {item.get('attendance_count', 0)} attended"
        )

    embed = discord.Embed(
        title="🧠 DIFF Suggestions",
        description="\n".join([
            "**🏆 Promotion Candidates**",
            *(promotion_lines[:8] or ["• None right now"]),
            "",
            "**📈 RSVP-Based Promotions**",
            *(rsvp_suggestions[:5] or ["• None right now"]),
            "",
            "**📉 Inactive Members**",
            *(inactive_lines[:8] or ["• None right now"]),
            "",
            "**🎤 Best Hosts**",
            *(best_host_lines or ["• None right now"]),
        ]),
        color=discord.Color.blurple(),
        timestamp=utc_now(),
    )
    embed.set_footer(text="Different Meets • Suggestions Panel")
    return embed


class NotifyMeetView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Notify Me For Meets",
        style=discord.ButtonStyle.primary,
        emoji="🔔",
        custom_id="diff_notify_meet_toggle",
    )
    async def toggle_notify(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user if isinstance(interaction.user, discord.Member) else (interaction.guild.get_member(interaction.user.id) if interaction.guild else None)
        if not member or not interaction.guild:
            return await interaction.response.send_message("Could not find your profile.", ephemeral=True)
        role = interaction.guild.get_role(NOTIFY_ROLE_ID)
        if not role:
            return await interaction.response.send_message("Notify role not configured.", ephemeral=True)
        if role in member.roles:
            try:
                await member.remove_roles(role, reason="DIFF notify toggle off")
            except discord.Forbidden:
                return await interaction.response.send_message("I don't have permission to remove that role.", ephemeral=True)
            return await interaction.response.send_message("🔕 Meet notifications turned **off**.", ephemeral=True)
        else:
            try:
                await member.add_roles(role, reason="DIFF notify toggle on")
            except discord.Forbidden:
                return await interaction.response.send_message("I don't have permission to add that role.", ephemeral=True)
            return await interaction.response.send_message("🔔 Meet notifications turned **on**.", ephemeral=True)


# =========================
# STAFF DASHBOARD PANEL
# =========================

def _build_staff_dashboard_embed() -> discord.Embed:
    try:
        apps = _load_diff_json(APPLICATIONS_FILE) if os.path.exists(APPLICATIONS_FILE) else {}
    except Exception:
        apps = {}

    pending, ready = [], []
    for user_id, app in apps.items():
        status = app.get("status", "")
        if status in ("Approved", "Denied"):
            continue
        if status == "PendingReview":
            ready.append(int(user_id))
        else:
            pending.append(int(user_id))

    inactive = [
        int(e["user_id"])
        for e in _rsvp_leaderboard.values()
        if int(e.get("attendance_count", 0)) == 0
    ]

    def fmt(lst): return [f"• <@{u}>" for u in lst[:10]] or ["• None"]

    sep = "━━━━━━━━━━━━━━━━━━━━━━"
    embed = discord.Embed(
        title="🧠 DIFF Staff Dashboard",
        description="\n".join([
            "Private staff control panel",
            "",
            sep,
            f"📥 **Pending Applications ({len(pending)})**",
            *fmt(pending),
            "",
            f"✅ **Ready For Review ({len(ready)})**",
            *fmt(ready),
            "",
            f"📉 **Inactive Members ({len(inactive)})**",
            *fmt(inactive),
            sep,
        ]),
        color=discord.Color.dark_gray(),
        timestamp=utc_now(),
    )
    embed.set_footer(text="Different Meets • Staff Dashboard")
    return embed


class StaffDashboardRefreshButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Refresh Dashboard", emoji="🔄", style=discord.ButtonStyle.secondary, custom_id="diff_staff_dashboard_refresh")

    async def callback(self, interaction: discord.Interaction):
        if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
            return await interaction.response.send_message("Only staff can use this.", ephemeral=True)
        await interaction.response.edit_message(embed=_build_staff_dashboard_embed(), view=StaffDashboardView())


class StaffDashboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(StaffDashboardRefreshButton())


async def _upsert_staff_dashboard(bot: commands.Bot) -> None:
    channel = bot.get_channel(STAFF_DASHBOARD_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        try:
            channel = await bot.fetch_channel(STAFF_DASHBOARD_CHANNEL_ID)
        except Exception:
            return
    if not isinstance(channel, discord.TextChannel):
        return
    existing = None
    try:
        async for msg in channel.history(limit=20):
            if msg.author.bot and msg.components:
                for row in msg.components:
                    for child in row.children:
                        if getattr(child, "custom_id", None) == "diff_staff_dashboard_refresh":
                            existing = msg
                            break
                if existing:
                    break
    except Exception:
        pass
    embed = _build_staff_dashboard_embed()
    view = StaffDashboardView()
    try:
        if existing:
            await existing.edit(embed=embed, view=view)
        else:
            await channel.send(embed=embed, view=view)
    except Exception:
        pass


async def _auto_staff_dashboard_loop() -> None:
    await bot.wait_until_ready()
    while not bot.is_closed():
        await asyncio.sleep(43200)
        try:
            await _upsert_staff_dashboard(bot)
        except Exception as e:
            print(f"[Staff Dashboard] Refresh error: {e}")


# =========================
# CREW INVITE AUTOMATION
# =========================

async def run_crew_invite_automation() -> None:
    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        return
    try:
        apps = _load_diff_json(APPLICATIONS_FILE) if os.path.exists(APPLICATIONS_FILE) else {}
    except Exception:
        apps = {}

    already_pinged = _crew_pinged_load()
    candidates = []

    top10 = sorted(
        _rsvp_leaderboard.values(),
        key=lambda x: int(x.get("attendance_count", 0)),
        reverse=True,
    )[:10]

    for entry in top10:
        uid = int(entry["user_id"])
        attendance = int(entry.get("attendance_count", 0))
        status = apps.get(str(uid), {}).get("status", "")
        if status == "Approved" and attendance >= 3 and uid not in already_pinged:
            candidates.append((uid, attendance))

    if not candidates:
        return

    log_ch = guild.get_channel(STAFF_LOGS_CHANNEL_ID)
    if not isinstance(log_ch, discord.TextChannel):
        return

    lines = [f"• <@{uid}> — {att} meet(s)" for uid, att in candidates]
    try:
        await log_ch.send(embed=discord.Embed(
            title="🏆 Crew Invite Consideration",
            description="\n".join([
                "These members have reached top activity and should be considered for a crew invite:",
                "",
                *lines,
                "",
                "Path: **Join → Attend → Top 10 → Crew consideration**",
            ]),
            color=discord.Color.gold(),
            timestamp=utc_now(),
        ))
    except Exception:
        return

    if CREW_CANDIDATE_ROLE_ID:
        role = guild.get_role(CREW_CANDIDATE_ROLE_ID)
        if role:
            for uid, _ in candidates:
                member = guild.get_member(uid)
                if member:
                    try:
                        await member.add_roles(role, reason="DIFF crew candidate automation")
                    except Exception:
                        pass

    already_pinged.update(uid for uid, _ in candidates)
    _crew_pinged_save(already_pinged)


async def _daily_crew_invite_check() -> None:
    await bot.wait_until_ready()
    while not bot.is_closed():
        await asyncio.sleep(86400)
        try:
            await run_crew_invite_automation()
        except Exception as e:
            print(f"[Crew Invite] Automation error: {e}")


# =========================
# WEEKLY ROLL CALL — MODAL + VIEW
# =========================

class WeeklyRollCallModal(discord.ui.Modal, title="📅 Weekly Roll Call Setup"):
    week_of = discord.ui.TextInput(
        label="Week Of",
        placeholder="e.g. March 22 – March 24",
        required=True,
        max_length=50,
    )
    meet1 = discord.ui.TextInput(
        label="Meet 1 – Day, Theme & Host",
        placeholder="e.g. Friday – Demolition Derby | Host: @BriMedia",
        required=True,
        max_length=120,
    )
    meet2 = discord.ui.TextInput(
        label="Meet 2 – Day, Theme & Host",
        placeholder="e.g. Saturday – Tire Meet | Host: @Host",
        required=True,
        max_length=120,
    )
    meet3 = discord.ui.TextInput(
        label="Meet 3 – Day, Theme & Host",
        placeholder="e.g. Sunday – Tire Lettering | Host: @Tso_Kyng",
        required=False,
        max_length=120,
    )

    async def on_submit(self, interaction: discord.Interaction):
        roll_call_ch = interaction.guild.get_channel(ROLL_CALL_CHANNEL_ID)
        if not isinstance(roll_call_ch, discord.TextChannel):
            return await interaction.response.send_message("Roll call channel not found.", ephemeral=True)
        meet3_val = self.meet3.value.strip() or None
        description = (
            f"**Week of {self.week_of.value}**\n"
            "Use the buttons below to RSVP for each meet separately.\n\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"🏁 **Meet 1** — {self.meet1.value}\n\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔥 **Meet 2** — {self.meet2.value}"
        )
        if meet3_val:
            description += f"\n\n━━━━━━━━━━━━━━━━━━━\n\n💎 **Meet 3** — {meet3_val}"
        embed = discord.Embed(
            title="📅 DIFF Weekly Roll Call",
            description=description,
            color=discord.Color.blue(),
        )
        await roll_call_ch.send(
            content=f"<@&{CREW_MEMBER_ROLE_ID}>",
            embed=embed,
            view=MeetRSVPView(meet1=self.meet1.value, meet2=self.meet2.value, meet3=meet3_val),
        )
        await interaction.response.send_message(f"Weekly roll call posted in {roll_call_ch.mention} ✅", ephemeral=True)

class MeetRSVPButton(discord.ui.Button):
    def __init__(self, label: str, style: discord.ButtonStyle, custom_id: str, row: int, meet_label: str, response: str):
        super().__init__(label=label, style=style, custom_id=custom_id, row=row)
        self.meet_label = meet_label
        self.response = response

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"You're marked as **{self.response}** for **{self.meet_label}** ✅",
            ephemeral=True,
        )


class MeetRSVPView(discord.ui.View):
    def __init__(self, meet1: str = "Meet 1", meet2: str = "Meet 2", meet3: str = None):
        super().__init__(timeout=None)

        def short(name: str) -> str:
            return (name[:22] + "…") if len(name) > 22 else name

        m1 = short(meet1)
        m2 = short(meet2)

        for custom, label, style, resp in [
            ("diff_m1_going", f"✅ {m1}", discord.ButtonStyle.success,   "Pulling Up"),
            ("diff_m1_maybe", f"❔ {m1}", discord.ButtonStyle.secondary, "Maybe"),
            ("diff_m1_not",   f"❌ {m1}", discord.ButtonStyle.danger,    "Not Coming"),
        ]:
            self.add_item(MeetRSVPButton(label=label, style=style, custom_id=custom, row=0, meet_label=meet1, response=resp))

        for custom, label, style, resp in [
            ("diff_m2_going", f"✅ {m2}", discord.ButtonStyle.success,   "Pulling Up"),
            ("diff_m2_maybe", f"❔ {m2}", discord.ButtonStyle.secondary, "Maybe"),
            ("diff_m2_not",   f"❌ {m2}", discord.ButtonStyle.danger,    "Not Coming"),
        ]:
            self.add_item(MeetRSVPButton(label=label, style=style, custom_id=custom, row=1, meet_label=meet2, response=resp))

        if meet3:
            m3 = short(meet3)
            for custom, label, style, resp in [
                ("diff_m3_going", f"✅ {m3}", discord.ButtonStyle.success,   "Pulling Up"),
                ("diff_m3_maybe", f"❔ {m3}", discord.ButtonStyle.secondary, "Maybe"),
                ("diff_m3_not",   f"❌ {m3}", discord.ButtonStyle.danger,    "Not Coming"),
            ]:
                self.add_item(MeetRSVPButton(label=label, style=style, custom_id=custom, row=2, meet_label=meet3, response=resp))
        else:
            for custom, label in [
                ("diff_m3_going", "Meet 3 N/A"),
                ("diff_m3_maybe", "Meet 3 N/A"),
                ("diff_m3_not",   "Meet 3 N/A"),
            ]:
                self.add_item(discord.ui.Button(label=label, style=discord.ButtonStyle.secondary, custom_id=custom, row=2, disabled=True))


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


def _count_hierarchy_statuses(guild: discord.Guild) -> dict:
    all_role_ids = [
        LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID,
        HOST_ROLE_ID, DESIGNER_TEAM_ROLE_ID, CONTENT_TEAM_ROLE_ID, COLOR_TEAM_ROLE_ID,
    ]
    seen: set = set()
    counts = {"online": 0, "idle": 0, "dnd": 0, "offline": 0}
    for role_id in all_role_ids:
        role = guild.get_role(role_id)
        if not role:
            continue
        for m in role.members:
            if m.id in seen:
                continue
            seen.add(m.id)
            if m.status == discord.Status.online:
                counts["online"] += 1
            elif m.status == discord.Status.idle:
                counts["idle"] += 1
            elif m.status == discord.Status.dnd:
                counts["dnd"] += 1
            else:
                counts["offline"] += 1
    return counts


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

    status_counts = _count_hierarchy_statuses(guild)

    embeds = []
    for index, (section_title, entries) in enumerate(role_sections):
        embed = discord.Embed(
            title="🏆 DIFF SERVER HIERARCHY",
            description=panel_descriptions[index] if index < len(panel_descriptions) else "Server staff and teams.",
            color=0xC9A227,
        )
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.set_image(url=DIFF_BANNER_URL)

        if index == 0:
            embed.add_field(
                name="📊 Staff Status",
                value=(
                    f"🟢 Online: **{status_counts['online']}**\u2003"
                    f"🌙 Idle: **{status_counts['idle']}**\u2003"
                    f"⛔ DND: **{status_counts['dnd']}**\u2003"
                    f"⚫ Offline: **{status_counts['offline']}**"
                ),
                inline=False,
            )

        embed.add_field(
            name=section_title,
            value="━━━━━━━━━━━━━━━━━━━━",
            inline=False,
        )

        for role_id, label in entries:
            role = guild.get_role(role_id)
            if role is None:
                embed.add_field(name=label, value="Role not found.", inline=False)
                continue
            embed.add_field(name="\u200b", value=format_role_member_lines(role), inline=False)

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


LIVE_ATTENDANCE_CHANNEL_ID = 1485469927312850974
LIVE_ATTENDANCE_PANEL_TITLE = "📊 DIFF Crew Attendance Status"


def build_live_attendance_embed(guild: discord.Guild) -> discord.Embed:
    crew_role = guild.get_role(CREW_MEMBER_ROLE_ID)
    crew_members = sorted(crew_role.members, key=lambda m: m.display_name.lower()) if crew_role else []

    online = [m for m in crew_members if m.status != discord.Status.offline]
    offline = [m for m in crew_members if m.status == discord.Status.offline]

    def _chunk_members(members: list) -> list[str]:
        if not members:
            return ["None right now."]
        chunks = []
        current_lines: list[str] = []
        current_len = 0
        for m in members:
            line = f"{get_member_status_emoji(m)} {m.mention} — `{m.display_name}`"
            cost = len(line) + (1 if current_lines else 0)
            if current_len + cost > 1000 and current_lines:
                chunks.append("\n".join(current_lines))
                current_lines = [line]
                current_len = len(line)
            else:
                current_lines.append(line)
                current_len += cost
        if current_lines:
            chunks.append("\n".join(current_lines))
        return chunks

    online_chunks = _chunk_members(online)
    offline_chunks = _chunk_members(offline)

    total_fields = len(online_chunks) + len(offline_chunks)
    if total_fields > 25:
        online_chunks = online_chunks[:12]
        offline_chunks = offline_chunks[:12]

    embed = discord.Embed(
        title=LIVE_ATTENDANCE_PANEL_TITLE,
        description=(
            "Live attendance snapshot for **Different Meets** crew members.\n"
            "This panel refreshes automatically every 5 minutes.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=discord.Color.green(),
        timestamp=datetime.utcnow(),
    )

    for i, chunk in enumerate(online_chunks):
        header = f"✅ Active Right Now ({len(online)})" if i == 0 else f"✅ Active (continued)"
        embed.add_field(name=header, value=chunk, inline=False)

    for i, chunk in enumerate(offline_chunks):
        header = f"⚫ Offline Right Now ({len(offline)})" if i == 0 else f"⚫ Offline (continued)"
        embed.add_field(name=header, value=chunk, inline=False)

    embed.set_footer(text="Different Meets • Auto-refreshes every 5 min • Same panel, no duplicates")
    return embed


async def post_or_refresh_live_attendance(guild: discord.Guild) -> None:
    channel = guild.get_channel(LIVE_ATTENDANCE_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        return

    embed = build_live_attendance_embed(guild)
    state = _load_diff_json(DIFF_PANEL_STATE_FILE)
    message_id = state.get("live_attendance_message_id")
    message = None

    if message_id:
        try:
            message = await channel.fetch_message(int(message_id))
        except (discord.NotFound, discord.HTTPException):
            message = None

    if message is None:
        async for msg in channel.history(limit=30):
            if msg.author.id == bot.user.id and msg.embeds and msg.embeds[0].title == LIVE_ATTENDANCE_PANEL_TITLE:
                message = msg
                break

    if message:
        try:
            await message.edit(embed=embed)
        except Exception:
            message = None

    if message is None:
        message = await channel.send(embed=embed)

    state["live_attendance_message_id"] = message.id
    _save_diff_json(DIFF_PANEL_STATE_FILE, state)


@tasks.loop(minutes=5)
async def hierarchy_attendance_loop():
    guild = bot.guilds[0] if bot.guilds else None
    if guild is None:
        return
    try:
        hierarchy_message_ids = data.get("hierarchy_message_ids", [])
        if hierarchy_message_ids:
            channel = guild.get_channel(HIERARCHY_CHANNEL_ID)
            if isinstance(channel, discord.TextChannel):
                embeds = build_hierarchy_embeds(guild)
                support_view = build_hierarchy_support_view()
                msgs = []
                for mid in hierarchy_message_ids:
                    try:
                        msgs.append(await channel.fetch_message(mid))
                    except Exception:
                        msgs = []
                        break
                if msgs and len(msgs) == len(embeds):
                    for i, (msg, emb) in enumerate(zip(msgs, embeds)):
                        is_last = i == len(embeds) - 1
                        try:
                            await msg.edit(
                                content="## DIFF Hierarchy Panel" if i == 0 else None,
                                embed=emb,
                                view=support_view if is_last else discord.ui.View(),
                            )
                        except Exception:
                            pass
    except Exception:
        pass
    try:
        await post_or_refresh_live_attendance(guild)
    except Exception:
        pass


@hierarchy_attendance_loop.before_loop
async def before_hierarchy_attendance_loop():
    await bot.wait_until_ready()


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


class MeetInfoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        guild_id = GUILD_ID
        self.add_item(discord.ui.Button(label="General Rules", style=discord.ButtonStyle.link, emoji="📜", url=build_channel_link(guild_id, MEET_RULES_CHANNEL_ID)))
        self.add_item(discord.ui.Button(label="Join Meets", style=discord.ButtonStyle.link, emoji="📥", url=build_channel_link(guild_id, JOIN_MEETS_CHANNEL_ID)))
        self.add_item(discord.ui.Button(label="Upcoming Meet", style=discord.ButtonStyle.link, emoji="📅", url=build_channel_link(guild_id, UPCOMING_MEET_CHANNEL_ID)))
        self.add_item(discord.ui.Button(label="Support Tickets", style=discord.ButtonStyle.link, emoji="🎟️", url=build_channel_link(guild_id, SUPPORT_TICKETS_CHANNEL_ID)))
        self.add_item(discord.ui.Button(label="Hosts", style=discord.ButtonStyle.link, emoji="👥", url=build_channel_link(guild_id, DIFF_HOSTS_CHANNEL_ID)))

    @discord.ui.button(
        label="Submit Feedback",
        style=discord.ButtonStyle.primary,
        custom_id="diff_meetinfo_feedback_submit",
        emoji="📝",
        row=1,
    )
    async def submit_feedback(self, interaction: discord.Interaction, button: discord.ui.Button):
        from cogs.diff_feedback_system import FeedbackModal
        cog = interaction.client.cogs.get("FeedbackSystem")
        if cog is None:
            await interaction.response.send_message(
                "Feedback system is temporarily unavailable.", ephemeral=True
            )
            return
        await interaction.response.send_modal(FeedbackModal(cog))


def build_meet_info_view(guild_id: int = GUILD_ID) -> MeetInfoView:
    return MeetInfoView()


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

        unverified = interaction.guild.get_role(UNVERIFIED_ROLE_ID)
        if unverified and unverified in member.roles:
            try:
                await member.remove_roles(unverified, reason="Rules accepted — removing unverified")
            except discord.HTTPException:
                pass

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
        cooldown_text = get_reapply_cooldown_text(interaction.user.id)
        if cooldown_text:
            await interaction.response.send_message(
                f"❌ You cannot apply to DIFF yet.\n"
                f"Your reapply cooldown is still active: **{cooldown_text}**.\n"
                "Please wait until the cooldown expires before submitting a new application.",
                ephemeral=True,
            )
            return
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
        score_data = generate_application_score(answers)
        score_embed = build_score_embed(app_id, interaction.user, score_data)
        await ticket_channel.send(embed=score_embed, view=DIFFRecruitmentTicketView())
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

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        traceback.print_exception(type(error), error, error.__traceback__)
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
            else:
                await interaction.followup.send("Something went wrong. Please try again.", ephemeral=True)
        except Exception:
            pass

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
# DIFF CREW PANEL
# =========================

class DiffPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="📝 Crew Roll Call", style=discord.ButtonStyle.link, url=ROLL_CALL_URL, row=0))
        self.add_item(discord.ui.Button(label="🎨 Crew Color Voting", style=discord.ButtonStyle.link, url=COLOR_CHANNEL_URL, row=0))

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        traceback.print_exception(type(error), error, error.__traceback__)
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
            else:
                await interaction.followup.send("Something went wrong. Please try again.", ephemeral=True)
        except Exception:
            pass

    @discord.ui.button(label="⚠️ Strike System", style=discord.ButtonStyle.primary, custom_id="diff_panel_strike", row=1)
    async def strike(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="⚠️ DIFF Strike & Warning System",
            description=(
                "To maintain a clean, realistic, and respectful environment, "
                "DIFF uses a structured conduct system for all members."
            ),
            color=discord.Color.red(),
        )
        embed.add_field(
            name="📊 System Overview",
            value=(
                "• ⚠️ Warning — Minor issue (notice)\n"
                "• 🚨 Strike 1 — Official warning\n"
                "• ⛔ Strike 2 — Final warning\n"
                "• ❌ Strike 3 — Removal from DIFF"
            ),
            inline=False,
        )
        embed.add_field(
            name="📌 What Can Lead to Strikes",
            value=(
                "• Disruptive behavior during meets\n"
                "• Unrealistic / non-compliant builds\n"
                "• Disrespect toward members or staff\n"
                "• Failure to follow crew rules"
            ),
            inline=False,
        )
        embed.add_field(
            name="🚨 Important",
            value=(
                "Repeated issues will escalate quickly. "
                "Staff decisions are final to keep the crew organized and professional."
            ),
            inline=False,
        )
        embed.add_field(
            name="✅ Stay in Good Standing",
            value="Follow the rules, respect the community, and contribute positively to DIFF.",
            inline=False,
        )
        embed.set_footer(text="— DIFF Management")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🧥 Crew Jackets", style=discord.ButtonStyle.secondary, custom_id="diff_panel_jackets", row=1)
    async def jackets(self, interaction: discord.Interaction, button: discord.ui.Button):
        first = discord.Embed(
            title="🧥 DIFF Crew Jackets",
            description=(
                "**Leaders / Managers Jacket** shown below.\n"
                "Crew member jacket images will follow in separate messages.\n\n"
                "If a member cannot place the crew emblem on the new jackets, "
                "they must wear the alternate jacket."
            ),
            color=discord.Color.blue(),
        )
        first.set_image(url=LEADER_JACKET)
        await interaction.response.send_message(embed=first, ephemeral=True)
        for index, url in enumerate(CREW_JACKETS, start=1):
            jacket_embed = discord.Embed(title=f"🧥 Crew Member Jacket {index}", color=discord.Color.blue())
            jacket_embed.set_image(url=url)
            await interaction.followup.send(embed=jacket_embed, ephemeral=True)
        alt_embed = discord.Embed(
            title="🧥 Alternate Crew Jacket",
            description="Use this jacket only if the crew emblem cannot be placed on the new jackets.",
            color=discord.Color.blue(),
        )
        alt_embed.set_image(url=ALT_JACKET)
        await interaction.followup.send(embed=alt_embed, ephemeral=True)

    @discord.ui.button(label="📈 My Stats", style=discord.ButtonStyle.success, custom_id="diff_panel_member_stats", row=2)
    async def member_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = str(interaction.user.id)
        meets_data = _load_activity_meets()
        m_stats = meets_data.get("members", {}).get(uid, {})
        attended = m_stats.get("attended", 0)
        hosted = m_stats.get("hosted", 0)
        no_shows = m_stats.get("no_shows", 0)
        penalty_pts = m_stats.get("penalty_points", 0)
        rep_data = _load_activity_json(REPUTATION_FILE)
        reputation = rep_data.get("reputation", {}).get(uid, 0)
        warnings = get_warning_count(interaction.user.id)
        score = max(0, (attended * 5) + (hosted * 8) - (no_shows * 6) - (warnings * 4) - (penalty_pts * 2))
        if score >= 80:
            grade = "A"
        elif score >= 60:
            grade = "B"
        elif score >= 40:
            grade = "C"
        else:
            grade = "D"
        embed = discord.Embed(
            title=f"📈 {interaction.user.display_name} — My DIFF Stats",
            description="Your current DIFF activity snapshot.",
            color=discord.Color.green(),
        )
        embed.add_field(name="✅ Meets Attended", value=str(attended), inline=True)
        embed.add_field(name="🎤 Meets Hosted", value=str(hosted), inline=True)
        embed.add_field(name="❌ No-Shows", value=str(no_shows), inline=True)
        embed.add_field(name="⭐ Reputation", value=str(reputation), inline=True)
        embed.add_field(name="⚠️ Warnings", value=str(warnings), inline=True)
        embed.add_field(name="🏅 Activity Score", value=f"{score} ({grade})", inline=True)
        embed.set_footer(text="Stats are updated live from the DIFF activity systems.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="📋 Roles & Responsibility", style=discord.ButtonStyle.secondary, custom_id="diff_panel_crew_roles", row=2)
    async def crew_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📋 DIFF Roles & Responsibility",
            description=(
                "**Leader** — Oversees the full crew, staff direction, and major decisions.\n\n"
                "**Co-Leader / Manager** — Helps run operations, reviews activity, and supports hosts and staff.\n\n"
                "**Host** — Runs meets, organizes the lobby, helps with attendance, and keeps events smooth.\n\n"
                "**Crew Member** — Represents DIFF properly, does roll calls, follows rules, votes on colors, and stays active.\n\n"
                "**What DIFF expects from everyone:**\n"
                "• Respect staff and members\n"
                "• Follow meet rules\n"
                "• Stay active and consistent\n"
                "• Represent the crew professionally"
            ),
            color=discord.Color.blurple(),
        )
        embed.set_footer(text="— DIFF Management")
        await interaction.response.send_message(embed=embed, ephemeral=True)


def _build_diff_panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title="📌 DIFF Crew Control Hub",
        description=(
            "*The all-in-one crew hub for Different Meets.*\n\n"
            "---\n\n"
            "📊 **Available Systems:**\n\n"
            "📝 **Crew Roll Call** — Confirm your attendance for upcoming meets\n"
            "🎨 **Crew Color Voting** — Help decide crew themes & styles\n"
            "⚠️ **Strike System** — Review conduct rules and standards\n"
            "🧥 **Crew Jackets** — View official DIFF crew outfits\n"
            "📋 **Crew Roles & Responsibility** — Learn each role and expectations within DIFF\n"
            "📈 **My Stats** — View your personal DIFF activity snapshot\n\n"
            "---\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📊 Stay active, stay consistent, and represent DIFF the right way.\n\n"
            "— **Different Meets**"
        ),
        color=discord.Color.blue(),
    )
    embed.set_thumbnail(url=DIFF_LOGO)
    embed.set_image(url=DIFF_LOGO)
    return embed


@bot.tree.command(name="diffpanel", description="Post the DIFF Crew Control Panel (staff only)")
async def diffpanel(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    panel_ch = interaction.guild.get_channel(DIFF_PANEL_CHANNEL_ID)
    if not isinstance(panel_ch, discord.TextChannel):
        return await interaction.response.send_message("Panel channel not found.", ephemeral=True)
    message = await panel_ch.send(embed=_build_diff_panel_embed(), view=DiffPanel())
    _save_diff_json(DIFF_PANEL_STATE_FILE, {"channel_id": panel_ch.id, "message_id": message.id})
    await interaction.response.send_message(f"Panel posted in {panel_ch.mention} ✅", ephemeral=True)


@bot.tree.command(name="refreshdiffpanel", description="Refresh the existing DIFF Crew Control Panel (staff only)")
async def refreshdiffpanel(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    panel_ch = interaction.guild.get_channel(DIFF_PANEL_CHANNEL_ID)
    if not isinstance(panel_ch, discord.TextChannel):
        return await interaction.response.send_message("Panel channel not found.", ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    message = None
    state = _load_diff_json(DIFF_PANEL_STATE_FILE)
    message_id = state.get("message_id")
    if message_id:
        try:
            message = await panel_ch.fetch_message(int(message_id))
        except (discord.NotFound, discord.HTTPException):
            message = None
    if message is None:
        async for msg in panel_ch.history(limit=50):
            if msg.author.id == bot.user.id and msg.embeds:
                message = msg
                _save_diff_json(DIFF_PANEL_STATE_FILE, {"channel_id": panel_ch.id, "message_id": msg.id})
                break
    if message is None:
        return await interaction.followup.send("No panel message found in the channel. Use `/diffpanel` to post one.", ephemeral=True)
    await message.edit(embed=_build_diff_panel_embed(), view=DiffPanel())
    await interaction.followup.send("Panel refreshed ✅", ephemeral=True)


@bot.tree.command(name="diffhub", description="Post the DIFF Crew Control Hub in this channel (staff only)")
async def diffhub(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    if not isinstance(interaction.channel, discord.TextChannel):
        return await interaction.response.send_message("Must be used in a text channel.", ephemeral=True)
    embed = discord.Embed(
        title="📌 DIFF Crew Control Hub",
        description=(
            "*The all-in-one crew hub for Different Meets.*\n\n"
            "---\n\n"
            "📊 **Available Systems:**\n\n"
            "📝 **Crew Roll Call** — Confirm your attendance for upcoming meets\n"
            "🎨 **Crew Color Voting** — Help decide crew themes & styles\n"
            "⚠️ **Strike System** — Review conduct rules and standards\n"
            "🧥 **Crew Jackets** — View official DIFF crew outfits\n"
            "📋 **Crew Roles & Responsibility** — Learn each role and expectations within DIFF\n"
            "📈 **My Stats** — View your personal DIFF activity snapshot\n\n"
            "---\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📊 Stay active, stay consistent, and represent DIFF the right way.\n\n"
            "— **Different Meets**"
        ),
        color=discord.Color.blue(),
    )
    embed.set_thumbnail(url=DIFF_LOGO)
    embed.set_image(url=DIFF_LOGO)
    await interaction.channel.send(embed=embed, view=DiffPanel())
    await interaction.response.send_message("Control Hub posted ✅", ephemeral=True)


# =========================
# ACTIVITY MEETS SYSTEM
# =========================

def _load_activity_meets() -> dict:
    data = _load_diff_json(ACTIVITY_MEETS_FILE)
    for key, default in [("members", {}), ("meets", {}), ("dashboard_message_id", None), ("dashboard_channel_id", None)]:
        data.setdefault(key, default)
    return data


def _save_activity_meets(data: dict):
    _save_diff_json(ACTIVITY_MEETS_FILE, data)


def _get_member_activity(data: dict, user_id: int) -> dict:
    uid = str(user_id)
    members = data.setdefault("members", {})
    if uid not in members:
        members[uid] = {"attended": 0, "hosted": 0, "maybe": 0, "declined": 0, "no_shows": 0, "penalty_points": 0, "last_updated": datetime.utcnow().isoformat()}
    return members[uid]


def _get_meet(data: dict, meet_id: str) -> dict:
    meets = data.setdefault("meets", {})
    if meet_id not in meets:
        meets[meet_id] = {"title": meet_id, "host_id": None, "scheduled_time": None, "created_at": datetime.utcnow().isoformat(), "rsvps": {}, "checked_in": [], "closed": False}
    return meets[meet_id]


def _activity_promotion_suggestion(member: discord.Member, stats: dict) -> Optional[str]:
    attended = stats.get("attended", 0)
    hosted = stats.get("hosted", 0)
    no_shows = stats.get("no_shows", 0)
    role_ids = {role.id for role in member.roles}
    if no_shows > 1:
        return None
    if CREW_MEMBER_ROLE_ID in role_ids and attended >= 5:
        return "Host"
    if HOST_ROLE_ID in role_ids and attended >= 10 and hosted >= 3:
        return "Manager"
    if MANAGER_ROLE_ID in role_ids and attended >= 18 and hosted >= 6:
        return "Co-Leader"
    return None


async def _build_activity_dashboard_embed(guild: discord.Guild, data: dict) -> discord.Embed:
    embed = discord.Embed(title="DIFF Activity Dashboard", description="Live overview of attendance, leaderboard, and promotion watch.", color=discord.Color.blue(), timestamp=utc_now())
    members = data.get("members", {})
    ranked = sorted(members.items(), key=lambda x: (x[1].get("attended", 0), x[1].get("hosted", 0), -x[1].get("no_shows", 0)), reverse=True)
    medals = ["🥇", "🥈", "🥉"]
    lb_lines = []
    for idx, (uid, stats) in enumerate(ranked[:5], start=1):
        m = guild.get_member(int(uid))
        name = m.mention if m else f"<@{uid}>"
        prefix = medals[idx - 1] if idx <= 3 else f"{idx}."
        lb_lines.append(f"{prefix} {name} — {stats.get('attended', 0)} attended / {stats.get('hosted', 0)} hosted")
    embed.add_field(name="🏆 Top Activity", value="\n".join(lb_lines) or "No data yet.", inline=False)
    watch_lines = []
    for uid, stats in ranked:
        if stats.get("attended", 0) >= 5 and stats.get("no_shows", 0) <= 1:
            m = guild.get_member(int(uid))
            name = m.mention if m else f"<@{uid}>"
            watch_lines.append(f"{name} — {stats.get('attended', 0)} attended / {stats.get('hosted', 0)} hosted / {stats.get('no_shows', 0)} no-shows")
        if len(watch_lines) == 5:
            break
    embed.add_field(name="📈 Promotion Watch", value="\n".join(watch_lines) or "None yet.", inline=False)
    penalty_lines = []
    for uid, stats in ranked:
        if stats.get("no_shows", 0) > 0 or stats.get("penalty_points", 0) > 0:
            m = guild.get_member(int(uid))
            name = m.mention if m else f"<@{uid}>"
            penalty_lines.append(f"{name} — {stats.get('no_shows', 0)} no-shows / {stats.get('penalty_points', 0)} penalty pts")
        if len(penalty_lines) == 5:
            break
    embed.add_field(name="⚠️ Penalty Watch", value="\n".join(penalty_lines) or "None recorded.", inline=False)
    embed.set_footer(text="Auto-refreshes after each activity update")
    return embed


async def _refresh_activity_dashboard(guild: discord.Guild, data: dict):
    ch_id = data.get("dashboard_channel_id")
    msg_id = data.get("dashboard_message_id")
    if not ch_id or not msg_id:
        return
    channel = guild.get_channel(int(ch_id))
    if not isinstance(channel, discord.TextChannel):
        return
    try:
        message = await channel.fetch_message(int(msg_id))
        embed = await _build_activity_dashboard_embed(guild, data)
        await message.edit(embed=embed, view=ActivityDashboardView())
    except Exception:
        pass


class ActivityDashboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(
            label="Support Channel",
            style=discord.ButtonStyle.link,
            url=f"https://discord.com/channels/{GUILD_ID}/{SUPPORT_CHANNEL_ID}",
        ))


@bot.tree.command(name="meet-create", description="Create a tracked meet record (staff only)")
@app_commands.describe(meet_id="Short unique ID e.g. friday-derby-01", title="Meet title", scheduled_time_unix="Unix timestamp", host="Meet host")
async def meet_create(interaction: discord.Interaction, meet_id: str, title: str, scheduled_time_unix: int, host: discord.Member):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    data = _load_activity_meets()
    record = _get_meet(data, meet_id)
    record["title"] = title
    record["host_id"] = host.id
    record["scheduled_time"] = scheduled_time_unix
    record["closed"] = False
    _save_activity_meets(data)
    embed = discord.Embed(title="Meet Created", color=discord.Color.green())
    embed.add_field(name="Meet ID", value=f"`{meet_id}`", inline=False)
    embed.add_field(name="Title", value=title, inline=False)
    embed.add_field(name="Time", value=f"<t:{scheduled_time_unix}:F>", inline=False)
    embed.add_field(name="Host", value=host.mention, inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="meet-rsvp", description="Set a member's RSVP for a tracked meet (staff only)")
@app_commands.describe(meet_id="Tracked meet ID", member="Member to update", status="going, maybe, or not_going")
@app_commands.choices(status=[
    app_commands.Choice(name="going", value="going"),
    app_commands.Choice(name="maybe", value="maybe"),
    app_commands.Choice(name="not_going", value="not_going"),
])
async def meet_rsvp(interaction: discord.Interaction, meet_id: str, member: discord.Member, status: app_commands.Choice[str]):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    data = _load_activity_meets()
    meet = _get_meet(data, meet_id)
    meet.setdefault("rsvps", {})[str(member.id)] = status.value
    stats = _get_member_activity(data, member.id)
    if status.value == "maybe":
        stats["maybe"] = stats.get("maybe", 0) + 1
    elif status.value == "not_going":
        stats["declined"] = stats.get("declined", 0) + 1
    stats["last_updated"] = datetime.utcnow().isoformat()
    _save_activity_meets(data)
    rsvps = meet.get("rsvps", {})
    going = sum(1 for v in rsvps.values() if v == "going")
    maybe = sum(1 for v in rsvps.values() if v == "maybe")
    not_going = sum(1 for v in rsvps.values() if v == "not_going")
    await interaction.response.send_message(f"Set {member.mention} to **{status.value}** for `{meet_id}`.\nGoing: {going} | Maybe: {maybe} | Not Going: {not_going}", ephemeral=True)


@bot.tree.command(name="meet-checkin", description="Mark a member as attended for a meet (staff only)")
@app_commands.describe(meet_id="Tracked meet ID", member="Member that showed up")
async def meet_checkin(interaction: discord.Interaction, meet_id: str, member: discord.Member):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    data = _load_activity_meets()
    meet = _get_meet(data, meet_id)
    checked_in = meet.setdefault("checked_in", [])
    if member.id not in checked_in:
        checked_in.append(member.id)
    stats = _get_member_activity(data, member.id)
    stats["attended"] = stats.get("attended", 0) + 1
    stats["last_updated"] = datetime.utcnow().isoformat()
    _save_activity_meets(data)
    suggestion = _activity_promotion_suggestion(member, stats)
    if suggestion and interaction.guild:
        logs_ch = interaction.guild.get_channel(STAFF_LOGS_CHANNEL_ID)
        if isinstance(logs_ch, discord.TextChannel):
            promo_embed = discord.Embed(title="📈 Promotion Suggestion", color=discord.Color.gold(), timestamp=utc_now())
            promo_embed.add_field(name="Member", value=member.mention, inline=False)
            promo_embed.add_field(name="Suggested Role", value=suggestion, inline=False)
            promo_embed.add_field(name="Stats", value=f"Attended: {stats.get('attended', 0)} | Hosted: {stats.get('hosted', 0)} | No-Shows: {stats.get('no_shows', 0)}", inline=False)
            await logs_ch.send(embed=promo_embed)
    if interaction.guild:
        await _refresh_activity_dashboard(interaction.guild, data)
    await interaction.response.send_message(f"Checked in {member.mention} for `{meet_id}`. Total attended: {stats.get('attended', 0)}", ephemeral=True)


@bot.tree.command(name="meet-hosted", description="Add a hosted meet to a member's record (staff only)")
@app_commands.describe(member="Host member")
async def meet_hosted(interaction: discord.Interaction, member: discord.Member):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    data = _load_activity_meets()
    stats = _get_member_activity(data, member.id)
    stats["hosted"] = stats.get("hosted", 0) + 1
    stats["last_updated"] = datetime.utcnow().isoformat()
    _save_activity_meets(data)
    if interaction.guild:
        await _refresh_activity_dashboard(interaction.guild, data)
    await interaction.response.send_message(f"Added 1 hosted meet to {member.mention}. Total hosted: {stats.get('hosted', 0)}", ephemeral=True)


@bot.tree.command(name="meet-close", description="Close a meet and apply no-show penalties (staff only)")
@app_commands.describe(meet_id="Tracked meet ID")
async def meet_close(interaction: discord.Interaction, meet_id: str):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    data = _load_activity_meets()
    meet = _get_meet(data, meet_id)
    if meet.get("closed"):
        return await interaction.response.send_message(f"`{meet_id}` is already closed.", ephemeral=True)
    rsvps = meet.get("rsvps", {})
    checked_in = set(meet.get("checked_in", []))
    no_show_ids = []
    for uid, status in rsvps.items():
        if status == "going" and int(uid) not in checked_in:
            stats = _get_member_activity(data, int(uid))
            stats["no_shows"] = stats.get("no_shows", 0) + 1
            stats["penalty_points"] = stats.get("penalty_points", 0) + 1
            stats["last_updated"] = datetime.utcnow().isoformat()
            no_show_ids.append(int(uid))
    meet["closed"] = True
    _save_activity_meets(data)
    if interaction.guild and no_show_ids:
        logs_ch = interaction.guild.get_channel(STAFF_LOGS_CHANNEL_ID)
        if isinstance(logs_ch, discord.TextChannel):
            lines = []
            for uid in no_show_ids:
                m = interaction.guild.get_member(uid)
                name = m.mention if m else f"<@{uid}>"
                s = _get_member_activity(data, uid)
                lines.append(f"{name} — No-Shows: {s.get('no_shows', 0)} / Penalty Pts: {s.get('penalty_points', 0)}")
            penalty_embed = discord.Embed(title="⚠️ No-Show Penalties Applied", color=discord.Color.red(), timestamp=utc_now())
            penalty_embed.add_field(name="Meet", value=f"{meet.get('title', meet_id)} (`{meet_id}`)", inline=False)
            penalty_embed.add_field(name="Members Penalised", value="\n".join(lines), inline=False)
            await logs_ch.send(embed=penalty_embed)
    if interaction.guild:
        await _refresh_activity_dashboard(interaction.guild, data)
    msg = f"Closed `{meet_id}`."
    if no_show_ids:
        msg += f" {len(no_show_ids)} no-show penalt{'y' if len(no_show_ids) == 1 else 'ies'} applied and logged to staff channel."
    else:
        msg += " No no-shows recorded."
    await interaction.response.send_message(msg, ephemeral=True)


@bot.tree.command(name="diff-leaderboard", description="Post the DIFF activity leaderboard (staff only)")
async def diff_leaderboard(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    if not interaction.guild:
        return
    data = _load_activity_meets()
    members = data.get("members", {})
    ranked = sorted(members.items(), key=lambda x: (x[1].get("attended", 0), x[1].get("hosted", 0), -x[1].get("no_shows", 0)), reverse=True)
    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for idx, (uid, stats) in enumerate(ranked[:10], start=1):
        m = interaction.guild.get_member(int(uid))
        name = m.mention if m else f"<@{uid}>"
        prefix = medals[idx - 1] if idx <= 3 else f"{idx}."
        lines.append(f"{prefix} {name}\nAttended: {stats.get('attended', 0)} | Hosted: {stats.get('hosted', 0)} | No-Shows: {stats.get('no_shows', 0)}")
    embed = discord.Embed(title="DIFF Activity Leaderboard", description="\n\n".join(lines) if lines else "No data yet.", color=discord.Color.blue(), timestamp=utc_now())
    lb_ch = interaction.guild.get_channel(LEADERBOARD_CHANNEL_ID)
    if isinstance(lb_ch, discord.TextChannel):
        await lb_ch.send(embed=embed)
        await interaction.response.send_message("Leaderboard posted.", ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="diff-dashboard-post", description="Post the live DIFF activity dashboard (staff only)")
async def diff_dashboard_post(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    if not interaction.guild or not isinstance(interaction.channel, discord.TextChannel):
        return await interaction.response.send_message("Use this in a text channel.", ephemeral=True)
    data = _load_activity_meets()
    embed = await _build_activity_dashboard_embed(interaction.guild, data)
    message = await interaction.channel.send(embed=embed, view=ActivityDashboardView())
    data["dashboard_message_id"] = message.id
    data["dashboard_channel_id"] = interaction.channel.id
    _save_activity_meets(data)
    await interaction.response.send_message("Activity dashboard posted and linked for auto-refresh.", ephemeral=True)


@bot.tree.command(name="diff-dashboard-refresh", description="Manually refresh the DIFF activity dashboard (staff only)")
async def diff_dashboard_refresh(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    if not interaction.guild:
        return
    data = _load_activity_meets()
    await _refresh_activity_dashboard(interaction.guild, data)
    await interaction.response.send_message("Dashboard refreshed.", ephemeral=True)


@bot.tree.command(name="diff-member-stats", description="Show full activity stats for a member (staff only)")
@app_commands.describe(member="Member to inspect")
async def diff_member_stats(interaction: discord.Interaction, member: discord.Member):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    data = _load_activity_meets()
    stats = _get_member_activity(data, member.id)
    embed = discord.Embed(title="Member Activity Stats", color=discord.Color.blurple())
    embed.set_author(name=str(member), icon_url=member.display_avatar.url)
    embed.add_field(name="Attended", value=str(stats.get("attended", 0)), inline=True)
    embed.add_field(name="Hosted", value=str(stats.get("hosted", 0)), inline=True)
    embed.add_field(name="Maybe", value=str(stats.get("maybe", 0)), inline=True)
    embed.add_field(name="Declined", value=str(stats.get("declined", 0)), inline=True)
    embed.add_field(name="No-Shows", value=str(stats.get("no_shows", 0)), inline=True)
    embed.add_field(name="Penalty Points", value=str(stats.get("penalty_points", 0)), inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="diff-reset-member", description="Reset a member's activity meets record (staff only)")
@app_commands.describe(member="Member to reset")
async def diff_reset_member(interaction: discord.Interaction, member: discord.Member):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    data = _load_activity_meets()
    data.setdefault("members", {})[str(member.id)] = {"attended": 0, "hosted": 0, "maybe": 0, "declined": 0, "no_shows": 0, "penalty_points": 0, "last_updated": datetime.utcnow().isoformat()}
    _save_activity_meets(data)
    if interaction.guild:
        await _refresh_activity_dashboard(interaction.guild, data)
    await interaction.response.send_message(f"Reset activity stats for {member.mention}.", ephemeral=True)


# =========================
# HOST PERFORMANCE + WARNING SYSTEM
# =========================

_HP_DATA_FILE = os.path.join("diff_data", "diff_host_performance.json")


def _hp_load() -> dict:
    try:
        with open(_HP_DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"active_sessions": {}, "host_stats": {}, "hub_message_id": None}


def _hp_save(data: dict) -> None:
    with open(_HP_DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _hp_get_hub_msg_id(data: dict):
    v = data.get("hub_message_id")
    return int(v) if v else None


def _hp_has_role(member: discord.Member) -> bool:
    ids = {r.id for r in member.roles}
    return any(rid in ids for rid in (HOST_ROLE_ID, MANAGER_ROLE_ID, CO_LEADER_ROLE_ID, LEADER_ROLE_ID))


def _hp_utcnow() -> str:
    from datetime import timezone as _tz
    return datetime.now(_tz.utc).isoformat()


def _hp_score(session: dict) -> tuple[int, list[str]]:
    score = 2
    warnings = []
    if session.get("blacklist_checked"):
        score += 2
    else:
        score -= 3
        warnings.append("Blacklist was not confirmed before or during the meet")
    if session.get("checklist_completed"):
        score += 2
    else:
        score -= 2
        warnings.append("Host checklist was not completed")
    if session.get("lobby_proof_posted"):
        score += 2
    else:
        score -= 2
        warnings.append("Lobby proof was not confirmed")
    if session.get("todays_meet_posted"):
        score += 2
    else:
        score -= 2
        warnings.append("Today's Meet post was not confirmed")
    att = session.get("total_attendance", 0)
    if att >= 15:
        score += 2
    elif att >= 8:
        score += 1
    if session.get("diff_attendance", 0) >= 5:
        score += 1
    return score, warnings


def _hp_session_embed(s: dict) -> discord.Embed:
    embed = discord.Embed(
        title=f"🚗 Host Session • {s.get('meet_name', '—')}",
        description=(
            f"**Host:** <@{s['host_id']}>\n"
            f"**Session ID:** `{s['session_id']}`\n\n"
            "Use the buttons below to mark progress during your meet."
        ),
        color=discord.Color.green(),
    )
    embed.add_field(
        name="✅ Required Steps",
        value=(
            f"Blacklist Checked: {'✅' if s.get('blacklist_checked') else '❌'}\n"
            f"Checklist Completed: {'✅' if s.get('checklist_completed') else '❌'}\n"
            f"Lobby Opened: {'✅' if s.get('lobby_opened') else '❌'}\n"
            f"Lobby Proof Posted: {'✅' if s.get('lobby_proof_posted') else '❌'}\n"
            f"Today's Meet Posted: {'✅' if s.get('todays_meet_posted') else '❌'}"
        ),
        inline=False,
    )
    embed.add_field(
        name="📈 Attendance",
        value=(
            f"Total Attendance: **{s.get('total_attendance', 0)}**\n"
            f"DIFF Attendance: **{s.get('diff_attendance', 0)}**"
        ),
        inline=False,
    )
    embed.set_footer(text="Complete every required step to avoid warnings")
    return embed


def _hp_hub_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🧠 DIFF Host Performance Hub",
        description=(
            "*Track host sessions, attendance, required steps, and warning compliance.*\n\n"
            "Use the buttons below to start a host session, confirm required actions, "
            "submit attendance, and view your host stats.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "**Available Tools**\n"
            "🟢 Start Meet Session — open a tracked host session\n"
            "📊 My Host Stats — view your performance totals\n"
            "⚠️ System Info — see what gets tracked and warned\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "This system helps DIFF track quality, consistency, and host accountability."
        ),
        color=discord.Color.blurple(),
    )
    embed.set_footer(text="DIFF Host Performance • Built for structure • Powered by consistency")
    return embed


def _hp_stats_embed(user: discord.abc.User, stats: dict) -> discord.Embed:
    meets = stats.get("meets_hosted", 0)
    avg_att = round(stats.get("total_attendance_sum", 0) / meets, 1) if meets else 0
    avg_diff = round(stats.get("diff_attendance_sum", 0) / meets, 1) if meets else 0
    embed = discord.Embed(
        title="📊 DIFF Host Stats",
        description=f"*Performance summary for {user.mention}*",
        color=discord.Color.blurple(),
    )
    embed.add_field(
        name="Core Stats",
        value=(
            f"Meets Hosted: **{meets}**\n"
            f"Avg Attendance: **{avg_att}**\n"
            f"Avg DIFF Attendance: **{avg_diff}**\n"
            f"Score Total: **{stats.get('score_total', 0)}**\n"
            f"Warnings: **{stats.get('warning_count', 0)}**"
        ),
        inline=False,
    )
    embed.add_field(
        name="Compliance",
        value=(
            f"Blacklist Checks: **{stats.get('blacklist_checks', 0)}**\n"
            f"Checklists Completed: **{stats.get('checklists_completed', 0)}**\n"
            f"Lobby Proofs: **{stats.get('lobby_proofs', 0)}**\n"
            f"Today's Meet Posts: **{stats.get('todays_meet_posts', 0)}**"
        ),
        inline=False,
    )
    embed.set_footer(text="Consistency is what builds trust in a host")
    return embed


class _HPStartModal(discord.ui.Modal, title="Start Host Session"):
    meet_name = discord.ui.TextInput(label="Meet Name", placeholder="Example: Tire Lettering Meet", max_length=100)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Server only.", ephemeral=True)
        if not _hp_has_role(interaction.user):
            return await interaction.response.send_message("Host role required.", ephemeral=True)

        data = _hp_load()
        for s in data["active_sessions"].values():
            if s["host_id"] == interaction.user.id and not s.get("ended"):
                return await interaction.response.send_message(
                    f"You already have an active session: **{s['meet_name']}**", ephemeral=True
                )

        parent = interaction.channel
        if not isinstance(parent, discord.TextChannel):
            return await interaction.response.send_message("Use this inside the host channel.", ephemeral=True)

        session_id = f"{interaction.user.id}-{int(datetime.utcnow().timestamp())}"
        try:
            thread = await parent.create_thread(
                name=f"host-session-{interaction.user.display_name[:20]}-{self.meet_name.value[:30]}",
                type=discord.ChannelType.private_thread if parent.guild.me.guild_permissions.create_private_threads else discord.ChannelType.public_thread,
                invitable=False if parent.guild.me.guild_permissions.create_private_threads else True,
            )
            try:
                await thread.add_user(interaction.user)
            except Exception:
                pass
        except Exception as e:
            return await interaction.response.send_message(f"Could not create session thread: {e}", ephemeral=True)

        session = {
            "session_id": session_id,
            "guild_id": interaction.guild_id,
            "channel_id": parent.id,
            "thread_id": thread.id,
            "host_id": interaction.user.id,
            "host_name": interaction.user.display_name,
            "meet_name": self.meet_name.value,
            "started_at": _hp_utcnow(),
            "ended_at": None,
            "blacklist_checked": False,
            "checklist_completed": False,
            "lobby_opened": False,
            "lobby_proof_posted": False,
            "todays_meet_posted": False,
            "total_attendance": 0,
            "diff_attendance": 0,
            "ended": False,
            "score": 0,
            "warning_count": 0,
        }
        data["active_sessions"][session_id] = session
        _hp_save(data)

        await thread.send(embed=_hp_session_embed(session), view=HostSessionView())
        await interaction.response.send_message(
            f"Host session started: {thread.mention}", ephemeral=True
        )


class _HPAttendanceModal(discord.ui.Modal, title="Submit Attendance"):
    total_attendance = discord.ui.TextInput(label="Total Attendance", placeholder="18", max_length=4)
    diff_attendance = discord.ui.TextInput(label="DIFF Attendance", placeholder="7", max_length=4)

    def __init__(self, session_id: str):
        super().__init__()
        self.session_id = session_id

    async def on_submit(self, interaction: discord.Interaction) -> None:
        data = _hp_load()
        session = data["active_sessions"].get(self.session_id)
        if not session:
            return await interaction.response.send_message("Session not found.", ephemeral=True)
        try:
            total = max(0, int(str(self.total_attendance.value)))
            diff = max(0, int(str(self.diff_attendance.value)))
        except ValueError:
            return await interaction.response.send_message("Attendance must be valid numbers.", ephemeral=True)
        session["total_attendance"] = total
        session["diff_attendance"] = diff
        _hp_save(data)
        await interaction.response.send_message(
            f"Attendance updated. Total: **{total}** | DIFF: **{diff}**", ephemeral=True
        )
        if isinstance(interaction.channel, discord.Thread):
            await interaction.channel.send(embed=_hp_session_embed(session), view=HostSessionView())


class HostSessionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def _get_session(self, interaction: discord.Interaction):
        if not isinstance(interaction.channel, discord.Thread):
            await interaction.response.send_message("Use this inside a session thread.", ephemeral=True)
            return None
        data = _hp_load()
        for s in data["active_sessions"].values():
            if s["thread_id"] == interaction.channel.id and not s.get("ended"):
                return s, data
        await interaction.response.send_message("No active session found in this thread.", ephemeral=True)
        return None

    async def _refresh_embed(self, thread: discord.Thread, session: dict) -> None:
        try:
            async for msg in thread.history(limit=15, oldest_first=True):
                if msg.author.id == bot.user.id and msg.embeds:
                    await msg.edit(embed=_hp_session_embed(session), view=self)
                    return
        except Exception:
            pass

    @discord.ui.button(label="Blacklist Checked", emoji="🚫", style=discord.ButtonStyle.danger,
                       custom_id="diff_host_session:blacklist_checked", row=0)
    async def blacklist_checked(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = await self._get_session(interaction)
        if not result:
            return
        session, data = result
        session["blacklist_checked"] = True
        _hp_save(data)
        await self._refresh_embed(interaction.channel, session)
        await interaction.response.send_message("Blacklist check confirmed. ✅", ephemeral=True)

    @discord.ui.button(label="Checklist Complete", emoji="📝", style=discord.ButtonStyle.success,
                       custom_id="diff_host_session:checklist_complete", row=0)
    async def checklist_complete(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = await self._get_session(interaction)
        if not result:
            return
        session, data = result
        session["checklist_completed"] = True
        _hp_save(data)
        await self._refresh_embed(interaction.channel, session)
        await interaction.response.send_message("Checklist completion confirmed. ✅", ephemeral=True)

    @discord.ui.button(label="Lobby Opened", emoji="🚪", style=discord.ButtonStyle.primary,
                       custom_id="diff_host_session:lobby_opened", row=0)
    async def lobby_opened(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = await self._get_session(interaction)
        if not result:
            return
        session, data = result
        session["lobby_opened"] = True
        _hp_save(data)
        await self._refresh_embed(interaction.channel, session)
        await interaction.response.send_message("Lobby opening confirmed. ✅", ephemeral=True)

    @discord.ui.button(label="Proof Posted", emoji="📸", style=discord.ButtonStyle.secondary,
                       custom_id="diff_host_session:proof_posted", row=1)
    async def proof_posted(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = await self._get_session(interaction)
        if not result:
            return
        session, data = result
        session["lobby_proof_posted"] = True
        _hp_save(data)
        await self._refresh_embed(interaction.channel, session)
        await interaction.response.send_message("Lobby proof confirmed. ✅", ephemeral=True)

    @discord.ui.button(label="Today's Meet Posted", emoji="📢", style=discord.ButtonStyle.primary,
                       custom_id="diff_host_session:todays_meet_posted", row=1)
    async def todays_meet_posted(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = await self._get_session(interaction)
        if not result:
            return
        session, data = result
        session["todays_meet_posted"] = True
        _hp_save(data)
        await self._refresh_embed(interaction.channel, session)
        await interaction.response.send_message("Today's Meet confirmation saved. ✅", ephemeral=True)

    @discord.ui.button(label="Submit Attendance", emoji="📊", style=discord.ButtonStyle.success,
                       custom_id="diff_host_session:submit_attendance", row=1)
    async def submit_attendance(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = await self._get_session(interaction)
        if not result:
            return
        session, _ = result
        await interaction.response.send_modal(_HPAttendanceModal(session["session_id"]))

    @discord.ui.button(label="End Meet Session", emoji="🏁", style=discord.ButtonStyle.danger,
                       custom_id="diff_host_session:end_session", row=2)
    async def end_session(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = await self._get_session(interaction)
        if not result:
            return
        session, data = result

        is_host = interaction.user.id == session["host_id"]
        is_staff = isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.manage_guild
        if not is_host and not is_staff:
            return await interaction.response.send_message("Only the session host or staff can end this session.", ephemeral=True)

        session["ended"] = True
        session["ended_at"] = _hp_utcnow()
        score, warnings = _hp_score(session)
        session["score"] = score
        session["warning_count"] = len(warnings)

        stats = data["host_stats"].setdefault(str(session["host_id"]), {
            "host_name": session["host_name"],
            "meets_hosted": 0, "total_attendance_sum": 0, "diff_attendance_sum": 0,
            "blacklist_checks": 0, "checklists_completed": 0, "lobby_proofs": 0,
            "todays_meet_posts": 0, "warning_count": 0, "score_total": 0, "last_session_at": None,
        })
        stats["host_name"] = session["host_name"]
        stats["meets_hosted"] += 1
        stats["total_attendance_sum"] += session["total_attendance"]
        stats["diff_attendance_sum"] += session["diff_attendance"]
        stats["blacklist_checks"] += 1 if session["blacklist_checked"] else 0
        stats["checklists_completed"] += 1 if session["checklist_completed"] else 0
        stats["lobby_proofs"] += 1 if session["lobby_proof_posted"] else 0
        stats["todays_meet_posts"] += 1 if session["todays_meet_posted"] else 0
        stats["warning_count"] += len(warnings)
        stats["score_total"] += score
        stats["last_session_at"] = session["ended_at"]
        _hp_save(data)

        await self._refresh_embed(interaction.channel, session)

        staff_ch = bot.get_channel(STAFF_LOGS_CHANNEL_ID)
        if isinstance(staff_ch, discord.TextChannel):
            log_embed = discord.Embed(
                title="📊 Host Performance Update",
                description=f"Host performance logged for <@{session['host_id']}>.",
                color=discord.Color.blue(),
            )
            log_embed.add_field(name="Session Summary", value=(
                f"Meet: **{session['meet_name']}**\n"
                f"Total Attendance: **{session['total_attendance']}**\n"
                f"DIFF Attendance: **{session['diff_attendance']}**\n"
                f"Score: **{score}**\n"
                f"Warnings: **{len(warnings)}**"
            ), inline=False)
            log_embed.add_field(name="Compliance", value=(
                f"Blacklist Checked: {'✅' if session['blacklist_checked'] else '❌'}\n"
                f"Checklist Completed: {'✅' if session['checklist_completed'] else '❌'}\n"
                f"Lobby Proof Posted: {'✅' if session['lobby_proof_posted'] else '❌'}\n"
                f"Today's Meet Posted: {'✅' if session['todays_meet_posted'] else '❌'}"
            ), inline=False)
            log_embed.set_footer(text="Auto-generated by DIFF Host Performance System")
            await staff_ch.send(embed=log_embed)
            for issue in warnings:
                warn_embed = discord.Embed(
                    title="⚠️ Host Warning Logged",
                    description=f"A host warning has been logged for <@{session['host_id']}>.",
                    color=discord.Color.red(),
                )
                warn_embed.add_field(name="Warning Details", value=(
                    f"Meet: **{session['meet_name']}**\n"
                    f"Issue: **{issue}**\n"
                    f"Session ID: `{session['session_id']}`"
                ), inline=False)
                warn_embed.set_footer(text="Logged automatically for staff review")
                await staff_ch.send(embed=warn_embed)

        await interaction.response.send_message(
            f"Meet session ended. Score: **{score}** | Warnings: **{len(warnings)}**", ephemeral=True
        )
        try:
            await interaction.channel.send(
                f"Session closed for <@{session['host_id']}>.\n"
                f"Final Score: **{score}** | Warnings: **{len(warnings)}**"
            )
        except Exception:
            pass


class HostPerformanceHubView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Start Meet Session", emoji="🟢", style=discord.ButtonStyle.success,
                       custom_id="diff_host_performance:start_session", row=0)
    async def start_session(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member) or not _hp_has_role(interaction.user):
            return await interaction.response.send_message("Host role required.", ephemeral=True)
        await interaction.response.send_modal(_HPStartModal())

    @discord.ui.button(label="My Host Stats", emoji="📊", style=discord.ButtonStyle.primary,
                       custom_id="diff_host_performance:my_stats", row=0)
    async def my_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = _hp_load()
        stats = data["host_stats"].get(str(interaction.user.id))
        if not stats:
            return await interaction.response.send_message("No host stats found yet.", ephemeral=True)
        await interaction.response.send_message(embed=_hp_stats_embed(interaction.user, stats), ephemeral=True)

    @discord.ui.button(label="System Info", emoji="⚠️", style=discord.ButtonStyle.secondary,
                       custom_id="diff_host_performance:system_info", row=0)
    async def system_info(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="⚠️ DIFF Host Performance System Info",
            description="*Here is what this system tracks automatically during each host session.*",
            color=discord.Color.orange(),
        )
        embed.add_field(name="📊 Performance Tracking", value=(
            "• Meets hosted\n• Total attendance\n• DIFF attendance\n"
            "• Blacklist confirmations\n• Checklist confirmations\n"
            "• Lobby proof confirmations\n• Today's Meet confirmations\n• Host session score"
        ), inline=False)
        embed.add_field(name="🚨 Warning Triggers", value=(
            "• Blacklist not checked\n• Checklist not completed\n"
            "• Lobby proof missing\n• Today's Meet post missing\n"
            "• Session ended with missing required steps"
        ), inline=False)
        embed.set_footer(text="Hosts are expected to use the tracking thread for every meet")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def _hp_post_or_refresh() -> None:
    channel = bot.get_channel(HOST_HUB_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        try:
            channel = await bot.fetch_channel(HOST_HUB_CHANNEL_ID)
        except Exception:
            return
    if not isinstance(channel, discord.TextChannel):
        return
    data = _hp_load()
    msg_id = _hp_get_hub_msg_id(data)
    embed = _hp_hub_embed()
    view = HostPerformanceHubView()
    if msg_id:
        try:
            msg = await channel.fetch_message(msg_id)
            await msg.edit(embed=embed, view=view)
            return
        except Exception:
            pass
    try:
        msg = await channel.send(embed=embed, view=view)
        data["hub_message_id"] = msg.id
        _hp_save(data)
    except Exception as e:
        print(f"[HP] post error: {e}")


@bot.command(name="hostperformance")
async def cmd_hostperformance(ctx: commands.Context):
    if not any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID} for r in ctx.author.roles):
        return await ctx.reply("Manager+ only.", mention_author=False)
    await _hp_post_or_refresh()
    await ctx.reply("Host Performance Hub posted/updated.", mention_author=False)


# =========================
# AUTO ROLL CALL SYSTEM
# =========================
_RC_DB_PATH = os.path.join("diff_data", "diff_rollcall.db")
_RC_ADMIN_ROLE_IDS = {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID}


class _RollCallDB:
    def __init__(self):
        os.makedirs("diff_data", exist_ok=True)
        self.conn = sqlite3.connect(_RC_DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._setup()

    def _setup(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS rollcall_panels (
                guild_id INTEGER PRIMARY KEY,
                channel_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                admin_message_id INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS rollcall_meets (
                guild_id INTEGER NOT NULL,
                meet_number INTEGER NOT NULL,
                class_name TEXT NOT NULL DEFAULT 'TBD',
                start_time TEXT NOT NULL DEFAULT 'TBD',
                host_id INTEGER,
                date_text TEXT NOT NULL DEFAULT 'TBD',
                is_finalized INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (guild_id, meet_number)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS rollcall_responses (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                meet_number INTEGER NOT NULL,
                status TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (guild_id, user_id, meet_number)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS attendance_actual (
                guild_id INTEGER NOT NULL,
                meet_number INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                recorded_at TEXT NOT NULL,
                PRIMARY KEY (guild_id, meet_number, user_id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS attendance_stats (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                yes_count INTEGER NOT NULL DEFAULT 0,
                maybe_count INTEGER NOT NULL DEFAULT 0,
                no_count INTEGER NOT NULL DEFAULT 0,
                attended_count INTEGER NOT NULL DEFAULT 0,
                no_show_count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (guild_id, user_id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS meet_state (
                guild_id INTEGER NOT NULL,
                meet_number INTEGER NOT NULL,
                attendance_finalized INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (guild_id, meet_number)
            )
        """)
        self.conn.commit()

    def upsert_panel(self, guild_id, channel_id, message_id, admin_message_id=None):
        now = datetime.utcnow().isoformat()
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO rollcall_panels (guild_id, channel_id, message_id, admin_message_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                channel_id=excluded.channel_id,
                message_id=excluded.message_id,
                admin_message_id=COALESCE(excluded.admin_message_id, rollcall_panels.admin_message_id),
                updated_at=excluded.updated_at
        """, (guild_id, channel_id, message_id, admin_message_id, now, now))
        self.conn.commit()

    def get_panel(self, guild_id):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM rollcall_panels WHERE guild_id=?", (guild_id,))
        return cur.fetchone()

    def clear_panel(self, guild_id):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM rollcall_panels WHERE guild_id=?", (guild_id,))
        self.conn.commit()

    def upsert_meets(self, guild_id, meets: list):
        cur = self.conn.cursor()
        for m in meets:
            cur.execute("""
                INSERT INTO rollcall_meets (guild_id, meet_number, class_name, start_time, host_id, date_text, is_finalized)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(guild_id, meet_number) DO UPDATE SET
                    class_name=excluded.class_name,
                    start_time=excluded.start_time,
                    host_id=excluded.host_id,
                    date_text=excluded.date_text,
                    is_finalized=excluded.is_finalized
            """, (guild_id, m["meet_number"], m.get("class_name", "TBD"), m.get("start_time", "TBD"),
                  m.get("host_id"), m.get("date_text", "TBD"), 1 if m.get("is_finalized") else 0))
            cur.execute("""
                INSERT OR IGNORE INTO meet_state (guild_id, meet_number, attendance_finalized) VALUES (?, ?, 0)
            """, (guild_id, m["meet_number"]))
        self.conn.commit()

    def get_meets(self, guild_id):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM rollcall_meets WHERE guild_id=? ORDER BY meet_number ASC", (guild_id,))
        return cur.fetchall()

    def set_response(self, guild_id, user_id, meet_number, status):
        now = datetime.utcnow().isoformat()
        cur = self.conn.cursor()
        cur.execute("SELECT status FROM rollcall_responses WHERE guild_id=? AND user_id=? AND meet_number=?",
                    (guild_id, user_id, meet_number))
        prev_row = cur.fetchone()
        previous = prev_row[0] if prev_row else None
        cur.execute("""
            INSERT INTO rollcall_responses (guild_id, user_id, meet_number, status, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(guild_id, user_id, meet_number) DO UPDATE SET status=excluded.status, updated_at=excluded.updated_at
        """, (guild_id, user_id, meet_number, status, now))
        cur.execute("INSERT OR IGNORE INTO attendance_stats (guild_id, user_id) VALUES (?, ?)", (guild_id, user_id))
        if previous in ("yes", "maybe", "no"):
            cur.execute(f"UPDATE attendance_stats SET {previous}_count = MAX({previous}_count - 1, 0) WHERE guild_id=? AND user_id=?",
                        (guild_id, user_id))
        if status in ("yes", "maybe", "no"):
            cur.execute(f"UPDATE attendance_stats SET {status}_count = {status}_count + 1 WHERE guild_id=? AND user_id=?",
                        (guild_id, user_id))
        self.conn.commit()
        return previous

    def get_counts(self, guild_id, meet_number):
        cur = self.conn.cursor()
        cur.execute("SELECT status, COUNT(*) AS total FROM rollcall_responses WHERE guild_id=? AND meet_number=? GROUP BY status",
                    (guild_id, meet_number))
        counts = {"yes": 0, "maybe": 0, "no": 0}
        for row in cur.fetchall():
            counts[row[0]] = row[1]
        return counts

    def get_all_counts(self, guild_id):
        return {n: self.get_counts(guild_id, n) for n in (1, 2, 3)}

    def set_actual_attendees(self, guild_id, meet_number, user_ids):
        now = datetime.utcnow().isoformat()
        cur = self.conn.cursor()
        cur.execute("DELETE FROM attendance_actual WHERE guild_id=? AND meet_number=?", (guild_id, meet_number))
        for uid in user_ids:
            cur.execute("INSERT INTO attendance_actual (guild_id, meet_number, user_id, recorded_at) VALUES (?, ?, ?, ?)",
                        (guild_id, meet_number, uid, now))
            cur.execute("INSERT OR IGNORE INTO attendance_stats (guild_id, user_id) VALUES (?, ?)", (guild_id, uid))
        self.conn.commit()

    def finalize_no_shows(self, guild_id, meet_number):
        cur = self.conn.cursor()
        cur.execute("SELECT attendance_finalized FROM meet_state WHERE guild_id=? AND meet_number=?",
                    (guild_id, meet_number))
        row = cur.fetchone()
        if row and row[0] == 1:
            return [], []
        cur.execute("SELECT user_id FROM attendance_actual WHERE guild_id=? AND meet_number=?", (guild_id, meet_number))
        actual = {r[0] for r in cur.fetchall()}
        cur.execute("SELECT user_id FROM rollcall_responses WHERE guild_id=? AND meet_number=? AND status='yes'",
                    (guild_id, meet_number))
        yes_users = {r[0] for r in cur.fetchall()}
        attended = sorted(actual)
        no_shows = sorted(yes_users - actual)
        for uid in attended:
            cur.execute("INSERT OR IGNORE INTO attendance_stats (guild_id, user_id) VALUES (?, ?)", (guild_id, uid))
            cur.execute("UPDATE attendance_stats SET attended_count=attended_count+1 WHERE guild_id=? AND user_id=?", (guild_id, uid))
        for uid in no_shows:
            cur.execute("INSERT OR IGNORE INTO attendance_stats (guild_id, user_id) VALUES (?, ?)", (guild_id, uid))
            cur.execute("UPDATE attendance_stats SET no_show_count=no_show_count+1 WHERE guild_id=? AND user_id=?", (guild_id, uid))
        cur.execute("""
            INSERT INTO meet_state (guild_id, meet_number, attendance_finalized) VALUES (?, ?, 1)
            ON CONFLICT(guild_id, meet_number) DO UPDATE SET attendance_finalized=1
        """, (guild_id, meet_number))
        self.conn.commit()
        return attended, no_shows

    def get_top_attendance(self, guild_id, limit=10):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT * FROM attendance_stats WHERE guild_id=?
            ORDER BY attended_count DESC, yes_count DESC, no_show_count ASC LIMIT ?
        """, (guild_id, limit))
        return cur.fetchall()


_rc_db = _RollCallDB()


def _rc_is_admin(member) -> bool:
    if not isinstance(member, discord.Member):
        return False
    if member.guild_permissions.administrator:
        return True
    return any(r.id in _RC_ADMIN_ROLE_IDS for r in member.roles)


def _rc_build_rollcall_embed(guild: discord.Guild) -> discord.Embed:
    meets = _rc_db.get_meets(guild.id)
    meets_by_num = {row["meet_number"]: row for row in meets}
    counts = _rc_db.get_all_counts(guild.id)
    embed = discord.Embed(
        title="📊 DIFF Auto Roll Call",
        description="Use the buttons below to mark your attendance for each meet.",
        color=discord.Color.blurple(),
        timestamp=datetime.utcnow(),
    )
    embed.set_author(name="Different Meets")
    for n in (1, 2, 3):
        meet = meets_by_num.get(n)
        c = counts[n]
        class_name = meet["class_name"] if meet else "TBD"
        start_time = meet["start_time"] if meet else "TBD"
        date_text = meet["date_text"] if meet else "TBD"
        host_id = meet["host_id"] if meet else None
        host_text = f"<@{host_id}>" if host_id else "*No host assigned*"
        finalized = "✅ Finalized" if meet and meet["is_finalized"] else "⏳ Pending"
        embed.add_field(
            name=f"Meet {n}",
            value=(
                f"📅 **Date:** {date_text}\n"
                f"🎮 **Class:** {class_name}\n"
                f"🕒 **Time:** {start_time}\n"
                f"👤 **Host:** {host_text}\n"
                f"📌 **Status:** {finalized}\n\n"
                f"✅ Attending: **{c['yes']}** | ❓ Maybe: **{c['maybe']}** | ❌ Not Attending: **{c['no']}**"
            ),
            inline=False,
        )
    embed.add_field(
        name="Reminders",
        value="🧥 Wear your crew jacket\n🎙️ Join voice chat if required\n⚠️ Repeated no-shows affect activity tracking",
        inline=False,
    )
    embed.set_footer(text="DIFF • Auto Roll Call System")
    return embed


def _rc_build_admin_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🛠️ DIFF Roll Call — Staff Tools",
        description="After each meet ends, click the button below to finalize attendance and detect no-shows.",
        color=discord.Color.dark_teal(),
    )
    embed.add_field(
        name="How it works",
        value="Click **Finalize Meet #**, paste or mention the users who actually attended. The system will update stats and flag no-shows automatically.",
        inline=False,
    )
    return embed


class _RcFinalizeModal(discord.ui.Modal):
    attendees = discord.ui.TextInput(
        label="Users who actually attended",
        style=discord.TextStyle.paragraph,
        placeholder="Paste mentions or IDs: <@123> <@456>",
        required=False,
        max_length=4000,
    )

    def __init__(self, meet_number: int):
        super().__init__(title=f"Finalize Meet {meet_number} Attendance")
        self.meet_number = meet_number

    async def on_submit(self, interaction: discord.Interaction):
        if not _rc_is_admin(interaction.user):
            await interaction.response.send_message("Staff only.", ephemeral=True)
            return
        raw = self.attendees.value or ""
        user_ids = sorted({int(m) for m in re.findall(r"\d{15,25}", raw)})
        _rc_db.set_actual_attendees(interaction.guild.id, self.meet_number, user_ids)
        attended, no_shows = _rc_db.finalize_no_shows(interaction.guild.id, self.meet_number)
        await _rc_refresh_panel(interaction.guild)
        await _rc_log_attendance(interaction.guild, self.meet_number, attended, no_shows, interaction.user)
        await interaction.response.send_message(
            f"✅ Meet {self.meet_number} finalized. Present: **{len(attended)}** | No-shows: **{len(no_shows)}**",
            ephemeral=True,
        )


class _RcRollCallView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def _handle(self, interaction: discord.Interaction, meet_number: int, status: str):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Server only.", ephemeral=True)
            return
        previous = _rc_db.set_response(interaction.guild.id, interaction.user.id, meet_number, status)
        await _rc_refresh_panel(interaction.guild)
        await _rc_log_rsvp(interaction.guild, interaction.user, meet_number, previous, status)
        labels = {"yes": "✅ marked as attending", "maybe": "❓ marked as maybe", "no": "❌ marked as not attending"}
        await interaction.response.send_message(f"You are {labels[status]} for **Meet {meet_number}**.", ephemeral=True)

    @discord.ui.button(label="Meet 1 ✅", style=discord.ButtonStyle.success, custom_id="diff_rollcall:1:yes", row=0)
    async def m1_yes(self, i, b): await self._handle(i, 1, "yes")

    @discord.ui.button(label="Meet 1 ❓", style=discord.ButtonStyle.secondary, custom_id="diff_rollcall:1:maybe", row=0)
    async def m1_maybe(self, i, b): await self._handle(i, 1, "maybe")

    @discord.ui.button(label="Meet 1 ❌", style=discord.ButtonStyle.danger, custom_id="diff_rollcall:1:no", row=0)
    async def m1_no(self, i, b): await self._handle(i, 1, "no")

    @discord.ui.button(label="Meet 2 ✅", style=discord.ButtonStyle.success, custom_id="diff_rollcall:2:yes", row=1)
    async def m2_yes(self, i, b): await self._handle(i, 2, "yes")

    @discord.ui.button(label="Meet 2 ❓", style=discord.ButtonStyle.secondary, custom_id="diff_rollcall:2:maybe", row=1)
    async def m2_maybe(self, i, b): await self._handle(i, 2, "maybe")

    @discord.ui.button(label="Meet 2 ❌", style=discord.ButtonStyle.danger, custom_id="diff_rollcall:2:no", row=1)
    async def m2_no(self, i, b): await self._handle(i, 2, "no")

    @discord.ui.button(label="Meet 3 ✅", style=discord.ButtonStyle.success, custom_id="diff_rollcall:3:yes", row=2)
    async def m3_yes(self, i, b): await self._handle(i, 3, "yes")

    @discord.ui.button(label="Meet 3 ❓", style=discord.ButtonStyle.secondary, custom_id="diff_rollcall:3:maybe", row=2)
    async def m3_maybe(self, i, b): await self._handle(i, 3, "maybe")

    @discord.ui.button(label="Meet 3 ❌", style=discord.ButtonStyle.danger, custom_id="diff_rollcall:3:no", row=2)
    async def m3_no(self, i, b): await self._handle(i, 3, "no")


class _RcAdminView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def _finalize(self, interaction: discord.Interaction, meet_number: int):
        if not _rc_is_admin(interaction.user):
            await interaction.response.send_message("Staff only.", ephemeral=True)
            return
        await interaction.response.send_modal(_RcFinalizeModal(meet_number))

    @discord.ui.button(label="Finalize Meet 1", style=discord.ButtonStyle.primary, custom_id="diff_rollcall_finalize:1", row=0)
    async def fin1(self, i, b): await self._finalize(i, 1)

    @discord.ui.button(label="Finalize Meet 2", style=discord.ButtonStyle.primary, custom_id="diff_rollcall_finalize:2", row=0)
    async def fin2(self, i, b): await self._finalize(i, 2)

    @discord.ui.button(label="Finalize Meet 3", style=discord.ButtonStyle.primary, custom_id="diff_rollcall_finalize:3", row=0)
    async def fin3(self, i, b): await self._finalize(i, 3)


async def _rc_refresh_panel(guild: discord.Guild):
    panel = _rc_db.get_panel(guild.id)
    channel = guild.get_channel(ROLL_CALL_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        return
    if not panel:
        await _rc_post_new_panel(guild, ping_roles=True)
        return
    try:
        msg = await channel.fetch_message(panel["message_id"])
        await msg.edit(embed=_rc_build_rollcall_embed(guild), view=_RcRollCallView())
    except discord.NotFound:
        await _rc_post_new_panel(guild, ping_roles=True)
    except Exception:
        pass


async def _rc_post_new_panel(guild: discord.Guild, ping_roles: bool = False):
    channel = guild.get_channel(ROLL_CALL_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        return
    ping_text = None
    if ping_roles:
        parts = []
        cr = guild.get_role(CREW_MEMBER_ROLE_ID)
        if cr:
            parts.append(cr.mention)
        ps5r = guild.get_role(PS5_ROLE_ID)
        if ps5r:
            parts.append(ps5r.mention)
        if parts:
            ping_text = " ".join(parts)
    try:
        rc_msg = await channel.send(
            content=ping_text,
            embed=_rc_build_rollcall_embed(guild),
            view=_RcRollCallView(),
            allowed_mentions=discord.AllowedMentions(roles=True),
        )
        admin_msg = await channel.send(embed=_rc_build_admin_embed(), view=_RcAdminView())
        _rc_db.upsert_panel(guild.id, channel.id, rc_msg.id, admin_msg.id)
    except Exception as e:
        print(f"[RollCall] post failed: {e}")


async def _rc_ensure_panel(guild: discord.Guild):
    panel = _rc_db.get_panel(guild.id)
    channel = guild.get_channel(ROLL_CALL_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        return
    if panel:
        try:
            await channel.fetch_message(panel["message_id"])
            return
        except discord.NotFound:
            pass
        except Exception:
            return
    await _rc_post_new_panel(guild, ping_roles=True)


async def _rc_log_rsvp(guild, member, meet_number, previous, new_status):
    ch = guild.get_channel(STAFF_LOGS_CHANNEL_ID)
    if not isinstance(ch, discord.TextChannel):
        return
    embed = discord.Embed(title="📋 Roll Call Update", color=discord.Color.orange(), timestamp=datetime.utcnow())
    embed.add_field(name="User", value=f"{member.mention} (`{member.id}`)", inline=False)
    embed.add_field(name="Meet", value=f"Meet {meet_number}", inline=True)
    embed.add_field(name="Previous", value=previous or "none", inline=True)
    embed.add_field(name="New", value=new_status, inline=True)
    try:
        await ch.send(embed=embed)
    except Exception:
        pass


async def _rc_log_attendance(guild, meet_number, attended, no_shows, action_by):
    ch = guild.get_channel(STAFF_LOGS_CHANNEL_ID)
    if not isinstance(ch, discord.TextChannel):
        return
    embed = discord.Embed(title="📊 Meet Attendance Finalized", color=discord.Color.green(), timestamp=datetime.utcnow())
    embed.add_field(name="Meet", value=f"Meet {meet_number}", inline=True)
    embed.add_field(name="Finalized By", value=action_by.mention, inline=True)
    embed.add_field(name="Present", value=str(len(attended)), inline=True)
    attended_text = " ".join(f"<@{uid}>" for uid in attended[:30]) or "None recorded"
    no_show_text = " ".join(f"<@{uid}>" for uid in no_shows[:30]) or "None"
    embed.add_field(name="Present Users", value=attended_text[:1024], inline=False)
    embed.add_field(name="No-Shows", value=no_show_text[:1024], inline=False)
    try:
        await ch.send(embed=embed)
    except Exception:
        pass


async def _rc_sync_from_schedule(guild: discord.Guild, meets: list):
    present = {m["meet_number"] for m in meets}
    for n in (1, 2, 3):
        if n not in present:
            meets.append({"meet_number": n, "class_name": "TBD", "start_time": "TBD", "host_id": None, "date_text": "TBD", "is_finalized": False})
    meets.sort(key=lambda x: x["meet_number"])
    _rc_db.upsert_meets(guild.id, meets)
    await _rc_refresh_panel(guild)


@tasks.loop(minutes=10)
async def _rc_ensure_loop():
    for guild in bot.guilds:
        try:
            await _rc_ensure_panel(guild)
        except Exception as e:
            print(f"[RollCall] ensure loop error: {e}")


@bot.command(name="postrollcall")
async def _cmd_postrollcall(ctx: commands.Context):
    if not _rc_is_admin(ctx.author):
        return
    try:
        await ctx.message.delete()
    except Exception:
        pass
    panel = _rc_db.get_panel(ctx.guild.id)
    if panel:
        channel = ctx.guild.get_channel(ROLL_CALL_CHANNEL_ID)
        if isinstance(channel, discord.TextChannel):
            for mid in (panel.get("message_id"), panel.get("admin_message_id")):
                if mid:
                    try:
                        old = await channel.fetch_message(mid)
                        await old.delete()
                    except Exception:
                        pass
        _rc_db.clear_panel(ctx.guild.id)
    await _rc_post_new_panel(ctx.guild, ping_roles=True)


@bot.command(name="rollleaderboard")
async def _cmd_rollleaderboard(ctx: commands.Context):
    rows = _rc_db.get_top_attendance(ctx.guild.id, 10)
    if not rows:
        await ctx.send("No attendance data yet.", delete_after=10)
        return
    embed = discord.Embed(title="🏆 DIFF Attendance Leaderboard", color=discord.Color.gold(), timestamp=datetime.utcnow())
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    lines = []
    for idx, row in enumerate(rows, 1):
        prefix = medals.get(idx, f"**{idx}.**")
        lines.append(f"{prefix} <@{row['user_id']}> — Attended: **{row['attended_count']}** | Yes RSVP: **{row['yes_count']}** | No-Shows: **{row['no_show_count']}**")
    embed.description = "\n".join(lines)
    await ctx.send(embed=embed)


# =========================
# OFFICIAL MEET ANNOUNCEMENT
# =========================

_OM_DATA_FILE = os.path.join(DATA_FOLDER, "diff_official_meets.json")
_om_rsvps: dict[int, dict[str, set]] = {}
_om_lock = asyncio.Lock()


@dataclass
class _OmRecord:
    message_id: int
    channel_id: int
    host_id: int
    theme: str
    timestamp: int
    started: bool = False
    ended: bool = False
    one_hour_sent: bool = False
    fifteen_sent: bool = False
    started_at_ts: int | None = None
    ended_at_ts: int | None = None
    attendance_message_id: int | None = None
    attendance_channel_id: int | None = None
    rsvp_yes_ids: list = field(default_factory=list)
    rsvp_maybe_ids: list = field(default_factory=list)
    rsvp_no_ids: list = field(default_factory=list)
    checked_in_ids: list = field(default_factory=list)
    late_ids: list = field(default_factory=list)
    unable_ids: list = field(default_factory=list)
    no_show_ids: list = field(default_factory=list)


def _om_load_records() -> dict:
    try:
        with open(_OM_DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _om_save_records(data: dict) -> None:
    try:
        with open(_OM_DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[OfficialMeet] save error: {e}")


def _om_get_record(msg_id: int) -> _OmRecord | None:
    data = _om_load_records()
    raw = data.get(str(msg_id))
    if not raw:
        return None
    try:
        return _OmRecord(**{k: v for k, v in raw.items() if k in _OmRecord.__dataclass_fields__})
    except Exception:
        return None


def _om_upsert_record(record: _OmRecord) -> None:
    data = _om_load_records()
    data[str(record.message_id)] = asdict(record)
    _om_save_records(data)


def _om_get_record_by_attendance_msg(attendance_msg_id: int) -> _OmRecord | None:
    data = _om_load_records()
    for raw in data.values():
        if raw.get("attendance_message_id") == attendance_msg_id:
            try:
                return _OmRecord(**{k: v for k, v in raw.items() if k in _OmRecord.__dataclass_fields__})
            except Exception:
                pass
    return None


# ---- Stats store ----
_OM_STATS_FILE = os.path.join(DATA_FOLDER, "diff_om_stats.json")
_OM_LEADERBOARD_CHANNEL_ID = 1485282044392243290


def _om_stats_load() -> dict:
    try:
        with open(_OM_STATS_FILE) as f:
            return json.load(f)
    except Exception:
        return {"members": {}, "hosts": {}}


def _om_stats_save(data: dict) -> None:
    try:
        with open(_OM_STATS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def _om_increment_member_stat(user_id: int, field_name: str, amount: int = 1) -> None:
    data = _om_stats_load()
    members = data.setdefault("members", {})
    entry = members.setdefault(str(user_id), {"user_id": user_id, "attended": 0, "late": 0, "unable": 0, "no_shows": 0})
    entry[field_name] = int(entry.get(field_name, 0)) + amount
    _om_stats_save(data)


def _om_increment_host_stat(user_id: int, field_name: str, amount: int = 1) -> None:
    data = _om_stats_load()
    hosts = data.setdefault("hosts", {})
    entry = hosts.setdefault(str(user_id), {
        "user_id": user_id, "meets_hosted": 0, "meets_completed": 0,
        "total_attendance": 0, "total_late": 0, "total_no_shows": 0,
    })
    entry[field_name] = int(entry.get(field_name, 0)) + amount
    _om_stats_save(data)


async def _om_post_or_update_leaderboard() -> None:
    channel = bot.get_channel(_OM_LEADERBOARD_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        return
    data = _om_stats_load()
    host_list = sorted(
        data.get("hosts", {}).values(),
        key=lambda x: (x.get("meets_completed", 0), x.get("total_attendance", 0)),
        reverse=True,
    )
    member_list = sorted(
        data.get("members", {}).values(),
        key=lambda x: (x.get("attended", 0), -x.get("no_shows", 0)),
        reverse=True,
    )
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    host_lines = []
    for i, s in enumerate(host_list[:10], 1):
        prefix = medals.get(i, f"**{i}.**")
        host_lines.append(
            f"{prefix} <@{s['user_id']}> — Hosted: **{s.get('meets_hosted', 0)}** | "
            f"Completed: **{s.get('meets_completed', 0)}** | "
            f"Attendance: **{s.get('total_attendance', 0)}** | "
            f"No-Shows: **{s.get('total_no_shows', 0)}**"
        )
    member_lines = []
    for i, s in enumerate(member_list[:10], 1):
        prefix = medals.get(i, f"**{i}.**")
        member_lines.append(
            f"{prefix} <@{s['user_id']}> — Attended: **{s.get('attended', 0)}** | "
            f"Late: **{s.get('late', 0)}** | "
            f"No-Shows: **{s.get('no_shows', 0)}**"
        )
    content = (
        "🏆 **DIFF Activity Leaderboard**\n\n"
        "**Top Hosts**\n"
        + ("\n".join(host_lines) if host_lines else "No host data yet.")
        + "\n\n**Top Members**\n"
        + ("\n".join(member_lines) if member_lines else "No member data yet.")
    )
    try:
        async for msg in channel.history(limit=15):
            if msg.author == bot.user and "🏆 **DIFF Activity Leaderboard**" in (msg.content or ""):
                await msg.edit(content=content)
                return
    except Exception:
        pass
    await channel.send(content)


class _OmAttendanceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def _handle(self, interaction: discord.Interaction, state: str):
        record = _om_get_record_by_attendance_msg(interaction.message.id)
        if not record:
            await interaction.response.send_message("Meet record not found.", ephemeral=True)
            return
        if record.ended:
            await interaction.response.send_message("This meet has already ended.", ephemeral=True)
            return
        uid = interaction.user.id
        record.checked_in_ids = [x for x in record.checked_in_ids if x != uid]
        record.late_ids       = [x for x in record.late_ids       if x != uid]
        record.unable_ids     = [x for x in record.unable_ids     if x != uid]
        if state == "present":
            record.checked_in_ids.append(uid)
            reply = "✅ You've been checked in as **Present**."
        elif state == "late":
            record.late_ids.append(uid)
            reply = "🕐 You've been marked as **Late**."
        else:
            record.unable_ids.append(uid)
            reply = "❌ You've been marked as **Unable to Join**."
        _om_upsert_record(record)
        await interaction.response.send_message(reply, ephemeral=True)

    @discord.ui.button(label="Present", style=discord.ButtonStyle.success, custom_id="diff_om_att:present")
    async def btn_present(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "present")

    @discord.ui.button(label="Late", style=discord.ButtonStyle.secondary, custom_id="diff_om_att:late")
    async def btn_late(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "late")

    @discord.ui.button(label="Unable to Join", style=discord.ButtonStyle.danger, custom_id="diff_om_att:unable")
    async def btn_unable(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "unable")


async def _om_create_attendance_panel(record: _OmRecord) -> discord.Message | None:
    channel = bot.get_channel(MEET_ATTENDANCE_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        return None
    return await channel.send(
        f"<@&{PS5_ROLE_ID}>\n\n"
        f"📊 **DIFF Meet Attendance — {record.theme}**\n\n"
        f"Host: <@{record.host_id}>\n"
        f"Date: <t:{record.timestamp}:F>\n\n"
        f"Use the buttons below to check in:\n"
        f"• **Present** — you're here\n"
        f"• **Late** — joining a bit late\n"
        f"• **Unable to Join** — can't make it\n\n"
        f"Your check-in is recorded for attendance stats and no-show tracking.",
        view=_OmAttendanceView(),
        allowed_mentions=discord.AllowedMentions(roles=True, users=False),
    )


def _om_get_counts(msg_id: int) -> dict:
    data = _om_rsvps.get(msg_id, {})
    return {
        "yes": len(data.get("yes", set())),
        "maybe": len(data.get("maybe", set())),
        "no": len(data.get("no", set())),
    }


class _OfficialMeetRSVPView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def _handle_rsvp(self, interaction: discord.Interaction, status: str):
        msg_id = interaction.message.id
        uid = interaction.user.id
        if msg_id not in _om_rsvps:
            _om_rsvps[msg_id] = {"yes": set(), "maybe": set(), "no": set()}
        for s in ("yes", "maybe", "no"):
            _om_rsvps[msg_id][s].discard(uid)
        _om_rsvps[msg_id][status].add(uid)
        counts = _om_get_counts(msg_id)
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                if child.custom_id == "diff_om_rsvp:yes":
                    child.label = f"Attending ({counts['yes']})"
                elif child.custom_id == "diff_om_rsvp:maybe":
                    child.label = f"Maybe ({counts['maybe']})"
                elif child.custom_id == "diff_om_rsvp:no":
                    child.label = f"Not Attending ({counts['no']})"
        label_map = {"yes": "Attending", "maybe": "Maybe", "no": "Not Attending"}
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            f"You're marked as **{label_map[status]}** for this meet.", ephemeral=True
        )

    async def _handle_ctrl(self, interaction: discord.Interaction, action: str):
        msg_id = interaction.message.id
        record = _om_get_record(msg_id)
        member = interaction.user
        is_staff = (
            isinstance(member, discord.Member)
            and (member.guild_permissions.manage_guild or any(r.id in _JOIN_STAFF_ROLE_IDS for r in member.roles))
        )
        is_host = record and isinstance(member, discord.Member) and member.id == record.host_id
        if not (is_staff or is_host):
            await interaction.response.send_message("Only the assigned host or staff can use this.", ephemeral=True)
            return
        if not record:
            await interaction.response.send_message("Meet record not found.", ephemeral=True)
            return

        if action == "start":
            if record.started:
                await interaction.response.send_message("This meet has already been started.", ephemeral=True)
                return
            if record.ended:
                await interaction.response.send_message("This meet has already ended.", ephemeral=True)
                return
            record.started = True
            record.started_at_ts = int(datetime.now(timezone.utc).timestamp())
            att_msg = await _om_create_attendance_panel(record)
            if att_msg:
                record.attendance_message_id = att_msg.id
                record.attendance_channel_id = att_msg.channel.id
            _om_upsert_record(record)
            _om_increment_host_stat(record.host_id, "meets_hosted")
            ch = bot.get_channel(record.channel_id)
            att_ref = f"<#{MEET_ATTENDANCE_CHANNEL_ID}>" if att_msg else "#attendance"
            if isinstance(ch, discord.TextChannel):
                await ch.send(
                    f"<@&{PS5_ROLE_ID}> <@&{NOTIFY_ROLE_ID}>\n\n"
                    f"🚨 **DIFF Session Is Now Live**\n\n"
                    f"⏳ Started: <t:{record.timestamp}:R>\n\n"
                    f"🎮 Join through the host: <@{record.host_id}>\n"
                    f"💬 Head to #chat for instructions\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"📊 Attendance tracking is now open in {att_ref}.\n"
                    f"Check in with **Present**, **Late**, or **Unable to Join**.",
                    allowed_mentions=discord.AllowedMentions(roles=True, users=True),
                )
            await _om_staff_log("Meet Started", record, interaction.user)
            for child in self.children:
                if isinstance(child, discord.ui.Button) and child.custom_id == "diff_om_ctrl:start":
                    child.disabled = True
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(
                f"Meet marked as **live**. Attendance panel opened in <#{MEET_ATTENDANCE_CHANNEL_ID}>.",
                ephemeral=True,
            )

        elif action == "end":
            if record.ended:
                await interaction.response.send_message("This meet has already ended.", ephemeral=True)
                return
            record.ended = True
            record.ended_at_ts = int(datetime.now(timezone.utc).timestamp())
            rsvp_pool = set(record.rsvp_yes_ids) | set(record.rsvp_maybe_ids)
            if not rsvp_pool:
                rsvp_pool = set(x for x in _om_rsvps.get(record.message_id, {}).get("yes", set()))
                rsvp_pool |= set(x for x in _om_rsvps.get(record.message_id, {}).get("maybe", set()))
            present_pool = set(record.checked_in_ids) | set(record.late_ids) | set(record.unable_ids)
            record.no_show_ids = sorted(list(rsvp_pool - present_pool))
            _om_upsert_record(record)
            for uid in set(record.checked_in_ids):
                _om_increment_member_stat(uid, "attended")
            for uid in set(record.late_ids):
                _om_increment_member_stat(uid, "late")
            for uid in set(record.unable_ids):
                _om_increment_member_stat(uid, "unable")
            for uid in set(record.no_show_ids):
                _om_increment_member_stat(uid, "no_shows")
            _om_increment_host_stat(record.host_id, "meets_completed")
            _om_increment_host_stat(record.host_id, "total_attendance", len(set(record.checked_in_ids)))
            _om_increment_host_stat(record.host_id, "total_late", len(set(record.late_ids)))
            _om_increment_host_stat(record.host_id, "total_no_shows", len(set(record.no_show_ids)))
            ch = bot.get_channel(record.channel_id)
            if isinstance(ch, discord.TextChannel):
                await ch.send(
                    f"📌 **DIFF Meet Closed**\n\n"
                    f"Host: <@{record.host_id}>\n"
                    f"Theme: {record.theme}\n"
                    f"Scheduled Time: <t:{record.timestamp}:F>\n\n"
                    f"**Attendance Summary**\n"
                    f"• Present: **{len(set(record.checked_in_ids))}**\n"
                    f"• Late: **{len(set(record.late_ids))}**\n"
                    f"• Unable: **{len(set(record.unable_ids))}**\n"
                    f"• No-Shows: **{len(set(record.no_show_ids))}**\n\n"
                    f"Thank you to everyone who attended and helped keep the meet clean."
                )
            await _om_staff_log("Meet Ended", record, interaction.user)
            try:
                await _om_post_or_update_leaderboard()
            except Exception:
                pass
            for child in self.children:
                if isinstance(child, discord.ui.Button) and child.custom_id in ("diff_om_ctrl:start", "diff_om_ctrl:end"):
                    child.disabled = True
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(
                "Meet marked as **ended**. Attendance stats saved and leaderboard updated.",
                ephemeral=True,
            )

    @discord.ui.button(label="Attending (0)", style=discord.ButtonStyle.success, custom_id="diff_om_rsvp:yes", row=0)
    async def btn_yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_rsvp(interaction, "yes")

    @discord.ui.button(label="Maybe (0)", style=discord.ButtonStyle.secondary, custom_id="diff_om_rsvp:maybe", row=0)
    async def btn_maybe(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_rsvp(interaction, "maybe")

    @discord.ui.button(label="Not Attending (0)", style=discord.ButtonStyle.danger, custom_id="diff_om_rsvp:no", row=0)
    async def btn_no(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_rsvp(interaction, "no")

    @discord.ui.button(label="▶ Start Meet", style=discord.ButtonStyle.success, custom_id="diff_om_ctrl:start", row=1)
    async def btn_start(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_ctrl(interaction, "start")

    @discord.ui.button(label="⏹ End Meet", style=discord.ButtonStyle.danger, custom_id="diff_om_ctrl:end", row=1)
    async def btn_end(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_ctrl(interaction, "end")


async def _om_staff_log(title: str, record: _OmRecord, acted_by: discord.Member) -> None:
    ch = bot.get_channel(STAFF_LOGS_CHANNEL_ID)
    if not isinstance(ch, discord.TextChannel):
        return
    embed = discord.Embed(title=f"🏁 {title}", color=discord.Color.blurple(), timestamp=datetime.now(timezone.utc))
    embed.add_field(name="Host", value=f"<@{record.host_id}>", inline=True)
    embed.add_field(name="Theme", value=record.theme, inline=True)
    embed.add_field(name="Scheduled", value=f"<t:{record.timestamp}:F>", inline=False)
    embed.add_field(name="Action By", value=acted_by.mention, inline=True)
    try:
        await ch.send(embed=embed)
    except Exception:
        pass


async def _om_reminder_task(msg_id: int, delay_secs: int, reminder_type: str) -> None:
    try:
        if delay_secs > 0:
            await asyncio.sleep(delay_secs)
        record = _om_get_record(msg_id)
        if not record or record.ended:
            return
        if reminder_type == "1h" and record.one_hour_sent:
            return
        if reminder_type == "15m" and record.fifteen_sent:
            return
        ch = bot.get_channel(record.channel_id)
        if isinstance(ch, discord.TextChannel):
            if reminder_type == "1h":
                await ch.send(
                    "⏳ **DIFF Meet Reminder**\n\n"
                    "This meet begins in:\n"
                    f"<t:{record.timestamp}:R>\n\n"
                    "Be ready with your build and check in with the host."
                )
                record.one_hour_sent = True
            else:
                await ch.send(
                    "🚨 **DIFF Meet Starting Soon**\n\n"
                    f"⏳ <t:{record.timestamp}:R>\n\n"
                    "Make sure you're ready to join and have your cars prepared."
                )
                record.fifteen_sent = True
            _om_upsert_record(record)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"[OfficialMeet] reminder error: {e}")


def _om_schedule_reminders(record: _OmRecord) -> None:
    now_ts = int(datetime.now(timezone.utc).timestamp())
    if not record.one_hour_sent:
        delay = record.timestamp - now_ts - 3600
        asyncio.create_task(_om_reminder_task(record.message_id, max(delay, 0), "1h"))
    if not record.fifteen_sent:
        delay = record.timestamp - now_ts - 900
        asyncio.create_task(_om_reminder_task(record.message_id, max(delay, 0), "15m"))


async def _om_restore_on_ready() -> None:
    await bot.wait_until_ready()
    data = _om_load_records()
    now_ts = int(datetime.now(timezone.utc).timestamp())
    for raw in data.values():
        try:
            record = _OmRecord(**{k: v for k, v in raw.items() if k in _OmRecord.__dataclass_fields__})
        except Exception:
            continue
        if record.ended and record.timestamp < now_ts - 86400:
            continue
        _om_schedule_reminders(record)
        if record.started or record.ended:
            ch = bot.get_channel(record.channel_id)
            if isinstance(ch, discord.TextChannel):
                try:
                    msg = await ch.fetch_message(record.message_id)
                    view = _OfficialMeetRSVPView()
                    for child in view.children:
                        if isinstance(child, discord.ui.Button):
                            if child.custom_id == "diff_om_ctrl:start" and (record.started or record.ended):
                                child.disabled = True
                            if child.custom_id == "diff_om_ctrl:end" and record.ended:
                                child.disabled = True
                    await msg.edit(view=view)
                except Exception:
                    pass


def _om_build_message(theme: str, host: discord.Member, timestamp: int) -> str:
    ps_ping = f"<@&{PS5_ROLE_ID}>"
    cm_ping = f"<@&{NOTIFY_ROLE_ID}>"
    return (
        f"{ps_ping} {cm_ping}\n\n"
        f"🏁 **DIFF Official Meet**\n\n"
        f"Date: <t:{timestamp}:F>\n"
        f"Begins: <t:{timestamp}:R>\n"
        f"Host: {host.mention}\n"
        f"Theme: {theme}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"**Entry Info**\n\n"
        f"Send your vehicle photos to the host before joining, unless told otherwise.\n\n"
        f"All vehicles must match the meet theme and follow the standards listed in #meet-info and #rules.\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"**Meet Notes**\n\n"
        f"• Follow all host instructions at all times\n"
        f"• Use #chat for meet communication and updates\n"
        f"• Bring clean, realistic, theme-fitting vehicles only\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"**Style Direction**\n\n"
        f"Choose vehicles that match tonight's theme and represent DIFF properly."
    )


@bot.command(name="officialmeet")
async def _cmd_officialmeet(ctx: commands.Context, theme: str, date: str, time_str: str, host: discord.Member):
    if not ctx.author.guild_permissions.manage_guild and not any(
        r.id in _JOIN_STAFF_ROLE_IDS for r in getattr(ctx.author, "roles", [])
    ):
        return
    try:
        await ctx.message.delete()
    except Exception:
        pass
    channel = bot.get_channel(_OFFICIAL_MEET_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        await ctx.send("Meet announcement channel not found.", delete_after=10)
        return
    try:
        local_dt = datetime.strptime(f"{date} {time_str}", "%Y-%m-%d %H:%M").replace(
            tzinfo=ZoneInfo(_OFFICIAL_MEET_TZ)
        )
    except ValueError:
        await ctx.send("Invalid date/time. Use: `!officialmeet \"Theme\" YYYY-MM-DD HH:MM @Host`", delete_after=15)
        return
    meet_ts = int(local_dt.timestamp())
    if meet_ts <= int(datetime.now(timezone.utc).timestamp()):
        await ctx.send("That meet time is already in the past.", delete_after=10)
        return
    try:
        sent = await channel.send(
            _om_build_message(theme=theme, host=host, timestamp=meet_ts),
            view=_OfficialMeetRSVPView(),
            allowed_mentions=discord.AllowedMentions(roles=True, users=True),
        )
    except discord.Forbidden:
        await ctx.send("Missing permissions to post in the meet channel.", delete_after=10)
        return
    record = _OmRecord(
        message_id=sent.id,
        channel_id=channel.id,
        host_id=host.id,
        theme=theme,
        timestamp=meet_ts,
    )
    _om_upsert_record(record)
    _om_schedule_reminders(record)
    await ctx.send(f"Official meet posted in {channel.mention} for <t:{meet_ts}:F>.", delete_after=15)


# =========================
# OFFICIAL MEET PANEL
# =========================

_OM_PANEL_FILE = os.path.join(DATA_FOLDER, "diff_om_panel.json")


def _om_panel_load() -> dict:
    try:
        with open(_OM_PANEL_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def _om_panel_save(data: dict):
    try:
        with open(_OM_PANEL_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def _om_parse_datetime(date_str: str, time_str: str) -> int | None:
    """Parse 'YYYY-MM-DD' + '8pm EST' into a Unix timestamp. Returns None on failure."""
    from datetime import timedelta
    tz_abbr = "EST"
    clean_time = time_str.strip()
    m = re.search(r'([A-Za-z]{2,4})$', clean_time)
    if m:
        tz_abbr = m.group(1).upper()
        clean_time = clean_time[:m.start()].strip()
    tz_name = _POPUP_TZ_MAP.get(tz_abbr, "America/New_York")
    try:
        tz = ZoneInfo(tz_name)
        date_part = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
        tm = re.match(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', clean_time, re.IGNORECASE)
        if not tm:
            return None
        hour = int(tm.group(1))
        minute = int(tm.group(2)) if tm.group(2) else 0
        meridiem = tm.group(3).lower() if tm.group(3) else None
        if meridiem == "pm" and hour != 12:
            hour += 12
        elif meridiem == "am" and hour == 12:
            hour = 0
        local_dt = datetime(date_part.year, date_part.month, date_part.day, hour, minute, tzinfo=tz)
        return int(local_dt.timestamp())
    except Exception:
        return None


def _om_panel_build_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🏁 DIFF Official Meet Hub",
        color=discord.Color.dark_gold(),
        description=(
            "Use the button below to schedule and post an official DIFF meet announcement.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "**What gets posted**\n"
            "• Full meet announcement with role pings\n"
            "• Auto-converting Discord timestamp (every member sees their own timezone)\n"
            "• Entry info, meet notes, and style direction\n"
            "• RSVP buttons for members\n"
            "• Start / End meet controls for the host\n"
            "• Automatic 1-hour and 15-minute reminders\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "**Restricted to staff and assigned hosts.**"
        ),
    )
    embed.set_footer(text="DIFF Official Meet System")
    return embed


class _OfficialMeetScheduleModal(discord.ui.Modal, title="🏁 Schedule Official Meet"):
    theme_field = discord.ui.TextInput(
        label="Theme",
        placeholder="e.g. Tire Lettering / JDM Night / Stanced Only",
        required=True,
        max_length=100,
    )
    date_field = discord.ui.TextInput(
        label="Date (YYYY-MM-DD)",
        placeholder="e.g. 2026-04-05",
        required=True,
        max_length=20,
    )
    time_field = discord.ui.TextInput(
        label="Time",
        placeholder="e.g. 8pm EST  or  8:30pm CST  or  20:00 ET",
        required=True,
        max_length=50,
    )
    host_field = discord.ui.TextInput(
        label="Host (user ID or @mention)",
        placeholder="e.g. 123456789012345678  or paste their @mention",
        required=True,
        max_length=100,
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("Server only.", ephemeral=True)
            return

        raw_host = self.host_field.value.strip()
        host_id_match = re.search(r'\d{15,20}', raw_host)
        if not host_id_match:
            await interaction.response.send_message(
                "Couldn't find a valid user ID. Paste their user ID or @mention.", ephemeral=True
            )
            return
        host_id = int(host_id_match.group())
        host_member = guild.get_member(host_id)
        if not host_member:
            try:
                host_member = await guild.fetch_member(host_id)
            except Exception:
                await interaction.response.send_message(
                    "That user wasn't found in the server.", ephemeral=True
                )
                return

        meet_ts = _om_parse_datetime(self.date_field.value, self.time_field.value)
        if meet_ts is None:
            await interaction.response.send_message(
                "Couldn't parse the date/time. Use format: `YYYY-MM-DD` and `8pm EST`.", ephemeral=True
            )
            return
        if meet_ts <= int(datetime.now(timezone.utc).timestamp()):
            await interaction.response.send_message("That date/time is already in the past.", ephemeral=True)
            return

        channel = bot.get_channel(_OFFICIAL_MEET_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("Meet channel not found.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        try:
            sent = await channel.send(
                _om_build_message(theme=self.theme_field.value.strip(), host=host_member, timestamp=meet_ts),
                view=_OfficialMeetRSVPView(),
                allowed_mentions=discord.AllowedMentions(roles=True, users=True),
            )
        except discord.Forbidden:
            await interaction.followup.send("Missing permissions to post in the meet channel.", ephemeral=True)
            return

        record = _OmRecord(
            message_id=sent.id,
            channel_id=channel.id,
            host_id=host_member.id,
            theme=self.theme_field.value.strip(),
            timestamp=meet_ts,
        )
        _om_upsert_record(record)
        _om_schedule_reminders(record)
        await interaction.followup.send(
            f"Official meet posted for <t:{meet_ts}:F>.", ephemeral=True
        )
        try:
            await _om_panel_post_or_refresh(guild, force_repost=True)
        except Exception:
            pass


class _OfficialMeetPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📋 Schedule Official Meet", style=discord.ButtonStyle.primary, custom_id="diff_om_panel:schedule")
    async def schedule_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user
        if not isinstance(member, discord.Member):
            await interaction.response.send_message("Server only.", ephemeral=True)
            return
        is_staff = member.guild_permissions.manage_guild or any(r.id in _JOIN_STAFF_ROLE_IDS for r in member.roles)
        if not is_staff:
            await interaction.response.send_message("Only staff can schedule official meets.", ephemeral=True)
            return
        await interaction.response.send_modal(_OfficialMeetScheduleModal())


async def _om_panel_post_or_refresh(guild: discord.Guild, force_repost: bool = False):
    """Post or refresh the Official Meet panel.

    force_repost=False (startup): edit existing in place, or create if missing.
    force_repost=True  (after new meet posted): delete old panel, send fresh one at
                        the bottom of the channel so it's always visible.
    """
    channel = guild.get_channel(_OFFICIAL_MEET_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        try:
            channel = await guild.fetch_channel(_OFFICIAL_MEET_CHANNEL_ID)
        except Exception:
            return
    if not isinstance(channel, discord.TextChannel):
        return

    data = _om_panel_load()
    msg_id = data.get(str(guild.id))

    if force_repost:
        if msg_id:
            try:
                old = await channel.fetch_message(int(msg_id))
                await old.delete()
            except Exception:
                pass
        msg = await channel.send(
            embed=_om_panel_build_embed(),
            view=_OfficialMeetPanelView(),
        )
        data[str(guild.id)] = msg.id
        _om_panel_save(data)
        return

    if msg_id:
        try:
            msg = await channel.fetch_message(int(msg_id))
            await msg.edit(embed=_om_panel_build_embed(), view=_OfficialMeetPanelView())
            return
        except discord.NotFound:
            pass
        except Exception:
            return

    msg = await channel.send(embed=_om_panel_build_embed(), view=_OfficialMeetPanelView())
    data[str(guild.id)] = msg.id
    _om_panel_save(data)


@bot.command(name="postofficialmeetpanel")
async def _cmd_postofficialmeetpanel(ctx: commands.Context):
    is_auth = (
        ctx.author.guild_permissions.administrator
        or (ctx.guild and ctx.guild.owner_id == ctx.author.id)
        or any(r.id in _JOIN_STAFF_ROLE_IDS for r in getattr(ctx.author, "roles", []))
    )
    if not is_auth:
        await ctx.send("Staff only.", delete_after=6)
        return
    try:
        await ctx.message.delete()
    except Exception:
        pass
    await _om_panel_post_or_refresh(ctx.guild)


# =========================
# POP-UP MEET SYSTEM
# =========================

_POPUP_PANEL_CHANNEL_ID = 1484768466023223418
_POPUP_DB_FILE = os.path.join(DATA_FOLDER, "diff_popup_meets.db")


class _PopupDB:
    def __init__(self):
        self.conn = sqlite3.connect(_POPUP_DB_FILE)
        self.conn.row_factory = sqlite3.Row
        self._setup()

    def _setup(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS popup_meets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                host_user_id INTEGER NOT NULL,
                theme TEXT,
                location TEXT NOT NULL,
                time_text TEXT NOT NULL,
                extra_notes TEXT,
                ping_playstation INTEGER NOT NULL DEFAULT 0,
                ping_carmeet INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS panel_state (
                guild_id INTEGER NOT NULL,
                panel_name TEXT NOT NULL,
                channel_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                PRIMARY KEY (guild_id, panel_name)
            )
        """)
        self.conn.commit()

    def add_meet(self, guild_id, host_id, theme, location, time_text, extra_notes, ping_ps, ping_cm) -> int:
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO popup_meets (guild_id, host_user_id, theme, location, time_text, extra_notes,
                ping_playstation, ping_carmeet, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (guild_id, host_id, theme, location, time_text, extra_notes,
              1 if ping_ps else 0, 1 if ping_cm else 0, datetime.utcnow().isoformat()))
        self.conn.commit()
        return int(cur.lastrowid)

    def save_panel(self, guild_id, channel_id, message_id):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO panel_state (guild_id, panel_name, channel_id, message_id)
            VALUES (?, 'popup', ?, ?)
            ON CONFLICT(guild_id, panel_name)
            DO UPDATE SET channel_id=excluded.channel_id, message_id=excluded.message_id
        """, (guild_id, channel_id, message_id))
        self.conn.commit()

    def get_panel(self, guild_id):
        cur = self.conn.cursor()
        cur.execute("SELECT channel_id, message_id FROM panel_state WHERE guild_id=? AND panel_name='popup'", (guild_id,))
        return cur.fetchone()


_popup_db = _PopupDB()

_POPUP_TZ_MAP = {
    "EST": "America/New_York", "EDT": "America/New_York", "ET": "America/New_York",
    "CST": "America/Chicago", "CDT": "America/Chicago", "CT": "America/Chicago",
    "MST": "America/Denver", "MDT": "America/Denver", "MT": "America/Denver",
    "PST": "America/Los_Angeles", "PDT": "America/Los_Angeles", "PT": "America/Los_Angeles",
    "UTC": "UTC", "GMT": "UTC",
}


def _popup_parse_time(raw: str) -> str:
    """Convert '8pm EST' / '8:30pm CST' / '20:00 ET' to a Discord timestamp string.
    Falls back to the original string if parsing fails."""
    import re
    from datetime import timedelta
    m = re.search(
        r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*([A-Za-z]{2,4})?',
        raw.strip(), re.IGNORECASE
    )
    if not m:
        return raw
    hour = int(m.group(1))
    minute = int(m.group(2)) if m.group(2) else 0
    meridiem = m.group(3).lower() if m.group(3) else None
    tz_abbr = m.group(4).upper() if m.group(4) else "EST"
    tz_name = _POPUP_TZ_MAP.get(tz_abbr, "America/New_York")
    if meridiem == "pm" and hour != 12:
        hour += 12
    elif meridiem == "am" and hour == 12:
        hour = 0
    if hour > 23 or minute > 59:
        return raw
    try:
        tz = ZoneInfo(tz_name)
        now = datetime.now(tz)
        local_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if local_dt <= now:
            local_dt += timedelta(days=1)
        ts = int(local_dt.timestamp())
        return f"<t:{ts}:F> — <t:{ts}:R>"
    except Exception:
        return raw


class _PopupMeetModal(discord.ui.Modal, title="⚡ Create Pop-Up Meet"):
    theme_field = discord.ui.TextInput(
        label="Theme (optional)",
        placeholder="Example: JDM Night / Clean Euros / Under 1M",
        required=False,
        max_length=100,
    )
    location_field = discord.ui.TextInput(
        label="Location",
        placeholder="Example: LS Car Meet / City / Sandy",
        required=True,
        max_length=100,
    )
    time_field = discord.ui.TextInput(
        label="Time",
        placeholder="e.g. 8pm EST  or  8:30pm CST  or  20:00 ET",
        required=True,
        max_length=300,
    )
    notes_field = discord.ui.TextInput(
        label="Extra notes (optional)",
        style=discord.TextStyle.paragraph,
        placeholder="Example: Clean builds only / first come first served",
        required=False,
        max_length=500,
    )
    ping_field = discord.ui.TextInput(
        label="Ping roles",
        placeholder="ps5, carmeet, both, or none",
        required=True,
        max_length=30,
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        if guild is None or not isinstance(user, discord.Member):
            await interaction.response.send_message("This can only be used inside the server.", ephemeral=True)
            return
        host_role = guild.get_role(HOST_ROLE_ID)
        if not user.guild_permissions.administrator and (not host_role or host_role not in user.roles):
            await interaction.response.send_message("Only users with the Host role can create pop-up meets.", ephemeral=True)
            return
        panel_ch = guild.get_channel(_POPUP_PANEL_CHANNEL_ID)
        if not isinstance(panel_ch, discord.TextChannel):
            await interaction.response.send_message("Pop-up meet channel not found.", ephemeral=True)
            return

        raw_ping = self.ping_field.value.strip().lower()
        ping_ps = any(w in raw_ping for w in ("playstation", "ps5", "ps", "both", "all"))
        ping_cm = any(w in raw_ping for w in ("carmeet", "car meet", "car", "both", "all", "notify"))

        theme = self.theme_field.value.strip()
        location = self.location_field.value.strip()
        time_text = _popup_parse_time(self.time_field.value.strip())
        notes = self.notes_field.value.strip()

        meet_id = _popup_db.add_meet(
            guild.id, user.id, theme, location, time_text, notes, ping_ps, ping_cm
        )

        ping_parts = []
        if ping_ps:
            r = guild.get_role(PS5_ROLE_ID)
            ping_parts.append(r.mention if r else "@PlayStation")
        if ping_cm:
            r = guild.get_role(NOTIFY_ROLE_ID)
            ping_parts.append(r.mention if r else "@CarMeet")
        ping_text = " ".join(ping_parts) or None

        embed = discord.Embed(
            title="⚡ DIFF Pop-Up Meet",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow(),
            description="A spontaneous meet has just been opened. Pull up quick.",
        )
        embed.add_field(name="👤 Host", value=user.mention, inline=False)
        embed.add_field(name="🎨 Theme", value=theme or "Open theme", inline=True)
        embed.add_field(name="📍 Location", value=location, inline=True)
        embed.add_field(name="🕒 Time", value=time_text, inline=False)
        embed.add_field(name="📝 Notes", value=notes or "No extra notes", inline=False)
        embed.set_footer(text=f"Pop-Up Meet #{meet_id}")

        await panel_ch.send(
            content=ping_text,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True, users=False),
        )

        log_ch = guild.get_channel(STAFF_LOGS_CHANNEL_ID)
        if isinstance(log_ch, discord.TextChannel):
            log_embed = discord.Embed(
                title="📋 Pop-Up Meet Created",
                color=discord.Color.green(),
                timestamp=datetime.utcnow(),
                description=f"{user.mention} created a new pop-up meet.",
            )
            log_embed.add_field(name="Meet ID", value=str(meet_id), inline=True)
            log_embed.add_field(name="Location", value=location, inline=True)
            log_embed.add_field(name="Theme", value=theme or "Open theme", inline=True)
            try:
                await log_ch.send(embed=log_embed)
            except Exception:
                pass

        await interaction.response.send_message(f"Pop-up meet #{meet_id} posted successfully.", ephemeral=True)


class _PopupMeetPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="⚡ Create Pop-Up Meet", style=discord.ButtonStyle.success, custom_id="diff_popup:create")
    async def create_popup(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        if not isinstance(user, discord.Member):
            await interaction.response.send_message("Server only.", ephemeral=True)
            return
        host_role = interaction.guild.get_role(HOST_ROLE_ID) if interaction.guild else None
        if not user.guild_permissions.administrator and (not host_role or host_role not in user.roles):
            await interaction.response.send_message("Only users with the Host role can use this.", ephemeral=True)
            return
        await interaction.response.send_modal(_PopupMeetModal())


def _popup_build_panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title="⚡ DIFF Pop-Up Meets Hub",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow(),
        description=(
            "*Spontaneous meets hosted throughout the week.*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🚗 **What are Pop-Up Meets?**\n"
            "Quick unscheduled meets hosted by approved DIFF hosts.\n\n"
            "📋 **How It Works**\n"
            "• Host clicks the button below\n"
            "• Fills out meet details\n"
            "• Bot posts a clean pop-up meet embed\n"
            "• Members pull up and join fast\n\n"
            "⚠️ **Rules**\n"
            "• Clean builds only\n"
            "• No crashing / griefing\n"
            "• Respect the host\n"
            "• Be ready to join quickly\n\n"
            "Only users with the **Host** role can create pop-up meets."
        ),
    )
    embed.set_footer(text="DIFF Pop-Up Meet System")
    return embed


async def _popup_post_or_refresh(guild: discord.Guild):
    channel = guild.get_channel(_POPUP_PANEL_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        return
    row = _popup_db.get_panel(guild.id)
    if row:
        try:
            msg = await channel.fetch_message(row["message_id"])
            await msg.edit(embed=_popup_build_panel_embed(), view=_PopupMeetPanelView())
            return
        except discord.NotFound:
            pass
        except Exception:
            return
    msg = await channel.send(embed=_popup_build_panel_embed(), view=_PopupMeetPanelView())
    _popup_db.save_panel(guild.id, channel.id, msg.id)


@bot.command(name="postpopuppanel")
async def _cmd_postpopuppanel(ctx: commands.Context):
    is_owner = ctx.guild and ctx.guild.owner_id == ctx.author.id
    is_admin = ctx.author.guild_permissions.administrator
    is_staff = any(r.id in _JOIN_STAFF_ROLE_IDS for r in getattr(ctx.author, "roles", []))
    if not (is_owner or is_admin or is_staff):
        await ctx.send("You need a staff role to use this command.", delete_after=8)
        return
    try:
        await ctx.message.delete()
    except Exception:
        pass
    await _popup_post_or_refresh(ctx.guild)


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
        bot.add_view(DIFFRecruitmentTicketView())
        bot.add_view(DIFFDashboardView())
        bot.add_view(MeetAttendancePanelView())
        bot.add_view(LeaderboardView())
        bot.add_view(CrewHubView())
        bot.add_view(MeetRSVPView(meet1="Meet 1", meet2="Meet 2", meet3="Meet 3"))
        bot.add_view(ActivityDashboardView())
        bot.add_view(DiffPanel())
        bot.add_view(ColorSubmissionPanelView())
        bot.add_view(SubmissionActionView())
        bot.add_view(ControlHubView())
        bot.add_view(ColorTeamPanelView())
        bot.add_view(InterviewInfoView())
        bot.add_view(InterviewOutcomeView())
        bot.add_view(SupportDropdownView())
        bot.add_view(SupportCloseButton())
        bot.add_view(SupportApplicationReviewView())
        bot.add_view(StaffReviewView())
        bot.add_view(JoinPlatformView())
        bot.add_view(JoinTicketView())
        bot.add_view(NotifyMeetView())
        bot.add_view(StaffDashboardView())
        bot.add_view(MeetInfoView())
        bot.add_view(HostFeedbackRequestView())
        _tab_state = _tab_load()
        _seen_member_ids: set[int] = set()
        for _link in _tab_state.get("ticket_links", {}).values():
            _mid = _link.get("member_id")
            _panel_msg_id = _link.get("panel_message_id")
            if _mid:
                _mid_int = int(_mid)
                _view_instance = ApplicationReviewView(_mid_int)
                if _panel_msg_id:
                    try:
                        bot.add_view(_view_instance, message_id=int(_panel_msg_id))
                    except Exception:
                        pass
                elif _mid_int not in _seen_member_ids:
                    bot.add_view(_view_instance)
                _seen_member_ids.add(_mid_int)
        del _tab_state, _seen_member_ids
    except Exception as e:
        print(f"View registration warning: {e}")

    _cs_ensure_file()
    if not color_schedule_loop.is_running():
        color_schedule_loop.start()
    if not color_ops_refresh_loop.is_running():
        color_ops_refresh_loop.start()
    if not ticket_scan_loop.is_running():
        ticket_scan_loop.start()

    _rsvp_load_all()
    for _rsvp_mid, _rsvp_rec in _rsvp_meets.items():
        if not _rsvp_rec.closed and _rsvp_rec.message_id:
            try:
                bot.add_view(AttendanceRsvpView(_rsvp_mid), message_id=int(_rsvp_rec.message_id))
            except Exception:
                pass

    bot.loop.create_task(application_timeout_loop())
    bot.loop.create_task(_tab_refresh_all_panels())
    bot.loop.create_task(_startup_refresh_all_panels())
    bot.loop.create_task(_auto_weekly_loop())
    bot.loop.create_task(_auto_staff_dashboard_loop())
    bot.loop.create_task(_daily_crew_invite_check())
    bot.loop.create_task(_ft_auto_progression_loop())
    bot.loop.create_task(_season_loop())
    bot.add_view(HostRSVPView())
    await _hrsvp_update_panel(bot)
    bot.add_view(AutoScheduleView(bot))
    bot.add_view(_ASchedAnnounceView())
    _asched_build()
    await _asched_update_panel(bot)
    bot.add_view(HostHubView())
    await _hosthub_post_or_refresh()
    bot.add_view(HostFlowView())
    await _hostflow_post_or_refresh()
    bot.add_view(_MobileRefreshView())
    bot.add_view(HostPerformanceHubView())
    bot.add_view(HostSessionView())
    await _hp_post_or_refresh()
    bot.add_view(_RcRollCallView())
    bot.add_view(_RcAdminView())
    bot.add_view(_OfficialMeetRSVPView())
    bot.add_view(_OfficialMeetPanelView())
    bot.add_view(_OmAttendanceView())
    asyncio.create_task(_om_restore_on_ready())
    bot.add_view(_PopupMeetPanelView())
    for _g in bot.guilds:
        try:
            await _om_panel_post_or_refresh(_g)
        except Exception as _e:
            print(f"[OfficialMeetPanel] on_ready error: {_e}")
    for _g in bot.guilds:
        try:
            await _popup_post_or_refresh(_g)
        except Exception as _e:
            print(f"[PopupMeet] on_ready refresh error: {_e}")
    bot.add_view(WelcomeHubView())
    bot.add_view(SocialMediaLinksView())
    bot.add_view(_PshipPanelView())
    bot.add_view(_PshipStaffView())
    bot.add_view(_RsvpView())
    bot.add_view(_IgDropView())
    for _g in bot.guilds:
        try:
            await _wh_post_or_refresh(_g)
        except Exception as _e:
            print(f"[WelcomeHub] on_ready error: {_e}")
    for _g in bot.guilds:
        try:
            await _ig_panel_post_or_refresh(_g)
        except Exception as _e:
            print(f"[IGPanel] on_ready error: {_e}")
    if not _rc_ensure_loop.is_running():
        _rc_ensure_loop.start()

    if not hierarchy_attendance_loop.is_running():
        hierarchy_attendance_loop.start()

    status_message_id = data.get("panel_message_id")

    # ── server lock: leave any guild that isn't the authorised DIFF server ──
    for guild in list(bot.guilds):
        if guild.id != GUILD_ID:
            print(f"[ServerLock] Leaving unauthorised guild: {guild.name} ({guild.id})")
            try:
                await guild.leave()
            except Exception as _e:
                print(f"[ServerLock] Could not leave {guild.id}: {_e}")


@bot.event
async def on_guild_join(guild: discord.Guild):
    """Immediately leave any server that isn't the authorised DIFF server."""
    if guild.id != GUILD_ID:
        print(f"[ServerLock] Joined unauthorised guild {guild.name} ({guild.id}) — leaving.")
        try:
            await guild.leave()
        except Exception as _e:
            print(f"[ServerLock] Could not leave {guild.id}: {_e}")


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
async def refreshpanel(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
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
async def removehost(interaction: discord.Interaction, member: discord.Member):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    before = len(data["hosts"])
    data["hosts"] = [host for host in data["hosts"] if host["discord_id"] != member.id]
    save_data(data)

    if len(data["hosts"]) == before:
        await interaction.response.send_message("That host was not found.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Removed **{member.display_name}** from the DIFF host list.", ephemeral=True)


@bot.tree.command(name="sendmeetinfo", description="Post or update the DIFF meet info panel")
async def sendmeetinfo(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
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
async def refreshcrewpanel(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
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




@bot.tree.command(name="sethostrole", description="Set the DIFF host role")
async def sethostrole(interaction: discord.Interaction, role: discord.Role):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    data["host_role_id"] = role.id
    save_data(data)
    await interaction.response.send_message(f"Host role set to {role.mention}", ephemeral=True)


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
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
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
async def posthierarchy(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
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
async def refreshhierarchy(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
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


@bot.tree.command(name="refresh-live-attendance", description="Post or refresh the live crew attendance status panel")
@app_commands.checks.has_permissions(administrator=True)
async def refresh_live_attendance_cmd(interaction: discord.Interaction):
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
    try:
        await post_or_refresh_live_attendance(interaction.guild)
        await interaction.followup.send("Live attendance panel posted/refreshed.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Error: {e}", ephemeral=True)


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


@bot.tree.command(name="recordattendance", description="Record a member's meet attendance (staff only)")
@discord.app_commands.describe(member="The member who attended", meet_name="Name of the meet")
async def recordattendance(interaction: discord.Interaction, member: discord.Member, meet_name: str):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Only Leader, Co-Leader, or Manager can use this.", ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    await record_meet_attendance(interaction.guild, member, meet_name, host_member=interaction.user)
    await interaction.followup.send(f"✅ Recorded attendance for {member.mention} at **{meet_name}**.", ephemeral=True)


@bot.tree.command(name="recordhost", description="Record a member hosting a meet (staff only)")
@discord.app_commands.describe(member="The member who hosted", meet_name="Name of the meet")
async def recordhost(interaction: discord.Interaction, member: discord.Member, meet_name: str):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Only Leader, Co-Leader, or Manager can use this.", ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    await record_meet_host(interaction.guild, member, meet_name)
    await interaction.followup.send(f"✅ Recorded {member.mention} as host for **{meet_name}**.", ephemeral=True)


@bot.tree.command(name="giverep", description="Give or remove reputation from a crew member (staff only)")
@discord.app_commands.describe(member="Target member", amount="Positive to add, negative to remove", reason="Reason for the change")
async def giverep(interaction: discord.Interaction, member: discord.Member, amount: int, reason: str):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Only Leader, Co-Leader, or Manager can use this.", ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    await update_member_reputation(interaction.guild, member, amount, reason, given_by=interaction.user)
    direction = "Added" if amount >= 0 else "Removed"
    await interaction.followup.send(f"✅ {direction} **{amount:+}** reputation for {member.mention}. Reason: {reason}", ephemeral=True)


@bot.tree.command(name="memberstats", description="View a crew member's activity stats (staff only)")
@discord.app_commands.describe(member="The member to look up")
async def memberstats(interaction: discord.Interaction, member: discord.Member):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Only Leader, Co-Leader, or Manager can use this.", ephemeral=True)
    embed = build_member_stats_embed(member)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="mystats", description="View your own DIFF activity stats")
async def mystats(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member):
        return await interaction.response.send_message("Server only.", ephemeral=True)
    embed = build_member_stats_embed(interaction.user)
    await interaction.response.send_message(embed=embed, ephemeral=True)



@bot.tree.command(name="postattendancepanel", description="Post the meet attendance panel (staff only)")
async def postattendancepanel(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Only Leader, Co-Leader, or Manager can use this.", ephemeral=True)
    embed = discord.Embed(
        title="DIFF Meet Attendance System",
        description=(
            "Use the button below to log a meet attendance record.\n\n"
            "This will post a summary embed in the meet attendance channel with:\n"
            "• Host Name\n• Meet Name\n• Date\n• Total Players\n• DIFF Members Present\n• Screenshot reminder"
        ),
        color=discord.Color.blue(),
    )
    await interaction.channel.send(embed=embed, view=MeetAttendancePanelView())
    await interaction.response.send_message("✅ Attendance panel posted.", ephemeral=True)


@bot.tree.command(name="rankinfo", description="View the DIFF rank promotion requirements")
async def rankinfo(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📈 DIFF Rank Progression",
        description="Requirements to be promoted to each rank:",
        color=discord.Color.blue(),
    )
    embed.add_field(
        name="Crew Member → Host",
        value=f"• Meets Attended: {HOST_PROMOTION_ATTENDED}\n• Meets Hosted: {HOST_PROMOTION_HOSTED}\n• Reputation: {HOST_PROMOTION_REPUTATION}",
        inline=False,
    )
    embed.add_field(
        name="Host → Manager",
        value=f"• Meets Attended: {MANAGER_PROMOTION_ATTENDED}\n• Meets Hosted: {MANAGER_PROMOTION_HOSTED}\n• Reputation: {MANAGER_PROMOTION_REPUTATION}",
        inline=False,
    )
    embed.add_field(
        name="Manager → Leader",
        value=f"• Meets Attended: {LEADER_PROMOTION_ATTENDED}\n• Meets Hosted: {LEADER_PROMOTION_HOSTED}\n• Reputation: {LEADER_PROMOTION_REPUTATION}",
        inline=False,
    )
    embed.set_footer(text="Promotion suggestions are auto-posted to staff logs when thresholds are met.")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="weeklyrollcall", description="Post the weekly DIFF roll call with RSVP buttons (staff only)")
async def weeklyrollcall(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Only Leader, Co-Leader, or Manager can use this.", ephemeral=True)
    await interaction.response.send_modal(WeeklyRollCallModal())


@bot.tree.command(name="staffdashboard", description="Post the DIFF staff recruitment dashboard (staff only)")
async def staffdashboard(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Only Leader, Co-Leader, or Manager can use this command.", ephemeral=True)
    await interaction.channel.send(embed=build_dashboard_embed(), view=DIFFDashboardView())
    await interaction.response.send_message("✅ Dashboard posted.", ephemeral=True)


# =========================
# ADVANCED COLOR SYSTEM
# =========================
COLOR_PANEL_CHANNEL_ID = 1177436572304556084
COLOR_SUBMISSION_CHANNEL_ID = 1177434999381831680
COLOR_ANNOUNCEMENT_CHANNEL_ID = 1108181679308283965
COLOR_SYSTEM_FILE = os.path.join(DATA_FOLDER, "diff_color_system_data.json")
COLOR_PANEL_STATE_FILE = os.path.join(DATA_FOLDER, "diff_color_panel_state.json")
COLOR_TZ = ZoneInfo("America/New_York")
COLOR_SCHEDULE_HOUR = 12
AUTO_LOCK_DAYS = 21
NUMBER_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]


def _cs_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cs_ensure_file() -> None:
    if not os.path.exists(COLOR_SYSTEM_FILE):
        _save_diff_json(COLOR_SYSTEM_FILE, {
            "submissions": {}, "current_vote": None, "stats": {},
            "schedule": {"last_vote_post_date": "", "last_winner_post_date": ""},
            "history": [],
        })


def _cs_load() -> Dict[str, Any]:
    _cs_ensure_file()
    return _load_diff_json(COLOR_SYSTEM_FILE)


def _cs_save(data: Dict[str, Any]) -> None:
    _save_diff_json(COLOR_SYSTEM_FILE, data)


def _cs_add_stat(data: Dict[str, Any], user_id: int, field: str, amount: int = 1) -> None:
    key = str(user_id)
    data["stats"].setdefault(key, {"submitted": 0, "selected_for_vote": 0, "wins": 0, "manual_approvals": 0})
    data["stats"][key][field] = data["stats"][key].get(field, 0) + amount


def _cs_is_color_team(member: discord.Member) -> bool:
    return any(r.id == COLOR_TEAM_ROLE_ID for r in member.roles)


def _cs_is_color_admin(member: discord.Member) -> bool:
    return any(r.id in (LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID) for r in member.roles)


async def _cs_fetch_channel(channel_id: int):
    ch = bot.get_channel(channel_id)
    if ch is None:
        ch = await bot.fetch_channel(channel_id)
    return ch


async def _cs_update_submission_message(submission: Dict[str, Any], *, disable_view: bool = False, extra_footer: Optional[str] = None) -> None:
    try:
        channel = await _cs_fetch_channel(int(submission["channel_id"]))
        message = await channel.fetch_message(int(submission["message_id"]))
    except Exception:
        return
    status = submission.get("status", "pending").replace("_", " ").title()
    try:
        embed_color = discord.Color.from_str(submission["hex_code"])
    except Exception:
        embed_color = discord.Color.blurple()
    embed = discord.Embed(
        title="🎨 DIFF Color Submission",
        description=(
            "A new crew color has been submitted by the Color Team.\n\n"
            f"**Color Name:** {submission['color_name']}\n"
            f"**HEX Code:** `{submission['hex_code']}`\n"
            f"**Status:** **{status}**\n\n"
            "Use this post to review the submission."
        ),
        color=embed_color,
    )
    embed.set_image(url=submission["image_url"])
    footer = f"Submitted by {submission.get('author_name', 'Unknown')}"
    if extra_footer:
        footer += f" • {extra_footer}"
    embed.set_footer(text=footer)
    view = None if disable_view else SubmissionActionView()
    try:
        await message.edit(embed=embed, view=view)
    except Exception:
        pass


async def _cs_build_vote_collage(candidates: List[Dict[str, Any]]) -> Optional[discord.File]:
    if not PIL_AVAILABLE or aiohttp is None:
        return None
    try:
        async with aiohttp.ClientSession() as session:
            images = []
            for c in candidates:
                async with session.get(c["image_url"], timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    if resp.status != 200:
                        return None
                    images.append(Image.open(io.BytesIO(await resp.read())).convert("RGB"))
        w, h, pad, lh = 420, 300, 16, 54
        canvas = Image.new("RGB", (w * 2 + pad * 3, h * 2 + lh * 2 + pad * 3), (18, 24, 38))
        draw = ImageDraw.Draw(canvas)
        try:
            font = ImageFont.truetype("arial.ttf", 26)
            font_sm = ImageFont.truetype("arial.ttf", 20)
        except Exception:
            font = font_sm = ImageFont.load_default()
        for idx, img in enumerate(images[:4]):
            col, row = idx % 2, idx // 2
            x = pad + col * (w + pad)
            y = pad + row * (h + lh + pad)
            canvas.paste(ImageOps.fit(img, (w, h), method=Image.LANCZOS), (x, y))
            draw.rectangle([x, y + h, x + w, y + h + lh], fill=(10, 14, 24))
            draw.text((x + 14, y + h + 12), f"{idx + 1}. {candidates[idx]['color_name']}", font=font, fill=(255, 255, 255))
            draw.text((x + 14, y + h + 32), candidates[idx]["hex_code"], font=font_sm, fill=(180, 190, 210))
        bio = io.BytesIO()
        canvas.save(bio, format="PNG")
        bio.seek(0)
        return discord.File(bio, filename="diff_color_vote.png")
    except Exception:
        return None


async def _cs_post_winner_announcement(guild: discord.Guild, winner: Dict[str, Any], manual: bool = False):
    channel = await _cs_fetch_channel(COLOR_ANNOUNCEMENT_CHANNEL_ID)
    crew_role = guild.get_role(CREW_MEMBER_ROLE_ID)
    ping = crew_role.mention if crew_role else ""
    lines = []
    if ping:
        lines += [ping, ""]
    lines += ["*The Crew Color has been changed this week.*", "", f"**{winner['color_name']}**", "", "*I hope you enjoy this color!*"]
    try:
        embed_color = discord.Color.from_str(winner["hex_code"])
    except Exception:
        embed_color = discord.Color.blurple()
    embed = discord.Embed(color=embed_color, timestamp=datetime.now(COLOR_TZ))
    embed.set_image(url=winner["image_url"])
    embed.set_footer(text="DIFF • Crew Color Announcement" + (" • Manual Approval" if manual else ""))
    return await channel.send("\n".join(lines), embed=embed)


async def _cs_post_vote_announcement(guild: discord.Guild, candidates: List[Dict[str, Any]]):
    channel = await _cs_fetch_channel(COLOR_ANNOUNCEMENT_CHANNEL_ID)
    crew_role = guild.get_role(CREW_MEMBER_ROLE_ID)
    ping = crew_role.mention if crew_role else ""
    lines = []
    if ping:
        lines += [ping, ""]
    lines += [
        "*Crew Color will be voted on this week.*", "",
        "*The color with the most votes will be the crew color for the following week.*", "",
    ]
    for idx, c in enumerate(candidates[:4]):
        lines.append(f"{['1️⃣', '2️⃣', '3️⃣', '4️⃣'][idx]} **{c['color_name']}**")
    lines += ["", "*Color order starts from left to right.*", "", "*Please choose one color below* 👇"]
    collage = await _cs_build_vote_collage(candidates[:4])
    if collage:
        try:
            embed = discord.Embed(color=discord.Color.blurple(), timestamp=datetime.now(COLOR_TZ))
            embed.set_image(url="attachment://diff_color_vote.png")
            embed.set_footer(text="DIFF • Weekly Crew Color Vote")
            msg = await channel.send("\n".join(lines), embed=embed, file=collage)
        except Exception:
            msg = await channel.send("\n".join(lines))
    else:
        msg = await channel.send("\n".join(lines))
        for idx, c in enumerate(candidates[:4]):
            try:
                clr = discord.Color.from_str(c["hex_code"])
            except Exception:
                clr = discord.Color.blurple()
            preview = discord.Embed(title=f"{idx + 1}. {c['color_name']}", description=f"`{c['hex_code']}`", color=clr)
            preview.set_image(url=c["image_url"])
            await channel.send(embed=preview)
    for emoji in NUMBER_EMOJIS[:len(candidates[:4])]:
        try:
            await msg.add_reaction(emoji)
        except Exception:
            pass
    return msg


def _cs_get_candidate_pool(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    pending = sorted(
        [s for s in data["submissions"].values() if s.get("status") == "pending"],
        key=lambda s: s.get("submitted_at", ""), reverse=True,
    )
    unique: Dict[str, Dict[str, Any]] = {}
    for sub in pending:
        if sub["author_id"] not in unique:
            unique[sub["author_id"]] = sub
    candidates = list(unique.values())
    random.shuffle(candidates)
    return candidates[:4]


async def _cs_try_post_weekly_vote(guild: discord.Guild) -> bool:
    data = _cs_load()
    current_vote = data.get("current_vote")
    if current_vote and not current_vote.get("closed", False):
        return False
    candidates = _cs_get_candidate_pool(data)
    if len(candidates) < 4:
        return False
    msg = await _cs_post_vote_announcement(guild, candidates)
    if msg is None:
        return False
    for c in candidates:
        c["status"] = "in_voting"
        c["selected_for_vote"] = True
        _cs_add_stat(data, int(c["author_id"]), "selected_for_vote", 1)
    data["current_vote"] = {
        "message_id": str(msg.id), "channel_id": str(msg.channel.id),
        "candidate_submission_ids": [c["message_id"] for c in candidates],
        "opened_at": _cs_utc_now(), "closed": False,
    }
    for c in candidates:
        await _cs_update_submission_message(c, extra_footer="Selected for weekly voting")
    _cs_save(data)
    return True


async def _cs_try_close_vote(guild: discord.Guild) -> bool:
    data = _cs_load()
    current_vote = data.get("current_vote")
    if not current_vote or current_vote.get("closed", False):
        return False
    try:
        channel = await _cs_fetch_channel(int(current_vote["channel_id"]))
        vote_msg = await channel.fetch_message(int(current_vote["message_id"]))
    except Exception:
        return False
    candidate_ids = current_vote.get("candidate_submission_ids", [])
    candidates = [data["submissions"].get(cid) for cid in candidate_ids]
    candidates = [c for c in candidates if c]
    if not candidates:
        return False
    reaction_totals = {e: 0 for e in NUMBER_EMOJIS[:len(candidates)]}
    for reaction in vote_msg.reactions:
        if str(reaction.emoji) in reaction_totals:
            reaction_totals[str(reaction.emoji)] = max(reaction.count - 1, 0)
    top_idx, top_votes = 0, -1
    for idx, emoji in enumerate(NUMBER_EMOJIS[:len(candidates)]):
        v = reaction_totals.get(emoji, 0)
        if v > top_votes:
            top_votes = v
            top_idx = idx
    winner = candidates[top_idx]
    await _cs_post_winner_announcement(guild, winner, manual=False)
    winner["status"] = "won"
    winner["won_at"] = _cs_utc_now()
    _cs_add_stat(data, int(winner["author_id"]), "wins", 1)
    for idx, c in enumerate(candidates):
        if idx != top_idx:
            c["status"] = "locked"
            c["locked_at"] = _cs_utc_now()
    current_vote["closed"] = True
    current_vote["closed_at"] = _cs_utc_now()
    current_vote["winner_submission_id"] = winner["message_id"]
    data["history"].append({
        "closed_at": current_vote["closed_at"], "winner_name": winner["color_name"], "votes": reaction_totals,
    })
    try:
        await vote_msg.edit(content=(vote_msg.content or "") + f"\n\n🔒 **Voting Closed**\n🏆 Winner: **{winner['color_name']}**")
    except Exception:
        pass
    for c in candidates:
        await _cs_update_submission_message(c, disable_view=c["status"] in {"locked", "won"}, extra_footer="Voting cycle completed")
    data["current_vote"] = None
    _cs_save(data)
    return True


@tasks.loop(minutes=1)
async def color_schedule_loop():
    now = datetime.now(COLOR_TZ)
    current_date = now.date().isoformat()
    data = _cs_load()
    guild = bot.guilds[0] if bot.guilds else None
    if guild is None:
        return
    if (now.weekday() == 1 and now.hour == COLOR_SCHEDULE_HOUR and 0 <= now.minute <= 4
            and data["schedule"].get("last_vote_post_date") != current_date):
        if await _cs_try_post_weekly_vote(guild):
            data = _cs_load()
            data["schedule"]["last_vote_post_date"] = current_date
            _cs_save(data)
    if (now.weekday() == 0 and now.hour == COLOR_SCHEDULE_HOUR and 0 <= now.minute <= 4
            and data["schedule"].get("last_winner_post_date") != current_date):
        if await _cs_try_close_vote(guild):
            data = _cs_load()
            data["schedule"]["last_winner_post_date"] = current_date
            _cs_save(data)

    weekly_state = _weekly_color_load()
    if (now.weekday() == 0 and now.hour == COLOR_SCHEDULE_HOUR and 0 <= now.minute <= 4):
        monday_key = _weekly_color_today_key("monday")
        if weekly_state.get("last_monday_team_post") != current_date:
            role = guild.get_role(COLOR_TEAM_ROLE_ID)
            ping = role.mention if role else "@Color Team"
            await _weekly_color_send_or_edit(
                monday_key,
                f"{ping} Weekly color announced — prep next vote.",
                _weekly_color_monday_embed(),
            )
            weekly_state = _weekly_color_load()
            weekly_state["last_monday_team_post"] = current_date
            _weekly_color_save(weekly_state)
    if (now.weekday() == 1 and now.hour == COLOR_SCHEDULE_HOUR and 0 <= now.minute <= 4):
        tuesday_key = _weekly_color_today_key("tuesday")
        if weekly_state.get("last_tuesday_team_post") != current_date:
            role = guild.get_role(COLOR_TEAM_ROLE_ID)
            ping = role.mention if role else "@Color Team"
            await _weekly_color_send_or_edit(
                tuesday_key,
                f"{ping} Voting is live — direct members.",
                _weekly_color_tuesday_embed(),
            )
            weekly_state = _weekly_color_load()
            weekly_state["last_tuesday_team_post"] = current_date
            _weekly_color_save(weekly_state)
    now_utc = datetime.now(timezone.utc)
    changed = False
    current_vote = data.get("current_vote") or {}
    active_ids = set(current_vote.get("candidate_submission_ids", []))
    for sub in data["submissions"].values():
        if sub.get("status") != "pending" or sub["message_id"] in active_ids:
            continue
        try:
            age = (now_utc - datetime.fromisoformat(sub["submitted_at"]).astimezone(timezone.utc)).days
        except Exception:
            continue
        if age >= AUTO_LOCK_DAYS:
            sub["status"] = "locked"
            sub["locked_at"] = _cs_utc_now()
            changed = True
            await _cs_update_submission_message(sub, disable_view=True, extra_footer="Auto-locked due to age")
    if changed:
        _cs_save(data)


@color_schedule_loop.before_loop
async def before_color_schedule_loop():
    await bot.wait_until_ready()


class ColorSubmissionModal(discord.ui.Modal, title="DIFF Color Submission"):
    color_name = discord.ui.TextInput(label="Color Name", placeholder="Example: Tangerine Tango", max_length=100, required=True)
    hex_code = discord.ui.TextInput(label="HEX Code", placeholder="Example: #FF9742", max_length=7, min_length=4, required=True)
    image_url = discord.ui.TextInput(label="Image URL", placeholder="Paste the direct image link here", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not isinstance(interaction.user, discord.Member) or not _cs_is_color_team(interaction.user):
            return await interaction.response.send_message("Only the Color Team can submit crew colors.", ephemeral=True)
        submit_channel = await _cs_fetch_channel(COLOR_SUBMISSION_CHANNEL_ID)
        color_name_val = str(self.color_name.value).strip()
        hex_val = str(self.hex_code.value).strip().upper()
        image_val = str(self.image_url.value).strip()
        if not hex_val.startswith("#"):
            hex_val = f"#{hex_val}"
        if len(hex_val) not in (4, 7):
            return await interaction.response.send_message("Your HEX code needs to look like `#FF9742` or `#F94`.", ephemeral=True)
        try:
            embed_color = discord.Color.from_str(hex_val)
        except Exception:
            embed_color = discord.Color.blurple()
        embed = discord.Embed(
            title="🎨 DIFF Color Submission",
            description=(
                "A new crew color has been submitted by the Color Team.\n\n"
                f"**Color Name:** {color_name_val}\n"
                f"**HEX Code:** `{hex_val}`\n"
                "**Status:** **Pending Review**\n\n"
                "Use this post to review the submission."
            ),
            color=embed_color,
        )
        embed.set_image(url=image_val)
        embed.set_footer(text=f"Submitted by {interaction.user.display_name}")
        msg = await submit_channel.send(embed=embed, view=SubmissionActionView())
        for emoji in ("✅", "❌", "🤔"):
            try:
                await msg.add_reaction(emoji)
            except Exception:
                pass
        data = _cs_load()
        data["submissions"][str(msg.id)] = {
            "message_id": str(msg.id), "channel_id": str(submit_channel.id),
            "author_id": str(interaction.user.id), "author_name": interaction.user.display_name,
            "color_name": color_name_val, "hex_code": hex_val, "image_url": image_val,
            "status": "pending", "submitted_at": _cs_utc_now(),
            "selected_for_vote": False, "locked_at": "", "approved_at": "", "won_at": "",
        }
        _cs_add_stat(data, interaction.user.id, "submitted", 1)
        _cs_save(data)
        await interaction.response.send_message(f"Your color submission has been posted in {submit_channel.mention}.", ephemeral=True)


class ColorSubmissionPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Submit Color", style=discord.ButtonStyle.primary, emoji="🎨", custom_id="diff_submit_color_button_v3")
    async def submit_color_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ColorSubmissionModal())


class SubmissionActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        traceback.print_exception(type(error), error, error.__traceback__)
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
            else:
                await interaction.followup.send("Something went wrong. Please try again.", ephemeral=True)
        except Exception:
            pass

    @discord.ui.button(label="Approve Color", style=discord.ButtonStyle.success, emoji="🏆", custom_id="diff_approve_color_button_v3")
    async def approve_color_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member) or not _cs_is_color_admin(interaction.user):
            return await interaction.response.send_message("Only Leaders, Co-Leaders, or Managers can approve colors.", ephemeral=True)
        data = _cs_load()
        submission = data["submissions"].get(str(interaction.message.id))
        if not submission:
            return await interaction.response.send_message("Submission not found in the system.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        submission["status"] = "approved"
        submission["approved_at"] = _cs_utc_now()
        _cs_add_stat(data, int(submission["author_id"]), "manual_approvals", 1)
        _cs_save(data)
        await _cs_update_submission_message(submission, extra_footer="Approved by leadership")
        await _cs_post_winner_announcement(interaction.guild, submission, manual=True)
        await interaction.followup.send("Color approved and announcement posted.", ephemeral=True)

    @discord.ui.button(label="Lock Submission", style=discord.ButtonStyle.secondary, emoji="🔒", custom_id="diff_lock_submission_button_v3")
    async def lock_submission_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member) or not _cs_is_color_admin(interaction.user):
            return await interaction.response.send_message("Only Leaders, Co-Leaders, or Managers can lock submissions.", ephemeral=True)
        data = _cs_load()
        submission = data["submissions"].get(str(interaction.message.id))
        if not submission:
            return await interaction.response.send_message("Submission not found in the system.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        submission["status"] = "locked"
        submission["locked_at"] = _cs_utc_now()
        _cs_save(data)
        await _cs_update_submission_message(submission, disable_view=True, extra_footer="Locked by leadership")
        await interaction.followup.send("Submission locked.", ephemeral=True)


def _cs_build_panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🎨 DIFF Color Submission Panel",
        description=(
            "**Color Team Guide**\n\n"
            "Use the button below to submit a new crew color for review.\n\n"
            "**What to include:**\n"
            "• Color name\n• HEX code\n• Image link for the preview car\n\n"
            "**Before submitting:**\n"
            "• Keep the color clean and realistic\n• Double-check the HEX code\n"
            "• Use a clear image that shows the color well\n• Make sure the submission is meet-ready\n\n"
            "**How it works:**\n"
            "• Press **Submit Color** and fill out the form\n"
            "• Your submission posts to the review channel automatically\n"
            "• Leadership can approve or lock submissions\n"
            "• Weekly vote auto-posts Tuesday ~12 PM EST\n"
            "• Winner auto-announces Monday ~12 PM EST\n\n"
            "Press **Submit Color** below to begin."
        ),
        color=discord.Color.blurple(),
    )
    embed.set_footer(text="DIFF • Advanced Color Team System")
    return embed


@bot.tree.command(name="post-color-panel", description="Post the DIFF color submission panel (staff only)")
async def post_color_panel(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    panel_ch = await _cs_fetch_channel(COLOR_PANEL_CHANNEL_ID)
    msg = await panel_ch.send(embed=_cs_build_panel_embed(), view=ColorSubmissionPanelView())
    _save_diff_json(COLOR_PANEL_STATE_FILE, {"channel_id": panel_ch.id, "message_id": msg.id})
    await interaction.response.send_message(f"Color submission panel posted in {panel_ch.mention}.", ephemeral=True)


@bot.tree.command(name="refresh-color-panel", description="Refresh the existing DIFF color submission panel (staff only)")
async def refresh_color_panel(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    panel_ch = bot.get_channel(COLOR_PANEL_CHANNEL_ID)
    if not isinstance(panel_ch, discord.TextChannel):
        panel_ch = await bot.fetch_channel(COLOR_PANEL_CHANNEL_ID)
    await interaction.response.defer(ephemeral=True)
    message = None
    state = _load_diff_json(COLOR_PANEL_STATE_FILE)
    message_id = state.get("message_id")
    if message_id:
        try:
            message = await panel_ch.fetch_message(int(message_id))
        except (discord.NotFound, discord.HTTPException):
            message = None
    if message is None:
        async for msg in panel_ch.history(limit=50):
            if msg.author.id == bot.user.id and msg.embeds:
                message = msg
                _save_diff_json(COLOR_PANEL_STATE_FILE, {"channel_id": panel_ch.id, "message_id": msg.id})
                break
    if message is None:
        return await interaction.followup.send(
            "No panel message found. Use `/post-color-panel` to post one first.", ephemeral=True
        )
    await message.edit(embed=_cs_build_panel_embed(), view=ColorSubmissionPanelView())
    await interaction.followup.send("Color panel refreshed ✅", ephemeral=True)


@bot.tree.command(name="color-stats", description="Show the DIFF color team leaderboard")
async def color_stats(interaction: discord.Interaction):
    data = _cs_load()
    if not data["stats"]:
        return await interaction.response.send_message("No color team stats yet.", ephemeral=True)
    sorted_stats = sorted(
        data["stats"].items(),
        key=lambda item: (item[1].get("wins", 0), item[1].get("selected_for_vote", 0), item[1].get("submitted", 0)),
        reverse=True,
    )
    lines = []
    for idx, (uid, stats) in enumerate(sorted_stats[:10], start=1):
        member = interaction.guild.get_member(int(uid)) if interaction.guild else None
        name = member.display_name if member else f"User {uid}"
        lines.append(
            f"**{idx}. {name}**\n"
            f"Submitted: {stats.get('submitted', 0)} | Selected: {stats.get('selected_for_vote', 0)} | "
            f"Wins: {stats.get('wins', 0)} | Approvals: {stats.get('manual_approvals', 0)}"
        )
    embed = discord.Embed(
        title="📊 DIFF Color Team Leaderboard",
        description="\n\n".join(lines),
        color=discord.Color.blurple(),
    )
    embed.set_footer(text="Top color team members by wins, selections, and submissions")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="force-color-vote", description="Manually post the weekly color vote (leadership only)")
async def force_color_vote(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not _cs_is_color_admin(interaction.user):
        return await interaction.response.send_message("Leaders, Co-Leaders, and Managers only.", ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    success = await _cs_try_post_weekly_vote(interaction.guild)
    if success:
        await interaction.followup.send("Weekly color vote posted.", ephemeral=True)
    else:
        await interaction.followup.send(
            "Could not post vote. Need at least 4 pending submissions from 4 different Color Team members and no active vote already open.",
            ephemeral=True,
        )


@bot.tree.command(name="force-color-winner", description="Manually close the vote and post the winner (leadership only)")
async def force_color_winner(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not _cs_is_color_admin(interaction.user):
        return await interaction.response.send_message("Leaders, Co-Leaders, and Managers only.", ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    success = await _cs_try_close_vote(interaction.guild)
    if success:
        await interaction.followup.send("Vote closed and winner posted.", ephemeral=True)
    else:
        await interaction.followup.send("No active vote to close.", ephemeral=True)


# =========================
# COLOR TEAM PANEL
# =========================
COLOR_TEAM_POST_CHANNEL_ID = 1485453653916520549
COLOR_TEAM_PANEL_STATE_KEY = "color_team_panel_message_id"
WEEKLY_COLOR_STATE_FILE = os.path.join(DATA_FOLDER, "diff_weekly_color_state.json")


def _weekly_color_load() -> dict:
    return _load_diff_json(WEEKLY_COLOR_STATE_FILE) or {}


def _weekly_color_save(state: dict) -> None:
    _save_diff_json(WEEKLY_COLOR_STATE_FILE, state)


def _weekly_color_today_key(name: str) -> str:
    now = datetime.now(COLOR_TZ)
    return f"{name}_{now.strftime('%Y_%m_%d')}"


def _weekly_color_monday_embed() -> discord.Embed:
    return (
        discord.Embed(
            title="🎨 Weekly Color Update",
            description="New color is live.\n\nColor Team — start preparing the next vote.",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow(),
        )
        .add_field(
            name="What to do",
            value="• Plan next colors\n• Coordinate in chat\n• Prepare voting",
            inline=False,
        )
        .set_footer(text="Different Meets • Color Team")
    )


def _weekly_color_tuesday_embed() -> discord.Embed:
    return (
        discord.Embed(
            title="🗳️ Voting Now Live",
            description="Voting has started.\n\nGuide members and keep things organized.",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow(),
        )
        .add_field(
            name="Focus",
            value="• Direct traffic\n• Monitor voting\n• Stay active",
            inline=False,
        )
        .set_footer(text="Different Meets • Color Team")
    )


async def _weekly_color_send_or_edit(key: str, content: str, embed: discord.Embed) -> None:
    guild = bot.guilds[0] if bot.guilds else None
    if guild is None:
        return
    channel = guild.get_channel(COLOR_TEAM_POST_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        return
    state = _weekly_color_load()
    view = ColorTeamPanelView()
    if key in state:
        try:
            msg = await channel.fetch_message(int(state[key]))
            await msg.edit(content=content, embed=embed, view=view)
            return
        except (discord.NotFound, discord.HTTPException):
            pass
    msg = await channel.send(
        content=content,
        embed=embed,
        view=view,
        allowed_mentions=discord.AllowedMentions(roles=True),
    )
    state[key] = msg.id
    _weekly_color_save(state)


class ColorTeamPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(
            label="Color Information",
            style=discord.ButtonStyle.link,
            url=f"https://discord.com/channels/{GUILD_ID}/{COLOR_PANEL_CHANNEL_ID}",
            emoji="🎨",
        ))
        self.add_item(discord.ui.Button(
            label="Color Submission",
            style=discord.ButtonStyle.link,
            url=f"https://discord.com/channels/{GUILD_ID}/{COLOR_SUBMISSION_CHANNEL_ID}",
            emoji="🗳️",
        ))


def _build_color_team_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🎨 DIFF Color Team Coordination",
        description=(
            "This panel is here to keep the **Color Team** organized and on the same page.\n\n"
            "**What this area is used for:**\n"
            "• Coordinating weekly crew color changes\n"
            "• Discussing color ideas and submissions\n"
            "• Preparing voting posts and announcements\n"
            "• Keeping the team updated on current color plans\n\n"
            "Use the buttons below to quickly access the main channels for coordination and voting."
        ),
        color=discord.Color.purple(),
        timestamp=datetime.utcnow(),
    )
    embed.add_field(
        name="📌 Team Purpose",
        value=(
            "Work together to manage the crew's weekly color direction, planning, "
            "and communication so everything stays clean, consistent, and organized."
        ),
        inline=False,
    )
    embed.add_field(
        name="✅ Expectations",
        value="Stay active • communicate clearly • help with planning • support weekly color operations",
        inline=False,
    )
    embed.set_footer(text="Different Meets • Color Team Panel")
    return embed


async def _post_or_refresh_color_team_panel(ping_role: bool = True) -> Optional[discord.Message]:
    guild = bot.guilds[0] if bot.guilds else None
    if guild is None:
        return None
    channel = guild.get_channel(COLOR_TEAM_POST_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        return None

    state = _load_diff_json(DIFF_PANEL_STATE_FILE)
    msg_id = state.get(COLOR_TEAM_PANEL_STATE_KEY)
    existing: Optional[discord.Message] = None
    if msg_id:
        try:
            existing = await channel.fetch_message(int(msg_id))
        except (discord.NotFound, discord.HTTPException):
            existing = None

    role = guild.get_role(COLOR_TEAM_ROLE_ID)
    content = role.mention if (ping_role and role) else None
    embed = _build_color_team_embed()
    view = ColorTeamPanelView()

    if existing:
        await existing.edit(content=content, embed=embed, view=view)
        return existing

    msg = await channel.send(
        content=content,
        embed=embed,
        view=view,
        allowed_mentions=discord.AllowedMentions(roles=True),
    )
    state[COLOR_TEAM_PANEL_STATE_KEY] = msg.id
    _save_diff_json(DIFF_PANEL_STATE_FILE, state)
    return msg


@bot.tree.command(name="post-color-team-panel", description="Post or refresh the Color Team coordination panel (staff only)")
@app_commands.checks.has_permissions(manage_guild=True)
async def post_color_team_panel(interaction: discord.Interaction):
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return
    await _post_or_refresh_color_team_panel(ping_role=True)
    await interaction.followup.send("Color team coordination panel posted/refreshed.", ephemeral=True)


@bot.tree.command(name="refresh-color-team-panel", description="Refresh the Color Team panel in place without duplicating (staff only)")
@app_commands.checks.has_permissions(manage_guild=True)
async def refresh_color_team_panel(interaction: discord.Interaction):
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return
    await _post_or_refresh_color_team_panel(ping_role=False)
    await interaction.followup.send("Color team panel refreshed with no duplicate post.", ephemeral=True)


@bot.tree.command(name="reset-color-team-panel", description="Reset the Color Team panel state and repost cleanly (admin only)")
@app_commands.checks.has_permissions(administrator=True)
async def reset_color_team_panel(interaction: discord.Interaction):
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return
    state = _load_diff_json(DIFF_PANEL_STATE_FILE)
    state.pop(COLOR_TEAM_PANEL_STATE_KEY, None)
    _save_diff_json(DIFF_PANEL_STATE_FILE, state)
    await _post_or_refresh_color_team_panel(ping_role=True)
    await interaction.followup.send("Color team panel reset and reposted cleanly.", ephemeral=True)


@bot.tree.command(name="test-monday-color", description="Manually trigger the Monday color team update post (staff only)")
@app_commands.checks.has_permissions(manage_guild=True)
async def test_monday_color(interaction: discord.Interaction):
    if interaction.guild is None:
        return await interaction.response.send_message("Server only.", ephemeral=True)
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return
    role = interaction.guild.get_role(COLOR_TEAM_ROLE_ID)
    ping = role.mention if role else "@Color Team"
    await _weekly_color_send_or_edit(
        _weekly_color_today_key("monday"),
        f"{ping} Weekly color announced — prep next vote.",
        _weekly_color_monday_embed(),
    )
    await interaction.followup.send("Monday color team post sent.", ephemeral=True)


@bot.tree.command(name="test-tuesday-color", description="Manually trigger the Tuesday voting live post (staff only)")
@app_commands.checks.has_permissions(manage_guild=True)
async def test_tuesday_color(interaction: discord.Interaction):
    if interaction.guild is None:
        return await interaction.response.send_message("Server only.", ephemeral=True)
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return
    role = interaction.guild.get_role(COLOR_TEAM_ROLE_ID)
    ping = role.mention if role else "@Color Team"
    await _weekly_color_send_or_edit(
        _weekly_color_today_key("tuesday"),
        f"{ping} Voting is live — direct members.",
        _weekly_color_tuesday_embed(),
    )
    await interaction.followup.send("Tuesday color team post sent.", ephemeral=True)


# =========================
# CREW INTERVIEW PANEL
# =========================

def _interview_panel_load() -> dict:
    return _load_diff_json(INTERVIEW_PANEL_FILE) or {}


def _interview_panel_save(data: dict) -> None:
    _save_diff_json(INTERVIEW_PANEL_FILE, data)


def _build_interview_panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🎤 Crew Interview Zone",
        description=(
            "*This panel is the staff interview guide for bringing new members into DIFF.*\n\n"
            "Use the buttons below during interviews to stay organized, cover every required topic, "
            "and keep the process clean, professional, and consistent.\n\n"
            "﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍\n\n"
            "🗣️ **Interview Speech** — Open with the official DIFF introduction\n\n"
            "❓ **Interview Questions** — Ask every required question for new applicants\n\n"
            "🎉 **Crew Events** — Explain the types of events and expectations in DIFF\n\n"
            "📌 **Crew Positions** — Show the roles members can work toward in the crew\n\n"
            "✅ **End of Interview** — Close out the interview the right way\n\n"
            "👑 **Leadership Team** — Show who applicants can contact for help or questions\n\n"
            "﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍\n\n"
            "📘 Keep interviews smooth, respectful, and professional so every applicant gets the same clear DIFF experience."
        ),
        color=discord.Color.blue(),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Different Meets • Staff Interview Panel")
    return embed


class InterviewInfoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Interview Speech",
        emoji="🗣️",
        style=discord.ButtonStyle.primary,
        custom_id="diff_interview_speech",
        row=0,
    )
    async def interview_speech(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = (
            "__**Interview Speech**__\n\n"
            "*Hello, (Player Name). Welcome to our crew interview. This is (Present your name). "
            "Also, give some info about when you joined the crew and your role. After that, tell the applicant "
            "some history about DIFF, which has been around since 2020 under various names. We came to PS5 back in 2022. "
            "We are an active crew and community looking for active members to help out in the car meet scene. "
            "Before you ask them questions, ask them if they have any questions before we get started.*"
        )
        await interaction.response.send_message(text, ephemeral=True)

    @discord.ui.button(
        label="Interview Questions",
        emoji="❓",
        style=discord.ButtonStyle.success,
        custom_id="diff_interview_questions",
        row=0,
    )
    async def interview_questions(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = (
            "__**Interview Questions**__\n\n"
            "*You don't have to answer the questions in order but you do have to ask them all of the questions.*\n\n"
            "■ *All DIFF members must be over the age of 18. Just to confirm how old are you?*\n\n"
            "■ *We are a clean car community. Do you know the difference between clean cars and being a ricer? "
            "If so, please explain.*\n\n"
            "■ *Car knowledge is extremely important. Can you provide me with a car brand made in Japan, Europe, "
            "& America? What is your dream car?*\n\n"
            "■ *How often are you able to check Discord? We do a lot of communication via this Discord server. "
            "You have to be able to react to weekly roll calls, & crew color announcements.*\n\n"
            "■ *A good working headset is required for all members. You have to be able to speak when needed.*\n\n"
            "■ *You are required to set DIFF as active to all meets you attend within this crew and community meets. "
            "Failed to wear a crew tag to meets will result in a strike.*\n\n"
            "■ *You must wear the crew jackets to all DIFF meets, and crew events.*\n\n"
            "■ *Are you aware of our meet time which is 8pm EST? You have to join the meet 30 mins early. "
            "You're required to attend at least one meet a week. If you can't attend you must let someone on Management know in advance.*\n\n"
            "■ *Why do you want to join our crew Different Meets (DIFF)? What roles are you considering trying out for the crew?*"
        )
        await interaction.response.send_message(text, ephemeral=True)

    @discord.ui.button(
        label="Crew Events",
        emoji="🎉",
        style=discord.ButtonStyle.secondary,
        custom_id="diff_interview_events",
        row=0,
    )
    async def crew_events(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = (
            "__**Crew Events**__\n\n"
            "*We offer a range of events in our crew.*\n\n"
            "﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍\n\n"
            "■ *Monthly crew meetings on Discord (Meetings are mandatory to attend). "
            "If you can't attend you must let someone in management know in advance.*\n\n"
            "■ *Weekly crew meets, and crew color photoshoots.*\n\n"
            "■ *Crew events on other games if requested by another member.*"
        )
        await interaction.response.send_message(text, ephemeral=True)

    @discord.ui.button(
        label="Crew Positions",
        emoji="📌",
        style=discord.ButtonStyle.secondary,
        custom_id="diff_interview_positions",
        row=1,
    )
    async def crew_positions(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = (
            "__**Crew Positions**__\n\n"
            "*If you're interested in any one of these roles, please message the Leader or Co-Leader of DIFF.*\n\n"
            "■ **Crew Managers**\n"
            "■ **Crew Meet Hosts**\n"
            "■ **Crew Content Creators**\n"
            "■ **Crew Designer Team**\n"
            "■ **Crew Color Team Members**"
        )
        await interaction.response.send_message(text, ephemeral=True)

    @discord.ui.button(
        label="End of Interview",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="diff_interview_end",
        row=1,
    )
    async def end_of_interview(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = (
            "__**End of Interview**__\n\n"
            "*Before you end the interview, ask them if they have any questions, comments, or concerns. "
            "Please say welcome to the crew and that you hope they enjoy their stay here.*\n\n"
            "*We expect all of our members to carry themselves professionally inside and outside the crew. "
            "Make sure you are always representing the crew in a positive light. Having a healthy relationship "
            "with fellow crew members and meet attendees is extremely important. Do you understand?*"
        )
        await interaction.response.send_message(text, ephemeral=True)

    @discord.ui.button(
        label="Leadership Team",
        emoji="👑",
        style=discord.ButtonStyle.danger,
        custom_id="diff_interview_leadership",
        row=1,
    )
    async def leadership_team(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        leader_text = f"<@&{LEADER_ROLE_ID}>"
        co_leader_text = f"<@&{CO_LEADER_ROLE_ID}>"
        manager_text = f"<@&{MANAGER_ROLE_ID}>"

        if guild is not None:
            if guild.get_role(LEADER_ROLE_ID) is None:
                leader_text = "**Leader role not set**"
            if guild.get_role(CO_LEADER_ROLE_ID) is None:
                co_leader_text = "**Co-Leader role not set**"
            if guild.get_role(MANAGER_ROLE_ID) is None:
                manager_text = "**Manager role not set**"

        text = (
            "__**Crew Leadership & Management Team**__\n\n"
            "*Please direct the applicant you're interviewing to the higher-ups list so they know who to contact "
            "if they have any questions, comments, or concerns.*\n\n"
            "﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍\n\n"
            f"👑 **Leader:** {leader_text}\n\n"
            f"🛡️ **Co-Leader:** {co_leader_text}\n\n"
            f"📋 **Managers:** {manager_text}\n\n"
            "﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍\n\n"
            "**STARTED THIS CREW ON AUGUST 20TH 2020**"
        )
        await interaction.response.send_message(text, ephemeral=True)


async def _post_or_refresh_interview_panel() -> None:
    guild = bot.guilds[0] if bot.guilds else None
    if guild is None:
        return
    channel = guild.get_channel(INTERVIEW_PANEL_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        return
    data = _interview_panel_load()
    embed = _build_interview_panel_embed()
    view = InterviewInfoView()
    old_ch_id = data.get("channel_id")
    old_msg_id = data.get("message_id")
    if old_ch_id and old_msg_id:
        old_channel = guild.get_channel(int(old_ch_id))
        if isinstance(old_channel, discord.TextChannel):
            try:
                old_msg = await old_channel.fetch_message(int(old_msg_id))
                if old_channel.id == channel.id:
                    await old_msg.edit(embed=embed, view=view)
                    return
                else:
                    try:
                        await old_msg.delete()
                    except discord.HTTPException:
                        pass
            except (discord.NotFound, discord.HTTPException):
                pass
    msg = await channel.send(embed=embed, view=view)
    _interview_panel_save({"channel_id": channel.id, "message_id": msg.id})


@bot.tree.command(name="post-interview-panel", description="Post or refresh the Crew Interview Zone panel (staff only)")
@app_commands.checks.has_permissions(manage_guild=True)
async def post_interview_panel(interaction: discord.Interaction):
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return
    await _post_or_refresh_interview_panel()
    guild = interaction.guild
    channel = guild.get_channel(INTERVIEW_PANEL_CHANNEL_ID) if guild else None
    mention = channel.mention if isinstance(channel, discord.TextChannel) else "the interview channel"
    await interaction.followup.send(f"Interview panel posted or refreshed in {mention}.", ephemeral=True)


@bot.tree.command(name="refresh-interview-panel", description="Refresh the interview panel in place without reposting (staff only)")
@app_commands.checks.has_permissions(manage_guild=True)
async def refresh_interview_panel(interaction: discord.Interaction):
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return
    await _post_or_refresh_interview_panel()
    await interaction.followup.send("Interview panel refreshed.", ephemeral=True)


# =========================
# INTERVIEW OUTCOME SYSTEM
# =========================

def _interview_outcome_load() -> dict:
    return _load_diff_json(INTERVIEW_OUTCOME_FILE) or {}


def _interview_outcome_save(data: dict) -> None:
    _save_diff_json(INTERVIEW_OUTCOME_FILE, data)


def _interview_outcome_can_manage(member: discord.Member) -> bool:
    return any(r.id in INTERVIEW_OUTCOME_ALLOWED_ROLES for r in member.roles)


def _build_interview_outcome_embed() -> discord.Embed:
    embed = discord.Embed(
        title="✅ DIFF Interview Results Panel",
        description=(
            "*Use this panel after the applicant interview is complete.*\n\n"
            "This system helps staff finalize interview decisions in a clean, professional, "
            "and trackable way inside the ticket.\n\n"
            "﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍\n\n"
            "✅ **Accept Applicant** — approve the applicant, assign the crew role, and log the result\n\n"
            "❌ **Deny Applicant** — mark the applicant as denied and send a clean result log\n\n"
            "📌 **Applicant Reminder** — quick checklist before choosing the final result\n\n"
            "﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍﹍\n\n"
            "🎯 Keep decisions respectful, consistent, and clearly logged for staff review."
        ),
        color=discord.Color.green(),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Different Meets • Interview Outcome System")
    return embed


async def _interview_outcome_send_log(
    guild: discord.Guild,
    applicant: discord.Member,
    interviewer: discord.Member,
    result: str,
    notes: str,
    role_given: str | None = None,
    ticket_channel: discord.TextChannel | None = None,
) -> None:
    channel = guild.get_channel(INTERVIEW_OUTCOME_LOG_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        return
    color = discord.Color.green() if result == "Accepted" else discord.Color.red()
    icon = "✅" if result == "Accepted" else "❌"
    embed = discord.Embed(
        title=f"{icon} Interview Result Logged",
        color=color,
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name="Applicant", value=applicant.mention, inline=True)
    embed.add_field(name="Handled By", value=interviewer.mention, inline=True)
    embed.add_field(name="Result", value=result, inline=True)
    embed.add_field(name="Ticket Channel", value=ticket_channel.mention if ticket_channel else "Unknown", inline=True)
    embed.add_field(name="Role Given", value=role_given or "None", inline=True)
    embed.add_field(name="Date", value=datetime.now(timezone.utc).strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="Notes", value=notes if notes else "No notes added.", inline=False)
    embed.set_footer(text="Different Meets • Applicant Review Log")
    await channel.send(embed=embed)


async def _interview_outcome_send_onboarding(guild: discord.Guild, applicant: discord.Member) -> None:
    channel = guild.get_channel(INTERVIEW_OUTCOME_ONBOARDING_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        return
    embed = discord.Embed(
        title="🎉 Welcome to Different Meets",
        description=(
            f"{applicant.mention} has officially been accepted into **DIFF**.\n\n"
            "Please welcome them to the crew and help them get settled in.\n\n"
            "📌 Make sure to review the server, stay active, check announcements, "
            "and be ready for upcoming meets and crew events."
        ),
        color=discord.Color.blue(),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Different Meets • New Member Onboarding")
    await channel.send(embed=embed)


async def _interview_outcome_close_ticket(channel: discord.TextChannel, status: str) -> None:
    try:
        await channel.send(
            f"🔒 This interview ticket has been marked as **{status}**.\n"
            f"Closing this channel in **{INTERVIEW_OUTCOME_CLOSE_DELAY} seconds**."
        )
    except discord.HTTPException:
        pass
    await asyncio.sleep(INTERVIEW_OUTCOME_CLOSE_DELAY)
    try:
        await channel.delete(reason=f"DIFF interview ticket auto-closed after {status.lower()}.")
    except discord.HTTPException:
        pass


async def _interview_outcome_dm_accept(applicant: discord.Member) -> None:
    try:
        await applicant.send(
            "✅ **Welcome to Different Meets (DIFF)!**\n\n"
            "Your interview has been accepted.\n\n"
            "Please make sure you review the server information, stay active, "
            "and represent DIFF the right way at meets and events.\n\n"
            "Welcome to the crew."
        )
    except discord.HTTPException:
        pass


async def _interview_outcome_dm_deny(applicant: discord.Member, notes: str) -> None:
    msg = (
        "❌ **DIFF Interview Update**\n\n"
        "Thank you for taking the time to interview with Different Meets.\n\n"
        "At this time, your application was not accepted. "
        "Please continue improving and feel free to reapply in the future.\n\n"
    )
    if notes:
        msg += f"**Notes:** {notes}"
    try:
        await applicant.send(msg)
    except discord.HTTPException:
        pass


async def _interview_outcome_process_accept(
    interaction: discord.Interaction, applicant: discord.Member, notes: str
) -> None:
    guild = interaction.guild
    interviewer = interaction.user
    if guild is None or not isinstance(interviewer, discord.Member):
        await interaction.response.send_message("This can only be used in a server.", ephemeral=True)
        return

    ticket_channel = interaction.channel if isinstance(interaction.channel, discord.TextChannel) else None

    role = guild.get_role(CREW_MEMBER_ROLE_ID)
    assigned_role_name: str | None = None
    if role is not None:
        try:
            await applicant.add_roles(role, reason=f"Accepted into DIFF by {interviewer}")
            assigned_role_name = role.name
        except discord.HTTPException:
            assigned_role_name = "Role assignment failed"

    result_embed = discord.Embed(
        title="✅ Applicant Accepted",
        description=(
            f"{applicant.mention} has been accepted into **Different Meets (DIFF)**.\n\n"
            "Please welcome them to the crew and make sure they understand the expectations, "
            "crew standards, and activity requirements."
        ),
        color=discord.Color.green(),
        timestamp=datetime.now(timezone.utc),
    )
    result_embed.add_field(name="Handled By", value=interviewer.mention, inline=True)
    result_embed.add_field(name="Crew Role", value=assigned_role_name or "Not assigned", inline=True)
    result_embed.add_field(name="Notes", value=notes if notes else "No notes added.", inline=False)
    result_embed.set_footer(text="Different Meets • Interview Accepted")

    await _interview_outcome_dm_accept(applicant)
    await _interview_outcome_send_onboarding(guild, applicant)
    await _interview_outcome_send_log(guild, applicant, interviewer, "Accepted", notes, assigned_role_name, ticket_channel)

    if interaction.response.is_done():
        await interaction.followup.send(embed=result_embed)
    else:
        await interaction.response.send_message(embed=result_embed)

    if ticket_channel and INTERVIEW_OUTCOME_AUTO_CLOSE:
        asyncio.ensure_future(_interview_outcome_close_ticket(ticket_channel, "Accepted"))


async def _interview_outcome_process_deny(
    interaction: discord.Interaction, applicant: discord.Member, notes: str
) -> None:
    guild = interaction.guild
    interviewer = interaction.user
    if guild is None or not isinstance(interviewer, discord.Member):
        await interaction.response.send_message("This can only be used in a server.", ephemeral=True)
        return

    ticket_channel = interaction.channel if isinstance(interaction.channel, discord.TextChannel) else None

    result_embed = discord.Embed(
        title="❌ Applicant Denied",
        description=(
            f"{applicant.mention} has been marked as **not accepted** for DIFF at this time.\n\n"
            "Make sure all feedback stays respectful and professional."
        ),
        color=discord.Color.red(),
        timestamp=datetime.now(timezone.utc),
    )
    result_embed.add_field(name="Handled By", value=interviewer.mention, inline=True)
    result_embed.add_field(name="Notes", value=notes if notes else "No notes added.", inline=False)
    result_embed.set_footer(text="Different Meets • Interview Denied")

    await _interview_outcome_dm_deny(applicant, notes)
    await _interview_outcome_send_log(guild, applicant, interviewer, "Denied", notes, ticket_channel=ticket_channel)

    if interaction.response.is_done():
        await interaction.followup.send(embed=result_embed)
    else:
        await interaction.response.send_message(embed=result_embed)

    if ticket_channel and INTERVIEW_OUTCOME_AUTO_CLOSE:
        asyncio.ensure_future(_interview_outcome_close_ticket(ticket_channel, "Denied"))


class ApplicantLookupModal(discord.ui.Modal, title="Interview Result"):
    applicant_input = discord.ui.TextInput(
        label="Applicant User ID",
        placeholder="Paste the applicant Discord user ID here",
        required=True,
        max_length=25,
    )
    reason_input = discord.ui.TextInput(
        label="Notes / Reason",
        placeholder="Optional notes for logs or feedback",
        required=False,
        style=discord.TextStyle.paragraph,
        max_length=1000,
    )

    def __init__(self, action: str):
        super().__init__()
        self.action = action

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("This can only be used inside the server.", ephemeral=True)
        if not _interview_outcome_can_manage(interaction.user):
            return await interaction.response.send_message("You do not have permission to use this panel.", ephemeral=True)

        raw_id = str(self.applicant_input.value).strip().replace("<@", "").replace(">", "").replace("!", "")
        try:
            applicant_id = int(raw_id)
        except ValueError:
            return await interaction.response.send_message("That user ID is not valid.", ephemeral=True)

        applicant = interaction.guild.get_member(applicant_id)
        if applicant is None:
            try:
                applicant = await interaction.guild.fetch_member(applicant_id)
            except (discord.NotFound, discord.HTTPException):
                applicant = None

        if applicant is None:
            return await interaction.response.send_message(
                "I could not find that applicant in the server. Make sure they are still in the server and paste the correct user ID.",
                ephemeral=True,
            )

        notes = str(self.reason_input.value).strip()
        if self.action == "accept":
            await _interview_outcome_process_accept(interaction, applicant, notes)
        else:
            await _interview_outcome_process_deny(interaction, applicant, notes)


class InterviewOutcomeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Accept Applicant",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="diff_interview_accept",
        row=0,
    )
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("This can only be used inside the server.", ephemeral=True)
        if not _interview_outcome_can_manage(interaction.user):
            return await interaction.response.send_message(
                "Only Leader, Co-Leader, or Manager can use this outcome panel.", ephemeral=True
            )
        await interaction.response.send_modal(ApplicantLookupModal("accept"))

    @discord.ui.button(
        label="Deny Applicant",
        emoji="❌",
        style=discord.ButtonStyle.danger,
        custom_id="diff_interview_deny",
        row=0,
    )
    async def deny_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("This can only be used inside the server.", ephemeral=True)
        if not _interview_outcome_can_manage(interaction.user):
            return await interaction.response.send_message(
                "Only Leader, Co-Leader, or Manager can use this outcome panel.", ephemeral=True
            )
        await interaction.response.send_modal(ApplicantLookupModal("deny"))

    @discord.ui.button(
        label="Applicant Reminder",
        emoji="📌",
        style=discord.ButtonStyle.secondary,
        custom_id="diff_interview_reminder",
        row=1,
    )
    async def reminder_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = (
            "__**Interview Result Reminder**__\n\n"
            "• Confirm the applicant finished the interview\n"
            "• Review their answers carefully\n"
            "• Keep notes professional and clear\n"
            "• If accepted, make sure they understand DIFF expectations\n"
            "• If denied, be respectful and explain the reason clearly\n"
            "• Use this panel only after the interview is fully completed"
        )
        await interaction.response.send_message(text, ephemeral=True)


async def _post_or_refresh_interview_outcome_panel(channel: discord.TextChannel) -> None:
    data = _interview_outcome_load()
    embed = _build_interview_outcome_embed()
    view = InterviewOutcomeView()
    old_ch_id = data.get("channel_id")
    old_msg_id = data.get("message_id")
    if old_ch_id and old_msg_id:
        old_channel = bot.get_channel(int(old_ch_id))
        if isinstance(old_channel, discord.TextChannel):
            try:
                old_msg = await old_channel.fetch_message(int(old_msg_id))
                if old_channel.id == channel.id:
                    await old_msg.edit(embed=embed, view=view)
                    return
                else:
                    try:
                        await old_msg.delete()
                    except discord.HTTPException:
                        pass
            except (discord.NotFound, discord.HTTPException):
                pass
    msg = await channel.send(embed=embed, view=view)
    _interview_outcome_save({"channel_id": channel.id, "message_id": msg.id})


@bot.tree.command(name="post-interview-results-panel", description="Post the accept/deny interview results panel in this channel (Leader/Co-Leader/Manager only)")
async def post_interview_results_panel(interaction: discord.Interaction):
    if not interaction.guild or not isinstance(interaction.channel, discord.TextChannel):
        return await interaction.response.send_message("Run this command in the ticket channel where you want the panel.", ephemeral=True)
    if not isinstance(interaction.user, discord.Member) or not _interview_outcome_can_manage(interaction.user):
        return await interaction.response.send_message("Only Leader, Co-Leader, or Manager can post this panel.", ephemeral=True)
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return
    await _post_or_refresh_interview_outcome_panel(interaction.channel)
    await interaction.followup.send(f"Interview results panel posted in {interaction.channel.mention}.", ephemeral=True)


# =========================
# TICKET APPLICATION BRIDGE
# =========================

def _tab_load() -> dict:
    raw = _load_diff_json(TICKET_APP_BRIDGE_FILE)
    if not raw:
        return {"applications": {}, "ticket_links": {}}
    raw.setdefault("applications", {})
    raw.setdefault("ticket_links", {})
    return raw


def _tab_save(state: dict) -> None:
    _save_diff_json(TICKET_APP_BRIDGE_FILE, state)


def _tab_get_app(state: dict, user_id: int) -> dict:
    key = str(user_id)
    if key not in state["applications"]:
        state["applications"][key] = {
            "user_id": user_id,
            "display_name": None,
            "status": "Applied",
            "submitted_at": None,
            "interview_scheduled_for": None,
            "interview_notes": None,
            "result_notes": None,
            "reviewed_by": None,
            "last_updated_at": None,
        }
    return state["applications"][key]


def _tab_now() -> str:
    return datetime.now(COLOR_TZ).strftime("%Y-%m-%d %I:%M %p ET")


def _tab_build_status_embed(member: discord.Member, app: dict) -> discord.Embed:
    embed = discord.Embed(
        title="📋 Application Review Panel",
        description=(
            f"Use the buttons below to move **{member.mention}** through the application process.\n\n"
            "This ticket is now directly connected to application review and interview actions."
        ),
        color=discord.Color.blue(),
        timestamp=datetime.utcnow(),
    )
    embed.add_field(name="Applicant", value=member.mention, inline=False)
    embed.add_field(name="Current Status", value=f"**{app.get('status', 'Unknown')}**", inline=True)
    embed.add_field(name="Submitted", value=app.get("submitted_at") or "Not logged", inline=True)
    if app.get("interview_scheduled_for"):
        embed.add_field(name="Interview Scheduled", value=app["interview_scheduled_for"], inline=False)
    if app.get("interview_notes"):
        embed.add_field(name="Interview Notes", value=app["interview_notes"], inline=False)
    if app.get("result_notes"):
        embed.add_field(name="Result Notes", value=app["result_notes"], inline=False)
    if app.get("reviewed_by"):
        embed.add_field(name="Last Reviewed By", value=app["reviewed_by"], inline=False)
    embed.set_footer(text="Different Meets • Ticket Application Bridge")
    return embed


async def _tab_post_staff_log(title: str, description: str, color: discord.Color) -> None:
    guild = bot.guilds[0] if bot.guilds else None
    if guild is None:
        return
    channel = guild.get_channel(STAFF_LOGS_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        return
    embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.utcnow())
    embed.set_footer(text="Different Meets • Staff Logs")
    await channel.send(embed=embed)


async def _fus_safe_dm(member: discord.Member, message: str) -> None:
    try:
        em = discord.Embed(
            description=message,
            color=discord.Color.dark_blue(),
        )
        em.set_author(name="Different Meets", icon_url=DIFF_LOGO_URL)
        em.set_thumbnail(url=DIFF_LOGO_URL)
        await member.send(embed=em)
    except Exception:
        pass


def _fus_detect_applicant(channel: discord.TextChannel) -> discord.Member | None:
    guild = channel.guild
    for target, overwrite in channel.overwrites.items():
        if not isinstance(target, discord.Member):
            continue
        if target.bot:
            continue
        if _interview_outcome_can_manage(target):
            continue
        if overwrite.view_channel is True or overwrite.send_messages is True:
            return target
    name = channel.name.lower()
    for member in guild.members:
        if member.bot or _interview_outcome_can_manage(member):
            continue
        compact = member.name.lower().replace(" ", "-")
        if compact in name:
            return member
    return None


async def _fus_handle_approval(member: discord.Member, channel: discord.TextChannel, notes: str) -> None:
    guild = channel.guild
    role = guild.get_role(CREW_MEMBER_ROLE_ID)
    if role:
        try:
            await member.add_roles(role, reason="DIFF application approved")
        except Exception:
            pass
    if FUS_DM_ON_APPROVAL:
        await _fus_safe_dm(
            member,
            f"Your DIFF application has been **Approved**.\n\n"
            f"**Notes:** {notes}\n"
            "Welcome to Different Meets.",
        )
    try:
        await channel.send(
            f"✅ {member.mention} has been approved."
            + (f" Role assigned: {role.mention}" if role else "")
        )
    except Exception:
        pass
    if FUS_AUTO_CLOSE_ENABLED:
        await channel.send(f"🧼 This ticket will close in **{FUS_AUTO_CLOSE_DELAY_SECONDS} seconds**.")
        asyncio.ensure_future(_fus_delayed_close(channel, FUS_AUTO_CLOSE_DELAY_SECONDS))


async def _fus_delayed_close(channel: discord.TextChannel, delay: int) -> None:
    await asyncio.sleep(delay)
    try:
        await channel.delete(reason="DIFF application workflow complete")
    except Exception:
        pass


async def _tab_refresh_all_panels() -> None:
    await asyncio.sleep(3)
    state = _tab_load()
    for ticket_key, link_data in list(state.get("ticket_links", {}).items()):
        member_id = link_data.get("member_id")
        channel_id = int(ticket_key)
        if not member_id:
            continue
        channel = bot.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            continue
        guild = channel.guild
        member = guild.get_member(int(member_id))
        if member is None:
            try:
                member = await guild.fetch_member(int(member_id))
            except Exception:
                continue
        try:
            await _tab_update_panel(channel, member, state)
        except Exception:
            pass


async def _startup_refresh_all_panels() -> None:
    await asyncio.sleep(5)

    async def _safe_edit(channel_id: int, message_id: int, embed_fn, view_fn) -> None:
        try:
            ch = bot.get_channel(channel_id)
            if ch is None:
                ch = await bot.fetch_channel(channel_id)
            if not isinstance(ch, discord.TextChannel):
                return
            msg = await ch.fetch_message(message_id)
            await msg.edit(embed=embed_fn(), view=view_fn())
        except Exception:
            pass

    try:
        interview_data = _interview_panel_load()
        ch_id = interview_data.get("channel_id")
        msg_id = interview_data.get("message_id")
        if ch_id and msg_id:
            await _safe_edit(int(ch_id), int(msg_id), _build_interview_panel_embed, InterviewInfoView)
    except Exception:
        pass

    try:
        color_state = _load_diff_json(COLOR_PANEL_STATE_FILE)
        ch_id = color_state.get("channel_id")
        msg_id = color_state.get("message_id")
        if ch_id and msg_id:
            await _safe_edit(int(ch_id), int(msg_id), _cs_build_panel_embed, ColorSubmissionPanelView)
    except Exception:
        pass

    try:
        panel_state = _load_diff_json(DIFF_PANEL_STATE_FILE)
        color_team_msg_id = panel_state.get(COLOR_TEAM_PANEL_STATE_KEY)
        if color_team_msg_id:
            guild = bot.guilds[0] if bot.guilds else None
            if guild:
                ch = guild.get_channel(COLOR_TEAM_POST_CHANNEL_ID)
                if isinstance(ch, discord.TextChannel):
                    try:
                        msg = await ch.fetch_message(int(color_team_msg_id))
                        await msg.edit(embed=_build_color_team_embed(), view=ColorTeamPanelView())
                    except Exception:
                        pass
    except Exception:
        pass

    try:
        hub_data = _load_diff_json(ATT_CONTROL_HUB_FILE)
        ch_id = hub_data.get("channel_id")
        msg_id = hub_data.get("message_id")
        if ch_id and msg_id:
            await _safe_edit(int(ch_id), int(msg_id), _rsvp_build_control_hub_embed, ControlHubView)
    except Exception:
        pass

    try:
        outcome_data = _interview_outcome_load()
        ch_id = outcome_data.get("channel_id")
        msg_id = outcome_data.get("message_id")
        if ch_id and msg_id:
            await _safe_edit(int(ch_id), int(msg_id), _build_interview_outcome_embed, InterviewOutcomeView)
    except Exception:
        pass

    try:
        meet_info_msg_id = data.get("meet_info_message_id")
        if meet_info_msg_id:
            guild = bot.guilds[0] if bot.guilds else None
            if guild:
                ch = guild.get_channel(MEET_INFO_CHANNEL_ID)
                if isinstance(ch, discord.TextChannel):
                    try:
                        msg = await ch.fetch_message(int(meet_info_msg_id))
                        await msg.edit(
                            embed=build_meet_info_embed(),
                            view=build_meet_info_view(guild.id),
                        )
                    except Exception:
                        pass
    except Exception:
        pass


async def _tab_update_panel(channel: discord.TextChannel, member: discord.Member, state: dict) -> None:
    app = _tab_get_app(state, member.id)
    embed = _tab_build_status_embed(member, app)
    view = ApplicationReviewView(member.id)
    ticket_key = str(channel.id)
    panel_msg_id = state["ticket_links"].get(ticket_key, {}).get("panel_message_id")
    if panel_msg_id:
        try:
            msg = await channel.fetch_message(int(panel_msg_id))
            await msg.edit(embed=embed, view=view)
            _tab_save(state)
            return
        except (discord.NotFound, discord.HTTPException):
            pass
    msg = await channel.send(embed=embed, view=view)
    state["ticket_links"].setdefault(ticket_key, {})["panel_message_id"] = msg.id
    _tab_save(state)


class InterviewScheduleModal(discord.ui.Modal, title="Schedule Interview"):
    interview_time = discord.ui.TextInput(
        label="Interview time",
        placeholder="Example: Friday 7:30 PM ET",
        max_length=100,
        required=True,
    )
    notes = discord.ui.TextInput(
        label="Interview notes",
        placeholder="Any notes for staff or the applicant",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=500,
    )

    def __init__(self, member_id: int):
        super().__init__()
        self.member_id = member_id

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.guild is None:
            return await interaction.response.send_message("Server only.", ephemeral=True)
        member = interaction.guild.get_member(self.member_id)
        if member is None:
            return await interaction.response.send_message("Applicant not found in this server.", ephemeral=True)

        state = _tab_load()
        app = _tab_get_app(state, member.id)
        now = _tab_now()
        app.update({
            "display_name": member.display_name,
            "status": "Interview Scheduled",
            "interview_scheduled_for": str(self.interview_time),
            "interview_notes": str(self.notes) if self.notes else "No notes provided.",
            "reviewed_by": interaction.user.mention,
            "submitted_at": app.get("submitted_at") or now,
            "last_updated_at": now,
        })
        _tab_save(state)

        await _tab_post_staff_log(
            "🎤 Interview Scheduled",
            (
                f"**Applicant:** {member.mention}\n"
                f"**Interview:** {self.interview_time}\n"
                f"**Notes:** {self.notes or 'No notes provided.'}\n"
                f"**Reviewed By:** {interaction.user.mention}"
            ),
            discord.Color.orange(),
        )
        if FUS_DM_ON_INTERVIEW:
            await _fus_safe_dm(
                member,
                f"Your DIFF application has moved to the **Interview Scheduled** stage.\n\n"
                f"**Interview Time:** {self.interview_time}\n"
                f"**Notes:** {self.notes or 'No notes provided.'}",
            )
        if isinstance(interaction.channel, discord.TextChannel):
            await _tab_update_panel(interaction.channel, member, state)
        await interaction.response.send_message(f"Interview scheduled for {member.mention}.", ephemeral=True)


class ApplicationResultModal(discord.ui.Modal):
    result_notes = discord.ui.TextInput(
        label="Result notes",
        placeholder="Reason or final notes",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=500,
    )

    def __init__(self, member_id: int, result_name: str):
        super().__init__(title=f"{result_name} Application")
        self.member_id = member_id
        self.result_name = result_name

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.guild is None:
            return await interaction.response.send_message("Server only.", ephemeral=True)
        member = interaction.guild.get_member(self.member_id)
        if member is None:
            return await interaction.response.send_message("Applicant not found in this server.", ephemeral=True)

        state = _tab_load()
        app = _tab_get_app(state, member.id)
        now = _tab_now()
        app.update({
            "display_name": member.display_name,
            "status": self.result_name,
            "result_notes": str(self.result_notes) if self.result_notes else "No notes provided.",
            "reviewed_by": interaction.user.mention,
            "submitted_at": app.get("submitted_at") or now,
            "last_updated_at": now,
        })
        _tab_save(state)

        color = discord.Color.green() if self.result_name == "Approved" else discord.Color.red()
        icon = "✅" if self.result_name == "Approved" else "❌"
        await _tab_post_staff_log(
            f"{icon} Application {self.result_name}",
            (
                f"**Applicant:** {member.mention}\n"
                f"**Status:** {self.result_name}\n"
                f"**Notes:** {self.result_notes or 'No notes provided.'}\n"
                f"**Reviewed By:** {interaction.user.mention}"
            ),
            color,
        )
        if isinstance(interaction.channel, discord.TextChannel):
            await _tab_update_panel(interaction.channel, member, state)
            if self.result_name == "Approved":
                await _fus_handle_approval(member, interaction.channel, str(self.result_notes) if self.result_notes else "No notes provided.")
            else:
                if FUS_DM_ON_DENIAL:
                    await _fus_safe_dm(
                        member,
                        f"Your DIFF application has been **Denied**.\n\n"
                        f"**Notes:** {self.result_notes or 'No notes provided.'}",
                    )
                if FUS_AUTO_CLOSE_ENABLED:
                    await interaction.channel.send(f"🧼 This ticket will close in **{FUS_AUTO_CLOSE_DELAY_SECONDS} seconds**.")
                    asyncio.ensure_future(_fus_delayed_close(interaction.channel, FUS_AUTO_CLOSE_DELAY_SECONDS))
        await interaction.response.send_message(
            f"Application marked as **{self.result_name}** for {member.mention}.", ephemeral=True
        )


class ApplicationReviewView(discord.ui.View):
    def __init__(self, target_member_id: int):
        super().__init__(timeout=None)
        self.target_member_id = target_member_id
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.custom_id:
                item.custom_id = f"{item.custom_id}:{target_member_id}"

    async def _check_staff(self, interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member) or not _interview_outcome_can_manage(interaction.user):
            await interaction.response.send_message(
                "You do not have permission to use these review buttons.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Mark Applied", style=discord.ButtonStyle.secondary, emoji="🧾", custom_id="tab_mark_applied")
    async def mark_applied(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_staff(interaction):
            return
        if interaction.guild is None:
            return await interaction.response.send_message("Server only.", ephemeral=True)
        member = interaction.guild.get_member(self.target_member_id)
        if member is None:
            return await interaction.response.send_message("Applicant not found in this server.", ephemeral=True)

        state = _tab_load()
        app = _tab_get_app(state, member.id)
        now = _tab_now()
        app.update({
            "display_name": member.display_name,
            "status": "Applied",
            "submitted_at": app.get("submitted_at") or now,
            "reviewed_by": interaction.user.mention,
            "last_updated_at": now,
        })
        _tab_save(state)

        await _tab_post_staff_log(
            "🧾 Application Linked",
            (
                f"**Applicant:** {member.mention}\n"
                f"**Status:** Applied\n"
                f"**Linked By:** {interaction.user.mention}\n"
                f"**Ticket:** {interaction.channel.mention}"
            ),
            discord.Color.blurple(),
        )
        if isinstance(interaction.channel, discord.TextChannel):
            await _tab_update_panel(interaction.channel, member, state)
        await interaction.response.send_message(f"{member.mention} marked as applied.", ephemeral=True)

    @discord.ui.button(label="Schedule Interview", style=discord.ButtonStyle.primary, emoji="🎤", custom_id="tab_schedule_interview")
    async def schedule_interview(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_staff(interaction):
            return
        await interaction.response.send_modal(InterviewScheduleModal(self.target_member_id))

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success, emoji="✅", custom_id="tab_approve")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_staff(interaction):
            return
        await interaction.response.send_modal(ApplicationResultModal(self.target_member_id, "Approved"))

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger, emoji="❌", custom_id="tab_deny")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_staff(interaction):
            return
        await interaction.response.send_modal(ApplicationResultModal(self.target_member_id, "Denied"))


@bot.tree.command(name="send-application-review-panel", description="Post the application review panel for a member in this ticket (staff only)")
@app_commands.describe(member="The applicant to link to this ticket")
@app_commands.checks.has_permissions(manage_guild=True)
async def send_application_review_panel(interaction: discord.Interaction, member: discord.Member):
    if not isinstance(interaction.channel, discord.TextChannel):
        return await interaction.response.send_message("Run this command inside the ticket channel.", ephemeral=True)
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return
    state = _tab_load()
    ticket_key = str(interaction.channel.id)
    state["ticket_links"].setdefault(ticket_key, {})["member_id"] = member.id
    await _tab_update_panel(interaction.channel, member, state)
    await interaction.followup.send(
        f"Application review panel connected to {member.mention} in this ticket.", ephemeral=True
    )


@bot.tree.command(name="link-application-ticket", description="Link the current ticket channel to an applicant and log it (staff only)")
@app_commands.describe(member="The applicant to link")
@app_commands.checks.has_permissions(manage_guild=True)
async def link_application_ticket(interaction: discord.Interaction, member: discord.Member):
    if not isinstance(interaction.channel, discord.TextChannel):
        return await interaction.response.send_message("Run this command inside the ticket channel.", ephemeral=True)
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return
    state = _tab_load()
    app = _tab_get_app(state, member.id)
    now = _tab_now()
    app.update({
        "display_name": member.display_name,
        "submitted_at": app.get("submitted_at") or now,
        "status": app.get("status") or "Applied",
        "last_updated_at": now,
        "reviewed_by": interaction.user.mention,
    })
    ticket_key = str(interaction.channel.id)
    state["ticket_links"].setdefault(ticket_key, {})["member_id"] = member.id
    await _tab_update_panel(interaction.channel, member, state)
    await _tab_post_staff_log(
        "🔗 Ticket Linked to Application",
        (
            f"**Applicant:** {member.mention}\n"
            f"**Ticket:** {interaction.channel.mention}\n"
            f"**Linked By:** {interaction.user.mention}"
        ),
        discord.Color.blurple(),
    )
    await interaction.followup.send(
        f"This ticket is now linked to {member.mention}'s application.", ephemeral=True
    )


@bot.tree.command(name="setup-application-ticket", description="Auto-detect the applicant in this ticket and attach the review panel (staff only)")
@app_commands.checks.has_permissions(manage_guild=True)
async def setup_application_ticket(interaction: discord.Interaction):
    if not isinstance(interaction.channel, discord.TextChannel):
        return await interaction.response.send_message("Use this command inside a ticket text channel.", ephemeral=True)
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return
    applicant = _fus_detect_applicant(interaction.channel)
    if applicant is None:
        return await interaction.followup.send(
            "I could not auto-detect the applicant in this ticket. "
            "Use `/send-application-review-panel @member` to link manually.", ephemeral=True
        )
    state = _tab_load()
    app = _tab_get_app(state, applicant.id)
    now = _tab_now()
    app.update({
        "display_name": applicant.display_name,
        "submitted_at": app.get("submitted_at") or now,
        "status": app.get("status") or "Applied",
        "last_updated_at": now,
    })
    ticket_key = str(interaction.channel.id)
    state["ticket_links"].setdefault(ticket_key, {})["member_id"] = applicant.id
    await _tab_update_panel(interaction.channel, applicant, state)
    await _tab_post_staff_log(
        "🔗 Ticket Auto-Connected",
        (
            f"**Applicant:** {applicant.mention}\n"
            f"**Ticket:** {interaction.channel.mention}\n"
            f"**Status:** {app['status']}"
        ),
        discord.Color.blurple(),
    )
    await interaction.followup.send(f"Review panel attached for {applicant.mention}.", ephemeral=True)


@bot.tree.command(name="rebuild-application-panel", description="Rebuild the review panel in this ticket if it was deleted (staff only)")
@app_commands.checks.has_permissions(manage_guild=True)
async def rebuild_application_panel(interaction: discord.Interaction):
    if not isinstance(interaction.channel, discord.TextChannel):
        return await interaction.response.send_message("Use this command inside a ticket text channel.", ephemeral=True)
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return
    state = _tab_load()
    ticket_key = str(interaction.channel.id)
    link = state["ticket_links"].get(ticket_key)
    if link and link.get("member_id"):
        applicant = interaction.guild.get_member(int(link["member_id"])) if interaction.guild else None
    else:
        applicant = _fus_detect_applicant(interaction.channel)
    if applicant is None:
        return await interaction.followup.send("Could not find the applicant for this ticket.", ephemeral=True)
    state["ticket_links"].setdefault(ticket_key, {}).pop("panel_message_id", None)
    state["ticket_links"][ticket_key]["member_id"] = applicant.id
    await _tab_update_panel(interaction.channel, applicant, state)
    await interaction.followup.send("Application review panel rebuilt.", ephemeral=True)


@bot.tree.command(name="application-status", description="Show the linked application status for this ticket (staff only)")
@app_commands.checks.has_permissions(manage_guild=True)
async def application_status(interaction: discord.Interaction):
    if not isinstance(interaction.channel, discord.TextChannel):
        return await interaction.response.send_message("Run this command inside a ticket channel.", ephemeral=True)
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return
    state = _tab_load()
    link = state["ticket_links"].get(str(interaction.channel.id))
    if not link or not link.get("member_id"):
        return await interaction.followup.send("This ticket is not linked to an application yet.", ephemeral=True)
    member = interaction.guild.get_member(int(link["member_id"])) if interaction.guild else None
    if member is None:
        return await interaction.followup.send("That linked applicant is no longer in the server.", ephemeral=True)
    app = _tab_get_app(state, member.id)
    embed = _tab_build_status_embed(member, app)
    await interaction.followup.send(embed=embed, ephemeral=True)


@tasks.loop(minutes=2)
async def ticket_scan_loop():
    guild = bot.guilds[0] if bot.guilds else None
    if guild is None:
        return
    state = _tab_load()
    for channel in guild.text_channels:
        name = channel.name.lower()
        if not any(word in name for word in FUS_TICKET_KEYWORDS):
            continue
        ticket_key = str(channel.id)
        link = state["ticket_links"].get(ticket_key, {})
        if link.get("panel_message_id"):
            continue
        try:
            applicant = _fus_detect_applicant(channel)
        except Exception:
            continue
        if applicant is None:
            continue
        app = _tab_get_app(state, applicant.id)
        now = _tab_now()
        app.update({
            "display_name": applicant.display_name,
            "submitted_at": app.get("submitted_at") or now,
            "status": app.get("status") or "Applied",
            "last_updated_at": now,
        })
        state["ticket_links"].setdefault(ticket_key, {})["member_id"] = applicant.id
        try:
            await _tab_update_panel(channel, applicant, state)
            await _tab_post_staff_log(
                "🔗 Ticket Auto-Connected",
                (
                    f"**Applicant:** {applicant.mention}\n"
                    f"**Ticket:** {channel.mention}\n"
                    f"**Status:** {app['status']}"
                ),
                discord.Color.blurple(),
            )
        except Exception:
            continue


@ticket_scan_loop.before_loop
async def before_ticket_scan_loop():
    await bot.wait_until_ready()


# =========================
# COLOR OPS SYSTEM
# =========================

_COLOR_OPS_STATE_DEFAULTS: dict = {
    "applications": {},
    "colors": {
        "history": [],
        "active_entries": [],
        "contributors": {},
    },
    "panel_messages": {},
}


def _color_ops_load() -> dict:
    raw = _load_diff_json(COLOR_OPS_STATE_FILE)
    if not raw:
        return {k: v for k, v in _COLOR_OPS_STATE_DEFAULTS.items()}
    for key, default in _COLOR_OPS_STATE_DEFAULTS.items():
        raw.setdefault(key, default)
    return raw


def _color_ops_save(state: dict) -> None:
    _save_diff_json(COLOR_OPS_STATE_FILE, state)


def _color_ops_app_bucket(state: dict, user_id: int) -> dict:
    key = str(user_id)
    if key not in state["applications"]:
        state["applications"][key] = {
            "user_id": user_id,
            "display_name": None,
            "status": "Applied",
            "submitted_at": None,
            "interview_scheduled_for": None,
            "interview_notes": None,
            "result_notes": None,
            "reviewed_by": None,
        }
    return state["applications"][key]


def _color_ops_contributor_bucket(state: dict, user_id: int) -> dict:
    key = str(user_id)
    contributors = state["colors"]["contributors"]
    if key not in contributors:
        contributors[key] = {
            "submission_count": 0,
            "win_count": 0,
            "last_submission_at": None,
            "last_win_at": None,
            "display_name": None,
        }
    return contributors[key]


def _build_color_ops_stats_embed(state: dict) -> discord.Embed:
    apps = state["applications"]
    colors = state["colors"]
    history = colors["history"]
    contributors = colors["contributors"]

    approved = sum(1 for x in apps.values() if x.get("status") == "Approved")
    denied = sum(1 for x in apps.values() if x.get("status") == "Denied")
    interviewing = sum(1 for x in apps.values() if x.get("status") == "Interview Scheduled")
    applied = sum(1 for x in apps.values() if x.get("status") == "Applied")
    total_submissions = sum(v.get("submission_count", 0) for v in contributors.values())
    active_entries = len(colors["active_entries"])

    embed = discord.Embed(
        title="📊 DIFF Color + Application Stats",
        description="Live tracking panel for color operations and application/interview flow.",
        color=discord.Color.gold(),
        timestamp=datetime.utcnow(),
    )
    embed.add_field(
        name="🧾 Applications",
        value=(
            f"Applied: **{applied}**\n"
            f"Interview Scheduled: **{interviewing}**\n"
            f"Approved: **{approved}**\n"
            f"Denied: **{denied}**"
        ),
        inline=False,
    )
    embed.add_field(
        name="🎨 Color System",
        value=(
            f"Active Entries: **{active_entries}**\n"
            f"Total Submissions Logged: **{total_submissions}**\n"
            f"Total Winners Logged: **{len(history)}**"
        ),
        inline=False,
    )
    if history:
        last = history[-1]
        contrib_text = (
            f"<@{last['contributor_id']}>" if last.get("contributor_id")
            else "**Unknown**"
        )
        embed.add_field(
            name="🏆 Most Recent Winner",
            value=f"Color: **{last.get('color_name', 'Unknown')}**\nContributor: {contrib_text}",
            inline=False,
        )
    embed.set_footer(text="Different Meets • Staff Logs • Auto-refresh enabled")
    return embed


def _build_color_ops_leaderboard_embed(state: dict) -> discord.Embed:
    contributors = state["colors"]["contributors"]
    sorted_rows = sorted(
        contributors.items(),
        key=lambda kv: (kv[1].get("win_count", 0), kv[1].get("submission_count", 0)),
        reverse=True,
    )
    lines = []
    for index, (user_id, data) in enumerate(sorted_rows[:10], start=1):
        display = data.get("display_name") or f"User {user_id}"
        wins = data.get("win_count", 0)
        subs = data.get("submission_count", 0)
        lines.append(f"**#{index}** {display} — 🏆 `{wins}` wins • 🎨 `{subs}` submissions")
    if not lines:
        lines.append("No contributor data logged yet.")

    embed = discord.Embed(
        title="🏆 DIFF Top Color Contributors",
        description="Leaderboard for the most active and successful color contributors.",
        color=discord.Color.purple(),
        timestamp=datetime.utcnow(),
    )
    embed.add_field(name="📈 Leaderboard", value="\n".join(lines), inline=False)
    embed.add_field(
        name="📌 Notes",
        value=(
            "This panel updates from logged color submissions and weekly winners.\n"
            "Buttons below go straight to the team coordination channels."
        ),
        inline=False,
    )
    embed.set_footer(text="Different Meets • Color Team Leaderboard • No duplicate panels")
    return embed


def _build_color_ops_application_embed(
    member: discord.Member, app_data: dict, title: str, color: discord.Color
) -> discord.Embed:
    embed = discord.Embed(title=title, color=color, timestamp=datetime.utcnow())
    embed.add_field(name="Member", value=member.mention, inline=False)
    embed.add_field(name="Status", value=f"**{app_data.get('status', 'Unknown')}**", inline=True)
    embed.add_field(name="Submitted", value=app_data.get("submitted_at", "Not logged"), inline=True)
    if app_data.get("interview_scheduled_for"):
        embed.add_field(name="Interview Scheduled", value=app_data["interview_scheduled_for"], inline=False)
    if app_data.get("interview_notes"):
        embed.add_field(name="Interview Notes", value=app_data["interview_notes"], inline=False)
    if app_data.get("result_notes"):
        embed.add_field(name="Result Notes", value=app_data["result_notes"], inline=False)
    if app_data.get("reviewed_by"):
        embed.add_field(name="Reviewed By", value=app_data["reviewed_by"], inline=False)
    embed.set_footer(text="Different Meets • Application / Interview System")
    return embed


def _build_color_ops_winner_embed(color_name: str, contributor_text: str, image_url: str | None) -> discord.Embed:
    embed = discord.Embed(
        title="🏆 Weekly Winning Color",
        description=(
            "The crew color has been decided for this cycle.\n\n"
            f"**Winning Color:** {color_name}\n"
            f"**Submitted By:** {contributor_text}\n\n"
            "Use the buttons below for team coordination and the next vote flow."
        ),
        color=discord.Color.blue(),
        timestamp=datetime.utcnow(),
    )
    if image_url:
        embed.set_image(url=image_url)
    embed.set_footer(text="Different Meets • Winner Auto Post")
    return embed


async def _color_ops_upsert_panel(
    channel: discord.TextChannel,
    state: dict,
    key: str,
    embed: discord.Embed,
    view: discord.ui.View | None = None,
    content: str | None = None,
) -> None:
    msg_id = state["panel_messages"].get(key)
    if msg_id:
        try:
            msg = await channel.fetch_message(int(msg_id))
            await msg.edit(content=content, embed=embed, view=view)
            return
        except (discord.NotFound, discord.HTTPException):
            pass
    msg = await channel.send(
        content=content,
        embed=embed,
        view=view,
        allowed_mentions=discord.AllowedMentions(roles=True),
    )
    state["panel_messages"][key] = msg.id


async def _color_ops_refresh_panels() -> None:
    guild = bot.guilds[0] if bot.guilds else None
    if guild is None:
        return
    state = _color_ops_load()
    staff_logs = guild.get_channel(STAFF_LOGS_CHANNEL_ID)
    color_notice = guild.get_channel(COLOR_TEAM_POST_CHANNEL_ID)

    if isinstance(staff_logs, discord.TextChannel):
        await _color_ops_upsert_panel(
            staff_logs, state, "color_ops_stats_panel",
            embed=_build_color_ops_stats_embed(state),
        )
    if isinstance(color_notice, discord.TextChannel):
        role = guild.get_role(COLOR_TEAM_ROLE_ID)
        await _color_ops_upsert_panel(
            color_notice, state, "color_ops_leaderboard_panel",
            embed=_build_color_ops_leaderboard_embed(state),
            view=ColorTeamPanelView(),
            content=role.mention if role else None,
        )
    _color_ops_save(state)


@tasks.loop(minutes=5)
async def color_ops_refresh_loop():
    try:
        await _color_ops_refresh_panels()
    except Exception as e:
        print(f"[COLOR OPS AUTO REFRESH ERROR] {e}")


@color_ops_refresh_loop.before_loop
async def before_color_ops_refresh_loop():
    await bot.wait_until_ready()


# Application / Interview commands

@bot.tree.command(name="log-application", description="Log a member application into the system (staff only)")
@app_commands.describe(member="The applicant", notes="Optional notes")
@app_commands.checks.has_permissions(manage_guild=True)
async def log_application(interaction: discord.Interaction, member: discord.Member, notes: str = "Application logged."):
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return
    state = _color_ops_load()
    app = _color_ops_app_bucket(state, member.id)
    now_str = datetime.now(COLOR_TZ).strftime("%Y-%m-%d %I:%M %p ET")
    app.update({
        "display_name": member.display_name,
        "status": "Applied",
        "submitted_at": now_str,
        "result_notes": notes,
        "reviewed_by": interaction.user.mention,
    })
    _color_ops_save(state)
    embed = _build_color_ops_application_embed(member, app, "🧾 New Application Logged", discord.Color.blurple())
    staff_logs = interaction.guild.get_channel(STAFF_LOGS_CHANNEL_ID) if interaction.guild else None
    if isinstance(staff_logs, discord.TextChannel):
        await staff_logs.send(embed=embed)
    await _color_ops_refresh_panels()
    await interaction.followup.send(f"Application logged for {member.mention}.", ephemeral=True)


@bot.tree.command(name="schedule-interview", description="Connect an interview time to an existing application (staff only)")
@app_commands.describe(member="The applicant", when_text="When the interview is (e.g. 'Friday 8pm ET')", notes="Optional notes")
@app_commands.checks.has_permissions(manage_guild=True)
async def schedule_interview(interaction: discord.Interaction, member: discord.Member, when_text: str, notes: str = "Interview scheduled."):
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return
    state = _color_ops_load()
    app = _color_ops_app_bucket(state, member.id)
    now_str = datetime.now(COLOR_TZ).strftime("%Y-%m-%d %I:%M %p ET")
    if not app.get("submitted_at"):
        app["submitted_at"] = now_str
    app.update({
        "display_name": member.display_name,
        "status": "Interview Scheduled",
        "interview_scheduled_for": when_text,
        "interview_notes": notes,
        "reviewed_by": interaction.user.mention,
    })
    _color_ops_save(state)
    embed = _build_color_ops_application_embed(member, app, "🎤 Interview Scheduled", discord.Color.orange())
    staff_logs = interaction.guild.get_channel(STAFF_LOGS_CHANNEL_ID) if interaction.guild else None
    if isinstance(staff_logs, discord.TextChannel):
        await staff_logs.send(embed=embed)
    await _color_ops_refresh_panels()
    await interaction.followup.send(f"Interview connected to {member.mention}'s application.", ephemeral=True)


@bot.tree.command(name="application-result", description="Set the final result for a member application (staff only)")
@app_commands.describe(member="The applicant", result="approved / denied / pending", notes="Optional notes")
@app_commands.checks.has_permissions(manage_guild=True)
async def application_result(interaction: discord.Interaction, member: discord.Member, result: str, notes: str = "No extra notes provided."):
    normalized = result.strip().lower()
    if normalized not in {"approved", "denied", "pending"}:
        return await interaction.response.send_message(
            "Use one of: `approved`, `denied`, or `pending`.", ephemeral=True
        )
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return
    state = _color_ops_load()
    app = _color_ops_app_bucket(state, member.id)
    now_str = datetime.now(COLOR_TZ).strftime("%Y-%m-%d %I:%M %p ET")
    if not app.get("submitted_at"):
        app["submitted_at"] = now_str
    color_map = {"approved": discord.Color.green(), "denied": discord.Color.red(), "pending": discord.Color.gold()}
    title_map = {"approved": "✅ Application Approved", "denied": "❌ Application Denied", "pending": "⏳ Application Pending"}
    app.update({
        "display_name": member.display_name,
        "status": normalized.title(),
        "result_notes": notes,
        "reviewed_by": interaction.user.mention,
    })
    _color_ops_save(state)
    embed = _build_color_ops_application_embed(member, app, title_map[normalized], color_map[normalized])
    staff_logs = interaction.guild.get_channel(STAFF_LOGS_CHANNEL_ID) if interaction.guild else None
    if isinstance(staff_logs, discord.TextChannel):
        await staff_logs.send(embed=embed)
    await _color_ops_refresh_panels()
    await interaction.followup.send(f"Application result updated for {member.mention}.", ephemeral=True)


# Color submission / winner commands

@bot.tree.command(name="log-color-submission", description="Log a color submission and track contributor stats (staff only)")
@app_commands.describe(contributor="Who submitted the color", color_name="Name of the color", image_url="Optional image URL")
@app_commands.checks.has_permissions(manage_guild=True)
async def log_color_submission(interaction: discord.Interaction, contributor: discord.Member, color_name: str, image_url: str = ""):
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return
    state = _color_ops_load()
    now_str = datetime.now(COLOR_TZ).strftime("%Y-%m-%d %I:%M %p ET")
    entry = {
        "color_name": color_name,
        "contributor_id": contributor.id,
        "contributor_name": contributor.display_name,
        "image_url": image_url or None,
        "submitted_at": now_str,
    }
    state["colors"]["active_entries"].append(entry)
    bucket = _color_ops_contributor_bucket(state, contributor.id)
    bucket["submission_count"] += 1
    bucket["last_submission_at"] = now_str
    bucket["display_name"] = contributor.display_name
    _color_ops_save(state)

    embed = discord.Embed(
        title="🎨 Color Submission Logged",
        description=(
            f"**Color:** {color_name}\n"
            f"**Contributor:** {contributor.mention}\n"
            f"**Logged By:** {interaction.user.mention}"
        ),
        color=discord.Color.purple(),
        timestamp=datetime.utcnow(),
    )
    if image_url:
        embed.set_image(url=image_url)
    embed.set_footer(text="Different Meets • Color Submission Tracker")
    staff_logs = interaction.guild.get_channel(STAFF_LOGS_CHANNEL_ID) if interaction.guild else None
    if isinstance(staff_logs, discord.TextChannel):
        await staff_logs.send(embed=embed)
    await _color_ops_refresh_panels()
    await interaction.followup.send(f"Color submission logged for {contributor.mention}.", ephemeral=True)


@bot.tree.command(name="set-color-winner", description="Set the winning color, update stats, and auto-post the winner announcement (staff only)")
@app_commands.describe(color_name="Winning color name", contributor="Who submitted it", image_url="Optional image URL")
@app_commands.checks.has_permissions(manage_guild=True)
async def set_color_winner(interaction: discord.Interaction, color_name: str, contributor: discord.Member, image_url: str = ""):
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return
    state = _color_ops_load()
    now_str = datetime.now(COLOR_TZ).strftime("%Y-%m-%d %I:%M %p ET")
    winner_entry = {
        "color_name": color_name,
        "contributor_id": contributor.id,
        "contributor_name": contributor.display_name,
        "image_url": image_url or None,
        "won_at": now_str,
    }
    state["colors"]["history"].append(winner_entry)
    bucket = _color_ops_contributor_bucket(state, contributor.id)
    bucket["win_count"] += 1
    bucket["last_win_at"] = now_str
    bucket["display_name"] = contributor.display_name
    state["colors"]["active_entries"] = [
        x for x in state["colors"]["active_entries"]
        if not (x.get("color_name", "").lower() == color_name.lower()
                and x.get("contributor_id") == contributor.id)
    ]
    _color_ops_save(state)

    staff_embed = discord.Embed(
        title="🏆 Winning Color Logged",
        description=(
            f"**Winning Color:** {color_name}\n"
            f"**Contributor:** {contributor.mention}\n"
            f"**Logged By:** {interaction.user.mention}"
        ),
        color=discord.Color.blue(),
        timestamp=datetime.utcnow(),
    )
    if image_url:
        staff_embed.set_image(url=image_url)
    staff_embed.set_footer(text="Different Meets • Winner Tracker")
    staff_logs = interaction.guild.get_channel(STAFF_LOGS_CHANNEL_ID) if interaction.guild else None
    if isinstance(staff_logs, discord.TextChannel):
        await staff_logs.send(embed=staff_embed)

    public_embed = _build_color_ops_winner_embed(color_name, contributor.mention, image_url or None)
    color_notice = interaction.guild.get_channel(COLOR_TEAM_POST_CHANNEL_ID) if interaction.guild else None
    if isinstance(color_notice, discord.TextChannel):
        role = interaction.guild.get_role(COLOR_TEAM_ROLE_ID) if interaction.guild else None
        await color_notice.send(
            content=role.mention if role else None,
            embed=public_embed,
            view=ColorTeamPanelView(),
            allowed_mentions=discord.AllowedMentions(roles=True),
        )

    await _color_ops_refresh_panels()
    await interaction.followup.send(f"Winner set and announced for **{color_name}**.", ephemeral=True)


@bot.tree.command(name="refresh-color-ops-panels", description="Refresh the color stats and contributor leaderboard panels (staff only)")
@app_commands.checks.has_permissions(manage_guild=True)
async def refresh_color_ops_panels(interaction: discord.Interaction):
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return
    await _color_ops_refresh_panels()
    await interaction.followup.send("Color ops panels refreshed.", ephemeral=True)


@bot.tree.command(name="reset-color-ops-panels", description="Reset saved panel IDs and repost clean panels (admin only)")
@app_commands.checks.has_permissions(administrator=True)
async def reset_color_ops_panels(interaction: discord.Interaction):
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return
    state = _color_ops_load()
    state["panel_messages"] = {}
    _color_ops_save(state)
    await _color_ops_refresh_panels()
    await interaction.followup.send("Color ops panel IDs reset and panels reposted cleanly.", ephemeral=True)


# =========================
# RSVP ATTENDANCE SYSTEM
# =========================
ATT_RSVP_CHANNEL_ID = 1485469927312850974
ATT_RSVP_FILE = os.path.join(DATA_FOLDER, "diff_rsvp_meets.json")
ATT_LB_FILE = os.path.join(DATA_FOLDER, "diff_rsvp_leaderboard.json")
ATT_PROMO_FILE = os.path.join(DATA_FOLDER, "diff_rsvp_promotions.json")
ATT_CONTROL_HUB_FILE = os.path.join(DATA_FOLDER, "diff_control_hub_panel.json")

ATT_PROMO_PATH = {
    "Crew Member": "Host",
    "Host": "Manager",
    "Manager": "Co-Leader",
    "Co-Leader": "Leader",
}
ATT_PROMO_THRESHOLDS = {
    "Crew Member": 5,
    "Host": 10,
    "Manager": 18,
    "Co-Leader": 30,
}
ATT_PROMO_RATE_MIN = 60.0


@dataclass
class RsvpMeet:
    meet_id: str
    title: str
    host_id: int
    host_name: str
    meet_date: str
    created_at: str
    channel_id: int
    message_id: Optional[int] = None
    attendees_yes: Optional[Set[int]] = None
    attendees_maybe: Optional[Set[int]] = None
    attendees_no: Optional[Set[int]] = None
    checked_in: Optional[Set[int]] = None
    closed: bool = False

    def __post_init__(self):
        self.attendees_yes = set(self.attendees_yes or [])
        self.attendees_maybe = set(self.attendees_maybe or [])
        self.attendees_no = set(self.attendees_no or [])
        self.checked_in = set(self.checked_in or [])

    def to_dict(self) -> dict:
        d = asdict(self)
        d["attendees_yes"] = list(self.attendees_yes)
        d["attendees_maybe"] = list(self.attendees_maybe)
        d["attendees_no"] = list(self.attendees_no)
        d["checked_in"] = list(self.checked_in)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "RsvpMeet":
        return cls(**d)


_rsvp_meets: Dict[str, RsvpMeet] = {}
_rsvp_leaderboard: dict = {}
_rsvp_promotions: list = []
_rsvp_control_hub: dict = {}


def _rsvp_load_all() -> None:
    global _rsvp_meets, _rsvp_leaderboard, _rsvp_promotions, _rsvp_control_hub
    raw = _load_diff_json(ATT_RSVP_FILE)
    _rsvp_meets = {k: RsvpMeet.from_dict(v) for k, v in raw.items()} if raw else {}
    _rsvp_leaderboard = _load_diff_json(ATT_LB_FILE) or {}
    _rsvp_promotions = _load_diff_json(ATT_PROMO_FILE) or []
    _rsvp_control_hub = _load_diff_json(ATT_CONTROL_HUB_FILE) or {}


def _rsvp_save_all() -> None:
    _save_diff_json(ATT_RSVP_FILE, {k: v.to_dict() for k, v in _rsvp_meets.items()})
    _save_diff_json(ATT_LB_FILE, _rsvp_leaderboard)
    _save_diff_json(ATT_PROMO_FILE, _rsvp_promotions)
    _save_diff_json(ATT_CONTROL_HUB_FILE, _rsvp_control_hub)


def _rsvp_make_id() -> str:
    return datetime.now(timezone.utc).strftime("meet_%Y%m%d_%H%M%S")


def _rsvp_build_embed(meet: RsvpMeet) -> discord.Embed:
    embed = discord.Embed(
        title="📊 DIFF Meet Attendance",
        description="Use the buttons below to update your status for this meet.\n\n━━━━━━━━━━━━━━━━━━━━━━",
        color=discord.Color.blue(),
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name="Meet", value=meet.title, inline=True)
    embed.add_field(name="Host", value=meet.host_name, inline=True)
    embed.add_field(name="Date", value=meet.meet_date, inline=True)
    embed.add_field(name="✅ Pulling Up", value=str(len(meet.attendees_yes)), inline=True)
    embed.add_field(name="❓ Maybe", value=str(len(meet.attendees_maybe)), inline=True)
    embed.add_field(name="❌ Can't Make It", value=str(len(meet.attendees_no)), inline=True)
    embed.add_field(name="✅ Checked In", value=str(len(meet.checked_in)), inline=True)
    embed.add_field(name="Status", value="Closed 🔒" if meet.closed else "Open ✅", inline=True)
    embed.add_field(name="Meet ID", value=f"`{meet.meet_id}`", inline=True)
    embed.set_footer(text="Different Meets • Attendance System")
    return embed


def _rsvp_top_role(member: discord.Member) -> str:
    priority = ["Leader", "Co-Leader", "Manager", "Host", "Crew Member"]
    names = {r.name for r in member.roles}
    for name in priority:
        if name in names:
            return name
    return "Crew Member"


def _rsvp_get_entry(member: discord.Member) -> dict:
    return _rsvp_leaderboard.get(str(member.id), {
        "user_id": member.id,
        "name": member.display_name,
        "attendance_count": 0,
        "hosted_count": 0,
        "current_role": _rsvp_top_role(member),
        "last_attended": None,
        "rsvp_yes": 0,
        "rsvp_maybe": 0,
        "rsvp_no": 0,
        "missed_after_rsvp": 0,
        "promotion_logged_for": [],
    })


def _rsvp_attendance_rate(entry: dict) -> float:
    yes = int(entry.get("rsvp_yes", 0))
    attended = int(entry.get("attendance_count", 0))
    if yes <= 0:
        return 100.0 if attended > 0 else 0.0
    return round((attended / yes) * 100, 1)


async def _rsvp_check_and_post_promotion(guild: discord.Guild, member: discord.Member, entry: dict) -> None:
    current = entry.get("current_role", "Crew Member")
    threshold = ATT_PROMO_THRESHOLDS.get(current)
    next_role = ATT_PROMO_PATH.get(current)
    if not threshold or not next_role:
        return

    attendance_count = int(entry.get("attendance_count", 0))
    rate = _rsvp_attendance_rate(entry)
    if attendance_count < threshold or rate < ATT_PROMO_RATE_MIN:
        return

    promoted_for: list = entry.setdefault("promotion_logged_for", [])
    if next_role in promoted_for:
        return

    suggestion = {
        "user_id": member.id,
        "name": member.display_name,
        "current_role": current,
        "suggested_role": next_role,
        "attendance_count": attendance_count,
        "hosted_count": int(entry.get("hosted_count", 0)),
        "attendance_rate": rate,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _rsvp_promotions.append(suggestion)
    promoted_for.append(next_role)
    entry["promotion_logged_for"] = promoted_for

    ch = guild.get_channel(STAFF_LOGS_CHANNEL_ID)
    if isinstance(ch, discord.TextChannel):
        promo_embed = discord.Embed(
            title="📈 Promotion Suggestion",
            description="This member hit the auto-promotion threshold.",
            color=discord.Color.purple(),
            timestamp=datetime.now(timezone.utc),
        )
        promo_embed.add_field(name="User", value=f"<@{member.id}>", inline=True)
        promo_embed.add_field(name="Current Role", value=current, inline=True)
        promo_embed.add_field(name="Suggested Role", value=next_role, inline=True)
        promo_embed.add_field(name="✅ Meets Attended", value=str(attendance_count), inline=True)
        promo_embed.add_field(name="🎤 Meets Hosted", value=str(suggestion["hosted_count"]), inline=True)
        promo_embed.add_field(name="📊 Attendance Rate", value=f"{rate}%", inline=True)
        promo_embed.set_footer(text="Review manually before changing roles.")
        try:
            await ch.send(embed=promo_embed)
        except Exception:
            pass


def _rsvp_update_stats(guild: discord.Guild, user_id: int) -> None:
    member = guild.get_member(user_id)
    if not member:
        return
    entry = _rsvp_get_entry(member)
    entry["name"] = member.display_name
    entry["attendance_count"] = int(entry.get("attendance_count", 0)) + 1
    entry["current_role"] = _rsvp_top_role(member)
    entry["last_attended"] = datetime.now(timezone.utc).isoformat()
    _rsvp_leaderboard[str(user_id)] = entry


def _rsvp_increment_host(guild: discord.Guild, host_id: int) -> None:
    member = guild.get_member(host_id)
    if not member:
        return
    entry = _rsvp_get_entry(member)
    entry["name"] = member.display_name
    entry["current_role"] = _rsvp_top_role(member)
    entry["hosted_count"] = int(entry.get("hosted_count", 0)) + 1
    _rsvp_leaderboard[str(host_id)] = entry


async def _rsvp_update_rsvp_stats(guild: discord.Guild, meet: RsvpMeet) -> None:
    all_ids = set(meet.attendees_yes) | set(meet.attendees_maybe) | set(meet.attendees_no) | set(meet.checked_in)
    for user_id in all_ids:
        member = guild.get_member(user_id)
        if not member:
            continue
        entry = _rsvp_get_entry(member)
        entry["name"] = member.display_name
        entry["current_role"] = _rsvp_top_role(member)
        if user_id in meet.attendees_yes:
            entry["rsvp_yes"] = int(entry.get("rsvp_yes", 0)) + 1
            if user_id not in meet.checked_in:
                entry["missed_after_rsvp"] = int(entry.get("missed_after_rsvp", 0)) + 1
        elif user_id in meet.attendees_maybe:
            entry["rsvp_maybe"] = int(entry.get("rsvp_maybe", 0)) + 1
        elif user_id in meet.attendees_no:
            entry["rsvp_no"] = int(entry.get("rsvp_no", 0)) + 1
        _rsvp_leaderboard[str(user_id)] = entry
    _rsvp_save_all()


async def _rsvp_evaluate_promotions(guild: discord.Guild, meet: RsvpMeet) -> None:
    user_ids = set(meet.checked_in)
    user_ids.add(meet.host_id)
    for user_id in user_ids:
        member = guild.get_member(user_id)
        if not member:
            continue
        entry = _rsvp_leaderboard.get(str(user_id))
        if not entry:
            continue
        await _rsvp_check_and_post_promotion(guild, member, entry)
    _rsvp_save_all()


async def _rsvp_refresh_message(meet: RsvpMeet) -> None:
    ch = bot.get_channel(meet.channel_id)
    if not isinstance(ch, discord.TextChannel) or not meet.message_id:
        return
    try:
        msg = await ch.fetch_message(meet.message_id)
        view = None if meet.closed else AttendanceRsvpView(meet.meet_id)
        await msg.edit(embed=_rsvp_build_embed(meet), view=view)
    except (discord.NotFound, discord.HTTPException):
        pass


class AttendanceRsvpView(discord.ui.View):
    def __init__(self, meet_id: str):
        super().__init__(timeout=None)
        self.meet_id = meet_id

    @discord.ui.button(label="Pulling Up", emoji="✅", style=discord.ButtonStyle.success, custom_id="rsvp_btn_yes")
    async def pulling_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "yes")

    @discord.ui.button(label="Maybe", emoji="❓", style=discord.ButtonStyle.secondary, custom_id="rsvp_btn_maybe")
    async def maybe(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "maybe")

    @discord.ui.button(label="Can't Make It", emoji="❌", style=discord.ButtonStyle.danger, custom_id="rsvp_btn_no")
    async def cant_make_it(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "no")

    async def _handle(self, interaction: discord.Interaction, status: str) -> None:
        meet = _rsvp_meets.get(self.meet_id)
        if not meet:
            return await interaction.response.send_message("Meet record not found.", ephemeral=True)
        if meet.closed:
            return await interaction.response.send_message("This attendance panel is already closed.", ephemeral=True)
        uid = interaction.user.id
        meet.attendees_yes.discard(uid)
        meet.attendees_maybe.discard(uid)
        meet.attendees_no.discard(uid)
        if status == "yes":
            meet.attendees_yes.add(uid)
            msg = "You are marked as **Pulling Up** ✅"
        elif status == "maybe":
            meet.attendees_maybe.add(uid)
            msg = "You are marked as **Maybe** ❓"
        else:
            meet.attendees_no.add(uid)
            msg = "You are marked as **Can't Make It** ❌"
        _rsvp_save_all()
        await _rsvp_refresh_message(meet)
        await interaction.response.send_message(msg, ephemeral=True)


def _rsvp_get_latest_meet() -> Optional[RsvpMeet]:
    if not _rsvp_meets:
        return None
    return sorted(_rsvp_meets.values(), key=lambda m: m.created_at, reverse=True)[0]


def _rsvp_build_leaderboard_embed() -> discord.Embed:
    if not _rsvp_leaderboard:
        return discord.Embed(
            title="🏆 DIFF Attendance Leaderboard",
            description="No attendance data tracked yet.",
            color=discord.Color.gold(),
            timestamp=datetime.now(timezone.utc),
        )
    top = sorted(
        _rsvp_leaderboard.values(),
        key=lambda x: (int(x.get("attendance_count", 0)), int(x.get("hosted_count", 0))),
        reverse=True,
    )[:10]
    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for idx, entry in enumerate(top, start=1):
        prefix = medals[idx - 1] if idx <= 3 else f"{idx}."
        lines.append(
            f"{prefix} <@{entry['user_id']}> — **{entry.get('attendance_count', 0)}** attended | "
            f"**{entry.get('hosted_count', 0)}** hosted"
        )
    embed = discord.Embed(
        title="🏆 DIFF Attendance Leaderboard",
        description="\n".join(lines),
        color=discord.Color.gold(),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Attendance is tracked from check-ins, not just button votes.")
    return embed


def _rsvp_build_promotions_embed() -> Optional[discord.Embed]:
    if not _rsvp_promotions:
        return None
    lines = []
    for item in _rsvp_promotions[-10:][::-1]:
        lines.append(
            f"📈 <@{item['user_id']}> — {item['current_role']} → **{item['suggested_role']}** "
            f"| {item.get('attendance_count', 0)} attended | {item.get('hosted_count', 0)} hosted"
        )
    embed = discord.Embed(
        title="📈 Promotion Suggestions",
        description="\n".join(lines),
        color=discord.Color.purple(),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Auto suggestions are also logged in the staff channel.")
    return embed


def _rsvp_build_control_hub_embed() -> discord.Embed:
    latest = _rsvp_get_latest_meet()
    if latest:
        latest_value = f"**{latest.title}**\nHost: {latest.host_name}\nDate: {latest.meet_date}"
    else:
        latest_value = "No meet panel created yet."
    embed = discord.Embed(
        title="📌 DIFF Crew Control Hub",
        description=(
            "*The all-in-one crew hub for Different Meets.*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📊 **Attendance & Activity**\n"
            "Use the buttons below to check your personal stats, open the leaderboard, "
            "and quickly view your latest meet panel.\n\n"
            "🎯 **What This Hub Controls**\n"
            "• Attendance tracking\n"
            "• My Stats\n"
            "• Leaderboard\n"
            "• Promotion suggestions for staff\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=discord.Color.blue(),
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name="Attendance Channel", value=f"<#{ATT_RSVP_CHANNEL_ID}>", inline=True)
    embed.add_field(name="Promotion Logs", value=f"<#{STAFF_LOGS_CHANNEL_ID}>", inline=True)
    embed.add_field(name="Latest Meet", value=latest_value, inline=False)
    embed.set_footer(text="Different Meets • Control Hub")
    return embed


async def _rsvp_post_or_refresh_control_hub(channel: discord.TextChannel) -> discord.Message:
    global _rsvp_control_hub
    existing_channel_id = _rsvp_control_hub.get("channel_id")
    existing_message_id = _rsvp_control_hub.get("message_id")
    embed = _rsvp_build_control_hub_embed()
    view = ControlHubView()

    if existing_channel_id and existing_message_id:
        old_ch = bot.get_channel(int(existing_channel_id))
        if isinstance(old_ch, discord.TextChannel):
            try:
                old_msg = await old_ch.fetch_message(int(existing_message_id))
                if old_ch.id != channel.id:
                    try:
                        await old_msg.delete()
                    except discord.HTTPException:
                        pass
                else:
                    await old_msg.edit(embed=embed, view=view)
                    _rsvp_control_hub = {"channel_id": channel.id, "message_id": old_msg.id}
                    _rsvp_save_all()
                    return old_msg
            except (discord.NotFound, discord.HTTPException):
                pass

    msg = await channel.send(embed=embed, view=view)
    _rsvp_control_hub = {"channel_id": channel.id, "message_id": msg.id}
    _rsvp_save_all()
    return msg


class ControlHubView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="My Stats", emoji="📊", style=discord.ButtonStyle.primary, custom_id="control_hub_my_stats")
    async def my_stats_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("This button only works inside the server.", ephemeral=True)
            return
        entry = _rsvp_leaderboard.get(str(interaction.user.id), {
            "user_id": interaction.user.id,
            "name": interaction.user.display_name,
            "attendance_count": 0,
            "hosted_count": 0,
            "current_role": _rsvp_top_role(interaction.user),
            "last_attended": None,
            "rsvp_yes": 0,
            "rsvp_maybe": 0,
            "rsvp_no": 0,
            "missed_after_rsvp": 0,
        })
        rate = _rsvp_attendance_rate(entry)
        sorted_entries = sorted(
            _rsvp_leaderboard.values(),
            key=lambda x: (int(x.get("attendance_count", 0)), int(x.get("hosted_count", 0))),
            reverse=True,
        )
        rank = next((i for i, e in enumerate(sorted_entries, 1) if int(e.get("user_id", 0)) == interaction.user.id), None)
        embed = discord.Embed(
            title="📈 My DIFF Stats",
            description=f"Stats for {interaction.user.mention}",
            color=discord.Color.blurple(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="Current Role", value=entry.get("current_role", "Crew Member"), inline=True)
        embed.add_field(name="Attendance Rank", value=f"#{rank}" if rank else "Unranked", inline=True)
        embed.add_field(name="📊 Attendance Rate", value=f"{rate}%", inline=True)
        embed.add_field(name="✅ Meets Attended", value=str(int(entry.get("attendance_count", 0))), inline=True)
        embed.add_field(name="🎤 Meets Hosted", value=str(int(entry.get("hosted_count", 0))), inline=True)
        embed.add_field(name="✅ RSVP Pulling Up", value=str(int(entry.get("rsvp_yes", 0))), inline=True)
        embed.add_field(name="❓ RSVP Maybe", value=str(int(entry.get("rsvp_maybe", 0))), inline=True)
        embed.add_field(name="❌ RSVP Can't Make It", value=str(int(entry.get("rsvp_no", 0))), inline=True)
        embed.add_field(name="⚠️ No-Shows After RSVP", value=str(int(entry.get("missed_after_rsvp", 0))), inline=True)
        last = entry.get("last_attended")
        embed.set_footer(text=f"Last attended: {last[:10] if last else 'No check-ins yet'}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Leaderboard", emoji="🏆", style=discord.ButtonStyle.success, custom_id="control_hub_leaderboard")
    async def leaderboard_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = _rsvp_build_leaderboard_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Latest Meet", emoji="📅", style=discord.ButtonStyle.secondary, custom_id="control_hub_latest_meet")
    async def latest_meet_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        meet = _rsvp_get_latest_meet()
        if not meet:
            await interaction.response.send_message("No attendance panels have been created yet.", ephemeral=True)
            return
        embed = _rsvp_build_embed(meet)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Promotion Suggestions", emoji="📈", style=discord.ButtonStyle.secondary, custom_id="control_hub_promotions")
    async def promotions_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
            await interaction.response.send_message("Only DIFF staff can view promotion suggestions.", ephemeral=True)
            return
        embed = _rsvp_build_promotions_embed()
        if embed is None:
            await interaction.response.send_message("No promotion suggestions yet.", ephemeral=True)
            return
        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="attendance-create", description="Create a live RSVP attendance panel for a meet (staff only)")
@app_commands.describe(meet_title="Meet name", host="Host for the meet", meet_date="Date shown on the panel")
async def attendance_create(interaction: discord.Interaction, meet_title: str, host: discord.Member, meet_date: str):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    ch = bot.get_channel(ATT_RSVP_CHANNEL_ID)
    if not isinstance(ch, discord.TextChannel):
        ch = await bot.fetch_channel(ATT_RSVP_CHANNEL_ID)
    meet_id = _rsvp_make_id()
    meet = RsvpMeet(
        meet_id=meet_id, title=meet_title,
        host_id=host.id, host_name=host.mention,
        meet_date=meet_date, created_at=datetime.now(timezone.utc).isoformat(),
        channel_id=ch.id,
    )
    _rsvp_meets[meet_id] = meet
    if interaction.guild:
        _rsvp_increment_host(interaction.guild, host.id)
    view = AttendanceRsvpView(meet_id)
    msg = await ch.send(embed=_rsvp_build_embed(meet), view=view)
    meet.message_id = msg.id
    bot.add_view(view, message_id=msg.id)
    _rsvp_save_all()
    await interaction.response.send_message(
        f"RSVP panel created in {ch.mention} for **{meet_title}**.\nMeet ID: `{meet_id}`", ephemeral=True,
    )


@bot.tree.command(name="attendance-checkin", description="Mark a member as actually present at the meet (staff only)")
@app_commands.describe(meet_id="Meet ID from the attendance panel", member="Member to check in")
async def attendance_checkin(interaction: discord.Interaction, meet_id: str, member: discord.Member):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    meet = _rsvp_meets.get(meet_id)
    if not meet:
        return await interaction.response.send_message("Meet ID not found.", ephemeral=True)
    if member.id in meet.checked_in:
        return await interaction.response.send_message(f"{member.mention} is already checked in.", ephemeral=True)
    meet.checked_in.add(member.id)
    if interaction.guild:
        _rsvp_update_stats(interaction.guild, member.id)
    _rsvp_save_all()
    await _rsvp_refresh_message(meet)
    entry = _rsvp_leaderboard.get(str(member.id), {})
    await interaction.response.send_message(
        f"Checked in {member.mention} for **{meet.title}**. Total check-ins: {entry.get('attendance_count', 1)}", ephemeral=True,
    )


@bot.tree.command(name="attendance-close", description="Close a meet RSVP panel and post final results (staff only)")
@app_commands.describe(meet_id="Meet ID from the attendance panel", total_players="Total players in lobby")
async def attendance_close(interaction: discord.Interaction, meet_id: str, total_players: int):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    meet = _rsvp_meets.get(meet_id)
    if not meet:
        return await interaction.response.send_message("Meet ID not found.", ephemeral=True)
    if meet.closed:
        return await interaction.response.send_message("That meet is already closed.", ephemeral=True)
    meet.closed = True
    _rsvp_save_all()
    await _rsvp_refresh_message(meet)
    if interaction.guild:
        await _rsvp_update_rsvp_stats(interaction.guild, meet)
        await _rsvp_evaluate_promotions(interaction.guild, meet)
    ch = bot.get_channel(meet.channel_id)
    if isinstance(ch, discord.TextChannel):
        no_shows = max(0, len(meet.attendees_yes) - len(meet.checked_in))
        result_embed = discord.Embed(
            title="📊 DIFF Meet Results",
            description="Final attendance results for this meet.",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc),
        )
        result_embed.add_field(name="Meet", value=meet.title, inline=True)
        result_embed.add_field(name="Host", value=meet.host_name, inline=True)
        result_embed.add_field(name="Lobby Size", value=str(total_players), inline=True)
        result_embed.add_field(name="✅ Checked In", value=str(len(meet.checked_in)), inline=True)
        result_embed.add_field(name="❌ No Shows", value=str(no_shows), inline=True)
        result_embed.add_field(name="❓ Maybe", value=str(len(meet.attendees_maybe)), inline=True)
        result_embed.set_footer(text="Attach your lobby screenshot below this post.")
        await ch.send(embed=result_embed)
    await interaction.response.send_message(
        f"Attendance closed for **{meet.title}** and final results posted.", ephemeral=True,
    )


@bot.tree.command(name="attendance-leaderboard", description="Show the most active DIFF members by meet attendance")
async def attendance_leaderboard(interaction: discord.Interaction):
    if not _rsvp_leaderboard:
        return await interaction.response.send_message("No attendance data yet.", ephemeral=True)
    top = sorted(
        _rsvp_leaderboard.values(),
        key=lambda x: (int(x.get("attendance_count", 0)), int(x.get("hosted_count", 0))),
        reverse=True,
    )[:10]
    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for idx, entry in enumerate(top, start=1):
        prefix = medals[idx - 1] if idx <= 3 else f"{idx}."
        lines.append(
            f"{prefix} <@{entry['user_id']}> — **{entry.get('attendance_count', 0)}** attended | "
            f"**{entry.get('hosted_count', 0)}** hosted"
        )
    embed = discord.Embed(
        title="🏆 DIFF Attendance Leaderboard",
        description="\n".join(lines),
        color=discord.Color.gold(),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Attendance is tracked from check-ins, not RSVP votes.")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="post-crew-hub", description="Post or refresh the DIFF Crew Hub stats panel (staff only)")
async def post_crew_hub(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    if not isinstance(interaction.channel, discord.TextChannel):
        return await interaction.response.send_message("Use this in a text channel.", ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    embed = _build_crew_hub_embed()
    state = _load_diff_json(CREW_HUB_STATE_FILE) or {}
    msg_id = state.get("message_id")
    ch_id = state.get("channel_id")
    existing_msg = None
    if msg_id and ch_id and interaction.guild:
        ch = interaction.guild.get_channel(ch_id)
        if isinstance(ch, discord.TextChannel):
            try:
                existing_msg = await ch.fetch_message(msg_id)
            except discord.NotFound:
                existing_msg = None
    if existing_msg:
        await existing_msg.edit(embed=embed, view=CrewHubView())
        await interaction.followup.send("Crew Hub panel refreshed.", ephemeral=True)
    else:
        msg = await interaction.channel.send(embed=embed, view=CrewHubView())
        _save_diff_json(CREW_HUB_STATE_FILE, {"message_id": msg.id, "channel_id": interaction.channel.id})
        await interaction.followup.send("Crew Hub panel posted and linked for auto-refresh.", ephemeral=True)


@bot.tree.command(name="post-notify-panel", description="Post the meet notification opt-in panel in this channel (staff only)")
async def post_notify_panel(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    if not isinstance(interaction.channel, discord.TextChannel):
        return await interaction.response.send_message("Use this in a text channel.", ephemeral=True)
    embed = discord.Embed(
        title="🔔 DIFF Meet Notifications",
        description="\n".join([
            "Want to be pinged when meets are announced?",
            "",
            "Press the button below to **toggle your notification role on or off**.",
            "You can switch it at any time.",
        ]),
        color=discord.Color.blurple(),
    )
    embed.set_footer(text="Different Meets • Notification Panel")
    await interaction.channel.send(embed=embed, view=NotifyMeetView())
    await interaction.response.send_message("✅ Notification panel posted.", ephemeral=True)


@bot.tree.command(name="post-staff-dashboard", description="Post/refresh the staff dashboard and run crew invite check (staff only)")
async def post_staff_dashboard(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    await _upsert_staff_dashboard(bot)
    await run_crew_invite_automation()
    await interaction.followup.send("✅ Staff dashboard refreshed and crew invite check complete.", ephemeral=True)


@bot.tree.command(name="suggestions", description="Show DIFF promotion and activity suggestions (staff only)")
async def suggestions(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    embed = _ft_build_suggestions_embed(interaction.guild)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="meetrecap", description="Post a DIFF meet recap and update host stats (staff only)")
@app_commands.describe(
    host="Meet host",
    meet="Meet name or theme",
    attendance="Total attendance number",
    top1="Top member 1 (optional)",
    top2="Top member 2 (optional)",
    top3="Top member 3 (optional)",
    screenshot="Optional screenshot attachment",
)
async def meetrecap(
    interaction: discord.Interaction,
    host: discord.Member,
    meet: str,
    attendance: int,
    top1: Optional[discord.Member] = None,
    top2: Optional[discord.Member] = None,
    top3: Optional[discord.Member] = None,
    screenshot: Optional[discord.Attachment] = None,
):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    await interaction.response.defer(ephemeral=True)

    data = _ft_ensure_user(host.id)
    ft_user = _ft_get_user(data, host.id)
    hosts_section = data.setdefault("hosts", {})
    host_entry = hosts_section.setdefault(str(host.id), {"hostedMeets": 0, "hostAttendanceTotal": 0})
    host_entry["hostedMeets"] = int(host_entry.get("hostedMeets", 0)) + 1
    host_entry["hostAttendanceTotal"] = int(host_entry.get("hostAttendanceTotal", 0)) + attendance
    ft_user["hostedMeets"] = int(ft_user.get("hostedMeets", 0)) + 1
    ft_user["hostAttendanceTotal"] = int(ft_user.get("hostAttendanceTotal", 0)) + attendance
    data.setdefault("recaps", []).append({
        "hostId": host.id,
        "meet": meet,
        "attendance": attendance,
        "timestamp": utc_now().isoformat(),
    })
    _ft_save(data)

    top_members = [m.mention for m in [top1, top2, top3] if m is not None]
    embed = discord.Embed(
        title="🎬 DIFF Meet Recap",
        description="\n".join([
            f"**Meet:** {meet}",
            f"**Host:** {host.mention}",
            f"**Attendance:** {attendance}",
            "",
            "**Top Members**",
            *(top_members or ["None provided"]),
            "",
            "Built through consistency, structure, and clean meets.",
        ]),
        color=discord.Color.dark_gray(),
        timestamp=utc_now(),
    )
    embed.set_footer(text="Different Meets • Meet Recap")

    files = []
    if screenshot:
        try:
            files.append(await screenshot.to_file())
            embed.set_image(url=f"attachment://{screenshot.filename}")
        except Exception:
            pass

    recap_channel = interaction.guild.get_channel(RECAP_CHANNEL_ID) if RECAP_CHANNEL_ID else None
    if isinstance(recap_channel, discord.TextChannel):
        await recap_channel.send(embed=embed, files=files)
    else:
        await interaction.channel.send(embed=embed, files=files)

    log_ch = interaction.guild.get_channel(STAFF_LOGS_CHANNEL_ID)
    if isinstance(log_ch, discord.TextChannel):
        try:
            await log_ch.send(embed=discord.Embed(
                title="🎬 Meet Recap Logged",
                description=f"**Host:** {host.mention} | **Meet:** {meet} | **Attendance:** {attendance}",
                color=discord.Color.dark_gray(),
                timestamp=utc_now(),
            ))
        except Exception:
            pass

    await _ft_refresh_progression(host)
    await interaction.followup.send("✅ Meet recap posted and host stats updated.", ephemeral=True)


@bot.tree.command(name="behavior", description="Set a member's behavior score and update their tier rank (staff only)")
@app_commands.describe(
    user="Target member",
    score="Behavior score 1–10 (10 = perfect)",
    note="Optional staff note",
)
async def behavior(
    interaction: discord.Interaction,
    user: discord.Member,
    score: app_commands.Range[int, 1, 10],
    note: Optional[str] = None,
):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)

    data = _ft_ensure_user(user.id)
    ft_user = _ft_get_user(data, user.id)
    ft_user["behaviorScore"] = score
    if note:
        ft_user.setdefault("notes", []).append({
            "note": note,
            "by": interaction.user.id,
            "at": utc_now().isoformat(),
        })
    _ft_save(data)

    rank, lb_ok, crew_ok = await _ft_refresh_progression(user)

    embed = discord.Embed(
        title="🧾 Behavior Score Updated",
        description="\n".join([
            f"**User:** {user.mention}",
            f"**Behavior Score:** {score}/10",
            f"**Tier Rank:** {rank}",
            f"**Leaderboard Eligible:** {'Yes' if lb_ok else 'No'}",
            f"**Crew Invite Eligible:** {'Yes' if crew_ok else 'No'}",
            f"**Note:** {note or 'None'}",
        ]),
        color=discord.Color.orange(),
        timestamp=utc_now(),
    )
    log_ch = interaction.guild.get_channel(STAFF_LOGS_CHANNEL_ID) if interaction.guild else None
    if isinstance(log_ch, discord.TextChannel):
        try:
            await log_ch.send(embed=embed)
        except Exception:
            pass
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="my-stats", description="View your DIFF meet attendance and activity stats")
@app_commands.describe(member="Optional: check another member's stats (staff only)")
async def my_stats(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    if member and member != interaction.user:
        if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
            return await interaction.response.send_message("You can only view your own stats.", ephemeral=True)
    target = member or interaction.user
    if not isinstance(target, discord.Member):
        return await interaction.response.send_message("Member not found.", ephemeral=True)

    entry = _rsvp_leaderboard.get(str(target.id), {
        "user_id": target.id,
        "name": target.display_name,
        "attendance_count": 0,
        "hosted_count": 0,
        "current_role": _rsvp_top_role(target),
        "last_attended": None,
        "rsvp_yes": 0,
        "rsvp_maybe": 0,
        "rsvp_no": 0,
        "missed_after_rsvp": 0,
    })
    attendance_count = int(entry.get("attendance_count", 0))
    hosted_count = int(entry.get("hosted_count", 0))
    rsvp_yes = int(entry.get("rsvp_yes", 0))
    rsvp_maybe = int(entry.get("rsvp_maybe", 0))
    rsvp_no = int(entry.get("rsvp_no", 0))
    missed = int(entry.get("missed_after_rsvp", 0))
    rate = _rsvp_attendance_rate(entry)

    sorted_entries = sorted(
        _rsvp_leaderboard.values(),
        key=lambda x: (int(x.get("attendance_count", 0)), int(x.get("hosted_count", 0))),
        reverse=True,
    )
    rank = next((i for i, e in enumerate(sorted_entries, 1) if int(e.get("user_id", 0)) == target.id), None)

    embed = discord.Embed(
        title="📈 My DIFF Stats",
        description=f"Stats for {target.mention}",
        color=discord.Color.blurple(),
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name="Current Role", value=entry.get("current_role", "Crew Member"), inline=True)
    embed.add_field(name="Attendance Rank", value=f"#{rank}" if rank else "Unranked", inline=True)
    embed.add_field(name="📊 Attendance Rate", value=f"{rate}%", inline=True)
    embed.add_field(name="✅ Meets Attended", value=str(attendance_count), inline=True)
    embed.add_field(name="🎤 Meets Hosted", value=str(hosted_count), inline=True)
    embed.add_field(name="✅ RSVP Pulling Up", value=str(rsvp_yes), inline=True)
    embed.add_field(name="❓ RSVP Maybe", value=str(rsvp_maybe), inline=True)
    embed.add_field(name="❌ RSVP Can't Make It", value=str(rsvp_no), inline=True)
    embed.add_field(name="⚠️ No-Shows After RSVP", value=str(missed), inline=True)
    ft_data = _ft_ensure_user(target.id)
    ft_user = _ft_get_user(ft_data, target.id)
    behavior_score = int(ft_user.get("behaviorScore", 10) or 10)
    ft_rank = ft_user.get("rank", "Member")
    hosted_meets = int(ft_user.get("hostedMeets", 0) or 0)
    strikes = _ft_get_strike_count(target)
    warnings = _ft_get_warning_count(target)

    embed.add_field(name="🎯 Tier Rank", value=ft_rank, inline=True)
    embed.add_field(name="🎤 Recapped Meets Hosted", value=str(hosted_meets), inline=True)
    embed.add_field(name="🧾 Behavior Score", value=f"{behavior_score}/10", inline=True)
    embed.add_field(name="⚠️ Strikes", value=str(strikes), inline=True)
    embed.add_field(name="⚠️ Warnings", value=str(warnings), inline=True)

    last = entry.get("last_attended")
    embed.set_footer(text=f"Last attended: {last[:10] if last else 'No check-ins yet'}")
    await interaction.response.send_message(embed=embed, ephemeral=member is None)


@bot.tree.command(name="clear-history", description="Clear message history in this channel (Leadership only)")
@app_commands.describe(amount="Number of messages to delete (1–1000, default 100). Use 0 to delete ALL messages.")
async def clear_history(interaction: discord.Interaction, amount: int = 100):
    _leadership_ids = {LEADER_ROLE_ID, CO_LEADER_ROLE_ID}
    if not isinstance(interaction.user, discord.Member) or not any(r.id in _leadership_ids for r in interaction.user.roles):
        return await interaction.response.send_message("Only Leader or Co-Leader can use this command.", ephemeral=True)
    if not isinstance(interaction.channel, discord.TextChannel):
        return await interaction.response.send_message("This command can only be used in a text channel.", ephemeral=True)
    if amount < 0 or amount > 1000:
        return await interaction.response.send_message("Amount must be between 0 and 1000.", ephemeral=True)

    await interaction.response.defer(ephemeral=True)

    limit = amount if amount > 0 else None
    try:
        deleted = await interaction.channel.purge(limit=limit, reason=f"Channel history cleared by {interaction.user}")
    except discord.Forbidden:
        return await interaction.followup.send("I don't have permission to delete messages in this channel.", ephemeral=True)
    except discord.HTTPException as e:
        return await interaction.followup.send(f"Failed to clear messages: {e}", ephemeral=True)

    logs_ch = interaction.guild.get_channel(STAFF_LOGS_CHANNEL_ID)
    if isinstance(logs_ch, discord.TextChannel):
        log_embed = discord.Embed(
            title="🗑️ Channel History Cleared",
            color=discord.Color.orange(),
            timestamp=utc_now(),
        )
        log_embed.add_field(name="Channel", value=interaction.channel.mention, inline=True)
        log_embed.add_field(name="Cleared By", value=interaction.user.mention, inline=True)
        log_embed.add_field(name="Messages Deleted", value=str(len(deleted)), inline=True)
        log_embed.set_footer(text="Different Meets • Leadership Action")
        try:
            await logs_ch.send(embed=log_embed)
        except discord.HTTPException:
            pass

    await interaction.followup.send(f"✅ Deleted **{len(deleted)}** message(s).", ephemeral=True)


@bot.tree.command(name="control-hub-post", description="Post or refresh the DIFF Crew Control Hub panel (staff only)")
async def control_hub_post(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    if not isinstance(interaction.channel, discord.TextChannel):
        return await interaction.response.send_message("Run this inside a server text channel.", ephemeral=True)
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return
    try:
        await _rsvp_post_or_refresh_control_hub(interaction.channel)
        await interaction.followup.send(f"Control hub posted in {interaction.channel.mention}.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Error: {e}", ephemeral=True)


# =========================
# DIFF SUPPORT CENTER — DROPDOWN TICKET SYSTEM (V2)
# =========================

SUPPORT_PANEL_CHANNEL_ID = SUPPORT_TICKETS_CHANNEL_ID
SUPPORT_TICKET_CATEGORY_ID: int = 1328457973583839282
JOIN_PANEL_CHANNEL_ID = 1277084633858576406
JOIN_TICKET_CATEGORY_ID = 1328457973583839282
_SUPPORT_BRAND = "DIFF Support Center"
_SUPP_APPROVED_STAFF_ROLE_ID = HOST_ROLE_ID

_SUPP_APPLICATION_QUESTIONS = [
    "What DIFF staff role are you applying for?",
    "How long have you been in DIFF?",
    "Why do you want to join the staff team?",
    "What makes you a strong fit for DIFF staff?",
    "How active are you in the server and at meets?",
    "How would you handle disrespect, trolling, or meet disruption?",
    "What days / times are you usually available?",
]


def _supp_clean_name(value: str) -> str:
    import re as _re
    value = value.lower().strip()
    value = _re.sub(r"[^a-z0-9]+", "-", value)
    value = _re.sub(r"-{2,}", "-", value).strip("-")
    return value or "user"


def _supp_role_mention(role_id: int | None) -> str:
    return f"<@&{role_id}>" if role_id else ""


def _supp_parse_topic(topic: str | None, key: str) -> str | None:
    if not topic:
        return None
    import re as _re
    m = _re.search(rf"{_re.escape(key)}=([^|]+)", topic)
    return m.group(1).strip() if m else None


from dataclasses import dataclass as _dataclass

@_dataclass(frozen=True)
class _TicketType:
    key: str
    label: str
    emoji: str
    description: str
    title: str
    long_description: str
    ping_role_id: int | None

    @property
    def channel_prefix(self) -> str:
        return self.key


_TICKET_TYPES: dict[str, _TicketType] = {
    "report": _TicketType(
        key="report",
        label="🛡️ Report",
        emoji="🛡️",
        description="Report behavior issues, trolling, griefing, or rule breaking.",
        title="Report Ticket",
        long_description=(
            "Report a DIFF member, meet attender, or any issue involving behavior, "
            "rule breaking, disrespect, trolling, or meet disruption.\n\n"
            "**Use this if you need to notify staff about:**\n"
            "• Rule violations\n"
            "• Toxic behavior\n"
            "• Disrespect toward members or hosts\n"
            "• Griefing, trolling, or disruption at meets\n"
            "• Any situation that needs staff review"
        ),
        ping_role_id=MANAGER_ROLE_ID,
    ),
    "appeal": _TicketType(
        key="appeal",
        label="⚠️ Appeal",
        emoji="⚠️",
        description="Appeal a ban, strike, warning, or other staff action.",
        title="Appeal Ticket",
        long_description=(
            "Submit an appeal for a ban, strike, warning, or other staff action taken "
            "against your account.\n\n"
            "**Use this if you believe:**\n"
            "• A punishment was unfair\n"
            "• You want a second review\n"
            "• You are ready to take accountability and request another chance\n\n"
            "Please make sure your appeal is honest, respectful, and detailed."
        ),
        ping_role_id=LEADER_ROLE_ID,
    ),
    "support": _TicketType(
        key="support",
        label="🚗 Support",
        emoji="🚗",
        description="Get help with questions, rules, roles, channels, or DIFF systems.",
        title="Support Ticket",
        long_description=(
            "Get help with general server questions, meet information, crew systems, "
            "channels, roles, or other DIFF-related support.\n\n"
            "**Use this for:**\n"
            "• General questions about the server\n"
            "• Help understanding meet rules or requirements\n"
            "• Assistance with channels, roles, or permissions\n"
            "• Questions about schedules, crew activities, or DIFF systems"
        ),
        ping_role_id=HOST_ROLE_ID,
    ),
    "apply": _TicketType(
        key="apply",
        label="📩 Apply",
        emoji="📩",
        description="Apply for a DIFF staff position.",
        title="Staff Application Ticket",
        long_description=(
            "Apply for a DIFF staff position and show your interest in helping the crew "
            "grow and improve.\n\n"
            "**Use this if you want to:**\n"
            "• Join the staff team\n"
            "• Take on more responsibility in DIFF\n"
            "• Help with hosting, management, support, or community growth\n\n"
            "Please only apply if you are active, mature, professional, and ready to "
            "contribute consistently."
        ),
        ping_role_id=CO_LEADER_ROLE_ID,
    ),
}


def _supp_brand_embed(embed: discord.Embed) -> discord.Embed:
    if DIFF_LOGO_URL:
        embed.set_thumbnail(url=DIFF_LOGO_URL)
    if DIFF_BANNER_URL:
        embed.set_image(url=DIFF_BANNER_URL)
    embed.set_footer(text="Different Meets • Support System")
    return embed


def _supp_build_panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title=_SUPPORT_BRAND,
        description=(
            "Need help with something in the server or during a meet? Use the dropdown "
            "below to contact the right staff team.\n\n"
            "Whether you have a concern, need assistance, want to appeal a punishment, "
            "or are interested in joining the DIFF staff team, this panel is here to "
            "direct you to the correct place quickly and clearly.\n\n"
            "**Please select the option that best matches your situation below.**"
        ),
        color=discord.Color.blue(),
    )
    for ticket in _TICKET_TYPES.values():
        embed.add_field(name=ticket.label, value=ticket.long_description, inline=False)
    return _supp_brand_embed(embed)


def _supp_build_ticket_embed(ticket: _TicketType, user: discord.Member) -> discord.Embed:
    from datetime import timezone as _tz
    embed = discord.Embed(
        title=f"{ticket.emoji} {ticket.title}",
        description=(
            f"{user.mention}, your ticket has been created.\n\n"
            f"{ticket.long_description}\n\n"
            "**Please explain your situation clearly and include as much detail as possible.**"
        ),
        color=discord.Color.blue(),
        timestamp=datetime.now(_tz.utc),
    )
    embed.add_field(name="Opened By", value=f"{user.mention} (`{user.id}`)", inline=False)
    embed.add_field(name="Category", value=ticket.label, inline=True)
    embed.add_field(name="Status", value="Open", inline=True)
    return _supp_brand_embed(embed)


def _supp_build_questions_embed(user: discord.Member) -> discord.Embed:
    embed = discord.Embed(
        title="📋 DIFF Staff Application Questions",
        description=(
            f"{user.mention}, please answer each question below in this ticket.\n\n"
            "**Take your time and be detailed, honest, and professional.**"
        ),
        color=discord.Color.blurple(),
    )
    embed.add_field(
        name="Questions",
        value="\n".join(f"**{i}.** {q}" for i, q in enumerate(_SUPP_APPLICATION_QUESTIONS, 1)),
        inline=False,
    )
    embed.add_field(
        name="Review Process",
        value="Once you answer everything, DIFF leadership can review your application and use the panel below to approve or deny it.",
        inline=False,
    )
    return _supp_brand_embed(embed)


def _supp_build_review_embed(applicant: discord.Member) -> discord.Embed:
    from datetime import timezone as _tz
    embed = discord.Embed(
        title="🧾 Staff Review Panel",
        description=(
            f"Applicant: {applicant.mention}\n\n"
            "Leadership can review this application and choose one of the actions below."
        ),
        color=discord.Color.dark_blue(),
        timestamp=datetime.now(_tz.utc),
    )
    embed.add_field(
        name="Actions",
        value=(
            "✅ **Accept** — Approve the application and assign the configured staff role\n"
            "❌ **Deny** — Deny the application and log the decision"
        ),
        inline=False,
    )
    return _supp_brand_embed(embed)


def _supp_build_decision_embed(applicant: discord.Member, reviewer: discord.Member, approved: bool) -> discord.Embed:
    from datetime import timezone as _tz
    embed = discord.Embed(
        title="✅ Application Approved" if approved else "❌ Application Denied",
        description=(
            f"Applicant: {applicant.mention}\n"
            f"Reviewed By: {reviewer.mention}\n\n"
            f"Decision: {'Approved' if approved else 'Denied'}"
        ),
        color=discord.Color.green() if approved else discord.Color.red(),
        timestamp=datetime.now(_tz.utc),
    )
    return _supp_brand_embed(embed)


def _supp_build_log_embed(action: str, user: discord.Member, ticket: _TicketType, channel: discord.TextChannel) -> discord.Embed:
    from datetime import timezone as _tz
    now = datetime.now(_tz.utc)
    embed = discord.Embed(
        title=f"📁 Ticket {action}",
        color=discord.Color.dark_blue(),
        timestamp=now,
    )
    embed.add_field(name="User", value=f"{user.mention} (`{user.id}`)", inline=False)
    embed.add_field(name="Type", value=ticket.label, inline=True)
    embed.add_field(name="Channel", value=channel.name, inline=True)
    embed.add_field(name="Time", value=f"<t:{int(now.timestamp())}:F>", inline=False)
    return _supp_brand_embed(embed)


async def _supp_find_existing_ticket(
    guild: discord.Guild,
    member: discord.Member,
    ticket: _TicketType,
) -> discord.TextChannel | None:
    expected = f"{ticket.channel_prefix}-{_supp_clean_name(member.name)}"
    for ch in guild.text_channels:
        if ch.name.startswith(expected) and ch.topic:
            if f"ticket_owner={member.id}" in ch.topic and f"ticket_type={ticket.key}" in ch.topic:
                return ch
    return None


async def _supp_export_transcript(channel: discord.TextChannel) -> discord.File:
    lines: list[str] = []
    async for msg in channel.history(limit=None, oldest_first=True):
        created = msg.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        header = f"[{created}] {msg.author} ({msg.author.id})"
        content = msg.content or ""
        attachments = "\n" + "\n".join(f"[Attachment] {a.url}" for a in msg.attachments) if msg.attachments else ""
        embed_lines: list[str] = []
        for emb in msg.embeds:
            if emb.title:
                embed_lines.append(f"[Embed Title] {emb.title}")
            if emb.description:
                embed_lines.append(f"[Embed Description] {emb.description}")
            for field in emb.fields:
                embed_lines.append(f"[Embed Field] {field.name}: {field.value}")
        embeds = ("\n" + "\n".join(embed_lines)) if embed_lines else ""
        lines.append(f"{header}\n{content}{attachments}{embeds}\n{'-'*60}\n")
    text = "".join(lines) if lines else "No messages found."
    buffer = io.BytesIO(text.encode("utf-8"))
    return discord.File(buffer, filename=f"{channel.name[:80]}-transcript.txt")


class SupportCloseButton(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="diff_support_close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not interaction.guild or not isinstance(interaction.channel, discord.TextChannel):
            return await interaction.response.send_message("This can only be used in a ticket channel.", ephemeral=True)
        if not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Member check failed.", ephemeral=True)
        channel = interaction.channel
        member = interaction.user
        owner_id = _supp_parse_topic(channel.topic, "ticket_owner")
        is_owner = owner_id == str(member.id)
        is_staff = any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID, HOST_ROLE_ID} for r in member.roles)
        if not (is_owner or is_staff or member.guild_permissions.manage_channels):
            return await interaction.response.send_message("You do not have permission to close this ticket.", ephemeral=True)

        await interaction.response.send_message("Closing ticket and saving transcript...", ephemeral=True)

        ticket_key = _supp_parse_topic(channel.topic, "ticket_type") or "support"
        ticket = _TICKET_TYPES.get(ticket_key, _TICKET_TYPES["support"])

        transcript_file = await _supp_export_transcript(channel)
        logs_channel = interaction.guild.get_channel(STAFF_LOGS_CHANNEL_ID)
        if isinstance(logs_channel, discord.TextChannel):
            from datetime import timezone as _tz
            now = datetime.now(_tz.utc)
            close_embed = discord.Embed(
                title="🧾 Ticket Closed",
                description=(
                    f"Closed By: {member.mention}\n"
                    f"Channel: `{channel.name}`\n"
                    f"Type: {ticket.label}\n"
                    f"Closed At: <t:{int(now.timestamp())}:F>"
                ),
                color=discord.Color.red(),
                timestamp=now,
            )
            if owner_id:
                close_embed.add_field(name="Ticket Owner ID", value=owner_id, inline=False)
            _supp_brand_embed(close_embed)
            try:
                await logs_channel.send(embed=close_embed, file=transcript_file)
            except discord.HTTPException:
                pass

        await asyncio.sleep(1.5)
        try:
            await channel.delete(reason=f"Ticket closed by {member} ({member.id})")
        except discord.HTTPException:
            pass


class SupportApplicationReviewView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    async def _check(self, interaction: discord.Interaction) -> bool:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return False
        return any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID} for r in interaction.user.roles) \
               or interaction.user.guild_permissions.manage_guild

    @discord.ui.button(label="Accept", emoji="✅", style=discord.ButtonStyle.success, custom_id="diff_app_accept")
    async def accept_application(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not await self._check(interaction):
            return await interaction.response.send_message("Only DIFF leadership can approve applications.", ephemeral=True)
        if not interaction.guild or not isinstance(interaction.channel, discord.TextChannel) or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Server only.", ephemeral=True)
        applicant_id_raw = _supp_parse_topic(interaction.channel.topic, "ticket_owner")
        if not applicant_id_raw or not applicant_id_raw.isdigit():
            return await interaction.response.send_message("Could not detect the applicant from this ticket.", ephemeral=True)
        applicant = interaction.guild.get_member(int(applicant_id_raw))
        if applicant is None:
            return await interaction.response.send_message("The applicant is no longer in the server.", ephemeral=True)
        await interaction.response.send_message("Application approved.", ephemeral=True)
        role = interaction.guild.get_role(_SUPP_APPROVED_STAFF_ROLE_ID) if _SUPP_APPROVED_STAFF_ROLE_ID else None
        if role:
            try:
                await applicant.add_roles(role, reason=f"Application approved by {interaction.user}")
            except discord.HTTPException:
                pass
        embed = _supp_build_decision_embed(applicant, interaction.user, approved=True)
        await interaction.channel.send(embed=embed)
        logs_channel = interaction.guild.get_channel(STAFF_LOGS_CHANNEL_ID)
        if isinstance(logs_channel, discord.TextChannel):
            await logs_channel.send(embed=embed)
        for child in self.children:
            child.disabled = True
        try:
            await interaction.message.edit(view=self)
        except discord.HTTPException:
            pass

    @discord.ui.button(label="Deny", emoji="❌", style=discord.ButtonStyle.danger, custom_id="diff_app_deny")
    async def deny_application(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not await self._check(interaction):
            return await interaction.response.send_message("Only DIFF leadership can deny applications.", ephemeral=True)
        if not interaction.guild or not isinstance(interaction.channel, discord.TextChannel) or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Server only.", ephemeral=True)
        applicant_id_raw = _supp_parse_topic(interaction.channel.topic, "ticket_owner")
        if not applicant_id_raw or not applicant_id_raw.isdigit():
            return await interaction.response.send_message("Could not detect the applicant from this ticket.", ephemeral=True)
        applicant = interaction.guild.get_member(int(applicant_id_raw))
        if applicant is None:
            return await interaction.response.send_message("The applicant is no longer in the server.", ephemeral=True)
        embed = _supp_build_decision_embed(applicant, interaction.user, approved=False)
        await interaction.response.send_message("Application denied.", ephemeral=True)
        await interaction.channel.send(embed=embed)
        logs_channel = interaction.guild.get_channel(STAFF_LOGS_CHANNEL_ID)
        if isinstance(logs_channel, discord.TextChannel):
            await logs_channel.send(embed=embed)
        for child in self.children:
            child.disabled = True
        try:
            await interaction.message.edit(view=self)
        except discord.HTTPException:
            pass


class SupportDropdown(discord.ui.Select):
    def __init__(self) -> None:
        options = [
            discord.SelectOption(
                label=t.label,
                value=t.key,
                description=t.description[:100],
                emoji=t.emoji,
            )
            for t in _TICKET_TYPES.values()
        ]
        super().__init__(
            placeholder="Choose the support option that best fits your situation...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="diff_support_dropdown_select",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("This can only be used inside the server.", ephemeral=True)

        ticket = _TICKET_TYPES[self.values[0]]

        panel_channel = interaction.guild.get_channel(SUPPORT_PANEL_CHANNEL_ID)
        category = None
        if SUPPORT_TICKET_CATEGORY_ID:
            category = interaction.guild.get_channel(SUPPORT_TICKET_CATEGORY_ID)
        elif isinstance(panel_channel, discord.TextChannel):
            category = panel_channel.category

        if not isinstance(category, discord.CategoryChannel):
            return await interaction.response.send_message(
                "Ticket category is not set up correctly. Please ask staff to check the configuration.",
                ephemeral=True,
            )

        try:
            await interaction.response.defer(ephemeral=True)
        except discord.NotFound:
            return

        existing = await _supp_find_existing_ticket(interaction.guild, interaction.user, ticket)
        if existing:
            return await interaction.followup.send(
                f"You already have an open {ticket.label} ticket: {existing.mention}", ephemeral=True
            )

        staff_role_ids = {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID, HOST_ROLE_ID}
        overwrites: dict = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True, send_messages=True,
                read_message_history=True, attach_files=True, embed_links=True,
            ),
        }
        me = interaction.guild.me
        if me:
            overwrites[me] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True,
                read_message_history=True, manage_channels=True, manage_messages=True,
                attach_files=True, embed_links=True,
            )
        for role_id in staff_role_ids:
            role = interaction.guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True,
                    read_message_history=True, manage_messages=True,
                    attach_files=True, embed_links=True,
                )

        channel_name = f"{ticket.channel_prefix}-{_supp_clean_name(interaction.user.name)}"
        topic = f"ticket_owner={interaction.user.id} | ticket_type={ticket.key}"
        channel = await interaction.guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=topic,
            reason=f"{ticket.title} opened by {interaction.user} ({interaction.user.id})",
        )

        ping = " ".join(filter(None, [interaction.user.mention, _supp_role_mention(ticket.ping_role_id)]))
        await channel.send(
            content=ping or None,
            embed=_supp_build_ticket_embed(ticket, interaction.user),
            view=SupportCloseButton(),
        )

        if ticket.key == "apply":
            await channel.send(embed=_supp_build_questions_embed(interaction.user))
            await channel.send(embed=_supp_build_review_embed(interaction.user), view=SupportApplicationReviewView())

        logs_channel = interaction.guild.get_channel(STAFF_LOGS_CHANNEL_ID)
        if isinstance(logs_channel, discord.TextChannel):
            try:
                await logs_channel.send(embed=_supp_build_log_embed("Opened", interaction.user, ticket, channel))
            except discord.HTTPException:
                pass

        await interaction.followup.send(
            f"Your {ticket.label} ticket has been created: {channel.mention}", ephemeral=True
        )


class SupportDropdownView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.add_item(SupportDropdown())

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        traceback.print_exception(type(error), error, error.__traceback__)
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
            else:
                await interaction.followup.send("Something went wrong. Please try again.", ephemeral=True)
        except Exception:
            pass


@bot.tree.command(name="post-support-panel", description="Post the DIFF Support Center dropdown panel (staff only)")
async def post_support_panel(interaction: discord.Interaction) -> None:
    if not interaction.guild:
        return await interaction.response.send_message("Server only.", ephemeral=True)
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    channel = interaction.guild.get_channel(SUPPORT_PANEL_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        return await interaction.response.send_message("Support panel channel not found.", ephemeral=True)
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return
    try:
        async for msg in channel.history(limit=50):
            if msg.author.id == bot.user.id and any(e.title == _SUPPORT_BRAND for e in msg.embeds):
                try:
                    await msg.delete()
                except discord.HTTPException:
                    pass
    except discord.HTTPException:
        pass
    await channel.send(embed=_supp_build_panel_embed(), view=SupportDropdownView())
    await interaction.followup.send(f"Support panel posted in {channel.mention}.", ephemeral=True)




# =========================
# DIFF STAFF AUTOMATION SYSTEM
# =========================

_STAFF_DATA_FILE = "diff_data/diff_staff_stats.json"
_PROMOTION_LOG_CHANNEL_ID = STAFF_LOGS_CHANNEL_ID

_PROMOTION_FLOW: dict[int, int] = {
    CREW_MEMBER_ROLE_ID: HOST_ROLE_ID,
    HOST_ROLE_ID: MANAGER_ROLE_ID,
    MANAGER_ROLE_ID: CO_LEADER_ROLE_ID,
    CO_LEADER_ROLE_ID: LEADER_ROLE_ID,
}

_PROMOTION_THRESHOLDS = {
    "tickets_handled": 8,
    "applications_reviewed": 4,
    "meets_hosted": 4,
    "score": 18,
}

_STAFF_DM_APPROVED_TITLE = "DIFF Staff Application Update"
_STAFF_DM_DENIED_TITLE = "DIFF Staff Application Decision"
_STAFF_DM_APPROVED_BODY = (
    "You have been approved for the DIFF staff team.\n\n"
    "Congratulations, and thank you for showing interest in helping the crew grow.\n\n"
    "A leadership member reviewed your application and chose to move forward with you. "
    "Please remain active, professional, and consistent as you step into this role.\n\n"
    "Be ready to support the community, assist members, and represent DIFF the right way.\n\n"
    "— Different Meets"
)
_STAFF_DM_DENIED_BODY = (
    "Thank you for applying for the DIFF staff team.\n\n"
    "After review, your application was not approved at this time.\n\n"
    "This does not mean you cannot improve and apply again later. Keep staying active, "
    "show maturity, support the community, and continue building your presence in DIFF.\n\n"
    "We appreciate your interest and effort.\n\n"
    "— Different Meets"
)


class _StatsStore:
    def __init__(self, file_path: str) -> None:
        from pathlib import Path as _Path
        self.path = _Path(file_path)
        self.data = self._load()

    def _default(self) -> dict:
        from datetime import timezone as _tz
        return {"users": {}, "last_reset": datetime.now(_tz.utc).isoformat()}

    def _load(self) -> dict:
        if not self.path.exists():
            d = self._default()
            self.path.write_text(json.dumps(d, indent=2), encoding="utf-8")
            return d
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            d = self._default()
            self.path.write_text(json.dumps(d, indent=2), encoding="utf-8")
            return d

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def ensure_user(self, user_id: int) -> dict:
        key = str(user_id)
        if key not in self.data["users"]:
            from datetime import timezone as _tz
            self.data["users"][key] = {
                "tickets_handled": 0,
                "applications_reviewed": 0,
                "meets_hosted": 0,
                "reports_resolved": 0,
                "appeals_reviewed": 0,
                "accepted_apps": 0,
                "denied_apps": 0,
                "last_updated": datetime.now(_tz.utc).isoformat(),
            }
        return self.data["users"][key]

    def add_stat(self, user_id: int, field: str, amount: int = 1) -> dict:
        from datetime import timezone as _tz
        user = self.ensure_user(user_id)
        user[field] = int(user.get(field, 0)) + amount
        user["last_updated"] = datetime.now(_tz.utc).isoformat()
        self.save()
        return user

    def reset_all(self) -> None:
        self.data = self._default()
        self.save()

    def leaderboard(self) -> list[tuple[int, dict]]:
        rows = [(int(uid), stats) for uid, stats in self.data["users"].items()]
        rows.sort(key=lambda x: _staff_score(x[1]), reverse=True)
        return rows


def _staff_score(stats: dict) -> int:
    return (
        stats.get("tickets_handled", 0) * 2
        + stats.get("applications_reviewed", 0) * 3
        + stats.get("meets_hosted", 0) * 2
        + stats.get("reports_resolved", 0) * 2
        + stats.get("appeals_reviewed", 0) * 2
    )


def _staff_next_promo_role(member: discord.Member) -> int | None:
    current_ids = {r.id for r in member.roles}
    for cur, nxt in _PROMOTION_FLOW.items():
        if cur in current_ids and nxt not in current_ids:
            return nxt
    return None


_staff_store = _StatsStore(_STAFF_DATA_FILE)


async def _staff_send_dm(member: discord.Member, approved: bool) -> None:
    from datetime import timezone as _tz
    try:
        embed = discord.Embed(
            title=_STAFF_DM_APPROVED_TITLE if approved else _STAFF_DM_DENIED_TITLE,
            description=_STAFF_DM_APPROVED_BODY if approved else _STAFF_DM_DENIED_BODY,
            color=discord.Color.green() if approved else discord.Color.red(),
            timestamp=datetime.now(_tz.utc),
        )
        embed.set_footer(text="Different Meets • Staff System")
        await member.send(embed=embed)
    except discord.HTTPException:
        pass


async def _staff_check_promotion(guild: discord.Guild, member: discord.Member) -> None:
    from datetime import timezone as _tz
    stats = _staff_store.ensure_user(member.id)
    score = _staff_score(stats)
    meets_threshold = (
        stats.get("tickets_handled", 0) >= _PROMOTION_THRESHOLDS["tickets_handled"]
        or stats.get("applications_reviewed", 0) >= _PROMOTION_THRESHOLDS["applications_reviewed"]
        or stats.get("meets_hosted", 0) >= _PROMOTION_THRESHOLDS["meets_hosted"]
        or score >= _PROMOTION_THRESHOLDS["score"]
    )
    if not meets_threshold:
        return
    next_role_id = _staff_next_promo_role(member)
    if not next_role_id:
        return
    next_role = guild.get_role(next_role_id)
    if not next_role:
        return
    log_channel = guild.get_channel(_PROMOTION_LOG_CHANNEL_ID)
    if not isinstance(log_channel, discord.TextChannel):
        return
    now = datetime.now(_tz.utc)
    embed = discord.Embed(
        title="📈 Promotion Suggestion",
        description=(
            f"User: {member.mention}\n"
            f"Suggested Next Role: {next_role.mention}\n\n"
            "This staff member has reached the DIFF activity threshold for a promotion review."
        ),
        color=discord.Color.green(),
        timestamp=now,
    )
    embed.add_field(name="Tickets Handled", value=str(stats.get("tickets_handled", 0)), inline=True)
    embed.add_field(name="Apps Reviewed", value=str(stats.get("applications_reviewed", 0)), inline=True)
    embed.add_field(name="Meets Hosted", value=str(stats.get("meets_hosted", 0)), inline=True)
    embed.add_field(name="Reports Resolved", value=str(stats.get("reports_resolved", 0)), inline=True)
    embed.add_field(name="Appeals Reviewed", value=str(stats.get("appeals_reviewed", 0)), inline=True)
    embed.add_field(name="Activity Score", value=str(score), inline=True)
    if DIFF_LOGO_URL:
        embed.set_thumbnail(url=DIFF_LOGO_URL)
    if DIFF_BANNER_URL:
        embed.set_image(url=DIFF_BANNER_URL)
    embed.set_footer(text="Different Meets • Staff Automation")
    try:
        await log_channel.send(embed=embed)
    except discord.HTTPException:
        pass


class StaffReviewView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    async def _get_applicant(self, interaction: discord.Interaction) -> discord.Member | None:
        if not interaction.guild or not isinstance(interaction.channel, discord.TextChannel):
            return None
        owner_raw = _supp_parse_topic(interaction.channel.topic, "ticket_owner")
        if not owner_raw or not owner_raw.isdigit():
            return None
        return interaction.guild.get_member(int(owner_raw))

    async def _handle(self, interaction: discord.Interaction, approved: bool) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Server only.", ephemeral=True)
        if not any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID} for r in interaction.user.roles) \
                and not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("Only DIFF leadership can use this panel.", ephemeral=True)

        applicant = await self._get_applicant(interaction)
        if applicant is None:
            return await interaction.response.send_message("Could not detect the applicant from this ticket.", ephemeral=True)

        await interaction.response.send_message(
            f"Application {'approved' if approved else 'denied'} and logged.", ephemeral=True
        )

        _staff_store.add_stat(interaction.user.id, "applications_reviewed", 1)
        _staff_store.add_stat(interaction.user.id, "accepted_apps" if approved else "denied_apps", 1)

        if approved:
            role = interaction.guild.get_role(_SUPP_APPROVED_STAFF_ROLE_ID)
            if role and role not in applicant.roles:
                try:
                    await applicant.add_roles(role, reason=f"Application approved by {interaction.user}")
                except discord.HTTPException:
                    pass

        from datetime import timezone as _tz
        now = datetime.now(_tz.utc)
        ch_embed = discord.Embed(
            title="✅ Application Approved" if approved else "❌ Application Denied",
            description=f"Applicant: {applicant.mention}\nReviewed By: {interaction.user.mention}",
            color=discord.Color.green() if approved else discord.Color.red(),
            timestamp=now,
        )
        ch_embed.set_footer(text="Different Meets • Staff System")
        if isinstance(interaction.channel, discord.TextChannel):
            await interaction.channel.send(embed=ch_embed)

        await _staff_send_dm(applicant, approved=approved)

        logs_channel = interaction.guild.get_channel(STAFF_LOGS_CHANNEL_ID)
        if isinstance(logs_channel, discord.TextChannel):
            log_embed = discord.Embed(
                title="🧾 Staff Application Decision",
                description=(
                    f"Applicant: {applicant.mention}\n"
                    f"Reviewed By: {interaction.user.mention}\n"
                    f"Decision: {'Approved' if approved else 'Denied'}\n"
                    f"Time: <t:{int(now.timestamp())}:F>"
                ),
                color=discord.Color.blue(),
                timestamp=now,
            )
            log_embed.set_footer(text="Different Meets • Staff System")
            try:
                await logs_channel.send(embed=log_embed)
            except discord.HTTPException:
                pass

        await _staff_check_promotion(interaction.guild, interaction.user)

        for child in self.children:
            child.disabled = True
        try:
            await interaction.message.edit(view=self)
        except discord.HTTPException:
            pass

    @discord.ui.button(label="Accept", emoji="✅", style=discord.ButtonStyle.success, custom_id="diff_staff_auto_accept")
    async def accept(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._handle(interaction, approved=True)

    @discord.ui.button(label="Deny", emoji="❌", style=discord.ButtonStyle.danger, custom_id="diff_staff_auto_deny")
    async def deny(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._handle(interaction, approved=False)


@bot.tree.command(name="staff-stats", description="View DIFF staff performance stats for a member (staff only)")
@app_commands.describe(member="The staff member to look up")
async def staff_stats(interaction: discord.Interaction, member: discord.Member) -> None:
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return await interaction.response.send_message("Server only.", ephemeral=True)
    if not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    stats = _staff_store.ensure_user(member.id)
    from datetime import timezone as _tz
    embed = discord.Embed(
        title="📊 DIFF Staff Performance Snapshot",
        description=f"Stats for {member.mention}",
        color=discord.Color.blue(),
        timestamp=datetime.now(_tz.utc),
    )
    embed.add_field(name="Tickets Handled", value=str(stats.get("tickets_handled", 0)), inline=True)
    embed.add_field(name="Apps Reviewed", value=str(stats.get("applications_reviewed", 0)), inline=True)
    embed.add_field(name="Meets Hosted", value=str(stats.get("meets_hosted", 0)), inline=True)
    embed.add_field(name="Reports Resolved", value=str(stats.get("reports_resolved", 0)), inline=True)
    embed.add_field(name="Appeals Reviewed", value=str(stats.get("appeals_reviewed", 0)), inline=True)
    embed.add_field(name="Score", value=str(_staff_score(stats)), inline=True)
    embed.set_footer(text="Different Meets • Staff Automation")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="staff-add-ticket", description="Add handled ticket stats to a staff member (leadership only)")
@app_commands.describe(member="Staff member to update", amount="Number of tickets to add (default 1)")
async def staff_add_ticket(interaction: discord.Interaction, member: discord.Member, amount: app_commands.Range[int, 1, 100] = 1) -> None:
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return await interaction.response.send_message("Server only.", ephemeral=True)
    if not any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID} for r in interaction.user.roles) \
            and not interaction.user.guild_permissions.manage_guild:
        return await interaction.response.send_message("Leadership only.", ephemeral=True)
    _staff_store.add_stat(member.id, "tickets_handled", amount)
    await interaction.response.send_message(f"Added **{amount}** handled ticket(s) to {member.mention}.", ephemeral=True)
    await _staff_check_promotion(interaction.guild, member)


@bot.tree.command(name="staff-add-application", description="Add reviewed application stats to a staff member (leadership only)")
@app_commands.describe(member="Staff member to update", amount="Number of applications to add (default 1)")
async def staff_add_application(interaction: discord.Interaction, member: discord.Member, amount: app_commands.Range[int, 1, 100] = 1) -> None:
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return await interaction.response.send_message("Server only.", ephemeral=True)
    if not any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID} for r in interaction.user.roles) \
            and not interaction.user.guild_permissions.manage_guild:
        return await interaction.response.send_message("Leadership only.", ephemeral=True)
    _staff_store.add_stat(member.id, "applications_reviewed", amount)
    await interaction.response.send_message(f"Added **{amount}** reviewed application(s) to {member.mention}.", ephemeral=True)
    await _staff_check_promotion(interaction.guild, member)


@bot.tree.command(name="staff-add-report", description="Add resolved report stats to a staff member (leadership only)")
@app_commands.describe(member="Staff member to update", amount="Number of reports to add (default 1)")
async def staff_add_report(interaction: discord.Interaction, member: discord.Member, amount: app_commands.Range[int, 1, 100] = 1) -> None:
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return await interaction.response.send_message("Server only.", ephemeral=True)
    if not any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID} for r in interaction.user.roles) \
            and not interaction.user.guild_permissions.manage_guild:
        return await interaction.response.send_message("Leadership only.", ephemeral=True)
    _staff_store.add_stat(member.id, "reports_resolved", amount)
    await interaction.response.send_message(f"Added **{amount}** resolved report(s) to {member.mention}.", ephemeral=True)
    await _staff_check_promotion(interaction.guild, member)


@bot.tree.command(name="staff-add-appeal", description="Add reviewed appeal stats to a staff member (leadership only)")
@app_commands.describe(member="Staff member to update", amount="Number of appeals to add (default 1)")
async def staff_add_appeal(interaction: discord.Interaction, member: discord.Member, amount: app_commands.Range[int, 1, 100] = 1) -> None:
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return await interaction.response.send_message("Server only.", ephemeral=True)
    if not any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID} for r in interaction.user.roles) \
            and not interaction.user.guild_permissions.manage_guild:
        return await interaction.response.send_message("Leadership only.", ephemeral=True)
    _staff_store.add_stat(member.id, "appeals_reviewed", amount)
    await interaction.response.send_message(f"Added **{amount}** reviewed appeal(s) to {member.mention}.", ephemeral=True)
    await _staff_check_promotion(interaction.guild, member)


@bot.tree.command(name="staff-post-leaderboard", description="Post the DIFF staff performance leaderboard (leadership only)")
async def staff_post_leaderboard(interaction: discord.Interaction) -> None:
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return await interaction.response.send_message("Server only.", ephemeral=True)
    if not any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID} for r in interaction.user.roles) \
            and not interaction.user.guild_permissions.manage_guild:
        return await interaction.response.send_message("Leadership only.", ephemeral=True)
    lb_channel = interaction.guild.get_channel(LEADERBOARD_CHANNEL_ID)
    if not isinstance(lb_channel, discord.TextChannel):
        return await interaction.response.send_message("Leaderboard channel not found.", ephemeral=True)
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return
    from datetime import timezone as _tz
    rows = _staff_store.leaderboard()
    embed = discord.Embed(
        title="🏆 DIFF Staff Performance Leaderboard",
        description="Top active staff members based on tickets, applications, and meets.",
        color=discord.Color.gold(),
        timestamp=datetime.now(_tz.utc),
    )
    if not rows:
        embed.add_field(name="No Data Yet", value="No staff stats recorded yet.", inline=False)
    else:
        lines: list[str] = []
        for idx, (uid, stats) in enumerate(rows[:10], 1):
            m = interaction.guild.get_member(uid)
            display = m.mention if m else f"<@{uid}>"
            lines.append(
                f"**#{idx}** {display}\n"
                f"Score: **{_staff_score(stats)}** | "
                f"Tickets: **{stats.get('tickets_handled', 0)}** | "
                f"Apps: **{stats.get('applications_reviewed', 0)}** | "
                f"Meets: **{stats.get('meets_hosted', 0)}**"
            )
        embed.add_field(name="Top Staff", value="\n\n".join(lines), inline=False)
    embed.set_footer(text="Different Meets • Staff Automation")
    await lb_channel.send(embed=embed)
    await interaction.followup.send(f"Leaderboard posted in {lb_channel.mention}.", ephemeral=True)


@bot.tree.command(name="staff-reset-stats", description="Reset all DIFF staff performance stats (leadership only)")
async def staff_reset_stats(interaction: discord.Interaction) -> None:
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return await interaction.response.send_message("Server only.", ephemeral=True)
    if not any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID} for r in interaction.user.roles) \
            and not interaction.user.guild_permissions.manage_guild:
        return await interaction.response.send_message("Leadership only.", ephemeral=True)
    _staff_store.reset_all()
    await interaction.response.send_message("All staff stats have been reset.", ephemeral=True)


@bot.tree.command(name="post-staff-review-panel", description="Post an Accept / Deny review panel in the current ticket (leadership only)")
async def post_staff_review_panel(interaction: discord.Interaction) -> None:
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return await interaction.response.send_message("Server only.", ephemeral=True)
    if not any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID} for r in interaction.user.roles) \
            and not interaction.user.guild_permissions.manage_guild:
        return await interaction.response.send_message("Leadership only.", ephemeral=True)
    if not isinstance(interaction.channel, discord.TextChannel):
        return await interaction.response.send_message("Must be used inside a ticket channel.", ephemeral=True)
    from datetime import timezone as _tz
    embed = discord.Embed(
        title="🧾 DIFF Staff Review Panel",
        description=(
            "Leadership can review this application using the buttons below.\n\n"
            "✅ **Accept** — Approve the application, DM the applicant, assign host role, and log the decision\n"
            "❌ **Deny** — Deny the application, DM the applicant, and log the decision"
        ),
        color=discord.Color.blurple(),
        timestamp=datetime.now(_tz.utc),
    )
    embed.set_footer(text="Different Meets • Staff Automation")
    await interaction.channel.send(embed=embed, view=StaffReviewView())
    await interaction.response.send_message("Review panel posted.", ephemeral=True)


# =========================
# DIFF AUTO TRACKING — WEEKLY REPORT SYSTEM
# =========================

_AUTO_STATS_FILE = "diff_data/diff_auto_staff_stats.json"
_AUTO_CACHE_FILE = "diff_data/diff_ticket_activity_cache.json"
_AUTO_WEEKLY_WEEKDAY = 0      # Monday
_AUTO_WEEKLY_HOUR_UTC = 16    # 12 PM ET / 16 UTC
_AUTO_WEEKLY_MINUTE_UTC = 0
_AUTO_MIN_MSG_TO_COUNT = 1


class _AutoStatsStore:
    def __init__(self, file_path: str) -> None:
        from pathlib import Path as _Path
        self.path = _Path(file_path)
        self.data = self._load()

    def _default(self) -> dict:
        from datetime import timezone as _tz
        return {"users": {}, "weekly_history": [], "last_reset": datetime.now(_tz.utc).isoformat()}

    def _load(self) -> dict:
        if not self.path.exists():
            d = self._default()
            self.path.write_text(json.dumps(d, indent=2), encoding="utf-8")
            return d
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            d = self._default()
            self.path.write_text(json.dumps(d, indent=2), encoding="utf-8")
            return d

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def ensure_user(self, user_id: int) -> dict:
        from datetime import timezone as _tz
        key = str(user_id)
        if key not in self.data["users"]:
            self.data["users"][key] = {
                "tickets_handled": 0,
                "applications_reviewed": 0,
                "meets_hosted": 0,
                "reports_resolved": 0,
                "appeals_reviewed": 0,
                "accepted_apps": 0,
                "denied_apps": 0,
                "messages_in_tickets": 0,
                "last_updated": datetime.now(_tz.utc).isoformat(),
            }
        return self.data["users"][key]

    def add_stat(self, user_id: int, field: str, amount: int = 1) -> dict:
        from datetime import timezone as _tz
        user = self.ensure_user(user_id)
        user[field] = int(user.get(field, 0)) + amount
        user["last_updated"] = datetime.now(_tz.utc).isoformat()
        self.save()
        return user

    def leaderboard(self) -> list[tuple[int, dict]]:
        rows = [(int(uid), s) for uid, s in self.data["users"].items()]
        rows.sort(key=lambda x: _auto_score(x[1]), reverse=True)
        return rows

    def archive_and_reset(self) -> None:
        from datetime import timezone as _tz
        snapshot = {"ended_at": datetime.now(_tz.utc).isoformat(), "leaderboard": self.leaderboard()[:10]}
        self.data["weekly_history"].append(snapshot)
        self.data["users"] = {}
        self.data["last_reset"] = datetime.now(_tz.utc).isoformat()
        self.save()


class _TicketActivityStore:
    def __init__(self, file_path: str) -> None:
        from pathlib import Path as _Path
        self.path = _Path(file_path)
        self.data = self._load()

    def _default(self) -> dict:
        return {"tickets": {}}

    def _load(self) -> dict:
        if not self.path.exists():
            d = self._default()
            self.path.write_text(json.dumps(d, indent=2), encoding="utf-8")
            return d
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            d = self._default()
            self.path.write_text(json.dumps(d, indent=2), encoding="utf-8")
            return d

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def add_staff_message(self, channel_id: int, channel_name: str, ticket_type: str, owner_id: str | None, user_id: int) -> None:
        from datetime import timezone as _tz
        key = str(channel_id)
        if key not in self.data["tickets"]:
            self.data["tickets"][key] = {
                "channel_name": channel_name,
                "ticket_type": ticket_type,
                "owner_id": owner_id,
                "staff_messages": {},
                "created_at": datetime.now(_tz.utc).isoformat(),
                "last_seen_at": datetime.now(_tz.utc).isoformat(),
            }
        ticket = self.data["tickets"][key]
        uid = str(user_id)
        ticket["staff_messages"][uid] = int(ticket["staff_messages"].get(uid, 0)) + 1
        ticket["last_seen_at"] = datetime.now(_tz.utc).isoformat()
        self.save()

    def pop_ticket(self, channel_id: int) -> dict | None:
        key = str(channel_id)
        ticket = self.data["tickets"].pop(key, None)
        if ticket is not None:
            self.save()
        return ticket


_auto_stats = _AutoStatsStore(_AUTO_STATS_FILE)
_ticket_cache = _TicketActivityStore(_AUTO_CACHE_FILE)


def _auto_score(stats: dict) -> int:
    return (
        stats.get("tickets_handled", 0) * 2
        + stats.get("applications_reviewed", 0) * 3
        + stats.get("meets_hosted", 0) * 2
        + stats.get("reports_resolved", 0) * 2
        + stats.get("appeals_reviewed", 0) * 2
        + stats.get("accepted_apps", 0) * 1
    )


def _auto_is_ticket_channel(channel: discord.TextChannel) -> bool:
    return bool(channel.topic and "ticket_owner=" in channel.topic and "ticket_type=" in channel.topic)


def _auto_build_weekly_embed(guild: discord.Guild, rows: list[tuple[int, dict]]) -> discord.Embed:
    from datetime import timezone as _tz
    embed = discord.Embed(
        title="🏆 Weekly DIFF Staff Report",
        description="Automatic weekly recap for DIFF staff performance.",
        color=discord.Color.gold(),
        timestamp=datetime.now(_tz.utc),
    )
    if not rows:
        embed.add_field(name="No Activity Logged", value="No staff activity was recorded this week.", inline=False)
    else:
        lines: list[str] = []
        for idx, (uid, stats) in enumerate(rows[:10], 1):
            m = guild.get_member(uid)
            display = m.mention if m else f"<@{uid}>"
            lines.append(
                f"**#{idx}** {display}\n"
                f"Score: **{_auto_score(stats)}** | "
                f"Tickets: **{stats.get('tickets_handled', 0)}** | "
                f"Apps: **{stats.get('applications_reviewed', 0)}** | "
                f"Meets: **{stats.get('meets_hosted', 0)}**"
            )
        embed.add_field(name="Leaderboard", value="\n\n".join(lines), inline=False)
        top_uid, top_stats = rows[0]
        top_m = guild.get_member(top_uid)
        top_display = top_m.mention if top_m else f"<@{top_uid}>"
        embed.add_field(
            name="🔥 Top Performer of the Week",
            value=(
                f"{top_display}\n"
                f"Score: **{_auto_score(top_stats)}**\n"
                f"Tickets Handled: **{top_stats.get('tickets_handled', 0)}**\n"
                f"Applications Reviewed: **{top_stats.get('applications_reviewed', 0)}**\n"
                f"Meets Hosted: **{top_stats.get('meets_hosted', 0)}**"
            ),
            inline=False,
        )
    if DIFF_LOGO_URL:
        embed.set_thumbnail(url=DIFF_LOGO_URL)
    if DIFF_BANNER_URL:
        embed.set_image(url=DIFF_BANNER_URL)
    embed.set_footer(text="Different Meets • Automated Tracking")
    return embed


async def _auto_check_promotion(guild: discord.Guild, member: discord.Member) -> None:
    from datetime import timezone as _tz
    stats = _auto_stats.ensure_user(member.id)
    score = _auto_score(stats)
    meets = (
        stats.get("tickets_handled", 0) >= _PROMOTION_THRESHOLDS["tickets_handled"]
        or stats.get("applications_reviewed", 0) >= _PROMOTION_THRESHOLDS["applications_reviewed"]
        or stats.get("meets_hosted", 0) >= _PROMOTION_THRESHOLDS["meets_hosted"]
        or score >= _PROMOTION_THRESHOLDS["score"]
    )
    if not meets:
        return
    next_role_id = _staff_next_promo_role(member)
    if not next_role_id:
        return
    next_role = guild.get_role(next_role_id)
    if not next_role:
        return
    log_ch = guild.get_channel(STAFF_LOGS_CHANNEL_ID)
    if not isinstance(log_ch, discord.TextChannel):
        return
    now = datetime.now(_tz.utc)
    embed = discord.Embed(
        title="📈 Promotion Suggestion (Auto)",
        description=(
            f"User: {member.mention}\n"
            f"Suggested Next Role: {next_role.mention}\n\n"
            "This staff member reached the automated promotion review threshold."
        ),
        color=discord.Color.green(),
        timestamp=now,
    )
    embed.add_field(name="Tickets Handled", value=str(stats.get("tickets_handled", 0)), inline=True)
    embed.add_field(name="Apps Reviewed", value=str(stats.get("applications_reviewed", 0)), inline=True)
    embed.add_field(name="Meets Hosted", value=str(stats.get("meets_hosted", 0)), inline=True)
    embed.add_field(name="Activity Score", value=str(score), inline=True)
    if DIFF_LOGO_URL:
        embed.set_thumbnail(url=DIFF_LOGO_URL)
    embed.set_footer(text="Different Meets • Automated Tracking")
    try:
        await log_ch.send(embed=embed)
    except discord.HTTPException:
        pass


async def _auto_finalize_ticket(guild: discord.Guild, channel_id: int) -> None:
    from datetime import timezone as _tz
    ticket = _ticket_cache.pop_ticket(channel_id)
    if not ticket:
        return
    ticket_type = ticket.get("ticket_type", "support")
    staff_messages: dict = ticket.get("staff_messages", {})
    awarded: list[tuple[discord.Member, int]] = []

    for uid_str, count in staff_messages.items():
        if int(count) < _AUTO_MIN_MSG_TO_COUNT:
            continue
        m = guild.get_member(int(uid_str))
        if not m:
            continue
        _auto_stats.add_stat(int(uid_str), "messages_in_tickets", int(count))
        _auto_stats.add_stat(int(uid_str), "tickets_handled", 1)
        if ticket_type == "report":
            _auto_stats.add_stat(int(uid_str), "reports_resolved", 1)
        elif ticket_type == "appeal":
            _auto_stats.add_stat(int(uid_str), "appeals_reviewed", 1)
        awarded.append((m, int(count)))
        await _auto_check_promotion(guild, m)

    if awarded:
        now = datetime.now(_tz.utc)
        lines = [f"{m.mention} — {cnt} message(s)" for m, cnt in awarded]
        embed = discord.Embed(
            title="🎫 Ticket Auto Tracking Complete",
            description=(
                f"Ticket: `{ticket.get('channel_name', 'unknown')}`\n"
                f"Type: **{ticket_type}**\n"
                "Tracked Staff:\n" + "\n".join(lines)
            ),
            color=discord.Color.blurple(),
            timestamp=now,
        )
        if DIFF_LOGO_URL:
            embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.set_footer(text="Different Meets • Automated Tracking")
        log_ch = guild.get_channel(STAFF_LOGS_CHANNEL_ID)
        if isinstance(log_ch, discord.TextChannel):
            try:
                await log_ch.send(embed=embed)
            except discord.HTTPException:
                pass


def _auto_seconds_until_weekly() -> float:
    from datetime import timezone as _tz, timedelta as _td
    now = datetime.now(_tz.utc)
    target = now.replace(hour=_AUTO_WEEKLY_HOUR_UTC, minute=_AUTO_WEEKLY_MINUTE_UTC, second=0, microsecond=0)
    days_ahead = (_AUTO_WEEKLY_WEEKDAY - now.weekday()) % 7
    if days_ahead == 0 and target <= now:
        days_ahead = 7
    target = target + _td(days=days_ahead)
    return max((target - now).total_seconds(), 30.0)


async def _auto_weekly_loop() -> None:
    from datetime import timezone as _tz
    await bot.wait_until_ready()
    while not bot.is_closed():
        await asyncio.sleep(_auto_seconds_until_weekly())
        guild = bot.get_guild(GUILD_ID)
        if guild is None:
            continue
        report_channel = guild.get_channel(LEADERBOARD_CHANNEL_ID)
        rows = _auto_stats.leaderboard()
        if isinstance(report_channel, discord.TextChannel):
            try:
                await report_channel.send(embed=_auto_build_weekly_embed(guild, rows))
            except discord.HTTPException:
                pass
            try:
                lb_embed = build_leaderboard_embed(guild)
                notify_role = guild.get_role(NOTIFY_ROLE_ID)
                content = notify_role.mention if notify_role else None
                await report_channel.send(content=content, embed=lb_embed, view=LeaderboardView())
            except discord.HTTPException:
                pass
            try:
                hub_embed = _build_crew_hub_embed()
                state = _load_diff_json(CREW_HUB_STATE_FILE) or {}
                msg_id = state.get("message_id")
                ch_id = state.get("channel_id")
                if msg_id and ch_id:
                    ch = guild.get_channel(ch_id)
                    if isinstance(ch, discord.TextChannel):
                        try:
                            existing = await ch.fetch_message(msg_id)
                            await existing.edit(embed=hub_embed, view=CrewHubView())
                        except discord.NotFound:
                            pass
            except Exception:
                pass
        for entry in _rsvp_leaderboard.values():
            entry["last_attendance_count"] = int(entry.get("attendance_count", 0))
        _rsvp_save_all()

        _auto_stats.archive_and_reset()
        now = datetime.now(_tz.utc)
        log_ch = guild.get_channel(STAFF_LOGS_CHANNEL_ID)
        if isinstance(log_ch, discord.TextChannel):
            try:
                reset_embed = discord.Embed(
                    title="🔄 Weekly Staff Stats Reset",
                    description=f"Weekly report posted and stats reset at <t:{int(now.timestamp())}:F>",
                    color=discord.Color.orange(),
                    timestamp=now,
                )
                reset_embed.set_footer(text="Different Meets • Automated Tracking")
                await log_ch.send(embed=reset_embed)
            except discord.HTTPException:
                pass


@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    before_ids = {r.id for r in before.roles}
    after_ids = {r.id for r in after.roles}
    if HOST_ROLE_ID not in before_ids and HOST_ROLE_ID in after_ids:
        if _hauto_db.is_blacklisted(after.guild.id, after.id):
            host_role = after.guild.get_role(HOST_ROLE_ID)
            if host_role:
                try:
                    await after.remove_roles(host_role, reason="Blacklisted user cannot hold the host role")
                except Exception:
                    return
                entry = _hauto_db.get_active_entry(after.guild.id, after.id)
                embed = discord.Embed(
                    title="⛔ Host Role Auto-Removed",
                    description="A blacklisted user was automatically prevented from holding the host role.",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow(),
                )
                embed.add_field(name="User", value=after.mention, inline=False)
                if entry:
                    embed.add_field(name="Blacklist Entry", value=f"#{entry['id']}", inline=True)
                    embed.add_field(name="Severity", value=entry["severity"], inline=True)
                log_ch = after.guild.get_channel(STAFF_LOGS_CHANNEL_ID)
                if isinstance(log_ch, discord.TextChannel):
                    try:
                        await log_ch.send(embed=embed)
                    except Exception:
                        pass


@bot.event
async def on_message(message: discord.Message) -> None:
    await bot.process_commands(message)

    if not message.guild or message.author.bot:
        return
    if not isinstance(message.author, discord.Member):
        return
    if not isinstance(message.channel, discord.TextChannel):
        return

    # --- Instagram auto-post ---
    if message.channel.id == _IG_CHANNEL_ID:
        _ig_m = _IG_LINK_RE.search(message.content)
        if _ig_m:
            await _ig_handle_drop(message.channel, _ig_m.group(1))
        return

    # --- Join channel photo progress tracking ---
    topic = message.channel.topic
    join_user_id = _join_parse_user_id(topic)
    if join_user_id and str(message.author.id) == join_user_id:
        raw_images = [a for a in message.attachments if a.content_type and a.content_type.startswith("image/")]
        if raw_images:
            spam_ignored = max(0, len(raw_images) - 5)
            candidates = raw_images[:5]

            photo_hashes = _photo_hashes_load()
            user_hashes: list = photo_hashes.setdefault(join_user_id, [])
            accepted = 0
            dupes = 0
            for att in candidates:
                h = _attachment_hash(att)
                if h in user_hashes:
                    dupes += 1
                else:
                    user_hashes.append(h)
                    accepted += 1
            _photo_hashes_save(photo_hashes)

            history = [m async for m in message.channel.history(limit=200)]
            total_images = sum(
                len([a for a in m.attachments if a.content_type and a.content_type.startswith("image/")])
                for m in history
                if m.author.id == message.author.id
            )
            prev_total = total_images - len(raw_images)
            capped = min(total_images, MIN_GARAGE_PHOTOS)

            filled   = min(capped, MIN_GARAGE_PHOTOS)
            empty    = MIN_GARAGE_PHOTOS - filled
            bar      = "🟦" * filled + "⬛" * empty
            complete = capped >= MIN_GARAGE_PHOTOS
            progress_color = discord.Color.green() if complete else discord.Color.blue()

            progress_embed = discord.Embed(
                title = "📸 Photo Progress",
                color = progress_color,
                timestamp = utc_now(),
            )
            progress_embed.add_field(
                name  = f"Progress  {capped}/{MIN_GARAGE_PHOTOS}",
                value = bar,
                inline= False,
            )
            if accepted:
                progress_embed.add_field(name="✅ Accepted", value=str(accepted), inline=True)
            if dupes:
                progress_embed.add_field(name="🔁 Duplicates Ignored", value=str(dupes), inline=True)
            if spam_ignored:
                progress_embed.add_field(name="⚠️ Extra Images (Anti-Spam)", value=str(spam_ignored), inline=True)
            progress_embed.set_footer(text="Different Meets • Photo Review System")
            await message.channel.send(embed=progress_embed)

            if prev_total < MIN_GARAGE_PHOTOS <= total_images:
                leader_role = message.guild.get_role(LEADER_ROLE_ID)
                co_role = message.guild.get_role(CO_LEADER_ROLE_ID)
                mgr_role = message.guild.get_role(MANAGER_ROLE_ID)
                mentions = " ".join(r.mention for r in [leader_role, co_role, mgr_role] if r)

                review_embed = discord.Embed(
                    title       = "✅ Application Ready for Review",
                    description = f"{message.author.mention} has submitted all **{MIN_GARAGE_PHOTOS}** required photos and is ready to be reviewed.",
                    color       = discord.Color.green(),
                    timestamp   = utc_now(),
                )
                review_embed.add_field(name="📸 Valid Photos",  value=f"{capped}/{MIN_GARAGE_PHOTOS}", inline=True)
                review_embed.add_field(name="📋 Channel",       value=message.channel.mention,        inline=True)
                review_embed.set_thumbnail(url=message.author.display_avatar.url)
                review_embed.set_footer(text="Different Meets • Application System")
                await message.channel.send(
                    content=mentions if mentions else None,
                    embed=review_embed,
                    allowed_mentions=discord.AllowedMentions(roles=True),
                )
                log_ch = message.guild.get_channel(STAFF_LOGS_CHANNEL_ID)
                if isinstance(log_ch, discord.TextChannel):
                    try:
                        await log_ch.send(embed=discord.Embed(
                            title="✅ Application Ready For Review",
                            description="\n".join([
                                f"**User:** <@{join_user_id}>",
                                f"**Channel:** {message.channel.mention}",
                                f"**Valid Photos:** {capped}/{MIN_GARAGE_PHOTOS}",
                            ]),
                            color=discord.Color.green(),
                            timestamp=utc_now(),
                        ))
                    except Exception:
                        pass
        return

    # --- Staff ticket message tracking ---
    if not _auto_is_ticket_channel(message.channel):
        return
    if not is_staff_reviewer(message.author):
        return
    ticket_type = _supp_parse_topic(message.channel.topic, "ticket_type") or "support"
    owner_id = _supp_parse_topic(message.channel.topic, "ticket_owner")
    _ticket_cache.add_staff_message(
        channel_id=message.channel.id,
        channel_name=message.channel.name,
        ticket_type=ticket_type,
        owner_id=owner_id,
        user_id=message.author.id,
    )


@bot.event
async def on_guild_channel_delete(channel: discord.abc.GuildChannel) -> None:
    if not isinstance(channel, discord.TextChannel):
        return
    if channel.guild.id != GUILD_ID:
        return
    await _auto_finalize_ticket(channel.guild, channel.id)


@bot.event
async def on_interaction(interaction: discord.Interaction) -> None:
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return
    if interaction.guild.id != GUILD_ID:
        return
    if not interaction.data:
        return
    custom_id = interaction.data.get("custom_id")
    if not isinstance(custom_id, str):
        return
    if not isinstance(interaction.channel, discord.TextChannel):
        return
    if not _auto_is_ticket_channel(interaction.channel):
        return
    if not any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID} for r in interaction.user.roles) \
            and not interaction.user.guild_permissions.manage_guild:
        return
    lowered = custom_id.lower()
    if "accept" not in lowered and "deny" not in lowered:
        return
    _auto_stats.add_stat(interaction.user.id, "applications_reviewed", 1)
    if "accept" in lowered:
        _auto_stats.add_stat(interaction.user.id, "accepted_apps", 1)
        decision = "Approved"
    else:
        _auto_stats.add_stat(interaction.user.id, "denied_apps", 1)
        decision = "Denied"
    from datetime import timezone as _tz
    now = datetime.now(_tz.utc)
    log_ch = interaction.guild.get_channel(STAFF_LOGS_CHANNEL_ID)
    if isinstance(log_ch, discord.TextChannel):
        embed = discord.Embed(
            title="🧾 Application Auto Tracking",
            description=(
                f"Reviewer: {interaction.user.mention}\n"
                f"Decision: **{decision}**\n"
                f"Channel: {interaction.channel.mention}\n"
                f"Time: <t:{int(now.timestamp())}:F>"
            ),
            color=discord.Color.green() if decision == "Approved" else discord.Color.red(),
            timestamp=now,
        )
        if DIFF_LOGO_URL:
            embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.set_footer(text="Different Meets • Automated Tracking")
        try:
            await log_ch.send(embed=embed)
        except discord.HTTPException:
            pass
    await _auto_check_promotion(interaction.guild, interaction.user)


@bot.tree.command(name="auto-staff-stats", description="View automatically tracked staff stats for a member (staff only)")
@app_commands.describe(member="The staff member to look up")
async def auto_staff_stats(interaction: discord.Interaction, member: discord.Member) -> None:
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return await interaction.response.send_message("Server only.", ephemeral=True)
    if not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    stats = _auto_stats.ensure_user(member.id)
    from datetime import timezone as _tz
    embed = discord.Embed(
        title="📊 DIFF Auto Tracking Snapshot",
        description=f"Automatically tracked stats for {member.mention}",
        color=discord.Color.blue(),
        timestamp=datetime.now(_tz.utc),
    )
    embed.add_field(name="Tickets Handled", value=str(stats.get("tickets_handled", 0)), inline=True)
    embed.add_field(name="Apps Reviewed", value=str(stats.get("applications_reviewed", 0)), inline=True)
    embed.add_field(name="Meets Hosted", value=str(stats.get("meets_hosted", 0)), inline=True)
    embed.add_field(name="Reports Resolved", value=str(stats.get("reports_resolved", 0)), inline=True)
    embed.add_field(name="Appeals Reviewed", value=str(stats.get("appeals_reviewed", 0)), inline=True)
    embed.add_field(name="Messages in Tickets", value=str(stats.get("messages_in_tickets", 0)), inline=True)
    embed.add_field(name="Accepted Apps", value=str(stats.get("accepted_apps", 0)), inline=True)
    embed.add_field(name="Denied Apps", value=str(stats.get("denied_apps", 0)), inline=True)
    embed.add_field(name="Score", value=str(_auto_score(stats)), inline=True)
    if DIFF_LOGO_URL:
        embed.set_thumbnail(url=DIFF_LOGO_URL)
    embed.set_footer(text="Different Meets • Automated Tracking")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="force-weekly-staff-report", description="Force post the weekly staff report and reset stats (leadership only)")
async def force_weekly_staff_report(interaction: discord.Interaction) -> None:
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return await interaction.response.send_message("Server only.", ephemeral=True)
    if not any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID} for r in interaction.user.roles) \
            and not interaction.user.guild_permissions.manage_guild:
        return await interaction.response.send_message("Leadership only.", ephemeral=True)
    report_channel = interaction.guild.get_channel(LEADERBOARD_CHANNEL_ID)
    if not isinstance(report_channel, discord.TextChannel):
        return await interaction.response.send_message("Leaderboard channel not found.", ephemeral=True)
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return
    rows = _auto_stats.leaderboard()
    await report_channel.send(embed=_auto_build_weekly_embed(interaction.guild, rows))
    _auto_stats.archive_and_reset()
    await interaction.followup.send(f"Weekly report posted in {report_channel.mention} and stats reset.", ephemeral=True)


@bot.command(name="clearweeklyreport")
async def clearweeklyreport(ctx: commands.Context):
    """Delete the most recent Weekly DIFF Staff Report from the leaderboard channel (leadership only)."""
    is_leader = any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID} for r in getattr(ctx.author, "roles", [])) \
        or getattr(ctx.author, "guild_permissions", None) and ctx.author.guild_permissions.manage_guild
    if not is_leader:
        return await ctx.send("Leadership only.", delete_after=5)
    channel = ctx.guild.get_channel(LEADERBOARD_CHANNEL_ID) if ctx.guild else None
    if not isinstance(channel, discord.TextChannel):
        return await ctx.send("Leaderboard channel not found.", delete_after=5)
    deleted = False
    async for msg in channel.history(limit=50):
        if msg.author == bot.user and msg.embeds:
            title = msg.embeds[0].title or ""
            if "Weekly DIFF Staff Report" in title:
                try:
                    await msg.delete()
                    deleted = True
                except Exception:
                    pass
                break
    if deleted:
        await ctx.send("Weekly report message deleted.", delete_after=5)
    else:
        await ctx.send("No recent weekly report message found in the leaderboard channel.", delete_after=5)
    try:
        await ctx.message.delete()
    except Exception:
        pass


@bot.tree.command(name="auto-add-meet-host", description="Add hosted meet stats to a staff member (leadership only)")
@app_commands.describe(member="Staff member to update", amount="Number of meets to add (default 1)")
async def auto_add_meet_host(interaction: discord.Interaction, member: discord.Member, amount: app_commands.Range[int, 1, 20] = 1) -> None:
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return await interaction.response.send_message("Server only.", ephemeral=True)
    if not any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID} for r in interaction.user.roles) \
            and not interaction.user.guild_permissions.manage_guild:
        return await interaction.response.send_message("Leadership only.", ephemeral=True)
    _auto_stats.add_stat(member.id, "meets_hosted", amount)
    await _auto_check_promotion(interaction.guild, member)
    await interaction.response.send_message(f"Added **{amount}** hosted meet(s) to {member.mention}.", ephemeral=True)


@bot.tree.command(name="post-auto-staff-leaderboard", description="Post the current automated staff leaderboard (leadership only)")
async def post_auto_staff_leaderboard(interaction: discord.Interaction) -> None:
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return await interaction.response.send_message("Server only.", ephemeral=True)
    if not any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID} for r in interaction.user.roles) \
            and not interaction.user.guild_permissions.manage_guild:
        return await interaction.response.send_message("Leadership only.", ephemeral=True)
    lb_channel = interaction.guild.get_channel(LEADERBOARD_CHANNEL_ID)
    if not isinstance(lb_channel, discord.TextChannel):
        return await interaction.response.send_message("Leaderboard channel not found.", ephemeral=True)
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return
    await lb_channel.send(embed=_auto_build_weekly_embed(interaction.guild, _auto_stats.leaderboard()))
    await interaction.followup.send(f"Auto leaderboard posted in {lb_channel.mention}.", ephemeral=True)


# =========================
# DIFF JOIN HUB — PLATFORM SELECT + TICKET SYSTEM (V2)
# =========================

_JOIN_MMI_INVITE = "https://discord.gg/mmi"
_JOIN_STAFF_ROLE_IDS = {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID, HOST_ROLE_ID}


def _join_is_staff(member: discord.Member) -> bool:
    return any(r.id in _JOIN_STAFF_ROLE_IDS for r in member.roles)


def _join_parse_user_id(topic: str | None) -> str | None:
    if not topic or "JOIN_USER:" not in topic:
        return None
    try:
        return topic.split("JOIN_USER:")[1].split()[0].strip()
    except IndexError:
        return None


def _join_parse_psn(topic: str | None) -> str:
    if not topic or "PSN:" not in topic:
        return "Unknown"
    try:
        raw = topic.split("PSN:")[1]
        return raw.split("|")[0].strip() or "Unknown"
    except IndexError:
        return "Unknown"


def _join_sanitize_psn(text: str) -> str:
    return text.strip().replace("\n", "").replace("\r", "")[:28]


def _join_sanitize_channel_name(psn: str) -> str:
    safe = "".join(c if c.isalnum() or c == "-" else "-" for c in psn.lower())
    safe = "-".join(p for p in safe.split("-") if p)
    return f"join-{safe}"[:90] or "join-ps"


def _join_build_panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🏁 DIFF MEETS — OFFICIAL JOIN HUB",
        description="\n".join([
            "👋 **Select your platform** below to join our GTA car meets.",
            "",
            "**Attention**",
            "🚗 Only clean customized vehicles are allowed at our meets.",
            "",
            "**Crew**",
            "🤝 If you also want to join the crew, head to your crew application area after getting set up.",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━",
            "🎮 **PlayStation** — Enter your PSN and open a private join ticket",
            "🟢 **Xbox** — Redirects to our partners at **MMI Meets**",
            "💻 **PC** — Redirects to our partners at **MMI Meets**",
            "━━━━━━━━━━━━━━━━━━━━━━",
        ]),
        color=discord.Color.from_str("#111111"),
    )
    if DIFF_LOGO_URL:
        embed.set_thumbnail(url=DIFF_LOGO_URL)
    if DIFF_BANNER_URL:
        embed.set_image(url=DIFF_BANNER_URL)
    embed.set_footer(text="Different Meets • PlayStation GTA Car Meets")
    return embed


def _join_build_ticket_embed(member: discord.Member, psn_name: str = "", nickname_status: str = "") -> discord.Embed:
    lines = [f"{member.mention}, your PSN name has been submitted.", ""]
    if psn_name:
        lines.append(f"**PSN Name:** {psn_name}")
    if nickname_status:
        lines.append(f"**Nickname Status:** {nickname_status}")
    lines += [
        "",
        "**Now only do this:**",
        "• Send **10 car photos** showing your builds",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━",
        "✅ Staff can review using the buttons below.",
        "🔒 When finished, staff can close the ticket.",
    ]
    embed = discord.Embed(
        title="🎮 PlayStation Join Application",
        description="\n".join(lines),
        color=discord.Color.from_str("#111111"),
    )
    if DIFF_LOGO_URL:
        embed.set_thumbnail(url=DIFF_LOGO_URL)
    embed.set_footer(text="Different Meets • PlayStation GTA Car Meets")
    return embed


async def _join_build_transcript(channel: discord.TextChannel) -> discord.File:
    lines: list[str] = []
    async for msg in channel.history(limit=200, oldest_first=True):
        ts = msg.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        content = (msg.content or "").replace("\n", " ").strip()
        attachments = (
            " [Attachments: " + ", ".join(a.url for a in msg.attachments) + "]"
            if msg.attachments else ""
        )
        lines.append(f"[{ts}] {msg.author} ({msg.author.id}): {content}{attachments}")
    header = (
        f"Transcript for #{channel.name}\n"
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        f"{'=' * 52}\n\n"
    )
    buf = io.BytesIO((header + "\n".join(lines)).encode("utf-8"))
    return discord.File(buf, filename=f"{channel.name[:80]}-transcript.txt")


class JoinPlatformSelect(discord.ui.Select):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Select your platform to get started...",
            min_values=1,
            max_values=1,
            custom_id="diff_join_platform_select",
            options=[
                discord.SelectOption(
                    label="PlayStation",
                    value="playstation",
                    description="Enter PSN, get renamed, then open a ticket",
                    emoji="🎮",
                ),
                discord.SelectOption(
                    label="Xbox",
                    value="xbox",
                    description="Join our partners on Xbox Series X|S",
                    emoji="🟢",
                ),
                discord.SelectOption(
                    label="PC",
                    value="pc",
                    description="Join our partners on PC",
                    emoji="💻",
                ),
            ],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("This can only be used inside the server.", ephemeral=True)

        platform = self.values[0]

        if platform in ("xbox", "pc"):
            label = "Xbox Series X|S" if platform == "xbox" else "PC"
            embed = discord.Embed(
                title="🟢 Xbox Join Info" if platform == "xbox" else "💻 PC Join Info",
                description="\n".join([
                    f"Your {label} car meets are handled via our partner **MMI Meets**.",
                    "",
                    "**Join their server for more information:**",
                    _JOIN_MMI_INVITE,
                    "",
                    "Then go to **#join-car-meet**.",
                ]),
                color=discord.Color.from_str("#111111"),
            )
            if DIFF_LOGO_URL:
                embed.set_thumbnail(url=DIFF_LOGO_URL)
            embed.set_footer(text="Different Meets • PlayStation Only")
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        category = interaction.guild.get_channel(JOIN_TICKET_CATEGORY_ID)
        if not isinstance(category, discord.CategoryChannel):
            return await interaction.response.send_message(
                "Join ticket category is not configured. Please contact staff.", ephemeral=True
            )

        for ch in category.text_channels:
            if ch.topic and f"JOIN_USER:{interaction.user.id}" in ch.topic:
                return await interaction.response.send_message(
                    f"You already have an open join ticket: {ch.mention}", ephemeral=True
                )

        await interaction.response.send_modal(JoinPsnModal())


class JoinPsnModal(discord.ui.Modal, title="PlayStation Join"):
    psn_name = discord.ui.TextInput(
        label="Enter your PSN name",
        placeholder="Example: Frostyy2003",
        required=True,
        max_length=28,
        min_length=2,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Server only.", ephemeral=True)

        clean_psn = _join_sanitize_psn(str(self.psn_name))

        try:
            await interaction.response.defer(ephemeral=True)
        except discord.NotFound:
            return

        nickname_status: str
        target_nick = f"🅸🅳 - {clean_psn}"
        try:
            if interaction.user.top_role < interaction.guild.me.top_role:
                await interaction.user.edit(nick=target_nick, reason="DIFF join system PSN name sync")
                nickname_status = f"Changed to {target_nick}"
            else:
                nickname_status = "Could not change nickname automatically (role hierarchy)"
        except discord.Forbidden:
            nickname_status = "Could not change nickname automatically (missing Manage Nicknames)"
        except discord.HTTPException:
            nickname_status = "Nickname change failed"

        category = interaction.guild.get_channel(JOIN_TICKET_CATEGORY_ID)
        if not isinstance(category, discord.CategoryChannel):
            return await interaction.followup.send(
                "Join ticket category is not configured. Please contact staff.", ephemeral=True
            )

        overwrites: dict = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True, send_messages=True,
                read_message_history=True, attach_files=True, embed_links=True,
            ),
        }
        me = interaction.guild.me
        if me:
            overwrites[me] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True,
                read_message_history=True, manage_channels=True,
                manage_messages=True, attach_files=True, embed_links=True,
            )
        for role_id in _JOIN_STAFF_ROLE_IDS:
            role = interaction.guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True,
                    read_message_history=True, manage_messages=True,
                    attach_files=True, embed_links=True,
                )

        channel = await interaction.guild.create_text_channel(
            name=_join_sanitize_channel_name(clean_psn),
            category=category,
            overwrites=overwrites,
            topic=f"DIFF PlayStation Join Application | JOIN_USER:{interaction.user.id} | PSN:{clean_psn}",
            reason=f"PS Join ticket opened by {interaction.user} ({interaction.user.id})",
        )

        ping_parts = [interaction.user.mention]
        for rid in (LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID):
            r = interaction.guild.get_role(rid)
            if r:
                ping_parts.append(r.mention)
        await channel.send(
            content=" ".join(ping_parts),
            embed=_join_build_ticket_embed(interaction.user, psn_name=clean_psn, nickname_status=nickname_status),
            view=JoinTicketView(),
            allowed_mentions=discord.AllowedMentions(roles=True, users=True),
        )

        from datetime import timezone as _tz
        logs_channel = interaction.guild.get_channel(STAFF_LOGS_CHANNEL_ID)
        if isinstance(logs_channel, discord.TextChannel):
            log_embed = discord.Embed(
                title="📥 New Join Application",
                description="\n".join([
                    f"**User:** {interaction.user.mention}",
                    f"**Platform:** PlayStation",
                    f"**PSN:** {clean_psn}",
                    f"**Ticket:** {channel.mention}",
                    f"**Nickname Status:** {nickname_status}",
                    f"**Status:** Pending Review",
                ]),
                color=discord.Color.gold(),
                timestamp=datetime.now(_tz.utc),
            )
            if DIFF_LOGO_URL:
                log_embed.set_thumbnail(url=DIFF_LOGO_URL)
            log_embed.set_footer(text="Different Meets • Join Hub")
            try:
                await logs_channel.send(embed=log_embed)
            except discord.HTTPException:
                pass

        await interaction.followup.send(
            f"Your PlayStation join ticket has been created: {channel.mention}\n"
            "Please send your **10 car photos** and a staff member will review you shortly.",
            ephemeral=True,
        )


class JoinPlatformView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.add_item(JoinPlatformSelect())

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        traceback.print_exception(type(error), error, error.__traceback__)
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
            else:
                await interaction.followup.send("Something went wrong. Please try again.", ephemeral=True)
        except Exception:
            pass

    @discord.ui.button(
        label="🔔 Notify Me For Meets",
        style=discord.ButtonStyle.primary,
        custom_id="diff_join_notify",
        row=1,
    )
    async def notify_toggle(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Server only.", ephemeral=True)
        role = interaction.guild.get_role(NOTIFY_ROLE_ID)
        if not role:
            return await interaction.response.send_message("Notify role not found. Please contact staff.", ephemeral=True)
        if role in interaction.user.roles:
            try:
                await interaction.user.remove_roles(role, reason="DIFF notify toggle — OFF")
            except discord.HTTPException:
                return await interaction.response.send_message("Failed to remove role. Try again.", ephemeral=True)
            await interaction.response.send_message("🔕 Meet notifications **OFF** — you've been removed from the notify role.", ephemeral=True)
        else:
            try:
                await interaction.user.add_roles(role, reason="DIFF notify toggle — ON")
            except discord.HTTPException:
                return await interaction.response.send_message("Failed to add role. Try again.", ephemeral=True)
            await interaction.response.send_message("🔔 Meet notifications **ON** — you'll be pinged for meets.", ephemeral=True)


class JoinTicketView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        traceback.print_exception(type(error), error, error.__traceback__)
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
            else:
                await interaction.followup.send("Something went wrong. Please try again.", ephemeral=True)
        except Exception:
            pass

    def _staff_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return False
        return _join_is_staff(interaction.user)

    @discord.ui.button(label="Accept", emoji="✅", style=discord.ButtonStyle.success, custom_id="diff_join_accept")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not self._staff_check(interaction):
            return await interaction.response.send_message("Only Leader / Co-Leader / Manager can use this button.", ephemeral=True)
        if not isinstance(interaction.channel, discord.TextChannel):
            return await interaction.response.send_message("Channel error.", ephemeral=True)
        uid_raw = _join_parse_user_id(interaction.channel.topic)
        if not uid_raw or not uid_raw.isdigit():
            return await interaction.response.send_message("Could not find the applicant for this ticket.", ephemeral=True)
        member = interaction.guild.get_member(int(uid_raw))
        if not member:
            try:
                member = await interaction.guild.fetch_member(int(uid_raw))
            except discord.HTTPException:
                member = None
        if member is None:
            return await interaction.response.send_message("That user is no longer in the server.", ephemeral=True)

        psn = _join_parse_psn(interaction.channel.topic)

        await interaction.response.send_message(f"{member.mention} has been accepted.", ephemeral=True)

        roles_to_add = []
        for rid in (PS5_ROLE_ID, MEET_ATTENDER_ROLE_ID, VERIFIED_ROLE_ID):
            r = interaction.guild.get_role(rid)
            if r:
                roles_to_add.append(r)
        if roles_to_add:
            try:
                await member.add_roles(*roles_to_add, reason=f"PS join approved by {interaction.user}")
            except discord.HTTPException:
                pass
        unverified_role = interaction.guild.get_role(UNVERIFIED_ROLE_ID)
        if unverified_role and unverified_role in member.roles:
            try:
                await member.remove_roles(unverified_role, reason="PS join approved — removing unverified")
            except discord.HTTPException:
                pass
        role = interaction.guild.get_role(PS5_ROLE_ID)

        for ch_id in _JOIN_UNLOCK_CHANNEL_IDS:
            ch = interaction.guild.get_channel(ch_id)
            if isinstance(ch, discord.TextChannel):
                try:
                    await ch.set_permissions(member, view_channel=True, reason="DIFF join approved")
                except discord.HTTPException:
                    pass

        welcome_channel = interaction.guild.get_channel(JOIN_WELCOME_CHANNEL_ID)
        if isinstance(welcome_channel, discord.TextChannel):
            welcome_embed = discord.Embed(
                title="Welcome to DIFF Meets",
                description="\n".join([
                    f"{member.mention} has joined the DIFF car meet community.",
                    "",
                    f"**PSN:** {psn}",
                    "Stay ready for meet posts, announcements, and instructions.",
                ]),
                color=discord.Color.green(),
            )
            if DIFF_BANNER_URL:
                welcome_embed.set_image(url=DIFF_BANNER_URL)
            if DIFF_LOGO_URL:
                welcome_embed.set_thumbnail(url=DIFF_LOGO_URL)
            welcome_embed.set_footer(text="Different Meets • PlayStation GTA Car Meets")
            try:
                await welcome_channel.send(content=member.mention, embed=welcome_embed)
            except discord.HTTPException:
                pass

        from datetime import timezone as _tz
        now = datetime.now(_tz.utc)
        approve_embed = discord.Embed(
            title="✅ Application Accepted",
            description="\n".join([
                f"{member.mention}, your PlayStation join application has been **approved**.",
                "",
                f"**PSN:** {psn}",
                "Welcome to DIFF Meets.",
                "Stay ready for meet posts, announcements, and instructions.",
            ]),
            color=discord.Color.green(),
            timestamp=now,
        )
        if DIFF_LOGO_URL:
            approve_embed.set_thumbnail(url=DIFF_LOGO_URL)
        approve_embed.set_footer(text="Different Meets • PlayStation GTA Car Meets")
        await interaction.channel.send(embed=approve_embed)

        try:
            await member.send(embed=discord.Embed(
                title="✅ You were accepted into DIFF Meets",
                description="\n".join([
                    f"**PSN:** {psn}",
                    "Your PlayStation join application was approved.",
                    "",
                    "Welcome in.",
                    "Keep your builds clean and stay ready for meet updates.",
                ]),
                color=discord.Color.green(),
            ))
        except discord.HTTPException:
            pass

        logs_channel = interaction.guild.get_channel(STAFF_LOGS_CHANNEL_ID)
        if isinstance(logs_channel, discord.TextChannel):
            log_embed = discord.Embed(
                title="✅ Join Application Accepted",
                description="\n".join([
                    f"**User:** {member.mention}",
                    f"**PSN:** {psn}",
                    f"**Reviewed by:** {interaction.user.mention}",
                    f"**Ticket:** {interaction.channel.mention}",
                    f"**Role Added:** {role.mention if role else 'Not configured'}",
                ]),
                color=discord.Color.green(),
                timestamp=now,
            )
            if DIFF_LOGO_URL:
                log_embed.set_thumbnail(url=DIFF_LOGO_URL)
            log_embed.set_footer(text="Different Meets • Join Hub")
            try:
                await logs_channel.send(embed=log_embed)
            except discord.HTTPException:
                pass

        for child in self.children:
            child.disabled = True
        try:
            await interaction.message.edit(view=self)
        except discord.HTTPException:
            pass

        await asyncio.sleep(5)
        try:
            await interaction.channel.delete(reason=f"Join application accepted by {interaction.user}")
        except discord.HTTPException:
            pass

    @discord.ui.button(label="Deny", emoji="❌", style=discord.ButtonStyle.danger, custom_id="diff_join_deny")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not self._staff_check(interaction):
            return await interaction.response.send_message("Only Leader / Co-Leader / Manager can use this button.", ephemeral=True)
        if not isinstance(interaction.channel, discord.TextChannel):
            return await interaction.response.send_message("Channel error.", ephemeral=True)
        uid_raw = _join_parse_user_id(interaction.channel.topic)
        if not uid_raw or not uid_raw.isdigit():
            return await interaction.response.send_message("Could not find the applicant for this ticket.", ephemeral=True)

        member = interaction.guild.get_member(int(uid_raw))
        if not member:
            try:
                member = await interaction.guild.fetch_member(int(uid_raw))
            except discord.HTTPException:
                member = None

        psn = _join_parse_psn(interaction.channel.topic)

        await interaction.response.send_message(
            f"Application denied.{f' {member.mention} was notified by DM.' if member else ''}",
            ephemeral=True,
        )

        if member:
            try:
                await member.send(embed=discord.Embed(
                    title="❌ DIFF Join Application Update",
                    description="\n".join([
                        f"**PSN:** {psn}",
                        "Your PlayStation join application was not accepted at this time.",
                        "",
                        "You can improve your builds, presentation, or application details and apply again later.",
                    ]),
                    color=discord.Color.red(),
                ))
            except discord.HTTPException:
                pass

        from datetime import timezone as _tz
        now = datetime.now(_tz.utc)
        deny_embed = discord.Embed(
            title="❌ Application Denied",
            description="\n".join([
                f"{member.mention if member else f'<@{uid_raw}>'}, your PlayStation join application was **denied** at this time.",
                f"**PSN:** {psn}",
                "",
                "You may improve your builds and reapply in the future.",
            ]),
            color=discord.Color.red(),
            timestamp=now,
        )
        if DIFF_LOGO_URL:
            deny_embed.set_thumbnail(url=DIFF_LOGO_URL)
        deny_embed.set_footer(text="Different Meets • PlayStation GTA Car Meets")
        await interaction.channel.send(embed=deny_embed)

        logs_channel = interaction.guild.get_channel(STAFF_LOGS_CHANNEL_ID)
        if isinstance(logs_channel, discord.TextChannel):
            log_embed = discord.Embed(
                title="❌ Join Application Denied",
                description="\n".join([
                    f"**User:** {member.mention if member else f'<@{uid_raw}>'}",
                    f"**PSN:** {psn}",
                    f"**Reviewed by:** {interaction.user.mention}",
                    f"**Ticket:** {interaction.channel.mention}",
                ]),
                color=discord.Color.red(),
                timestamp=now,
            )
            if DIFF_LOGO_URL:
                log_embed.set_thumbnail(url=DIFF_LOGO_URL)
            log_embed.set_footer(text="Different Meets • Join Hub")
            try:
                await logs_channel.send(embed=log_embed)
            except discord.HTTPException:
                pass

        for child in self.children:
            child.disabled = True
        try:
            await interaction.message.edit(view=self)
        except discord.HTTPException:
            pass

        await asyncio.sleep(5)
        try:
            await interaction.channel.delete(reason=f"Join application denied by {interaction.user}")
        except discord.HTTPException:
            pass

    @discord.ui.button(label="Close Ticket", emoji="🔒", style=discord.ButtonStyle.secondary, custom_id="diff_join_close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not self._staff_check(interaction):
            return await interaction.response.send_message("Only Leader / Co-Leader / Manager can close this ticket.", ephemeral=True)
        if not isinstance(interaction.channel, discord.TextChannel):
            return await interaction.response.send_message("Channel error.", ephemeral=True)

        await interaction.response.send_message("Closing ticket and saving transcript...", ephemeral=True)

        transcript_file: discord.File | None = None
        try:
            transcript_file = await _join_build_transcript(interaction.channel)
        except Exception:
            pass

        from datetime import timezone as _tz
        now = datetime.now(_tz.utc)
        logs_channel = interaction.guild.get_channel(STAFF_LOGS_CHANNEL_ID)
        if isinstance(logs_channel, discord.TextChannel):
            close_embed = discord.Embed(
                title="🔒 Join Ticket Closed",
                description="\n".join([
                    f"**Channel:** {interaction.channel.name}",
                    f"**Closed by:** {interaction.user.mention}",
                    f"**Ticket Topic:** {interaction.channel.topic or 'No topic set'}",
                ]),
                color=discord.Color.greyple(),
                timestamp=now,
            )
            if DIFF_LOGO_URL:
                close_embed.set_thumbnail(url=DIFF_LOGO_URL)
            close_embed.set_footer(text="Different Meets • Join Hub")
            try:
                if transcript_file:
                    await logs_channel.send(embed=close_embed, file=transcript_file)
                else:
                    await logs_channel.send(embed=close_embed)
            except discord.HTTPException:
                pass

        await asyncio.sleep(2.5)
        try:
            await interaction.channel.delete(reason=f"Join ticket closed by {interaction.user}")
        except discord.HTTPException:
            pass


@bot.tree.command(name="post-join-panel", description="Post the DIFF Join Hub platform selector panel (staff only)")
async def post_join_panel(interaction: discord.Interaction) -> None:
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return await interaction.response.send_message("Server only.", ephemeral=True)
    if not any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID, HOST_ROLE_ID} for r in interaction.user.roles) \
            and not interaction.user.guild_permissions.manage_guild:
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    channel = interaction.guild.get_channel(JOIN_PANEL_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        return await interaction.response.send_message("Join panel channel not found.", ephemeral=True)
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return
    try:
        async for msg in channel.history(limit=30):
            if msg.author.id == bot.user.id and any(e.title and "JOIN HUB" in e.title.upper() for e in msg.embeds):
                try:
                    await msg.delete()
                except discord.HTTPException:
                    pass
    except discord.HTTPException:
        pass
    await channel.send(embed=_join_build_panel_embed(), view=JoinPlatformView())
    await interaction.followup.send(f"Join Hub panel posted in {channel.mention}.", ephemeral=True)


@bot.tree.command(name="refresh-join-panel", description="Refresh the DIFF Join Hub panel in place, or repost it if missing (staff only)")
async def refresh_join_panel(interaction: discord.Interaction) -> None:
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return await interaction.response.send_message("Server only.", ephemeral=True)
    if not any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID, HOST_ROLE_ID} for r in interaction.user.roles) \
            and not interaction.user.guild_permissions.manage_guild:
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    channel = interaction.guild.get_channel(JOIN_PANEL_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        return await interaction.response.send_message("Join panel channel not found.", ephemeral=True)
    try:
        await interaction.response.defer(ephemeral=True)
    except discord.NotFound:
        return
    existing: discord.Message | None = None
    try:
        async for msg in channel.history(limit=30):
            if msg.author.id == bot.user.id and any(e.title and "JOIN HUB" in e.title.upper() for e in msg.embeds):
                existing = msg
                break
    except discord.HTTPException:
        pass
    if existing:
        try:
            await existing.edit(embed=_join_build_panel_embed(), view=JoinPlatformView())
            return await interaction.followup.send(f"Join Hub panel refreshed in {channel.mention}.", ephemeral=True)
        except discord.HTTPException:
            pass
    await channel.send(embed=_join_build_panel_embed(), view=JoinPlatformView())
    await interaction.followup.send(f"Join Hub panel reposted in {channel.mention} (no existing panel found).", ephemeral=True)


# =========================
# WELCOME HUB PANEL
# =========================

_WH_CHANNEL_ID = 1485687906382123331
_WH_STATE_FILE = os.path.join(DATA_FOLDER, "diff_welcome_hub.json")

_SOCIAL_INSTAGRAM = "https://instagram.com/diff_meets?igshid=Y2I2MzMwZWM3ZA=="
_SOCIAL_YOUTUBE   = "https://youtube.com/@DIFF_Meets"
_SOCIAL_TIKTOK    = "https://www.tiktok.com/@different_meets?_t=8iGiQZS9LXR&_r=1"
_SOCIAL_REDDIT    = "https://www.reddit.com/u/DIFF_Meets/s/JzGIrrvZSd"
_SOCIAL_TWITTER   = "https://x.com/diff_meets?s=21"


def _social_build_embed() -> discord.Embed:
    embed = discord.Embed(
        title="📲 DIFF Social Media Hub",
        description=(
            "Stay connected with **Different Meets** beyond the server.\n"
            "Catch event highlights, community features, cinematic recaps, and platform updates."
        ),
        color=discord.Color.from_rgb(20, 20, 20),
    )
    embed.add_field(
        name="🔥 Why Follow?",
        value=(
            "• See photos from recent meets\n"
            "• Get featured — your car could be next 👀\n"
            "• Watch recaps, edits, and event highlights\n"
            "• Stay updated on DIFF posts, drops, and announcements"
        ),
        inline=False,
    )
    embed.add_field(name="📸 Instagram", value="Main platform for event photos, features, and DIFF content.", inline=False)
    embed.add_field(name="🎥 YouTube",   value="Watch event recaps, edits, and longer-form DIFF media.", inline=False)
    embed.add_field(name="🎬 TikTok",    value="Quick clips, shorts, and DIFF highlights.", inline=False)
    embed.add_field(name="💬 Reddit",    value="Community posts, discussions, and extra content.", inline=False)
    embed.add_field(name="🐦 Twitter / X", value="Announcements, updates, and social posts.", inline=False)
    embed.set_footer(text="Follow. Stay active. Get noticed. — Different Meets")
    return embed


class SocialMediaLinksView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Instagram", emoji="📸", style=discord.ButtonStyle.link, url=_SOCIAL_INSTAGRAM, row=0))
        self.add_item(discord.ui.Button(label="YouTube",   emoji="🎥", style=discord.ButtonStyle.link, url=_SOCIAL_YOUTUBE,   row=0))
        self.add_item(discord.ui.Button(label="TikTok",    emoji="🎬", style=discord.ButtonStyle.link, url=_SOCIAL_TIKTOK,    row=0))
        self.add_item(discord.ui.Button(label="Reddit",    emoji="💬", style=discord.ButtonStyle.link, url=_SOCIAL_REDDIT,    row=0))
        self.add_item(discord.ui.Button(label="Twitter / X", emoji="🐦", style=discord.ButtonStyle.link, url=_SOCIAL_TWITTER, row=0))


def _wh_state_load() -> dict:
    try:
        with open(_WH_STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def _wh_state_save(data: dict) -> None:
    try:
        with open(_WH_STATE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def _wh_build_embed() -> discord.Embed:
    embed = discord.Embed(
        title="📍 Welcome to Different Meets (DIFF)",
        color=discord.Color.blue(),
        description=(
            "*The official hub for clean builds, organized meets, and a strong car community.*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🚗 **What is DIFF?**\n"
            "Different Meets (DIFF) is a PS5-based GTA car meet community focused on "
            "**clean, realistic builds**, organized meets, and a respectful environment.\n\n"
            "We host:\n"
            "🎬 Cinematic car meets\n"
            "🏁 Themed events\n"
            "📸 Photoshoots\n"
            "🏆 Competitions & rankings\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📊 **Get Started:**\n"
            "Use the buttons below to navigate the server and get set up.\n\n"
            f"• 📋 **Rules & Requirements** — Know the standards in <#{RULES_CHANNEL_ID}>\n"
            f"• 🚗 **How Meets Work** — Learn how to join & participate\n"
            f"• 📅 **Upcoming Meets** — View the schedule in <#{UPCOMING_MEET_CHANNEL_ID}>\n"
            f"• 🏎️ **Join Crew** — Browse & apply to a crew in <#{CREW_PANEL_CHANNEL_ID}>\n"
            f"• 🎫 **Support** — Get help in <#{SUPPORT_CHANNEL_ID}>\n"
            f"• 📊 **My Stats** — View your personal meet activity\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ **DIFF Standards:**\n"
            "• Clean & realistic builds only\n"
            "• Respect all members\n"
            "• No trolling, griefing, or rice behavior\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "*Stay active, stay consistent, and represent DIFF the right way.*\n\n"
            "— **Different Meets**"
        ),
    )
    embed.set_footer(text="DIFF Welcome Hub")
    return embed


class WelcomeHubView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(
            label="Rules", emoji="📋", style=discord.ButtonStyle.link, row=0,
            url=f"https://discord.com/channels/{GUILD_ID}/{RULES_CHANNEL_ID}",
        ))
        self.add_item(discord.ui.Button(
            label="Schedule", emoji="📅", style=discord.ButtonStyle.link, row=0,
            url=f"https://discord.com/channels/{GUILD_ID}/{UPCOMING_MEET_CHANNEL_ID}",
        ))
        self.add_item(discord.ui.Button(
            label="Support", emoji="🎫", style=discord.ButtonStyle.link, row=0,
            url=f"https://discord.com/channels/{GUILD_ID}/{SUPPORT_CHANNEL_ID}",
        ))
        self.add_item(discord.ui.Button(
            label="Join Crew", emoji="🏎️", style=discord.ButtonStyle.link, row=0,
            url=f"https://discord.com/channels/{GUILD_ID}/{CREW_PANEL_CHANNEL_ID}",
        ))

    @discord.ui.button(label="Social Media", emoji="📲", style=discord.ButtonStyle.secondary,
                       custom_id="diff_wh_social", row=1)
    async def social_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            embed=_social_build_embed(), view=SocialMediaLinksView(), ephemeral=True
        )

    @discord.ui.button(label="How Meets Work", emoji="🚗", style=discord.ButtonStyle.secondary,
                       custom_id="diff_wh_meets", row=1)
    async def meets_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "**🚗 How DIFF Meets Work**\n\n"
            "1. Watch for the meet announcement and schedule.\n"
            "2. Join on time and be ready with a clean vehicle.\n"
            "3. Follow the host's parking and lineup instructions.\n"
            "4. Drive responsibly and represent DIFF properly.\n"
            "5. Enjoy the meet, photos, and community.",
            ephemeral=True,
        )

    @discord.ui.button(label="My Stats", emoji="📊", style=discord.ButtonStyle.secondary,
                       custom_id="diff_wh_stats", row=1)
    async def stats_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = interaction.user.id
        lb_entry = _rsvp_leaderboard.get(str(uid), {})
        att_count  = int(lb_entry.get("attendance_count", 0))
        host_count = int(lb_entry.get("hosted_count", 0))
        om_stats   = _om_stats_load().get("members", {}).get(str(uid), {})
        on_time  = int(om_stats.get("attended", 0))
        late     = int(om_stats.get("late", 0))
        unable   = int(om_stats.get("unable", 0))
        no_show  = int(om_stats.get("no_shows", 0))
        lines = [
            f"**📊 Your DIFF Stats — {interaction.user.display_name}**\n",
            f"🎟️ Meets Attended: **{att_count}**",
            f"🎙️ Meets Hosted: **{host_count}**",
        ]
        if any([on_time, late, unable, no_show]):
            lines += [
                "",
                f"✅ On-Time Check-Ins: **{on_time}**",
                f"🕐 Late Check-Ins: **{late}**",
                f"❌ Unable to Join: **{unable}**",
                f"⚠️ No-Shows: **{no_show}**",
            ]
        await interaction.response.send_message("\n".join(lines), ephemeral=True)

    @discord.ui.button(label="Partnership", emoji="🤝", style=discord.ButtonStyle.primary,
                       custom_id="diff_wh_partnership", row=2)
    async def partnership_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        partners = _pp_get_partners()
        await interaction.response.send_message(
            embed=_pp_build_embed(partners), view=_PartnerHubView(partners), ephemeral=True
        )

    @discord.ui.button(label="Before You Invite Anyone", emoji="🚪", style=discord.ButtonStyle.danger,
                       custom_id="diff_wh_invite", row=2)
    async def invite_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🚪 Before You Invite Anyone",
            description="*This is a required step before sharing DIFF invites.*",
            color=discord.Color.red(),
        )
        embed.add_field(
            name="⚠️ Zero-Tolerance Policy",
            value=(
                "Everyone you invite represents **you**.\n"
                "If they break rules, it reflects directly on you.\n\n"
                "**There are no exceptions.**"
            ),
            inline=False,
        )
        embed.add_field(
            name="📌 What You MUST Do Before Inviting",
            value=(
                "✔️ Make sure your friend understands DIFF standards\n"
                "✔️ Ensure they bring clean, realistic builds\n"
                "✔️ Confirm they are respectful and active\n"
                f"✔️ Have them read the rules FIRST → <#{RULES_CHANNEL_ID}>"
            ),
            inline=False,
        )
        embed.add_field(
            name="🚫 Do NOT Invite",
            value=(
                "• Random players\n"
                "• Trollers / griefers\n"
                "• People who don't follow instructions\n"
                "• Anyone who hasn't read the rules"
            ),
            inline=False,
        )
        embed.add_field(
            name="🔗 Invite Links (Use Responsibly)",
            value=(
                "• https://discord.gg/vYcqNEtksS\n"
                "• https://discord.gg/NTeqDCg74Y\n"
                "• https://discord.gg/diffmeets"
            ),
            inline=False,
        )
        embed.set_footer(text="📊 Invite quality > quantity. Keep DIFF clean.  —  Different Meets Crew 🏁")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        log_ch = interaction.guild.get_channel(STAFF_LOGS_CHANNEL_ID) if interaction.guild else None
        if isinstance(log_ch, discord.TextChannel):
            log_embed = discord.Embed(
                title="🚪 Invite Policy Accessed",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc),
            )
            log_embed.add_field(name="Member", value=f"{interaction.user.mention} (`{interaction.user}`)", inline=False)
            log_embed.set_footer(text="Welcome Hub — Invite Button")
            try:
                await log_ch.send(embed=log_embed)
            except Exception:
                pass


async def _wh_post_or_refresh(guild: discord.Guild) -> None:
    channel = guild.get_channel(_WH_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        try:
            channel = await guild.fetch_channel(_WH_CHANNEL_ID)
        except Exception:
            return
    if not isinstance(channel, discord.TextChannel):
        return
    data = _wh_state_load()
    msg_id = data.get(str(guild.id))
    if msg_id:
        try:
            msg = await channel.fetch_message(int(msg_id))
            await msg.edit(embed=_wh_build_embed(), view=WelcomeHubView())
            return
        except discord.NotFound:
            pass
        except Exception:
            return
    msg = await channel.send(embed=_wh_build_embed(), view=WelcomeHubView())
    data[str(guild.id)] = msg.id
    _wh_state_save(data)


@bot.command(name="welcomehub")
async def _cmd_welcomehub(ctx: commands.Context):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("Admins only.", delete_after=6)
        return
    try:
        await ctx.message.delete()
    except Exception:
        pass
    await _wh_post_or_refresh(ctx.guild)


@bot.command(name="postsocialhub")
async def _cmd_postsocialhub(ctx: commands.Context, channel: discord.TextChannel = None):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("Admins only.", delete_after=6)
        return
    target = channel or ctx.channel
    try:
        await ctx.message.delete()
    except Exception:
        pass
    await target.send(embed=_social_build_embed(), view=SocialMediaLinksView())


# =========================
# PARTNER PANEL (DIRECTORY)
# =========================

_PP_CHANNEL_ID = 1485892421593337926
_PP_FILE       = os.path.join(DATA_FOLDER, "diff_partner_panel.json")
_PP_FOOTER     = "Different Meets • Official Partnership System"

_PP_DEFAULT_PARTNERS: list[dict] = [
    {"name": "MMI Meets",            "short_desc": "PC & Xbox Series S|X meet community.",            "description": "MMI Meets PC & Xbox Series S|X",                                    "invite": "https://discord.gg/mmi",               "platforms": "PC, Xbox Series S|X",          "banner": ""},
    {"name": "San Andreas Roleplay", "short_desc": "Professional and friendly roleplay community.",    "description": "A professional and friendly roleplay community on Xbox and PlayStation.\n\n**Departments:** Highway Patrol, Sheriff, Fire, EMS, Civilian Ops, Comms\n\n**What They Offer:**\n• Daily roleplays\n• Friendly staff\n• CAD system\n• Realistic uniforms & ranks", "invite": "https://discord.gg/bwzCykt9ZS",        "platforms": "Xbox, PlayStation",             "banner": ""},
    {"name": "Los Santos MotorSports","short_desc": "Active multi-platform meet community.",            "description": "**Los Santos MotorSports**\n\n• Daily car meets on all platforms\n• Active staff and chats\n• 1500+ members\n• Weekly photo competitions\n• Giveaways\n• Forza, NFS, Snowrunner meets\n• LSMS merch", "invite": "https://discord.gg/Jf42kGD",           "platforms": "All Platforms",                 "banner": ""},
    {"name": "LS Underground",       "short_desc": "Daily chill car meets and vibes on PlayStation.",  "description": "A very active and engaging community.\n\n• Daily car meets\n• Business lobbies\n• Chill lobbies\n• LFG channels\n• Active staff & giveaways\n• In-house game bot\n• Fully SFW with trained staff", "invite": "https://discord.gg/T5eZpu329K",        "platforms": "PlayStation",                   "banner": ""},
    {"name": "Auto Minded",          "short_desc": "GTAO car enthusiast hub with events and trading.", "description": "A server for GTAO car enthusiasts and car fans.\n\n**Events:**\n• Car meets\n• Racing\n• Rally events\n• Buy/sell & trading\n• Car competitions\n• Server economy",  "invite": "https://discord.gg/autominded",        "platforms": "Xbox (focus), open to all",     "banner": ""},
    {"name": "Civil Network",        "short_desc": "Large roleplay network with multiple departments.","description": "**Platforms:** Xbox New Gen, PS Old Gen, PS New Gen, FiveM\n\n**Departments:** Civilian Ops, Fire/EMS, Dispatch, Military Police, FBI, BCSO, LSPD, PBPD, SASP\n\n• Specialized giveaways\n• 24/7 sessions\n• Professional/friendly staff", "invite": "https://discord.gg/civilrp",           "platforms": "Xbox, PlayStation, FiveM",      "banner": "https://share.creavite.co/DKn05AwFAYa5mCl9.gif"},
    {"name": "RVO",                  "short_desc": "PS5 GTA meet community with daily meets.",         "description": "A chill server to show off your rides and level up your GTA car meet experience.\n\n• Chill community\n• Daily car meets\n• Epic events\n• Media sharing\n• Gaming hub", "invite": "https://discord.gg/rvo",               "platforms": "PS5",                           "banner": ""},
    {"name": "Chop Shop",            "short_desc": "Large GTAO-focused online gaming community.",      "description": "One of the larger active GCTF Discord servers.\n\n• Active members, traders & staff\n• Booster rewards\n• Server currency\n• Clubs that host car meets and lobby drops\n• Always looking for new partners", "invite": "https://discord.gg/YZMbqER2bv",        "platforms": "Multi-game / GTAO",             "banner": ""},
    {"name": "Automotive Union",     "short_desc": "Established events community with multiple titles.","description": "Established in 2018.\n\nHosts GTA events every Friday and Sunday (8–9 PM UK).\n\n**Also on:**\n• Wreckfest\n• GT7\n• Forza Horizon\n• Crew Motorfest",               "invite": "https://discord.gg/kaApne5w4x",        "platforms": "GTA + racing titles",           "banner": ""},
    {"name": "Car Meet Server",      "short_desc": "All-platform car meet and GTAO utility server.",   "description": "• Modded heists (PC)\n• Modded/stock cars\n• Car and photo competitions\n• GTAO inspired bot games",                                                              "invite": "https://discord.gg/zNd2F3sz5U",        "platforms": "All Platforms",                 "banner": ""},
    {"name": "Fast Funds (GTA)",     "short_desc": "Private selling, sourcing, and heist group.",      "description": "**Fast Funds (GTA)**\n\nPrivate selling, sourcing, and heist group. Started recently and growing.",                                                                   "invite": "https://discord.gg/zxEdwZ9M6s",        "platforms": "GTA",                           "banner": ""},
    {"name": "Hurricane's Cars & Chill","short_desc": "PS5-based GTA Online car meet server.",         "description": "A PlayStation 5 GTA Online car meet server.\n\n• Daily car meets\n• Photo competitions\n• Weekly giveaways\n• Game nights\n• Car advice/rating channels\n• New members daily\n• Welcoming community", "invite": "https://discord.gg/CkEXt34waa",        "platforms": "PS5",                           "banner": ""},
]


def _pp_load() -> dict:
    data = _load_diff_json(_PP_FILE) or {}
    if "partners" not in data:
        data["partners"] = _PP_DEFAULT_PARTNERS
        _pp_save(data)
    return data


def _pp_save(data: dict) -> None:
    _save_diff_json(_PP_FILE, data)


def _pp_get_partners() -> list:
    return _pp_load().get("partners", [])


def _pp_build_embed(partners: list) -> discord.Embed:
    embed = discord.Embed(
        title="🤝 DIFF Partnership Hub",
        description=(
            "Explore our official partners below.\n\n"
            "Use the dropdown menu to view each community, their info, and their invite link.\n"
            "This panel is managed by staff and refreshes cleanly without duplicate posts."
        ),
        color=discord.Color.blurple(),
    )
    embed.add_field(name="Current Partners", value=str(len(partners)), inline=True)
    embed.add_field(name="System Status",    value="Active",            inline=True)
    embed.add_field(
        name="How It Works",
        value="Select a partner from the dropdown below to view their information and invite.",
        inline=False,
    )
    embed.set_footer(text=_PP_FOOTER)
    return embed


async def _pp_dropdown_callback(interaction: discord.Interaction, selected: str) -> None:
    partners = _pp_get_partners()
    partner = next((p for p in partners if p["name"] == selected), None)
    if not partner:
        await interaction.response.send_message("Partner not found. Try refreshing the panel.", ephemeral=True)
        return
    embed = discord.Embed(
        title=f"🤝 {partner['name']}",
        description=partner.get("description", "No description provided."),
        color=discord.Color.blue(),
    )
    if partner.get("platforms"):
        embed.add_field(name="Platforms", value=partner["platforms"], inline=False)
    invite = partner.get("invite", "").strip()
    if invite:
        embed.add_field(name="Invite", value=f"[Join Partner]({invite})", inline=False)
    if partner.get("banner"):
        embed.set_image(url=partner["banner"])
    embed.set_footer(text=_PP_FOOTER)
    await interaction.response.send_message(embed=embed, ephemeral=True)


class _PartnerDropdown(discord.ui.Select):
    """Persistent dropdown for the public channel panel."""
    def __init__(self, partners: list) -> None:
        options = [
            discord.SelectOption(label=p["name"][:100], description=p.get("short_desc", "")[:100], value=p["name"], emoji="🤝")
            for p in partners[:25]
        ]
        super().__init__(placeholder="Select a partner to view more info...", min_values=1, max_values=1, options=options, custom_id="diff_partner_select")

    async def callback(self, interaction: discord.Interaction) -> None:
        await _pp_dropdown_callback(interaction, self.values[0])


class _PartnerHubDropdown(discord.ui.Select):
    """Non-persistent dropdown for the Welcome Hub ephemeral popup."""
    def __init__(self, partners: list) -> None:
        options = [
            discord.SelectOption(label=p["name"][:100], description=p.get("short_desc", "")[:100], value=p["name"], emoji="🤝")
            for p in partners[:25]
        ]
        super().__init__(placeholder="Select a partner to view more info...", min_values=1, max_values=1, options=options, custom_id="diff_pp_hub_sel")

    async def callback(self, interaction: discord.Interaction) -> None:
        await _pp_dropdown_callback(interaction, self.values[0])


class _PartnerPanelView(discord.ui.View):
    """Persistent view for the public channel panel."""
    def __init__(self, partners: list) -> None:
        super().__init__(timeout=None)
        if partners:
            self.add_item(_PartnerDropdown(partners))


class _PartnerHubView(discord.ui.View):
    """Non-persistent view sent ephemerally from the Welcome Hub button."""
    def __init__(self, partners: list) -> None:
        super().__init__(timeout=120)
        if partners:
            self.add_item(_PartnerHubDropdown(partners))

    @discord.ui.button(label="Apply for Partnership", emoji="📩", style=discord.ButtonStyle.primary, row=1)
    async def apply_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(_PshipApplicationModal())


class _PartnerAddModal(discord.ui.Modal, title="Add New Partner"):
    p_name    = discord.ui.TextInput(label="Partner Name",                                                   required=True,  max_length=100)
    p_invite  = discord.ui.TextInput(label="Invite / Link",                                                  required=True,  max_length=200)
    p_short   = discord.ui.TextInput(label="Short Description (shown in dropdown)",                          required=True,  max_length=100)
    p_plat    = discord.ui.TextInput(label="Platforms",  placeholder="e.g. PS5, Xbox, All",                 required=False, max_length=100)
    p_desc    = discord.ui.TextInput(label="Full Description", style=discord.TextStyle.paragraph,            required=False, max_length=1000)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        data = _pp_load()
        name = str(self.p_name).strip()
        if any(p["name"].lower() == name.lower() for p in data["partners"]):
            await interaction.response.send_message(f"**{name}** already exists in the partner list.", ephemeral=True)
            return
        data["partners"].append({
            "name":       name,
            "short_desc": str(self.p_short).strip(),
            "description": str(self.p_desc).strip() if self.p_desc.value else str(self.p_short).strip(),
            "invite":     str(self.p_invite).strip(),
            "platforms":  str(self.p_plat).strip() if self.p_plat.value else "",
            "banner":     "",
        })
        _pp_save(data)
        if interaction.guild:
            await _pp_post_or_refresh(interaction.guild)
        await interaction.response.send_message(f"✅ **{name}** added and panel refreshed.", ephemeral=True)


class _PartnerAddTriggerView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=60)

    @discord.ui.button(label="Add Partner", emoji="➕", style=discord.ButtonStyle.primary)
    async def add_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(_PartnerAddModal())


async def _pp_scan_existing(channel: discord.TextChannel) -> discord.Message | None:
    """Return the most recent hub panel message posted by this bot in the channel."""
    try:
        async for msg in channel.history(limit=50):
            if msg.author.id == channel.guild.me.id and msg.embeds:
                if msg.embeds[0].title == "🤝 DIFF Partnership Hub":
                    return msg
    except Exception:
        pass
    return None


async def _pp_delete_duplicates(channel: discord.TextChannel, keep_id: int) -> None:
    """Delete all hub panel messages in the channel except the one we want to keep."""
    try:
        async for old_msg in channel.history(limit=50):
            if (
                old_msg.id != keep_id
                and old_msg.author.id == channel.guild.me.id
                and old_msg.embeds
                and old_msg.embeds[0].title == "🤝 DIFF Partnership Hub"
            ):
                try:
                    await old_msg.delete()
                except Exception:
                    pass
    except Exception:
        pass


async def _pp_post_or_refresh(guild: discord.Guild) -> None:
    channel = guild.get_channel(_PP_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        try:
            channel = await guild.fetch_channel(_PP_CHANNEL_ID)
        except Exception:
            return
    if not isinstance(channel, discord.TextChannel):
        return
    partners = _pp_get_partners()
    embed    = _pp_build_embed(partners)
    view     = _PartnerPanelView(partners)
    data     = _pp_load()
    msg_id   = data.get("panel_message_id")

    # Try the stored message ID first
    if msg_id:
        try:
            msg = await channel.fetch_message(int(msg_id))
            await msg.edit(embed=embed, view=view)
            await _pp_delete_duplicates(channel, msg.id)
            return
        except discord.NotFound:
            data["panel_message_id"] = None
            _pp_save(data)
        except Exception:
            return

    # Stored ID missing or deleted — scan channel history to find any existing panel
    existing = await _pp_scan_existing(channel)
    if existing:
        try:
            await existing.edit(embed=embed, view=view)
            data["panel_message_id"] = existing.id
            _pp_save(data)
            await _pp_delete_duplicates(channel, existing.id)
            return
        except Exception:
            pass

    # Truly no existing panel — post fresh
    msg = await channel.send(embed=embed, view=view)
    data["panel_message_id"] = msg.id
    _pp_save(data)
    await _pp_delete_duplicates(channel, msg.id)


@bot.command(name="postpartnerpanel")
async def _cmd_postpartnerpanel(ctx: commands.Context):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("Admins only.", delete_after=6)
        return
    try:
        await ctx.message.delete()
    except Exception:
        pass
    await _pp_post_or_refresh(ctx.guild)


@bot.command(name="partneradd")
async def _cmd_partneradd(ctx: commands.Context):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("Admins only.", delete_after=6)
        return
    msg = await ctx.send("Click below to fill in the new partner details:", view=_PartnerAddTriggerView())
    try:
        await ctx.message.delete()
    except Exception:
        pass
    await asyncio.sleep(62)
    try:
        await msg.delete()
    except Exception:
        pass


@bot.command(name="partnerremove")
async def _cmd_partnerremove(ctx: commands.Context, *, name: str):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("Admins only.", delete_after=6)
        return
    data = _pp_load()
    before = len(data["partners"])
    data["partners"] = [p for p in data["partners"] if p["name"].lower() != name.strip().lower()]
    if len(data["partners"]) == before:
        await ctx.send(f"❌ Partner **{name}** not found.", delete_after=8)
        return
    _pp_save(data)
    await _pp_post_or_refresh(ctx.guild)
    await ctx.send(f"✅ Removed **{name}** and refreshed the panel.", delete_after=8)
    try:
        await ctx.message.delete()
    except Exception:
        pass


@bot.command(name="partnerslist")
async def _cmd_partnerslist(ctx: commands.Context):
    if not any(r.id in _JOIN_STAFF_ROLE_IDS for r in ctx.author.roles):
        await ctx.send("Staff only.", delete_after=6)
        return
    partners = _pp_get_partners()
    if not partners:
        await ctx.send("No partners on file.", delete_after=8)
        return
    embed = discord.Embed(
        title="🤝 Partner List",
        description="\n".join(f"• **{p['name']}** — {p.get('short_desc', '')}" for p in partners[:25]),
        color=discord.Color.blurple(),
    )
    embed.set_footer(text=f"Total: {len(partners)}")
    await ctx.send(embed=embed)


# =========================
# PARTNERSHIP SYSTEM
# =========================

_PSHIP_PANEL_CHANNEL_ID    = 0  # channel where the public panel is posted
_PSHIP_REVIEW_CHANNEL_ID   = 0  # staff-only review channel
_PSHIP_ACCEPTED_CHANNEL_ID = 0  # public channel for accepted partner announcements (0 = skip)
_PSHIP_PARTNER_ROLE_ID     = 0  # role assigned on acceptance (0 = skip)
_PSHIP_STAFF_PING_ROLE_ID  = 0  # staff role pinged on new application (0 = skip)
_PSHIP_FILE                = os.path.join(DATA_FOLDER, "diff_partnerships.json")

_PSHIP_EMBED_COLOR   = discord.Color.from_rgb(88, 101, 242)
_PSHIP_SUCCESS_COLOR = discord.Color.green()
_PSHIP_DENIED_COLOR  = discord.Color.red()
_PSHIP_WARN_COLOR    = discord.Color.gold()
_PSHIP_FOOTER        = "Different Meets • Partnership System"


def _pship_load() -> dict:
    return _load_diff_json(_PSHIP_FILE) or {}


def _pship_save(data: dict) -> None:
    _save_diff_json(_PSHIP_FILE, data)


def _pship_extract_app_id(message: discord.Message) -> str | None:
    try:
        desc = message.embeds[0].description or ""
        import re as _re
        m = _re.search(r"`(PARTNER-\d+-\d+)`", desc)
        return m.group(1) if m else None
    except Exception:
        return None


def _pship_build_info_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🤝 DIFF Partnership Program",
        description=(
            "Interested in partnering with **Different Meets**?\n"
            "We work with communities that match our standards of **activity, professionalism, and clean community culture**."
        ),
        color=_PSHIP_EMBED_COLOR,
    )
    embed.add_field(
        name="📌 Partnership Requirements",
        value=(
            "• Active and well-managed community\n"
            "• Clean and respectful environment\n"
            "• Related to car culture, GTA, automotive content, or gaming\n"
            "• Good engagement and not inactive\n"
            "• Organized setup with rules and moderation"
        ),
        inline=False,
    )
    embed.add_field(
        name="🚀 What You Get",
        value=(
            "• Promotion in the DIFF partnership area\n"
            "• Exposure to our community\n"
            "• Potential social media / event support\n"
            "• Future collab opportunities"
        ),
        inline=False,
    )
    embed.add_field(
        name="📋 How To Apply",
        value=(
            "Press **Apply for Partnership** below and complete the application form.\n"
            "A staff member will review your submission and respond once a decision is made."
        ),
        inline=False,
    )
    embed.add_field(
        name="⚠️ Important Notes",
        value=(
            "• Not all applications are accepted\n"
            "• Inactive or poor-quality partnerships may be removed\n"
            "• Partnerships must stay mutually beneficial"
        ),
        inline=False,
    )
    embed.set_footer(text=_PSHIP_FOOTER)
    return embed


def _pship_build_panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🤝 DIFF Partnership Center",
        description=(
            "Use the buttons below to learn how DIFF partnerships work or submit a partnership request.\n\n"
            "We look for communities that are **active, respectful, organized, and aligned with DIFF standards**."
        ),
        color=_PSHIP_EMBED_COLOR,
    )
    embed.add_field(
        name="Available Options",
        value=(
            "**📖 Partnership Info** — Read requirements and expectations\n"
            "**📩 Apply for Partnership** — Submit your community for staff review"
        ),
        inline=False,
    )
    embed.set_footer(text=_PSHIP_FOOTER)
    return embed


def _pship_build_application_embed(app: dict, user: discord.User | discord.Member) -> discord.Embed:
    embed = discord.Embed(
        title="📨 New Partnership Application",
        description=f"Application ID: `{app['application_id']}`",
        color=_PSHIP_WARN_COLOR,
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name="Applicant", value=f"{user.mention} (`{app['applicant_name']}`)", inline=False)
    embed.add_field(name="Community Name", value=app["server_name"], inline=False)
    embed.add_field(name="Invite Link", value=app["invite_link"], inline=False)
    embed.add_field(name="Community Type", value=app["community_type"], inline=True)
    embed.add_field(name="Member Count", value=app["member_count"], inline=True)
    embed.add_field(name="Why They Want To Partner", value=app["why_partner"][:1024], inline=False)
    embed.add_field(name="Extra Info", value=(app["extra_info"][:1024] if app.get("extra_info") else "None provided"), inline=False)
    embed.add_field(name="Status", value="🟡 Pending Review", inline=False)
    if hasattr(user, "display_avatar") and user.display_avatar:
        embed.set_thumbnail(url=user.display_avatar.url)
    embed.set_footer(text=_PSHIP_FOOTER)
    return embed


def _pship_build_accepted_embed(app: dict, reviewer: discord.Member | discord.User) -> discord.Embed:
    embed = discord.Embed(
        title="✅ Partnership Accepted",
        description=(
            f"The partnership request for **{app['server_name']}** has been approved.\n\n"
            "Welcome to the DIFF partnership network."
        ),
        color=_PSHIP_SUCCESS_COLOR,
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name="Community",    value=app["server_name"], inline=True)
    embed.add_field(name="Invite Link",  value=app["invite_link"], inline=True)
    embed.add_field(name="Reviewed By",  value=reviewer.mention,   inline=False)
    embed.set_footer(text=_PSHIP_FOOTER)
    return embed


def _pship_build_denied_embed(app: dict, reviewer: discord.Member | discord.User, reason: str) -> discord.Embed:
    embed = discord.Embed(
        title="❌ Partnership Denied",
        description=f"The partnership request for **{app['server_name']}** was not approved.",
        color=_PSHIP_DENIED_COLOR,
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name="Community",   value=app["server_name"], inline=True)
    embed.add_field(name="Reviewed By", value=reviewer.mention,   inline=True)
    embed.add_field(name="Reason",      value=reason[:1024],      inline=False)
    embed.set_footer(text=_PSHIP_FOOTER)
    return embed


def _pship_build_log_embed(action: str, app: dict, reviewer: discord.Member | discord.User, reason: str | None = None) -> discord.Embed:
    color = _PSHIP_SUCCESS_COLOR if action == "accepted" else _PSHIP_DENIED_COLOR
    icon  = "✅" if action == "accepted" else "❌"
    embed = discord.Embed(
        title=f"{icon} Partnership {action.title()}",
        color=color,
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name="Application ID", value=app["application_id"], inline=False)
    embed.add_field(name="Applicant",      value=f"<@{app['applicant_id']}>", inline=True)
    embed.add_field(name="Community",      value=app["server_name"],          inline=True)
    embed.add_field(name="Reviewed By",    value=reviewer.mention,            inline=False)
    if reason:
        embed.add_field(name="Reason", value=reason[:1024], inline=False)
    embed.set_footer(text=_PSHIP_FOOTER)
    return embed


async def _pship_process_accept(interaction: discord.Interaction, app_id: str) -> None:
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ You don't have permission to review applications.", ephemeral=True)
        return
    data = _pship_load()
    app = data.get(app_id)
    if not app:
        await interaction.response.send_message("❌ Application not found.", ephemeral=True)
        return
    if app.get("status") != "pending":
        await interaction.response.send_message("⚠️ This application has already been reviewed.", ephemeral=True)
        return
    app["status"]        = "accepted"
    app["reviewer_id"]   = interaction.user.id
    app["reviewer_name"] = str(interaction.user)
    app["decided_at"]    = datetime.now(timezone.utc).isoformat()
    data[app_id] = app
    _pship_save(data)
    guild = interaction.guild
    applicant = guild.get_member(app["applicant_id"]) if guild else None
    if applicant and _PSHIP_PARTNER_ROLE_ID:
        role = guild.get_role(_PSHIP_PARTNER_ROLE_ID)
        if role:
            try:
                await applicant.add_roles(role, reason="Partnership accepted")
            except discord.Forbidden:
                pass
    updated = _pship_build_application_embed(app, applicant or interaction.user)
    updated.color = _PSHIP_SUCCESS_COLOR
    updated.set_field_at(len(updated.fields) - 1, name="Status", value=f"✅ Accepted by {interaction.user.mention}", inline=False)
    await interaction.message.edit(embed=updated, view=None)
    if applicant:
        try:
            await applicant.send(embed=_pship_build_accepted_embed(app, interaction.user))
        except discord.Forbidden:
            pass
    if _PSHIP_ACCEPTED_CHANNEL_ID:
        acc_ch = guild.get_channel(_PSHIP_ACCEPTED_CHANNEL_ID) if guild else None
        if isinstance(acc_ch, discord.TextChannel):
            await acc_ch.send(embed=_pship_build_accepted_embed(app, interaction.user))
    log_ch = guild.get_channel(STAFF_LOGS_CHANNEL_ID) if guild else None
    if isinstance(log_ch, discord.TextChannel):
        await log_ch.send(embed=_pship_build_log_embed("accepted", app, interaction.user))
    await interaction.response.send_message("✅ Partnership accepted.", ephemeral=True)


async def _pship_process_deny(interaction: discord.Interaction, app_id: str, reason: str) -> None:
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("❌ You don't have permission to review applications.", ephemeral=True)
        return
    data = _pship_load()
    app = data.get(app_id)
    if not app:
        await interaction.response.send_message("❌ Application not found.", ephemeral=True)
        return
    if app.get("status") != "pending":
        await interaction.response.send_message("⚠️ This application has already been reviewed.", ephemeral=True)
        return
    app["status"]        = "denied"
    app["reviewer_id"]   = interaction.user.id
    app["reviewer_name"] = str(interaction.user)
    app["decided_at"]    = datetime.now(timezone.utc).isoformat()
    data[app_id] = app
    _pship_save(data)
    guild = interaction.guild
    applicant = guild.get_member(app["applicant_id"]) if guild else None
    updated = _pship_build_application_embed(app, applicant or interaction.user)
    updated.color = _PSHIP_DENIED_COLOR
    updated.set_field_at(len(updated.fields) - 1, name="Status", value=f"❌ Denied by {interaction.user.mention}", inline=False)
    await interaction.message.edit(embed=updated, view=None)
    if applicant:
        try:
            await applicant.send(embed=_pship_build_denied_embed(app, interaction.user, reason))
        except discord.Forbidden:
            pass
    log_ch = guild.get_channel(STAFF_LOGS_CHANNEL_ID) if guild else None
    if isinstance(log_ch, discord.TextChannel):
        await log_ch.send(embed=_pship_build_log_embed("denied", app, interaction.user, reason=reason))
    await interaction.response.send_message("❌ Partnership denied.", ephemeral=True)


class _PshipDenyModal(discord.ui.Modal, title="Deny Partnership Application"):
    reason = discord.ui.TextInput(
        label="Reason for denial",
        style=discord.TextStyle.paragraph,
        placeholder="Explain why this partnership was denied.",
        required=True,
        max_length=500,
    )

    def __init__(self, app_id: str) -> None:
        super().__init__()
        self.app_id = app_id

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await _pship_process_deny(interaction, self.app_id, str(self.reason))


class _PshipStaffView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success, emoji="✅", custom_id="pship_accept")
    async def accept_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        app_id = _pship_extract_app_id(interaction.message)
        if not app_id:
            await interaction.response.send_message("❌ Could not find application ID.", ephemeral=True)
            return
        await _pship_process_accept(interaction, app_id)

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger, emoji="❌", custom_id="pship_deny")
    async def deny_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        app_id = _pship_extract_app_id(interaction.message)
        if not app_id:
            await interaction.response.send_message("❌ Could not find application ID.", ephemeral=True)
            return
        await interaction.response.send_modal(_PshipDenyModal(app_id))


class _PshipApplicationModal(discord.ui.Modal, title="DIFF Partnership Application"):
    server_name    = discord.ui.TextInput(label="Community / Server Name",        placeholder="Enter your community name",                      required=True,  max_length=100)
    invite_link    = discord.ui.TextInput(label="Invite Link / Social Link",       placeholder="Paste your Discord invite or main link",          required=True,  max_length=200)
    community_type = discord.ui.TextInput(label="Community Type",                  placeholder="GTA, Car Community, Gaming, Automotive, etc.",    required=True,  max_length=100)
    member_count   = discord.ui.TextInput(label="Approximate Member Count",        placeholder="Example: 250",                                    required=True,  max_length=20)
    why_partner    = discord.ui.TextInput(label="Why do you want to partner?",     style=discord.TextStyle.paragraph,
                                          placeholder="Tell us why this partnership makes sense.",                required=True,  max_length=1000)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        app_id = f"PARTNER-{interaction.user.id}-{int(datetime.now(timezone.utc).timestamp())}"
        app = {
            "application_id": app_id,
            "applicant_id":   interaction.user.id,
            "applicant_name": str(interaction.user),
            "server_name":    str(self.server_name),
            "invite_link":    str(self.invite_link),
            "community_type": str(self.community_type),
            "member_count":   str(self.member_count),
            "why_partner":    str(self.why_partner),
            "extra_info":     "",
            "status":         "pending",
        }
        data = _pship_load()
        data[app_id] = app
        _pship_save(data)
        review_ch = interaction.guild.get_channel(_PSHIP_REVIEW_CHANNEL_ID) if interaction.guild else None
        if not isinstance(review_ch, discord.TextChannel):
            await interaction.response.send_message(
                "✅ Application received! Staff will review it shortly.\n"
                f"Your Application ID: `{app_id}`",
                ephemeral=True,
            )
            return
        content = f"<@&{_PSHIP_STAFF_PING_ROLE_ID}> New partnership application submitted." if _PSHIP_STAFF_PING_ROLE_ID else None
        await review_ch.send(
            content=content,
            embed=_pship_build_application_embed(app, interaction.user),
            view=_PshipStaffView(),
        )
        confirm = discord.Embed(
            title="✅ Application Submitted",
            description=f"Your application has been sent to staff for review.\nApplication ID: `{app_id}`",
            color=_PSHIP_SUCCESS_COLOR,
        )
        confirm.set_footer(text=_PSHIP_FOOTER)
        await interaction.response.send_message(embed=confirm, ephemeral=True)


class _PshipPanelView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(label="Partnership Info", style=discord.ButtonStyle.secondary, emoji="📖", custom_id="pship_info")
    async def info_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_message(embed=_pship_build_info_embed(), ephemeral=True)

    @discord.ui.button(label="Apply for Partnership", style=discord.ButtonStyle.primary, emoji="📩", custom_id="pship_apply")
    async def apply_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(_PshipApplicationModal())


@bot.command(name="postpartnershippanel")
async def _cmd_postpartnershippanel(ctx: commands.Context, channel: discord.TextChannel = None):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("Admins only.", delete_after=6)
        return
    target = channel or ctx.channel
    try:
        await ctx.message.delete()
    except Exception:
        pass
    await target.send(embed=_pship_build_panel_embed(), view=_PshipPanelView())


@bot.command(name="partnershiplist")
async def _cmd_partnershiplist(ctx: commands.Context):
    if not any(r.id in _JOIN_STAFF_ROLE_IDS for r in ctx.author.roles):
        await ctx.send("Staff only.", delete_after=6)
        return
    data = _pship_load()
    if not data:
        await ctx.send("No partnership applications on file.", delete_after=10)
        return
    lines = []
    for app_id, app in data.items():
        status_icon = {"pending": "🟡", "accepted": "✅", "denied": "❌"}.get(app.get("status", "pending"), "❔")
        lines.append(f"{status_icon} `{app_id}` — **{app.get('server_name', '?')}** by <@{app.get('applicant_id', 0)}>")
    embed = discord.Embed(
        title="📋 Partnership Applications",
        description="\n".join(lines[:25]),
        color=_PSHIP_EMBED_COLOR,
    )
    embed.set_footer(text=_PSHIP_FOOTER)
    await ctx.send(embed=embed)


# =========================
# RSVP + ATTENDANCE + SMART PING
# =========================

_RSVP_STORE: dict[int, dict] = {}


def _rsvp_get(msg_id: int) -> dict:
    return _RSVP_STORE.setdefault(msg_id, {
        "attending": set(), "maybe": set(), "not_attending": set(),
        "title": "Upcoming DIFF Meet", "notes": "No extra notes.",
        "created_by": 0, "created_at": "",
    })


def _rsvp_set_choice(entry: dict, user_id: int, choice: str) -> None:
    entry["attending"].discard(user_id)
    entry["maybe"].discard(user_id)
    entry["not_attending"].discard(user_id)
    entry[choice].add(user_id)


def _rsvp_build_embed(msg_id: int) -> discord.Embed:
    e = _rsvp_get(msg_id)
    embed = discord.Embed(
        title="📅 DIFF Meet RSVP",
        description=(
            f"**Meet:** {e['title']}\n"
            f"**Notes:** {e['notes']}\n\n"
            "*Use the buttons below to confirm your availability.*\n\n"
            "✅ **Attending** — You are confirmed\n"
            "❓ **Maybe** — You might pull up\n"
            "❌ **Not Attending** — You cannot make it\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "*Please respond honestly so DIFF can plan meets properly.*\n\n"
            "— **Different Meets**"
        ),
        color=discord.Color.blurple(),
    )
    embed.add_field(name="✅ Attending", value=str(len(e["attending"])), inline=True)
    embed.add_field(name="❓ Maybe", value=str(len(e["maybe"])), inline=True)
    embed.add_field(name="❌ Not Attending", value=str(len(e["not_attending"])), inline=True)
    embed.set_footer(text=f"Created {e['created_at']}")
    return embed


def _rsvp_mentions(guild: discord.Guild, ids: set) -> str:
    lines = [guild.get_member(uid).mention for uid in sorted(ids) if guild.get_member(uid)]
    return "\n".join(lines) if lines else "None"


class _RsvpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def _handle(self, interaction: discord.Interaction, choice: str, label: str):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Server only.", ephemeral=True)
            return
        if not interaction.message or interaction.message.id not in _RSVP_STORE:
            await interaction.response.send_message("This RSVP panel is no longer active.", ephemeral=True)
            return
        entry = _rsvp_get(interaction.message.id)
        _rsvp_set_choice(entry, interaction.user.id, choice)
        try:
            await interaction.message.edit(embed=_rsvp_build_embed(interaction.message.id), view=self)
        except discord.HTTPException:
            pass
        await interaction.response.send_message(
            f"Your RSVP is set to **{label}** for **{entry['title']}**.", ephemeral=True
        )

    @discord.ui.button(label="Attending", emoji="✅", style=discord.ButtonStyle.success, custom_id="diff_rsvp_attending")
    async def btn_attending(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "attending", "Attending")

    @discord.ui.button(label="Maybe", emoji="❓", style=discord.ButtonStyle.primary, custom_id="diff_rsvp_maybe")
    async def btn_maybe(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "maybe", "Maybe")

    @discord.ui.button(label="Not Attending", emoji="❌", style=discord.ButtonStyle.danger, custom_id="diff_rsvp_not_attending")
    async def btn_not_attending(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "not_attending", "Not Attending")


@bot.command(name="send_rsvp_panel")
@commands.guild_only()
async def _cmd_send_rsvp_panel(ctx: commands.Context, *, meet_info: str = "Upcoming DIFF Meet | No extra notes."):
    is_auth = (
        ctx.author.guild_permissions.manage_guild
        or any(r.id in _JOIN_STAFF_ROLE_IDS for r in getattr(ctx.author, "roles", []))
    )
    if not is_auth:
        await ctx.send("Staff only.", delete_after=6)
        return
    if "|" in meet_info:
        title, notes = [p.strip() for p in meet_info.split("|", 1)]
    else:
        title, notes = meet_info.strip(), "No extra notes."
    from datetime import datetime as _dt
    created_at = _dt.now().strftime("%b %d, %Y • %I:%M %p")
    tmp = await ctx.send(embed=discord.Embed(title="Loading RSVP...", color=discord.Color.blurple()), view=_RsvpView())
    _RSVP_STORE[tmp.id] = {
        "attending": set(), "maybe": set(), "not_attending": set(),
        "title": title, "notes": notes, "created_by": ctx.author.id, "created_at": created_at,
    }
    await tmp.edit(embed=_rsvp_build_embed(tmp.id), view=_RsvpView())
    try:
        await ctx.message.delete()
    except Exception:
        pass


@bot.command(name="rsvp_export")
@commands.guild_only()
async def _cmd_rsvp_export(ctx: commands.Context, message_id: int):
    is_auth = (
        ctx.author.guild_permissions.manage_guild
        or any(r.id in _JOIN_STAFF_ROLE_IDS for r in getattr(ctx.author, "roles", []))
    )
    if not is_auth:
        await ctx.send("Staff only.", delete_after=6)
        return
    if message_id not in _RSVP_STORE:
        await ctx.send("No RSVP panel found with that message ID.", delete_after=10)
        return
    e = _rsvp_get(message_id)
    embed = discord.Embed(
        title="📊 DIFF RSVP Export",
        description=f"**Meet:** {e['title']}",
        color=discord.Color.green(),
    )
    embed.add_field(name=f"✅ Attending ({len(e['attending'])})", value=_rsvp_mentions(ctx.guild, e["attending"]) or "None", inline=False)
    embed.add_field(name=f"❓ Maybe ({len(e['maybe'])})", value=_rsvp_mentions(ctx.guild, e["maybe"]) or "None", inline=False)
    embed.add_field(name=f"❌ Not Attending ({len(e['not_attending'])})", value=_rsvp_mentions(ctx.guild, e["not_attending"]) or "None", inline=False)
    embed.set_footer(text="Use the attending list for smart host pings if needed.")
    await ctx.send(embed=embed)


@bot.command(name="rsvp_ping_attending")
@commands.guild_only()
async def _cmd_rsvp_ping_attending(ctx: commands.Context, message_id: int):
    is_auth = (
        ctx.author.guild_permissions.manage_guild
        or any(r.id in _JOIN_STAFF_ROLE_IDS for r in getattr(ctx.author, "roles", []))
    )
    if not is_auth:
        await ctx.send("Staff only.", delete_after=6)
        return
    if message_id not in _RSVP_STORE:
        await ctx.send("No RSVP panel found with that message ID.", delete_after=10)
        return
    e = _rsvp_get(message_id)
    mentions = [ctx.guild.get_member(uid).mention for uid in sorted(e["attending"]) if ctx.guild.get_member(uid)]
    if not mentions:
        await ctx.send("Nobody is marked as attending yet.", delete_after=8)
        return
    chunks, current = [], "✅ **DIFF RSVP Attending Ping**\n\n"
    for m in mentions:
        if len(current) + len(m) + 1 > 1900:
            chunks.append(current)
            current = ""
        current += m + "\n"
    if current:
        chunks.append(current)
    for chunk in chunks:
        await ctx.send(chunk, allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False))


@bot.command(name="log_meet_attendance")
@commands.guild_only()
async def _cmd_log_meet_attendance(ctx: commands.Context, total_players: int, diff_members_present: int, *, meet_name: str = "DIFF Meet"):
    is_auth = (
        ctx.author.guild_permissions.manage_guild
        or any(r.id in _JOIN_STAFF_ROLE_IDS for r in getattr(ctx.author, "roles", []))
    )
    if not is_auth:
        await ctx.send("Staff only.", delete_after=6)
        return
    from datetime import datetime as _dt
    embed = discord.Embed(title="📊 DIFF Meet Attendance", color=discord.Color.orange())
    embed.add_field(name="Host", value=ctx.author.mention, inline=False)
    embed.add_field(name="Meet Name", value=meet_name, inline=False)
    embed.add_field(name="Date", value=_dt.now().strftime("%b %d, %Y"), inline=True)
    embed.add_field(name="Total Players in Lobby", value=str(total_players), inline=True)
    embed.add_field(name="DIFF Members Present", value=str(diff_members_present), inline=True)
    embed.add_field(name="Screenshot", value="Attach lobby screenshot below.", inline=False)
    embed.set_footer(text="Different Meets • Attendance Tracker")
    await ctx.send(embed=embed)


@bot.command(name="rsvp_help")
@commands.guild_only()
async def _cmd_rsvp_help(ctx: commands.Context):
    embed = discord.Embed(
        title="📘 DIFF RSVP System Help",
        description=(
            "`!send_rsvp_panel Meet Name | extra notes`\n"
            "Posts an RSVP panel with live vote counts.\n\n"
            "`!rsvp_export MESSAGE_ID`\n"
            "Shows who is attending, maybe, or not attending.\n\n"
            "`!rsvp_ping_attending MESSAGE_ID`\n"
            "Pings only members marked as attending.\n\n"
            "`!log_meet_attendance total diff_present Meet Name`\n"
            "Posts a quick attendance log.\n\n"
            "Note: RSVP data resets on bot restart (in-memory only)."
        ),
        color=discord.Color.blurple(),
    )
    await ctx.send(embed=embed)


# =========================
# IG AUTO POST SYSTEM
# =========================

_IG_CHANNEL_ID      = 1485830678980333568
_IG_PING_ROLE_ID    = 1138690897077338265
_IG_CONTENT_ROLE_ID = 1110037666147336293
_IG_AUTO_REACTIONS  = ["🔥", "📸", "🏁"]
_IG_PANEL_FILE      = os.path.join(DATA_FOLDER, "diff_ig_panel.json")

_IG_LINK_RE = re.compile(
    r"(https?://(?:www\.)?(?:instagram\.com|instagr\.am)/[^\s]+)",
    re.IGNORECASE,
)


def _ig_panel_load() -> dict:
    try:
        with open(_IG_PANEL_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def _ig_panel_save(data: dict):
    try:
        with open(_IG_PANEL_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def _ig_build_panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title="📸 DIFF Social Feed",
        color=discord.Color.magenta(),
        description=(
            "This is the official DIFF Instagram drop channel.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "**How it works**\n"
            "Drop a valid Instagram link anywhere in a message and the bot will:\n"
            "• Auto-format it into a clean embed\n"
            f"• Ping <@&{_IG_PING_ROLE_ID}>\n"
            "• Add 🔥 📸 🏁 reaction prompts automatically\n\n"
            "**React with**\n"
            "🔥 — This was hard\n"
            "📸 — I was there\n"
            "🏁 — Pulling up next meet\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "*Staff can also use `!igpost <link>` to manually trigger a formatted drop.*"
        ),
    )
    embed.set_footer(text="Different Meets • DIFF Social Feed")
    return embed


def _ig_user_allowed(member: discord.Member) -> bool:
    role_ids = {r.id for r in member.roles}
    return (
        member.guild_permissions.manage_guild
        or _IG_CONTENT_ROLE_ID in role_ids
        or bool(role_ids & _JOIN_STAFF_ROLE_IDS)
    )


class _IgDropModal(discord.ui.Modal, title="📸 Drop IG Post"):
    link_field = discord.ui.TextInput(
        label="Instagram Link",
        placeholder="https://www.instagram.com/p/...",
        required=True,
        max_length=500,
    )

    async def on_submit(self, interaction: discord.Interaction):
        raw = self.link_field.value.strip()
        m = _IG_LINK_RE.search(raw)
        if not m:
            await interaction.response.send_message(
                "That doesn't look like a valid Instagram link. Try again.", ephemeral=True
            )
            return
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("Can only post in a text channel.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        await _ig_handle_drop(channel, m.group(1))
        await interaction.followup.send("Posted!", ephemeral=True)


class _IgDropView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📸 Drop IG Post",
        style=discord.ButtonStyle.primary,
        custom_id="diff_ig:drop",
    )
    async def drop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Server only.", ephemeral=True)
            return
        if not _ig_user_allowed(interaction.user):
            await interaction.response.send_message(
                "You need the Content Team role to post here.", ephemeral=True
            )
            return
        await interaction.response.send_modal(_IgDropModal())


async def _ig_panel_post_or_refresh(guild: discord.Guild):
    """Edit existing panel in place on startup; never creates a duplicate."""
    channel = guild.get_channel(_IG_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        try:
            channel = await guild.fetch_channel(_IG_CHANNEL_ID)
        except Exception:
            return
    if not isinstance(channel, discord.TextChannel):
        return
    data = _ig_panel_load()
    msg_id = data.get(str(guild.id))
    if msg_id:
        try:
            msg = await channel.fetch_message(int(msg_id))
            await msg.edit(embed=_ig_build_panel_embed(), view=_IgDropView())
            return
        except discord.NotFound:
            pass
        except Exception:
            return
    msg = await channel.send(embed=_ig_build_panel_embed(), view=_IgDropView())
    data[str(guild.id)] = msg.id
    _ig_panel_save(data)
    try:
        await msg.pin()
    except Exception:
        pass


async def _ig_handle_drop(channel: discord.TextChannel, link: str):
    """Post a formatted IG drop embed and add reactions."""
    ping = f"<@&{_IG_PING_ROLE_ID}>"
    embed = discord.Embed(
        title="DIFF Instagram Drop",
        description=(
            "A new DIFF post is live.\n\n"
            "💬 **Show support:** like, comment, and share\n"
            f"🔗 **Post Link:** {link}"
        ),
        color=discord.Color.magenta(),
    )
    embed.add_field(
        name="Community Reactions",
        value="🔥 = This was hard\n📸 = I was there\n🏁 = Pulling up next meet",
        inline=False,
    )
    embed.set_footer(text="Different Meets • DIFF Social Feed")
    sent = await channel.send(
        content=f"{ping}\n\n🔥 __**NEW DIFF POST**__ 🔥",
        embed=embed,
        allowed_mentions=discord.AllowedMentions(roles=True, users=False, everyone=False),
    )
    for emoji in _IG_AUTO_REACTIONS:
        try:
            await sent.add_reaction(emoji)
        except Exception:
            pass


@bot.command(name="igpost")
async def _cmd_igpost(ctx: commands.Context, *, link: str = ""):
    is_auth = ctx.author.guild_permissions.manage_guild or any(
        r.id in _JOIN_STAFF_ROLE_IDS for r in getattr(ctx.author, "roles", [])
    )
    if not is_auth:
        await ctx.send("Staff only.", delete_after=6)
        return
    m = _IG_LINK_RE.search(link)
    if not m:
        await ctx.send("Please include a valid Instagram link.", delete_after=8)
        return
    try:
        await ctx.message.delete()
    except Exception:
        pass
    if isinstance(ctx.channel, discord.TextChannel):
        await _ig_handle_drop(ctx.channel, m.group(1))


@bot.command(name="postigpanel")
async def _cmd_postigpanel(ctx: commands.Context):
    is_auth = ctx.author.guild_permissions.administrator or any(
        r.id in _JOIN_STAFF_ROLE_IDS for r in getattr(ctx.author, "roles", [])
    )
    if not is_auth:
        await ctx.send("Staff only.", delete_after=6)
        return
    try:
        await ctx.message.delete()
    except Exception:
        pass
    await _ig_panel_post_or_refresh(ctx.guild)


# =========================
# START BOT
# =========================
if not TOKEN:
    raise ValueError("TOKEN not found. Set it in Render environment variables.")

if __name__ == "__main__":
    start_web_server_and_bot()
