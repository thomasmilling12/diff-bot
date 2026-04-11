"""
diff_photo_reminder.py
─────────────────────
Watches join-ticket channels and sends a 15-minute reminder when a player
has submitted some photos but hasn't hit the required count yet.

Logic per channel:
  • A photo lands → reset the 15-minute countdown (cancel old, start new).
  • If the countdown fires and the count is still < MIN_PHOTOS → send reminder.
  • If the count reaches MIN_PHOTOS at any point → cancel the countdown silently.
  • Also resets the main idle-close timer on every photo, so the 30-min window
    starts fresh from the last activity (not from ticket creation).
"""

from __future__ import annotations

import asyncio
import sys
from typing import Optional

import discord
from discord.ext import commands

print("[PhotoReminder] Module loading...")

MIN_PHOTOS          = 10
REMINDER_DELAY_SECS = 15 * 60   # 15 minutes
JOIN_TICKET_CATEGORY_ID = 1328457973583839282


# ── helpers ────────────────────────────────────────────────────────────────────

def _main():
    """Return the live __main__ (bot.py) module."""
    return sys.modules["__main__"]


def _get_join_user_id(channel: discord.TextChannel) -> Optional[str]:
    """Return the applicant's user-ID string from the channel topic, or None."""
    topic = getattr(channel, "topic", None)
    if not topic or "JOIN_USER:" not in topic:
        return None
    try:
        return topic.split("JOIN_USER:")[1].split()[0].strip()
    except IndexError:
        return None


async def _count_user_photos(channel: discord.TextChannel, user_id: int) -> int:
    """Count unique images sent by *user_id* in *channel* (last 200 messages)."""
    total = 0
    try:
        async for msg in channel.history(limit=200):
            if msg.author.id == user_id:
                total += sum(
                    1 for a in msg.attachments
                    if a.content_type and a.content_type.startswith("image/")
                )
    except Exception:
        pass
    return total


def _is_join_channel(channel: discord.abc.GuildChannel) -> bool:
    """True if *channel* lives inside the join-ticket category."""
    return (
        isinstance(channel, discord.TextChannel)
        and getattr(channel.category, "id", None) == JOIN_TICKET_CATEGORY_ID
    )


def _reset_idle_timer(channel: discord.TextChannel, member: discord.Member) -> None:
    """Cancel the bot's existing idle-close task for this channel and start fresh."""
    try:
        m = _main()
        tasks: dict = m._join_ticket_tasks
        old = tasks.pop(channel.id, None)
        if old and not old.done():
            old.cancel()
        new_task = asyncio.create_task(m._join_idle_timer(channel, member))
        tasks[channel.id] = new_task
    except Exception as e:
        print(f"[PhotoReminder] Could not reset idle timer for {channel.id}: {e}")


# ── reminder coroutine ─────────────────────────────────────────────────────────

async def _photo_reminder_task(
    channel: discord.TextChannel,
    member: discord.Member,
    photo_count_at_start: int,
) -> None:
    """
    Sleeps 15 minutes, then checks if the player has still not hit MIN_PHOTOS.
    If so, sends a friendly reminder ping.
    """
    await asyncio.sleep(REMINDER_DELAY_SECS)

    # Re-count photos to get an up-to-date number
    current = await _count_user_photos(channel, member.id)
    if current >= MIN_PHOTOS:
        return  # They finished — no reminder needed

    remaining = MIN_PHOTOS - current

    embed = discord.Embed(
        title="📸 Don't Forget Your Photos!",
        description="\n".join([
            f"{member.mention}, you still need to submit **{remaining} more photo{'s' if remaining != 1 else ''}** "
            f"to complete your application.",
            "",
            f"You've submitted **{current}/{MIN_PHOTOS}** so far — you're almost there!",
            "",
            "⏳ **Your ticket will close automatically if no photos are sent.** "
            "Upload the rest now to avoid losing your spot.",
        ]),
        color=discord.Color.orange(),
    )
    embed.add_field(
        name="📊 Progress",
        value="🟦" * current + "⬛" * remaining,
        inline=False,
    )
    embed.add_field(name="✅ Submitted",   value=str(current),   inline=True)
    embed.add_field(name="📌 Still Needed", value=str(remaining), inline=True)
    embed.set_footer(text="Different Meets • Photo Reminder")
    embed.set_thumbnail(url=member.display_avatar.url)

    try:
        await channel.send(
            content=member.mention,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(users=True),
        )
        print(
            f"[PhotoReminder] Sent reminder to {member} in #{channel.name} "
            f"({current}/{MIN_PHOTOS} photos)."
        )
    except Exception as e:
        print(f"[PhotoReminder] Could not send reminder in {channel.id}: {e}")


# ── cog ────────────────────────────────────────────────────────────────────────

class PhotoReminderCog(commands.Cog, name="PhotoReminder"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # channel_id → asyncio.Task
        self._timers: dict[int, asyncio.Task] = {}
        print("[PhotoReminder] Cog ready.")

    def cog_unload(self) -> None:
        for task in self._timers.values():
            task.cancel()
        self._timers.clear()

    def _cancel_timer(self, channel_id: int) -> None:
        old = self._timers.pop(channel_id, None)
        if old and not old.done():
            old.cancel()

    def _reset_timer(
        self,
        channel: discord.TextChannel,
        member: discord.Member,
        count: int,
    ) -> None:
        self._cancel_timer(channel.id)
        task = asyncio.create_task(
            _photo_reminder_task(channel, member, count)
        )
        self._timers[channel.id] = task

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # Only care about guild text messages with image attachments
        if (
            message.author.bot
            or not message.guild
            or not isinstance(message.channel, discord.TextChannel)
            or not _is_join_channel(message.channel)
        ):
            return

        raw_images = [
            a for a in message.attachments
            if a.content_type and a.content_type.startswith("image/")
        ]
        if not raw_images:
            return

        # Must be the applicant's own channel
        uid_str = _get_join_user_id(message.channel)
        if not uid_str or str(message.author.id) != uid_str:
            return

        # Count their total photos so far (post-send count from history)
        # Give the message a moment to settle in history
        await asyncio.sleep(0.5)
        count = await _count_user_photos(message.channel, message.author.id)

        if count >= MIN_PHOTOS:
            # They've finished — make sure any reminder is cancelled
            self._cancel_timer(message.channel.id)
            return

        # Photos submitted but not complete → reset reminder + idle-close timers
        member = message.author
        if not isinstance(member, discord.Member):
            return

        self._reset_timer(message.channel, member, count)
        _reset_idle_timer(message.channel, member)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        """Clean up timer when a ticket is deleted."""
        self._cancel_timer(channel.id)


print("[PhotoReminder] Module loaded OK.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PhotoReminderCog(bot))
