from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import discord
from discord.ext import commands

GUILD_ID = 850386896509337710

PARTNER_DIRECTORY_CHANNEL_ID = 1485892421593337926
PARTNER_ANNOUNCEMENT_CHANNEL_ID = 1047166622235893911
PARTNER_STAFF_ALERT_CHANNEL_ID = 1025842308752621719

PARTNER_ANNOUNCEMENT_PING_ROLE_ID = 1141435226929762335
COLLAB_PARTNER_ROLE_ID = 1333770908807991359

DATA_DIR = "diff_data"
PARTNER_DATA_FILE = os.path.join(DATA_DIR, "partners_directory.json")
PARTNERSHIP_APPLICATIONS_FILE = os.path.join(DATA_DIR, "partnership_applications.json")

INACTIVITY_DAYS = 14

EMBED_COLOR = 0x1F6FEB
SUCCESS_COLOR = 0x2ECC71
WARNING_COLOR = 0xF1C40F


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def ensure_data_dir() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


def load_json(path: str, default):
    ensure_data_dir()
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
    ensure_data_dir()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


@dataclass
class PartnerRecord:
    guild_name: str
    owner_name: str
    owner_id: int
    invite_link: str
    description: str
    server_logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    partner_role_assigned: bool = False
    collab_tag: str = "Official Partner"
    accepted_at: str = ""
    last_activity_at: str = ""
    is_active: bool = True
    announcement_message_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PartnerInviteView(discord.ui.View):
    def __init__(self, invite_link: str):
        super().__init__(timeout=None)
        if invite_link:
            self.add_item(
                discord.ui.Button(
                    label="Join Partner",
                    style=discord.ButtonStyle.link,
                    url=invite_link,
                    emoji="🔗"
                )
            )


