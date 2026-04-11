from __future__ import annotations

import json
import os
import re
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Optional

import discord
from discord.ext import commands, tasks

# In-memory dedup caches — prevents duplicate log entries caused by Discord
# replaying gateway events after the bot reconnects following a Pi freeze.
_DEDUP_TTL = 30  # seconds
_join_dedup:  dict[int, float] = {}
_leave_dedup: dict[int, float] = {}

# =========================================================
# CONFIG
# =========================================================
GUILD_ID = 850386896509337710

MOD_LOG_CHANNEL_ID       = 1486598266211664003
JOIN_LEAVE_LOG_CHANNEL_ID = 1485265848099799163   # Staff Logs

# Role given to every new member on join (Unverified)
AUTO_ROLE_ID = 1486011550916411512

STAFF_ROLE_IDS: set[int] = {
    850391095845584937,   # Leader
    850391378559238235,   # Co-Leader
    990011447193006101,   # Manager
}

# ── Anti-spam settings ────────────────────────────────────
SPAM_MSG_COUNT      = 5
SPAM_WINDOW_SECS    = 12
SPAM_TIMEOUT_MINS   = 10

DUP_MSG_COUNT       = 4
DUP_WINDOW_SECS     = 20

MASS_MENTION_LIMIT  = 5

BLOCK_INVITES   = True
BLOCK_BAD_WORDS = True

# Bad words are stored in diff_data/diff_word_filter.json
# and managed via !filter add / !filter remove in diff_community_features.
# Do NOT hard-code words here — use those commands instead.
BAD_WORDS: set[str] = set()

# ── Storage ───────────────────────────────────────────────
DATA_DIR         = "diff_data"
ROLE_BACKUP_FILE = os.path.join(DATA_DIR, "automod_role_backup.json")
WORD_FILTER_FILE = os.path.join(DATA_DIR, "diff_word_filter.json")

DIFF_LOGO_URL = (
    "https://media.discordapp.net/attachments/1107375326625005719/"
    "1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm="
    "2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
    "&=&format=webp&quality=lossless&width=1376&height=917"
)


