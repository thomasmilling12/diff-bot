from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Optional

import discord
from discord.ext import commands

# =========================================================
# CONFIG — mirrors bot.py constants
# =========================================================
MEET_INFO_CHANNEL_ID      = 1266933655486332999
MEET_RULES_CHANNEL_ID     = 1047161846257438743
JOIN_MEETS_CHANNEL_ID     = 1277084633858576406
UPCOMING_MEET_CHANNEL_ID  = 1485861257708834836
SUPPORT_TICKETS_CHANNEL_ID = 1156363575150002226
DIFF_HOSTS_CHANNEL_ID     = 1195953265377021952
STAFF_LOGS_CHANNEL_ID     = 1485265848099799163
GUILD_ID                  = 850386896509337710

DATA_DIR        = "diff_data"
CONFIG_FILE     = "diff_data/bot_config.json"

DIFF_LOGO_URL = (
    "https://media.discordapp.net/attachments/1107375326625005719/"
    "1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm="
    "2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
    "&=&format=webp&quality=lossless&width=1376&height=917"
)
DIFF_BANNER_URL = (
    "https://media.discordapp.net/attachments/1107375326625005719/"
    "1102966520086732902/Diff_Banner.png"
)


# =========================================================
# HELPERS
# =========================================================
def _load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _build_channel_link(guild_id: int, channel_id: int) -> str:
    return f"https://discord.com/channels/{guild_id}/{channel_id}"


