from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

import discord
from discord.ext import commands

# =========================================================
# CONFIG
# =========================================================

GUILD_ID = 850386896509337710

DIFF_LOGO_URL = "https://media.discordapp.net/attachments/1107375326625005719/1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm=2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a&=&format=webp&quality=lossless&width=1376&height=917"

PARTNER_REQUEST_CHANNEL_ID = 1485892421593337926
PARTNER_REVIEW_CHANNEL_ID = 1057016810261712938

STAFF_REVIEW_ROLE_ID: Optional[int] = None
PARTNER_LOG_CHANNEL_ID: Optional[int] = None

AUTO_ADD_TO_PARTNERSHIP_PANEL = True

DATA_DIR = Path("diff_data")
DATA_DIR.mkdir(exist_ok=True)

REQUESTS_FILE = DATA_DIR / "partner_requests.json"
APPROVED_FILE = DATA_DIR / "approved_partners.json"
PANEL_STATE_FILE = DATA_DIR / "partner_request_panel_state.json"

PANEL_TITLE = "🤝 DIFF Partner Request Center"
PANEL_DESCRIPTION = (
    "Interested in partnering with **Different Meets**?\n\n"
    "Use the button below to submit your community for review.\n"
    "All requests are reviewed by staff before being accepted."
)
FOOTER_TEXT = "Different Meets • Partnership Request System"
LOGO_URL = ""
BANNER_URL = ""

REQUEST_PANEL_MARKER = "diff_partner_request_open"


# =========================================================
# HELPERS
# =========================================================

def sanitize_url(url: str) -> str:
    url = url.strip()
    if url and not re.match(r"^https?://", url, flags=re.I):
        url = "https://" + url
    return url


def load_json(path: Path, default):
    if not path.exists():
        save_json(path, default)
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path: Path, data):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def ensure_files():
    load_json(REQUESTS_FILE, {"requests": []})
    load_json(APPROVED_FILE, {"partners": []})
    load_json(PANEL_STATE_FILE, {"channel_id": PARTNER_REQUEST_CHANNEL_ID, "message_id": None})


def next_request_id(data: dict) -> int:
    items = data.get("requests", [])
    if not items:
        return 1
    return max(item.get("request_id", 0) for item in items) + 1


def is_request_panel_message(msg: discord.Message) -> bool:
    for row in msg.components:
        for c in row.children:
            if getattr(c, "custom_id", "") == REQUEST_PANEL_MARKER:
                return True
    return False


# =========================================================
# MODAL
# =========================================================

