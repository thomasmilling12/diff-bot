import asyncio
import io
import json
import os
import random
import re
import sys
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, asdict
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
UPCOMING_MEET_CHANNEL_ID = 1047178296191885402
JOIN_MEETS_CHANNEL_ID = 1277084633858576406
SUPPORT_TICKETS_CHANNEL_ID = 1156363575150002226

MEET_ANNOUNCEMENT_CHANNEL_ID = 1484768466023223418
RULES_CHANNEL_ID = 1047161846257438743

RULES_BTN_UPCOMING_MEETS_ID = 1047178296191885402
RULES_BTN_JOIN_MEETS_ID = 1277084633858576406
RULES_BTN_MEET_RULES_ID = 1047161846257438743
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
STAFF_DASHBOARD_CHANNEL_ID = 1485273802391814224
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
        embed = discord.Embed(
            title="🏁 DIFF Activity Leaderboard",
            description="\n\n".join(build_leaderboard_lines(interaction.guild)),
            color=discord.Color.gold(),
            timestamp=utc_now(),
        )
        embed.set_footer(text="Score = Attended×2 + Hosted×5 + Reputation")
        await interaction.response.edit_message(embed=embed, view=LeaderboardView())


class LeaderboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RefreshLeaderboardButton())


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


def build_meet_info_view(guild_id: int) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(label="General Rules", style=discord.ButtonStyle.link, emoji="📜", url=build_channel_link(guild_id, MEET_RULES_CHANNEL_ID)))
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

    if not hierarchy_attendance_loop.is_running():
        hierarchy_attendance_loop.start()

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


@bot.tree.command(name="postleaderboard", description="Post the DIFF activity leaderboard (staff only)")
async def postleaderboard(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Only Leader, Co-Leader, or Manager can use this.", ephemeral=True)
    embed = discord.Embed(
        title="🏁 DIFF Activity Leaderboard",
        description="\n\n".join(build_leaderboard_lines(interaction.guild)),
        color=discord.Color.gold(),
        timestamp=utc_now(),
    )
    embed.set_footer(text="Score = Attended×2 + Hosted×5 + Reputation")
    await interaction.channel.send(embed=embed, view=LeaderboardView())
    await interaction.response.send_message("✅ Leaderboard posted.", ephemeral=True)


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

    @discord.ui.button(label="Approve Color", style=discord.ButtonStyle.success, emoji="🏆", custom_id="diff_approve_color_button_v3")
    async def approve_color_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member) or not _cs_is_color_admin(interaction.user):
            return await interaction.response.send_message("Only Leaders, Co-Leaders, or Managers can approve colors.", ephemeral=True)
        data = _cs_load()
        submission = data["submissions"].get(str(interaction.message.id))
        if not submission:
            return await interaction.response.send_message("Submission not found in the system.", ephemeral=True)
        submission["status"] = "approved"
        submission["approved_at"] = _cs_utc_now()
        _cs_add_stat(data, int(submission["author_id"]), "manual_approvals", 1)
        _cs_save(data)
        await _cs_update_submission_message(submission, extra_footer="Approved by leadership")
        await _cs_post_winner_announcement(interaction.guild, submission, manual=True)
        await interaction.response.send_message("Color approved and announcement posted.", ephemeral=True)

    @discord.ui.button(label="Lock Submission", style=discord.ButtonStyle.secondary, emoji="🔒", custom_id="diff_lock_submission_button_v3")
    async def lock_submission_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member) or not _cs_is_color_admin(interaction.user):
            return await interaction.response.send_message("Only Leaders, Co-Leaders, or Managers can lock submissions.", ephemeral=True)
        data = _cs_load()
        submission = data["submissions"].get(str(interaction.message.id))
        if not submission:
            return await interaction.response.send_message("Submission not found in the system.", ephemeral=True)
        submission["status"] = "locked"
        submission["locked_at"] = _cs_utc_now()
        _cs_save(data)
        await _cs_update_submission_message(submission, disable_view=True, extra_footer="Locked by leadership")
        await interaction.response.send_message("Submission locked.", ephemeral=True)


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
        await member.send(message)
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


@bot.tree.command(name="attendance-promotions", description="Show promotion suggestions based on meet attendance")
async def attendance_promotions(interaction: discord.Interaction):
    if not isinstance(interaction.user, discord.Member) or not is_staff_reviewer(interaction.user):
        return await interaction.response.send_message("Staff only.", ephemeral=True)
    if not _rsvp_promotions:
        return await interaction.response.send_message("No promotion suggestions yet.", ephemeral=True)
    lines = []
    for item in _rsvp_promotions[-10:][::-1]:
        lines.append(
            f"📈 <@{item['user_id']}> — {item['current_role']} → **{item['suggested_role']}** "
            f"| {item.get('attendance_count', 0)} attended | {item.get('hosted_count', 0)} hosted "
            f"| {item.get('attendance_rate', '?')}% rate"
        )
    embed = discord.Embed(
        title="📈 Attendance Promotion Suggestions",
        description="\n".join(lines),
        color=discord.Color.purple(),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Review manually before promoting. Auto-posted to staff logs when triggered.")
    embed.add_field(
        name="Thresholds",
        value="Crew Member → Host: 5 | Host → Manager: 10 | Manager → Co-Leader: 18 | Co-Leader → Leader: 30\nRequires ≥60% attendance rate",
        inline=False,
    )
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
    last = entry.get("last_attended")
    embed.set_footer(text=f"Last attended: {last[:10] if last else 'No check-ins yet'}")
    await interaction.response.send_message(embed=embed, ephemeral=member is None)


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
SUPPORT_TICKET_CATEGORY_ID: int | None = None
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
        role = interaction.guild.get_role(_SUPP_APPROVED_STAFF_ROLE_ID) if _SUPP_APPROVED_STAFF_ROLE_ID else None
        if role:
            try:
                await applicant.add_roles(role, reason=f"Application approved by {interaction.user}")
            except discord.HTTPException:
                pass
        embed = _supp_build_decision_embed(applicant, interaction.user, approved=True)
        await interaction.response.send_message("Application approved.", ephemeral=True)
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
        existing = await _supp_find_existing_ticket(interaction.guild, interaction.user, ticket)
        if existing:
            return await interaction.response.send_message(
                f"You already have an open {ticket.label} ticket: {existing.mention}", ephemeral=True
            )

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

        await interaction.response.send_message(
            f"Your {ticket.label} ticket has been created: {channel.mention}", ephemeral=True
        )


class SupportDropdownView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
        self.add_item(SupportDropdown())


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


@bot.tree.command(name="staff-add-meet", description="Add hosted meet stats to a staff member (leadership only)")
@app_commands.describe(member="Staff member to update", amount="Number of meets to add (default 1)")
async def staff_add_meet(interaction: discord.Interaction, member: discord.Member, amount: app_commands.Range[int, 1, 100] = 1) -> None:
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return await interaction.response.send_message("Server only.", ephemeral=True)
    if not any(r.id in {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID} for r in interaction.user.roles) \
            and not interaction.user.guild_permissions.manage_guild:
        return await interaction.response.send_message("Leadership only.", ephemeral=True)
    _staff_store.add_stat(member.id, "meets_hosted", amount)
    await interaction.response.send_message(f"Added **{amount}** hosted meet(s) to {member.mention}.", ephemeral=True)
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
