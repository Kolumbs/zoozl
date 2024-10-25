"""Testcases on slack server."""

from zoozl.chatbot import Message

from tests import base as bs, fixtures as fix


class Pong(bs.AbstractSlack):
    """Testcases on slack server."""

    config_file = "tests/data/slack.toml"

    @fix.patch("zoozl.slack.send_slack")
    async def test(self, mock_send_slack):
        """Test slack message."""
        user = "slack_tester"
        text = "Ābece"
        payload = fix.slack.get_slack_event(user, text)
        status, headers, body = await self.send_slack_event(payload)
        self.assertEqual(status, 200)
        self.assertEqual(body, b"")
        mock_send_slack.assert_called_once()
        self.assert_slack_called_with(
            mock_send_slack,
            self.slack_secret,
            payload["event"]["channel"],
            Message(text, author=self.author),
        )