class PartnerRequestModal(discord.ui.Modal, title="Submit a Partnership Request"):
    server_name = discord.ui.TextInput(
        label="Server / Community Name",
        placeholder="Enter your server name",
        max_length=100,
        required=True,
    )
    invite_link = discord.ui.TextInput(
        label="Discord Invite Link",
        placeholder="https://discord.gg/yourserver",
        max_length=200,
        required=True,
    )
    short_desc = discord.ui.TextInput(
        label="Short Description",
        placeholder="Short summary for your server",
        max_length=100,
        required=True,
    )
    platforms = discord.ui.TextInput(
        label="Platforms",
        placeholder="PS5 / Xbox / PC / All Platforms / etc",
        max_length=100,
        required=False,
    )
    full_description = discord.ui.TextInput(
        label="Full Description / Notes",
        style=discord.TextStyle.paragraph,
        placeholder="Tell us about your community, events, and style.",
        max_length=1200,
        required=True,
    )

    def __init__(self, cog: "PartnerRequestSystem"):
        super().__init__(timeout=300)
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        ensure_files()
        requests_data = load_json(REQUESTS_FILE, {"requests": []})
        request_id = next_request_id(requests_data)

        record = {
            "request_id": request_id,
            "submitted_by_id": interaction.user.id,
            "submitted_by_name": str(interaction.user),
            "server_name": str(self.server_name).strip(),
            "invite": sanitize_url(str(self.invite_link)),
            "short_desc": str(self.short_desc).strip(),
            "platforms": str(self.platforms).strip(),
            "description": str(self.full_description).strip(),
            "banner": "",
            "status": "pending",
        }

        requests_data["requests"].append(record)
        save_json(REQUESTS_FILE, requests_data)

        review_channel = interaction.client.get_channel(PARTNER_REVIEW_CHANNEL_ID)
        if review_channel is None:
            try:
                review_channel = await interaction.client.fetch_channel(PARTNER_REVIEW_CHANNEL_ID)
            except Exception:
                await interaction.response.send_message(
                    "Your request was saved, but the review channel could not be reached. Staff will be notified.",
                    ephemeral=True,
                )
                return

        embed = discord.Embed(
            title=f"🤝 Partner Request #{request_id}",
            description=(
                f"**Submitted By:** {interaction.user.mention}\n"
                f"**Server Name:** {record['server_name']}\n"
                f"**Platforms:** {record['platforms'] or 'Not provided'}\n"
                f"**Invite:** {record['invite']}\n\n"
                f"**Short Description:**\n{record['short_desc']}\n\n"
                f"**Full Description:**\n{record['description']}"
            ),
            color=discord.Color.orange(),
        )
        embed.set_footer(text=f"Request ID: {request_id} • Pending Review")
        if LOGO_URL:
            embed.set_thumbnail(url=LOGO_URL)

        view = PartnerReviewView(self.cog, request_id)
        content = f"<@&{STAFF_REVIEW_ROLE_ID}>" if STAFF_REVIEW_ROLE_ID else None
        msg = await review_channel.send(content=content, embed=embed, view=view)

        for item in requests_data["requests"]:
            if item["request_id"] == request_id:
                item["review_message_id"] = msg.id
                item["review_channel_id"] = review_channel.id
                break
        save_json(REQUESTS_FILE, requests_data)

        await interaction.response.send_message(
            "✅ Your partnership request has been submitted for staff review. You'll be notified of the outcome.",
            ephemeral=True,
        )


# =========================================================
# VIEWS
# =========================================================

class OpenPartnerRequestButton(discord.ui.View):
    def __init__(self, cog: "PartnerRequestSystem"):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="Submit Partnership Request",
        style=discord.ButtonStyle.blurple,
        emoji="🤝",
        custom_id="diff_partner_request_open",
    )
    async def submit_request(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PartnerRequestModal(self.cog))


