"""WhatsApp Cloud API functions to route WhatsApp events for chat completion."""

import json
import logging
from urllib import error, request

from zoozl.chatbot import Message

log = logging.getLogger(__name__)

GRAPH_API_URL = "https://graph.facebook.com/v19.0/{phone_number_id}/messages"


def send_whatsapp(access_token: str, phone_number_id: str, to: str, message: Message):
    """Send a WhatsApp message via WhatsApp Cloud API.

    :param access_token: WhatsApp Cloud API access token
    :param phone_number_id: WhatsApp phone number ID
    :param to: recipient phone number (wa_id)
    :param message: message to send
    """
    url = GRAPH_API_URL.format(phone_number_id=phone_number_id)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    for part in message.parts:
        if not part.binary:
            data = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": part.text},
            }
            req = request.Request(
                url,
                headers=headers,
                data=json.dumps(data).encode(),
                method="POST",
            )
            try:
                with request.urlopen(req):
                    pass
            except error.HTTPError as e:
                log.error("WhatsApp API HTTP error %s sending to %s: %s", e.code, to, e)
            except error.URLError as e:
                log.error("WhatsApp API URL error sending to %s: %s", to, e)
