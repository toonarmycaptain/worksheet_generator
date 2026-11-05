"""Tests for the site's pages: the home page links to each builder, and each has its forms."""

import re

import pytest
from django.test import Client


def get_links(content: bytes) -> list[str]:
    return re.findall(r'<a href="([^"]+)"', content.decode())


def test_pages(client: Client) -> None:
    """
    Recursively fetch pages, ensuring every link in the site works

    run with uv run pytest -s test_web_pages.py to see successful output
    """
    home = client.get("/")
    assert home.status_code == 200
    links = get_links(home.content)

    for link in links:
        page = client.get(link)
        assert page.status_code == 200, link
        print(f"successfully reached {link=}")
        links += [url for url in get_links(page.content) if url not in links]


@pytest.mark.parametrize(
    ("url", "action", "fields"),
    [
        (
            "/arithmetic/",
            b"/api/worksheets/arithmetic.pdf",
            [
                b"title",
                b"label",
                b"name_line",
                b"problems",
                b"operation",
                b"missing_number",
                b"max_number",
                b"largest_dividend",
                b"largest_divisor",
                b"answer_key",
                b"self_check_tiles",
                b"tile_pattern",  # a radio button for each pattern
                b"tile_pattern",
            ],
        ),
        (
            "/place-value/",
            b"/api/worksheets/place_value.pdf",
            [
                b"title",
                b"label",
                b"name_line",
                b"problems",
                b"given",
                b"asked",
                b"min_number",
                b"max_number",
                b"answer_key",
                b"multiple_choice",
                b"self_check_tiles",
                b"tile_pattern",  # a radio button for each pattern
                b"tile_pattern",
            ],
        ),
    ],
)
def test_builder_page(url: str, action: bytes, fields: list[bytes], client: Client) -> None:
    """
    A builder page has one form, a link home and no seed field.

    The form targets the kind's PDF endpoint, with a field for each option in order and none
    for a seed, since every sheet of a core kind is new.
    """
    content = client.get(url).content

    assert re.findall(rb'action="([^"]+)"', content) == [action]
    assert re.findall(rb'<(?:input|select) [^>]*?name="([^"]+)"', content) == fields
    assert get_links(content) == ["/"]


def test_the_tile_pattern_is_a_pair_of_radio_buttons_that_defaults_to_simple(
    client: Client,
) -> None:
    content = client.get("/arithmetic/").content
    assert re.findall(
        rb'<input type="radio" name="tile_pattern" value="(\w+)"( checked)?>', content
    ) == [(b"simple", b" checked"), (b"complex", b"")]


@pytest.mark.parametrize(
    ("url", "name", "expected"),
    [
        (
            "/arithmetic/",
            "operation",
            [
                (b"add", b" selected", b"Addition"),
                (b"subtract", b"", b"Subtraction"),
                (b"multiply", b"", b"Multiplication"),
                (b"divide", b"", b"Division"),
            ],
        ),
        (
            "/place-value/",
            "given",
            [
                (b"standard", b" selected", b"standard form"),
                (b"expanded", b"", b"expanded form"),
                (b"unit", b"", b"unit form"),
                (b"expanded_notation", b"", b"expanded notation"),
                (b"word", b"", b"word form"),
                (b"mixed", b"", b"mixed"),
            ],
        ),
        (
            "/place-value/",
            "asked",
            [
                (b"standard", b"", b"standard form"),
                (b"expanded", b" selected", b"expanded form"),
                (b"unit", b"", b"unit form"),
                (b"expanded_notation", b"", b"expanded notation"),
                (b"word", b"", b"word form"),
                (b"mixed", b"", b"mixed"),
            ],
        ),
    ],
)
def test_a_dropdown_sends_each_choice_s_id_and_shows_its_name(
    url: str, name: str, expected: list[tuple[bytes, bytes, bytes]], client: Client
) -> None:
    """
    Each dropdown option sends its ID and displays its name, with the expected default selected.

    Operation defaults to addition. From defaults to standard and To to expanded, and each also
    offers mixed.
    """
    content = client.get(url).content
    select = re.search(
        rb'<select name="' + name.encode() + rb'"[^>]*>(.*?)</select>', content, re.S
    )

    assert select is not None
    assert (
        re.findall(rb'<option value="(\w+)"( selected)?>([^<]+)</option>', select.group(1))
        == expected
    )


