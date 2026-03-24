from __future__ import annotations

import json
from pathlib import Path

import discord
from discord.ext import commands

GUILD_ID = 850386896509337710
MANAGER_HUB_CHANNEL_ID = 1485273802391814224

HUB_TITLE = "🧠 DIFF Manager Hub"
HUB_DESCRIPTION = (
    "The all-in-one management hub for **Different Meets**.\n\n"
    "Use the dropdown menu below to review manager duties, recruitment responsibilities, "
    "Discord management expectations, PlayStation group chat management, and common issues to watch for.\n\n"
    "This panel refreshes cleanly without duplicates."
)
FOOTER_TEXT = "Different Meets • Manager Hub System"
LOGO_URL = ""
BANNER_URL = ""

STATE_FILE = Path("diff_data/manager_hub_state.json")

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
            placeholder="Select a manager section to read...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="diff_manager_hub_select",
        )

    async def callback(self, interaction: discord.Interaction):
        section = SECTION_CONTENT.get(self.values[0])
        if not section:
            await interaction.response.send_message(
                "That section could not be found.", ephemeral=True
            )
            return
        embed = discord.Embed(
            title=f"{section['emoji']} {section['label']}",
            description=section["description"],
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=FOOTER_TEXT)
        if LOGO_URL:
            embed.set_thumbnail(url=LOGO_URL)
        if BANNER_URL:
            embed.set_image(url=BANNER_URL)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class ManagerHubView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ManagerHubSelect())


class ManagerHubSystem(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(ManagerHubView())

    @commands.Cog.listener()
    async def on_ready(self):
        print("[ManagerHubSystem] Cog ready.")
        await self.post_or_refresh_panel()

    def build_main_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=HUB_TITLE,
            description=HUB_DESCRIPTION,
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="Included Sections",
            value=(
                "• Crew Managers Roles & Responsibility\n"
                "• Crew Recruitment Roles\n"
                "• Discord Manager Roles\n"
                "• PlayStation Group Chat Manager Roles\n"
                "• Problem To Look Out For"
            ),
            inline=False,
        )
        embed.add_field(
            name="How To Use",
            value="Use the dropdown menu below to open each section in a clean private embed.",
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
                return False, f"Could not access the manager hub channel: {e}"

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
            return False, f"Failed to post manager hub panel: {e}"

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


async def setup(bot: commands.Bot):
    await bot.add_cog(ManagerHubSystem(bot))
