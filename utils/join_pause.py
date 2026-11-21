"""Presentation and narrow entry guards for the existing meet pause.

No role, ticket, verification, or application records are changed here.
"""
import discord

APPLICATION_NOTICE = (
    "Car meet applications are currently on hold. We'll announce when they reopen."
)


def is_paused(client):
    state = getattr(client, "_activity_pause", None)
    return bool(state and state.paused["meets"])


async def allow_application(interaction):
    if not is_paused(interaction.client):
        return True
    sender = (interaction.followup.send if interaction.response.is_done()
              else interaction.response.send_message)
    await sender(
        APPLICATION_NOTICE + " Rules verification and existing tickets remain available.",
        ephemeral=True, allowed_mentions=discord.AllowedMentions.none(),
    )
    return False


def verification_embed(rules_channel_id):
    embed = discord.Embed(
        title="DIFF — Server Verification",
        description=(
            "Rules verification is still available for the DIFF community.\n\n"
            + APPLICATION_NOTICE
        ),
        color=discord.Color.blurple(),
    )
    embed.add_field(
        name="How to verify",
        value=f"Read the rules in <#{rules_channel_id}> and use the **Verify** button there.",
        inline=False,
    )
    embed.add_field(
        name="After verification",
        value="Explore the community and follow staff announcements. "
              "You do not need to apply for car meets to verify.",
        inline=False,
    )
    embed.set_footer(text="Different Meets • Community access")
    return embed
