"""Tests for the site's pages: every link works, and each sheet's page has its form."""

import re

import pytest
from django.test import Client


def get_links(content: bytes) -> list[str]:
    return re.findall(r'<a href="([^"]+)"', content.decode())


def test_pages(client: Client) -> None:
    """
    Recursively fetch pages, ensuring every link in the site works

    External links are skipped, since the test client only reaches this site.

    run with uv run pytest -s test_web_pages.py to see successful output
    """
    home = client.get("/")
    assert home.status_code == 200
    links = get_links(home.content)

    for link in links:
        if not link.startswith("/"):
            continue
        page = client.get(link)
        assert page.status_code == 200, link
        print(f"successfully reached {link=}")
        links += [url for url in get_links(page.content) if url not in links]


@pytest.mark.parametrize(
    ("url", "actions", "fields"),
    [
        (
            "/worksheets/basic-operations/arithmetic/",
            [b"/api/worksheets/basic_operations.pdf"],
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
            ],
        ),
        (
            "/worksheets/basic-operations/word-problems/",
            [b"/api/worksheets/word_problems.pdf"],
            [
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
                b"steps",  # a radio button for each choice
                b"steps",
                b"no_hints",
                b"black_and_white",
                b"response",  # a radio button for each choice
                b"response",
                b"work_box",
                b"answer_key",
                b"self_check_tiles",
                b"tile_pattern",  # a radio button for each pattern
                b"tile_pattern",
            ],
        ),
        (
            "/worksheets/basic-operations/strip-choice/",
            [b"/api/worksheets/strip_choice.pdf"],
            [
                b"title",
                b"label",
                b"name_line",
                b"problems",
                b"operations",  # a checkbox for each operation
                b"operations",
                b"operations",
                b"operations",
                b"max_number",
                b"steps",  # a radio button for each choice
                b"steps",
                b"max_groups",
                b"prompt",  # a radio button for each choice
                b"prompt",
                b"prompt",
                b"answer_key",
            ],
        ),
        (
            "/worksheets/basic-operations/base-ten-blocks/",
            [b"/api/worksheets/base_ten_blocks.pdf"],
            [
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
                b"tile_pattern",  # a radio button for each pattern
                b"tile_pattern",
            ],
        ),
        (
            "/worksheets/basic-operations/multiplication-models/",
            [b"/api/worksheets/multiplication_models.pdf"],
            [
                b"title",
                b"label",
                b"name_line",
                b"problems",
                b"max_factor",
                b"max_product",
                b"no_jump_labels",
                b"answer_key",
            ],
        ),
        (
            "/worksheets/place-value/",
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
                b"multiple_choice",
                b"answer_key",
                b"self_check_tiles",
                b"tile_pattern",  # a radio button for each pattern
                b"tile_pattern",
            ],
        ),
        (
            "/worksheets/data-and-graphs/",
            [b"/api/worksheets/data_graphs.pdf"],
            [
                b"title",
                b"label",
                b"name_line",
                b"problems",
                b"list_style",  # a radio button for each style
                b"list_style",
                b"answer_key",
            ],
        ),
        (
            "/worksheets/algebra-and-functions/input-output-tables/",
            [b"/api/worksheets/input_output_tables.pdf"],
            [
                b"title",
                b"label",
                b"name_line",
                b"problems",
                b"operations",  # a checkbox for each operation
                b"operations",
                b"operations",
                b"operations",
                b"blanks",  # a radio button for each choice
                b"blanks",
                b"blanks",
                b"question_types",  # a checkbox for each type
                b"question_types",
                b"question_types",
                b"multiple_choice",
                b"answer_key",
                b"self_check_tiles",
                b"tile_pattern",  # a radio button for each pattern
                b"tile_pattern",
            ],
        ),
        (
            "/worksheets/algebra-and-functions/slope-and-intercepts/",
            [b"/api/worksheets/slope_and_intercepts.pdf"],
            [
                b"title",
                b"label",
                b"name_line",
                b"problems",
                b"given",  # a checkbox for each form
                b"given",
                b"given",
                b"given",
                b"given",
                b"given",
                b"given",
                b"asked",  # a checkbox for each question
                b"asked",
                b"asked",
                b"asked",
                b"asked",
                b"asked",
                b"intercept_answers",  # a checkbox for each shape
                b"intercept_answers",
                b"largest_coordinate",
                b"largest_denominator",
                b"whole_intercepts",
                b"number_styles",  # a checkbox for each style
                b"number_styles",
                b"multiple_choice",
                b"answer_key",
                b"self_check_tiles",
                b"tile_pattern",  # a radio button for each pattern
                b"tile_pattern",
            ],
        ),
        (
            "/worksheets/algebra-and-functions/writing-linear-equations/",
            [b"/api/worksheets/writing_linear_equations.pdf"],
            [
                b"title",
                b"label",
                b"name_line",
                b"problems",
                b"given",  # a checkbox for each given
                b"given",
                b"given",
                b"given",
                b"given",
                b"given",
                b"given",
                b"asked",  # a checkbox for each form
                b"asked",
                b"asked",
                b"asked",
                b"asked",
                b"largest_coordinate",
                b"largest_denominator",
                b"whole_intercepts",
                b"number_styles",  # a checkbox for each style
                b"number_styles",
                b"multiple_choice",
                b"answer_key",
                b"self_check_tiles",
                b"tile_pattern",  # a radio button for each pattern
                b"tile_pattern",
            ],
        ),
    ],
)
def test_builder_page(url: str, actions: list[bytes], fields: list[bytes], client: Client) -> None:
    """
    A sheet's page has its kind's form, the top bar, the catalogue sidebar, the feedback link,
    toonarmycaptain.com, the Buy Me a Coffee link and no seed field.

    The form targets its kind's PDF endpoint, with a field for each option and none for a seed,
    since every sheet of a core kind is new. The fields come in the page's order: the header,
    the questions, then the answers.
    """
    content = client.get(url).content

    assert re.findall(rb'action="([^"]+)"', content) == actions
    assert re.findall(rb'<(?:input|select) [^>]*?name="([^"]+)"', content) == fields
    assert get_links(content) == [
        # the top bar
        "/",
        "/worksheets/",
        # the sidebar
        "/worksheets/basic-operations/arithmetic/",
        "/worksheets/basic-operations/word-problems/",
        "/worksheets/basic-operations/strip-choice/",
        "/worksheets/basic-operations/base-ten-blocks/",
        "/worksheets/basic-operations/multiplication-models/",
        "/worksheets/place-value/",
        "/worksheets/data-and-graphs/",
        "/worksheets/algebra-and-functions/input-output-tables/",
        "/worksheets/algebra-and-functions/slope-and-intercepts/",
        "/worksheets/algebra-and-functions/writing-linear-equations/",
        # the footer
        f"/feedback/?from={url}",
        "https://toonarmycaptain.com",
        "https://buymeacoffee.com/toonarmycaptain",
    ]


