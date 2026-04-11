from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import discord
from discord.ext import commands

GUILD_ID = 850386896509337710
FEEDBACK_LOG_CHANNEL_ID = 1485265848099799163

DIFF_LOGO_URL = "https://media.discordapp.net/attachments/1107375326625005719/1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm=2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a&=&format=webp&quality=lossless&width=1376&height=917"
STAFF_PING_ROLE_ID = 0

DATA_DIR = "diff_data"
FEEDBACK_FILE = os.path.join(DATA_DIR, "meet_feedback.json")
HOST_RATINGS_FILE = os.path.join(DATA_DIR, "host_feedback_ratings.json")

COLOR_PRIMARY = 0x1F6FEB
COLOR_SUCCESS = 0x2ECC71
COLOR_WARNING = 0xF1C40F


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def load_json(path: str, default):
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=4)
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path: str, data) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


class FeedbackModal(discord.ui.Modal, title="DIFF Meet Feedback"):
    meet_name = discord.ui.TextInput(
        label="Meet Name",
        placeholder="Example: Tire Lettering Meet",
        max_length=100,
        required=True,
    )
    host_name = discord.ui.TextInput(
        label="Host Name / Host Discord",
        placeholder="Example: @HostName or Frostyy",
        max_length=100,
        required=True,
    )
    rating = discord.ui.TextInput(
        label="Overall Rating (1-5)",
        placeholder="Enter a number from 1 to 5",
        max_length=1,
        required=True,
    )
    feedback = discord.ui.TextInput(
        label="Your Feedback",
        placeholder="Tell us what went well, what could improve, and any suggestions.",
        style=discord.TextStyle.paragraph,
        max_length=1200,
        required=True,
    )

    def __init__(self, cog: "FeedbackSystem"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        try:
            numeric_rating = int(str(self.rating))
        except ValueError:
            await interaction.response.send_message(
                "Please enter a valid rating from 1 to 5.", ephemeral=True
            )
            return

        if not 1 <= numeric_rating <= 5:
            await interaction.response.send_message(
                "Rating must be between 1 and 5.", ephemeral=True
            )
            return

        entry = {
            "user_id": interaction.user.id,
            "username": str(interaction.user),
            "meet_name": str(self.meet_name),
            "host_name": str(self.host_name),
            "rating": numeric_rating,
            "feedback": str(self.feedback),
            "submitted_at": utcnow().isoformat(),
            "channel_id": interaction.channel_id,
        }

        await self.cog.store_feedback(entry)
        await self.cog.log_feedback(interaction.guild, entry)

        await interaction.response.send_message(
            "✅ Your feedback has been submitted. Thank you for helping DIFF improve.",
            ephemeral=True,
        )

        try:
            fb_em = discord.Embed(
                title="Feedback Received",
                description=(
                    f"Thanks for submitting feedback for **{entry['meet_name']}**.\n"
                    "Your response was recorded successfully."
                ),
                color=discord.Color.dark_blue(),
            )
            fb_em.set_author(name="Different Meets", icon_url=DIFF_LOGO_URL)
            fb_em.set_thumbnail(url=DIFF_LOGO_URL)
            await interaction.user.send(embed=fb_em)
        except discord.HTTPException:
            pass


class FeedbackView(discord.ui.View):
    """Persistent view — registered on every startup so the button always works."""
    def __init__(self, cog: "FeedbackSystem"):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Submit Feedback",
        style=discord.ButtonStyle.primary,
        emoji="📝",
        custom_id="diff_feedback_submit",
    )
    async def submit_feedback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FeedbackModal(self.cog))