class PartnerExpansion(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Auto-refresh loop is intentionally disabled — sync only fires on
        # partner changes or manual !partneradmin refresh / !postpartnerdirectory.

    def cog_unload(self):
        pass

    @commands.Cog.listener()
    async def on_ready(self):
        print("[PartnerExpansion] Cog ready.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        if message.guild.id != GUILD_ID:
            return
        if any(role.id == COLLAB_PARTNER_ROLE_ID for role in getattr(message.author, "roles", [])):
            await self.update_partner_activity_by_owner(message.author.id)

    def get_partner_records(self) -> Dict[str, Dict[str, Any]]:
        return load_json(PARTNER_DATA_FILE, {})

    def save_partner_records(self, data: Dict[str, Dict[str, Any]]) -> None:
        save_json(PARTNER_DATA_FILE, data)

    def get_application_records(self) -> Dict[str, Dict[str, Any]]:
        return load_json(PARTNERSHIP_APPLICATIONS_FILE, {})

    async def register_accepted_partner(
        self,
        member: discord.Member,
        guild_name: str,
        invite_link: str,
        description: str,
        server_logo_url: Optional[str] = None,
        banner_url: Optional[str] = None,
    ) -> None:
        data = self.get_partner_records()
        record = PartnerRecord(
            guild_name=guild_name,
            owner_name=str(member),
            owner_id=member.id,
            invite_link=invite_link,
            description=description,
            server_logo_url=server_logo_url,
            banner_url=banner_url,
            partner_role_assigned=False,
            collab_tag="Collab Partner",
            accepted_at=utcnow().isoformat(),
            last_activity_at=utcnow().isoformat(),
            is_active=True,
        )
        data[str(member.id)] = record.to_dict()
        self.save_partner_records(data)

        await self.assign_collab_role(member)
        await self.post_partner_announcement(record)
        await self.sync_directory_panel()

    async def update_partner_activity_by_owner(self, owner_id: int) -> None:
        data = self.get_partner_records()
        record = data.get(str(owner_id))
        if not record:
            return
        record["last_activity_at"] = utcnow().isoformat()
        record["is_active"] = True
        data[str(owner_id)] = record
        self.save_partner_records(data)

    async def assign_collab_role(self, member: discord.Member) -> None:
        role = member.guild.get_role(COLLAB_PARTNER_ROLE_ID)
        if role and role not in member.roles:
            try:
                await member.add_roles(role, reason="Accepted DIFF partnership")
            except discord.HTTPException:
                pass
        data = self.get_partner_records()
        if str(member.id) in data:
            data[str(member.id)]["partner_role_assigned"] = True
            self.save_partner_records(data)

    async def post_partner_announcement(self, record: PartnerRecord):
        channel = self.bot.get_channel(PARTNER_ANNOUNCEMENT_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            return None

        ping_role = f"<@&{PARTNER_ANNOUNCEMENT_PING_ROLE_ID}>"
        collab_role = f"<@&{COLLAB_PARTNER_ROLE_ID}>"

        embed = discord.Embed(
            title="🤝 New Official Partnership",
            description=(
                "We are proud to welcome a new DIFF Partner.\n\n"
                f"**Server Name:** {record.guild_name}\n"
                f"**Tag:** {record.collab_tag}\n"
                f"**Description:** {record.description}"
            ),
            color=SUCCESS_COLOR,
            timestamp=utcnow()
        )
        embed.add_field(name="Invite Link", value=f"[Join Server]({record.invite_link})", inline=False)
        embed.add_field(name="Partnership Type", value="Collab Meet Eligible", inline=True)
        embed.add_field(name="Status", value="Active", inline=True)

        if record.server_logo_url:
            embed.set_thumbnail(url=record.server_logo_url)
        if record.banner_url:
            embed.set_image(url=record.banner_url)

        embed.set_footer(text="Different Meets • Official Partner Announcement")

        message = await channel.send(
            content=f"{ping_role} {collab_role}",
            embed=embed,
            view=PartnerInviteView(record.invite_link)
        )

        data = self.get_partner_records()
        if str(record.owner_id) in data:
            data[str(record.owner_id)]["announcement_message_id"] = message.id
            self.save_partner_records(data)
        return message

    def _dir_state_path(self):
        return os.path.join(DATA_DIR, "partner_directory_state.json")

    def _load_dir_state(self):
        path = self._dir_state_path()
        if os.path.exists(path):
            try:
                with open(path) as f:
                    return json.load(f)
            except Exception:
                pass
        return {"header_id": None, "content_ids": []}

    def _save_dir_state(self, state):
        with open(self._dir_state_path(), "w") as f:
            json.dump(state, f)

    def _build_partner_embed(self, partner):
        status_text = "🟢 Active" if partner.get("is_active", True) else "🟠 Inactive Flagged"
        embed = discord.Embed(
            title=f"🤝 {partner.get('guild_name', 'Unknown Partner')}",
            description=partner.get("description", "No description provided."),
            color=EMBED_COLOR,
        )
        embed.add_field(name="Status", value=status_text, inline=True)
        embed.add_field(name="Type", value=partner.get("collab_tag", "Official Partner"), inline=True)
        embed.add_field(
            name="Invite",
            value=f"[Join Partner Server]({partner.get('invite_link', 'https://discord.gg/')})",
            inline=False,
        )
        if partner.get("server_logo_url"):
            embed.set_thumbnail(url=partner["server_logo_url"])
        if partner.get("banner_url"):
            embed.set_image(url=partner["banner_url"])
        embed.set_footer(text="Different Meets • Partner Directory")
        return embed

    _PARTNER_FOOTERS = {
        "Different Meets • Official Partner Network",
        "Different Meets • Partner Directory",
    }

    async def _scan_existing_panel_msgs(self, channel: discord.TextChannel) -> list:
        """Scan channel history and return bot messages that belong to the partner panel, oldest first."""
        found = []
        try:
            async for msg in channel.history(limit=200):
                if msg.author == self.bot.user and msg.embeds:
                    footer = msg.embeds[0].footer.text if msg.embeds[0].footer else ""
                    if footer in self._PARTNER_FOOTERS:
                        found.append(msg)
        except Exception:
            pass
        found.reverse()  # oldest first
        return found

    async def sync_directory_panel(self):
        if not hasattr(self, "_sync_lock"):
            import asyncio
            self._sync_lock = asyncio.Lock()

        if self._sync_lock.locked():
            return

        async with self._sync_lock:
            channel = self.bot.get_channel(PARTNER_DIRECTORY_CHANNEL_ID)
            if not isinstance(channel, discord.TextChannel):
                return

            partners = list(self.get_partner_records().values())
            state = self._load_dir_state()

            header_embed = discord.Embed(
                title="🔗 DIFF Partner Directory",
                description=(
                    "Welcome to the official DIFF Partner Showcase.\n"
                    "Below you can find our active partner communities."
                ),
                color=EMBED_COLOR,
            )
            header_embed.add_field(
                name="📋 Staff Commands",
                value=(
                    "`!postpartnerdirectory` — Post / refresh this directory\n"
                    "`!importacceptedpartners` — Import all approved partners\n"
                    "`!partneradmin refresh` — Manually refresh the directory panel\n"
                    "`!partneradmin activity` — View partner activity log\n"
                    "`!partneradmin add <name>` — Add a partner to the directory\n"
                    "`!partneradmin remove <name>` — Remove a partner from the directory"
                ),
                inline=False,
            )
            header_embed.set_footer(text="Different Meets • Official Partner Network")

            content_embeds = []
            content_views = []
            if not partners:
                content_embeds.append(discord.Embed(
                    title="No Partners Listed Yet",
                    description="Approved partners will appear here automatically.",
                    color=EMBED_COLOR,
                ))
                content_views.append(None)
            else:
                for p in partners:
                    content_embeds.append(self._build_partner_embed(p))
                    content_views.append(PartnerInviteView(p.get("invite_link", "")))

            # Total expected messages = 1 header + len(content_embeds)
            total_expected = 1 + len(content_embeds)

            # Fast path: try saved message IDs first
            header_id = state.get("header_id")
            content_ids = state.get("content_ids", [])
            edited_ok = False

            if header_id and len(content_ids) == len(content_embeds):
                try:
                    header_msg = await channel.fetch_message(header_id)
                    await header_msg.edit(embed=header_embed)
                    all_ok = True
                    for mid, emb, view in zip(content_ids, content_embeds, content_views):
                        try:
                            msg = await channel.fetch_message(mid)
                            await msg.edit(embed=emb, view=view)
                        except Exception:
                            all_ok = False
                            break
                    if all_ok:
                        edited_ok = True
                except Exception:
                    pass

            # Fallback: scan channel for existing panel messages and edit them
            if not edited_ok:
                existing = await self._scan_existing_panel_msgs(channel)
                if len(existing) == total_expected:
                    # Edit in place — header is first, rest are content
                    try:
                        await existing[0].edit(embed=header_embed)
                        for msg, emb, view in zip(existing[1:], content_embeds, content_views):
                            await msg.edit(embed=emb, view=view)
                        self._save_dir_state({
                            "header_id": existing[0].id,
                            "content_ids": [m.id for m in existing[1:]],
                        })
                        edited_ok = True
                    except Exception:
                        pass

            # Full sync: delete existing panel messages and repost fresh
            if not edited_ok:
                existing = await self._scan_existing_panel_msgs(channel)
                for msg in existing:
                    try:
                        await msg.delete()
                    except Exception:
                        pass

                header_msg = await channel.send(embed=header_embed)
                new_content_ids = []
                for emb, view in zip(content_embeds, content_views):
                    if view:
                        m = await channel.send(embed=emb, view=view)
                    else:
                        m = await channel.send(embed=emb)
                    new_content_ids.append(m.id)

                self._save_dir_state({"header_id": header_msg.id, "content_ids": new_content_ids})

    async def flag_inactive_partners(self):
        staff_channel = self.bot.get_channel(PARTNER_STAFF_ALERT_CHANNEL_ID)
        data = self.get_partner_records()
        changed = False

        for owner_id, record in data.items():
            last_activity_raw = record.get("last_activity_at")
            if not last_activity_raw:
                continue
            try:
                last_activity = datetime.fromisoformat(last_activity_raw)
            except ValueError:
                continue

            cutoff = utcnow() - timedelta(days=INACTIVITY_DAYS)
            is_inactive = last_activity < cutoff

            if is_inactive and record.get("is_active", True):
                record["is_active"] = False
                changed = True
                if isinstance(staff_channel, discord.TextChannel):
                    embed = discord.Embed(
                        title="⚠️ Inactive Partner Flagged",
                        description=(
                            f"**Partner:** {record.get('guild_name', 'Unknown')}\n"
                            f"**Owner ID:** {owner_id}\n"
                            f"**Last Activity:** {last_activity_raw[:19]}\n\n"
                            "This partner has been flagged for inactivity."
                        ),
                        color=WARNING_COLOR,
                        timestamp=utcnow()
                    )
                    try:
                        await staff_channel.send(embed=embed)
                    except Exception:
                        pass
            elif not is_inactive and not record.get("is_active", True):
                record["is_active"] = True
                changed = True

        if changed:
            self.save_partner_records(data)

    @commands.group(name="partneradmin", invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def partneradmin(self, ctx: commands.Context):
        await ctx.send(
            "**Partner Admin Commands:**\n"
            "`!partneradmin refresh` — Refresh directory & check inactivity\n"
            "`!partneradmin add @user <invite> Server Name | Description` — Register a new partner\n"
            "`!partneradmin activity @user` — Manually mark a partner as active\n"
            "`!partneradmin remove @user` — Remove a partner from the directory"
        )

    @partneradmin.command(name="refresh")
    @commands.has_permissions(manage_guild=True)
    async def partner_refresh(self, ctx: commands.Context):
        await ctx.send("🔄 Refreshing partner directory...")
        await self.sync_directory_panel()
        await self.flag_inactive_partners()
        await ctx.send("✅ Partner directory and activity monitor refreshed.")

    @partneradmin.command(name="activity")
    @commands.has_permissions(manage_guild=True)
    async def partner_activity(self, ctx: commands.Context, member: discord.Member):
        await self.update_partner_activity_by_owner(member.id)
        await ctx.send(f"✅ Updated activity for {member.mention}.")

    @partneradmin.command(name="remove")
    @commands.has_permissions(manage_guild=True)
    async def partner_remove(self, ctx: commands.Context, member: discord.Member):
        data = self.get_partner_records()
        record = data.pop(str(member.id), None)
        if not record:
            await ctx.send("❌ That member is not in the partner directory.")
            return

        role = ctx.guild.get_role(COLLAB_PARTNER_ROLE_ID)
        if role and role in member.roles:
            try:
                await member.remove_roles(role, reason="Removed from DIFF partner system")
            except discord.HTTPException:
                pass

        self.save_partner_records(data)
        await self.sync_directory_panel()
        await ctx.send(f"🗑️ Removed **{record.get('guild_name', 'Unknown Partner')}** from the partner system.")

    @partneradmin.command(name="add")
    @commands.has_permissions(manage_guild=True)
    async def partner_add(self, ctx: commands.Context, member: discord.Member, invite_link: str, *, guild_name_and_description: str):
        if "|" not in guild_name_and_description:
            await ctx.send("❌ Format: `!partneradmin add @user <invite> Server Name | Description`")
            return
        guild_name, description = [x.strip() for x in guild_name_and_description.split("|", 1)]
        await ctx.send(f"✅ Registering **{guild_name}**...")
        await self.register_accepted_partner(
            member=member,
            guild_name=guild_name,
            invite_link=invite_link,
            description=description
        )
        await ctx.send(f"✅ Added **{guild_name}** to the partner system and posted the announcement.")

    @commands.command(name="postpartnerdirectory")
    @commands.has_permissions(manage_guild=True)
    async def postpartnerdirectory(self, ctx: commands.Context):
        await ctx.send("🔄 Syncing partner directory...")
        await self.sync_directory_panel()
        await ctx.send("✅ Partner directory panel refreshed.")

    @commands.command(name="importacceptedpartners")
    @commands.has_permissions(manage_guild=True)
    async def importacceptedpartners(self, ctx: commands.Context):
        apps = self.get_application_records()
        data = self.get_partner_records()
        imported = 0

        guild = self.bot.get_guild(GUILD_ID)
        if guild is None:
            await ctx.send("❌ Guild not found.")
            return

        for _, app in apps.items():
            if str(app.get("status", "")).lower() != "accepted":
                continue

            owner_id = app.get("owner_id") or app.get("user_id") or app.get("applicant_id")
            if not owner_id:
                continue

            member = guild.get_member(int(owner_id))
            if member is None:
                continue
            if str(member.id) in data:
                continue

            record = PartnerRecord(
                guild_name=app.get("server_name", "Unnamed Partner"),
                owner_name=str(member),
                owner_id=member.id,
                invite_link=app.get("invite_link", "https://discord.gg/"),
                description=app.get("description", "Approved DIFF partner."),
                server_logo_url=app.get("logo_url"),
                banner_url=app.get("banner_url"),
                partner_role_assigned=False,
                collab_tag="Collab Partner",
                accepted_at=utcnow().isoformat(),
                last_activity_at=utcnow().isoformat(),
                is_active=True,
            )
            data[str(member.id)] = record.to_dict()
            imported += 1
            await self.assign_collab_role(member)
            await self.post_partner_announcement(record)

        self.save_partner_records(data)
        await self.sync_directory_panel()
        await ctx.send(f"✅ Imported **{imported}** accepted partner(s).")


async def setup(bot: commands.Bot):
    await bot.add_cog(PartnerExpansion(bot))
