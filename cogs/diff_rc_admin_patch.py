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

_LEADER_ROLE_ID = 850391095845584937
_CO_LEADER_ID   = 850391378559238235
_MANAGER_ID     = 990011447193006101
_ADMIN_ROLES    = {_LEADER_ROLE_ID, _CO_LEADER_ID, _MANAGER_ID}


def _main():
    return sys.modules["__main__"]


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


def _build_embed() -> discord.Embed:
    counts    = _get_live_counts()
    finalized = _get_finalized_meets()

    embed = discord.Embed(
        title="🛠️ DIFF Roll Call — Staff Tools",
        description=(
            "Use the dropdown below to manage this week's roll call.\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=discord.Color.dark_teal(),
        timestamp=datetime.now(timezone.utc),
    )

    count_lines = []
    for n in (1, 2, 3):
        c = counts[n]
        if n in finalized:
            count_lines.append(
                f"**Meet {n}** — ✅ `{c['yes']}` · ❓ `{c['maybe']}` · ❌ `{c['no']}`\n"
                f"🏁 *Finalized*"
            )
        else:
            total     = c["yes"] + c["maybe"] + c["no"]
            bar_yes   = round(c["yes"]   / max(total, 10) * 10)
            bar_maybe = round(c["maybe"] / max(total, 10) * 10)
            bar = "🟩" * bar_yes + "🟨" * bar_maybe + "⬜" * (10 - bar_yes - bar_maybe)
            count_lines.append(
                f"**Meet {n}** — ✅ `{c['yes']}` · ❓ `{c['maybe']}` · ❌ `{c['no']}`\n{bar}"
            )
    embed.add_field(
        name="📊 Live RSVP Counts",
        value="\n\n".join(count_lines),
        inline=False,
    )
    embed.add_field(
        name="🏁 Finalize Attendance",
        value="Select a meet → paste who actually attended. Stats and no-shows update automatically.",
        inline=False,
    )
    embed.add_field(
        name="📋 View Attendance",
        value="See who voted for each meet, with full ✅/❓/❌ breakdown.",
        inline=False,
    )
    embed.add_field(
        name="🗓️ Sync from Schedule",
        value="Pull the latest dates, times, hosts, and classes from the host schedule panel.",
        inline=False,
    )
    embed.add_field(
        name="🔄 Reset Roll Call",
        value="Clears all responses and reposts a fresh roll call for a new week.",
        inline=False,
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


# ── Shared helper: rebuild + reset the staff panel ─────────────────────────────

async def _refresh_admin_panel() -> None:
    """Re-edit the staff panel with a fresh embed and fresh view (resets dropdown)."""
    try:
        admin_id = _get_admin_msg_id()
        if not admin_id:
            return
        m  = _main()
        ch = m.bot.get_channel(ROLL_CALL_CHANNEL_ID)
        if not isinstance(ch, discord.TextChannel):
            return
        msg = await ch.fetch_message(admin_id)
        await msg.edit(embed=_build_embed(), view=_StaffView())
    except Exception as e:
        print(f"[RcAdminPatch] _refresh_admin_panel error: {e}")


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
            await _refresh_admin_panel()

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
            print(f"[RcAdminPatch] Finalize error: {e}")
            await interaction.followup.send(f"Error finalizing: {e}", ephemeral=True)


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
        await interaction.response.edit_message(content="Reset cancelled.", view=None)
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
            placeholder="Select a staff action…",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Finalize Meet 1", value="fin1", emoji="🏁",
                    description="Mark attendees and flag no-shows for Meet 1.",
                ),
                discord.SelectOption(
                    label="Finalize Meet 2", value="fin2", emoji="🏁",
                    description="Mark attendees and flag no-shows for Meet 2.",
                ),
                discord.SelectOption(
                    label="Finalize Meet 3", value="fin3", emoji="🏁",
                    description="Mark attendees and flag no-shows for Meet 3.",
                ),
                discord.SelectOption(
                    label="View Attendance", value="attendance", emoji="📋",
                    description="See who voted ✅/❓/❌ for each meet.",
                ),
                discord.SelectOption(
                    label="Sync from Schedule", value="sync", emoji="🗓️",
                    description="Pull latest dates, times, hosts from the host schedule.",
                ),
                discord.SelectOption(
                    label="Reset Roll Call", value="reset", emoji="🔄",
                    description="Clear all responses and post a fresh roll call.",
                ),
            ],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        member = interaction.user
        if not isinstance(member, discord.Member) or \
                not any(r.id in _ADMIN_ROLES for r in member.roles):
            return await interaction.response.send_message("Staff only.", ephemeral=True)

        v = self.values[0]

        if v in ("fin1", "fin2", "fin3"):
            return await interaction.response.send_modal(_FinalizeModal(int(v[-1])))

        if v == "attendance":
            await interaction.response.defer(ephemeral=True)
            try:
                m         = _main()
                responses = m._rc_db.get_all_responses(interaction.guild.id)
                await interaction.followup.send(
                    embed=_build_attendance_embed(responses), ephemeral=True
                )
            except Exception as e:
                await interaction.followup.send(f"Error fetching attendance: {e}", ephemeral=True)
            await _refresh_admin_panel()
            return

        if v == "sync":
            try:
                await interaction.response.defer(ephemeral=True)
                m        = _main()
                schedule = m._asched_load()
                guild    = interaction.guild
                rc_meets = []
                for idx, day in enumerate(m._HRSVP_DAYS, 1):
                    entry = schedule["days"].get(day, {})
                    rc_meets.append({
                        "meet_number": idx,
                        "class_name":  entry.get("class", "TBD"),
                        "start_time":  entry.get("time",  "TBD"),
                        "host_id":     entry.get("host_id"),
                        "date_text":   entry.get("day",   day),
                        "is_finalized": entry.get("host_id") is not None,
                    })
                await m._rc_sync_from_schedule(guild, rc_meets)
                await interaction.followup.send(
                    "✅ Schedule synced — roll call updated with latest dates, times, and hosts.",
                    ephemeral=True,
                )
                await _refresh_admin_panel()
                return
            except Exception as e:
                try:
                    await interaction.followup.send(f"Sync failed: {e}", ephemeral=True)
                except Exception:
                    pass
                return

        if v == "reset":
            return await interaction.response.send_message(
                "⚠️ **Reset Roll Call?**\nThis clears **all** responses and posts a fresh panel.",
                view=_ResetConfirmView(),
                ephemeral=True,
            )


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

    async def refresh_panel(self) -> None:
        ch = self.bot.get_channel(ROLL_CALL_CHANNEL_ID)
        if not isinstance(ch, discord.TextChannel):
            try:
                ch = await self.bot.fetch_channel(ROLL_CALL_CHANNEL_ID)
            except Exception as e:
                print(f"[RcAdminPatch] Cannot fetch channel: {e}")
                return

        bot_id   = self.bot.user.id if self.bot.user else None
        admin_id = _get_admin_msg_id()
        if admin_id:
            try:
                msg = await ch.fetch_message(admin_id)
                await msg.edit(embed=_build_embed(), view=self.view)
                print(f"[RcAdminPatch] Panel updated via DB (msg {admin_id}).")
                return
            except discord.NotFound:
                print("[RcAdminPatch] DB message not found, scanning…")
            except Exception as e:
                print(f"[RcAdminPatch] DB edit failed: {e}")

        if not bot_id:
            return
        try:
            async for msg in ch.history(limit=80):
                if msg.author.id != bot_id:
                    continue
                for row in msg.components:
                    for child in row.children:
                        cid = getattr(child, "custom_id", "") or ""
                        if cid.startswith("diff_rollcall_finalize:"):
                            await msg.edit(embed=_build_embed(), view=self.view)
                            print(f"[RcAdminPatch] Panel updated via scan (msg {msg.id}).")
                            return
        except Exception as e:
            print(f"[RcAdminPatch] Scan error: {e}")

        print("[RcAdminPatch] Admin panel not found.")

    @commands.Cog.listener()
    async def on_ready(self):
        import asyncio
        await asyncio.sleep(10)
        print("[RcAdminPatch] on_ready refresh…")
        await self.refresh_panel()

    @commands.command(name="patch_rc_admin")
    @commands.has_permissions(manage_guild=True)
    async def cmd_patch(self, ctx: commands.Context):
        await ctx.send("Refreshing roll call staff panel…", delete_after=5)
        await self.refresh_panel()
        await ctx.send("Done.", delete_after=8)


print("[RcAdminPatch] Module loaded OK.")


async def setup(bot: commands.Bot):
    await bot.add_cog(RcAdminPatch(bot))
