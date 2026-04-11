from __future__ import annotations

import asyncio
import html as html_lib
import io
import json
import os
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional

import discord
from discord.ext import commands

# =========================================================
# CONFIG
# =========================================================
TARGET_CHANNEL_ID   = 1177449010949259355
GUILD_ID            = 850386896509337710
LOG_CHANNEL_ID      = 1485265848099799163   # staff-logs

COLOR_TEAM_ROLE_ID  = 1115495008670330902
TICKET_CATEGORY_ID  = 0   # <-- active tickets category ID
ARCHIVE_CATEGORY_ID = 0   # <-- archived tickets category ID

DATA_DIR          = "diff_data"
DATA_FILE         = os.path.join(DATA_DIR, "color_lab_panel.json")
OPEN_TICKETS_FILE = os.path.join(DATA_DIR, "color_lab_open_tickets.json")
TRANSCRIPTS_DIR   = os.path.join(DATA_DIR, "color_lab_transcripts")

DIFF_LOGO_URL = (
    "https://media.discordapp.net/attachments/1107375326625005719/"
    "1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm="
    "2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
    "&=&format=webp&quality=lossless&width=1376&height=917"
)

EMBED_COLOR   = 0x8F7CFF
SUCCESS_COLOR = 0x57F287
WARNING_COLOR = 0xFEE75C
ERROR_COLOR   = 0xED4245
PANEL_TAG     = "DIFF_COLOR_LAB_PANEL_V2"


# =========================================================
# FILE HELPERS
# =========================================================
def _ensure_dirs() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)


