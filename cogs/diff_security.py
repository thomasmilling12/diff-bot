from __future__ import annotations

import re
from collections import deque
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import discord
from discord.ext import commands, tasks

# =========================================================
# CONFIG
# =========================================================
GUILD_ID           = 850386896509337710
MOD_LOG_CHANNEL_ID = 1486598266211664003

STAFF_ROLE_IDS: set[int] = {
    850391095845584937,   # Leader
    850391378559238235,   # Co-Leader
    990011447193006101,   # Manager
}

# Channels where ONLY media/links are allowed (no plain text)
MEDIA_ONLY_CHANNEL_IDS: set[int] = {
    1266933655486332999,
    1047335715270316079,
}

# Domains that are allowed to be posted by regular members
ALLOWED_LINK_DOMAINS: set[str] = {
    "discord.com",
    "discord.gg",
    "youtube.com",
    "www.youtube.com",
    "youtu.be",
    "instagram.com",
    "www.instagram.com",
    "tiktok.com",
    "www.tiktok.com",
    "x.com",
    "twitter.com",
    "imgur.com",
    "tenor.com",
    "gfycat.com",
    "medal.tv",
    "rockstargames.com",
}

BLOCK_NON_WHITELISTED_LINKS = True

# Anti-raid
MIN_ACCOUNT_AGE_DAYS     = 3
RAID_JOIN_THRESHOLD      = 6      # burst join count
RAID_JOIN_WINDOW_SECS    = 20
RAID_TIMEOUT_MINS        = 30
RAID_ACTION              = "timeout"   # "timeout" or "kick"

DIFF_LOGO_URL = (
    "https://media.discordapp.net/attachments/1107375326625005719/"
    "1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm="
    "2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
    "&=&format=webp&quality=lossless&width=1376&height=917"
)

_URL_RE = re.compile(r"(https?://[^\s]+|www\.[^\s]+)", re.IGNORECASE)

MEDIA_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4", ".mov", ".avi", ".mkv", ".webm"}