def _build_embed() -> discord.Embed:
    embed = discord.Embed(
        title="📘 DIFF Meets — Meet Info",
        description=(
            "Everything you need to know before joining a **DIFF Car Meet**.\n"
            "Read each section carefully — these apply to every session.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=0xC9A227,
    )
    embed.add_field(
        name="🎙️ Voice Channel",
        value=(
            "▢ Check the VC name before joining to make sure you're in the correct session.\n"
            "▢ **Hosts can mute or kick you if you talk over them or break meet rules.**"
        ),
        inline=False,
    )
    embed.add_field(
        name="🛠️ Report a Player",
        value=(
            "▢ Having an issue with someone at the meet or on the server?\n"
            f"▢ Open a ticket in <#{SUPPORT_TICKETS_CHANNEL_ID}> — the DIFF Management team will assist you."
        ),
        inline=False,
    )
    embed.add_field(
        name="⚠️ Warnings & Bans",
        value=(
            f"▢ Warnings are issued for breaking rules listed in <#{MEET_RULES_CHANNEL_ID}>.\n"
            "▢ **Two warnings = ban** from the server and all meets.\n"
            "▢ You'll receive a DM from a Crew Manager explaining the reason.\n"
            "▢ **Ban Appeals:** you may appeal after **30 days**. Hosts & Management vote on every appeal."
        ),
        inline=False,
    )
    embed.add_field(
        name="🚗 How to Join the Meets",
        value=(
            "▢ You must be in our Discord server.\n"
            "▢ Your Discord name must match your PSN.\n"
            f"▢ Complete the steps in <#{JOIN_MEETS_CHANNEL_ID}> to get access and update your name.\n"
            f"▢ When a meet is live, add the hosts listed in <#{DIFF_HOSTS_CHANNEL_ID}> and track updates in <#{UPCOMING_MEET_CHANNEL_ID}>.\n"
            "▢ Hosts will only add you back if you send a **screen recording of your garages**."
        ),
        inline=False,
    )
    embed.set_thumbnail(url=DIFF_LOGO_URL)
    embed.set_image(url=DIFF_BANNER_URL)
    embed.set_footer(text="DIFF Meets • Read everything before joining")
    return embed


# =========================================================
# MODALS
# =========================================================
class _SuggestionModal(discord.ui.Modal, title="Suggest an Improvement"):
    category = discord.ui.TextInput(
        label="Category",
        placeholder="Meet Format / Rules / Discord / Hosts / Other",
        max_length=60, required=True,
    )
    suggestion = discord.ui.TextInput(
        label="Your Suggestion",
        placeholder="Describe your idea or improvement clearly…",
        style=discord.TextStyle.paragraph, max_length=1000, required=True,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="💡 Improvement Suggestion",
            color=0xFEE75C,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="Category",     value=str(self.category),   inline=True)
        embed.add_field(name="Submitted By", value=f"{interaction.user.mention}\n`{interaction.user.id}`", inline=True)
        embed.add_field(name="Suggestion",   value=str(self.suggestion), inline=False)
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.set_footer(text="DIFF Meets • Suggestion System")
        log_ch = interaction.client.get_channel(STAFF_LOGS_CHANNEL_ID)
        if isinstance(log_ch, discord.TextChannel):
            try:
                await log_ch.send(embed=embed)
            except Exception:
                pass
        await interaction.response.send_message(
            "💡 Thanks for the suggestion — it's been sent to the DIFF team.", ephemeral=True
        )


class _PlayerReportModal(discord.ui.Modal, title="Report a Player"):
    reported_user = discord.ui.TextInput(
        label="Player Name / PSN / Discord",
        placeholder="Username, PSN, or @mention",
        max_length=100, required=True,
    )
    incident = discord.ui.TextInput(
        label="What happened?",
        placeholder="Describe the incident clearly — when, where, and what they did…",
        style=discord.TextStyle.paragraph, max_length=1000, required=True,
    )
    evidence = discord.ui.TextInput(
        label="Evidence (optional)",
        placeholder="Any screenshots, clips, or video links",
        max_length=300, required=False,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="🚨 Player Report",
            color=0xED4245,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="Reported Player", value=str(self.reported_user), inline=True)
        embed.add_field(name="Reported By",     value=f"{interaction.user.mention}\n`{interaction.user.id}`", inline=True)
        embed.add_field(name="Incident",        value=str(self.incident),      inline=False)
        if str(self.evidence).strip():
            embed.add_field(name="Evidence",    value=str(self.evidence),      inline=False)
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.set_footer(text="DIFF Meets • Player Report")
        log_ch = interaction.client.get_channel(STAFF_LOGS_CHANNEL_ID)
        if isinstance(log_ch, discord.TextChannel):
            try:
                await log_ch.send(embed=embed)
            except Exception:
                pass
        await interaction.response.send_message(
            "🚨 Your report has been sent to the DIFF Management team. Thank you.", ephemeral=True
        )


# =========================================================
# FEEDBACK DROPDOWN
# =========================================================
class _MeetInfoFeedbackSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            custom_id="diff_meetinfo_feedback_select_v1",
            placeholder="📝 Feedback, suggestions, or reports…",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Submit Meet Feedback",
                    value="feedback",
                    emoji="📝",
                    description="Rate a meet and leave detailed feedback for the host.",
                ),
                discord.SelectOption(
                    label="Suggest an Improvement",
                    value="suggest",
                    emoji="💡",
                    description="Suggest a change to how DIFF meets or the server works.",
                ),
                discord.SelectOption(
                    label="Report a Player",
                    value="report",
                    emoji="🚨",
                    description="Report someone for breaking rules at a meet or on Discord.",
                ),
                discord.SelectOption(
                    label="Common Questions (FAQ)",
                    value="faq",
                    emoji="❓",
                    description="Quick answers to the most common meet questions.",
                ),
            ],
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        selected = self.values[0]

        if selected == "feedback":
            from cogs.diff_feedback_system import FeedbackModal
            cog = interaction.client.cogs.get("FeedbackSystem")
            if cog is None:
                return await interaction.response.send_message(
                    "Feedback system temporarily unavailable.", ephemeral=True
                )
            await interaction.response.send_modal(FeedbackModal(cog))

        elif selected == "suggest":
            await interaction.response.send_modal(_SuggestionModal())

        elif selected == "report":
            await interaction.response.send_modal(_PlayerReportModal())

        elif selected == "faq":
            embed = discord.Embed(
                title="❓ DIFF Meets — Common Questions",
                description="Quick answers to the most frequently asked questions.",
                color=0xC9A227,
                timestamp=datetime.now(timezone.utc),
            )
            embed.add_field(
                name="How do I join a meet?",
                value=f"Complete the steps in <#{JOIN_MEETS_CHANNEL_ID}>, make sure your Discord name matches your PSN, then add the hosts listed in <#{DIFF_HOSTS_CHANNEL_ID}>.",
                inline=False,
            )
            embed.add_field(
                name="What garages do I need?",
                value="Send a screen recording of your garages to the host. They will only add you once this is received.",
                inline=False,
            )
            embed.add_field(
                name="When is the next meet?",
                value=f"Check <#{UPCOMING_MEET_CHANNEL_ID}> for all scheduled meets and updates.",
                inline=False,
            )
            embed.add_field(
                name="I got a warning — what happens next?",
                value=f"A second warning results in a ban. Check the rules in <#{MEET_RULES_CHANNEL_ID}> to avoid further warnings.",
                inline=False,
            )
            embed.add_field(
                name="Can I appeal a ban?",
                value="Yes — after 30 days. Hosts and Management vote on every appeal. Open a ticket to start the process.",
                inline=False,
            )
            embed.add_field(
                name="What cars are allowed?",
                value=f"No weaponized, armored, or modded cars. Check the full rules in <#{MEET_RULES_CHANNEL_ID}>.",
                inline=False,
            )
            embed.set_thumbnail(url=DIFF_LOGO_URL)
            embed.set_footer(text="DIFF Meets • FAQ")
            await interaction.response.send_message(embed=embed, ephemeral=True)


