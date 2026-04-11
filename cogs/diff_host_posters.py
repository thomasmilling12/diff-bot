from __future__ import annotations

import sys
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

HOST_POSTERS_CHANNEL_ID  = 1091157191895023626
MEET_INFO_CHANNEL_ID     = 1266933655486332999
EVERYONE_CHAT_CHANNEL_ID = 1047335231826436166
PS5_ROLE_ID              = 1485668852921798849
GUILD_ID                 = 850386896509337710

DIFF_LOGO_URL = (
    "https://media.discordapp.net/attachments/1107375326625005719/"
    "1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm="
    "2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
    "&=&format=webp&quality=lossless&width=1376&height=917"
)

EMBED_COLOR = 0xE91E63


def _main():
    return sys.modules["__main__"]


def _image_attachments(msg: discord.Message) -> list[discord.Attachment]:
    return [
        a for a in msg.attachments
        if a.content_type and a.content_type.startswith("image/")
    ]


def _try_parse_ts(caption: str) -> int | None:
    """Split 'April 10th, 2026 | 9:00pm EST' on '|' then call _parse_meet_ts."""
    try:
        m = _main()
        parts = caption.split("|", 1)
        date_part = parts[0].strip() if parts else caption
        time_part = parts[1].strip() if len(parts) > 1 else caption
        return m._parse_meet_ts(date_part, time_part)
    except Exception:
        return None


def _build_embed(
    host: discord.Member | None,
    caption: str,
    ts: int | None,
    class_name: str | None = None,
    notes: str | None = None,
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
    elif caption:
        embed.add_field(name="📅 Date & Time", value=caption, inline=False)
    if notes:
        embed.add_field(name="📝 Notes", value=notes, inline=False)
    footer = "DIFF Meets • Host Poster"
    if footer_extra:
        footer += f"  •  {footer_extra}"
    embed.set_footer(text=footer)
    embed.set_thumbnail(url=DIFF_LOGO_URL)
    return embed


class DiffHostPosters(commands.Cog, name="DiffHostPosters"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── A + B + D  Auto-detect posters posted manually ─────────────────────────

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
        ts = _try_parse_ts(caption) if caption else None

        host = message.author if isinstance(message.author, discord.Member) else None

        # ── D: Create thread ────────────────────────────────────────────────────
        thread_name = (caption[:80] or "Meet Poster").strip()
        try:
            await message.create_thread(
                name=thread_name,
                auto_archive_duration=10080,
            )
        except Exception as e:
            print(f"[HostPosters] Thread error: {e}")

        # ── A: Reply with formatted embed ───────────────────────────────────────
        try:
            embed = _build_embed(host=host, caption=caption, ts=ts)
            await message.reply(embed=embed, mention_author=False)
        except Exception as e:
            print(f"[HostPosters] Embed reply error: {e}")

        # ── B: Forward images + embed to meet-info ──────────────────────────────
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
                    caption=caption,
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

    # ── C: /postmeet slash command ──────────────────────────────────────────────

    @app_commands.command(
        name="postmeet",
        description="Post a full meet announcement with poster, Discord timestamp, and cross-channel forwarding",
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(
        host="The host for this meet",
        date="Date of the meet — e.g. April 18, 2026",
        time="Time of the meet — e.g. 9:00pm EST",
        class_type="Meet class — e.g. Open Class, American Muscle",
        image_url="Direct link to the Canva poster image (right-click → Copy Image Link)",
        notes="Optional notes shown in the embed",
        ping_everyone="Ping @PS5 Member in everyone chat (default: yes)",
    )
    async def postmeet(
        self,
        interaction: discord.Interaction,
        host: discord.Member,
        date: str,
        time: str,
        class_type: str,
        image_url: str | None = None,
        notes: str | None = None,
        ping_everyone: bool = True,
    ):
        await interaction.response.defer(ephemeral=True)

        caption = f"{date} | {time}"
        ts = _try_parse_ts(caption)

        # ── Build the base embed ────────────────────────────────────────────────
        def make_embed(footer_extra: str = "") -> discord.Embed:
            e = _build_embed(
                host=host,
                caption=caption,
                ts=ts,
                class_name=class_type,
                notes=notes,
                footer_extra=footer_extra,
            )
            if image_url:
                e.set_image(url=image_url)
            return e

        # ── Post to host-posters channel ────────────────────────────────────────
        poster_ch = self.bot.get_channel(HOST_POSTERS_CHANNEL_ID)
        if not isinstance(poster_ch, discord.TextChannel):
            return await interaction.followup.send(
                "❌ Host posters channel not found.", ephemeral=True
            )

        poster_msg = await poster_ch.send(
            content=f"📅 **{date}** | 🕒 **{time}**",
            embed=make_embed(),
        )

        # ── D: Create thread ────────────────────────────────────────────────────
        try:
            thread_name = f"{date} — {class_type}"[:80]
            await poster_msg.create_thread(
                name=thread_name,
                auto_archive_duration=10080,
            )
        except Exception as e:
            print(f"[HostPosters] /postmeet thread error: {e}")

        # ── B: Forward to meet-info ─────────────────────────────────────────────
        info_ch = self.bot.get_channel(MEET_INFO_CHANNEL_ID)
        if isinstance(info_ch, discord.TextChannel):
            try:
                await info_ch.send(embed=make_embed(footer_extra="via /postmeet"))
            except Exception as e:
                print(f"[HostPosters] /postmeet meet-info error: {e}")

        # ── Ping everyone chat ──────────────────────────────────────────────────
        if ping_everyone:
            everyone_ch = self.bot.get_channel(EVERYONE_CHAT_CHANNEL_ID)
            if isinstance(everyone_ch, discord.TextChannel):
                try:
                    await everyone_ch.send(
                        content=f"<@&{PS5_ROLE_ID}>",
                        embed=make_embed(),
                        allowed_mentions=discord.AllowedMentions(roles=True),
                    )
                except Exception as e:
                    print(f"[HostPosters] /postmeet everyone chat error: {e}")

        info_mention = info_ch.mention if isinstance(info_ch, discord.TextChannel) else "#meet-info"
        await interaction.followup.send(
            f"✅ Meet posted in {poster_ch.mention}, forwarded to {info_mention}"
            + (f" and <#{EVERYONE_CHAT_CHANNEL_ID}>" if ping_everyone else "")
            + ".",
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(DiffHostPosters(bot))