@pytest.mark.parametrize(
    ("url", "name", "expected"),
    [
        # simple by default, on each sheet with tiles
        (
            "/worksheets/basic-operations/arithmetic/",
            "tile_pattern",
            [(b"simple", b" checked", b"simple"), (b"complex", b"", b"complex")],
        ),
        (
            "/worksheets/basic-operations/word-problems/",
            "tile_pattern",
            [(b"simple", b" checked", b"simple"), (b"complex", b"", b"complex")],
        ),
        (
            "/worksheets/basic-operations/base-ten-blocks/",
            "tile_pattern",
            [(b"simple", b" checked", b"simple"), (b"complex", b"", b"complex")],
        ),
        (
            "/worksheets/place-value/",
            "tile_pattern",
            [(b"simple", b" checked", b"simple"), (b"complex", b"", b"complex")],
        ),
        (
            "/worksheets/algebra-and-functions/input-output-tables/",
            "tile_pattern",
            [(b"simple", b" checked", b"simple"), (b"complex", b"", b"complex")],
        ),
        (
            "/worksheets/algebra-and-functions/slope-and-intercepts/",
            "tile_pattern",
            [(b"simple", b" checked", b"simple"), (b"complex", b"", b"complex")],
        ),
        (
            "/worksheets/algebra-and-functions/writing-linear-equations/",
            "tile_pattern",
            [(b"simple", b" checked", b"simple"), (b"complex", b"", b"complex")],
        ),
        # the input-output tables form's Missing table values: inputs and outputs by default
        (
            "/worksheets/algebra-and-functions/input-output-tables/",
            "blanks",
            [
                (b"inputs", b"", b"Inputs"),
                (b"outputs", b"", b"Outputs"),
                (b"inputs_and_outputs", b" checked", b"Inputs and outputs"),
            ],
        ),
        # none, some, all, with mixed by default
        (
            "/worksheets/basic-operations/base-ten-blocks/",
            "regrouping",
            [
                (b"never", b"", b"Never"),
                (b"mixed", b" checked", b"Mixed"),
                (b"always", b"", b"Always"),
            ],
        ),
        # the word problems form's Response: free response by default
        (
            "/worksheets/basic-operations/word-problems/",
            "response",
            [
                (b"free_response", b" checked", b"Free response"),
                (b"multiple_choice", b"", b"Multiple choice"),
            ],
        ),
        # the strip choice form's Show: the wording by default
        (
            "/worksheets/basic-operations/strip-choice/",
            "prompt",
            [
                (b"word_problem", b" checked", b"Word problem"),
                (b"equation", b"", b"Equation"),
                (b"both", b"", b"Both"),
            ],
        ),
        # one step by default, on the word problems and strip choice forms
        (
            "/worksheets/basic-operations/word-problems/",
            "steps",
            [(b"one", b" checked", b"One step"), (b"two", b"", b"Two steps")],
        ),
        (
            "/worksheets/basic-operations/strip-choice/",
            "steps",
            [(b"one", b" checked", b"One step"), (b"two", b"", b"Two steps")],
        ),
        # a grid by default
        (
            "/worksheets/data-and-graphs/",
            "list_style",
            [(b"grid", b" checked", b"Grid"), (b"commas", b"", b"Commas")],
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
            "/worksheets/basic-operations/word-problems/",
            "representation",
            [
                (b"strip", b"", b"Strip Diagrams"),
                (b"none", b" selected", b"Text Only"),
                (b"number_line", b"", b"Number Lines"),
                (b"blocks", b"", b"Base-Ten Blocks"),
                (b"equation", b"", b"Equations"),
            ],
        ),
        (
            "/worksheets/place-value/",
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
            "/worksheets/place-value/",
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

    Representation defaults to text only, and also offers strip diagrams. From defaults to standard
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
            "/worksheets/basic-operations/arithmetic/",
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
            "/worksheets/basic-operations/word-problems/",
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
        # all four by default on the strip choice form, with an All box
        (
            "/worksheets/basic-operations/strip-choice/",
            b"/api/worksheets/strip_choice.pdf",
            "operations",
            [
                (b"add", b" checked", b"Addition"),
                (b"subtract", b" checked", b"Subtraction"),
                (b"multiply", b" checked", b"Multiplication"),
                (b"divide", b" checked", b"Division"),
            ],
            True,
        ),
        # all four by default on the input-output tables form, with an All box
        (
            "/worksheets/algebra-and-functions/input-output-tables/",
            b"/api/worksheets/input_output_tables.pdf",
            "operations",
            [
                (b"add", b" checked", b"Addition"),
                (b"subtract", b" checked", b"Subtraction"),
                (b"multiply", b" checked", b"Multiplication"),
                (b"divide", b" checked", b"Division"),
            ],
            True,
        ),
        # every multiple-choice question type by default, with an All box for the three
        (
            "/worksheets/algebra-and-functions/input-output-tables/",
            b"/api/worksheets/input_output_tables.pdf",
            "question_types",
            [
                (b"table", b" checked", b"Choose the table that matches a rule"),
                (b"sentence", b" checked", b"Complete a sentence about a table"),
                (b"statement", b" checked", b"Choose the true statement about a table"),
            ],
            True,
        ),
        # every form by default, with an All box
        (
            "/worksheets/algebra-and-functions/slope-and-intercepts/",
            b"/api/worksheets/slope_and_intercepts.pdf",
            "given",
            [
                (b"slope_intercept", b" checked", b"Slope-intercept form (y = mx + b)"),
                (b"standard", b" checked", b"Standard form (Ax + By = C)"),
                (
                    b"point_slope",
                    b" checked",
                    "Point-slope form (y \N{MINUS SIGN} y\N{SUBSCRIPT ONE} = "
                    "m(x \N{MINUS SIGN} x\N{SUBSCRIPT ONE}))".encode(),
                ),
                (b"point_and_slope", b" checked", b"A point and the slope"),
                (b"two_points", b" checked", b"Two points"),
                (b"vertical", b" checked", b"Vertical lines (x = a)"),
                (b"horizontal", b" checked", b"Horizontal lines (y = b)"),
            ],
            True,
        ),
        # every question by default, with an All box
        (
            "/worksheets/algebra-and-functions/slope-and-intercepts/",
            b"/api/worksheets/slope_and_intercepts.pdf",
            "asked",
            [
                (b"slope", b" checked", b"Slope"),
                (b"rate_of_change", b" checked", b"Rate of change"),
                (b"y_intercept", b" checked", b"y-intercept"),
                (b"x_intercept", b" checked", b"x-intercept"),
                (b"zero", b" checked", b"Zero"),
                (b"slope_and_y_intercept", b" checked", b"Slope and y-intercept"),
            ],
            True,
        ),
        # numbers and ordered pairs by default
        (
            "/worksheets/algebra-and-functions/slope-and-intercepts/",
            b"/api/worksheets/slope_and_intercepts.pdf",
            "intercept_answers",
            [
                (b"number", b" checked", b"Numbers (2)"),
                (b"point", b" checked", b"Ordered pairs ((0, 2))"),
            ],
            True,
        ),
        # fractions and decimals by default: two, so no All box of their own, though the form's
        # other groups have one
        (
            "/worksheets/algebra-and-functions/slope-and-intercepts/",
            b"/api/worksheets/slope_and_intercepts.pdf",
            "number_styles",
            [
                (b"fraction", b" checked", b"Fractions (5/2)"),
                (b"decimal", b" checked", b"Decimals (2.5)"),
            ],
            True,
        ),
        # every given by default, with an All box
        (
            "/worksheets/algebra-and-functions/writing-linear-equations/",
            b"/api/worksheets/writing_linear_equations.pdf",
            "given",
            [
                (b"slope_intercept", b" checked", b"Slope-intercept form (y = mx + b)"),
                (b"standard", b" checked", b"Standard form (Ax + By = C)"),
                (
                    b"point_slope",
                    b" checked",
                    "Point-slope form (y \N{MINUS SIGN} y\N{SUBSCRIPT ONE} = "
                    "m(x \N{MINUS SIGN} x\N{SUBSCRIPT ONE}))".encode(),
                ),
                (b"point_and_slope", b" checked", b"A point and the slope"),
                (b"two_points", b" checked", b"Two points"),
                (b"parallel", b" checked", b"A point and a parallel line"),
                (b"perpendicular", b" checked", b"A point and a perpendicular line"),
            ],
            True,
        ),
        # every form by default, with an All box
        (
            "/worksheets/algebra-and-functions/writing-linear-equations/",
            b"/api/worksheets/writing_linear_equations.pdf",
            "asked",
            [
                (b"slope_intercept", b" checked", b"Slope-intercept form (y = mx + b)"),
                (b"standard", b" checked", b"Standard form (Ax + By = C)"),
                (
                    b"point_slope",
                    b" checked",
                    "Point-slope form (y \N{MINUS SIGN} y\N{SUBSCRIPT ONE} = "
                    "m(x \N{MINUS SIGN} x\N{SUBSCRIPT ONE}))".encode(),
                ),
                (b"vertical", b" checked", b"Vertical lines (x = a)"),
                (b"horizontal", b" checked", b"Horizontal lines (y = b)"),
            ],
            True,
        ),
        (
            "/worksheets/algebra-and-functions/writing-linear-equations/",
            b"/api/worksheets/writing_linear_equations.pdf",
            "number_styles",
            [
                (b"fraction", b" checked", b"Fractions (5/2)"),
                (b"decimal", b" checked", b"Decimals (2.5)"),
            ],
            True,
        ),
        # every type of question by default, with an All box for the three
        (
            "/worksheets/basic-operations/base-ten-blocks/",
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
        ("/worksheets/basic-operations/arithmetic/", False),
        ("/worksheets/basic-operations/word-problems/", False),
        ("/worksheets/basic-operations/strip-choice/", False),
        ("/worksheets/basic-operations/base-ten-blocks/", False),
        ("/worksheets/basic-operations/multiplication-models/", False),
        ("/worksheets/place-value/", True),
        ("/worksheets/data-and-graphs/", False),
        ("/worksheets/algebra-and-functions/input-output-tables/", False),
        ("/worksheets/algebra-and-functions/slope-and-intercepts/", False),
        ("/worksheets/algebra-and-functions/writing-linear-equations/", False),
        ("/worksheets/legacy/", False),
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
    ("url", "script"),
    [
        ("/worksheets/basic-operations/arithmetic/", False),
        ("/worksheets/basic-operations/word-problems/", False),
        ("/worksheets/basic-operations/strip-choice/", False),
        ("/worksheets/basic-operations/base-ten-blocks/", False),
        ("/worksheets/basic-operations/multiplication-models/", False),
        ("/worksheets/place-value/", False),
        ("/worksheets/data-and-graphs/", False),
        ("/worksheets/algebra-and-functions/input-output-tables/", True),
        ("/worksheets/algebra-and-functions/slope-and-intercepts/", False),
        ("/worksheets/algebra-and-functions/writing-linear-equations/", False),
        ("/worksheets/legacy/", False),
    ],
)
def test_the_input_output_tables_page_swaps_fields_for_multiple_choice(
    client: Client, url: str, script: bool
) -> None:
    """
    Only the input-output tables page includes the script that hides the Missing table values
    radio buttons while multiple choice, which shows complete tables, is ticked, and shows the
    question types only then.

    Whether the script works is checked manually in a browser.
    """
    content = client.get(url).content
    assert (b"function showChoiceFields()" in content) is script


@pytest.mark.parametrize(
    ("url", "script"),
    [
        ("/worksheets/basic-operations/arithmetic/", False),
        ("/worksheets/basic-operations/word-problems/", False),
        ("/worksheets/basic-operations/strip-choice/", False),
        ("/worksheets/basic-operations/base-ten-blocks/", False),
        ("/worksheets/basic-operations/multiplication-models/", False),
        ("/worksheets/place-value/", False),
        ("/worksheets/data-and-graphs/", False),
        ("/worksheets/algebra-and-functions/input-output-tables/", False),
        ("/worksheets/algebra-and-functions/slope-and-intercepts/", True),
        ("/worksheets/algebra-and-functions/writing-linear-equations/", False),
        ("/worksheets/legacy/", False),
    ],
)
def test_the_slope_and_intercepts_page_shows_intercepts_as_only_for_an_intercept(
    client: Client, url: str, script: bool
) -> None:
    """
    Only the slope and intercepts page includes the script that shows the Intercepts as
    checkboxes while the y- or x-intercept is ticked, and hides them otherwise.

    Whether the script works is checked manually in a browser.
    """
    content = client.get(url).content
    assert (b"function showInterceptAnswers()" in content) is script


@pytest.mark.parametrize(
    ("url", "tiles_script", "titles_script", "representation_script"),
    [
        ("/worksheets/basic-operations/arithmetic/", True, True, False),
        ("/worksheets/basic-operations/word-problems/", True, False, True),
        ("/worksheets/basic-operations/strip-choice/", False, False, False),
        ("/worksheets/basic-operations/base-ten-blocks/", True, False, False),
        ("/worksheets/basic-operations/multiplication-models/", False, False, False),
        ("/worksheets/place-value/", True, False, False),
        ("/worksheets/data-and-graphs/", False, False, False),
        ("/worksheets/algebra-and-functions/input-output-tables/", True, False, False),
        ("/worksheets/algebra-and-functions/slope-and-intercepts/", True, False, False),
        ("/worksheets/algebra-and-functions/writing-linear-equations/", True, False, False),
        ("/worksheets/legacy/", False, False, False),
    ],
)
def test_ticking_self_check_tiles_asks_for_12_questions(
    client: Client, url: str, tiles_script: bool, titles_script: bool, representation_script: bool
) -> None:
    """
    The arithmetic, word problems, base-ten blocks, place-value, input-output tables, slope and
    intercepts, and writing linear equations pages include the script that sets problems to 12
    for tiles.

    The other pages have no self-check tiles box, and so no script. Whether the script works is
    checked manually in a browser. Only the arithmetic page has the operation names that its other
    script puts in the title, and only the word problems page has the titles that its
    representation script puts in the title (that script also hides "Leave out the hints" for
    text only).
    """
    content = client.get(url).content
    assert (b"selfCheckTiles.checked ? 12 : problems.defaultValue" in content) is tiles_script
    assert (b'id="operation-titles"' in content) is titles_script
    assert (b'id="representation-titles"' in content) is representation_script


@pytest.mark.parametrize(
    ("url", "script_id", "expected"),
    [
        # the operations each representation can show, for the script to grey out the others
        (
            "/worksheets/basic-operations/word-problems/",
            "representation-operations",
            b'<script id="representation-operations" type="application/json">'
            b'{"strip": ["add", "subtract", "multiply", "divide"], '
            b'"none": ["add", "subtract", "multiply", "divide"], '
            b'"number_line": ["add", "subtract"], '
            b'"blocks": ["add", "subtract"], '
            b'"equation": ["add", "subtract", "multiply", "divide"]}</script>',
        ),
        # the title of a sheet choosing each representation offered as multiple choice
        (
            "/worksheets/basic-operations/word-problems/",
            "choice-titles",
            b'<script id="choice-titles" type="application/json">'
            b'{"number_line": "Word Problems \\u2014 Number Line multiple choice", '
            b'"equation": "Word Problems \\u2014 Equation multiple choice"}</script>',
        ),
        ("/worksheets/basic-operations/arithmetic/", "representation-operations", None),
        ("/worksheets/basic-operations/arithmetic/", "choice-titles", None),
        ("/worksheets/basic-operations/strip-choice/", "representation-operations", None),
        ("/worksheets/basic-operations/strip-choice/", "choice-titles", None),
        ("/worksheets/basic-operations/base-ten-blocks/", "representation-operations", None),
        ("/worksheets/basic-operations/base-ten-blocks/", "choice-titles", None),
        ("/worksheets/basic-operations/multiplication-models/", "representation-operations", None),
        ("/worksheets/basic-operations/multiplication-models/", "choice-titles", None),
        ("/worksheets/place-value/", "representation-operations", None),
        ("/worksheets/place-value/", "choice-titles", None),
        ("/worksheets/data-and-graphs/", "representation-operations", None),
        ("/worksheets/data-and-graphs/", "choice-titles", None),
        (
            "/worksheets/algebra-and-functions/input-output-tables/",
            "representation-operations",
            None,
        ),
        ("/worksheets/algebra-and-functions/input-output-tables/", "choice-titles", None),
        (
            "/worksheets/algebra-and-functions/slope-and-intercepts/",
            "representation-operations",
            None,
        ),
        ("/worksheets/algebra-and-functions/slope-and-intercepts/", "choice-titles", None),
        (
            "/worksheets/algebra-and-functions/writing-linear-equations/",
            "representation-operations",
            None,
        ),
        ("/worksheets/algebra-and-functions/writing-linear-equations/", "choice-titles", None),
    ],
)
def test_the_representation_script_s_data(
    client: Client, url: str, script_id: str, expected: bytes | None
) -> None:
    """
    The word problems page has the data its representation script needs: the operations each
    representation can show, to grey out the others, and the title of a sheet choosing each
    representation offered as multiple choice. Whether the scripts work is checked manually in a
    browser.
    """
    found = re.search(
        rb'<script id="' + script_id.encode() + rb'".*?</script>', client.get(url).content
    )
    assert (found.group() if found else None) == expected


@pytest.mark.parametrize(
    ("url", "forms"),
    [
        (
            "/worksheets/basic-operations/arithmetic/",
            [(b"/api/worksheets/basic_operations.pdf", b" data-check-first")],
        ),
        (
            "/worksheets/basic-operations/word-problems/",
            [(b"/api/worksheets/word_problems.pdf", b" data-check-first")],
        ),
        (
            "/worksheets/basic-operations/strip-choice/",
            [(b"/api/worksheets/strip_choice.pdf", b" data-check-first")],
        ),
        (
            "/worksheets/basic-operations/base-ten-blocks/",
            [(b"/api/worksheets/base_ten_blocks.pdf", b" data-check-first")],
        ),
        (
            "/worksheets/basic-operations/multiplication-models/",
            [(b"/api/worksheets/multiplication_models.pdf", b" data-check-first")],
        ),
        ("/worksheets/place-value/", [(b"/api/worksheets/place_value.pdf", b" data-check-first")]),
        (
            "/worksheets/data-and-graphs/",
            [(b"/api/worksheets/data_graphs.pdf", b" data-check-first")],
        ),
        (
            "/worksheets/algebra-and-functions/input-output-tables/",
            [(b"/api/worksheets/input_output_tables.pdf", b" data-check-first")],
        ),
        (
            "/worksheets/algebra-and-functions/slope-and-intercepts/",
            [(b"/api/worksheets/slope_and_intercepts.pdf", b" data-check-first")],
        ),
        (
            "/worksheets/algebra-and-functions/writing-linear-equations/",
            [(b"/api/worksheets/writing_linear_equations.pdf", b" data-check-first")],
        ),
        (
            "/worksheets/legacy/",
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


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "/worksheets/basic-operations/arithmetic/",
            [
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
            ],
        ),
        (
            "/worksheets/basic-operations/word-problems/",
            [
                (b"title", b"Title"),
                (b"label", b"Label"),
                (b"name_line", b"Add Name/Date blanks"),
                (b"problems", b"Problems"),
                (b"max_number", b"Largest number"),
                (b"representation", b"Representation"),
                (b"no_hints", b"Leave out the hints"),
                (b"black_and_white", b"Black and white blocks"),
                (b"work_box", b"Include working out space"),
                (b"answer_key", b"Add an answer key page"),
                (b"self_check_tiles", b"Self-check tile answers"),
            ],
        ),
        (
            "/worksheets/basic-operations/strip-choice/",
            [
                (b"title", b"Title"),
                (b"label", b"Label"),
                (b"name_line", b"Add Name/Date blanks"),
                (b"problems", b"Problems"),
                (b"max_number", b"Largest number"),
                (b"max_groups", b"Largest number of groups"),
                (b"answer_key", b"Add an answer key page"),
            ],
        ),
        (
            "/worksheets/basic-operations/base-ten-blocks/",
            [
                (b"title", b"Title"),
                (b"label", b"Label"),
                (b"name_line", b"Add Name/Date blanks"),
                (b"problems", b"Problems"),
                (b"min_number", b"Smallest number"),
                (b"max_number", b"Largest number"),
                (b"black_and_white", b"Black and white blocks"),
                (b"answer_key", b"Add an answer key page"),
                (b"self_check_tiles", b"Self-check tile answers"),
            ],
        ),
        (
            "/worksheets/basic-operations/multiplication-models/",
            [
                (b"title", b"Title"),
                (b"label", b"Label"),
                (b"name_line", b"Add Name/Date blanks"),
                (b"problems", b"Problems"),
                (b"max_factor", b"Largest factor"),
                (b"max_product", b"Largest product"),
                (b"no_jump_labels", b"Leave the number-line jumps unnumbered"),
                (b"answer_key", b"Add an answer key page"),
            ],
        ),
        (
            "/worksheets/algebra-and-functions/input-output-tables/",
            [
                (b"title", b"Title"),
                (b"label", b"Label"),
                (b"name_line", b"Add Name/Date blanks"),
                (b"problems", b"Problems"),
                (b"multiple_choice", b"Multiple choice"),
                (b"answer_key", b"Add an answer key page"),
                (b"self_check_tiles", b"Self-check tile answers"),
            ],
        ),
        (
            "/worksheets/algebra-and-functions/slope-and-intercepts/",
            [
                (b"title", b"Title"),
                (b"label", b"Label"),
                (b"name_line", b"Add Name/Date blanks"),
                (b"problems", b"Problems"),
                (b"largest_coordinate", b"Largest number in a point"),
                (b"largest_denominator", b"Largest denominator"),
                (b"whole_intercepts", b"Whole-number intercepts only"),
                (b"multiple_choice", b"Multiple choice"),
                (b"answer_key", b"Add an answer key page"),
                (b"self_check_tiles", b"Self-check tile answers"),
            ],
        ),
        (
            "/worksheets/algebra-and-functions/writing-linear-equations/",
            [
                (b"title", b"Title"),
                (b"label", b"Label"),
                (b"name_line", b"Add Name/Date blanks"),
                (b"problems", b"Problems"),
                (b"largest_coordinate", b"Largest number in a point"),
                (b"largest_denominator", b"Largest denominator"),
                (b"whole_intercepts", b"Whole-number intercepts only"),
                (b"multiple_choice", b"Multiple choice"),
                (b"answer_key", b"Add an answer key page"),
                (b"self_check_tiles", b"Self-check tile answers"),
            ],
        ),
    ],
)
def test_each_field_carries_its_label_for_the_check_first_messages(
    client: Client, url: str, expected: list[tuple[bytes, bytes]]
) -> None:
    """
    Each field's data-label supplies the label that begins a rejected option's message.

    The tile pattern's radio buttons and the operations' checkboxes have none, as no message
    names them.
    """
    content = client.get(url).content
    assert re.findall(rb'name="(\w+)" data-label="([^"]+)"', content) == expected


def test_legacy_page(client: Client) -> None:
    """
    The legacy page has a form for each of the nine imported scripts, the top bar, the catalogue
    sidebar, the feedback link, toonarmycaptain.com and the Buy Me a Coffee link.

    The form actions are compared as a whole, in order, so an omitted script, or the basic
    operations form appearing here, makes them differ.
    """
    content = client.get("/worksheets/legacy/").content

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
    assert get_links(content) == [
        # the top bar
        "/",
        "/worksheets/",
        # the sidebar
        "/worksheets/basic-operations/arithmetic/",
        "/worksheets/basic-operations/word-problems/",
        "/worksheets/basic-operations/strip-choice/",
        "/worksheets/basic-operations/base-ten-blocks/",
        "/worksheets/basic-operations/multiplication-models/",
        "/worksheets/place-value/",
        "/worksheets/data-and-graphs/",
        "/worksheets/algebra-and-functions/input-output-tables/",
        "/worksheets/algebra-and-functions/slope-and-intercepts/",
        "/worksheets/algebra-and-functions/writing-linear-equations/",
        # the footer
        "/feedback/?from=/worksheets/legacy/",
        "https://toonarmycaptain.com",
        "https://buymeacoffee.com/toonarmycaptain",
    ]


@pytest.mark.parametrize(
    ("url", "location"),
    [
        # a group of several sheets sends its own path on to its first sheet
        ("/worksheets/basic-operations/", "/worksheets/basic-operations/arithmetic/"),
        (
            "/worksheets/algebra-and-functions/",
            "/worksheets/algebra-and-functions/input-output-tables/",
        ),
        # where input-output tables were before their group had a second sheet
        (
            "/worksheets/input-output-tables/",
            "/worksheets/algebra-and-functions/input-output-tables/",
        ),
    ],
)
def test_group_and_old_paths_redirect(client: Client, url: str, location: str) -> None:
    """A group's own path, and a sheet's old one, redirect to the sheet's page."""
    response = client.get(url)
    assert (response.status_code, response["Location"]) == (302, location)
