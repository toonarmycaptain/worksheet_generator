"""The home page links to a page for each builder, and each page has its own forms."""

import re

from django.test import Client


def get_links(content: bytes) -> list[str]:
    return re.findall(r'<a href="([^"]+)"', content.decode())


def test_pages(client: Client) -> None:
    """
    Recursively fetch pages, ensuring every link in the site works

    run with uv run pytest -s test_web_pages.py so see successful output
    """
    home = client.get("/")
    assert home.status_code == 200
    links = get_links(home.content)

    for link in links:
        page = client.get(link)
        assert page.status_code == 200, link
        print(f"successfully reached {link=}")
        links += [url for url in get_links(page.content) if url not in links]


def test_arithmetic_page(client: Client) -> None:
    """The arithmetic page has its one form and a link back home, and no seed field.

    The form posts to the arithmetic PDF endpoint, with a field for each option in order and
    none for a seed, since every arithmetic sheet is new.
    """
    content = client.get("/arithmetic/").content

    assert re.findall(rb'action="([^"]+)"', content) == [b"/api/worksheets/arithmetic.pdf"]
    assert re.findall(rb'<(?:input|select) [^>]*?name="([^"]+)"', content) == [
        b"title",
        b"label",
        b"problems",
        b"operation",
        b"max_number",
        b"answer_key",
    ]
    assert get_links(content) == ["/"]


def test_legacy_page(client: Client) -> None:
    """The legacy page has a form for each of the nine imported scripts, and a link back home.

    The list of form actions is the whole list, in order, so a script left out, or the
    arithmetic form appearing here, makes it differ.
    """
    content = client.get("/legacy/").content

    assert re.findall(rb'action="([^"]+)"', content) == [
        b"/api/worksheets/block.pdf",
        b"/api/worksheets/word.pdf",
        b"/api/worksheets/strip.pdf",
        b"/api/worksheets/number_line.pdf",
        b"/api/worksheets/number_line_mc.pdf",
        b"/api/worksheets/multiplication_mc.pdf",
        b"/api/worksheets/data_graph.pdf",
        b"/api/worksheets/data_graph_mc.pdf",
        b"/api/worksheets/worksheet.pdf",
    ]
    assert get_links(content) == ["/"]
