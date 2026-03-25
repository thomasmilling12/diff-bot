from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

import discord
from discord.ext import commands, tasks

GUILD_ID                  = 850386896509337710
MARKETPLACE_CHANNEL_ID    = 1182386801235742801
MARKETPLACE_LOG_CHANNEL_ID = 1485265848099799163  # Staff Logs

LEADER_ROLE_ID    = 850391095845584937
CO_LEADER_ROLE_ID = 850391378559238235
MANAGER_ROLE_ID   = 990011447193006101

AUTO_DELETE_AFTER_DAYS  = 7
LISTING_COOLDOWN_SECONDS = 300

COLOR_PRIMARY = 0x1F6FEB
COLOR_SUCCESS = 0x2ECC71
COLOR_WARNING = 0xF39C12
COLOR_MUTED   = 0x95A5A6

DATA_DIR         = "diff_data"
MARKETPLACE_FILE = os.path.join(DATA_DIR, "marketplace_listings.json")
PANEL_TAG        = "DIFF_MARKETPLACE_PANEL_V1"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def load_json(path: str, default):
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=4)
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path: str, data) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def has_staff_access(member: discord.Member) -> bool:
    if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
        return True
    role_ids = {role.id for role in member.roles}
    return bool(role_ids & {LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID})


def _parse_listing_id(message: discord.Message) -> Optional[str]:
    """Extract listing ID from embed title — e.g. '🛒 Selling • MKT-0001'."""
    if not message or not message.embeds:
        return None
    title = message.embeds[0].title or ""
    if "•" in title:
        return title.split("•")[-1].strip()
    return None


# ---------------------------------------------------------------------------
# Modals
# ---------------------------------------------------------------------------

class ListingModal(discord.ui.Modal):
    def __init__(self, cog: "MarketplaceSystem", listing_type: str):
        super().__init__(title=f"{listing_type} Listing")
        self.cog = cog
        self.listing_type = listing_type

        self.item = discord.ui.TextInput(
            label="Item",
            placeholder="Car name / mod / service",
            max_length=100,
            required=True,
        )
        self.details = discord.ui.TextInput(
            label="Details",
            placeholder="Specs, upgrades, condition, color, extras, etc.",
            style=discord.TextStyle.paragraph,
            max_length=1000,
            required=True,
        )
        self.price = discord.ui.TextInput(
            label="Price",
            placeholder="Price / trade value / N/A",
            max_length=100,
            required=True,
        )
        self.contact = discord.ui.TextInput(
            label="Contact",
            placeholder="DM me / tag / other contact note",
            max_length=100,
            required=True,
        )
        self.tags = discord.ui.TextInput(
            label="Tags",
            placeholder="Bennys, Clean, Stock colors, Yantons, etc.",
            max_length=200,
            required=False,
        )

        self.add_item(self.item)
        self.add_item(self.details)
        self.add_item(self.price)
        self.add_item(self.contact)
        self.add_item(self.tags)

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.create_listing(
            interaction=interaction,
            listing_type=self.listing_type,
            item=str(self.item).strip(),
            details=str(self.details).strip(),
            price=str(self.price).strip(),
            contact=str(self.contact).strip(),
            tags=str(self.tags).strip() or "None",
        )


