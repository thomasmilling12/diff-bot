from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import discord
from discord.ext import commands

GUILD_ID = 850386896509337710
MANAGER_HUB_CHANNEL_ID = 1485273802391814224

HUB_TITLE = "🧠 DIFF Manager Hub"
HUB_DESCRIPTION = (
    "The all-in-one management hub for **Different Meets**.\n\n"
    "Use the dropdowns below to review manager duties and browse official DIFF crew logos.\n\n"
    "This panel refreshes cleanly without duplicates."
)
FOOTER_TEXT = "Different Meets • Manager Hub System"
LOGO_URL = ""
BANNER_URL = ""

STATE_FILE     = Path("diff_data/manager_hub_state.json")
CREW_LOGOS_FILE = Path("diff_data/crew_logos.json")

# =========================================================
# PREDEFINED LOGOS (filename → display info)
# URLs are populated by !initcrewlogos or !addcrewlogo
# =========================================================
PRESET_LOGOS: list[dict] = [
    {"key": "diff_classic",       "name": "Different Meets Classic",   "description": "Blue Porsche edition logo — Est. 2020"},
    {"key": "diff_crew_gold",     "name": "DIFF Crew — Gold",          "description": "Gold metallic Different Meets Crew wordmark"},
    {"key": "diff_crew_silver",   "name": "DIFF Crew — Silver",        "description": "Silver metallic Different Meets Crew wordmark"},
    {"key": "diff_5th_anniversary","name": "5th Anniversary",          "description": "Official DIFF Meets 5th Anniversary logo"},
    {"key": "diff_420",           "name": "420 Edition",               "description": "DIFF Meets Crew 420 slime edition"},
    {"key": "dmc_classic",        "name": "DMC Classic",               "description": "Different Meets Crew — black & white DMC logo"},
    {"key": "diff_graffiti",      "name": "Graffiti Style",            "description": "Different Meets Crew graffiti text logo"},
    {"key": "diff_red_black",     "name": "Red & Black — Est. 2020",   "description": "Different Meets Crew bold red/black edition"},
    {"key": "diff_4th_anniversary","name": "4th Anniversary",          "description": "Official DIFF Meets 4th Anniversary logo"},
    {"key": "diff_loyalty_club",  "name": "DIFF Loyalty Club",         "description": "DIFF Meets Loyalty Club official logo"},
    {"key": "diff_chrome_crew",   "name": "Chrome Crew — Est. 2020",   "description": "Different Meets Crew chrome metallic — Est. 2020"},
]

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
# HELPERS
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
# UI — MANAGER SECTIONS DROPDOWN
# =========================================================

class ManagerHubSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=v["label"][:100],
                description="Open this manager hub section.",
                value=k,
                emoji=v["emoji"],
            )
            for k, v in SECTION_CONTENT.items()
        ]
        super().__init__(
            placeholder="📋  Select a manager section...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="diff_manager_hub_select",
        )

    async def callback(self, interaction: discord.Interaction):
        section = SECTION_CONTENT.get(self.values[0])
        if not section:
            await interaction.response.send_message("Section not found.", ephemeral=True)
            return
        embed = discord.Embed(
            title=f"{section['emoji']} {section['label']}",
            description=section["description"],
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=FOOTER_TEXT)
        await interaction.response.send_message(embed=embed, ephemeral=True)


# =========================================================
# UI — CREW LOGOS DROPDOWN
# =========================================================

class CrewLogosSelect(discord.ui.Select):
    def __init__(self, logos: list[dict]):
        ready = [l for l in logos if l.get("url")]
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
                description="Run !initcrewlogos to upload the preset logos",
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
                "No logos have been uploaded yet. Run `!initcrewlogos` to set them up.",
                ephemeral=True,
            )
            return

        logos = _load_logos()
        logo = _logo_by_key(logos, self.values[0])
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
# VIEW
# =========================================================

class ManagerHubView(discord.ui.View):
    def __init__(self, logos: Optional[list[dict]] = None):
        super().__init__(timeout=None)
        self.add_item(ManagerHubSelect())
        self.add_item(CrewLogosSelect(logos or _load_logos()))


# =========================================================
# COG
# =========================================================

