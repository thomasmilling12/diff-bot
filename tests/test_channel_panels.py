"""Compact channel panels; offline rendering and edit-in-place behavior."""
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

import discord
from cogs import diff_meet_channel_panel as meet
from cogs import diff_host_team_announcement_panel as host


async def history(messages):
    for message in messages:
        yield message


class ChannelPanelTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot = SimpleNamespace(user=SimpleNamespace(id=10))
        self.guild = SimpleNamespace(get_role=lambda rid: SimpleNamespace(mention="<@&100>"))
        self.channel = Mock(spec=discord.TextChannel)
        self.channel.guild = self.guild
        self.channel.send = AsyncMock()
        self.bot.get_channel = lambda cid: self.channel

    def message(self, footer):
        embed = discord.Embed(title="Old panel").set_footer(text=footer)
        return SimpleNamespace(author=SimpleNamespace(id=10), embeds=[embed],
                               edit=AsyncMock(), delete=AsyncMock())

    async def test_meet_card_short_and_access_retained(self):
        embed = meet.DiffMeetChannelPanel(self.bot)._build_embed(self.guild)
        self.assertLess(len(embed), 500)
        self.assertIn("<@&100>", embed.description)
        self.assertIn("hosts and staff only", embed.description)
        self.assertFalse(embed.fields)
        self.assertEqual(embed.footer.text, meet.PANEL_FOOTER)
        self.assertFalse(embed.image.url)

    async def test_old_and_new_meet_cards_refresh_in_place(self):
        for tag in (meet.PANEL_TAG, meet.PANEL_FOOTER):
            message = self.message(tag)
            self.channel.history.side_effect = lambda **kw: history([message])
            result = await meet.DiffMeetChannelPanel(self.bot)._post_or_refresh(self.channel)
            self.assertIs(result, message)
            message.edit.assert_awaited_once()
        self.channel.send.assert_not_awaited()

    async def test_failed_meet_edit_does_not_duplicate(self):
        message = self.message(meet.PANEL_TAG)
        message.edit.side_effect = discord.Forbidden(SimpleNamespace(status=403, reason="Forbidden"), "denied")
        self.channel.history.side_effect = lambda **kw: history([message])
        await meet.DiffMeetChannelPanel(self.bot)._post_or_refresh(self.channel)
        self.channel.send.assert_not_awaited()

    async def test_host_empty_and_active_summaries(self):
        data = host.ensure_data_shape({})
        embed = host.build_unified_host_team_embed(data)
        self.assertEqual(len(embed.fields), 1)
        self.assertIn("No open announcements", embed.fields[0].value)
        self.assertLess(len(embed), 500)
        data["announcements"] = {"a": {"closed": False}, "b": {"closed": True}}
        data["host_stats"] = {"1": {"warning_count": 2, "flagged": True}}
        embed = host.build_unified_host_team_embed(data)
        self.assertEqual(embed.fields[0].value,
                         "**1** open announcement · **2** warnings · **1** flagged host")
        self.assertTrue(embed.footer.text.startswith(host.UNIFIED_HOST_TEAM_TAG))

    async def test_host_links_and_persistent_menu_retained(self):
        view = host.UnifiedHostTeamView()
        self.assertTrue(view.is_persistent())
        self.assertEqual([c.url for c in view.children[:6]], [link[2] for link in host._CHANNEL_LINKS])
        self.assertEqual([c.row for c in view.children], [0, 0, 0, 1, 1, 1, 2])
        self.assertEqual(len(view.to_components()), 3)
        self.assertEqual([o.value for o in view.children[-1].options],
                         ["create_ann", "view_stats", "view_perf", "view_ignored", "refresh"])

    async def test_host_refresh_acknowledges_before_network_work(self):
        interaction = SimpleNamespace(
            user=Mock(spec=discord.Member), client=self.bot,
            response=SimpleNamespace(defer=AsyncMock(), send_message=AsyncMock()),
            followup=SimpleNamespace(send=AsyncMock()),
        )
        select = host._HostTeamActionSelect()
        select._values = ["refresh"]
        async def refresh(bot):
            interaction.response.defer.assert_awaited_once_with(ephemeral=True)
        with patch.object(host, "user_is_manager", return_value=True), \
                patch.object(host, "ensure_unified_host_team_panel", side_effect=refresh) as work:
            await select.callback(interaction)
            work.assert_awaited_once()
            interaction.followup.send.assert_awaited_once()
        with patch.object(host, "user_is_manager", return_value=False), \
                patch.object(host, "ensure_unified_host_team_panel") as work:
            await select.callback(interaction)
            work.assert_not_awaited()

    async def test_existing_host_panel_edits_in_place(self):
        message = self.message(host.UNIFIED_HOST_TEAM_TAG + " | old footer")
        self.channel.history.side_effect = lambda **kw: history([message])
        with patch.object(host, "load_data", return_value={}):
            await host.ensure_unified_host_team_panel(self.bot)
        message.edit.assert_awaited_once()
        self.channel.send.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
