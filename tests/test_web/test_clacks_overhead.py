"""Tests for the X-Clacks-Overhead header on the site's responses."""

import pytest
from django.test import Client


@pytest.mark.parametrize(
    ("url", "status"),
    [
        ("/", 200),
        ("/no-such-page/", 404),
    ],
)
def test_clacks_overhead(client: Client, url: str, status: int) -> None:
    response = client.get(url)
    assert response.status_code == status
    assert response.headers["X-Clacks-Overhead"] == "GNU Terry Pratchett"
