"""Cloudflare Turnstile verification for the feedback form, copied from the website's contact form.

Uses only the standard library so no extra runtime dependency is needed.
"""

import json
import logging
from urllib import parse, request

SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

logger = logging.getLogger(__name__)


def verify_turnstile(
    token: str,
    secret: str,
    remoteip: str | None = None,
    timeout: float = 5.0,
) -> bool:
    """
    Verify a Turnstile token against Cloudflare's siteverify endpoint.

    Fails closed: any missing token, network/timeout error, or malformed
    response returns False rather than letting the submission through.

    :param token: str
    :param secret: str
    :param remoteip: str | None
    :param timeout: float
    :return: bool
    """
    if not token:
        return False

    fields = {"secret": secret, "response": token}
    if remoteip:
        fields["remoteip"] = remoteip
    data = parse.urlencode(fields).encode()

    try:
        with request.urlopen(SITEVERIFY_URL, data=data, timeout=timeout) as resp:
            result = json.loads(resp.read().decode())
    except Exception as e:  # network error, timeout, non-JSON body, etc.
        logger.warning(f"Turnstile verification error: {e}")
        return False

    if not result.get("success"):
        # error-codes distinguishes routine bot failures (missing/invalid-input-response)
        # from misconfiguration (eg invalid-input-secret after a bad deploy).
        logger.info(f"Turnstile verification failed: error-codes={result.get('error-codes')}")
        return False
    return True
