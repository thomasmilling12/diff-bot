import json
import asyncio
from pathlib import Path

import discord
from discord.ext import commands, tasks

# =========================================================
# CONFIG
# =========================================================

GUILD_ID                  = 850386896509337710
COLOR_TEAM_CHANNEL_ID     = 1485453653916520549   # #color-team (where the unified panel lives)
COLOR_INFO_CHANNEL_ID     = 1177436572304556084   # #color-information (link button)
COLOR_SUBMISSION_CHANNEL_ID = 1177434999381831680 # #color-submission (link button)

COLOR_TEAM_ROLE_ID        = 1115495008670330902
URGENT_PING_ROLE_ID       = 0

MANAGER_ROLE_IDS: list[int] = []

PANEL_HEADER_URL        = ""
ANNOUNCEMENT_BANNER_URL = ""
DIFF_LOGO_URL           = ""

UNIFIED_COLOR_TEAM_TAG = "Different Meets • Color Team"

# Data files
DATA_FILE          = Path("diff_data/color_team_announcement_panel.json")
COLOR_OPS_STATE_FILE = Path("diff_data/diff_color_ops_state.json")

# Old panel titles to clean up
OLD_PANEL_TITLES = {
    "🎨 DIFF Color Team Coordination",
    "🏆 DIFF Top Color Contributors",
    "🎨 DIFF Color Team Announcement Center",
    "DIFF Color Team Coordination",
    "DIFF Top Color Contributors",
    "DIFF Color Team Announcement Center",
}


# =========================================================
# STORAGE
# =========================================================

def load_data() -> dict:
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_data(data: dict) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _load_color_ops() -> dict:
    if COLOR_OPS_STATE_FILE.exists():
        try:
            return json.loads(COLOR_OPS_STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


# =========================================================
# HELPERS
# =========================================================

def user_is_manager(member: discord.Member) -> bool:
    if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
        return True
    if MANAGER_ROLE_IDS:
        role_ids = {role.id for role in member.roles}
        return any(rid in role_ids for rid in MANAGER_ROLE_IDS)
    return False


def get_color_team_ping() -> str:
    return f"<@&{COLOR_TEAM_ROLE_ID}>" if COLOR_TEAM_ROLE_ID else "@Color Team"


def get_urgent_ping() -> str:
    return f"<@&{URGENT_PING_ROLE_ID}>" if URGENT_PING_ROLE_ID else ""


def maybe_set_image(embed: discord.Embed, url: str) -> None:
    if url and url.strip():
        embed.set_image(url=url.strip())


def maybe_set_thumbnail(embed: discord.Embed, url: str) -> None:
    if url and url.strip():
        embed.set_thumbnail(url=url.strip())


def _build_leaderboard_lines() -> list[str]:
    try:
        state = _load_color_ops()
        contributors: dict = state.get("colors", {}).get("contributors", {})
        if not contributors:
            return ["No contributor data logged yet."]
        sorted_rows = sorted(
            contributors.items(),
            key=lambda kv: (kv[1].get("win_count", 0), kv[1].get("submission_count", 0)),
            reverse=True,
        )
        lines = []
        for idx, (_, d) in enumerate(sorted_rows[:5], start=1):
            display = d.get("display_name") or "Unknown"
            wins    = d.get("win_count", 0)
            subs    = d.get("submission_count", 0)
            medal   = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][idx - 1]
            lines.append(f"{medal} **{display}** — 🏆 `{wins}` wins · 🎨 `{subs}` subs")
        return lines
    except Exception:
        return ["Leaderboard temporarily unavailable."]


# =========================================================
# ANNOUNCEMENT TYPES
# =========================================================

ANNOUNCEMENT_TYPES: dict[str, dict] = {
    "general_update": {
        "label":        "General Update",
        "emoji":        "🎨",
        "title_prefix": "DIFF Color Team Update",
        "color":        0xF59E0B,
        "description":  "General Color Team notices and updates.",
    },
    "weekly_color": {
        "label":        "Weekly Color",
        "emoji":        "🌈",
        "title_prefix": "DIFF Weekly Color Notice",
        "color":        0xFBBF24,
        "description":  "Use for weekly crew color announcements.",
    },
    "submission_notice": {
        "label":        "Submission Notice",
        "emoji":        "📥",
        "title_prefix": "DIFF Color Submission Notice",
        "color":        0xFB923C,
        "description":  "Use for color requests, drops, and submissions.",
    },
    "reminder": {
        "label":        "Reminder",
        "emoji":        "⏰",
        "title_prefix": "DIFF Color Team Reminder",
        "color":        0xD97706,
        "description":  "Use for reminders and deadlines.",
    },
    "urgent_notice": {
        "label":        "Urgent Notice",
        "emoji":        "🚨",
        "title_prefix": "DIFF Urgent Color Notice",
        "color":        0xEF4444,
        "description":  "Use for urgent Color Team updates.",
    },
    "event_support": {
        "label":        "Event Support",
        "emoji":        "🏁",
        "title_prefix": "DIFF Event Color Support",
        "color":        0xF97316,
        "description":  "Use for meet/event-related Color Team coordination.",
    },
}