class RemoveListingModal(discord.ui.Modal, title="Remove Marketplace Listing"):
    listing_id = discord.ui.TextInput(
        label="Listing ID",
        placeholder="Example: MKT-0001",
        max_length=20,
        required=True,
    )
    reason = discord.ui.TextInput(
        label="Reason",
        placeholder="Why should this listing be removed?",
        style=discord.TextStyle.paragraph,
        max_length=500,
        required=True,
    )

    def __init__(self, cog: "MarketplaceSystem"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.remove_listing(
            interaction=interaction,
            listing_id=str(self.listing_id).strip().upper(),
            reason=str(self.reason).strip(),
        )


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

class ListingActionView(discord.ui.View):
    """Persistent view on each listing embed.
    Listing ID is recovered from the embed title at interaction time.
    """

    def __init__(self, cog: "MarketplaceSystem"):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Mark Sold", style=discord.ButtonStyle.success, emoji="✅", custom_id="diff_marketplace_mark_sold")
    async def mark_sold(self, interaction: discord.Interaction, button: discord.ui.Button):
        listing_id = _parse_listing_id(interaction.message)
        if not listing_id:
            await interaction.response.send_message("Could not determine listing ID.", ephemeral=True)
            return
        await self.cog.mark_listing_status(interaction, listing_id, "Sold")

    @discord.ui.button(label="Mark Closed", style=discord.ButtonStyle.secondary, emoji="🔒", custom_id="diff_marketplace_mark_closed")
    async def mark_closed(self, interaction: discord.Interaction, button: discord.ui.Button):
        listing_id = _parse_listing_id(interaction.message)
        if not listing_id:
            await interaction.response.send_message("Could not determine listing ID.", ephemeral=True)
            return
        await self.cog.mark_listing_status(interaction, listing_id, "Closed")

    @discord.ui.button(label="Remove", style=discord.ButtonStyle.danger, emoji="🗑️", custom_id="diff_marketplace_remove")
    async def remove_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        listing_id = _parse_listing_id(interaction.message)
        if not listing_id:
            await interaction.response.send_message("Could not determine listing ID.", ephemeral=True)
            return
        await self.cog.remove_listing(
            interaction=interaction,
            listing_id=listing_id,
            reason="Removed via listing action button.",
        )


class MarketplacePanelView(discord.ui.View):
    def __init__(self, cog: "MarketplaceSystem"):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Post Listing", style=discord.ButtonStyle.primary, emoji="🛒", custom_id="diff_market_post_listing")
    async def post_listing(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ListingModal(self.cog, "Selling"))

    @discord.ui.button(label="Looking For", style=discord.ButtonStyle.secondary, emoji="🔍", custom_id="diff_market_looking_for")
    async def looking_for(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ListingModal(self.cog, "Buying"))

    @discord.ui.button(label="Remove Listing", style=discord.ButtonStyle.danger, emoji="❌", custom_id="diff_market_remove_listing")
    async def remove_listing(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RemoveListingModal(self.cog))


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------

class MarketplaceSystem(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(MarketplacePanelView(self))
        self.bot.add_view(ListingActionView(self))
        self.cleanup_task.start()

    def cog_unload(self):
        self.cleanup_task.cancel()

    @tasks.loop(hours=6)
    async def cleanup_task(self):
        guild = self.bot.get_guild(GUILD_ID)
        if guild is None:
            return
        await self.auto_cleanup_expired_listings(guild)

    @cleanup_task.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_ready(self):
        print("[MarketplaceSystem] Cog ready.")
        guild = self.bot.get_guild(GUILD_ID)
        if guild is None:
            return
        channel = guild.get_channel(MARKETPLACE_CHANNEL_ID)
        if isinstance(channel, discord.TextChannel):
            await self._post_or_refresh_panel(channel)

    # ------------------------------------------------------------------
    # Data helpers
    # ------------------------------------------------------------------

    def get_data(self) -> Dict[str, Any]:
        return load_json(MARKETPLACE_FILE, {"counter": 0, "entries": {}, "cooldowns": {}})

    def save_data(self, data: Dict[str, Any]) -> None:
        save_json(MARKETPLACE_FILE, data)

    def next_listing_id(self) -> str:
        data = self.get_data()
        data["counter"] += 1
        self.save_data(data)
        return f"MKT-{data['counter']:04d}"

    # ------------------------------------------------------------------
    # Embed builders
    # ------------------------------------------------------------------

    def build_panel_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="DIFF Community Marketplace",
            description=(
                "Buy, sell, and trade within the DIFF community.\n\n"
                "**Use the buttons below to:**\n"
                "• Post a clean listing\n"
                "• Post what you are looking for\n"
                "• Remove your old listing"
            ),
            color=COLOR_PRIMARY,
        )
        embed.add_field(
            name="Marketplace Rules",
            value=(
                "• Be specific and honest\n"
                "• No spam or repeated posts\n"
                "• Keep it related to DIFF / GTA marketplace use\n"
                "• Inactive listings are removed automatically after 7 days"
            ),
            inline=False,
        )
        embed.add_field(
            name="Required Format",
            value="Item • Details • Price • Contact • Tags",
            inline=False,
        )
        embed.set_footer(text=PANEL_TAG)
        return embed

    def build_listing_embed(self, entry: Dict[str, Any], color: int = COLOR_PRIMARY) -> discord.Embed:
        embed = discord.Embed(
            title=f"🛒 {entry['listing_type']} • {entry['listing_id']}",
            color=color,
            timestamp=utcnow(),
        )
        embed.add_field(name="Posted By", value=entry["author_mention"], inline=True)
        embed.add_field(name="Status",    value=entry["status"],         inline=True)
        embed.add_field(name="Item",      value=entry["item"],           inline=True)
        embed.add_field(name="Price",     value=entry["price"],          inline=True)
        embed.add_field(name="Contact",   value=entry["contact"],        inline=True)
        embed.add_field(name="Tags",      value=entry["tags"],           inline=True)
        embed.add_field(name="Details",   value=entry["details"][:1024], inline=False)
        embed.set_footer(text="Different Meets • Marketplace Listing")
        return embed

    # ------------------------------------------------------------------
    # Panel auto-post
    # ------------------------------------------------------------------

    async def _post_or_refresh_panel(self, channel: discord.TextChannel):
        embed = self.build_panel_embed()
        view  = MarketplacePanelView(self)
        existing = None

        async for msg in channel.history(limit=50):
            if msg.author.id == self.bot.user.id and msg.embeds:
                footer = msg.embeds[0].footer.text if msg.embeds[0].footer else ""
                if footer == PANEL_TAG:
                    if existing is None:
                        existing = msg
                    else:
                        try:
                            await msg.delete()
                        except Exception:
                            pass

        if existing:
            try:
                await existing.edit(content=None, embed=embed, view=view)
                return
            except Exception:
                pass

        await channel.send(embed=embed, view=view)

    # ------------------------------------------------------------------
    # Core logic
    # ------------------------------------------------------------------

    async def create_listing(
        self,
        interaction: discord.Interaction,
        listing_type: str,
        item: str,
        details: str,
        price: str,
        contact: str,
        tags: str,
    ):
        if not interaction.guild or interaction.guild.id != GUILD_ID:
            await interaction.response.send_message("This system is not configured for this server.", ephemeral=True)
            return

        data = self.get_data()
        now_ts   = int(utcnow().timestamp())
        user_key = str(interaction.user.id)
        last_used = int(data["cooldowns"].get(user_key, 0))

        if now_ts - last_used < LISTING_COOLDOWN_SECONDS:
            remaining = LISTING_COOLDOWN_SECONDS - (now_ts - last_used)
            await interaction.response.send_message(
                f"Please wait {remaining}s before posting another listing.", ephemeral=True
            )
            return

        listing_id = self.next_listing_id()
        entry: Dict[str, Any] = {
            "listing_id":     listing_id,
            "listing_type":   listing_type,
            "author_id":      interaction.user.id,
            "author_name":    str(interaction.user),
            "author_mention": interaction.user.mention,
            "item":           item,
            "details":        details,
            "price":          price,
            "contact":        contact,
            "tags":           tags,
            "status":         "Active",
            "created_at":     utcnow().isoformat(),
            "expires_at":     (utcnow() + timedelta(days=AUTO_DELETE_AFTER_DAYS)).isoformat(),
            "message_id":     None,
        }

        channel = interaction.guild.get_channel(MARKETPLACE_CHANNEL_ID)
        if channel is None:
            await interaction.response.send_message("Marketplace channel not found.", ephemeral=True)
            return

        embed   = self.build_listing_embed(entry)
        message = await channel.send(embed=embed, view=ListingActionView(self))

        data = self.get_data()
        entry["message_id"] = message.id
        data["entries"][listing_id] = entry
        data["cooldowns"][user_key] = now_ts
        self.save_data(data)

        await interaction.response.send_message(
            f"✅ Your listing **{listing_id}** has been posted.", ephemeral=True
        )

    async def mark_listing_status(self, interaction: discord.Interaction, listing_id: str, new_status: str):
        if not interaction.guild:
            await interaction.response.send_message("This can only be used in the server.", ephemeral=True)
            return

        data  = self.get_data()
        entry = data["entries"].get(listing_id)
        if not entry:
            await interaction.response.send_message("Listing not found.", ephemeral=True)
            return

        if interaction.user.id != entry["author_id"] and not has_staff_access(interaction.user):
            await interaction.response.send_message("You can only manage your own listing.", ephemeral=True)
            return

        entry["status"] = new_status
        data["entries"][listing_id] = entry
        self.save_data(data)

        color = COLOR_SUCCESS if new_status == "Sold" else COLOR_MUTED
        embed = self.build_listing_embed(entry, color=color)

        try:
            await interaction.message.edit(embed=embed, view=ListingActionView(self))
        except discord.HTTPException:
            pass

        await interaction.response.send_message(
            f"✅ Listing **{listing_id}** marked as {new_status}.", ephemeral=True
        )

    async def remove_listing(self, interaction: discord.Interaction, listing_id: str, reason: str):
        if not interaction.guild:
            await interaction.response.send_message("This can only be used in the server.", ephemeral=True)
            return

        data  = self.get_data()
        entry = data["entries"].get(listing_id)
        if not entry:
            await interaction.response.send_message("Listing not found.", ephemeral=True)
            return

        if interaction.user.id != entry["author_id"] and not has_staff_access(interaction.user):
            await interaction.response.send_message("You can only remove your own listing.", ephemeral=True)
            return

        channel = interaction.guild.get_channel(MARKETPLACE_CHANNEL_ID)
        if channel and entry.get("message_id"):
            try:
                msg = await channel.fetch_message(entry["message_id"])
                await msg.delete()
            except discord.HTTPException:
                pass

        data["entries"].pop(listing_id, None)
        self.save_data(data)

        await interaction.response.send_message(f"🗑️ Listing **{listing_id}** removed.", ephemeral=True)

        log_channel = interaction.guild.get_channel(MARKETPLACE_LOG_CHANNEL_ID)
        if log_channel:
            try:
                await log_channel.send(
                    f"Marketplace listing **{listing_id}** removed by {interaction.user.mention}.\nReason: {reason}"
                )
            except discord.HTTPException:
                pass

    async def auto_cleanup_expired_listings(self, guild: discord.Guild):
        data    = self.get_data()
        changed = False
        channel = guild.get_channel(MARKETPLACE_CHANNEL_ID)

        for listing_id, entry in list(data["entries"].items()):
            expires_at = entry.get("expires_at")
            if not expires_at:
                continue
            try:
                expiry = datetime.fromisoformat(expires_at)
            except ValueError:
                continue

            if utcnow() >= expiry:
                if channel and entry.get("message_id"):
                    try:
                        msg = await channel.fetch_message(entry["message_id"])
                        await msg.delete()
                    except discord.HTTPException:
                        pass
                data["entries"].pop(listing_id, None)
                changed = True

        if changed:
            self.save_data(data)

    # ------------------------------------------------------------------
    # Prefix commands
    # ------------------------------------------------------------------

    @commands.command(name="postmarketpanel")
    @commands.has_permissions(manage_guild=True)
    async def post_market_panel(self, ctx: commands.Context):
        """Posts or refreshes the Marketplace panel. Usage: !postmarketpanel"""
        channel = ctx.guild.get_channel(MARKETPLACE_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            await ctx.send("❌ Marketplace channel not found.", delete_after=8)
            return
        try:
            await ctx.message.delete()
        except Exception:
            pass
        await self._post_or_refresh_panel(channel)
        await ctx.send(f"✅ Marketplace panel posted/refreshed in {channel.mention}.", delete_after=8)

    @commands.command(name="marketcleanup")
    @commands.has_permissions(manage_guild=True)
    async def market_cleanup(self, ctx: commands.Context):
        """Manually triggers expired listing cleanup. Usage: !marketcleanup"""
        await self.auto_cleanup_expired_listings(ctx.guild)
        await ctx.send("✅ Marketplace cleanup completed.", delete_after=8)

    @commands.command(name="marketlistings")
    @commands.has_permissions(manage_guild=True)
    async def market_listings(self, ctx: commands.Context):
        """Lists all active marketplace entries. Usage: !marketlistings"""
        data    = self.get_data()
        entries = list(data["entries"].values())
        if not entries:
            await ctx.send("No active marketplace listings.")
            return

        embed = discord.Embed(title="Active Marketplace Listings", color=COLOR_PRIMARY)
        lines = [
            f"**{e['listing_id']}** — {e['listing_type']} — {e['item']} — {e['author_name']}"
            for e in entries[:15]
        ]
        embed.add_field(name="Current Listings", value="\n".join(lines), inline=False)
        embed.set_footer(text="Different Meets • Marketplace System")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(MarketplaceSystem(bot))