def _load(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(path: str, data: dict) -> None:
    _ensure_dirs()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def _get_msg_id() -> Optional[int]:
    v = _load(DATA_FILE).get("panel_message_id")
    return int(v) if v else None


def _set_msg_id(mid: int) -> None:
    d = _load(DATA_FILE)
    d["panel_message_id"] = mid
    _save(DATA_FILE, d)


def _load_tickets() -> dict:
    return _load(OPEN_TICKETS_FILE)


def _save_tickets(data: dict) -> None:
    _save(OPEN_TICKETS_FILE, data)


def _clean_name(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9-]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text[:25] if text else "request"


_EST_TZ = ZoneInfo("America/New_York")


def _ts() -> str:
    return datetime.now(_EST_TZ).strftime("%Y-%m-%d_%I-%M-%S_%p_EST")


def _is_color_team(member: discord.Member) -> bool:
    if member.guild_permissions.administrator or member.guild_permissions.manage_channels:
        return True
    return any(r.id == COLOR_TEAM_ROLE_ID for r in member.roles)


# =========================================================
# TRANSCRIPT BUILDER
# =========================================================
async def _build_transcript(channel: discord.TextChannel) -> str:
    messages = [m async for m in channel.history(limit=None, oldest_first=True)]

    rows = []
    for m in messages:
        created = m.created_at.astimezone(_EST_TZ).strftime("%b %d, %Y %-I:%M %p EST")
        display = getattr(m.author, "display_name", None) or str(m.author)
        author  = html_lib.escape(display)
        content = html_lib.escape(m.content or "")

        embed_parts = []
        for emb in m.embeds:
            title  = html_lib.escape(emb.title or "")
            desc   = html_lib.escape(emb.description or "")
            fields = "".join(
                f"<div class='field'><b>{html_lib.escape(f.name)}:</b><br>{html_lib.escape(f.value)}</div>"
                for f in emb.fields
            )
            embed_parts.append(
                f"<div class='embed'><div><b>{title}</b></div><div>{desc}</div>{fields}</div>"
            )

        attachments = "".join(
            f"<div class='attachment'><a href='{html_lib.escape(a.url)}'>{html_lib.escape(a.filename)}</a></div>"
            for a in m.attachments
        )

        rows.append(f"""
        <div class="message">
            <div class="meta">
                <span class="author">{author}</span>
                <span class="time">{created}</span>
            </div>
            <div class="content">{content.replace(chr(10), "<br>")}</div>
            {"".join(embed_parts)}{attachments}
        </div>""")

    title_esc = html_lib.escape(f"Transcript — #{channel.name}")
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{title_esc}</title>
<style>
body{{background:#1e1f22;color:#e3e5e8;font-family:Arial,sans-serif;padding:20px}}
h1{{color:#fff;border-bottom:1px solid #3f4147;padding-bottom:10px}}
.message{{background:#2b2d31;border:1px solid #3f4147;border-radius:10px;padding:12px;margin-bottom:12px}}
.meta{{margin-bottom:8px;font-size:13px}}
.author{{font-weight:bold;color:#fff}}
.time{{color:#b5bac1;margin-left:10px}}
.content{{white-space:normal;line-height:1.5}}
.embed{{background:#232428;border-left:4px solid #8F7CFF;padding:10px;margin-top:10px;border-radius:8px}}
.field{{margin-top:8px}}
.attachment{{margin-top:8px}}
a{{color:#7ab8ff;text-decoration:none}}
</style></head><body>
<h1>{title_esc}</h1>
<div>Generated: {_ts()}</div>
<div style="margin-top:20px">{"".join(rows)}</div>
</body></html>"""


# =========================================================
# MODALS
# =========================================================
class ColorTicketRequestModal(discord.ui.Modal, title="Open Private Color Request"):
    reference = discord.ui.TextInput(
        label="Reference Image Link or Description",
        placeholder="Paste an image link or describe the exact color/build",
        required=True, max_length=300,
        style=discord.TextStyle.paragraph,
    )
    hex_code = discord.ui.TextInput(
        label="Hex Code (if known)",
        placeholder="#A9E3D6 — or type Unknown",
        required=True, max_length=30,
    )
    car_name = discord.ui.TextInput(
        label="Car Name",
        placeholder="Example: Vorschlaghammer",
        required=True, max_length=100,
    )
    finish = discord.ui.TextInput(
        label="Finish Type",
        placeholder="Metallic / Pearlescent / Matte / Worn / Unknown",
        required=True, max_length=100,
    )
    extra_notes = discord.ui.TextInput(
        label="Extra Notes (optional)",
        placeholder="Lighting, angle, or anything else the Color Team should know",
        required=False, max_length=400,
        style=discord.TextStyle.paragraph,
    )

    def __init__(self, cog: "ColorLabCog"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            return await interaction.response.send_message(
                "This can only be used inside the server.", ephemeral=True
            )

        if COLOR_TEAM_ROLE_ID == 0 or TICKET_CATEGORY_ID == 0 or ARCHIVE_CATEGORY_ID == 0:
            return await interaction.response.send_message(
                "The Color Lab ticket system is not fully configured yet. "
                "Please ask staff to set the Color Team role and ticket categories.",
                ephemeral=True,
            )

        color_team_role = guild.get_role(COLOR_TEAM_ROLE_ID)
        category        = guild.get_channel(TICKET_CATEGORY_ID)

        if color_team_role is None:
            return await interaction.response.send_message(
                "Could not find the Color Team role. Please contact staff.", ephemeral=True
            )
        if not isinstance(category, discord.CategoryChannel):
            return await interaction.response.send_message(
                "Could not find the ticket category. Please contact staff.", ephemeral=True
            )

        requester    = interaction.user
        open_tickets = _load_tickets()
        existing_id  = open_tickets.get(str(requester.id))

        if existing_id:
            existing_ch = guild.get_channel(int(existing_id))
            if existing_ch:
                return await interaction.response.send_message(
                    f"You already have an open color ticket: {existing_ch.mention}\n"
                    "Please use that ticket or wait for it to be closed before opening another.",
                    ephemeral=True,
                )
            open_tickets.pop(str(requester.id), None)
            _save_tickets(open_tickets)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            requester: discord.PermissionOverwrite(
                view_channel=True, send_messages=True,
                read_message_history=True, attach_files=True, embed_links=True,
            ),
            color_team_role: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True,
                manage_messages=True, attach_files=True, embed_links=True, manage_channels=True,
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, manage_channels=True,
                manage_messages=True, read_message_history=True,
            ),
        }

        await interaction.response.defer(ephemeral=True)

        try:
            ticket_ch = await guild.create_text_channel(
                name=f"color-{_clean_name(requester.display_name)}",
                category=category,
                overwrites=overwrites,
                topic=f"DIFF Color Lab | color_request_user_id:{requester.id} | status:open",
                reason=f"Color request ticket for {requester}",
            )
        except Exception as e:
            return await interaction.followup.send(
                f"Failed to create ticket channel: {e}", ephemeral=True
            )

        open_tickets[str(requester.id)] = ticket_ch.id
        _save_tickets(open_tickets)

        # ---- Opening embed inside ticket ----
        ticket_embed = discord.Embed(
            title="🎨 Color Request Opened",
            description=(
                f"Hey {requester.mention}, your private Color Lab ticket is now open.\n"
                f"The **Color Team** will review your request and reply here shortly.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=EMBED_COLOR,
            timestamp=datetime.now(timezone.utc),
        )
        ticket_embed.add_field(name="📎 Reference",  value=str(self.reference),          inline=False)
        ticket_embed.add_field(name="🎨 Hex Code",   value=f"`{str(self.hex_code)}`",    inline=True)
        ticket_embed.add_field(name="🚗 Car Name",   value=str(self.car_name),           inline=True)
        ticket_embed.add_field(name="✨ Finish",      value=str(self.finish),             inline=True)
        if str(self.extra_notes).strip():
            ticket_embed.add_field(name="📝 Extra Notes", value=str(self.extra_notes),   inline=False)
        ticket_embed.add_field(
            name="📋 What happens next",
            value=(
                "› The Color Team will match your color in GTA\n"
                "› An official result will be posted in this ticket\n"
                "› Once complete, the ticket will be archived"
            ),
            inline=False,
        )
        ticket_embed.set_thumbnail(url=DIFF_LOGO_URL)
        ticket_embed.set_footer(text="DIFF Color Lab • Private Ticket")

        await ticket_ch.send(
            content=f"{requester.mention} {color_team_role.mention}",
            embed=ticket_embed,
            view=ColorTicketControlsView(self.cog),
            allowed_mentions=discord.AllowedMentions(users=True, roles=True),
        )

        await interaction.followup.send(
            f"Your private color ticket has been created: {ticket_ch.mention}\n"
            "Head over there and wait for the Color Team to respond.",
            ephemeral=True,
        )
        await self.cog.log_action(
            guild, f"🎨 Opened color ticket {ticket_ch.mention} for {requester.mention}"
        )


class ColorResultModal(discord.ui.Modal, title="Post Official Color Result"):
    base_color = discord.ui.TextInput(
        label="Base Color",
        placeholder="#A9E3D6 / Seafoam Blue",
        required=True, max_length=100,
    )
    pearl = discord.ui.TextInput(
        label="Pearl / Pearlescent",
        placeholder="Ice White / Diamond Blue / None",
        required=True, max_length=100,
    )
    finish = discord.ui.TextInput(
        label="Finish Type",
        placeholder="Metallic / Pearlescent / Matte / Worn",
        required=True, max_length=100,
    )
    how_to_apply = discord.ui.TextInput(
        label="How to Apply (optional)",
        placeholder="Any steps, tips, or GTA notes for the requester",
        required=False, max_length=400,
        style=discord.TextStyle.paragraph,
    )
    notes = discord.ui.TextInput(
        label="Extra Notes (optional)",
        placeholder="Lighting notes, closest alternatives, etc.",
        required=False, max_length=400,
        style=discord.TextStyle.paragraph,
    )

    async def on_submit(self, interaction: discord.Interaction):
        member = interaction.user if isinstance(interaction.user, discord.Member) else None
        if member is None:
            return await interaction.response.send_message("Could not verify your permissions.", ephemeral=True)

        if not _is_color_team(member):
            return await interaction.response.send_message(
                "Only the Color Team or staff can post official color results.", ephemeral=True
            )

        embed = discord.Embed(
            title="✅ Official Color Match — Result",
            description="Your color has been matched by the DIFF Color Team.",
            color=SUCCESS_COLOR,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="🎨 Base Color",   value=str(self.base_color), inline=True)
        embed.add_field(name="✨ Pearl",         value=str(self.pearl),      inline=True)
        embed.add_field(name="🪞 Finish",        value=str(self.finish),     inline=True)
        if str(self.how_to_apply).strip():
            embed.add_field(name="📋 How to Apply", value=str(self.how_to_apply), inline=False)
        if str(self.notes).strip():
            embed.add_field(name="📝 Extra Notes",  value=str(self.notes),         inline=False)
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.set_footer(text=f"Posted by {interaction.user.display_name} • DIFF Color Lab")
        await interaction.response.send_message(embed=embed)


class ColorTeamNoteModal(discord.ui.Modal, title="Add Color Team Note"):
    note = discord.ui.TextInput(
        label="Note",
        placeholder="An update, question, or message for the requester…",
        required=True, max_length=600,
        style=discord.TextStyle.paragraph,
    )

    async def on_submit(self, interaction: discord.Interaction):
        member = interaction.user if isinstance(interaction.user, discord.Member) else None
        if member is None:
            return await interaction.response.send_message("Could not verify permissions.", ephemeral=True)
        if not _is_color_team(member):
            return await interaction.response.send_message(
                "Only the Color Team or staff can add notes.", ephemeral=True
            )

        embed = discord.Embed(
            title="📝 Color Team Update",
            description=str(self.note),
            color=WARNING_COLOR,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_footer(text=f"Note by {interaction.user.display_name} • DIFF Color Lab")
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        await interaction.response.send_message(embed=embed)


# =========================================================
# TICKET CONTROLS  (inside each ticket channel)
# =========================================================
class _TicketActionsSelect(discord.ui.Select):
    def __init__(self, cog: "ColorLabCog"):
        super().__init__(
            custom_id="diff_color_lab_ticket_actions_select_v2",
            placeholder="🎨 Select an action…",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Post Official Result",
                    value="result",
                    emoji="✅",
                    description="Post the matched color result for the requester.",
                ),
                discord.SelectOption(
                    label="Add Team Note",
                    value="note",
                    emoji="📝",
                    description="Send an update or question to the requester.",
                ),
                discord.SelectOption(
                    label="Close Request",
                    value="close",
                    emoji="🔒",
                    description="Lock the ticket once resolved (before archiving).",
                ),
                discord.SelectOption(
                    label="Archive & Close",
                    value="archive",
                    emoji="📦",
                    description="Archive this ticket and save a full transcript.",
                ),
            ],
            row=0,
        )
        self.cog = cog

    async def callback(self, interaction: discord.Interaction) -> None:
        member = interaction.user if isinstance(interaction.user, discord.Member) else None
        if member is None:
            return await interaction.response.send_message("Could not verify permissions.", ephemeral=True)

        selected = self.values[0]

        if selected == "result":
            if not _is_color_team(member):
                return await interaction.response.send_message(
                    "Only the Color Team or staff can post results.", ephemeral=True
                )
            await interaction.response.send_modal(ColorResultModal())

        elif selected == "note":
            if not _is_color_team(member):
                return await interaction.response.send_message(
                    "Only the Color Team or staff can add notes.", ephemeral=True
                )
            await interaction.response.send_modal(ColorTeamNoteModal())

        elif selected == "close":
            if not _is_color_team(member):
                return await interaction.response.send_message(
                    "Only the Color Team or staff can close tickets.", ephemeral=True
                )
            channel = interaction.channel
            guild   = interaction.guild
            if not isinstance(channel, discord.TextChannel) or guild is None:
                return await interaction.response.send_message(
                    "This only works inside a ticket channel.", ephemeral=True
                )
            # Lock out the requester
            if channel.topic and "color_request_user_id:" in channel.topic:
                try:
                    uid = int(channel.topic.split("color_request_user_id:")[1].split("|")[0].strip())
                    requester_member = guild.get_member(uid)
                    if requester_member:
                        await channel.set_permissions(requester_member, send_messages=False)
                except Exception:
                    pass

            await channel.edit(topic=(channel.topic or "") + " | status:closed")

            close_embed = discord.Embed(
                title="🔒 Request Closed",
                description=(
                    "This color request has been marked as **resolved** by the Color Team.\n\n"
                    "If you're happy with the result, no action is needed — this ticket will be archived shortly.\n"
                    "If you need further help, please contact the Color Team directly."
                ),
                color=SUCCESS_COLOR,
                timestamp=datetime.now(timezone.utc),
            )
            close_embed.set_thumbnail(url=DIFF_LOGO_URL)
            close_embed.set_footer(text=f"Closed by {interaction.user.display_name} • DIFF Color Lab")
            await interaction.response.send_message(embed=close_embed)

        elif selected == "archive":
            if not _is_color_team(member):
                return await interaction.response.send_message(
                    "Only the Color Team or staff can archive tickets.", ephemeral=True
                )
            channel = interaction.channel
            guild   = interaction.guild
            if not isinstance(channel, discord.TextChannel) or guild is None:
                return await interaction.response.send_message(
                    "This only works inside a ticket channel.", ephemeral=True
                )

            archive_cat = guild.get_channel(ARCHIVE_CATEGORY_ID)
            if not isinstance(archive_cat, discord.CategoryChannel):
                return await interaction.response.send_message(
                    "Archive category not configured. Contact staff.", ephemeral=True
                )

            await interaction.response.defer(ephemeral=True)

            transcript_html = await _build_transcript(channel)
            _ensure_dirs()
            transcript_path = os.path.join(TRANSCRIPTS_DIR, f"{channel.name}_{_ts()}.html")
            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write(transcript_html)

            if channel.topic and "color_request_user_id:" in channel.topic:
                try:
                    uid = channel.topic.split("color_request_user_id:")[1].split("|")[0].strip()
                    tickets = _load_tickets()
                    if str(tickets.get(str(uid))) == str(channel.id):
                        tickets.pop(str(uid), None)
                        _save_tickets(tickets)
                except Exception:
                    pass

            color_team_role = guild.get_role(COLOR_TEAM_ROLE_ID)
            new_overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                guild.me: discord.PermissionOverwrite(
                    view_channel=True, send_messages=True,
                    manage_channels=True, manage_messages=True, read_message_history=True,
                ),
            }
            if color_team_role:
                new_overwrites[color_team_role] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=False,
                    read_message_history=True, manage_messages=True, manage_channels=True,
                )

            try:
                await channel.edit(
                    name=f"archived-{channel.name}"[:100],
                    category=archive_cat,
                    topic=(channel.topic or "") + " | status:archived",
                    overwrites=new_overwrites,
                    reason=f"Archived by {interaction.user}",
                )
            except Exception as e:
                return await interaction.followup.send(f"Failed to archive: {e}", ephemeral=True)

            archive_embed = discord.Embed(
                title="📦 Ticket Archived",
                description=(
                    "This ticket has been **archived**.\n"
                    "A full transcript has been saved to staff logs for records."
                ),
                color=WARNING_COLOR,
                timestamp=datetime.now(timezone.utc),
            )
            archive_embed.set_thumbnail(url=DIFF_LOGO_URL)
            archive_embed.set_footer(text=f"Archived by {interaction.user.display_name} • DIFF Color Lab")
            await channel.send(embed=archive_embed)

            transcript_file = discord.File(transcript_path, filename=os.path.basename(transcript_path))
            await self.cog.log_action(
                guild,
                f"📦 Archived color ticket `#{channel.name}` by {interaction.user.mention}",
                file=transcript_file,
            )
            await interaction.followup.send(
                "Ticket archived and transcript saved to staff logs.", ephemeral=True
            )


class ColorTicketControlsView(discord.ui.View):
    def __init__(self, cog: "ColorLabCog"):
        super().__init__(timeout=None)
        self.cog = cog
        self.add_item(_TicketActionsSelect(cog))

    @discord.ui.button(
        label="Post Result", emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="diff_color_lab_ticket_post_result_v2", row=1,
    )
    async def post_result(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user if isinstance(interaction.user, discord.Member) else None
        if not member or not _is_color_team(member):
            return await interaction.response.send_message(
                "Only the Color Team or staff can post results.", ephemeral=True
            )
        await interaction.response.send_modal(ColorResultModal())

    @discord.ui.button(
        label="Archive Ticket", emoji="📦",
        style=discord.ButtonStyle.danger,
        custom_id="diff_color_lab_ticket_archive_v2", row=1,
    )
    async def archive_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user if isinstance(interaction.user, discord.Member) else None
        if not member or not _is_color_team(member):
            return await interaction.response.send_message(
                "Only the Color Team or staff can archive tickets.", ephemeral=True
            )
        # Trigger the archive flow from the select
        fake_select = _TicketActionsSelect(self.cog)
        fake_select.values = ["archive"]
        fake_select.view = self
        await fake_select.callback(interaction)


# =========================================================
# PANEL DROPDOWN  (row 0)
# =========================================================
class _ColorLabPanelSelect(discord.ui.Select):
    def __init__(self, cog: "ColorLabCog"):
        super().__init__(
            custom_id="diff_color_lab_panel_select_v2",
            placeholder="🎨 What do you need help with?",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Open a Color Request",
                    value="open",
                    emoji="🎫",
                    description="Start a private ticket with the Color Team.",
                ),
                discord.SelectOption(
                    label="How It Works",
                    value="howto",
                    emoji="❓",
                    description="Learn how the Color Lab process works.",
                ),
                discord.SelectOption(
                    label="What to Include",
                    value="include",
                    emoji="📋",
                    description="See what info helps the Color Team match your color.",
                ),
                discord.SelectOption(
                    label="Color Lookup Tips",
                    value="tips",
                    emoji="🔍",
                    description="How to find hex codes and finish types in GTA.",
                ),
            ],
            row=0,
        )
        self.cog = cog

    async def callback(self, interaction: discord.Interaction) -> None:
        selected = self.values[0]

        if selected == "open":
            await interaction.response.send_modal(ColorTicketRequestModal(self.cog))

        elif selected == "howto":
            embed = discord.Embed(
                title="❓ How the Color Lab Works",
                description="Here's the full process from start to finish:",
                color=EMBED_COLOR,
            )
            embed.add_field(
                name="Step 1 — Open a Request",
                value="Click **Open a Color Request** and fill out the short form with your car info and reference.",
                inline=False,
            )
            embed.add_field(
                name="Step 2 — Private Ticket Created",
                value="A private channel is created that only you, the Color Team, and admins can see.",
                inline=False,
            )
            embed.add_field(
                name="Step 3 — Color Matching",
                value="The Color Team gets to work matching your color in GTA Online using the info you provided.",
                inline=False,
            )
            embed.add_field(
                name="Step 4 — Official Result Posted",
                value="Once matched, the team posts an official result embed with the base color, pearl, and finish.",
                inline=False,
            )
            embed.add_field(
                name="Step 5 — Ticket Archived",
                value="Your ticket is archived and a transcript is saved. One open ticket at a time per user.",
                inline=False,
            )
            embed.set_thumbnail(url=DIFF_LOGO_URL)
            embed.set_footer(text="DIFF Color Lab • Info")
            await interaction.response.send_message(embed=embed, ephemeral=True)

        elif selected == "include":
            embed = discord.Embed(
                title="📋 What to Include in Your Request",
                description="The more info you provide, the quicker and more accurate the match will be.",
                color=EMBED_COLOR,
            )
            embed.add_field(
                name="📎 Reference Image",
                value="A clear screenshot or photo of the car color you want to match. Direct image links work best.",
                inline=False,
            )
            embed.add_field(
                name="🎨 Hex Code",
                value="If you know it, paste the exact hex code (e.g. `#A9E3D6`). If not, type **Unknown**.",
                inline=False,
            )
            embed.add_field(
                name="🚗 Car Name",
                value="The GTA vehicle name (e.g. Vorschlaghammer, Zentorno). This helps narrow down finish results.",
                inline=False,
            )
            embed.add_field(
                name="✨ Finish Type",
                value="Metallic / Pearlescent / Matte / Worn — or **Unknown** if you're not sure.",
                inline=False,
            )
            embed.add_field(
                name="📝 Extra Notes",
                value="Lighting conditions, angle the photo was taken, or any other context that might help.",
                inline=False,
            )
            embed.set_thumbnail(url=DIFF_LOGO_URL)
            embed.set_footer(text="DIFF Color Lab • Info")
            await interaction.response.send_message(embed=embed, ephemeral=True)

        elif selected == "tips":
            embed = discord.Embed(
                title="🔍 Color Lookup Tips for GTA",
                description="Not sure what color you're looking for? Here are some ways to find it.",
                color=EMBED_COLOR,
            )
            embed.add_field(
                name="📱 GTA Color Picker Sites",
                value="Use sites like **GTABaseColors.com** or search **GTA Online color codes** to browse palettes.",
                inline=False,
            )
            embed.add_field(
                name="🖥️ Screenshot + Eyedropper",
                value="Take a screenshot and use a tool like **Adobe Color**, **imagecolorpicker.com**, or even Paint to grab the hex.",
                inline=False,
            )
            embed.add_field(
                name="✨ Finding the Finish",
                value=(
                    "**Metallic** — shiny, shifts slightly in light\n"
                    "**Pearlescent** — has a two-tone shimmer effect\n"
                    "**Matte** — flat, no shine at all\n"
                    "**Worn** — faded, aged look"
                ),
                inline=False,
            )
            embed.add_field(
                name="💡 Tip",
                value="If you saw the car at a meet, mention where — the Color Team may already know that build.",
                inline=False,
            )
            embed.set_thumbnail(url=DIFF_LOGO_URL)
            embed.set_footer(text="DIFF Color Lab • Info")
            await interaction.response.send_message(embed=embed, ephemeral=True)


# =========================================================
# PANEL VIEW  (persistent)
# =========================================================
class ColorLabPanelView(discord.ui.View):
    def __init__(self, cog: "ColorLabCog"):
        super().__init__(timeout=None)
        self.cog = cog
        self.add_item(_ColorLabPanelSelect(cog))

    @discord.ui.button(
        label="Open Color Request", emoji="🎫",
        style=discord.ButtonStyle.primary,
        custom_id="diff_color_lab_open_private_request_v2", row=1,
    )
    async def open_private_request(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ColorTicketRequestModal(self.cog))


# =========================================================
# COG
# =========================================================
class ColorLabCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        _ensure_dirs()
        self.bot          = bot
        self._panel_view  = ColorLabPanelView(self)
        self._ticket_view = ColorTicketControlsView(self)
        bot.add_view(self._panel_view)
        bot.add_view(self._ticket_view)

    # ------------------------------------------------------------------
    def _build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🎨 DIFF Color Lab",
            description=(
                "Need help recreating a custom GTA color?\n"
                "The **Color Team** will match it for you in a **private ticket**.\n\n"
                "Use the dropdown below to get started or learn more.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=EMBED_COLOR,
        )
        embed.add_field(
            name="🎫 Private Tickets",
            value="One-on-one help — only you, the Color Team, and admins can see your ticket.",
            inline=False,
        )
        embed.add_field(
            name="✅ Official Results",
            value="Every matched color is posted as a formal result embed inside your ticket.",
            inline=False,
        )
        embed.add_field(
            name="📦 Archived for Records",
            value="Completed tickets are archived with a full transcript saved to staff logs.",
            inline=False,
        )
        embed.set_thumbnail(url=DIFF_LOGO_URL)
        embed.set_footer(text=f"DIFF Color Lab • Private Request System • {PANEL_TAG}")
        return embed

    # ------------------------------------------------------------------
    async def _get_channel(self) -> Optional[discord.TextChannel]:
        ch = self.bot.get_channel(TARGET_CHANNEL_ID)
        if ch is None:
            try:
                ch = await self.bot.fetch_channel(TARGET_CHANNEL_ID)
            except Exception:
                return None
        return ch if isinstance(ch, discord.TextChannel) else None

    # ------------------------------------------------------------------
    async def log_action(
        self,
        guild: Optional[discord.Guild],
        message: str,
        file: Optional[discord.File] = None,
    ) -> None:
        if guild is None:
            return
        ch = guild.get_channel(LOG_CHANNEL_ID)
        if isinstance(ch, discord.TextChannel):
            try:
                if file:
                    await ch.send(message, file=file)
                else:
                    await ch.send(message)
            except Exception:
                pass

    # ------------------------------------------------------------------
    async def ensure_panel(self) -> None:
        channel = await self._get_channel()
        if channel is None:
            print(f"[ColorLab] Channel not found: {TARGET_CHANNEL_ID}")
            return

        embed    = self._build_embed()
        saved_id = _get_msg_id()

        if saved_id:
            try:
                msg = await channel.fetch_message(saved_id)
                await msg.edit(embed=embed, view=self._panel_view)
                print("[ColorLab] Panel refreshed.")
                return
            except discord.NotFound:
                pass
            except Exception as e:
                print(f"[ColorLab] Edit failed: {e}")

        try:
            async for msg in channel.history(limit=50):
                if (
                    msg.author == self.bot.user
                    and msg.embeds
                    and "DIFF_COLOR_LAB_PANEL" in (msg.embeds[0].footer.text or "")
                ):
                    try:
                        await msg.delete()
                    except Exception:
                        pass
        except Exception:
            pass

        try:
            new_msg = await channel.send(embed=embed, view=self._panel_view)
            _set_msg_id(new_msg.id)
            print(f"[ColorLab] Panel posted: {new_msg.id}")
        except Exception as e:
            print(f"[ColorLab] Failed to post panel: {e}")

    # ------------------------------------------------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        await self.ensure_panel()
        print("[ColorLab] Cog ready.")

    @commands.command(name="refresh_color_lab")
    @commands.has_permissions(manage_channels=True)
    async def cmd_refresh(self, ctx: commands.Context):
        await self.ensure_panel()
        await ctx.send("Color Lab panel refreshed.", delete_after=8)


# =========================================================
# SETUP
# =========================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(ColorLabCog(bot))
