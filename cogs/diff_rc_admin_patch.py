from __future__ import annotations

import os
import re
import sys
import sqlite3
from datetime import datetime, timezone

import discord
from discord.ext import commands

print("[RcAdminPatch] Module loading...")

ROLL_CALL_CHANNEL_ID = 1047338695352664165
GUILD_ID             = 850386896509337710
RC_DB_PATH           = os.path.join("diff_data", "diff_rollcall.db")

# Leadership
_LEADER_ROLE_ID = 850391095845584937
_CO_LEADER_ID   = 850391378559238235
_MANAGER_ID     = 990011447193006101
# Mod / admin tiers (mirrors _ALL_MOD_ROLE_IDS + developer in bot.py)
_SENIOR_ADMIN_ID  = 1034280192241307718
_ADMINISTRATOR_ID = 1328458892690063443
_LEAD_MOD_ID      = 1034282163513872424
_MODERATOR_ID     = 1328458459339030571
_JUNIOR_MOD_ID    = 1328458204262305792
_DEVELOPER_ID     = 1123234905057402890
# Combined set — any of these roles can use the staff dropdown
_STAFF_ROLES = {
    _LEADER_ROLE_ID, _CO_LEADER_ID, _MANAGER_ID,
    _SENIOR_ADMIN_ID, _ADMINISTRATOR_ID,
    _LEAD_MOD_ID, _MODERATOR_ID, _JUNIOR_MOD_ID,
    _DEVELOPER_ID,
}


def _main():
    return sys.modules["__main__"]


def _is_staff(member: discord.Member) -> bool:
    """Return True if member has any staff role OR administrator permission."""
    if member.guild_permissions.administrator:
        return True
    return any(r.id in _STAFF_ROLES for r in member.roles)


def _get_admin_msg_id() -> int | None:
    try:
        conn = sqlite3.connect(RC_DB_PATH)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT admin_message_id FROM rollcall_panels WHERE guild_id=?",
            (GUILD_ID,)
        ).fetchone()
        conn.close()
        if row and row["admin_message_id"]:
            return int(row["admin_message_id"])
    except Exception as e:
        print(f"[RcAdminPatch] DB read error: {e}")
    return None


def _get_finalized_meets() -> set:
    result = set()
    try:
        conn = sqlite3.connect(RC_DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT meet_number FROM rollcall_meets WHERE guild_id=? AND is_finalized=1",
            (GUILD_ID,),
        ).fetchall()
        conn.close()
        for row in rows:
            result.add(row["meet_number"])
    except Exception:
        pass
    return result


def _get_live_counts() -> dict:
    result = {n: {"yes": 0, "maybe": 0, "no": 0} for n in (1, 2, 3)}
    try:
        conn = sqlite3.connect(RC_DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT meet_number, status, COUNT(*) AS total "
            "FROM rollcall_responses WHERE guild_id=? GROUP BY meet_number, status",
            (GUILD_ID,)
        ).fetchall()
        conn.close()
        for row in rows:
            n, s, c = row["meet_number"], row["status"], row["total"]
            if n in result and s in result[n]:
                result[n][s] = c
    except Exception:
        pass
    return result


def _get_meet_details() -> dict:
    """Returns {meet_number: {class_name, start_time, host_id, date_text}} from DB."""
    result = {}
    try:
        conn = sqlite3.connect(RC_DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT meet_number, class_name, start_time, host_id, date_text "
            "FROM rollcall_meets WHERE guild_id=? ORDER BY meet_number",
            (GUILD_ID,)
        ).fetchall()
        conn.close()
        for row in rows:
            result[row["meet_number"]] = dict(row)
    except Exception:
        pass
    return result


def _parse_ts(date_text: str, start_time: str) -> int | None:
    """Parse a Unix timestamp from date_text + start_time strings."""
    try:
        from datetime import datetime as _dt
        from zoneinfo import ZoneInfo
        _tz = ZoneInfo("America/New_York")
        t = start_time.upper().replace("EST", "").replace("EDT", "").replace("ET", "").strip()
        for dfmt in ("%A, %B %d, %Y", "%B %d, %Y", "%A %B %d %Y",
                     "%b %d, %Y", "%m/%d/%Y", "%Y-%m-%d"):
            try:
                d = _dt.strptime(date_text.strip(), dfmt)
                break
            except ValueError:
                continue
        else:
            return None
        for tfmt in ("%I:%M %p", "%I %p", "%H:%M"):
            try:
                parsed_t = _dt.strptime(t, tfmt)
                break
            except ValueError:
                continue
        else:
            return None
        combined = d.replace(hour=parsed_t.hour, minute=parsed_t.minute,
                             second=0, microsecond=0, tzinfo=_tz)
        return int(combined.timestamp())
    except Exception:
        return None


