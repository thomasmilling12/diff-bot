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
BOOSTER_PANEL_CHANNEL = 1485687906382123331   # #welcome-hub
MOD_HUB_CHANNEL_ID    = 1486598266211664003   # staff review channel
LOG_CHANNEL_ID        = 1485265848099799163

# !! Create a "💎 DIFF Booster" role manually in your server,
#    then paste its ID below. Leave 0 to skip auto-role assignment.
BOOSTER_BADGE_ROLE_ID = 990106677330194453

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

        review_embed = discord.Embed(
            title="📸 Booster Showcase Submission",
            description=f"{author.mention} has submitted their build for the DIFF showcase.",
            color=0xF47FFF,
            timestamp=_utc_now(),
        )
        review_embed.add_field(name="🚗 Car",       value=str(self.car_name),    inline=True)
        review_embed.add_field(name="🎨 Color",     value=str(self.color_style), inline=True)
        review_embed.add_field(name="📝 Description",value=str(self.description), inline=False)
        if self.image_link.value:
            review_embed.add_field(name="🖼️ Link", value=str(self.image_link), inline=False)
        review_embed.set_thumbnail(url=author.display_avatar.url)
        review_embed.set_footer(text="Approve or Deny using the buttons below.")

        # Store pending submission in state
        data = _load()
        pending = data.setdefault("pending_showcases", {})
        pending[str(author.id)] = {
            "car":         str(self.car_name),
            "color":       str(self.color_style),
            "description": str(self.description),
            "image":       str(self.image_link) if self.image_link.value else "",
            "avatar":      author.display_avatar.url,
            "username":    str(author),
            "mention":     author.mention,
        }
        _save(data)

        mod_ch = guild.get_channel(MOD_HUB_CHANNEL_ID) if guild else None
        if isinstance(mod_ch, discord.TextChannel):
            try:
                await mod_ch.send(
                    embed=review_embed,
                    view=_ShowcaseReviewView(author.id),
                )
            except Exception as e:
                print(f"[BoosterHub] Showcase send error: {e}")

        await interaction.response.send_message(
            "✅ Your build has been submitted for staff review! "
            "We'll post it to the showcase if approved.",
            ephemeral=True,
        )


# ─── Showcase Staff Review Buttons ───────────────────────────────────────────
class _ApproveBtn(discord.ui.Button):
    def __init__(self, user_id: int):
        super().__init__(
            label="✅ Approve & Post",
            style=discord.ButtonStyle.success,
            custom_id=f"booster_showcase_approve:{user_id}",
        )
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction) -> None:
        data    = _load()
        pending = data.get("pending_showcases", {})
        info    = pending.pop(str(self.user_id), None)

        if not info:
            return await interaction.response.send_message(
                "Submission not found (already processed?)", ephemeral=True
            )
        _save(data)

        showcase_embed = discord.Embed(
            title="📸 DIFF Member Showcase — Booster Feature",
            description=info["description"],
            color=0xF47FFF,
            timestamp=_utc_now(),
        )
        showcase_embed.add_field(name="🚗 Build",  value=info["car"],   inline=True)
        showcase_embed.add_field(name="🎨 Color",  value=info["color"], inline=True)
        showcase_embed.add_field(name="👤 Member", value=info["mention"], inline=False)
        if info.get("image"):
            showcase_embed.set_image(url=info["image"])
        showcase_embed.set_thumbnail(url=info["avatar"])
        showcase_embed.set_footer(text="Different Meets • Booster Showcase")

        guild = interaction.guild
        if guild:
            # Post to welcome-hub or a configured showcase channel
            ch = guild.get_channel(BOOSTER_PANEL_CHANNEL)
            if isinstance(ch, discord.TextChannel):
                try:
                    await ch.send(
                        content=f"💎 Booster Build Showcase — <@{self.user_id}>",
                        embed=showcase_embed,
                        allowed_mentions=discord.AllowedMentions(users=True),
                    )
                except Exception as e:
                    print(f"[BoosterHub] Showcase post error: {e}")

        await interaction.response.edit_message(
            content=f"✅ Showcase approved and posted by {interaction.user.mention}.",
            embed=None,
            view=None,
        )


