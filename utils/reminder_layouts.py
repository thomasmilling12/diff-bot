"""Compact Discord reminder cards shared by channel posts and DMs."""
from datetime import datetime, timezone

import discord


def text(value, limit=180):
    """Keep user-supplied names readable without allowing markdown/field overflow."""
    return discord.utils.escape_markdown(str(value or "TBD"))[:limit]


def open_panel(label, url):
    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(label=label, style=discord.ButtonStyle.link, url=url))
    return view


def host_name(guild, host_id):
    try:
        member = guild.get_member(int(host_id)) if host_id else None
    except (TypeError, ValueError):
        member = None
    return text(member.display_name) if member else "Host to be confirmed"


def schedule_card(meets, pending_count, *, personal=False):
    """meets: (number, class, timestamp, readable host) tuples."""
    embed = discord.Embed(
        title="Roll call • Schedule ready",
        description="Choose **Going, Maybe, or Out** for each upcoming meet.",
        color=0x57F287, timestamp=datetime.now(timezone.utc),
    )
    for number, theme, ts, host in meets[:3]:
        embed.add_field(
            name=f"Meet {number} · {text(theme, 160)}",
            value=f"<t:{ts}:F>\nHost: {host}", inline=False,
        )
    if pending_count and not personal:
        embed.add_field(name="Awaiting a response",
                        value=f"**{pending_count}** crew members haven't answered any upcoming meet.",
                        inline=False)
    embed.set_footer(text="DIFF • Roll call")
    return embed


def meet_reminder(number, theme, ts, host, yes_count, maybe_count, pending_count):
    embed = discord.Embed(
        title=f"Meet {number} • {text(theme, 180)}",
        description=f"**Starts <t:{ts}:R>**\n<t:{ts}:F>\nHost: {host}",
        color=0x5865F2,
    )
    embed.add_field(name="RSVPs",
                    value=f"**{yes_count}** going · **{maybe_count}** maybe · **{pending_count}** no response",
                    inline=False)
    embed.add_field(name="Before the meet",
                    value="Going? Be ready on PSN.\nMaybe or no response? Update your RSVP below.",
                    inline=False)
    embed.set_footer(text="DIFF • Meet reminder")
    return embed


def host_reminder(pending_count, uncovered):
    lines = []
    if pending_count:
        lines.append(f"**{pending_count}** hosts still need to complete their availability.\n"
                     "Mark **Available or Unavailable** for each remaining slot.")
    if uncovered:
        lines.append("**Needs coverage:** " + ", ".join(text(day, 60) for day in uncovered))
    embed = discord.Embed(
        title="Hosts • Availability needed", description="\n\n".join(lines),
        color=0xFEE75C, timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="DIFF • Host schedule")
    return embed


def color_card(pending, *, reminder=False):
    try:
        color = discord.Color.from_str(pending.get("hex_code") or "#5865F2")
    except (ValueError, TypeError):
        color = discord.Color.blurple()
    done = pending.get("done") and not pending.get("expired")
    embed = discord.Embed(
        title="Crew color • Updated" if done else "Crew color • Update needed",
        description=(
            f"**{text(pending.get('color_name'))}** · `{text(pending.get('hex_code'), 20)}`\n\n"
            + ("Confirmed on Rockstar Social Club. Reminders stopped." if done else
               "Apply this color on **Rockstar Social Club**, then select **Mark updated**.")
        ),
        color=color, timestamp=datetime.now(timezone.utc),
    )
    if pending.get("image_url"):
        embed.set_thumbnail(url=pending["image_url"])
    embed.set_footer(text="DIFF • Crew color" + (" • Reminder every 12h until confirmed" if reminder and not done else ""))
    return embed
