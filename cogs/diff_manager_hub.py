from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import discord
from discord.ext import commands

# =========================================================
# CONFIG
# =========================================================

GUILD_ID                = 850386896509337710
MANAGER_HUB_CHANNEL_ID  = 1485273802391814224
LOGO_STORAGE_CHANNEL_ID = 1485265848099799163  # staff-logs — kept alive for CDN

HUB_TITLE = "🧠 DIFF Interactive Manager Hub"
HUB_DESCRIPTION = (
    "The all-in-one management hub for **Different Meets**.\n\n"
    "Use the dropdowns below to read leadership information, view live performance data, "
    "log your manager activity, and browse official DIFF crew logos.\n\n"
    "This panel refreshes cleanly without creating duplicate posts."
)
FOOTER_TEXT = "Different Meets • Interactive Manager Hub"

RECRUITMENT_POINTS    = 3
MEET_SUPPORT_POINTS   = 2
MANAGER_ACTION_POINTS = 2
ISSUE_REPORT_POINTS   = 1
WARNING_FILED_POINTS  = 1

VALID_STATS = {
    "recruitment": "recruitment", "recruit": "recruitment", "r": "recruitment",
    "meet_support": "meet_support", "meetsupport": "meet_support", "ms": "meet_support",
    "manager_actions": "manager_actions", "manageractions": "manager_actions",
    "actions": "manager_actions", "a": "manager_actions",
    "issues_reported": "issues_reported", "issues": "issues_reported",
    "issue": "issues_reported", "i": "issues_reported",
    "warnings_filed": "warnings_filed", "warnings": "warnings_filed",
    "warning": "warnings_filed", "w": "warnings_filed",
}
STAT_LABELS = {
    "recruitment":     ("Recruitment",     RECRUITMENT_POINTS),
    "meet_support":    ("Meet Support",    MEET_SUPPORT_POINTS),
    "manager_actions": ("Manager Actions", MANAGER_ACTION_POINTS),
    "issues_reported": ("Issues Reported", ISSUE_REPORT_POINTS),
    "warnings_filed":  ("Warnings Filed",  WARNING_FILED_POINTS),
}

STATE_FILE      = Path("diff_data/manager_hub_state.json")
STATS_FILE      = Path("diff_data/manager_performance_stats.json")
CREW_LOGOS_FILE = Path("diff_data/crew_logos.json")

# =========================================================
# PRESET LOGOS
# =========================================================

PRESET_LOGOS: list[dict] = [
    {"key": "diff_classic",        "name": "Different Meets Classic",    "description": "Blue Porsche edition logo — Est. 2020"},
    {"key": "diff_crew_gold",      "name": "DIFF Crew — Gold",           "description": "Gold metallic Different Meets Crew wordmark"},
    {"key": "diff_crew_silver",    "name": "DIFF Crew — Silver",         "description": "Silver metallic Different Meets Crew wordmark"},
    {"key": "diff_5th_anniversary","name": "5th Anniversary",            "description": "Official DIFF Meets 5th Anniversary logo"},
    {"key": "diff_420",            "name": "420 Edition",                "description": "DIFF Meets Crew 420 slime edition"},
    {"key": "dmc_classic",         "name": "DMC Classic",                "description": "Different Meets Crew — black & white DMC logo"},
    {"key": "diff_graffiti",       "name": "Graffiti Style",             "description": "Different Meets Crew graffiti text logo"},
    {"key": "diff_red_black",      "name": "Red & Black — Est. 2020",    "description": "Different Meets Crew bold red/black edition"},
    {"key": "diff_4th_anniversary","name": "4th Anniversary",            "description": "Official DIFF Meets 4th Anniversary logo"},
    {"key": "diff_loyalty_club",   "name": "DIFF Loyalty Club",          "description": "DIFF Meets Loyalty Club official logo"},
    {"key": "diff_chrome_crew",    "name": "Chrome Crew — Est. 2020",    "description": "Different Meets Crew chrome metallic — Est. 2020"},
]

# =========================================================
# SECTION CONTENT
# =========================================================

