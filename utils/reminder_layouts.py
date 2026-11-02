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


def host_reminder(pending_count, uncovered, *, pending_slots=()):
    lines = []
    if pending_count:
        lines.append(f"**{pending_count}** hosts still need to complete their availability.\n"
                     "Mark **Available or Unavailable** for slots still needing a confirmed host.")
    if pending_slots:
        lines.append("**Still awaiting responses:** " + ", ".join(text(day, 60) for day in pending_slots)
                     + "\nA volunteer does not mean the host is confirmed.")
    if uncovered:
        lines.append("**Needs coverage:** " + ", ".join(text(day, 60) for day in uncovered))
    if pending_count:
        lines.append("Select **Update availability**, then **My Status** for the exact slots "
                     "still needing **your** answer (shown privately). "
                     "Keep existing answers; confirmed meets need no further response.")
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


def availability_fields(slot, timestamp_for, uid_for, host_for):
    """Bounded host-only proposal summaries, never authoritative assignments."""
    fields = []
    for key, label in (("yes", "✅ Available — proposed hosting"),
                       ("maybe", "❓ Maybe — preferences"),
                       ("no", "❌ Unavailable")):
        entries, seen = [], set()
        for entry in slot.get(key, []):
            uid = str(uid_for(entry))
            if not uid or uid in seen:
                continue
            seen.add(uid)
            entries.append((uid, entry))
        if not entries:
            continue
        lines = []
        for uid, entry in entries[:3]:
            host = discord.utils.remove_markdown(str(host_for(uid) or f"Host {uid}"))
            host = host.split(" · <@", 1)[0]  # readable_host includes a redundant mention
            host = text(discord.utils.escape_mentions(host), 65)
            line = host
            if key != "no":
                ts = None
                if isinstance(entry, dict):
                    try:
                        resolved = timestamp_for(entry)
                        ts = int(resolved) if resolved else None
                    except (TypeError, ValueError, OverflowError, OSError):
                        pass
                    raw = " ".join(str(entry.get(k) or "") for k in ("day", "time")).strip()
                    when = f"<t:{ts}:f>" if ts else text(
                        discord.utils.escape_mentions(raw or "Time not provided"), 95)
                    theme = text(discord.utils.escape_mentions(str(entry.get("theme") or "")), 65)
                    line += f"\n↳ {when}" + (f" · {theme}" if entry.get("theme") else "")
                else:
                    line += "\n↳ Time not provided"
            lines.append(line)
        if len(entries) > 3:
            lines.append(f"+{len(entries) - 3} more · View Responses for the full list")
        fields.append((f"{label} ({len(entries)})", "\n".join(lines)[:1024]))
    return fields


def host_pending_fields(hosts):
    """Show the exact outstanding slots for the tagged hosts, not private proposals."""
    fields, lines, size = [], [], 0
    for name, days in hosts[:50]:
        label = text(discord.utils.escape_mentions(str(name)), 40)
        line = f"**{label}:** " + ", ".join(text(day, 20) for day in days[:3])
        if lines and size + len(line) + 1 > 950:
            fields.append(("Your outstanding responses", "\n".join(lines)))
            lines, size = [], 0
        lines.append(line)
        size += len(line) + 1
    if lines:
        fields.append(("Your outstanding responses", "\n".join(lines)))
    return fields

