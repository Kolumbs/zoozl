"""Testcases on WhatsApp server."""

from tests import base as bs, fixtures as fix


class Pong(bs.AbstractWhatsApp):
    """Testcases on WhatsApp server."""

    config_file = "tests/data/whatsapp.toml"

    @fix.patch("zoozl.whatsapp.send_whatsapp")
    async def test_message(self, mock_send_whatsapp):
        """Test WhatsApp inbound message is processed."""
        user = "15550001234"
        text = "pong"
        payload = fix.whatsapp.get_whatsapp_event(user, text)
        status, headers, body = await self.send_whatsapp_event(payload)
        self.assertEqual(status, 200)
        self.assertEqual(body, b"")
        mock_send_whatsapp.assert_called_once()
        call = mock_send_whatsapp.call_args
        self.assertEqual(call.args[0], self.whatsapp_access_token)
        self.assertEqual(call.args[1], self.whatsapp_phone_number_id)
        self.assertEqual(call.args[2], user)

    async def test_verification(self):
        """Test WhatsApp webhook verification GET."""
        challenge = "testchallenge123"
        status, headers, body = await self.send_whatsapp_verification(challenge)
        self.assertEqual(status, 200)
        self.assertEqual(body, challenge.encode("utf-8"))