SECTION_CONTENT = {
    "crew_manager_roles": {
        "label": "Crew Managers Roles & Responsibility",
        "emoji": "📋",
        "description": (
            "__**Crew Managers Roles & Responsibility**__\n\n"
            "Crew Managers help keep the crew organized, active, and professional at all times.\n\n"
            "**Main Duties:**\n"
            "• Help oversee day-to-day crew activity\n"
            "• Support hosts and crew staff when needed\n"
            "• Make sure members are following DIFF standards\n"
            "• Monitor crew behavior, professionalism, and activity\n"
            "• Help leaders keep the crew structured and running smoothly\n"
            "• Assist with event planning, communication, and team coordination\n\n"
            "**Expectations:**\n"
            "• Be active and present in the server\n"
            "• Set a strong example for other members\n"
            "• Handle situations maturely and professionally\n"
            "• Help solve issues before they grow into bigger problems\n"
            "• Represent DIFF properly in and outside the server"
        ),
    },
    "crew_recruitment_roles": {
        "label": "Crew Recruitment Roles",
        "emoji": "📣",
        "description": (
            "__**Crew Recruitment Roles**__\n\n"
            "Recruitment Managers are responsible for helping the crew grow with quality members.\n\n"
            "**Main Duties:**\n"
            "• Promote DIFF in a professional way\n"
            "• Reach out to potential new members\n"
            "• Help new members understand what DIFF is about\n"
            "• Answer questions about joining the crew\n"
            "• Guide applicants through the recruitment process\n"
            "• Focus on quality, not just numbers\n\n"
            "**Expectations:**\n"
            "• Bring in members that fit DIFF culture\n"
            "• Be respectful and professional in all outreach\n"
            "• Avoid spamming or low-quality recruiting\n"
            "• Communicate clearly with staff about promising recruits\n"
            "• Help maintain a strong and active community"
        ),
    },
    "discord_manager_roles": {
        "label": "Discord Manager Roles",
        "emoji": "🖥️",
        "description": (
            "__**Discord Manager Roles**__\n\n"
            "Discord Managers help maintain the structure, activity, and presentation of the server.\n\n"
            "**Main Duties:**\n"
            "• Monitor channels and server activity\n"
            "• Keep important panels, systems, and info updated\n"
            "• Assist with permissions, organization, and server flow\n"
            "• Help improve channel layouts and server experience\n"
            "• Support ticket systems, applications, and management tools\n"
            "• Report issues, bugs, or areas that need improvement\n\n"
            "**Expectations:**\n"
            "• Keep the server clean, professional, and easy to navigate\n"
            "• Be proactive instead of waiting for issues to get worse\n"
            "• Work closely with higher staff when changes are needed\n"
            "• Help maintain a strong first impression for members and guests\n"
            "• Always think about how to improve the DIFF experience"
        ),
    },
    "ps_group_chat_manager_roles": {
        "label": "PlayStation Group Chat Manager Roles",
        "emoji": "🎮",
        "description": (
            "♨️__**PlayStation Group Chat Manager Roles:**__♨️\n\n"
            "PlayStation Group Chat Managers help keep the PlayStation side of DIFF active, organized, and respectful.\n\n"
            "**Main Duties:**\n"
            "• Manage PlayStation group chats professionally\n"
            "• Keep chats active and useful for DIFF members\n"
            "• Share important meet updates and reminders\n"
            "• Make sure the right information reaches members quickly\n"
            "• Help reduce confusion before events start\n"
            "• Support communication between the crew and PlayStation members\n\n"
            "**Expectations:**\n"
            "• Keep group chats clean and organized\n"
            "• Avoid unnecessary spam or off-topic clutter\n"
            "• Address issues early before they become bigger problems\n"
            "• Be active, respectful, and informative\n"
            "• Make sure DIFF is represented properly at all times"
        ),
    },
    "problems_to_look_out_for": {
        "label": "Problem To Look Out For",
        "emoji": "⛔",
        "description": (
            "🚫__**PROBLEM TO LOOK OUT FOR**__🚫\n\n"
            "Managers should always stay alert and watch for issues that can hurt the crew, meets, or server experience.\n\n"
            "**Things To Watch For:**\n"
            "• Inactive staff or managers not doing their job\n"
            "• Low-quality recruiting or inviting the wrong people\n"
            "• Poor communication before events\n"
            "• Toxic behavior, unnecessary drama, or disrespect\n"
            "• Members ignoring rules or host instructions\n"
            "• Staff abusing power or handling situations badly\n"
            "• Group chats becoming messy, unorganized, or unprofessional\n"
            "• Important panels/systems not being maintained\n"
            "• Lack of teamwork between management roles\n\n"
            "**What Managers Should Do:**\n"
            "• Address problems early\n"
            "• Report serious issues to leadership\n"
            "• Stay professional when correcting others\n"
            "• Focus on solutions, structure, and consistency\n"
            "• Protect the quality and image of DIFF"
        ),
    },
}

# =========================================================
# HELPERS — STATE
# =========================================================

def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            with STATE_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"channel_id": MANAGER_HUB_CHANNEL_ID, "message_id": None}

