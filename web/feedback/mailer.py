"""Email each feedback message to me through the contact-mailer Cloudflare Worker."""

import json
import logging
from threading import Thread
from urllib import request

from django.conf import settings
from django.db import connections

from .models import Message

logger = logging.getLogger(__name__)

MAILER_TIMEOUT = 10  # seconds


def compose_email(message: Message) -> tuple[str, str]:
    """Return the subject and body of the notification email for a message."""
    subject = f"Feedback from {message.name}"
    body = f"{message.text}\n\nfrom {message.name}\n{message.email}\n"
    if message.page:
        body += f"Sent from: {message.page}\n"
    return subject, body


def send_email(message: Message) -> None:
    """
    POST the message to the mailer Worker, and mark it emailed if the Worker accepts it.

    A failed send is logged and leaves email_sent False; the message stays stored either way.
    """
    subject, body = compose_email(message)
    payload = json.dumps(
        {"site": "worksheets", "subject": subject, "text": body, "reply_to": message.email}
    ).encode()
    mailer_request = request.Request(
        settings.MAILER_URL,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {settings.MAILER_KEY}",
            "Content-Type": "application/json",
            # Cloudflare can reject the default Python-urllib agent
            "User-Agent": "worksheet-generator feedback form",
        },
    )
    try:
        with request.urlopen(mailer_request, timeout=MAILER_TIMEOUT) as response:
            mailer_id = json.load(response)["messageId"]
        Message.objects.filter(pk=message.pk).update(email_sent=True)
        logger.info(f"Feedback email sent for message {message.pk} (mailer id {mailer_id})")
    except Exception:
        logger.exception(f"Feedback email send failed for message {message.pk}")


def send_email_async(message: Message) -> None:
    """Send the email on a background thread, so the page doesn't wait for the mailer."""
    Thread(target=_send_in_thread, args=(message,), daemon=True).start()


def _send_in_thread(message: Message) -> None:
    try:
        send_email(message)
    finally:
        connections.close_all()  # a thread must close the database connections it opened
