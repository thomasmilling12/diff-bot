import re
import discord
from discord.ext import commands
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

HOST_POSTERS = 1091157191895023626
COLOR        = 0xE91E63
LOGO         = "https://media.discordapp.net/attachments/1107375326625005719/1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm=2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a&=&format=webp&quality=lossless&width=1376&height=917"
EST          = ZoneInfo("America/New_York")

# message_id -> list of display names who clicked Received
_seen_by: dict[int, list[str]] = {}


# ─── Timestamp helper ─────────────────────────────────────────────────────────

def _parse_meet_ts(date_str: str, time_str: str) -> int | None:
    """Return Unix timestamp from 'Month D, YYYY' + 'H:MMam EST', or None."""
    time_clean = re.sub(r"\s*(EST|EDT|ET|PST|PDT|UTC)\s*$", "", time_str.strip(), flags=re.IGNORECASE).strip()
    combined   = f"{date_str.strip()} {time_clean}"
    formats    = [
        "%B %d, %Y %I:%M%p",
        "%B %d, %Y %I:%M %p",
        "%B %d, %Y %I%p",
        "%B %d, %Y %I %p",
        "%B %d %Y %I:%M%p",
        "%B %d %Y %I:%M %p",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(combined, fmt).replace(tzinfo=EST)
            return int(dt.timestamp())
        except ValueError:
            continue
    return None


def _dt_field(date_str: str, time_str: str) -> str:
    """Return Discord Hammertime string, or fall back to plain text."""
    ts = _parse_meet_ts(date_str, time_str)
    if ts:
        return f"<t:{ts}:F>  •  <t:{ts}:R>"
    return f"{date_str}  •  {time_str}"


# ─── Received button ──────────────────────────────────────────────────────────

class ReceivedButton(discord.ui.Button):
    def __init__(self, count: int = 0):
        label = "✅ Mark Received" if count == 0 else f"✅ Received ({count})"
        super().__init__(
            style=discord.ButtonStyle.success,
            label=label,
            custom_id="diff_postmeet_received",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        msg_id = interaction.message.id
        name   = interaction.user.display_name

        seen = _seen_by.setdefault(msg_id, [])
        if name not in seen:
            seen.append(name)

        # Rebuild embed with updated Seen By field
        old_embeds = interaction.message.embeds
        if old_embeds:
            emb = discord.Embed.from_dict(old_embeds[0].to_dict())
            kept = [f for f in emb.fields if f.name != "👁️ Seen By"]
            emb.clear_fields()
            for f in kept:
                emb.add_field(name=f.name, value=f.value, inline=f.inline)
            emb.add_field(name="👁️ Seen By", value=", ".join(seen), inline=False)
        else:
            emb = None

        await interaction.response.edit_message(
            embed=emb,
            view=ReceivedView(count=len(seen)),
        )


class ReceivedView(discord.ui.View):
    def __init__(self, count: int = 0):
        super().__init__(timeout=None)
        self.add_item(ReceivedButton(count=count))


# ─── Cog ──────────────────────────────────────────────────────────────────────

class PostMeetCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.add_view(ReceivedView())  # register persistent view on load

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild or message.channel.id != HOST_POSTERS:
            return
        if message.content.startswith("!"):
            return

        images = [a for a in message.attachments if a.content_type and a.content_type.startswith("image/")]
        if not images:
            return

        caption = message.content.strip()
        parts   = [p.strip() for p in caption.split("|")] if caption else []
        date_part = parts[0] if parts else ""
        time_part = parts[1] if len(parts) > 1 else ""

        if date_part and time_part:
            dt_value = _dt_field(date_part, time_part)
        elif caption:
            dt_value = caption
        else:
            dt_value = "See poster"

        embed = discord.Embed(title="🏁 DIFF Meet Announcement", color=COLOR, timestamp=datetime.now(timezone.utc))
        embed.add_field(name="👤 Host",        value=f"{message.author.display_name}\n{message.author.mention}", inline=True)
        embed.add_field(name="📅 Date & Time", value=dt_value, inline=False)
        embed.set_footer(text="DIFF Meets • Host Poster")
        embed.set_thumbnail(url=LOGO)

        try:
            await message.create_thread(name=(caption[:80] or "Meet Poster"), auto_archive_duration=10080)
        except Exception:
            pass
        try:
            await message.reply(embed=embed, view=ReceivedView(), mention_author=False)
        except Exception:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(PostMeetCog(bot))
