from __future__ import annotations

import os
import re
import sys
import sqlite3

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
    """Return the live __main__ module (the running bot.py instance)."""
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


def _build_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🛠️ DIFF Roll Call — Staff Tools",
        description=(
            "Use the dropdown below to manage this week's roll call.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=discord.Color.dark_teal(),
    )
    embed.add_field(
        name="🏁 Finalize Attendance",
        value="Select a meet and paste the users who actually attended. Stats and no-shows update automatically.",
        inline=False,
    )
    embed.add_field(
        name="📊 View Stats",
        value="See current RSVP counts for all three meets.",
        inline=False,
    )
    embed.add_field(
        name="🔄 Reset Roll Call",
        value="Clears all responses and reposts a fresh roll call for a new week.",
        inline=False,
    )
    embed.set_footer(text="DIFF Roll Call • Staff Tools V2")
    return embed


# ── Finalize modal ────────────────────────────────────────────────────────────

class _FinalizeModal(discord.ui.Modal):
    attendees = discord.ui.TextInput(
        label="Users who actually attended",
        style=discord.TextStyle.paragraph,
        placeholder="Paste mentions or IDs: <@123> <@456>",
        required=False,
        max_length=4000,
    )

    def __init__(self, meet_number: int):
        super().__init__(title=f"Finalize Meet {meet_number} Attendance")
        self.meet_number = meet_number

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            m = _main()
            raw = self.attendees.value or ""
            user_ids = sorted({int(x) for x in re.findall(r"\d{15,25}", raw)})
            m._rc_db.set_actual_attendees(interaction.guild.id, self.meet_number, user_ids)
            attended, no_shows = m._rc_db.finalize_no_shows(interaction.guild.id, self.meet_number)
            await m._rc_refresh_panel(interaction.guild)
            await m._rc_log_attendance(
                interaction.guild, self.meet_number, attended, no_shows, interaction.user
            )
            await interaction.response.send_message(
                f"Meet {self.meet_number} finalized. "
                f"Present: **{len(attended)}** | No-shows: **{len(no_shows)}**",
                ephemeral=True,
            )
        except Exception as e:
            print(f"[RcAdminPatch] Finalize error: {e}")
            try:
                await interaction.response.send_message(
                    f"Error finalizing: {e}", ephemeral=True
                )
            except Exception:
                pass


# ── Reset confirm buttons ─────────────────────────────────────────────────────

class _ConfirmBtn(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Confirm Reset", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            m = _main()
            await m._rc_post_new_panel(interaction.guild, ping_roles=True)
            # Re-apply dropdown view to the freshly posted admin panel
            cog = interaction.client.cogs.get("RcAdminPatch")
            if cog:
                await cog.refresh_panel()
            await interaction.followup.send(
                "✅ Roll call reset and reposted.", ephemeral=True
            )
        except Exception as e:
            print(f"[RcAdminPatch] Reset confirm error: {e}")
            try:
                await interaction.followup.send(
                    f"Reset failed: {e}", ephemeral=True
                )
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
                    label="Finalize Meet 1", value="fin1",
                    description="Mark attendees and flag no-shows for Meet 1.",
                ),
                discord.SelectOption(
                    label="Finalize Meet 2", value="fin2",
                    description="Mark attendees and flag no-shows for Meet 2.",
                ),
                discord.SelectOption(
                    label="Finalize Meet 3", value="fin3",
                    description="Mark attendees and flag no-shows for Meet 3.",
                ),
                discord.SelectOption(
                    label="View Attendance Stats", value="stats",
                    description="See current RSVP counts for all meets.",
                ),
                discord.SelectOption(
                    label="Reset Roll Call", value="reset",
                    description="Clear all responses and post a fresh roll call.",
                ),
            ],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        member = interaction.user
        if not isinstance(member, discord.Member) or \
                not any(r.id in _ADMIN_ROLES for r in member.roles):
            return await interaction.response.send_message(
                "Staff only.", ephemeral=True
            )

        v = self.values[0]

        if v in ("fin1", "fin2", "fin3"):
            return await interaction.response.send_modal(
                _FinalizeModal(int(v[-1]))
            )

        if v == "stats":
            try:
                m = _main()
                embed = m._rc_build_rollcall_embed(interaction.guild)
                embed.title = "📊 Current Roll Call Stats"
                return await interaction.response.send_message(
                    embed=embed, ephemeral=True
                )
            except Exception as e:
                return await interaction.response.send_message(
                    f"Error fetching stats: {e}", ephemeral=True
                )

        if v == "reset":
            return await interaction.response.send_message(
                "Reset Roll Call? This clears **all** responses and posts a fresh panel.",
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
        """Edit the admin panel message to show the new dropdown embed + view."""
        ch = self.bot.get_channel(ROLL_CALL_CHANNEL_ID)
        if not isinstance(ch, discord.TextChannel):
            try:
                ch = await self.bot.fetch_channel(ROLL_CALL_CHANNEL_ID)
            except Exception as e:
                print(f"[RcAdminPatch] Cannot fetch channel: {e}")
                return

        bot_id = self.bot.user.id if self.bot.user else None

        # Try the DB-stored message ID first
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

        # Fallback: scan history for the old button-based admin panel
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
                            print(
                                f"[RcAdminPatch] Panel updated via scan (msg {msg.id})."
                            )
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
        """Manually refresh the roll call staff panel to the dropdown version."""
        await ctx.send("Refreshing roll call staff panel…", delete_after=5)
        await self.refresh_panel()
        await ctx.send("Done.", delete_after=8)


print("[RcAdminPatch] Module loaded OK.")


async def setup(bot: commands.Bot):
    await bot.add_cog(RcAdminPatch(bot))