class ManagerHubSystem(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(ManagerHubView())

    @commands.Cog.listener()
    async def on_ready(self):
        print("[ManagerHubSystem] Cog ready.")
        await self._auto_upload_logos()
        await self.post_or_refresh_panel()

    async def _auto_upload_logos(self):
        logos = _load_logos()
        existing_keys = {l["key"] for l in logos}

        for preset in PRESET_LOGOS:
            if preset["key"] not in existing_keys:
                logos.append({
                    "key": preset["key"],
                    "name": preset["name"],
                    "description": preset["description"],
                    "url": "",
                })

        missing = [l for l in logos if not l.get("url")]
        if not missing:
            _save_logos(logos)
            return

        channel = self.bot.get_channel(MANAGER_HUB_CHANNEL_ID)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(MANAGER_HUB_CHANNEL_ID)
            except Exception:
                _save_logos(logos)
                return

        logo_dir = Path("diff_data/crew_logos")
        uploaded = 0
        for logo in logos:
            if logo.get("url"):
                continue
            img_path = logo_dir / f"{logo['key']}.png"
            if not img_path.exists():
                continue
            try:
                msg = await channel.send(file=discord.File(img_path))
                logo["url"] = msg.attachments[0].url
                await msg.delete()
                uploaded += 1
            except Exception as e:
                print(f"[ManagerHubSystem] Logo upload failed for {logo['key']}: {e}")

        _save_logos(logos)
        if uploaded:
            print(f"[ManagerHubSystem] Auto-uploaded {uploaded} crew logo(s).")

    def build_main_embed(self) -> discord.Embed:
        logos = _load_logos()
        ready_count = sum(1 for l in logos if l.get("url"))
        total_count = len(logos)

        embed = discord.Embed(
            title=HUB_TITLE,
            description=HUB_DESCRIPTION,
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="📋 Manager Sections",
            value=(
                "• Crew Managers Roles & Responsibility\n"
                "• Crew Recruitment Roles\n"
                "• Discord Manager Roles\n"
                "• PlayStation Group Chat Manager Roles\n"
                "• Problem To Look Out For"
            ),
            inline=True,
        )
        embed.add_field(
            name="🎨 Crew Logo Gallery",
            value=(
                f"{ready_count}/{total_count} logos uploaded\n"
                "Browse all official DIFF crew logos\n"
                "from the dropdown below"
            ),
            inline=True,
        )
        embed.add_field(
            name="How To Use",
            value="Use the dropdowns below — each section opens privately just for you.",
            inline=False,
        )
        embed.set_footer(text=FOOTER_TEXT)
        if LOGO_URL:
            embed.set_thumbnail(url=LOGO_URL)
        if BANNER_URL:
            embed.set_image(url=BANNER_URL)
        return embed

    async def post_or_refresh_panel(self) -> tuple[bool, str]:
        state = _load_state()
        channel_id = state.get("channel_id", MANAGER_HUB_CHANNEL_ID)
        message_id = state.get("message_id")

        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception as e:
                return False, f"Could not access channel: {e}"

        embed = self.build_main_embed()
        view = ManagerHubView()

        if message_id:
            try:
                msg = await channel.fetch_message(message_id)
                await msg.edit(embed=embed, view=view)
                return True, "Manager hub panel refreshed."
            except Exception:
                pass

        try:
            msg = await channel.send(embed=embed, view=view)
            state["message_id"] = msg.id
            state["channel_id"] = channel.id
            _save_state(state)
            return True, "Manager hub panel posted."
        except Exception as e:
            return False, f"Failed to post panel: {e}"

    # ----------------------------------------------------------
    # PANEL COMMANDS
    # ----------------------------------------------------------

    @commands.command(name="postmanagerhub")
    @commands.has_permissions(manage_guild=True)
    async def post_manager_hub(self, ctx: commands.Context):
        ok, msg = await self.post_or_refresh_panel()
        await ctx.send(f"{'✅' if ok else '❌'} {msg}", delete_after=8)
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="refreshmanagerhub")
    @commands.has_permissions(manage_guild=True)
    async def refresh_manager_hub(self, ctx: commands.Context):
        ok, msg = await self.post_or_refresh_panel()
        await ctx.send(f"{'✅' if ok else '❌'} {msg}", delete_after=8)
        try:
            await ctx.message.delete()
        except Exception:
            pass

    # ----------------------------------------------------------
    # LOGO COMMANDS
    # ----------------------------------------------------------

    @commands.command(name="initcrewlogos")
    @commands.has_permissions(manage_guild=True)
    async def init_crew_logos(self, ctx: commands.Context):
        """Upload all preset logos from local files and save their Discord CDN URLs."""
        logos = _load_logos()
        existing_keys = {l["key"] for l in logos}

        for preset in PRESET_LOGOS:
            if preset["key"] not in existing_keys:
                logos.append({
                    "key": preset["key"],
                    "name": preset["name"],
                    "description": preset["description"],
                    "url": "",
                })

        logo_dir = Path("diff_data/crew_logos")
        status_msg = await ctx.send("⏳ Uploading crew logos...")
        uploaded = 0
        skipped = 0

        for logo in logos:
            if logo.get("url"):
                skipped += 1
                continue
            img_path = logo_dir / f"{logo['key']}.png"
            if not img_path.exists():
                continue
            try:
                upload_msg = await ctx.channel.send(file=discord.File(img_path))
                cdn_url = upload_msg.attachments[0].url
                logo["url"] = cdn_url
                await upload_msg.delete()
                uploaded += 1
            except Exception as e:
                print(f"[ManagerHubSystem] Logo upload failed for {logo['key']}: {e}")

        _save_logos(logos)
        await self.post_or_refresh_panel()
        await status_msg.edit(
            content=f"✅ Done — **{uploaded}** logos uploaded, **{skipped}** already set. Panel updated."
        )

    @commands.command(name="addcrewlogo")
    @commands.has_permissions(manage_guild=True)
    async def add_crew_logo(self, ctx: commands.Context, *, name: str):
        """Add or update a crew logo. Attach an image OR provide a URL as the last word.
        Usage: !addcrewlogo Logo Name [optional_url]
               !addcrewlogo Logo Name    (with image attached)
        """
        logos = _load_logos()
        url = ""

        parts = name.rsplit(None, 1)
        if len(parts) == 2 and parts[1].startswith("http"):
            name = parts[0].strip()
            url = parts[1].strip()

        if not url and ctx.message.attachments:
            try:
                upload_msg = await ctx.channel.send(file=await ctx.message.attachments[0].to_file())
                url = upload_msg.attachments[0].url
                await upload_msg.delete()
            except Exception as e:
                await ctx.send(f"❌ Failed to upload image: {e}", delete_after=10)
                return

        if not url:
            await ctx.send(
                "❌ Please attach an image or include a URL at the end of the command.", delete_after=10
            )
            return

        key = name.lower().replace(" ", "_").replace("-", "_")[:40]
        existing = _logo_by_key(logos, key)
        if existing:
            existing["url"] = url
            existing["name"] = name
        else:
            logos.append({"key": key, "name": name, "description": "", "url": url})

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
        """Remove a crew logo by name."""
        logos = _load_logos()
        key = name.lower().replace(" ", "_").replace("-", "_")[:40]
        before = len(logos)
        logos = [l for l in logos if l["key"] != key and l["name"].lower() != name.lower()]
        if len(logos) == before:
            await ctx.send(f"❌ No logo found matching `{name}`.", delete_after=8)
            return
        _save_logos(logos)
        await self.post_or_refresh_panel()
        await ctx.send(f"✅ Logo **{name}** removed and panel updated.", delete_after=8)
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="listcrewlogos")
    @commands.has_permissions(manage_guild=True)
    async def list_crew_logos(self, ctx: commands.Context):
        """List all crew logos and their upload status."""
        logos = _load_logos()
        if not logos:
            await ctx.send("No logos found. Run `!initcrewlogos` to set up the preset logos.")
            return
        lines = []
        for logo in logos:
            status = "✅" if logo.get("url") else "⏳"
            lines.append(f"{status} **{logo['name']}** (`{logo['key']}`)")
        embed = discord.Embed(
            title="🎨 Crew Logo List",
            description="\n".join(lines),
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=f"{sum(1 for l in logos if l.get('url'))}/{len(logos)} logos uploaded")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(ManagerHubSystem(bot))
