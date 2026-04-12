import re
import discord
from discord.ext import commands
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

HOST_POSTERS = 1091157191895023626
COLOR        = 0xE91E63
LOGO         = "https://media.discordapp.net/attachments/1107375326625005719/1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm=2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a&=&format=webp&quality=lossless&width=1376&height=917"
EST          = ZoneInfo("America/New_York")

USAGE = (
    "**Usage:** `!postmeet @host | date | time | class`\n"
    "**Example:** `!postmeet @Frostyy | April 18, 2026 | 9:00pm EST | Open Class`\n"
    "**With notes:** `!postmeet @Frostyy | April 18, 2026 | 9:00pm EST | Open Class | No weapons`\n"
    "Attach your Canva poster image directly to the message."
)

# message_id -> list of display names who clicked Received
_seen_by: dict[int, list[str]] = {}


# ─── Timestamp helper ────────────────────────────────────────────────────────

def _parse_meet_ts(date_str: str, time_str: str) -> int | None:
    """Return Unix timestamp from 'Month D, YYYY' + 'H:MMam EST' or None."""
    # strip timezone label
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
    """Return a Discord Hammertime string, falling back to plain text."""
    ts = _parse_meet_ts(date_str, time_str)
    if ts:
        return f"<t:{ts}:F>  •  <t:{ts}:R>"
    return f"{date_str}  •  {time_str}"


# ─── Received button ─────────────────────────────────────────────────────────

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
            # remove old seen-by field if present
            kept = [f for f in emb.fields if f.name != "👁️ Seen By"]
            emb.clear_fields()
            for f in kept:
                emb.add_field(name=f.name, value=f.value, inline=f.inline)
            emb.add_field(name="👁️ Seen By", value=", ".join(seen), inline=False)
        else:
            emb = None

        # Update button label
        self.label = f"✅ Received ({len(seen)})"
        view = ReceivedView(count=len(seen))

        await interaction.response.edit_message(
            embed=emb,
            view=view,
        )


class ReceivedView(discord.ui.View):
    def __init__(self, count: int = 0):
        super().__init__(timeout=None)
        self.add_item(ReceivedButton(count=count))


# ─── Cog ─────────────────────────────────────────────────────────────────────

class PostMeetCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.add_view(ReceivedView())  # register persistent view on load

    # ── Auto-listener: image dropped directly in hosts-posters ───────────────
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
        embed.add_field(name="👤 Host",       value=f"{message.author.display_name}\n{message.author.mention}", inline=True)
        embed.add_field(name="📅 Date & Time", value=dt_value, inline=False)
        embed.set_footer(text="DIFF Meets • Host Poster")
        embed.set_thumbnail(url=LOGO)

        view = ReceivedView()

        try:
            await message.create_thread(name=(caption[:80] or "Meet Poster"), auto_archive_duration=10080)
        except Exception:
            pass
        try:
            await message.reply(embed=embed, view=view, mention_author=False)
        except Exception:
            pass

    # ── !postmeet command ────────────────────────────────────────────────────
    @commands.command(name="postmeet")
    @commands.guild_only()
    async def postmeet(self, ctx: commands.Context, *, args: str = ""):
        try:
            fields = [f.strip() for f in args.split("|")]
            if len(fields) < 4:
                return await ctx.reply(USAGE, mention_author=False)

            host       = ctx.message.mentions[0] if ctx.message.mentions else None
            date       = fields[1]
            time_str   = fields[2]
            class_name = fields[3]
            notes      = fields[4] if len(fields) >= 5 else None

            img_atts  = [a for a in ctx.message.attachments if a.content_type and a.content_type.startswith("image/")]
            image_url = img_atts[0].url if img_atts else None

            dt_value = _dt_field(date, time_str)

            embed = discord.Embed(title="🏁 DIFF Meet Announcement", color=COLOR, timestamp=datetime.now(timezone.utc))
            if host:
                embed.add_field(name="👤 Host", value=f"{host.display_name}\n{host.mention}", inline=True)
            embed.add_field(name="🏎️ Class",    value=class_name, inline=True)
            embed.add_field(name="📅 Date & Time", value=dt_value, inline=False)
            if notes:
                embed.add_field(name="📝 Notes", value=notes, inline=False)
            if image_url:
                embed.set_image(url=image_url)
            embed.set_footer(text="DIFF Meets • Host Poster")
            embed.set_thumbnail(url=LOGO)

            poster_ch = self.bot.get_channel(HOST_POSTERS)
            if not poster_ch:
                return await ctx.reply("Host posters channel not found.", mention_author=False)

            files = []
            for a in img_atts[:4]:
                try:
                    files.append(await a.to_file())
                except Exception:
                    pass

            view    = ReceivedView()
            send_kw = dict(embed=embed, view=view)
            if files:
                send_kw["files"] = files
            poster_msg = await poster_ch.send(**send_kw)

            try:
                await poster_msg.create_thread(name=f"{date} — {class_name}"[:80], auto_archive_duration=10080)
            except Exception:
                pass

            confirm = await ctx.reply(f"Done! Posted in <#{HOST_POSTERS}>.", mention_author=False)
            try:
                await ctx.message.delete()
            except Exception:
                pass
            try:
                await confirm.delete(delay=15)
            except Exception:
                pass

        except Exception as e:
            try:
                await ctx.reply(f"Error: {e}", mention_author=False)
            except Exception:
                pass


async def setup(bot: commands.Bot):
    await bot.add_cog(PostMeetCog(bot))
