from __future__ import annotations

import sys
from datetime import datetime, timezone

import discord
from discord.ext import commands

HOST_POSTERS_CHANNEL_ID  = 1091157191895023626
MEET_INFO_CHANNEL_ID     = 1266933655486332999
EVERYONE_CHAT_CHANNEL_ID = 1047335231826436166
PS5_ROLE_ID              = 1485668852921798849

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


def _image_attachments(msg: discord.Message) -> list[discord.Attachment]:
    return [
        a for a in msg.attachments
        if a.content_type and a.content_type.startswith("image/")
    ]


def _try_parse_ts(date_str: str, time_str: str) -> int | None:
    try:
        return _main()._parse_meet_ts(date_str.strip(), time_str.strip())
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

    # ── A + B + D  Auto-detect posters posted manually in #hosts-posters ─────────

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild or message.channel.id != HOST_POSTERS_CHANNEL_ID:
            return
        # Skip bot commands so !postmeet doesn't double-fire
        if message.content.startswith("!"):
            return

        images = _image_attachments(message)
        if not images:
            return

        caption   = message.content.strip() or ""
        parts     = [p.strip() for p in caption.split("|", 1)]
        date_part = parts[0] if parts else caption
        time_part = parts[1] if len(parts) > 1 else caption
        ts        = _try_parse_ts(date_part, time_part) if caption else None
        host      = message.author if isinstance(message.author, discord.Member) else None

        # ── D: Auto-thread ────────────────────────────────────────────────────────
        thread_name = (caption[:80] or "Meet Poster").strip() or "Meet Poster"
        try:
            await message.create_thread(name=thread_name, auto_archive_duration=10080)
        except Exception as e:
            print(f"[HostPosters] Thread error: {e}")

        # ── A: Reply with embed ───────────────────────────────────────────────────
        try:
            embed = _build_embed(host=host, date=date_part, time=time_part, ts=ts)
            await message.reply(embed=embed, mention_author=False)
        except Exception as e:
            print(f"[HostPosters] Embed reply error: {e}")

        # ── B: Forward images + embed to meet-info ────────────────────────────────
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

    # ── C: !postmeet prefix command ───────────────────────────────────────────────

    @commands.command(name="postmeet")
    @commands.guild_only()
    async def postmeet(self, ctx: commands.Context, *, args: str = ""):
        """Post a meet announcement.
        Usage: !postmeet @host | date | time | class
        Optionally add | notes as a 5th field.
        Attach the Canva poster image to the message.
        """
        try:
            await self._do_postmeet(ctx, args)
        except Exception as e:
            print(f"[HostPosters] !postmeet unhandled error: {e}")
            try:
                await ctx.reply(f"❌ Error: {e}", mention_author=False)
            except Exception:
                pass

    async def _do_postmeet(self, ctx: commands.Context, args: str):
        # ── Parse pipe-separated fields ───────────────────────────────────────────
        fields = [f.strip() for f in args.split("|")]

        if len(fields) < 4:
            return await ctx.reply(USAGE, mention_author=False)

        # Field 0: host (use first @mention in message, fall back to plain text)
        host: discord.Member | None = None
        if ctx.message.mentions:
            host = ctx.message.mentions[0]
        else:
            try:
                host = await ctx.guild.fetch_member(int(fields[0].strip("<@!> ")))
            except Exception:
                host = None

        date       = fields[1]
        time_str   = fields[2]
        class_name = fields[3]

        # Field 4 (optional): notes or image URL
        notes    : str | None = None
        image_url: str | None = None
        if len(fields) >= 5:
            extra = fields[4].strip()
            if extra.startswith("http") and any(
                extra.lower().endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".webp", ".gif")
            ):
                image_url = extra
            elif extra:
                notes = extra

        # Attached image takes priority over URL
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
            return await ctx.reply("❌ Host posters channel not found.", mention_author=False)

        files = []
        for att in cmd_images[:4]:
            try:
                files.append(await att.to_file())
            except Exception:
                pass

        send_kwargs: dict = dict(
            content=f"📅 **{date}** | 🕒 **{time_str}**",
            embed=make_embed(),
        )
        if files:
            send_kwargs["files"] = files

        poster_msg = await poster_ch.send(**send_kwargs)

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

        # Confirm back to caller
        info_mention = info_ch.mention if isinstance(info_ch, discord.TextChannel) else "#meet-info"
        confirm = await ctx.reply(
            f"✅ Posted in {poster_ch.mention}, forwarded to {info_mention} and <#{EVERYONE_CHAT_CHANNEL_ID}>.",
            mention_author=False,
        )

        # Clean up — delete the original command message
        try:
            await ctx.message.delete()
        except Exception:
            pass
        # Auto-delete the confirm message after 15 s
        try:
            await confirm.delete(delay=15)
        except Exception:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(DiffHostPosters(bot))