def _build_embed() -> discord.Embed:
    counts = _get_live_counts()

    total_yes   = sum(counts[n]["yes"]   for n in (1, 2, 3))
    total_maybe = sum(counts[n]["maybe"] for n in (1, 2, 3))
    total_no    = sum(counts[n]["no"]    for n in (1, 2, 3))

    embed = discord.Embed(
        title="🛠️ DIFF Roll Call — Staff Tools",
        description=(
            f"**This week's response summary**\n"
            f"✅ `{total_yes}` attending  ·  ❓ `{total_maybe}` maybe  ·  ❌ `{total_no}` not attending\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=discord.Color.dark_teal(),
        timestamp=datetime.now(timezone.utc),
    )

    for n in (1, 2, 3):
        c = counts[n]
        embed.add_field(
            name=f"Meet {n}",
            value=f"✅ `{c['yes']}` · ❓ `{c['maybe']}` · ❌ `{c['no']}`",
            inline=True,
        )

    embed.set_footer(text="DIFF Roll Call • Staff Tools")
    return embed


def _build_attendance_embed(responses: dict) -> discord.Embed:
    embed = discord.Embed(
        title="📋 Roll Call — Attendance Overview",
        color=discord.Color.blurple(),
        timestamp=datetime.now(timezone.utc),
    )

    def _fmt(uids: list, limit: int = 20) -> str:
        if not uids:
            return "*Nobody yet*"
        tags = " ".join(f"<@{uid}>" for uid in uids[:limit])
        if len(uids) > limit:
            tags += f"  *+{len(uids) - limit} more*"
        return tags

    for n in (1, 2, 3):
        r       = responses.get(n, {"yes": [], "maybe": [], "no": []})
        yes_l   = r["yes"]
        maybe_l = r["maybe"]
        no_l    = r["no"]
        total   = len(yes_l) + len(maybe_l) + len(no_l)
        value = (
            f"✅ **Attending ({len(yes_l)}):** {_fmt(yes_l)}\n"
            f"❓ **Maybe ({len(maybe_l)}):** {_fmt(maybe_l)}\n"
            f"❌ **Not Attending ({len(no_l)}):** {_fmt(no_l)}\n"
            f"*{total} total response{'s' if total != 1 else ''}*"
        )
        embed.add_field(name=f"〔{n}〕 Meet {n}", value=value[:1024], inline=False)

    embed.set_footer(text="DIFF Roll Call • Staff View — visible only to you")
    return embed


# ── Finalize modal ─────────────────────────────────────────────────────────────

class _FinalizeModal(discord.ui.Modal):
    attendees = discord.ui.TextInput(
        label="Users who actually attended",
        style=discord.TextStyle.paragraph,
        placeholder="Paste @mentions or user IDs — e.g. <@123> <@456> 789...",
        required=False,
        max_length=4000,
    )

    def __init__(self, meet_number: int):
        super().__init__(title=f"✅ Finalize Meet {meet_number} Attendance")
        self.meet_number = meet_number

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            m        = _main()
            raw      = self.attendees.value or ""
            user_ids = sorted({int(x) for x in re.findall(r"\d{15,25}", raw)})
            m._rc_db.set_actual_attendees(interaction.guild.id, self.meet_number, user_ids)
            attended, no_shows = m._rc_db.finalize_no_shows(interaction.guild.id, self.meet_number)
            await m._rc_refresh_panel(interaction.guild)
            await m._rc_log_attendance(
                interaction.guild, self.meet_number, attended, no_shows, interaction.user
            )

            cog = interaction.client.cogs.get("RcAdminPatch")
            if cog:
                await cog.refresh_panel()

            def _tags(uids, limit=15):
                tags = " ".join(f"<@{uid}>" for uid in uids[:limit])
                if len(uids) > limit:
                    tags += f" *+{len(uids) - limit} more*"
                return tags or "*none*"

            attended_str = _tags(attended)
            noshows_str  = _tags(no_shows) if no_shows else "*none — great turnout!* 🎉"

            await interaction.followup.send(
                f"✅ **Meet {self.meet_number} finalized!**\n\n"
                f"**✅ Attended ({len(attended)}):** {attended_str}\n"
                f"**⚠️ No-shows ({len(no_shows)}):** {noshows_str}",
                ephemeral=True,
            )
        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"[RcAdminPatch] Finalize error: {e}")
            try:
                await interaction.followup.send(f"❌ Error finalizing: {e}", ephemeral=True)
            except Exception:
                pass


