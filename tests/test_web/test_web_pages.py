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
    ("url", "actions", "fields"),
    [
        (
            "/basic-operations/",
            [
                b"/api/worksheets/basic_operations.pdf",
                b"/api/worksheets/word_problems.pdf",
                b"/api/worksheets/base_ten_blocks.pdf",
            ],
            [
                b"title",
                b"label",
                b"name_line",
                b"problems",
                b"operations",  # a checkbox for each operation
                b"operations",
                b"operations",
                b"operations",
                b"missing_number",
                b"max_number",
                b"largest_dividend",
                b"largest_divisor",
                b"answer_key",
                b"self_check_tiles",
                b"tile_pattern",  # a radio button for each pattern
                b"tile_pattern",
                # the word problems form
                b"title",
                b"label",
                b"name_line",
                b"problems",
                b"operations",  # a checkbox for each operation
                b"operations",
                b"operations",
                b"operations",
                b"max_number",
                b"representation",
                b"no_hints",
                b"black_and_white",
                b"answer_key",
                b"self_check_tiles",
                b"tile_pattern",
                b"tile_pattern",
                # the base-ten blocks form
                b"title",
                b"label",
                b"name_line",
                b"problems",
                b"questions",  # a checkbox for each type of question
                b"questions",
                b"questions",
                b"min_number",
                b"max_number",
                b"regrouping",  # a radio button for each choice
                b"regrouping",
                b"regrouping",
                b"black_and_white",
                b"answer_key",
                b"self_check_tiles",
                b"tile_pattern",
                b"tile_pattern",
            ],
        ),
        (
            "/place-value/",
            [b"/api/worksheets/place_value.pdf"],
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
def test_builder_page(url: str, actions: list[bytes], fields: list[bytes], client: Client) -> None:
    """
    A builder page has a form for each of its kinds, a link home and no seed field.

    Each form targets its kind's PDF endpoint, with a field for each option in order and none
    for a seed, since every sheet of a core kind is new.
    """
    content = client.get(url).content

    assert re.findall(rb'action="([^"]+)"', content) == actions
    assert re.findall(rb'<(?:input|select) [^>]*?name="([^"]+)"', content) == fields
    assert get_links(content) == ["/"]


@pytest.mark.parametrize(
    ("url", "name", "expected"),
    [
        # simple by default, on each form with tiles
        (
            "/basic-operations/",
            "tile_pattern",
            [
                (b"simple", b" checked", b"simple"),
                (b"complex", b"", b"complex"),
                # the word problems form
                (b"simple", b" checked", b"simple"),
                (b"complex", b"", b"complex"),
                # the base-ten blocks form
                (b"simple", b" checked", b"simple"),
                (b"complex", b"", b"complex"),
            ],
        ),
        (
            "/place-value/",
            "tile_pattern",
            [(b"simple", b" checked", b"simple"), (b"complex", b"", b"complex")],
        ),
        # none, some, all, with mixed by default
        (
            "/basic-operations/",
            "regrouping",
            [
                (b"never", b"", b"Never"),
                (b"mixed", b" checked", b"Mixed"),
                (b"always", b"", b"Always"),
            ],
        ),
    ],
)
def test_radio_buttons_send_each_choice_s_id_and_show_its_name(
    url: str, name: str, expected: list[tuple[bytes, bytes, bytes]], client: Client
) -> None:
    """Each radio button sends its ID when chosen and displays its name, with the default chosen."""
    content = client.get(url).content
    assert (
        re.findall(
            rb'<input type="radio" name="'
            + name.encode()
            + rb'" value="(\w+)"( checked)?> ([^<]+)<',
            content,
        )
        == expected
    )


@pytest.mark.parametrize(
    ("url", "name", "expected"),
    [
        (
            "/basic-operations/",
            "representation",
            [
                (b"strip", b" selected", b"Strip Diagrams"),
                (b"none", b"", b"Text Only"),
                (b"number_line", b"", b"Number Lines"),
                (b"blocks", b"", b"Base-Ten Blocks"),
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

    Representation defaults to strip diagrams, and also offers text only. From defaults to standard
    and To to expanded, and each also offers mixed.
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
    ("url", "action", "name", "expected", "all_box"),
    [
        # addition by default, with an All box for the four
        (
            "/basic-operations/",
            b"/api/worksheets/basic_operations.pdf",
            "operations",
            [
                (b"add", b" checked", b"Addition"),
                (b"subtract", b"", b"Subtraction"),
                (b"multiply", b"", b"Multiplication"),
                (b"divide", b"", b"Division"),
            ],
            True,
        ),
        # addition and subtraction by default, with an All box for the four
        (
            "/basic-operations/",
            b"/api/worksheets/word_problems.pdf",
            "operations",
            [
                (b"add", b" checked", b"Addition"),
                (b"subtract", b" checked", b"Subtraction"),
                (b"multiply", b"", b"Multiplication"),
                (b"divide", b"", b"Division"),
            ],
            True,
        ),
        # every type of question by default, with an All box for the three
        (
            "/basic-operations/",
            b"/api/worksheets/base_ten_blocks.pdf",
            "questions",
            [
                (b"write_number", b" checked", b"Write the number"),
                (b"add", b" checked", b"Add"),
                (b"subtract", b" checked", b"Subtract"),
            ],
            True,
        ),
    ],
)
def test_a_checkbox_group_sends_each_ticked_choice_s_id_and_shows_its_name(
    url: str,
    action: bytes,
    name: str,
    expected: list[tuple[bytes, bytes, bytes]],
    all_box: bool,
    client: Client,
) -> None:
    """
    Each checkbox in a group sends its ID when ticked and displays its name, with the defaults
    ticked.

    A group of more than two also has an All box, which has no name, so it is never sent.
    Whether its script works is checked manually in a browser.
    """
    content = client.get(url).content
    form = re.search(rb'<form [^>]*?action="' + action + rb'".*?</form>', content, re.S)

    assert form is not None
    assert (
        re.findall(
            rb'<input type="checkbox" name="'
            + name.encode()
            + rb'" value="(\w+)"( checked)?> ([^<]+)<',
            form.group(),
        )
        == expected
    )
    assert (b"data-all" in form.group()) is all_box


@pytest.mark.parametrize(
    ("url", "script"),
    [
        ("/basic-operations/", False),
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
    ("url", "tiles_script", "titles_script", "representation_script"),
    [
        ("/basic-operations/", True, True, True),
        ("/place-value/", True, False, False),
        ("/legacy/", False, False, False),
    ],
)
def test_ticking_self_check_tiles_asks_for_12_questions(
    client: Client, url: str, tiles_script: bool, titles_script: bool, representation_script: bool
) -> None:
    """
    The basic operations and place-value pages include the script that sets problems to 12 for
    tiles.

    The legacy page has no self-check tiles box, and so no script. Whether the script works is
    checked manually in a browser. Only the basic operations page has the operation names that its
    other script puts in the title, and the word problems titles that its representation script puts
    in the title (that script also hides "Leave out the hints" for text only).
    """
    content = client.get(url).content
    assert (b"selfCheckTiles.checked ? 12 : problems.defaultValue" in content) is tiles_script
    assert (b'id="operation-titles"' in content) is titles_script
    assert (b'id="representation-titles"' in content) is representation_script


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "/basic-operations/",
            b'<script id="representation-operations" type="application/json">'
            b'{"strip": ["add", "subtract", "multiply", "divide"], '
            b'"none": ["add", "subtract", "multiply", "divide"], '
            b'"number_line": ["add", "subtract"], '
            b'"blocks": ["add", "subtract"]}</script>',
        ),
        ("/place-value/", None),
    ],
)
def test_the_representation_script_greys_out_the_operations_a_representation_cannot_show(
    client: Client, url: str, expected: bytes | None
) -> None:
    """
    The basic operations page has the operations each representation can show, for the
    representation script to grey out the others. Whether the script works is checked manually in a
    browser.
    """
    found = re.search(
        rb'<script id="representation-operations".*?</script>', client.get(url).content
    )
    assert (found.group() if found else None) == expected


@pytest.mark.parametrize(
    ("url", "forms"),
    [
        (
            "/basic-operations/",
            [
                (b"/api/worksheets/basic_operations.pdf", b" data-check-first"),
                (b"/api/worksheets/word_problems.pdf", b" data-check-first"),
                (b"/api/worksheets/base_ten_blocks.pdf", b" data-check-first"),
            ],
        ),
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

    The tile pattern's radio buttons and the operations' checkboxes have none, as no message
    names them.
    """
    content = client.get("/basic-operations/").content
    assert re.findall(rb'name="(\w+)" data-label="([^"]+)"', content) == [
        (b"title", b"Title"),
        (b"label", b"Label"),
        (b"name_line", b"Add Name/Date blanks"),
        (b"problems", b"Problems"),
        (b"missing_number", b"Missing number"),
        (b"max_number", b"Largest number"),
        (b"largest_dividend", b"Largest dividend"),
        (b"largest_divisor", b"Largest divisor"),
        (b"answer_key", b"Add an answer key page"),
        (b"self_check_tiles", b"Self-check tile answers"),
        # the word problems form
        (b"title", b"Title"),
        (b"label", b"Label"),
        (b"name_line", b"Add Name/Date blanks"),
        (b"problems", b"Problems"),
        (b"max_number", b"Largest number"),
        (b"representation", b"Representation"),
        (b"no_hints", b"Leave out the hints"),
        (b"black_and_white", b"Black and white blocks"),
        (b"answer_key", b"Add an answer key page"),
        (b"self_check_tiles", b"Self-check tile answers"),
        # the base-ten blocks form
        (b"title", b"Title"),
        (b"label", b"Label"),
        (b"name_line", b"Add Name/Date blanks"),
        (b"problems", b"Problems"),
        (b"min_number", b"Smallest number"),
        (b"max_number", b"Largest number"),
        (b"black_and_white", b"Black and white blocks"),
        (b"answer_key", b"Add an answer key page"),
        (b"self_check_tiles", b"Self-check tile answers"),
    ]


def test_legacy_page(client: Client) -> None:
    """
    The legacy page has a form for each of the nine imported scripts, and a link home.

    The form actions are compared as a whole, in order, so an omitted script, or the basic
    operations form appearing here, makes them differ.
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