class PartnerReviewView(discord.ui.View):
    def __init__(self, cog: "PartnerRequestSystem", request_id: int):
        super().__init__(timeout=None)
        self.cog = cog
        self.request_id = request_id

    @discord.ui.button(
        label="Approve",
        style=discord.ButtonStyle.green,
        emoji="✅",
        custom_id="diff_partner_request_approve",
    )
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("You need Manage Server to do this.", ephemeral=True)

        requests_data = load_json(REQUESTS_FILE, {"requests": []})
        approved_data = load_json(APPROVED_FILE, {"partners": []})

        req = next((r for r in requests_data["requests"] if r["request_id"] == self.request_id), None)
        if not req:
            return await interaction.response.send_message("Request not found.", ephemeral=True)
        if req["status"] != "pending":
            return await interaction.response.send_message("This request has already been reviewed.", ephemeral=True)

        req["status"] = "approved"
        req["reviewed_by_id"] = interaction.user.id
        req["reviewed_by_name"] = str(interaction.user)

        approved_partner = {
            "name": req["server_name"],
            "short_desc": req["short_desc"],
            "description": req["description"],
            "invite": req["invite"],
            "platforms": req.get("platforms", ""),
            "banner": req.get("banner", ""),
            "approved_by": str(interaction.user),
            "submitted_by": req["submitted_by_name"],
        }
        approved_data["partners"].append(approved_partner)
        save_json(REQUESTS_FILE, requests_data)
        save_json(APPROVED_FILE, approved_data)

        embed = interaction.message.embeds[0] if interaction.message.embeds else discord.Embed(title="Partner Request")
        embed.color = discord.Color.green()
        embed.add_field(name="Review Outcome", value="✅ Approved", inline=False)
        embed.set_footer(text=f"Request ID: {self.request_id} • Approved by {interaction.user}")

        for child in self.children:
            child.disabled = True
        await interaction.message.edit(embed=embed, view=self)

        try:
            member = interaction.guild.get_member(req["submitted_by_id"])
            if member:
                pr_em = discord.Embed(
                    title="Partner Request Approved",
                    description=f"Your partner request for **{req['server_name']}** has been **approved** in **{interaction.guild.name}**!",
                    color=discord.Color.green(),
                )
                pr_em.set_author(name="Different Meets", icon_url=DIFF_LOGO_URL)
                pr_em.set_thumbnail(url=DIFF_LOGO_URL)
                await member.send(embed=pr_em)
        except Exception:
            pass

        if PARTNER_LOG_CHANNEL_ID:
            log_ch = interaction.client.get_channel(PARTNER_LOG_CHANNEL_ID)
            if isinstance(log_ch, discord.TextChannel):
                try:
                    await log_ch.send(f"✅ Partner request approved: **{req['server_name']}** by {interaction.user.mention}")
                except Exception:
                    pass

        await interaction.response.send_message("Partner request approved.", ephemeral=True)

    @discord.ui.button(
        label="Deny",
        style=discord.ButtonStyle.red,
        emoji="⛔",
        custom_id="diff_partner_request_deny",
    )
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("You need Manage Server to do this.", ephemeral=True)

        requests_data = load_json(REQUESTS_FILE, {"requests": []})
        req = next((r for r in requests_data["requests"] if r["request_id"] == self.request_id), None)
        if not req:
            return await interaction.response.send_message("Request not found.", ephemeral=True)
        if req["status"] != "pending":
            return await interaction.response.send_message("This request has already been reviewed.", ephemeral=True)

        req["status"] = "denied"
        req["reviewed_by_id"] = interaction.user.id
        req["reviewed_by_name"] = str(interaction.user)
        save_json(REQUESTS_FILE, requests_data)

        embed = interaction.message.embeds[0] if interaction.message.embeds else discord.Embed(title="Partner Request")
        embed.color = discord.Color.red()
        embed.add_field(name="Review Outcome", value="⛔ Denied", inline=False)
        embed.set_footer(text=f"Request ID: {self.request_id} • Denied by {interaction.user}")

        for child in self.children:
            child.disabled = True
        await interaction.message.edit(embed=embed, view=self)

        try:
            member = interaction.guild.get_member(req["submitted_by_id"])
            if member:
                pr_em = discord.Embed(
                    title="Partner Request Denied",
                    description=f"Your partner request for **{req['server_name']}** was not approved in **{interaction.guild.name}**.",
                    color=discord.Color.red(),
                )
                pr_em.set_author(name="Different Meets", icon_url=DIFF_LOGO_URL)
                pr_em.set_thumbnail(url=DIFF_LOGO_URL)
                await member.send(embed=pr_em)
        except Exception:
            pass

        if PARTNER_LOG_CHANNEL_ID:
            log_ch = interaction.client.get_channel(PARTNER_LOG_CHANNEL_ID)
            if isinstance(log_ch, discord.TextChannel):
                try:
                    await log_ch.send(f"⛔ Partner request denied: **{req['server_name']}** by {interaction.user.mention}")
                except Exception:
                    pass

        await interaction.response.send_message("Partner request denied.", ephemeral=True)


# =========================================================
# COG
# =========================================================