def _save_state(data: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# =========================================================
# HELPERS — LOGOS
# =========================================================

def _load_logos() -> list[dict]:
    if CREW_LOGOS_FILE.exists():
        try:
            with CREW_LOGOS_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def _save_logos(logos: list[dict]) -> None:
    CREW_LOGOS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CREW_LOGOS_FILE.open("w", encoding="utf-8") as f:
        json.dump(logos, f, indent=4)

def _logo_by_key(logos: list[dict], key: str) -> Optional[dict]:
    return next((l for l in logos if l["key"] == key), None)

# =========================================================
# HELPERS — STATS
# =========================================================

def _load_stats() -> dict:
    if STATS_FILE.exists():
        try:
            with STATS_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"managers": {}}

def _save_stats(data: dict) -> None:
    STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with STATS_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def _blank_stats(member_id: int, name: str) -> dict:
    return {
        "member_id": member_id,
        "name": name,
        "recruitment": 0,
        "meet_support": 0,
        "manager_actions": 0,
        "issues_reported": 0,
        "warnings_filed": 0,
    }

def _compute_score(stats: dict) -> int:
    return (
        stats.get("recruitment",     0) * RECRUITMENT_POINTS
        + stats.get("meet_support",    0) * MEET_SUPPORT_POINTS
        + stats.get("manager_actions", 0) * MANAGER_ACTION_POINTS
        + stats.get("issues_reported", 0) * ISSUE_REPORT_POINTS
        + stats.get("warnings_filed",  0) * WARNING_FILED_POINTS
    )

def _sorted_managers(managers: dict) -> list:
    rows = list(managers.values())
    for r in rows:
        r["score"] = _compute_score(r)
    rows.sort(
        key=lambda x: (x["score"], x.get("recruitment", 0), x.get("meet_support", 0)),
        reverse=True,
    )
    return rows

# =========================================================
# UI — INTERACTIVE MANAGER HUB SELECT
# =========================================================

class ManagerHubSelect(discord.ui.Select):
    def __init__(self, cog: "ManagerHubSystem"):
        self.cog = cog
        options = [
            discord.SelectOption(label=v["label"][:100], value=k, emoji=v["emoji"],
                                 description="Open this manager hub section.")
            for k, v in SECTION_CONTENT.items()
        ] + [
            discord.SelectOption(label="Live Manager Leaderboard", value="live_leaderboard",
                                 emoji="📈", description="See the current top-performing managers."),
            discord.SelectOption(label="My Performance", value="my_performance",
                                 emoji="👤", description="View your own manager stats and score."),
            discord.SelectOption(label="Manager Actions", value="manager_actions",
                                 emoji="⚙️", description="Log your manager activity with one click."),
        ]
        super().__init__(
            placeholder="📋  Select a manager section...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="diff_interactive_manager_hub_select",
        )

    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]

        if value in SECTION_CONTENT:
            section = SECTION_CONTENT[value]
            embed = discord.Embed(
                title=f"{section['emoji']} {section['label']}",
                description=section["description"],
                color=discord.Color.blurple(),
            )
            embed.set_footer(text=FOOTER_TEXT)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if value == "live_leaderboard":
            await interaction.response.send_message(
                embed=self.cog.build_leaderboard_embed(), ephemeral=True
            )
            return

        if value == "my_performance":
            if not isinstance(interaction.user, discord.Member):
                await interaction.response.send_message("Could not load your profile.", ephemeral=True)
                return
            await interaction.response.send_message(
                embed=self.cog.build_profile_embed(interaction.user), ephemeral=True
            )
            return

        if value == "manager_actions":
            if not isinstance(interaction.user, discord.Member):
                await interaction.response.send_message("Could not open actions.", ephemeral=True)
                return
            await interaction.response.send_message(
                embed=self.cog.build_actions_embed(interaction.user),
                view=ManagerActionsView(self.cog),
                ephemeral=True,
            )
            return

# =========================================================
# UI — CREW LOGOS DROPDOWN
# =========================================================

