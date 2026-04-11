from __future__ import annotations

import sys
from datetime import datetime, timezone

import discord
from discord.ext import commands

HOST_POSTERS_CHANNEL_ID  = 1091157191895023626
MEET_INFO_CHANNEL_ID     = 1266933655486332999
EVERYONE_CHAT_CHANNEL_ID = 1047335231826436166
PS5_ROLE_ID              = 1485668852921798849

STAFF_ROLE_IDS: set[int] = {
    850391095845584937,   # Leader
    850391378559238235,   # Co-Leader
    990011447193006101,   # Manager
    1055823929358430248,  # Meet Host
}

DIFF_LOGO_URL = (
    "https://media.discordapp.net/attachments/1107375326625005719/"
    "1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm="
    "2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
    "&=&format=webp&quality=lossless&width=1376&height=917"
)

EMBED_COLOR = 0xE91E63

USAGE = (
    "**Usage:** `!postmeet @host | date | time | class`\n"
    "**Example:** `!postmeet @Frostyy | April 18, 2026 | 9:00pm EST | Open Class`\n"
    "**With notes:** `!postmeet @Frostyy | April 18, 2026 | 9:00pm EST | Open Class | No weapons`\n"
    "Attach your Canva poster image directly to the message, or paste an image URL as the last field."
)


def _main():
    return sys.modules["__main__"]


def _is_staff(member: discord.Member) -> bool:
    return any(r.id in STAFF_ROLE_IDS for r in member.roles)


def _image_attachments(msg: discord.Message) -> list[discord.Attachment]:
    return [
        a for a in msg.attachments
        if a.content_type and a.content_type.startswith("image/")
    ]


def _try_parse_ts(date_str: str, time_str: str) -> int | None:
    try:
        return _main()._parse_meet_ts(date_str, time_str)
    except Exception:
        return None


def _build_embed(
    host: discord.Member | None,
    date: str,
    time: str,
    ts: int | None,
    class_name: str | None = None,
    notes: str | None = None,
    image_url: str | None = None,
    footer_extra: str = "",
) -> discord.Embed:
    embed = discord.Embed(
        title="🏁 DIFF Meet Announcement",
        color=EMBED_COLOR,
        timestamp=datetime.now(timezone.utc),
    )
    if host:
        embed.add_field(name="👤 Host", value=host.mention, inline=True)
    if class_name:
        embed.add_field(name="🎮 Class", value=class_name, inline=True)
    if ts:
        embed.add_field(
            name="⏰ Date & Time",
            value=f"<t:{ts}:F>\n🕐 <t:{ts}:R>",
            inline=False,
        )
    else:
        embed.add_field(name="📅 Date & Time", value=f"{date}  •  {time}", inline=False)
    if notes:
        embed.add_field(name="📝 Notes", value=notes, inline=False)
    if image_url:
        embed.set_image(url=image_url)
    footer = "DIFF Meets • Host Poster"
    if footer_extra:
        footer += f"  •  {footer_extra}"
    embed.set_footer(text=footer)
    embed.set_thumbnail(url=DIFF_LOGO_URL)
    return embed