class _DenyBtn(discord.ui.Button):
    def __init__(self, user_id: int):
        super().__init__(
            label="❌ Deny",
            style=discord.ButtonStyle.danger,
            custom_id=f"booster_showcase_deny:{user_id}",
        )
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction) -> None:
        data    = _load()
        pending = data.get("pending_showcases", {})
        pending.pop(str(self.user_id), None)
        _save(data)
        await interaction.response.edit_message(
            content=f"❌ Showcase denied by {interaction.user.mention}.",
            embed=None,
            view=None,
        )
        try:
            member = interaction.guild.get_member(self.user_id)
            if member:
                await member.send(
                    embed=discord.Embed(
                        title="📸 Showcase Submission Update",
                        description=(
                            "Unfortunately your build showcase submission was not approved at this time.\n"
                            "Feel free to submit again with updated photos or details!"
                        ),
                        color=discord.Color.red(),
                    )
                )
        except Exception:
            pass


class _ShowcaseReviewView(discord.ui.View):
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

    async def _post_or_refresh(self) -> None:
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            print("[BoosterHub] Guild not found.")
            return
        ch = guild.get_channel(BOOSTER_PANEL_CHANNEL)
        if not isinstance(ch, discord.TextChannel):
            try:
                ch = await guild.fetch_channel(BOOSTER_PANEL_CHANNEL)
            except Exception as e:
                print(f"[BoosterHub] Channel fetch error: {e}")
                return

        bot_id = self.bot.user.id if self.bot.user else None

        # Scan channel history for ALL existing booster panels posted by the bot
        found: list[discord.Message] = []
        try:
            async for msg in ch.history(limit=100):
                if msg.author.id != bot_id:
                    continue
                if msg.embeds and "DIFF Booster Perks Hub" in (msg.embeds[0].title or ""):
                    found.append(msg)
        except Exception as e:
            print(f"[BoosterHub] History scan error: {e}")

        if found:
            # Keep the most recent one; delete extras
            found.sort(key=lambda m: m.created_at, reverse=True)
            keeper = found[0]
            for dup in found[1:]:
                try:
                    await dup.delete()
                    print(f"[BoosterHub] Deleted duplicate panel {dup.id}.")
                except Exception:
                    pass
            try:
                await keeper.edit(embed=_panel_embed(), view=self.view)
                _set_panel_id(keeper.id)
                print(f"[BoosterHub] Panel refreshed (msg {keeper.id}).")
                return
            except Exception as e:
                print(f"[BoosterHub] Edit error: {e}")

        # Also try the saved ID as a fallback before posting fresh
        msg_id = _get_panel_id()
        if msg_id:
            try:
                msg = await ch.fetch_message(msg_id)
                await msg.edit(embed=_panel_embed(), view=self.view)
                print(f"[BoosterHub] Panel refreshed via saved ID (msg {msg_id}).")
                return
            except discord.NotFound:
                print("[BoosterHub] Saved ID gone — posting fresh.")
            except Exception as e:
                print(f"[BoosterHub] Saved ID edit error: {e}")

        msg = await ch.send(embed=_panel_embed(), view=self.view)
        _set_panel_id(msg.id)
        print(f"[BoosterHub] Panel posted fresh (msg {msg.id}).")

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
        """Post or refresh the booster hub panel in the welcome-hub channel."""
        await ctx.send("Posting booster panel…", delete_after=5)
        await self._post_or_refresh()
        await ctx.send("Done.", delete_after=8)
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="refresh_booster_panel")
    @commands.has_permissions(administrator=True)
    async def cmd_refresh(self, ctx: commands.Context) -> None:
        """Refresh the booster hub panel embed."""
        await self._post_or_refresh()
        await ctx.send("Booster panel refreshed.", delete_after=8)
        try:
            await ctx.message.delete()
        except Exception:
            pass


print("[BoosterHub] Module loaded OK.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BoosterHubCog(bot))