class FeedbackSystem(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(FeedbackView(self))

    @commands.Cog.listener()
    async def on_ready(self):
        print("[FeedbackSystem] Cog ready.")

    def get_feedback_data(self) -> Dict[str, Any]:
        return load_json(FEEDBACK_FILE, {"entries": []})

    def save_feedback_data(self, data: Dict[str, Any]) -> None:
        save_json(FEEDBACK_FILE, data)

    def get_host_ratings(self) -> Dict[str, Any]:
        return load_json(HOST_RATINGS_FILE, {})

    def save_host_ratings(self, data: Dict[str, Any]) -> None:
        save_json(HOST_RATINGS_FILE, data)

    async def store_feedback(self, entry: Dict[str, Any]) -> None:
        feedback_data = self.get_feedback_data()
        feedback_data["entries"].append(entry)
        self.save_feedback_data(feedback_data)

        host_name = entry.get("host_name", "Unknown").strip()
        if host_name.lower() == "not provided":
            return

        ratings = self.get_host_ratings()
        if host_name not in ratings:
            ratings[host_name] = {
                "total_ratings": 0,
                "rating_sum": 0,
                "average_rating": 0,
                "feedback_count": 0,
                "last_updated": utcnow().isoformat(),
            }

        ratings[host_name]["total_ratings"] += 1
        ratings[host_name]["rating_sum"] += int(entry["rating"])
        ratings[host_name]["feedback_count"] += 1
        ratings[host_name]["average_rating"] = round(
            ratings[host_name]["rating_sum"] / ratings[host_name]["total_ratings"], 2
        )
        ratings[host_name]["last_updated"] = utcnow().isoformat()
        self.save_host_ratings(ratings)

    async def log_feedback(self, guild: Optional[discord.Guild], entry: Dict[str, Any]) -> None:
        if guild is None:
            return

        log_channel = guild.get_channel(FEEDBACK_LOG_CHANNEL_ID)
        if log_channel is None:
            return

        embed = discord.Embed(
            title="📝 New Meet Feedback Submitted",
            color=COLOR_PRIMARY,
            timestamp=utcnow(),
        )
        embed.add_field(name="Submitted By", value=f"<@{entry['user_id']}>", inline=True)
        embed.add_field(name="Meet Name", value=entry["meet_name"], inline=True)
        embed.add_field(name="Host", value=entry["host_name"], inline=True)
        embed.add_field(name="Rating", value=f"{entry['rating']}/5", inline=True)
        embed.add_field(
            name="Channel",
            value=f"<#{entry['channel_id']}>" if entry.get("channel_id") else "Unknown",
            inline=True,
        )
        embed.add_field(name="Feedback", value=entry["feedback"][:1024], inline=False)
        embed.set_footer(text="Different Meets • Feedback System")

        content = f"<@&{STAFF_PING_ROLE_ID}>" if STAFF_PING_ROLE_ID else None
        try:
            await log_channel.send(content=content, embed=embed)
        except discord.HTTPException:
            pass

    @commands.command(name="postfeedbackpanel")
    @commands.has_permissions(manage_guild=True)
    async def post_feedback_panel(self, ctx: commands.Context):
        """Re-post the meet feedback panel with a working Submit button."""
        embed = discord.Embed(
            title="📝 Leave Your Meet Feedback",
            description=(
                f"**DIFF** is requesting feedback from tonight's meet!\n\n"
                "Let us know how it went — your thoughts help us improve every event."
            ),
            color=COLOR_PRIMARY,
        )
        embed.add_field(name="\u00a0", value=(
            "☐ Rate the meet experience\n"
            "☐ Comment on the host's performance\n"
            "☐ Share suggestions for next time"
        ), inline=False)
        embed.add_field(
            name="📋 Staff Commands",
            value=(
                "`!postfeedbackpanel` — Post / refresh this panel\n"
                "`!feedbackleaderboard` — View top-rated hosts by feedback score\n"
                "`!hostfeedback @host` — View all feedback for a specific host\n"
                "`!feedbackstats` — Show server-wide feedback statistics"
            ),
            inline=False,
        )
        embed.set_footer(text="Different Meets • Meet Feedback • All responses are appreciated")
        await ctx.send(embed=embed, view=FeedbackView(self))
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="feedbackleaderboard")
    @commands.has_permissions(manage_guild=True)
    async def feedback_leaderboard(self, ctx: commands.Context):
        ratings = self.get_host_ratings()
        if not ratings:
            await ctx.send("No host feedback data yet.")
            return

        sorted_hosts = sorted(
            ratings.items(),
            key=lambda item: (item[1]["average_rating"], item[1]["total_ratings"]),
            reverse=True,
        )[:10]

        embed = discord.Embed(
            title="🏆 DIFF Host Feedback Leaderboard",
            description="Top hosts based on submitted meet feedback.",
            color=COLOR_SUCCESS,
        )
        lines = [
            f"**{i}. {host}** — {data['average_rating']}/5 ({data['total_ratings']} ratings)"
            for i, (host, data) in enumerate(sorted_hosts, 1)
        ]
        embed.add_field(name="Rankings", value="\n".join(lines), inline=False)
        embed.set_footer(text="Different Meets • Feedback Leaderboard")
        await ctx.send(embed=embed)

    @commands.command(name="hostfeedback")
    @commands.has_permissions(manage_guild=True)
    async def host_feedback(self, ctx: commands.Context, *, host_name: str):
        ratings = self.get_host_ratings()
        data = ratings.get(host_name)
        if not data:
            await ctx.send("No feedback found for that host.")
            return

        embed = discord.Embed(
            title=f"📊 Host Feedback: {host_name}", color=COLOR_WARNING
        )
        embed.add_field(name="Average Rating", value=f"{data['average_rating']}/5", inline=True)
        embed.add_field(name="Total Ratings", value=str(data["total_ratings"]), inline=True)
        embed.add_field(name="Feedback Count", value=str(data["feedback_count"]), inline=True)
        embed.set_footer(text="Different Meets • Host Feedback Stats")
        await ctx.send(embed=embed)

    @commands.command(name="feedbackstats")
    @commands.has_permissions(manage_guild=True)
    async def feedback_stats(self, ctx: commands.Context):
        entries = self.get_feedback_data().get("entries", [])
        if not entries:
            await ctx.send("No feedback data yet.")
            return

        avg = round(sum(int(e["rating"]) for e in entries) / len(entries), 2)
        embed = discord.Embed(title="📈 DIFF Feedback Stats", color=COLOR_PRIMARY)
        embed.add_field(name="Total Submissions", value=str(len(entries)), inline=True)
        embed.add_field(name="Average Score", value=f"{avg}/5", inline=True)
        embed.add_field(name="Latest Submission", value=entries[-1]["submitted_at"][:19], inline=True)
        embed.set_footer(text="Different Meets • Feedback Stats")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(FeedbackSystem(bot))