# =========================================================
# HELPERS
# =========================================================
def _load_json(path: str, default=None):
    if default is None:
        default = {}
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _is_staff(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    return any(r.id in STAFF_ROLE_IDS for r in member.roles)


def _reload_bad_words() -> None:
    """Read diff_word_filter.json and refresh the in-memory BAD_WORDS set."""
    global BAD_WORDS
    try:
        if os.path.exists(WORD_FILTER_FILE):
            with open(WORD_FILTER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            BAD_WORDS = {w.lower().strip() for w in data.get("words", []) if w.strip()}
        else:
            BAD_WORDS = set()
    except Exception:
        pass


def _normalize(content: str) -> str:
    return re.sub(r"\s+", " ", content.lower().strip())


def _check_bad_word(content: str) -> Optional[str]:
    if not BAD_WORDS:
        return None
    cleaned = re.sub(r"[^a-z0-9\s]", " ", content.lower())
    for word in cleaned.split():
        if word in BAD_WORDS:
            return word
    return None


def _has_invite(content: str) -> bool:
    patterns = [
        r"(https?://)?discord\.gg/[A-Za-z0-9]+",
        r"(https?://)?discord\.com/invite/[A-Za-z0-9]+",
    ]
    return any(re.search(p, content, re.IGNORECASE) for p in patterns)


# =========================================================
# COG
# =========================================================
class AutoModCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # { user_id → deque of datetimes }
        self._msg_times:  dict[int, deque] = defaultdict(deque)
        # { user_id → deque of (normalized_text, datetime) }
        self._msg_texts:  dict[int, deque] = defaultdict(deque)
        _reload_bad_words()
        self._cache_cleanup.start()
        self._filter_reload.start()

    def cog_unload(self):
        self._cache_cleanup.cancel()
        self._filter_reload.cancel()

    # ── Background cleanup ────────────────────────────────
    @tasks.loop(minutes=5)
    async def _cache_cleanup(self):
        cutoff = _utcnow() - timedelta(minutes=10)

        for uid in list(self._msg_times):
            dq = self._msg_times[uid]
            while dq and dq[0] < cutoff:
                dq.popleft()
            if not dq:
                del self._msg_times[uid]

        for uid in list(self._msg_texts):
            dq = self._msg_texts[uid]
            while dq and dq[0][1] < cutoff:
                dq.popleft()
            if not dq:
                del self._msg_texts[uid]

    @_cache_cleanup.before_loop
    async def _before_cleanup(self):
        await self.bot.wait_until_ready()

    # ── Word-filter hot-reload (every 5 min) ──────────────
    @tasks.loop(minutes=5)
    async def _filter_reload(self):
        _reload_bad_words()

    @_filter_reload.before_loop
    async def _before_filter_reload(self):
        await self.bot.wait_until_ready()

    # ── Internal helpers ──────────────────────────────────
    async def _send_log(self, embed: discord.Embed, channel_id: int = MOD_LOG_CHANNEL_ID):
        ch = self.bot.get_channel(channel_id)
        if isinstance(ch, discord.TextChannel):
            try:
                await ch.send(embed=embed)
            except Exception:
                pass

    async def _automod_action(self, message: discord.Message, reason: str, extra: str = ""):
        member = message.author
        if not isinstance(member, discord.Member):
            return

        try:
            await message.delete()
        except Exception:
            pass

        until = _utcnow() + timedelta(minutes=SPAM_TIMEOUT_MINS)
        timed_out = False
        timeout_err = ""

        try:
            await member.timeout(until, reason=f"AutoMod: {reason}")
            timed_out = True
        except Exception as e:
            timeout_err = str(e)

        action_text = (
            f"Timed out for {SPAM_TIMEOUT_MINS} minute(s)"
            if timed_out
            else "Message removed (timeout failed)"
        )

        log_embed = discord.Embed(
            title="🛡️ AutoMod Triggered",
            color=discord.Color.red(),
            timestamp=_utcnow(),
        )
        log_embed.add_field(name="User",    value=f"{member.mention}\n`{member.id}`", inline=True)
        log_embed.add_field(name="Channel", value=message.channel.mention,            inline=True)
        log_embed.add_field(name="Reason",  value=reason,                             inline=False)
        if extra:
            log_embed.add_field(name="Detail", value=extra, inline=False)
        log_embed.add_field(name="Action",  value=action_text, inline=False)
        if timeout_err:
            log_embed.add_field(name="Timeout Error", value=timeout_err[:1000], inline=False)
        log_embed.set_thumbnail(url=DIFF_LOGO_URL)
        log_embed.set_footer(text="DIFF Meets • AutoMod")
        await self._send_log(log_embed)

        try:
            dm = discord.Embed(
                title="🛡️ AutoMod Notice",
                description=(
                    f"Your message in **{member.guild.name}** was removed by AutoMod.\n\n"
                    f"**Reason:** {reason}\n"
                    f"{f'**Detail:** {extra}' + chr(10) if extra else ''}"
                    f"**Action:** {action_text}"
                ),
                color=discord.Color.red(),
            )
            dm.set_thumbnail(url=DIFF_LOGO_URL)
            dm.set_footer(text="DIFF Meets • AutoMod")
            await member.send(embed=dm)
        except Exception:
            pass

    # ── Role backup/restore ───────────────────────────────
    async def _backup_roles(self, member: discord.Member):
        data = _load_json(ROLE_BACKUP_FILE)
        gk, uk = str(member.guild.id), str(member.id)
        data.setdefault(gk, {})[uk] = [
            r.id for r in member.roles
            if r.name != "@everyone" and not r.managed and r.id != AUTO_ROLE_ID
        ]
        _save_json(ROLE_BACKUP_FILE, data)

    async def _restore_roles(self, member: discord.Member):
        data   = _load_json(ROLE_BACKUP_FILE)
        ids    = data.get(str(member.guild.id), {}).get(str(member.id), [])
        roles  = [r for rid in ids if (r := member.guild.get_role(rid))]

        auto   = member.guild.get_role(AUTO_ROLE_ID)
        if auto and auto not in roles:
            roles.append(auto)

        if roles:
            try:
                await member.add_roles(*roles, reason="Restoring roles on rejoin")
            except Exception:
                pass

    # ── Events ────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id != GUILD_ID:
            return
        now_ts = time.monotonic()
        if now_ts - _join_dedup.get(member.id, 0) < _DEDUP_TTL:
            return
        _join_dedup[member.id] = now_ts

        # Restore any saved roles (handles rejoin)
        await self._restore_roles(member)

        # Log join
        now = _utcnow()
        account_age_days = (now - member.created_at.replace(tzinfo=timezone.utc)).days
        age_warning = " ⚠️ New Account" if account_age_days < 7 else ""
        member_count = member.guild.member_count

        embed = discord.Embed(
            title=f"📥 Member Joined{age_warning}",
            color=discord.Color.green() if account_age_days >= 7 else discord.Color.orange(),
            timestamp=now,
        )
        embed.set_author(name=f"{member.display_name} ({member})", icon_url=member.display_avatar.url)
        embed.add_field(name="👤 User", value=f"{member.mention}\n`{member.id}`", inline=True)
        embed.add_field(name="📅 Account Created", value=(
            f"{discord.utils.format_dt(member.created_at, style='D')}\n"
            f"{discord.utils.format_dt(member.created_at, style='R')}"
        ), inline=True)
        embed.add_field(name="👥 Members", value=f"#{member_count:,}", inline=True)
        if account_age_days < 7:
            embed.add_field(
                name="⚠️ New Account Alert",
                value=f"Account is only **{account_age_days} day(s)** old — potential alt or new user.",
                inline=False,
            )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="DIFF Meets • Join Logs")
        await self._send_log(embed, JOIN_LEAVE_LOG_CHANNEL_ID)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.guild.id != GUILD_ID:
            return
        now_ts = time.monotonic()
        if now_ts - _leave_dedup.get(member.id, 0) < _DEDUP_TTL:
            return
        _leave_dedup[member.id] = now_ts

        # Back up roles before they're lost
        await self._backup_roles(member)

        now = _utcnow()
        role_list = [r.mention for r in member.roles if r.name != "@everyone"]
        roles_str = " · ".join(role_list[:15]) if role_list else "No roles"
        member_count = member.guild.member_count

        if member.joined_at:
            joined_at = member.joined_at.replace(tzinfo=timezone.utc)
            time_in_server = now - joined_at
            days = time_in_server.days
            if days >= 365:
                duration = f"{days // 365}y {(days % 365) // 30}mo"
            elif days >= 30:
                duration = f"{days // 30}mo {days % 30}d"
            elif days >= 1:
                duration = f"{days}d"
            else:
                hours = time_in_server.seconds // 3600
                duration = f"{hours}h" if hours else "< 1h"
            joined_value = (
                f"{discord.utils.format_dt(member.joined_at, style='D')}\n"
                f"{discord.utils.format_dt(member.joined_at, style='R')} · stayed **{duration}**"
            )
        else:
            joined_value = "Unknown"

        embed = discord.Embed(
            title="📤 Member Left",
            color=discord.Color.dark_red(),
            timestamp=now,
        )
        embed.set_author(name=f"{member.display_name} ({member})", icon_url=member.display_avatar.url)
        embed.add_field(name="👤 User", value=f"{member.mention}\n`{member.id}`", inline=True)
        embed.add_field(name="📅 Joined Server", value=joined_value, inline=True)
        embed.add_field(name="👥 Members", value=f"#{member_count:,}", inline=True)
        if roles_str:
            embed.add_field(name="🏷️ Roles", value=roles_str[:1024], inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="DIFF Meets • Leave Logs")
        await self._send_log(embed, JOIN_LEAVE_LOG_CHANNEL_ID)

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

        content = message.content or ""
        now     = _utcnow()

        # ── Bad word filter ───────────────────────────────
        if BLOCK_BAD_WORDS:
            hit = _check_bad_word(content)
            if hit:
                await self._automod_action(message, "Blocked bad word", extra=f"Matched: `{hit}`")
                return

        # ── Invite filter ─────────────────────────────────
        if BLOCK_INVITES and _has_invite(content):
            await self._automod_action(message, "Blocked Discord invite link")
            return

        # ── Mass mention filter ───────────────────────────
        if len(message.mentions) >= MASS_MENTION_LIMIT:
            await self._automod_action(
                message, "Mass mention",
                extra=f"{len(message.mentions)} mentions in one message"
            )
            return

        uid = message.author.id

        # ── Spam rate filter ──────────────────────────────
        times = self._msg_times[uid]
        times.append(now)
        while times and (now - times[0]).total_seconds() > SPAM_WINDOW_SECS:
            times.popleft()

        if len(times) >= SPAM_MSG_COUNT:
            await self._automod_action(
                message, "Message spam",
                extra=f"{len(times)} messages in {SPAM_WINDOW_SECS}s"
            )
            times.clear()
            self._msg_texts[uid].clear()
            return

        # ── Duplicate spam filter ─────────────────────────
        texts     = self._msg_texts[uid]
        normed    = _normalize(content)
        texts.append((normed, now))
        while texts and (now - texts[0][1]).total_seconds() > DUP_WINDOW_SECS:
            texts.popleft()

        if normed:
            dupes = [t for t, _ in texts if t == normed]
            if len(dupes) >= DUP_MSG_COUNT:
                await self._automod_action(
                    message, "Duplicate message spam",
                    extra=f"Repeated {len(dupes)} times in {DUP_WINDOW_SECS}s"
                )
                texts.clear()
                times.clear()
                return

    @commands.Cog.listener()
    async def on_ready(self):
        print("[AutoMod] Cog ready.")


# =========================================================
# SETUP
# =========================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(AutoModCog(bot))
