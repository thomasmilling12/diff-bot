import asyncio
import json
import os
from datetime import datetime
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
# HELPERS
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
        embed = discord.Embed(
            title="📝 DIFF Crew Application",
            description=(
                "Fill out the official application below:\n\n"
                "https://form.jotform.com/231268157057054\n\n"
                "Make sure you answer all questions seriously.\n"
                "Applications with effort are more likely to be accepted."
            ),
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def send_or_refresh_crew_panel(guild: discord.Guild):
    channel = guild.get_channel(CREW_PANEL_CHANNEL_ID)
    if channel is None:
        return False, "Crew panel channel not found."

    embed = discord.Embed(
        title="🏁 DIFF Crew Recruitment",
        description="Join Different Meets (DIFF). Use the buttons below to get started.",
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
            if msg.author == guild.me and msg.embeds and msg.embeds[0].title == "🏁 DIFF Crew Recruitment":
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
    except Exception as e:
        print(f"View registration warning: {e}")

    status_message_id = data.get("panel_message_id")


# =========================
# AUTO REFRESH PANEL
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
# START BOT
# =========================
if not TOKEN:
    raise ValueError("TOKEN not found.")

keep_alive()
bot.run(TOKEN)
