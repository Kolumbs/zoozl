"""Slack fixtures for testing."""


def get_slack_event(user, text, channel="C01F9GKQJ8F"):
    """Return slack event."""
    return {
        "event": {
            "client_msg_id": "0c0e0271-6f86-456c-b8a9-ac64cd106a58",
            "type": "message",
            "text": text,
            "user": user,
            "ts": "1663567590.130869",
            "team": "T01FG6C6RT9",
            "blocks": [
                {
                    "type": "rich_text",
                    "block_id": "YxWa",
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": [{"type": "text", "text": text}],
                        }
                    ],
                }
            ],
            "channel": channel,
            "event_ts": "1663567590.130869",
            "channel_type": "im",
        },
    }