class CrewLogosSelect(discord.ui.Select):
    def __init__(self, logos: list[dict]):
        ready   = [l for l in logos if l.get("url")]
        pending = [l for l in logos if not l.get("url")]

        options = []
        for logo in ready[:25]:
            options.append(discord.SelectOption(
                label=logo["name"][:100],
                description=(logo.get("description", "DIFF crew logo") or "")[:100],
                value=logo["key"],
                emoji="🎨",
            ))
        for logo in pending[:max(0, 25 - len(options))]:
            options.append(discord.SelectOption(
                label=logo["name"][:100],
                description="⏳ Image not uploaded yet",
                value=logo["key"],
                emoji="🕐",
            ))

        if not options:
            options = [discord.SelectOption(
                label="No logos added yet",
                description="Use !addcrewlogo to upload the preset logos",
                value="__none__",
                emoji="📭",
            )]

        super().__init__(
            placeholder="🎨  Browse crew logos...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="diff_crew_logos_select",
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "__none__":
            await interaction.response.send_message(
                "No logos have been uploaded yet.", ephemeral=True
            )
            return

        logos = _load_logos()
        logo  = _logo_by_key(logos, self.values[0])
        if not logo:
            await interaction.response.send_message("Logo not found.", ephemeral=True)
            return

        if not logo.get("url"):
            await interaction.response.send_message(
                f"**{logo['name']}** hasn't been uploaded yet.\n"
                "Staff can add it with `!addcrewlogo` and an image attachment.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title=f"🎨 {logo['name']}",
            description=logo.get("description", "DIFF crew logo"),
            color=discord.Color.blurple(),
        )
        embed.set_image(url=logo["url"])
        embed.set_footer(text="Different Meets • Crew Logo Gallery")
        await interaction.response.send_message(embed=embed, ephemeral=True)

# =========================================================
# UI — MANAGER ACTIONS BUTTONS
# =========================================================

class ManagerActionsView(discord.ui.View):
    def __init__(self, cog: "ManagerHubSystem"):
        super().__init__(timeout=None)
        self.cog = cog

    async def _check_perm(self, interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Could not verify permissions.", ephemeral=True)
            return False
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(
                "You need **Manage Server** permission to log manager actions.", ephemeral=True
            )
            return False
        return True

    async def _update(self, interaction: discord.Interaction):
        embed = self.cog.build_actions_embed(interaction.user)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="+1 Recruitment", style=discord.ButtonStyle.green,
                       emoji="📣", custom_id="mgr_btn_recruitment")
    async def add_recruitment(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_perm(interaction):
            return
        await self.cog.adjust_stats(interaction.user, recruitment=1)
        await self._update(interaction)

    @discord.ui.button(label="+1 Meet Support", style=discord.ButtonStyle.blurple,
                       emoji="🤝", custom_id="mgr_btn_meet_support")
    async def add_meet_support(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_perm(interaction):
            return
        await self.cog.adjust_stats(interaction.user, meet_support=1)
        await self._update(interaction)

    @discord.ui.button(label="+1 Manager Action", style=discord.ButtonStyle.secondary,
                       emoji="⚙️", custom_id="mgr_btn_action")
    async def add_action(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_perm(interaction):
            return
        await self.cog.adjust_stats(interaction.user, manager_actions=1)
        await self._update(interaction)

    @discord.ui.button(label="+1 Issue Reported", style=discord.ButtonStyle.red,
                       emoji="🚨", custom_id="mgr_btn_issue")
    async def add_issue(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_perm(interaction):
            return
        await self.cog.adjust_stats(interaction.user, issues_reported=1)
        await self._update(interaction)

    @discord.ui.button(label="+1 Warning Filed", style=discord.ButtonStyle.red,
                       emoji="📄", custom_id="mgr_btn_warning")
    async def add_warning(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_perm(interaction):
            return
        await self.cog.adjust_stats(interaction.user, warnings_filed=1)
        await self._update(interaction)

# =========================================================
# UI — COMBINED VIEW (hub select + logos select)
# =========================================================

class ManagerHubView(discord.ui.View):
    def __init__(self, cog: "ManagerHubSystem", logos: Optional[list[dict]] = None):
        super().__init__(timeout=None)
        self.add_item(ManagerHubSelect(cog))
        self.add_item(CrewLogosSelect(logos or _load_logos()))

# =========================================================
# COG
# =========================================================

class ManagerHubSystem(commands.Cog, name="ManagerHubSystem"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(ManagerHubView(self))
        self.bot.add_view(ManagerActionsView(self))

    @commands.Cog.listener()
    async def on_ready(self):
        print("[ManagerHubSystem] Cog ready.")
        await self._auto_upload_logos()

    # ── logo CDN management ───────────────────────────────────

    async def _auto_upload_logos(self):
        logos        = _load_logos()
        existing_keys = {l["key"] for l in logos}

        for preset in PRESET_LOGOS:
            if preset["key"] not in existing_keys:
                logos.append({
                    "key": preset["key"],
                    "name": preset["name"],
                    "description": preset["description"],
                    "url": "",
                    "message_id": None,
                    "storage_channel_id": None,
                })

        refreshed = 0
        for logo in logos:
            mid = logo.get("message_id")
            cid = logo.get("storage_channel_id")
            if mid and cid:
                try:
                    ch  = self.bot.get_channel(cid) or await self.bot.fetch_channel(cid)
                    msg = await ch.fetch_message(mid)
                    if msg.attachments:
                        logo["url"] = msg.attachments[0].proxy_url or msg.attachments[0].url
                        refreshed += 1
                except Exception as e:
                    print(f"[ManagerHubSystem] URL refresh failed for {logo['key']}: {e}")

        missing = [l for l in logos if not l.get("url")]
        if missing:
            storage_ch = self.bot.get_channel(LOGO_STORAGE_CHANNEL_ID)
            if storage_ch is None:
                try:
                    storage_ch = await self.bot.fetch_channel(LOGO_STORAGE_CHANNEL_ID)
                except Exception:
                    storage_ch = None

            if storage_ch:
                logo_dir = Path("diff_data/crew_logos")
                uploaded = 0
                for logo in logos:
                    if logo.get("url"):
                        continue
                    img_path = logo_dir / f"{logo['key']}.png"
                    if not img_path.exists():
                        continue
                    try:
                        msg = await storage_ch.send(
                            content=f"[LOGO STORAGE — do not delete] {logo['name']}",
                            file=discord.File(img_path),
                        )
                        logo["url"]                = msg.attachments[0].proxy_url or msg.attachments[0].url
                        logo["message_id"]         = msg.id
                        logo["storage_channel_id"] = storage_ch.id
                        uploaded += 1
                    except Exception as e:
                        print(f"[ManagerHubSystem] Logo upload failed for {logo['key']}: {e}")
                if uploaded:
                    print(f"[ManagerHubSystem] Uploaded {uploaded} new crew logo(s).")

        if refreshed:
            print(f"[ManagerHubSystem] Refreshed {refreshed} logo URL(s) from stored messages.")
        _save_logos(logos)

    # ── embed builders ───────────────────────────────────────

    def build_main_embed(self) -> discord.Embed:
        logos       = _load_logos()
        ready_count = sum(1 for l in logos if l.get("url"))
        total_count = len(logos)

        embed = discord.Embed(
            title=HUB_TITLE,
            description=HUB_DESCRIPTION,
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="📋 Hub Sections",
            value=(
                "• Crew Managers Roles & Responsibility\n"
                "• Crew Recruitment Roles\n"
                "• Discord Manager Roles\n"
                "• PlayStation Group Chat Manager Roles\n"
                "• Problem To Look Out For\n"
                "• 📈 Live Manager Leaderboard\n"
                "• 👤 My Performance\n"
                "• ⚙️ Manager Actions"
            ),
            inline=False,
        )
        embed.add_field(
            name="🎨 Crew Logo Gallery",
            value=f"{ready_count}/{total_count} logos available — browse using the dropdown below.",
            inline=False,
        )
        embed.add_field(
            name="ℹ️ How To Use",
            value="Select from the first dropdown to open a section or log activity. Select from the second dropdown to view crew logos.",
            inline=False,
        )
        embed.add_field(
            name="📋 Staff Commands",
            value=(
                "`!refreshmanagerhub` — Refresh this panel\n"
                "`!managerboard` — View the manager leaderboard\n"
                "`!managerprofile @user` — View a manager's performance profile\n"
                "`!manageradd @user <field> <amount>` — Add stats to a manager\n"
                "`!managerremove @user <field> <amount>` — Remove stats from a manager\n"
                "`!managerreset @user` — Reset a single manager's profile\n"
                "`!managerresetall` — Reset all manager profiles\n"
                "`!addcrewlogo <crew> <url>` — Add a crew logo to the gallery\n"
                "`!removecrewlogo <crew>` — Remove a crew logo\n"
                "`!listcrewlogos` — List all saved crew logos\n"
                "`!managerhelp` — View all manager commands"
            ),
            inline=False,
        )
        embed.set_footer(text=FOOTER_TEXT)
        return embed

    def build_leaderboard_embed(self) -> discord.Embed:
        data  = _load_stats()
        rows  = _sorted_managers(data.get("managers", {}))
        embed = discord.Embed(
            title="📈 DIFF Manager Leaderboard",
            description="Live manager rankings based on tracked activity.",
            color=discord.Color.green(),
        )
        if rows:
            medals = ["🥇", "🥈", "🥉"]
            lines  = []
            for idx, item in enumerate(rows[:10], start=1):
                prefix = medals[idx - 1] if idx <= 3 else f"**#{idx}**"
                lines.append(
                    f"{prefix} <@{item['member_id']}> — **{item['score']} pts**"
                    f"  `R:{item['recruitment']} MS:{item['meet_support']}"
                    f" A:{item['manager_actions']} I:{item['issues_reported']}"
                    f" W:{item['warnings_filed']}`"
                )
            embed.add_field(name="🏆 Top Managers", value="\n".join(lines), inline=False)
        else:
            embed.add_field(name="🏆 Top Managers", value="No manager stats recorded yet.", inline=False)

        embed.add_field(
            name="📊 Scoring",
            value=(
                f"Recruitment = **{RECRUITMENT_POINTS} pts** | "
                f"Meet Support = **{MEET_SUPPORT_POINTS} pts** | "
                f"Manager Actions = **{MANAGER_ACTION_POINTS} pts** | "
                f"Issues = **{ISSUE_REPORT_POINTS} pt** | "
                f"Warnings = **{WARNING_FILED_POINTS} pt**"
            ),
            inline=False,
        )
        embed.set_footer(text=FOOTER_TEXT)
        return embed

    def build_profile_embed(self, member: discord.Member) -> discord.Embed:
        data  = _load_stats()
        key   = str(member.id)
        stats = data["managers"].get(key, _blank_stats(member.id, str(member)))
        score = _compute_score(stats)
        rows  = _sorted_managers(data.get("managers", {}))
        rank  = next((i + 1 for i, r in enumerate(rows) if str(r["member_id"]) == key), None)

        embed = discord.Embed(
            title=f"📊 My Performance  •  {member.display_name}",
            description="Your current manager activity snapshot.",
            color=discord.Color.gold(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="🏅 Rank",            value=f"#{rank}" if rank else "Unranked", inline=True)
        embed.add_field(name="⭐ Total Score",      value=str(score),                          inline=True)
        embed.add_field(name="\u200b",              value="\u200b",                            inline=True)
        embed.add_field(name="📣 Recruitment",      value=str(stats.get("recruitment",    0)), inline=True)
        embed.add_field(name="🤝 Meet Support",     value=str(stats.get("meet_support",   0)), inline=True)
        embed.add_field(name="⚙️ Manager Actions",  value=str(stats.get("manager_actions",0)), inline=True)
        embed.add_field(name="🔎 Issues Reported",  value=str(stats.get("issues_reported",0)), inline=True)
        embed.add_field(name="⚠️ Warnings Filed",   value=str(stats.get("warnings_filed", 0)), inline=True)
        embed.set_footer(text=FOOTER_TEXT)
        return embed

    def build_actions_embed(self, member: discord.Member) -> discord.Embed:
        data  = _load_stats()
        stats = data["managers"].get(str(member.id), _blank_stats(member.id, str(member)))
        embed = discord.Embed(
            title="⚙️ Manager Actions",
            description=(
                "Use the buttons below to log your manager activity.\n"
                "Each press updates your score and refreshes the live leaderboard."
            ),
            color=discord.Color.blurple(),
        )
        embed.add_field(name="📣 Recruitment",     value=str(stats.get("recruitment",    0)), inline=True)
        embed.add_field(name="🤝 Meet Support",    value=str(stats.get("meet_support",   0)), inline=True)
        embed.add_field(name="⚙️ Manager Actions", value=str(stats.get("manager_actions",0)), inline=True)
        embed.add_field(name="🔎 Issues Reported", value=str(stats.get("issues_reported",0)), inline=True)
        embed.add_field(name="⚠️ Warnings Filed",  value=str(stats.get("warnings_filed", 0)), inline=True)
        embed.add_field(name="⭐ Total Score",      value=str(_compute_score(stats)),          inline=True)
        embed.set_footer(text=FOOTER_TEXT)
        return embed

    # ── panel post/refresh ───────────────────────────────────

    async def post_or_refresh_panel(self):
        state      = _load_state()
        channel_id = state.get("channel_id", MANAGER_HUB_CHANNEL_ID)
        message_id = state.get("message_id")

        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception as e:
                print(f"[ManagerHubSystem] Could not access channel: {e}")
                return False

        logos = _load_logos()
        embed = self.build_main_embed()
        view  = ManagerHubView(self, logos)

        if message_id:
            try:
                msg = await channel.fetch_message(message_id)
                await msg.edit(embed=embed, view=view)
                return True
            except Exception:
                pass

        try:
            msg = await channel.send(embed=embed, view=view)
            state["message_id"] = msg.id
            state["channel_id"] = channel.id
            _save_state(state)
            return True
        except Exception as e:
            print(f"[ManagerHubSystem] Failed to post panel: {e}")
            return False

    # ── stats adjustment ─────────────────────────────────────

    async def adjust_stats(self, member: discord.Member, **deltas) -> dict:
        data = _load_stats()
        key  = str(member.id)
        if key not in data["managers"]:
            data["managers"][key] = _blank_stats(member.id, str(member))
        stats = data["managers"][key]
        stats["name"] = str(member)
        for field, delta in deltas.items():
            stats[field] = max(0, stats.get(field, 0) + delta)
        _save_stats(data)
        await self.post_or_refresh_panel()
        return stats

    # =========================================================
    # PREFIX COMMANDS — PANEL
    # =========================================================

    @commands.command(name="refreshmanagerhub")
    @commands.has_permissions(manage_guild=True)
    async def refresh_hub(self, ctx: commands.Context):
        """Force-refresh the manager hub panel."""
        ok = await self.post_or_refresh_panel()
        await ctx.send("✅ Manager hub refreshed." if ok else "❌ Failed to refresh.", delete_after=8)
        try:
            await ctx.message.delete()
        except Exception:
            pass

    # =========================================================
    # PREFIX COMMANDS — LOGOS
    # =========================================================

    @commands.command(name="addcrewlogo")
    @commands.has_permissions(manage_guild=True)
    async def add_crew_logo(self, ctx: commands.Context, *, name: str):
        """Add or update a crew logo. Attach an image or include a URL at the end.
        Usage: !addcrewlogo Logo Name          (with image attached)
               !addcrewlogo Logo Name https://...
        """
        logos = _load_logos()
        url   = ""
        message_id        = None
        storage_channel_id = None

        parts = name.rsplit(None, 1)
        if len(parts) == 2 and parts[1].startswith("http"):
            name = parts[0].strip()
            url  = parts[1].strip()

        if not url and ctx.message.attachments:
            try:
                storage_ch = self.bot.get_channel(LOGO_STORAGE_CHANNEL_ID)
                if storage_ch is None:
                    storage_ch = await self.bot.fetch_channel(LOGO_STORAGE_CHANNEL_ID)
                upload_msg = await storage_ch.send(
                    content=f"[LOGO STORAGE — do not delete] {name}",
                    file=await ctx.message.attachments[0].to_file(),
                )
                url                = upload_msg.attachments[0].proxy_url or upload_msg.attachments[0].url
                message_id         = upload_msg.id
                storage_channel_id = storage_ch.id
            except Exception as e:
                await ctx.send(f"❌ Failed to upload image: {e}", delete_after=10)
                return

        if not url:
            await ctx.send(
                "❌ Please attach an image or include a URL at the end of the command.",
                delete_after=10,
            )
            return

        key      = name.lower().replace(" ", "_").replace("-", "_")[:40]
        existing = _logo_by_key(logos, key)
        if existing:
            existing["url"]  = url
            existing["name"] = name
            if message_id:
                existing["message_id"]         = message_id
                existing["storage_channel_id"] = storage_channel_id
        else:
            logos.append({
                "key": key, "name": name, "description": "",
                "url": url, "message_id": message_id,
                "storage_channel_id": storage_channel_id,
            })

        _save_logos(logos)
        await self.post_or_refresh_panel()
        await ctx.send(f"✅ Logo **{name}** saved and panel updated.", delete_after=8)
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="removecrewlogo")
    @commands.has_permissions(manage_guild=True)
    async def remove_crew_logo(self, ctx: commands.Context, *, name: str):
        """Remove a crew logo by name.  Usage: !removecrewlogo Logo Name"""
        logos  = _load_logos()
        key    = name.lower().replace(" ", "_").replace("-", "_")[:40]
        before = len(logos)
        logos  = [l for l in logos if l["key"] != key and l["name"].lower() != name.lower()]
        if len(logos) == before:
            await ctx.send(f"❌ No logo found matching `{name}`.", delete_after=8)
            return
        _save_logos(logos)
        await self.post_or_refresh_panel()
        await ctx.send(f"✅ Logo **{name}** removed and panel updated.", delete_after=8)

    @commands.command(name="listcrewlogos")
    @commands.has_permissions(manage_guild=True)
    async def list_crew_logos(self, ctx: commands.Context):
        """List all crew logos and their upload status."""
        logos = _load_logos()
        if not logos:
            await ctx.send("No logos configured yet.", delete_after=10)
            return
        lines = [
            f"{'✅' if l.get('url') else '⏳'} **{l['name']}**  (`{l['key']}`)"
            for l in logos
        ]
        embed = discord.Embed(
            title=f"🎨 Crew Logos ({len(logos)} total)",
            description="\n".join(lines),
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=FOOTER_TEXT)
        await ctx.send(embed=embed)

    # =========================================================
    # PREFIX COMMANDS — MANAGER STATS
    # =========================================================

    @commands.command(name="managerboard")
    @commands.has_permissions(manage_guild=True)
    async def manager_board(self, ctx: commands.Context):
        """Force-refresh the manager hub panel (also updates the leaderboard)."""
        ok = await self.post_or_refresh_panel()
        await ctx.send("✅ Manager hub refreshed." if ok else "❌ Failed.", delete_after=8)
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="managerprofile")
    @commands.has_permissions(manage_guild=True)
    async def manager_profile(self, ctx: commands.Context, member: discord.Member):
        """View a manager's performance profile.  Usage: !managerprofile @member"""
        await ctx.send(embed=self.build_profile_embed(member))

    @commands.command(name="manageradd")
    @commands.has_permissions(manage_guild=True)
    async def manager_add(self, ctx: commands.Context, member: discord.Member, stat: str, amount: int = 1):
        """Add to a manager's stat.
        Usage: !manageradd @member <stat> [amount]
        Stats: r  ms  a  i  w  (recruitment, meet_support, manager_actions, issues, warnings)
        """
        field = VALID_STATS.get(stat.lower())
        if not field:
            await ctx.send(
                "❌ Unknown stat. Use: `r` `ms` `a` `i` `w`\n"
                "(recruitment, meet_support, manager_actions, issues_reported, warnings_filed)",
                delete_after=12,
            )
            return
        if amount <= 0:
            await ctx.send("❌ Amount must be positive.", delete_after=8)
            return
        stats  = await self.adjust_stats(member, **{field: amount})
        label, pts = STAT_LABELS[field]
        score  = _compute_score(stats)
        await ctx.send(
            f"✅ Added **{amount}** {label} (+{amount * pts} pts) to {member.mention}. "
            f"Total score: **{score} pts**.",
            delete_after=10,
        )
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="managerremove")
    @commands.has_permissions(manage_guild=True)
    async def manager_remove(self, ctx: commands.Context, member: discord.Member, stat: str, amount: int = 1):
        """Remove from a manager's stat.
        Usage: !managerremove @member <stat> [amount]
        """
        field = VALID_STATS.get(stat.lower())
        if not field:
            await ctx.send(
                "❌ Unknown stat. Use: `r` `ms` `a` `i` `w`",
                delete_after=12,
            )
            return
        if amount <= 0:
            await ctx.send("❌ Amount must be positive.", delete_after=8)
            return
        stats  = await self.adjust_stats(member, **{field: -amount})
        label, _ = STAT_LABELS[field]
        score  = _compute_score(stats)
        await ctx.send(
            f"✅ Removed **{amount}** {label} from {member.mention}. "
            f"Total score: **{score} pts**.",
            delete_after=10,
        )
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="managerreset")
    @commands.has_permissions(manage_guild=True)
    async def manager_reset_one(self, ctx: commands.Context, member: discord.Member):
        """Reset one manager's stats.  Usage: !managerreset @member"""
        data = _load_stats()
        key  = str(member.id)
        if key in data["managers"]:
            data["managers"].pop(key)
            _save_stats(data)
            await self.post_or_refresh_panel()
            await ctx.send(f"✅ Stats for {member.mention} have been reset.", delete_after=8)
        else:
            await ctx.send(f"ℹ️ {member.mention} has no recorded stats.", delete_after=8)
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="managerresetall")
    @commands.has_permissions(administrator=True)
    async def manager_reset_all(self, ctx: commands.Context):
        """Reset ALL manager stats. Requires Administrator."""
        _save_stats({"managers": {}})
        await self.post_or_refresh_panel()
        await ctx.send("✅ All manager stats have been reset.", delete_after=10)
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="managerhelp")
    @commands.has_permissions(manage_guild=True)
    async def manager_help(self, ctx: commands.Context):
        """Show all manager hub commands."""
        embed = discord.Embed(
            title="📋 Manager Hub Commands",
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="Panel",
            value="`!refreshmanagerhub` — Refresh the manager hub panel",
            inline=False,
        )
        embed.add_field(
            name="Logos",
            value=(
                "`!addcrewlogo Name` *(+ attachment or URL)* — Add/update a logo\n"
                "`!removecrewlogo Name` — Remove a logo\n"
                "`!listcrewlogos` — List all logos\n"
            ),
            inline=False,
        )
        embed.add_field(
            name="Stats",
            value=(
                "`!managerprofile @m` — View a manager's profile\n"
                "`!manageradd @m <stat> [n]` — Add to a stat\n"
                "`!managerremove @m <stat> [n]` — Remove from a stat\n"
                "`!managerreset @m` — Reset one manager\n"
                "`!managerresetall` — Reset everyone *(Admin only)*\n"
            ),
            inline=False,
        )
        embed.add_field(
            name="Stat Aliases",
            value="`r` recruitment  |  `ms` meet support  |  `a` actions  |  `i` issues  |  `w` warnings",
            inline=False,
        )
        embed.set_footer(text=FOOTER_TEXT)
        await ctx.send(embed=embed)


# =========================================================
# SETUP
# =========================================================

async def setup(bot: commands.Bot):
    await bot.add_cog(ManagerHubSystem(bot))