@pytest.mark.parametrize(
    ("url", "script"),
    [
        ("/arithmetic/", False),
        ("/place-value/", True),
        ("/legacy/", False),
    ],
)
def test_the_place_value_page_keeps_from_and_to_different(
    client: Client, url: str, script: bool
) -> None:
    """
    Only the place-value page includes the script that disables the button while From equals To.

    Whether the script works is checked manually in a browser.
    """
    content = client.get(url).content
    assert (b"function blockSameForms()" in content) is script


@pytest.mark.parametrize(
    ("url", "tiles_script", "titles_script"),
    [
        ("/arithmetic/", True, True),
        ("/place-value/", True, False),
        ("/legacy/", False, False),
    ],
)
def test_ticking_self_check_tiles_asks_for_12_questions(
    client: Client, url: str, tiles_script: bool, titles_script: bool
) -> None:
    """
    The arithmetic and place-value pages include the script that sets problems to 12 for tiles.

    The legacy page has no self-check tiles box, and so no script. Whether the script works is
    checked manually in a browser. Only the arithmetic page has the operation names that its
    other script puts in the title.
    """
    content = client.get(url).content
    assert (b"selfCheckTiles.checked ? 12 : problems.defaultValue" in content) is tiles_script
    assert (b'id="operation-titles"' in content) is titles_script


@pytest.mark.parametrize(
    ("url", "forms"),
    [
        ("/arithmetic/", [(b"/api/worksheets/arithmetic.pdf", b" data-check-first")]),
        ("/place-value/", [(b"/api/worksheets/place_value.pdf", b" data-check-first")]),
        (
            "/legacy/",
            [
                (b"/api/worksheets/block.pdf", b""),
                (b"/api/worksheets/word.pdf", b""),
                (b"/api/worksheets/strip.pdf", b""),
                (b"/api/worksheets/number_line.pdf", b""),
                (b"/api/worksheets/number_line_mc.pdf", b""),
                (b"/api/worksheets/multiplication_mc.pdf", b""),
                (b"/api/worksheets/data_graph.pdf", b""),
                (b"/api/worksheets/data_graph_mc.pdf", b""),
                (b"/api/worksheets/worksheet.pdf", b""),
            ],
        ),
    ],
)
def test_only_core_forms_check_their_options_before_opening_a_tab(
    client: Client, url: str, forms: list[tuple[bytes, bytes]]
) -> None:
    """
    Only core kinds' forms are marked to have their options checked before a tab opens.

    The server rejects invalid options before drawing anything, so the check costs nothing for a
    core kind. A legacy kind draws its PDF immediately, so checking first would draw it twice,
    and its forms are not marked. Whether the script works is checked manually in a browser.
    """
    content = client.get(url).content
    assert re.findall(rb'<form [^>]*?action="([^"]+)"[^>]*?( data-check-first)?>', content) == forms


def test_each_field_carries_its_label_for_the_check_first_messages(client: Client) -> None:
    """
    Each field's data-label supplies the label that begins a rejected option's message.

    The tile pattern's radio buttons have none, as no message names them.
    """
    content = client.get("/arithmetic/").content
    assert re.findall(rb'name="(\w+)" data-label="([^"]+)"', content) == [
        (b"title", b"Title"),
        (b"label", b"Label"),
        (b"name_line", b"Add Name/Date blanks"),
        (b"problems", b"Problems"),
        (b"operation", b"Operation"),
        (b"missing_number", b"Missing number"),
        (b"max_number", b"Largest number"),
        (b"largest_dividend", b"Largest dividend"),
        (b"largest_divisor", b"Largest divisor"),
        (b"answer_key", b"Add an answer key page"),
        (b"self_check_tiles", b"Self-check tile answers"),
    ]


def test_legacy_page(client: Client) -> None:
    """
    The legacy page has a form for each of the nine imported scripts, and a link home.

    The form actions are compared as a whole, in order, so an omitted script, or the arithmetic
    form appearing here, makes them differ.
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
