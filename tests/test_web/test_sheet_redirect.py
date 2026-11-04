"""
Tests for the redirect that gives a core kind's request a ``sheet`` token.

A core kind's sheet is chosen by its ``sheet`` token rather than a seed. A request without one
is redirected to the same URL with a random token added.
"""

import secrets

import pytest
from django.test import Client


@pytest.mark.parametrize(
    ("url", "location"),
    [
        ("/api/worksheets/arithmetic.pdf", "/api/worksheets/arithmetic.pdf?sheet=1ab2c3"),
        (
            "/api/worksheets/arithmetic.pdf?operation=multiply&problems=2",
            "/api/worksheets/arithmetic.pdf?operation=multiply&problems=2&sheet=1ab2c3",
        ),
        (
            "/api/worksheets/arithmetic.pdf?title=Times+Tables&label=Day+2",
            "/api/worksheets/arithmetic.pdf?title=Times+Tables&label=Day+2&sheet=1ab2c3",
        ),
        # an empty token counts as none
        (
            "/api/worksheets/arithmetic.pdf?problems=3&sheet=",
            "/api/worksheets/arithmetic.pdf?problems=3&sheet=1ab2c3",
        ),
        (
            "/api/worksheets/place_value.pdf?given=word",
            "/api/worksheets/place_value.pdf?given=word&sheet=1ab2c3",
        ),
    ],
)
def test_a_request_without_a_sheet_is_redirected(
    url: str, location: str, client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    A request without a ``sheet`` token is redirected to the same URL with a random token added.

    ``token_hex`` is fixed so the target URL is known. The options keep their order, and an
    empty ``sheet`` is replaced. The redirect is ``no-store``: if it were cached, everyone
    requesting those options would be sent to the same token, and so to the same sheet.
    """
    monkeypatch.setattr(secrets, "token_hex", lambda nbytes: "1ab2c3")

    response = client.get(url)

    assert response.status_code == 302
    assert response["Location"] == location
    assert response["Cache-Control"] == "no-store"