# =========================================================
# MEET INFO VIEW  (updated persistent view)
# =========================================================
class MeetInfoViewV2(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="General Rules",   style=discord.ButtonStyle.link, emoji="📜", url=_build_channel_link(GUILD_ID, MEET_RULES_CHANNEL_ID),       row=0))
        self.add_item(discord.ui.Button(label="Join Meets",      style=discord.ButtonStyle.link, emoji="📥", url=_build_channel_link(GUILD_ID, JOIN_MEETS_CHANNEL_ID),        row=0))
        self.add_item(discord.ui.Button(label="Upcoming Meet",   style=discord.ButtonStyle.link, emoji="📅", url=_build_channel_link(GUILD_ID, UPCOMING_MEET_CHANNEL_ID),     row=0))
        self.add_item(discord.ui.Button(label="Support Tickets", style=discord.ButtonStyle.link, emoji="🎟️", url=_build_channel_link(GUILD_ID, SUPPORT_TICKETS_CHANNEL_ID),  row=0))
        self.add_item(discord.ui.Button(label="Hosts",           style=discord.ButtonStyle.link, emoji="👥", url=_build_channel_link(GUILD_ID, DIFF_HOSTS_CHANNEL_ID),        row=0))
        self.add_item(_MeetInfoFeedbackSelect())


# =========================================================
# COG
# =========================================================
class MeetInfoPatchCog(commands.Cog, name="MeetInfoPatch"):
    def __init__(self, bot: commands.Bot):
        self.bot  = bot
        self.view = MeetInfoViewV2()
        bot.add_view(self.view)

    def _get_meet_info_msg_id(self) -> Optional[int]:
        cfg = _load_config()
        v = cfg.get("meet_info_message_id")
        return int(v) if v else None

    async def refresh_panel(self) -> None:
        ch_id  = MEET_INFO_CHANNEL_ID
        msg_id = self._get_meet_info_msg_id()
        if not ch_id or not msg_id:
            print("[MeetInfoPatch] No channel/message ID found in config — skipping.")
            return
        ch = self.bot.get_channel(ch_id)
        if not isinstance(ch, discord.TextChannel):
            try:
                ch = await self.bot.fetch_channel(ch_id)
            except Exception:
                print(f"[MeetInfoPatch] Could not fetch channel {ch_id}.")
                return
        try:
            msg = await ch.fetch_message(msg_id)
            await msg.edit(embed=_build_embed(), view=self.view)
            print("[MeetInfoPatch] Meet-info panel updated successfully.")
        except discord.NotFound:
            print("[MeetInfoPatch] Saved message not found — posting new one.")
            try:
                new_msg = await ch.send(embed=_build_embed(), view=self.view)
                cfg = _load_config()
                cfg["meet_info_message_id"] = new_msg.id
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, indent=4)
            except Exception as e:
                print(f"[MeetInfoPatch] Failed to post: {e}")
        except Exception as e:
            print(f"[MeetInfoPatch] Edit failed: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        import asyncio
        await asyncio.sleep(5)   # let bot.py on_ready finish first
        await self.refresh_panel()
        print("[MeetInfoPatch] Cog ready.")

    @commands.command(name="refresh_meetinfo")
    @commands.has_permissions(manage_guild=True)
    async def cmd_refresh(self, ctx: commands.Context):
        await self.refresh_panel()
        await ctx.send("Meet-info panel refreshed.", delete_after=8)


async def setup(bot: commands.Bot):
    await bot.add_cog(MeetInfoPatchCog(bot))