DEFAULT_TYPE = "general_update"


# =========================================================
# PER-USER STATE (in-memory)
# =========================================================

class ColorTeamState:
    def __init__(self):
        self._selection: dict[int, str]  = {}
        self._urgent:    dict[int, bool] = {}

    def set_selection(self, user_id: int, value: str) -> None:
        self._selection[user_id] = value

    def get_selection(self, user_id: int) -> str:
        return self._selection.get(user_id, DEFAULT_TYPE)

    def set_urgent(self, user_id: int, value: bool) -> None:
        self._urgent[user_id] = value

    def get_urgent(self, user_id: int) -> bool:
        return self._urgent.get(user_id, False)


STATE = ColorTeamState()


# =========================================================
# EMBEDS
# =========================================================

def build_unified_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🎨 DIFF Color Team",
        description=(
            "Welcome to the Color Team hub. This is where coordination, tracking, and "
            "announcements all live — in one clean panel.\n\n"
            "**What this area is used for:**\n"
            "• Coordinating weekly crew color changes\n"
            "• Discussing color ideas and submissions\n"
            "• Preparing voting posts and announcements\n"
            "• Keeping the team updated on current color plans"
        ),
        color=discord.Color.purple(),
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
    leaderboard_text = "\n".join(_build_leaderboard_lines())
    embed.add_field(
        name="🏆 Top Color Contributors",
        value=leaderboard_text,
        inline=False,
    )
    embed.add_field(
        name="📢 Announcement Center",
        value=(
            "Managers can send branded Color Team announcements directly from this panel.\n"
            "**How to use:** Choose a type from the dropdown → toggle urgent mode if needed "
            "→ press **Open Announcement Form** → submit."
        ),
        inline=False,
    )
    embed.set_footer(text=f"{UNIFIED_COLOR_TEAM_TAG} • Updates automatically")
    maybe_set_thumbnail(embed, DIFF_LOGO_URL)
    return embed


def build_sent_embed(
    manager: discord.Member,
    announcement_type: str,
    custom_title: str,
    body: str,
    footer_text: str,
    urgent_mode: bool,
) -> discord.Embed:
    info        = ANNOUNCEMENT_TYPES[announcement_type]
    final_title = custom_title.strip() if custom_title.strip() else info["title_prefix"]
    if urgent_mode:
        final_title = f"URGENT • {final_title}"

    embed = discord.Embed(
        title=f"{info['emoji']} {final_title}",
        description=body,
        color=info["color"],
    )
    embed.set_author(
        name=f"DIFF Management • {manager.display_name}",
        icon_url=manager.display_avatar.url,
    )
    embed.add_field(name="Type",    value=info["label"],           inline=True)
    embed.add_field(name="Target",  value=get_color_team_ping(),   inline=True)
    embed.add_field(name="Sent By", value=manager.mention,         inline=True)
    if urgent_mode:
        embed.add_field(name="Priority", value="🚨 Urgent mode enabled", inline=False)
    maybe_set_image(embed, ANNOUNCEMENT_BANNER_URL)
    maybe_set_thumbnail(embed, DIFF_LOGO_URL)
    embed.set_footer(text=footer_text.strip() if footer_text.strip() else "DIFF Color Team")
    return embed


# =========================================================
# MODAL
# =========================================================

class ColorTeamAnnouncementModal(discord.ui.Modal):
    def __init__(self, announcement_type: str, urgent_mode: bool):
        info = ANNOUNCEMENT_TYPES[announcement_type]
        super().__init__(title=f"{info['label']} Announcement")
        self.announcement_type = announcement_type
        self.urgent_mode       = urgent_mode

        self.custom_title = discord.ui.TextInput(
            label="Custom title",
            placeholder=info["title_prefix"],
            required=False,
            max_length=100,
        )
        self.body_text = discord.ui.TextInput(
            label="Announcement message",
            placeholder="Write the full Color Team announcement here...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=2000,
        )
        self.footer_text = discord.ui.TextInput(
            label="Footer / sign-off",
            placeholder="DIFF Color Team",
            required=False,
            max_length=100,
        )
        self.add_item(self.custom_title)
        self.add_item(self.body_text)
        self.add_item(self.footer_text)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("This can only be used in a server.", ephemeral=True)
            return
        if not user_is_manager(interaction.user):
            await interaction.response.send_message("You do not have permission to use this panel.", ephemeral=True)
            return

        channel = interaction.guild.get_channel(COLOR_TEAM_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("Color Team channel not found.", ephemeral=True)
            return

        pings   = [get_color_team_ping()]
        if self.urgent_mode and get_urgent_ping():
            pings.append(get_urgent_ping())
        content = " ".join(p for p in pings if p).strip()

        embed = build_sent_embed(
            manager=interaction.user,
            announcement_type=self.announcement_type,
            custom_title=self.custom_title.value or "",
            body=self.body_text.value,
            footer_text=self.footer_text.value or "",
            urgent_mode=self.urgent_mode,
        )

        await channel.send(
            content=content,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True, users=True, everyone=False),
        )
        await interaction.response.send_message("✅ Color Team announcement sent.", ephemeral=True)


