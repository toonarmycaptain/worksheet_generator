"""
Tests for the feedback form: the page, storing a message, emailing it, and the Turnstile check.

Neither the mailer Worker nor Cloudflare's siteverify is called: ``urlopen`` is replaced, so a
test reads what would have been sent.
"""

import json
import re
from io import BytesIO
from threading import Thread
from typing import Any
from urllib import request
from urllib.error import HTTPError, URLError

import pytest
from django.test import Client
from feedback.mailer import compose_email, send_email, send_email_async
from feedback.models import Message
from feedback.turnstile import verify_turnstile
from pytest_django.fixtures import Settings


def urlopen_returns(
    monkeypatch: pytest.MonkeyPatch, reply: bytes | Exception
) -> list[request.Request]:
    """
    Make ``urllib.request.urlopen`` return ``reply`` as the response body, or raise it if it is
    an exception, and return the request of each call.

    A call made with a URL and ``data`` is recorded as a ``Request`` of them, so a test reads
    what was sent the same way for the mailer and for Turnstile.
    """
    sent: list[request.Request] = []

    def urlopen(
        url: str | request.Request, data: bytes | None = None, timeout: float | None = None
    ) -> BytesIO:
        sent.append(url if isinstance(url, request.Request) else request.Request(url, data))
        if isinstance(reply, Exception):
            raise reply
        return BytesIO(reply)

    monkeypatch.setattr(request, "urlopen", urlopen)
    return sent


@pytest.mark.parametrize(
    ("url", "page_field"),
    [
        (
            "/feedback/?from=/place-value/",
            b'<input type="hidden" name="page" value="/place-value/" id="id_page">',
        ),
        ("/feedback/", b'<input type="hidden" name="page" id="id_page">'),
    ],
)
def test_feedback_page(url: str, page_field: bytes, client: Client) -> None:
    """The page's hidden ``page`` field holds the page named by ``?from=``, if there is one."""
    response = client.get(url)

    assert response.status_code == 200
    assert page_field in response.content


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("url", "data", "captcha_passed", "redirects", "errors", "shown", "stored"),
    [
        (
            "/feedback/?from=/place-value/",
            {
                "name": "Ann",
                "email": "ann@example.com",
                "text": "More fractions, please.",
                "page": "/place-value/",
            },
            True,
            [("/feedback/", 302)],
            {},
            [b"Thankyou!", b"NB: I endeavour to respond within 48 hours."],
            [
                {
                    "name": "Ann",
                    "email": "ann@example.com",
                    "text": "More fractions, please.",
                    "page": "/place-value/",
                    "captcha_passed": True,
                    "email_sent": True,
                }
            ],
        ),
        # failing Turnstile: stored but not emailed, and the sender isn't told
        (
            "/feedback/?from=/place-value/",
            {
                "name": "Ann",
                "email": "ann@example.com",
                "text": "More fractions, please.",
                "page": "/place-value/",
            },
            False,
            [("/feedback/", 302)],
            {},
            [b"Thankyou!", b"NB: I endeavour to respond within 48 hours."],
            [
                {
                    "name": "Ann",
                    "email": "ann@example.com",
                    "text": "More fractions, please.",
                    "page": "/place-value/",
                    "captcha_passed": False,
                    "email_sent": False,
                }
            ],
        ),
        # a second message, sent from the plain URL the first one redirected to
        (
            "/feedback/",
            {"name": "Bo", "email": "bo@example.com", "text": "The PDF is blank.", "page": ""},
            True,
            [("/feedback/", 302)],
            {},
            [b"Thankyou!", b"NB: I endeavour to respond within 48 hours."],
            [
                {
                    "name": "Bo",
                    "email": "bo@example.com",
                    "text": "The PDF is blank.",
                    "page": "",
                    "captcha_passed": True,
                    "email_sent": True,
                }
            ],
        ),
        (
            "/feedback/?from=/place-value/",
            {
                "name": "Ann",
                "email": "ann.example.com",
                "text": "More fractions, please.",
                "page": "/place-value/",
            },
            True,
            [],
            {"email": ["Enter a valid email address."]},
            [],
            [],
        ),
        (
            "/feedback/?from=/place-value/",
            {"name": "Ann", "email": "ann@example.com", "text": "", "page": "/place-value/"},
            True,
            [],
            {"text": ["This field is required."]},
            [],
            [],
        ),
        (
            "/feedback/?from=/place-value/",
            {
                "name": "",
                "email": "ann@example.com",
                "text": "More fractions, please.",
                "page": "/place-value/",
            },
            True,
            [],
            {"name": ["This field is required."]},
            [],
            [],
        ),
    ],
)
def test_send_feedback(
    url: str,
    data: dict[str, str],
    captcha_passed: bool,
    redirects: list[tuple[str, int]],
    errors: dict[str, list[str]],
    shown: list[bytes],
    stored: list[dict[str, Any]],
    client: Client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    A valid message is stored, and emailed if it passed Turnstile, then the sender is redirected
    to an empty form with the thank-you messages below it. An invalid one is shown again with
    its errors, and nothing is stored.

    Turnstile's verdict is fixed, and ``send_email_async`` marks the message sent, as a
    successful send does, so the stored rows show which messages were emailed.
    """
    monkeypatch.setattr("feedback.views.verify_turnstile", lambda token, secret: captcha_passed)
    monkeypatch.setattr(
        "feedback.views.send_email_async",
        lambda message: Message.objects.filter(pk=message.pk).update(email_sent=True),
    )

    response = client.post(url, data, follow=True)
    below_form = re.findall(rb"<p>(.*?)</p>", response.content.partition(b"</form>")[2])

    assert response.redirect_chain == redirects
    assert (response.context["form"].errors, below_form) == (errors, shown)
    fields = ("name", "email", "text", "page", "captcha_passed", "email_sent")
    assert list(Message.objects.values(*fields)) == stored


@pytest.mark.parametrize(
    ("name", "email", "text", "page", "subject", "body"),
    [
        (
            "Ann",
            "ann@example.com",
            "More fractions, please.",
            "/place-value/",
            "Feedback from Ann",
            "More fractions, please.\n\nfrom Ann\nann@example.com\nSent from: /place-value/\n",
        ),
        # no page: no "Sent from" line
        (
            "Bo",
            "bo@example.com",
            "The PDF is blank.",
            "",
            "Feedback from Bo",
            "The PDF is blank.\n\nfrom Bo\nbo@example.com\n",
        ),
    ],
)
def test_compose_email(
    name: str, email: str, text: str, page: str, subject: str, body: str
) -> None:
    """The email's subject names the sender; its body is the message, the sender and the page."""
    message = Message(name=name, email=email, text=text, page=page)

    assert compose_email(message) == (subject, body)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("reply", "email_sent"),
    [
        (b'{"messageId": "m-123"}', True),
        # the Worker refuses the request, as for a wrong key
        (HTTPError("https://mailer.example/send", 401, "Unauthorized", None, None), False),
        (URLError("timed out"), False),
        # a reply without a message id isn't taken as sent
        (b'{"error": "missing subject"}', False),
        (b"<html>Bad gateway</html>", False),
    ],
)
def test_send_email(
    reply: bytes | Exception,
    email_sent: bool,
    monkeypatch: pytest.MonkeyPatch,
    settings: Settings,
) -> None:
    """
    The message is POSTed to the mailer Worker with its key, and marked emailed only if the Worker
    replies with a message id. A failed send leaves it stored and unmarked.
    """
    settings.MAILER_URL = "https://mailer.example/send"
    settings.MAILER_KEY = "test-key"
    sent = urlopen_returns(monkeypatch, reply)
    message = Message.objects.create(
        name="Ann", email="ann@example.com", text="More fractions, please.", page="/place-value/"
    )

    send_email(message)

    assert [
        (each.full_url, each.get_method(), each.headers, json.loads(each.data)) for each in sent
    ] == [
        (
            "https://mailer.example/send",
            "POST",
            {
                "Authorization": "Bearer test-key",
                "Content-type": "application/json",
                "User-agent": "worksheet-generator feedback form",
            },
            {
                "site": "worksheets",
                "subject": "Feedback from Ann",
                "text": (
                    "More fractions, please.\n\nfrom Ann\nann@example.com\n"
                    "Sent from: /place-value/\n"
                ),
                "reply_to": "ann@example.com",
            },
        )
    ]
    assert Message.objects.get(pk=message.pk).email_sent == email_sent