class PartnerRequestSystem(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        ensure_files()
        self.bot.add_view(OpenPartnerRequestButton(self))
        requests_data = load_json(REQUESTS_FILE, {"requests": []})
        for req in requests_data.get("requests", []):
            if req.get("status") == "pending":
                self.bot.add_view(PartnerReviewView(self, req["request_id"]))

    @commands.Cog.listener()
    async def on_ready(self):
        print("[PartnerRequestSystem] Cog ready.")

    def build_panel_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=PANEL_TITLE,
            description=PANEL_DESCRIPTION,
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="Review Process",
            value="All submissions are checked by staff before they are approved.",
            inline=False,
        )
        embed.add_field(
            name="What Helps",
            value="Clear descriptions, valid invite links, and professional server details.",
            inline=False,
        )
        embed.add_field(
            name="📋 Staff Commands",
            value=(
                "`!postpartnerrequests` — Post / refresh this panel\n"
                "`!partnerrequestspending` — View all pending partner requests\n"
                "`!partnerrequeststlist` — View the full partner requests list"
            ),
            inline=False,
        )
        embed.set_footer(text=FOOTER_TEXT)
        if LOGO_URL:
            embed.set_thumbnail(url=LOGO_URL)
        if BANNER_URL:
            embed.set_image(url=BANNER_URL)
        return embed

    async def post_or_refresh_panel(self) -> tuple[bool, str]:
        state = load_json(PANEL_STATE_FILE, {"channel_id": PARTNER_REQUEST_CHANNEL_ID, "message_id": None})
        channel_id = state.get("channel_id", PARTNER_REQUEST_CHANNEL_ID)
        message_id = state.get("message_id")

        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception as e:
                return False, f"Could not access channel: {e}"

        embed = self.build_panel_embed()
        view = OpenPartnerRequestButton(self)

        if message_id:
            try:
                msg = await channel.fetch_message(message_id)
                await msg.edit(embed=embed, view=view, content=None)
                return True, "Partner request panel refreshed."
            except Exception:
                pass

        try:
            msg = await channel.send(embed=embed, view=view)
            state["message_id"] = msg.id
            state["channel_id"] = channel.id
            save_json(PANEL_STATE_FILE, state)
            return True, "Partner request panel posted."
        except Exception as e:
            return False, f"Failed to post panel: {e}"

    @commands.command(name="postpartnerrequests")
    @commands.has_permissions(manage_guild=True)
    async def postpartnerrequests(self, ctx: commands.Context):
        """Post or refresh the partner request panel."""
        ok, msg = await self.post_or_refresh_panel()
        await ctx.send(f"{'✅' if ok else '❌'} {msg}", delete_after=8)
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="partnerrequestspending")
    @commands.has_permissions(manage_guild=True)
    async def partnerrequestspending(self, ctx: commands.Context):
        """View partner request stats."""
        data = load_json(REQUESTS_FILE, {"requests": []})
        pending  = [r for r in data["requests"] if r.get("status") == "pending"]
        approved = [r for r in data["requests"] if r.get("status") == "approved"]
        denied   = [r for r in data["requests"] if r.get("status") == "denied"]
        embed = discord.Embed(
            title="Partner Request Stats",
            description=(
                f"**Pending:** {len(pending)}\n"
                f"**Approved:** {len(approved)}\n"
                f"**Denied:** {len(denied)}"
            ),
            color=discord.Color.gold(),
        )
        await ctx.send(embed=embed, delete_after=30)

    @commands.command(name="partnerrequeststlist")
    @commands.has_permissions(manage_guild=True)
    async def partnerrequestslist(self, ctx: commands.Context):
        """List approved partners."""
        data = load_json(APPROVED_FILE, {"partners": []})
        partners = data.get("partners", [])
        if not partners:
            return await ctx.send("No approved partners saved yet.", delete_after=10)
        lines = [f"• **{p['name']}** — {p.get('platforms') or 'No platforms'}" for p in partners[:25]]
        embed = discord.Embed(
            title="Approved Partners",
            description="\n".join(lines),
            color=discord.Color.green(),
        )
        embed.set_footer(text=f"Total approved: {len(partners)}")
        await ctx.send(embed=embed, delete_after=30)


async def setup(bot: commands.Bot):
    await bot.add_cog(PartnerRequestSystem(bot))