# =========================================================
# DROPDOWNS
# =========================================================

class ColorTeamTypeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=v["label"],
                value=k,
                emoji=v["emoji"],
                description=v["description"][:100],
            )
            for k, v in ANNOUNCEMENT_TYPES.items()
        ]
        super().__init__(
            placeholder="📢 Choose announcement type...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="diff_unified_color_type_select",
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("This can only be used in a server.", ephemeral=True)
            return
        if not user_is_manager(interaction.user):
            await interaction.response.send_message("You need Manager+ to send announcements.", ephemeral=True)
            return
        selected = self.values[0]
        STATE.set_selection(interaction.user.id, selected)
        info = ANNOUNCEMENT_TYPES[selected]
        await interaction.response.send_message(
            f"✅ Announcement type set to **{info['label']}** {info['emoji']}.",
            ephemeral=True,
        )


# =========================================================
# UNIFIED VIEW
# =========================================================

class UnifiedColorTeamView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        # Row 0: Quick-link buttons
        self.add_item(discord.ui.Button(
            label="Color Information",
            style=discord.ButtonStyle.link,
            url=f"https://discord.com/channels/{GUILD_ID}/{COLOR_INFO_CHANNEL_ID}",
            emoji="🎨",
            row=0,
        ))
        self.add_item(discord.ui.Button(
            label="Color Submission",
            style=discord.ButtonStyle.link,
            url=f"https://discord.com/channels/{GUILD_ID}/{COLOR_SUBMISSION_CHANNEL_ID}",
            emoji="🗳️",
            row=0,
        ))

        # Row 1: Announcement type select (manager-only)
        self.add_item(ColorTeamTypeSelect())

    # Row 2: Action buttons

    @discord.ui.button(
        label="Urgent Mode",
        emoji="🚨",
        style=discord.ButtonStyle.red,
        custom_id="diff_unified_color_toggle_urgent",
        row=2,
    )
    async def toggle_urgent(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Server only.", ephemeral=True)
            return
        if not user_is_manager(interaction.user):
            await interaction.response.send_message("Manager+ only.", ephemeral=True)
            return
        new_val = not STATE.get_urgent(interaction.user.id)
        STATE.set_urgent(interaction.user.id, new_val)
        status = "**enabled** 🔴" if new_val else "**disabled** ⚫"
        await interaction.response.send_message(f"🚨 Urgent mode {status}.", ephemeral=True)

    @discord.ui.button(
        label="Open Announcement Form",
        emoji="📢",
        style=discord.ButtonStyle.blurple,
        custom_id="diff_unified_color_open_form",
        row=2,
    )
    async def open_form(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Server only.", ephemeral=True)
            return
        if not user_is_manager(interaction.user):
            await interaction.response.send_message("Manager+ only.", ephemeral=True)
            return
        selected    = STATE.get_selection(interaction.user.id)
        urgent_mode = STATE.get_urgent(interaction.user.id)
        await interaction.response.send_modal(ColorTeamAnnouncementModal(selected, urgent_mode))

    @discord.ui.button(
        label="Refresh Panel",
        emoji="♻️",
        style=discord.ButtonStyle.gray,
        custom_id="diff_unified_color_refresh_panel",
        row=2,
    )
    async def refresh_panel(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Server only.", ephemeral=True)
            return
        if not user_is_manager(interaction.user):
            await interaction.response.send_message("Manager+ only.", ephemeral=True)
            return
        await ensure_unified_color_panel(interaction.client)
        await interaction.response.send_message("✅ Color Team panel refreshed.", ephemeral=True)


# Keep old view registered for persistence (button custom_ids may still exist in Discord)
class ColorTeamAnnouncementPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)


# =========================================================
# PANEL MANAGEMENT
# =========================================================

async def ensure_unified_color_panel(bot: commands.Bot) -> None:
    data = load_data()
    try:
        channel = bot.get_channel(COLOR_TEAM_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            channel = await bot.fetch_channel(COLOR_TEAM_CHANNEL_ID)
    except Exception as e:
        print(f"[UnifiedColorTeam] Channel not found: {e}")
        return

    embed   = build_unified_embed()
    view    = UnifiedColorTeamView()
    msg_id  = data.get("unified_panel_message_id")

    # Try to edit existing tracked panel
    if msg_id:
        try:
            msg = await channel.fetch_message(int(msg_id))
            await msg.edit(content=None, embed=embed, view=view)
            print("[UnifiedColorTeam] Existing panel refreshed.")
            return
        except discord.NotFound:
            data.pop("unified_panel_message_id", None)
        except Exception as e:
            print(f"[UnifiedColorTeam] Could not edit saved panel: {e}")

    # Scan history — clean up old panels, keep unified one
    found_ids: list[int] = []
    try:
        async for msg in channel.history(limit=60):
            if msg.author != bot.user or not msg.embeds:
                continue
            footer_text = (msg.embeds[0].footer.text or "")
            title_text  = (msg.embeds[0].title or "")
            if UNIFIED_COLOR_TEAM_TAG in footer_text:
                found_ids.append(msg.id)
            elif title_text in OLD_PANEL_TITLES:
                try:
                    await msg.delete()
                    await asyncio.sleep(0.5)
                except Exception:
                    pass
    except Exception as e:
        print(f"[UnifiedColorTeam] History scan failed: {e}")

    # If we found an existing unified panel, edit it
    if found_ids:
        try:
            msg = await channel.fetch_message(found_ids[0])
            await msg.edit(content=None, embed=embed, view=view)
            data["unified_panel_message_id"] = found_ids[0]
            save_data(data)
            # Delete any duplicate unified panels
            for dup_id in found_ids[1:]:
                try:
                    dup = await channel.fetch_message(dup_id)
                    await dup.delete()
                    await asyncio.sleep(0.4)
                except Exception:
                    pass
            print("[UnifiedColorTeam] Found existing unified panel and refreshed it.")
            return
        except Exception as e:
            print(f"[UnifiedColorTeam] Could not reuse found panel: {e}")

    # Post fresh
    new_msg = await channel.send(embed=embed, view=view)
    data["unified_panel_message_id"] = new_msg.id
    save_data(data)
    print("[UnifiedColorTeam] New unified panel posted.")


# =========================================================
# COG
# =========================================================

class ColorTeamAnnouncementPanel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(UnifiedColorTeamView())
        self.bot.add_view(ColorTeamAnnouncementPanelView())
        self._refresh_task: tasks.Loop | None = None

    def cog_unload(self):
        if self._refresh_task and self._refresh_task.is_running():
            self._refresh_task.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        if getattr(self.bot, "_diff_unified_color_team_ready", False):
            return
        self.bot._diff_unified_color_team_ready = True
        await ensure_unified_color_panel(self.bot)

        if not self._refresh_task or not self._refresh_task.is_running():
            self._refresh_task = tasks.loop(minutes=5)(self._auto_refresh)
            self._refresh_task.start()

        print("[UnifiedColorTeam] Cog ready.")

    async def _auto_refresh(self):
        try:
            await ensure_unified_color_panel(self.bot)
        except Exception as e:
            print(f"[UnifiedColorTeam] Auto-refresh error: {e}")

    # ------------------------------------------------------------------
    # Commands

    @commands.command(name="colorteampanel")
    @commands.has_permissions(manage_guild=True)
    async def colorteampanel(self, ctx: commands.Context):
        """Refresh the unified Color Team panel."""
        await ensure_unified_color_panel(self.bot)
        try:
            await ctx.message.delete()
        except Exception:
            pass
        await ctx.send("✅ Color Team panel refreshed.", delete_after=8)

    @commands.command(name="colorannouncepanel")
    @commands.has_permissions(manage_guild=True)
    async def colorannouncepanel(self, ctx: commands.Context):
        """Alias — refreshes the unified Color Team panel."""
        await ensure_unified_color_panel(self.bot)
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="setcolorteamrole")
    @commands.has_permissions(administrator=True)
    async def setcolorteamrole(self, ctx: commands.Context, role: discord.Role):
        global COLOR_TEAM_ROLE_ID
        COLOR_TEAM_ROLE_ID = role.id
        await ctx.send(f"✅ Color Team role set to {role.mention}", delete_after=10)

    @commands.command(name="setcolorurgentrole")
    @commands.has_permissions(administrator=True)
    async def setcolorurgentrole(self, ctx: commands.Context, role: discord.Role):
        global URGENT_PING_ROLE_ID
        URGENT_PING_ROLE_ID = role.id
        await ctx.send(f"✅ Color Team urgent ping role set to {role.mention}", delete_after=10)


async def setup(bot: commands.Bot):
    await bot.add_cog(ColorTeamAnnouncementPanel(bot))