# ── Reset confirm ──────────────────────────────────────────────────────────────

class _ConfirmBtn(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Confirm Reset", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            m = _main()
            await m._rc_post_new_panel(interaction.guild, ping_roles=True)
            cog = interaction.client.cogs.get("RcAdminPatch")
            if cog:
                await cog.refresh_panel()
            await interaction.followup.send("✅ Roll call reset and reposted.", ephemeral=True)
        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"[RcAdminPatch] Reset confirm error: {e}")
            try:
                await interaction.followup.send(f"Reset failed: {e}", ephemeral=True)
            except Exception:
                pass
        self.view.stop()


class _CancelBtn(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Cancel", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.edit_message(content="Reset cancelled.", view=None)
        except Exception:
            pass
        self.view.stop()


class _ResetConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(_ConfirmBtn())
        self.add_item(_CancelBtn())


# ── Staff dropdown ─────────────────────────────────────────────────────────────

class _StaffSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            custom_id="diff_rollcall_finalize:select_v2",
            placeholder="⚙️  Choose a staff action…",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="View Attendance",
                    value="attendance",
                    emoji="📊",
                    description="See a full breakdown of who's going, maybe, or not going.",
                ),
                discord.SelectOption(
                    label="Sync from Schedule",
                    value="sync",
                    emoji="🗓️",
                    description="Update meet dates, times, classes & hosts from the schedule.",
                ),
                discord.SelectOption(
                    label="Refresh Panel",
                    value="refresh",
                    emoji="🔃",
                    description="Re-render this panel with the latest response counts.",
                ),
                discord.SelectOption(
                    label="Reset Roll Call",
                    value="reset",
                    emoji="🗑️",
                    description="Wipe all responses and post a fresh roll call panel.",
                ),
            ],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        # ── ALWAYS defer first — guarantees the 3-second window is met ──────
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.InteractionResponded:
            pass
        except Exception as e:
            print(f"[RcAdminPatch] defer failed: {e}")
            return

        # ── Permission check (after defer so interaction is already acked) ──
        member = interaction.user
        if not isinstance(member, discord.Member) or not _is_staff(member):
            try:
                await interaction.followup.send("Staff only.", ephemeral=True)
            except Exception:
                pass
            print(f"[RcAdminPatch] Unauthorized dropdown use by {member} ({getattr(member, 'id', '?')})")
            return

        v = self.values[0] if self.values else ""
        print(f"[RcAdminPatch] Staff action '{v}' by {member} ({member.id})")

        try:
            if v == "reset":
                await interaction.followup.send(
                    "⚠️ **Reset Roll Call?**\nThis clears **all** responses and posts a fresh panel.",
                    view=_ResetConfirmView(),
                    ephemeral=True,
                )

            elif v == "attendance":
                m         = _main()
                responses = m._rc_db.get_all_responses(interaction.guild.id)
                await interaction.followup.send(
                    embed=_build_attendance_embed(responses), ephemeral=True
                )
                cog = interaction.client.cogs.get("RcAdminPatch")
                if cog:
                    await cog.refresh_panel()

            elif v == "sync":
                m        = _main()
                schedule = m._asched_load()
                guild    = interaction.guild
                rc_meets = []
                for idx, day in enumerate(m._HRSVP_DAYS, 1):
                    entry = schedule["days"].get(day, {})
                    rc_meets.append({
                        "meet_number":  idx,
                        "class_name":   entry.get("class", "TBD"),
                        "start_time":   entry.get("time",  "TBD"),
                        "host_id":      entry.get("host_id"),
                        "date_text":    entry.get("day",   day),
                        "is_finalized": entry.get("host_id") is not None,
                    })
                await m._rc_sync_from_schedule(guild, rc_meets)
                await interaction.followup.send(
                    "✅ Schedule synced — roll call updated with latest dates, times, and hosts.",
                    ephemeral=True,
                )
                cog = interaction.client.cogs.get("RcAdminPatch")
                if cog:
                    await cog.refresh_panel()

            elif v == "refresh":
                cog = interaction.client.cogs.get("RcAdminPatch")
                if cog:
                    await cog.refresh_panel()
                await interaction.followup.send(
                    "🔃 Panel refreshed with the latest response counts.", ephemeral=True
                )

            else:
                await interaction.followup.send(
                    f"Unknown action: `{v}`", ephemeral=True
                )

        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"[RcAdminPatch] Staff action '{v}' error: {e}")
            try:
                await interaction.followup.send(
                    f"❌ Action failed: {e}", ephemeral=True
                )
            except Exception:
                pass