class DiffHostPosters(commands.Cog, name="DiffHostPosters"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── A + B + D  Auto-detect posters posted manually in #hosts-posters ────────

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild or message.channel.id != HOST_POSTERS_CHANNEL_ID:
            return

        images = _image_attachments(message)
        if not images:
            return

        caption = message.content.strip() or ""
        # Caption format: "April 10th, 2026 | 9:00pm EST" → split on first |
        parts     = [p.strip() for p in caption.split("|", 1)]
        date_part = parts[0] if parts else caption
        time_part = parts[1] if len(parts) > 1 else caption
        ts        = _try_parse_ts(date_part, time_part) if caption else None
        host      = message.author if isinstance(message.author, discord.Member) else None

        # ── D: Auto-thread ───────────────────────────────────────────────────────
        thread_name = (caption[:80] or "Meet Poster").strip() or "Meet Poster"
        try:
            await message.create_thread(name=thread_name, auto_archive_duration=10080)
        except Exception as e:
            print(f"[HostPosters] Thread error: {e}")

        # ── A: Reply with formatted embed ────────────────────────────────────────
        try:
            embed = _build_embed(host=host, date=date_part, time=time_part, ts=ts)
            await message.reply(embed=embed, mention_author=False)
        except Exception as e:
            print(f"[HostPosters] Embed reply error: {e}")

        # ── B: Forward images + embed to meet-info ───────────────────────────────
        try:
            info_ch = self.bot.get_channel(MEET_INFO_CHANNEL_ID)
            if isinstance(info_ch, discord.TextChannel):
                files = []
                for att in images[:4]:
                    try:
                        files.append(await att.to_file())
                    except Exception:
                        pass
                fwd_embed = _build_embed(
                    host=host,
                    date=date_part,
                    time=time_part,
                    ts=ts,
                    footer_extra=f"from #{message.channel.name}",
                )
                await info_ch.send(
                    content=f"📢 New meet poster from {host.mention if host else 'a host'}:",
                    files=files,
                    embed=fwd_embed,
                    allowed_mentions=discord.AllowedMentions.none(),
                )
        except Exception as e:
            print(f"[HostPosters] Forward error: {e}")

    # ── C: !postmeet prefix command ──────────────────────────────────────────────

    @commands.command(name="postmeet")
    @commands.guild_only()
    async def postmeet(self, ctx: commands.Context, *, args: str = ""):
        """Post a full meet announcement.
        Usage: !postmeet @host | date | time | class | [notes or image url]
        Attach the Canva poster to the message, or include an image URL as the last field.
        """
        if not isinstance(ctx.author, discord.Member) or not _is_staff(ctx.author):
            return await ctx.reply("Staff only.", mention_author=False, delete_after=10)

        # ── Parse pipe-separated args ─────────────────────────────────────────────
        fields = [f.strip() for f in args.split("|")]

        if len(fields) < 4:
            return await ctx.reply(USAGE, mention_author=False)

        # Field 0: host mention or ID
        host: discord.Member | None = None
        host_raw = fields[0].strip()
        if ctx.message.mentions:
            host = ctx.message.mentions[0]
        else:
            try:
                host = await ctx.guild.fetch_member(int(host_raw.strip("<@!> ")))
            except Exception:
                host = None

        date       = fields[1]
        time_str   = fields[2]
        class_name = fields[3]

        # Field 4 (optional): notes or image URL
        notes     : str | None = None
        image_url : str | None = None
        if len(fields) >= 5:
            extra = fields[4]
            if extra.startswith("http") and any(
                extra.lower().endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".webp", ".gif")
            ):
                image_url = extra
            else:
                notes = extra or None

        # Image attached to the command message takes priority
        cmd_images = _image_attachments(ctx.message)
        if cmd_images:
            image_url = cmd_images[0].url

        ts = _try_parse_ts(date, time_str)

        def make_embed(footer_extra: str = "") -> discord.Embed:
            return _build_embed(
                host=host,
                date=date,
                time=time_str,
                ts=ts,
                class_name=class_name,
                notes=notes,
                image_url=image_url,
                footer_extra=footer_extra,
            )

        # ── Post to #hosts-posters ────────────────────────────────────────────────
        poster_ch = self.bot.get_channel(HOST_POSTERS_CHANNEL_ID)
        if not isinstance(poster_ch, discord.TextChannel):
            return await ctx.reply("Host posters channel not found.", mention_author=False)

        # Re-upload attached images so they appear in the poster channel
        files = []
        for att in cmd_images[:4]:
            try:
                files.append(await att.to_file())
            except Exception:
                pass

        poster_msg = await poster_ch.send(
            content=f"📅 **{date}** | 🕒 **{time_str}**",
            embed=make_embed(),
            files=files or discord.utils.MISSING,
        )

        # ── D: Thread ─────────────────────────────────────────────────────────────
        try:
            thread_name = f"{date} — {class_name}"[:80]
            await poster_msg.create_thread(name=thread_name, auto_archive_duration=10080)
        except Exception as e:
            print(f"[HostPosters] !postmeet thread error: {e}")

        # ── B: Forward to meet-info ───────────────────────────────────────────────
        info_ch = self.bot.get_channel(MEET_INFO_CHANNEL_ID)
        if isinstance(info_ch, discord.TextChannel):
            try:
                await info_ch.send(embed=make_embed(footer_extra="via !postmeet"))
            except Exception as e:
                print(f"[HostPosters] !postmeet meet-info error: {e}")

        # ── Ping @PS5 Member in everyone chat ─────────────────────────────────────
        everyone_ch = self.bot.get_channel(EVERYONE_CHAT_CHANNEL_ID)
        if isinstance(everyone_ch, discord.TextChannel):
            try:
                await everyone_ch.send(
                    content=f"<@&{PS5_ROLE_ID}>",
                    embed=make_embed(),
                    allowed_mentions=discord.AllowedMentions(roles=True),
                )
            except Exception as e:
                print(f"[HostPosters] !postmeet everyone chat error: {e}")

        info_mention = info_ch.mention if isinstance(info_ch, discord.TextChannel) else "#meet-info"
        await ctx.reply(
            f"✅ Posted in {poster_ch.mention}, forwarded to {info_mention} and <#{EVERYONE_CHAT_CHANNEL_ID}>.",
            mention_author=False,
        )

        # Delete the command message to keep the channel clean
        try:
            await ctx.message.delete()
        except Exception:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(DiffHostPosters(bot))