def test_send_email_async(monkeypatch: pytest.MonkeyPatch) -> None:
    """The message is handed to ``send_email`` on a background thread."""
    emailed: list[Message] = []
    monkeypatch.setattr("feedback.mailer.send_email", emailed.append)
    started: list[Thread] = []

    def thread(**kwargs: Any) -> Thread:
        started.append(Thread(**kwargs))
        return started[-1]

    monkeypatch.setattr("feedback.mailer.Thread", thread)
    message = Message(name="Ann", email="ann@example.com", text="More fractions, please.")

    send_email_async(message)
    started[0].join()

    assert emailed == [message]


@pytest.mark.parametrize(
    ("token", "remoteip", "reply", "verified", "sent"),
    [
        (
            "tok",
            None,
            b'{"success": true}',
            True,
            [
                (
                    "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                    b"secret=s3cret&response=tok",
                )
            ],
        ),
        (
            "tok",
            "203.0.113.5",
            b'{"success": true}',
            True,
            [
                (
                    "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                    b"secret=s3cret&response=tok&remoteip=203.0.113.5",
                )
            ],
        ),
        # a failed check, an unreachable Cloudflare or a garbled reply all fail closed
        (
            "tok",
            None,
            b'{"success": false, "error-codes": ["invalid-input-response"]}',
            False,
            [
                (
                    "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                    b"secret=s3cret&response=tok",
                )
            ],
        ),
        (
            "tok",
            None,
            URLError("timed out"),
            False,
            [
                (
                    "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                    b"secret=s3cret&response=tok",
                )
            ],
        ),
        (
            "tok",
            None,
            b"<html>Bad gateway</html>",
            False,
            [
                (
                    "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                    b"secret=s3cret&response=tok",
                )
            ],
        ),
        # no token: Cloudflare isn't asked
        ("", None, b'{"success": true}', False, []),
    ],
)
def test_verify_turnstile(
    token: str,
    remoteip: str | None,
    reply: bytes | Exception,
    verified: bool,
    sent: list[tuple[str, bytes]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A token passes only if Cloudflare's siteverify says so; anything else fails closed."""
    requests = urlopen_returns(monkeypatch, reply)

    assert verify_turnstile(token, "s3cret", remoteip) == verified
    assert [(each.full_url, each.data) for each in requests] == sent


@pytest.mark.parametrize(
    ("name", "text", "shown"),
    [
        ("Ann", "More fractions, please.", "Ann: More fractions, please."),
        # cut to its first 50 characters
        (
            "Bo",
            "The strip diagram sheet prints the bars too far apart to read.",
            "Bo: The strip diagram sheet prints the bars too far ap",
        ),
    ],
)
def test_message_str(name: str, text: str, shown: str) -> None:
    """A message is named in the admin by its sender and the start of its text."""
    assert str(Message(name=name, email="ann@example.com", text=text)) == shown