class _StaffView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(_StaffSelect())


# ── Cog ────────────────────────────────────────────────────────────────────────

class RcAdminPatch(commands.Cog, name="RcAdminPatch"):
    def __init__(self, bot: commands.Bot):
        self.bot  = bot
        self.view = _StaffView()
        try:
            bot.add_view(self.view)
            print("[RcAdminPatch] Persistent view registered.")
        except Exception as e:
            print(f"[RcAdminPatch] add_view failed: {e}")

    async def _find_and_delete_old_panel(self, ch: discord.TextChannel) -> None:
        """Delete any existing staff panel messages so a fresh one can be posted."""
        bot_id = self.bot.user.id if self.bot.user else None
        if not bot_id:
            return
        admin_id = _get_admin_msg_id()
        if admin_id:
            try:
                old = await ch.fetch_message(admin_id)
                await old.delete()
                print(f"[RcAdminPatch] Deleted old panel (DB id={admin_id}).")
            except Exception:
                pass
        try:
            async for msg in ch.history(limit=100):
                if msg.author.id != bot_id:
                    continue
                for row in msg.components:
                    for child in row.children:
                        cid = getattr(child, "custom_id", "") or ""
                        if cid.startswith("diff_rollcall_finalize:"):
                            try:
                                await msg.delete()
                                print(f"[RcAdminPatch] Deleted stale panel (scan id={msg.id}).")
                            except Exception:
                                pass
        except Exception as e:
            print(f"[RcAdminPatch] Scan/delete error: {e}")

    async def refresh_panel(self, *, force_repost: bool = False) -> None:
        """Edit (or repost) the staff admin panel using the cog's registered view."""
        ch = self.bot.get_channel(ROLL_CALL_CHANNEL_ID)
        if not isinstance(ch, discord.TextChannel):
            try:
                ch = await self.bot.fetch_channel(ROLL_CALL_CHANNEL_ID)
            except Exception as e:
                print(f"[RcAdminPatch] Cannot fetch channel: {e}")
                return

        if not force_repost:
            admin_id = _get_admin_msg_id()
            if admin_id:
                try:
                    msg = await ch.fetch_message(admin_id)
                    # Always use self.view so the registered persistent view stays attached
                    await msg.edit(embed=_build_embed(), view=self.view)
                    print(f"[RcAdminPatch] Panel edited via DB (msg {admin_id}).")
                    return
                except discord.NotFound:
                    print("[RcAdminPatch] DB message not found, will repost.")
                except Exception as e:
                    print(f"[RcAdminPatch] Edit failed ({e}), will repost.")

        # Delete all old copies then post a fresh panel using self.view
        await self._find_and_delete_old_panel(ch)
        new_msg = await ch.send(embed=_build_embed(), view=self.view)
        print(f"[RcAdminPatch] Fresh panel posted (msg {new_msg.id}).")
        try:
            conn = sqlite3.connect(RC_DB_PATH)
            conn.execute(
                "UPDATE rollcall_panels SET admin_message_id=? WHERE guild_id=?",
                (new_msg.id, GUILD_ID)
            )
            if conn.execute("SELECT changes()").fetchone()[0] == 0:
                conn.execute(
                    "INSERT INTO rollcall_panels (guild_id, channel_id, admin_message_id) VALUES (?,?,?)",
                    (GUILD_ID, ch.id, new_msg.id)
                )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[RcAdminPatch] DB update error: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        import asyncio
        await asyncio.sleep(10)
        print("[RcAdminPatch] on_ready refresh…")
        await self.refresh_panel()

    @commands.command(name="patch_rc_admin")
    @commands.has_permissions(manage_guild=True)
    async def cmd_patch(self, ctx: commands.Context):
        await ctx.send("Reposting roll call staff panel…", delete_after=5)
        await self.refresh_panel(force_repost=True)
        await ctx.send("✅ Done — panel reposted with updated options.", delete_after=10)


print("[RcAdminPatch] Module loaded OK.")


async def setup(bot: commands.Bot):
    await bot.add_cog(RcAdminPatch(bot))