# =========================================================
# HELPERS
# =========================================================
def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _is_staff(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    return any(r.id in STAFF_ROLE_IDS for r in member.roles)


def _extract_urls(content: str) -> list[str]:
    return _URL_RE.findall(content or "")


def _domain(url: str) -> str | None:
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    try:
        d = urlparse(url).netloc.lower().strip()
        return d or None
    except Exception:
        return None


def _domain_allowed(domain: str) -> bool:
    if not domain:
        return False
    if domain in ALLOWED_LINK_DOMAINS:
        return True
    for allowed in ALLOWED_LINK_DOMAINS:
        if domain.endswith("." + allowed):
            return True
    return False


def _has_media_attachment(attachments: list[discord.Attachment]) -> bool:
    for a in attachments:
        if a.content_type and a.content_type.startswith(("image/", "video/")):
            return True
        if any(a.filename.lower().endswith(ext) for ext in MEDIA_EXTS):
            return True
    return False


def _has_media_embed(embeds: list[discord.Embed]) -> bool:
    return any(e.image or e.thumbnail or e.video for e in embeds)


# =========================================================
# COG
# =========================================================
class SecurityCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot                  = bot
        self.recent_joins: deque[datetime] = deque()
        self._punished_ids: set[int] = set()
        self._cleanup.start()

    def cog_unload(self):
        self._cleanup.cancel()

    @tasks.loop(minutes=2)
    async def _cleanup(self):
        now = _utcnow()
        while self.recent_joins and (now - self.recent_joins[0]).total_seconds() > RAID_JOIN_WINDOW_SECS:
            self.recent_joins.popleft()

    @_cleanup.before_loop
    async def _before_cleanup(self):
        await self.bot.wait_until_ready()

    # ── Log helper ────────────────────────────────────────
    async def _log(self, embed: discord.Embed) -> None:
        ch = self.bot.get_channel(MOD_LOG_CHANNEL_ID)
        if isinstance(ch, discord.TextChannel):
            try:
                await ch.send(embed=embed)
            except Exception:
                pass

    # ── Raid punishment ───────────────────────────────────
    async def _punish_raider(self, member: discord.Member, reason: str, burst: bool = False) -> None:
        action_taken = "none"
        err_text     = ""

        if RAID_ACTION == "kick":
            try:
                await member.kick(reason=f"Anti-Raid: {reason}")
                action_taken = "Kicked"
            except Exception as e:
                err_text = str(e)
        else:
            try:
                await member.timeout(
                    _utcnow() + timedelta(minutes=RAID_TIMEOUT_MINS),
                    reason=f"Anti-Raid: {reason}",
                )
                action_taken = f"Timed out ({RAID_TIMEOUT_MINS} min)"
            except Exception as e:
                err_text = str(e)

        log = discord.Embed(
            title="🚨 Anti-Raid Triggered",
            color=discord.Color.dark_red(),
            timestamp=_utcnow(),
        )
        log.add_field(name="User",   value=f"{member.mention}\n`{member.id}`", inline=True)
        log.add_field(name="Action", value=action_taken,                        inline=True)
        log.add_field(name="Reason", value=reason,                              inline=False)
        if burst:
            log.add_field(
                name="Burst Detail",
                value=f"{len(self.recent_joins)} joins in {RAID_JOIN_WINDOW_SECS}s",
                inline=False,
            )
        if err_text:
            log.add_field(name="Error", value=err_text[:1000], inline=False)
        log.set_thumbnail(url=DIFF_LOGO_URL)
        log.set_footer(text="DIFF Meets • Anti-Raid")
        await self._log(log)

        try:
            dm = discord.Embed(
                title="🚨 Security Action Applied",
                description=(
                    f"You triggered anti-raid protection in **{member.guild.name}**.\n\n"
                    f"**Action:** {action_taken}\n"
                    f"**Reason:** {reason}"
                ),
                color=discord.Color.red(),
            )
            dm.set_thumbnail(url=DIFF_LOGO_URL)
            dm.set_footer(text="DIFF Meets • Security")
            await member.send(embed=dm)
        except Exception:
            pass

    # ── Events ────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id != GUILD_ID:
            return
        if member.id in self._punished_ids:
            return
        self._punished_ids.add(member.id)

        now = _utcnow()
        self.recent_joins.append(now)
        while self.recent_joins and (now - self.recent_joins[0]).total_seconds() > RAID_JOIN_WINDOW_SECS:
            self.recent_joins.popleft()

        age        = now - member.created_at
        new_acct   = age < timedelta(days=MIN_ACCOUNT_AGE_DAYS)
        raid_burst = len(self.recent_joins) >= RAID_JOIN_THRESHOLD

        if new_acct or raid_burst:
            parts = []
            if new_acct:
                parts.append(f"Account younger than {MIN_ACCOUNT_AGE_DAYS} day(s)")
            if raid_burst:
                parts.append("Rapid join burst detected")
            await self._punish_raider(member, " | ".join(parts), burst=raid_burst)

        self.bot.loop.call_later(30, lambda: self._punished_ids.discard(member.id))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        if message.guild.id != GUILD_ID:
            return
        if not isinstance(message.author, discord.Member):
            return
        if _is_staff(message.author):
            return

        content     = message.content or ""
        attachments = message.attachments
        embeds      = message.embeds
        channel_id  = message.channel.id

        # ── Media-only channel enforcement ────────────────
        if channel_id in MEDIA_ONLY_CHANNEL_IDS:
            has_media  = _has_media_attachment(attachments) or _has_media_embed(embeds)
            has_link   = bool(_extract_urls(content))

            if not has_media and not has_link:
                try:
                    await message.delete()
                except Exception:
                    pass

                notice = discord.Embed(
                    title="🖼️ Media-Only Channel",
                    description=(
                        f"{message.author.mention}, this channel only allows images, "
                        "videos, or approved media links."
                    ),
                    color=discord.Color.orange(),
                )
                notice.set_thumbnail(url=DIFF_LOGO_URL)
                notice.set_footer(text="DIFF Meets • Media Guard")
                try:
                    warn_msg = await message.channel.send(embed=notice)
                    await warn_msg.delete(delay=8)
                except Exception:
                    pass

                log = discord.Embed(
                    title="🗑️ Media-Only Enforcement",
                    color=discord.Color.orange(),
                    timestamp=_utcnow(),
                )
                log.add_field(name="User",    value=f"{message.author.mention}\n`{message.author.id}`", inline=True)
                log.add_field(name="Channel", value=message.channel.mention,                             inline=True)
                log.add_field(name="Reason",  value="Non-media message in media-only channel",           inline=False)
                log.set_thumbnail(url=DIFF_LOGO_URL)
                log.set_footer(text="DIFF Meets • Media Guard")
                await self._log(log)
                return

        # ── Link whitelist ─────────────────────────────────
        if BLOCK_NON_WHITELISTED_LINKS:
            urls    = _extract_urls(content)
            blocked = []
            for url in urls:
                d = _domain(url)
                if d and not _domain_allowed(d):
                    blocked.append(d)

            if blocked:
                try:
                    await message.delete()
                except Exception:
                    pass

                notice = discord.Embed(
                    title="🔗 Link Not Allowed",
                    description=(
                        f"{message.author.mention}, that link is not permitted here. "
                        "Only approved domains can be posted."
                    ),
                    color=discord.Color.red(),
                )
                notice.set_thumbnail(url=DIFF_LOGO_URL)
                notice.set_footer(text="DIFF Meets • Link Filter")
                try:
                    warn_msg = await message.channel.send(embed=notice)
                    await warn_msg.delete(delay=8)
                except Exception:
                    pass

                log = discord.Embed(
                    title="🚫 Non-Whitelisted Link Removed",
                    color=discord.Color.red(),
                    timestamp=_utcnow(),
                )
                log.add_field(name="User",            value=f"{message.author.mention}\n`{message.author.id}`",  inline=True)
                log.add_field(name="Channel",         value=message.channel.mention,                              inline=True)
                log.add_field(name="Blocked Domains", value=", ".join(sorted(set(blocked)))[:1024],               inline=False)
                log.set_thumbnail(url=DIFF_LOGO_URL)
                log.set_footer(text="DIFF Meets • Link Filter")
                await self._log(log)
                return

    @commands.Cog.listener()
    async def on_ready(self):
        print("[Security] Cog ready.")


# =========================================================
# SETUP
# =========================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(SecurityCog(bot))
