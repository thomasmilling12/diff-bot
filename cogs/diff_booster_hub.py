"""
diff_booster_hub.py
═══════════════════
DIFF Meets — Server Booster Hub

Posts a persistent panel in the welcome-hub channel.
Dropdown options:
  • Claim Your Perks       — assigns the DIFF Booster badge role
  • My Booster Status      — shows boosting info + active perks
  • Submit Build Showcase  — modal → staff review → showcase post
  • Booster Perks Guide    — full breakdown of every perk

Auto-features:
  • New booster DM + #welcome-hub announcement on premium_since change
  • Showcase approval / denial buttons for staff

Staff commands:
  !post_booster_panel   — post panel to welcome-hub channel
  !refresh_booster_panel — refresh existing panel
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import discord
from discord.ext import commands

print("[BoosterHub] Module loading...")

# ─── Configuration ────────────────────────────────────────────────────────────
GUILD_ID              = 850386896509337710
BOOSTER_PANEL_CHANNEL = 1047335231826436166   # everyone chat
MOD_HUB_CHANNEL_ID    = 1486598266211664003   # staff review channel
LOG_CHANNEL_ID        = 1485265848099799163

# !! Create a "💎 DIFF Booster" role manually in your server,
#    then paste its ID below. Leave 0 to skip auto-role assignment.
BOOSTER_BADGE_ROLE_ID = 990106677330194453

# Category to create showcase ticket channels in.
# Set to 0 to create without a category (tickets appear at the top of the list).
SHOWCASE_TICKET_CATEGORY_ID = 1328457973583839282

# Roles that can see and manage showcase tickets
COLOR_TEAM_ROLE_ID = 1115495008670330902
LEADER_ROLE_ID     = 850391095845584937
CO_LEADER_ROLE_ID  = 850391378559238235
MANAGER_ROLE_ID    = 990011447193006101
_STAFF_ROLE_IDS    = (LEADER_ROLE_ID, CO_LEADER_ROLE_ID, MANAGER_ROLE_ID, COLOR_TEAM_ROLE_ID)

DATA_FILE = os.path.join("diff_data", "diff_booster_hub.json")

DIFF_LOGO = (
    "https://media.discordapp.net/attachments/1107375326625005719/"
    "1484949205331083375/content.png?ex=69c01637&is=69bec4b7&hm="
    "2f7f022f2c6ffce9ffb9c68ac86301c5a8ff407e36ec1c8b3bb97f12ea4b2e9a"
    "&=&format=webp&quality=lossless&width=1376&height=917"
)

PERK_LIST = [
    ("💎", "Booster Badge Role",        "Exclusive role displayed in the member list."),
    ("🎨", "Custom Crew Color Access",  "Priority access to color team for a custom crew color."),
    ("📸", "Car Showcase Feature",      "Submit your build to be featured in the DIFF showcase."),
    ("🏁", "Priority Meet Slot",        "You're highlighted as a priority RSVP at every meet."),
    ("📣", "Build Shoutout",            "Request a staff-posted shoutout of your build."),
    ("🔒", "Booster Lounge Access",     "Exclusive channel visible only to boosters & staff."),
]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ─── State helpers ────────────────────────────────────────────────────────────
def _load() -> dict:
    try:
        with open(DATA_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict) -> None:
    os.makedirs("diff_data", exist_ok=True)
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[BoosterHub] Save error: {e}")


def _get_panel_id() -> int | None:
    v = _load().get("panel_message_id")
    return int(v) if v else None


def _set_panel_id(mid: int) -> None:
    d = _load()
    d["panel_message_id"] = mid
    _save(d)


def _is_boosting(member: discord.Member) -> bool:
    return member.premium_since is not None


def _boost_since(member: discord.Member) -> str:
    if not member.premium_since:
        return "Not boosting"
    delta = _utc_now() - member.premium_since.replace(tzinfo=timezone.utc)
    days = delta.days
    if days == 0:
        return "Today"
    if days == 1:
        return "1 day"
    if days < 30:
        return f"{days} days"
    months = days // 30
    return f"{months} month{'s' if months != 1 else ''}"


# ─── Embeds ───────────────────────────────────────────────────────────────────
def _panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title="💎 DIFF Booster Perks Hub",
        description=(
            "**Thank you for supporting Different Meets!**\n\n"
            "Boosting the server helps us grow, unlock features, and keep the community strong. "
            "As a booster, you earn exclusive perks that no one else gets.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=0xF47FFF,
        timestamp=_utc_now(),
    )
    perks_text = "\n".join(f"{icon} **{name}** — {desc}" for icon, name, desc in PERK_LIST)
    embed.add_field(name="🎁 Your Exclusive Perks", value=perks_text, inline=False)
    embed.add_field(
        name="📌 How to Claim",
        value=(
            "Use the dropdown below to claim your role, check your status, "
            "submit your build for a showcase, or read the full perks guide."
        ),
        inline=False,
    )
    embed.set_thumbnail(url=DIFF_LOGO)
    embed.set_footer(text="Different Meets • Booster Hub • Use the dropdown below")
    return embed


def _status_embed(member: discord.Member) -> discord.Embed:
    boosting = _is_boosting(member)
    embed = discord.Embed(
        title=f"💎 Booster Status — {member.display_name}",
        color=0xF47FFF if boosting else discord.Color.greyple(),
        timestamp=_utc_now(),
    )
    embed.set_thumbnail(url=member.display_avatar.url)

    if boosting:
        embed.description = "✅ You are currently boosting DIFF Meets. Thank you for your support!"
        embed.add_field(name="⏱️ Boosting Since", value=_boost_since(member), inline=True)
        badge_role = member.guild.get_role(BOOSTER_BADGE_ROLE_ID) if BOOSTER_BADGE_ROLE_ID else None
        has_badge = badge_role in member.roles if badge_role else False
        embed.add_field(
            name="💎 Booster Badge",
            value="✅ Claimed" if has_badge else "❌ Not claimed — select **Claim Your Perks**",
            inline=True,
        )
        perks_text = "\n".join(f"{icon} {name}" for icon, name, _ in PERK_LIST)
        embed.add_field(name="🎁 Your Active Perks", value=perks_text, inline=False)
    else:
        embed.description = (
            "❌ You are not currently boosting DIFF Meets.\n\n"
            "Boost the server to unlock exclusive perks — your support keeps DIFF growing!"
        )
    embed.set_footer(text="Different Meets • Booster Status")
    return embed


def _guide_embed() -> discord.Embed:
    embed = discord.Embed(
        title="📖 DIFF Booster Perks — Full Guide",
        description=(
            "Everything you unlock by boosting Different Meets.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=0xF47FFF,
    )
    for icon, name, desc in PERK_LIST:
        embed.add_field(name=f"{icon} {name}", value=desc, inline=False)
    embed.add_field(
        name="❓ How to Boost",
        value=(
            "Open server settings → **Server Boost** → tap the boost button.\n"
            "Once boosted, come back here and select **Claim Your Perks**."
        ),
        inline=False,
    )
    embed.set_footer(text="Different Meets • Booster Perks Guide")
    return embed


# ─── Showcase Modal ───────────────────────────────────────────────────────────
class _ShowcaseModal(discord.ui.Modal, title="Submit Your Build for Showcase"):
    car_name    = discord.ui.TextInput(
        label="Car Name / Model",
        placeholder="e.g. Pegassi Zentorno, Karin Previon",
        max_length=80,
    )
    color_style = discord.ui.TextInput(
        label="Color & Finish",
        placeholder="e.g. Metallic Galaxy Blue, Matte Black accents",
        max_length=100,
    )
    description = discord.ui.TextInput(
        label="Build Description",
        style=discord.TextStyle.paragraph,
        placeholder="Tell us what makes this build special — stance, inspiration, mods...",
        max_length=400,
    )
    image_link  = discord.ui.TextInput(
        label="Screenshot Link (optional)",
        placeholder="https://cdn.discordapp.com/...",
        required=False,
        max_length=300,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        guild  = interaction.guild
        author = interaction.user
        if not guild or not isinstance(author, discord.Member):
            return await interaction.response.send_message(
                "Please use this inside the server.", ephemeral=True
            )

        # Build submission data
        sub = {
            "car":         str(self.car_name),
            "color":       str(self.color_style),
            "description": str(self.description),
            "image":       str(self.image_link) if self.image_link.value else "",
            "avatar":      author.display_avatar.url,
            "username":    str(author),
            "mention":     author.mention,
            "user_id":     author.id,
        }

        # ── Create private ticket channel ─────────────────────────────────────
        safe_name = "".join(
            c if c.isalnum() or c in ("-", "_") else "-"
            for c in author.display_name.lower()
        )[:28].strip("-") or "booster"
        channel_name = f"showcase-{safe_name}"

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            author:             discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True,
                attach_files=True,
            ),
        }
        for rid in _STAFF_ROLE_IDS:
            role = guild.get_role(rid)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True,
                    read_message_history=True, manage_messages=True,
                    manage_channels=True,
                )

        category = None
        if SHOWCASE_TICKET_CATEGORY_ID:
            category = guild.get_channel(SHOWCASE_TICKET_CATEGORY_ID)

        try:
            ticket_ch = await guild.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                category=category,
                topic=f"SHOWCASE_USER:{author.id} | Build: {sub['car']}",
                reason=f"Booster showcase ticket for {author}",
            )
        except Exception as e:
            print(f"[BoosterHub] Ticket create error: {e}")
            return await interaction.response.send_message(
                "❌ Could not create your showcase ticket. Please contact staff.", ephemeral=True
            )

        # Save pending entry
        data = _load()
        data.setdefault("pending_showcases", {})[str(author.id)] = {
            **sub, "ticket_channel_id": ticket_ch.id
        }
        _save(data)

        # ── Post inside the ticket ────────────────────────────────────────────
        ticket_embed = discord.Embed(
            title="📸 Showcase Submission — Under Review",
            description=(
                f"Hey {author.mention}! Your build has been received and is being reviewed "
                "by the DIFF Color Team and staff.\n\n"
                "Feel free to drop additional screenshots in this channel while you wait. "
                "Staff will approve or deny below."
            ),
            color=0xF47FFF,
            timestamp=_utc_now(),
        )
        ticket_embed.add_field(name="🚗 Car",         value=sub["car"],         inline=True)
        ticket_embed.add_field(name="🎨 Color",       value=sub["color"],       inline=True)
        ticket_embed.add_field(name="📝 Description", value=sub["description"], inline=False)
        if sub["image"]:
            ticket_embed.add_field(name="🖼️ Screenshot", value=sub["image"], inline=False)
        ticket_embed.set_thumbnail(url=author.display_avatar.url)
        ticket_embed.set_footer(text="Different Meets • Booster Showcase Ticket")

        # Build staff ping
        staff_mentions = " ".join(
            r.mention for rid in _STAFF_ROLE_IDS
            if (r := guild.get_role(rid))
        )
        await ticket_ch.send(
            content=f"{author.mention} {staff_mentions}",
            embed=ticket_embed,
            view=_ShowcaseTicketView(author.id),
            allowed_mentions=discord.AllowedMentions(roles=True, users=True),
        )

        await interaction.response.send_message(
            f"✅ Your showcase ticket has been created: {ticket_ch.mention}\n"
            "Staff will review your build there. Feel free to add more screenshots!",
            ephemeral=True,
        )
        print(f"[BoosterHub] Showcase ticket created #{ticket_ch.name} for {author}.")


# ─── Showcase Ticket Buttons (Pi-compatible — no decorators) ─────────────────

def _build_showcase_embed(info: dict) -> discord.Embed:
    embed = discord.Embed(
        title="📸 DIFF Booster Showcase — Featured Build",
        description=info["description"],
        color=0xF47FFF,
        timestamp=_utc_now(),
    )
    embed.add_field(name="🚗 Build",  value=info["car"],     inline=True)
    embed.add_field(name="🎨 Color",  value=info["color"],   inline=True)
    embed.add_field(name="💎 Member", value=info["mention"], inline=False)
    if info.get("image"):
        embed.set_image(url=info["image"])
    embed.set_thumbnail(url=info["avatar"])
    embed.set_footer(text="Different Meets • Booster Build Showcase")
    return embed


class _ApproveBtn(discord.ui.Button):
    def __init__(self, user_id: int):
        super().__init__(
            label="✅ Approve & Post",
            style=discord.ButtonStyle.success,
            custom_id=f"bsc_approve:{user_id}",
        )
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()

        data    = _load()
        pending = data.get("pending_showcases", {})
        info    = pending.pop(str(self.user_id), None)
        _save(data)

        if not info:
            return await interaction.followup.send(
                "Submission not found — may have already been processed.", ephemeral=True
            )

        guild = interaction.guild
        # Post showcase to welcome-hub
        pub_ch = guild.get_channel(BOOSTER_PANEL_CHANNEL) if guild else None
        if isinstance(pub_ch, discord.TextChannel):
            try:
                await pub_ch.send(
                    content=f"💎 Booster Build Showcase — <@{self.user_id}>",
                    embed=_build_showcase_embed(info),
                    allowed_mentions=discord.AllowedMentions(users=True),
                )
            except Exception as e:
                print(f"[BoosterHub] Showcase post error: {e}")

        # DM the booster
        try:
            member = guild.get_member(self.user_id) if guild else None
            if member:
                await member.send(embed=discord.Embed(
                    title="🎉 Your Showcase was Approved!",
                    description=(
                        "Your build has been featured in the DIFF showcase! "
                        f"Check out <#{BOOSTER_PANEL_CHANNEL}> to see it posted.\n\n"
                        "Thanks for representing the community 💎"
                    ),
                    color=discord.Color.green(),
                ))
        except Exception:
            pass

        # Close ticket channel
        ticket_ch = interaction.channel
        if isinstance(ticket_ch, discord.TextChannel):
            await ticket_ch.send(
                embed=discord.Embed(
                    description=f"✅ Approved by {interaction.user.mention}. This ticket will close shortly.",
                    color=discord.Color.green(),
                )
            )
            import asyncio
            await asyncio.sleep(5)
            try:
                await ticket_ch.delete(reason="Showcase approved — ticket closed")
            except Exception:
                pass


class _DenyBtn(discord.ui.Button):
    def __init__(self, user_id: int):
        super().__init__(
            label="❌ Deny",
            style=discord.ButtonStyle.danger,
            custom_id=f"bsc_deny:{user_id}",
        )
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(_DenyReasonModal(self.user_id, interaction.channel))


class _DenyReasonModal(discord.ui.Modal, title="Deny Showcase — Add Feedback"):
    reason = discord.ui.TextInput(
        label="Reason / Feedback for the member",
        style=discord.TextStyle.paragraph,
        placeholder="e.g. Photos are too dark, try a cleaner angle. Resubmit when ready.",
        max_length=500,
    )

    def __init__(self, user_id: int, channel):
        super().__init__()
        self.user_id = user_id
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()

        data    = _load()
        pending = data.get("pending_showcases", {})
        pending.pop(str(self.user_id), None)
        _save(data)

        # DM the booster with the feedback
        try:
            guild  = interaction.guild
            member = guild.get_member(self.user_id) if guild else None
            if member:
                await member.send(embed=discord.Embed(
                    title="📸 Showcase Submission — Not Approved",
                    description=(
                        "Your showcase submission wasn't approved this time.\n\n"
                        f"**Staff feedback:** {self.reason}\n\n"
                        "Feel free to improve your submission and try again — we'd love to feature you! 💎"
                    ),
                    color=discord.Color.red(),
                ))
        except Exception:
            pass

        # Close ticket
        ticket_ch = self.channel
        if isinstance(ticket_ch, discord.TextChannel):
            await ticket_ch.send(
                embed=discord.Embed(
                    description=(
                        f"❌ Denied by {interaction.user.mention}.\n"
                        f"**Feedback:** {self.reason}\n\n"
                        "The member has been notified. Ticket closing shortly."
                    ),
                    color=discord.Color.red(),
                )
            )
            import asyncio
            await asyncio.sleep(5)
            try:
                await ticket_ch.delete(reason="Showcase denied — ticket closed")
            except Exception:
                pass


class _ShowcaseTicketView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        self.add_item(_ApproveBtn(user_id))
        self.add_item(_DenyBtn(user_id))


# ─── Main Dropdown ────────────────────────────────────────────────────────────
class _BoosterSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            custom_id="diff_booster_hub_select_v1",
            placeholder="💎  Select a booster option...",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(
                    label="Claim Your Perks",
                    emoji="💎",
                    value="claim",
                    description="Verify your boost status and receive the Booster badge role.",
                ),
                discord.SelectOption(
                    label="My Booster Status",
                    emoji="📊",
                    value="status",
                    description="See how long you've been boosting and which perks are active.",
                ),
                discord.SelectOption(
                    label="Submit Build Showcase",
                    emoji="📸",
                    value="showcase",
                    description="Submit your car to be featured in the DIFF showcase.",
                ),
                discord.SelectOption(
                    label="Booster Perks Guide",
                    emoji="📖",
                    value="guide",
                    description="See the full breakdown of every booster perk.",
                ),
            ],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        member = interaction.user
        if not isinstance(member, discord.Member):
            return await interaction.response.send_message(
                "Please use this in the server.", ephemeral=True
            )

        v = self.values[0]

        # ── Claim ─────────────────────────────────────────────────────────────
        if v == "claim":
            if not _is_boosting(member):
                return await interaction.response.send_message(
                    embed=discord.Embed(
                        title="💎 Not a Booster",
                        description=(
                            "You're not currently boosting DIFF Meets.\n\n"
                            "Boost the server to unlock exclusive perks and then come back here!"
                        ),
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )

            results = []

            # Assign badge role
            if BOOSTER_BADGE_ROLE_ID:
                badge_role = member.guild.get_role(BOOSTER_BADGE_ROLE_ID)
                if badge_role:
                    if badge_role not in member.roles:
                        try:
                            await member.add_roles(
                                badge_role, reason="Booster perk claim"
                            )
                            results.append("💎 **Booster Badge** role assigned!")
                        except discord.Forbidden:
                            results.append("⚠️ Couldn't assign badge role — missing permissions.")
                    else:
                        results.append("✅ Booster Badge role already active.")
                else:
                    results.append("⚠️ Badge role not configured yet — contact staff.")
            else:
                results.append("⚠️ Booster badge role not configured yet — let staff know you boosted!")

            results += [
                "📸 **Build Showcase** — select it from the dropdown to submit",
                "🏁 **Priority Meet Slot** — your RSVPs are flagged as priority",
                "📣 **Build Shoutout** — ask any staff member to post one for you",
                "🔒 **Booster Lounge** — you should now have access automatically",
            ]

            embed = discord.Embed(
                title="💎 Booster Perks Claimed!",
                description="\n".join(results),
                color=0xF47FFF,
                timestamp=_utc_now(),
            )
            embed.add_field(
                name="Thank You",
                value="Your support keeps DIFF growing. Every boost helps us unlock more server features.",
                inline=False,
            )
            embed.set_footer(text="Different Meets • Booster Hub")
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # ── Status ────────────────────────────────────────────────────────────
        if v == "status":
            return await interaction.response.send_message(
                embed=_status_embed(member), ephemeral=True
            )

        # ── Showcase ──────────────────────────────────────────────────────────
        if v == "showcase":
            if not _is_boosting(member):
                return await interaction.response.send_message(
                    "The build showcase is a **booster-exclusive** perk. "
                    "Boost the server to unlock it!",
                    ephemeral=True,
                )
            return await interaction.response.send_modal(_ShowcaseModal())

        # ── Guide ─────────────────────────────────────────────────────────────
        if v == "guide":
            return await interaction.response.send_message(
                embed=_guide_embed(), ephemeral=True
            )


class _BoosterView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(_BoosterSelect())


# ─── COG ─────────────────────────────────────────────────────────────────────
class BoosterHubCog(commands.Cog, name="BoosterHub"):

    def __init__(self, bot: commands.Bot):
        self.bot  = bot
        self.view = _BoosterView()
        try:
            bot.add_view(self.view)
            print("[BoosterHub] Persistent view registered.")
        except Exception as e:
            print(f"[BoosterHub] add_view failed: {e}")

    async def _delete_standalone_panel(self) -> None:
        """Delete old standalone booster panel messages from welcome-hub.

        The booster options are now embedded in the combined Welcome Hub panel.
        Call this after running !welcomehub to clean up any leftover standalone panel.
        """
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return
        ch = guild.get_channel(BOOSTER_PANEL_CHANNEL)
        if not isinstance(ch, discord.TextChannel):
            try:
                ch = await guild.fetch_channel(BOOSTER_PANEL_CHANNEL)
            except Exception:
                return
        bot_id = self.bot.user.id if self.bot.user else None
        deleted = 0
        try:
            async for msg in ch.history(limit=100):
                if msg.author.id != bot_id:
                    continue
                title = msg.embeds[0].title if msg.embeds else ""
                if "DIFF Booster Perks Hub" in (title or ""):
                    try:
                        await msg.delete()
                        deleted += 1
                        print(f"[BoosterHub] Deleted standalone panel {msg.id}.")
                    except Exception:
                        pass
        except Exception as e:
            print(f"[BoosterHub] Panel scan error: {e}")
        print(f"[BoosterHub] Standalone panel cleanup done ({deleted} removed).")

    # ── New booster auto-welcome ──────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        was_boosting  = before.premium_since is not None
        now_boosting  = after.premium_since  is not None
        if was_boosting or not now_boosting:
            return  # Not a new boost

        # DM the new booster
        try:
            dm_embed = discord.Embed(
                title="💎 Thanks for Boosting DIFF Meets!",
                description=(
                    f"Hey {after.mention}! You just boosted **Different Meets** — "
                    "that means a lot to us.\n\n"
                    "Head to the **welcome hub** channel and use the **Booster Hub** dropdown "
                    "to claim your exclusive perks right now!"
                ),
                color=0xF47FFF,
                timestamp=_utc_now(),
            )
            dm_embed.add_field(
                name="🎁 Your Perks",
                value="\n".join(f"{icon} **{name}**" for icon, name, _ in PERK_LIST),
                inline=False,
            )
            dm_embed.set_footer(text="Different Meets • Thanks for your support 💎")
            await after.send(embed=dm_embed)
        except discord.Forbidden:
            pass

        # Post a welcome shoutout in welcome-hub
        guild = after.guild
        ch = guild.get_channel(BOOSTER_PANEL_CHANNEL)
        if isinstance(ch, discord.TextChannel):
            try:
                shout_embed = discord.Embed(
                    title="💎 New Server Booster!",
                    description=(
                        f"{after.mention} just boosted **DIFF Meets**! "
                        "Thank you for supporting the community — "
                        "your exclusive perks are ready to claim. 🙌"
                    ),
                    color=0xF47FFF,
                    timestamp=_utc_now(),
                )
                shout_embed.set_thumbnail(url=after.display_avatar.url)
                shout_embed.set_footer(text="Different Meets • Server Booster")
                await ch.send(
                    content=after.mention,
                    embed=shout_embed,
                    allowed_mentions=discord.AllowedMentions(users=True),
                )
            except Exception as e:
                print(f"[BoosterHub] Shoutout error: {e}")

    # ── Commands ──────────────────────────────────────────────────────────────
    @commands.command(name="post_booster_panel")
    @commands.has_permissions(administrator=True)
    async def cmd_post(self, ctx: commands.Context) -> None:
        """Booster options are now part of the combined !welcomehub panel.
        This command cleans up the old standalone panel and refreshes the welcome hub."""
        try:
            await ctx.message.delete()
        except Exception:
            pass
        await ctx.send(
            "💎 Booster options are now built into the Welcome Hub panel.\n"
            "Cleaning up the old standalone panel and refreshing...",
            delete_after=8,
        )
        await self._delete_standalone_panel()
        # Trigger the combined welcome hub refresh
        import sys as _sys
        main = _sys.modules.get("__main__")
        wh_fn = getattr(main, "_wh_post_or_refresh", None)
        if wh_fn and ctx.guild:
            await wh_fn(ctx.guild)
            await ctx.send("✅ Welcome Hub panel updated with booster options.", delete_after=8)
        else:
            await ctx.send("Run `!welcomehub` to refresh the combined panel.", delete_after=10)

    @commands.command(name="refresh_booster_panel")
    @commands.has_permissions(administrator=True)
    async def cmd_refresh(self, ctx: commands.Context) -> None:
        """Alias: refreshes the combined Welcome Hub panel (booster options are now inside it)."""
        try:
            await ctx.message.delete()
        except Exception:
            pass
        await self._delete_standalone_panel()
        import sys as _sys
        main = _sys.modules.get("__main__")
        wh_fn = getattr(main, "_wh_post_or_refresh", None)
        if wh_fn and ctx.guild:
            await wh_fn(ctx.guild)
            await ctx.send("✅ Welcome Hub refreshed (booster options included).", delete_after=8)
        else:
            await ctx.send("Run `!welcomehub` to refresh the combined panel.", delete_after=10)


print("[BoosterHub] Module loaded OK.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BoosterHubCog(bot))
