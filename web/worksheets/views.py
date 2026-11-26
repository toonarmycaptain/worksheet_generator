"""
The site's pages: a home page, a page for each sheet, grouped by builder, and the legacy page.

Each form opens its PDF in a new tab. The forms are generated from each kind's options schema,
so their defaults, limits and labels always match what the API accepts. Temporary, like the
registry: the React front end replaces these pages.
"""

from collections.abc import Mapping
from itertools import combinations
from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.safestring import mark_safe

from core.basic_operations.data import Operation
from core.basic_operations.generator import WORD_PROBLEM_STRIP_LARGEST_GROUPS
from core.basic_operations.multiplication_models import MULTIPLICATION_MODELS_NAME
from core.basic_operations.representation import (
    CHOICE_NAMES,
    REPRESENTATION_OPERATIONS,
    STRIP_CHOICE_NAME,
    WORD_PROBLEMS_NAME,
    Representation,
    operations_name,
    word_problems_title,
)
from core.comparing_fractions.generator import TILE_TYPES as COMPARING_FRACTIONS_TILE_TYPES
from core.comparing_fractions.representation import COMPARING_FRACTIONS_NAME
from core.discrete_data.data import DataDisplay
from core.discrete_data.generator import SHEET_DISPLAYS, available_parts
from core.fraction_number_lines.generator import TILE_TYPES as FRACTION_NUMBER_LINES_TILE_TYPES
from core.fraction_number_lines.representation import FRACTION_NUMBER_LINES_NAME
from core.input_output_tables.representation import INPUT_OUTPUT_TABLES_NAME
from core.line_equations.representation import (
    GRAPHING_LINEAR_EQUATIONS_NAME,
    SLOPE_AND_INTERCEPTS_NAME,
    WRITING_LINEAR_EQUATIONS_NAME,
)
from core.naming_fractions.representation import NAMING_FRACTIONS_NAME
from core.order_of_operations.data import TILE_TYPES as ORDER_OF_OPERATIONS_TILE_TYPES
from core.order_of_operations.representation import ORDER_OF_OPERATIONS_NAME
from core.prime_composite.data import TILE_TYPES
from core.prime_composite.representation import PRIME_COMPOSITE_NAME
from core.self_check_tiles import SLOTS

from .registry import CORE_KINDS, LEGACY_KINDS, CoreKind, Kind

# The worksheets catalogue, for the sidebar and the home page's cards: each builder's title,
# description and sheets, by kind, which is also each sheet's URL name. A builder's own page is
# its first sheet.
BUILDERS: list[dict[str, Any]] = [
    {
        "title": "Basic Operations",
        "description": "Addition, subtraction, multiplication and division questions, as a "
        "printable multiple-choice sheet, or an answer sheet for self-check tiles. Division can "
        "also leave out the dividend or the divisor for students to fill in. All four also come "
        "as word problems.",
        "sheets": [
            "basic_operations",
            "word_problems",
            "strip_choice",
            "base_ten_blocks",
            "multiplication_models",
        ],
    },
    {
        "title": "Place Value",
        "description": "Write numbers in standard, expanded, unit or word form, or in expanded "
        "notation, from another of those forms.",
        "sheets": ["place_value"],
    },
    {
        "title": "Data and Graphs",
        "description": "Read data in a table, graph or list, complete another display of the "
        "same data, then solve problems about it.",
        "sheets": ["data_graphs"],
    },
    {
        "title": "Algebra and Functions",
        "description": "Fill in tables of number pairs that follow a rule about a real "
        "situation, or choose the table that matches the rule. Find the slope and intercepts of "
        "a line from its equation, points, table or graph, write its equation, or graph it.",
        "sheets": [
            "input_output_tables",
            "slope_and_intercepts",
            "writing_linear_equations",
            "graphing_linear_equations",
            "order_of_operations",
        ],
    },
    {
        "title": "Factors and Primes",
        "description": "Tell prime numbers from composite numbers by their factors.",
        "sheets": ["prime_composite"],
    },
    {
        "title": "Fractions",
        "description": "Name the fraction a picture shows, shade one, and share equally. Find "
        "fractions and distances on a number line. Compare fractions.",
        "sheets": ["naming_fractions", "fraction_number_lines", "comparing_fractions"],
    },
]

HEADINGS = {
    "basic_operations": "Addition, Subtraction, Multiplication, and Division",
    "place_value": "Write the Number in Another Form",
    "word_problems": "Word Problems",
    "strip_choice": STRIP_CHOICE_NAME,
    "base_ten_blocks": "Base-Ten Blocks",
    "multiplication_models": MULTIPLICATION_MODELS_NAME,
    "data_graphs": "Read, Complete, Solve",
    "input_output_tables": INPUT_OUTPUT_TABLES_NAME,
    "prime_composite": PRIME_COMPOSITE_NAME,
    "naming_fractions": NAMING_FRACTIONS_NAME,
    "fraction_number_lines": FRACTION_NUMBER_LINES_NAME,
    "comparing_fractions": COMPARING_FRACTIONS_NAME,
    "order_of_operations": ORDER_OF_OPERATIONS_NAME,
    "slope_and_intercepts": SLOPE_AND_INTERCEPTS_NAME,
    "writing_linear_equations": WRITING_LINEAR_EQUATIONS_NAME,
    "graphing_linear_equations": GRAPHING_LINEAR_EQUATIONS_NAME,
}
LEGACY_HEADINGS = {
    "block": "Addition & Subtraction Word Problems — Base-Ten Blocks",
    "word": "Addition & Subtraction Word Problems",
    "strip": "Addition & Subtraction Word Problems — Strip Diagrams",
    "number_line": "Addition & Subtraction Word Problems — Number Lines",
    "number_line_mc": "Addition & Subtraction Word Problems — Number Lines (Multiple Choice)",
    "multiplication_mc": "Multiplication Word Problems — Pick the Models",
    "data_graph": "Data and Graphs — Read, Complete, Solve",
    "data_graph_mc": "Data and Graphs — Pick the Matching Graph",
    "worksheet": "Base-Ten Blocks: 3-Digit Addition & Subtraction",
}
HEADINGS |= LEGACY_HEADINGS

# JSON schema limit -> HTML input attribute
LIMITS = {"minimum": "min", "maximum": "max", "minLength": "minlength", "maxLength": "maxlength"}


def _field(name: str, schema: dict[str, Any]) -> dict[str, Any]:
    """Return the template context for one option's input, from its JSON schema entry."""
    field = {
        "name": name,
        "label": schema["title"],
        "value": schema["default"],
        "hint": "" if schema.get("mouseover") else schema.get("description", ""),
        # a description the label makes plain enough is shown only on mouseover
        "mouseover": schema.get("description", "") if schema.get("mouseover") else "",
        # the field it shows under, such as the tiles box for their pattern (see _forms)
        "under": schema.get("under"),
        # the operations it's for, if not all: the page shows it only while one is ticked
        "operations": schema.get("operations", []),
    }
    if schema.get("type") == "array":
        # A list of choices renders as a checkbox for each, and the page sends those ticked. Labels
        # marked as markup, written in the registry, show as drawn, such as a stacked fraction.
        labels = schema.get("labels", {})
        if schema.get("markup"):
            labels = {choice: mark_safe(label) for choice, label in labels.items()}
        choices = [(choice, labels.get(choice, choice)) for choice in schema["items"]["enum"]]
        return field | {"input": "checkboxes", "choices": choices}
    if "const" in schema:
        # A Literal of one value has a const instead of an enum: a select with one choice.
        schema = schema | {"enum": [schema["const"]]}
    if "enum" in schema:
        # An enum renders as a select unless its schema requests radio buttons. Each choice is
        # (submitted value, displayed label), using the schema's labels where present.
        labels = schema.get("labels", {})
        choices = [(choice, labels.get(choice, choice)) for choice in schema["enum"]]
        return field | {"input": schema.get("input", "select"), "choices": choices}
    if schema["type"] == "boolean":
        return field | {"input": "checkbox"}
    attrs = {html: schema[limit] for limit, html in LIMITS.items() if limit in schema}
    if schema["type"] == "integer" or "minLength" in schema:
        attrs["required"] = "required"  # the API rejects an empty value
    return field | {"input": "number" if schema["type"] == "integer" else "text", "attrs": attrs}


# A core page's sections, by field name, so a field such as multiple choice is in the same spot
# on every page: the header, then the questions beside the answers (see builder.html). The
# answers go in this order, from how students answer down; every other field is a question.
HEADER_FIELDS = ("title", "label", "name_line")
ANSWER_FIELDS = ("multiple_choice", "response", "work_box", "answer_key", "self_check_tiles")


def _sections(fields: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Return a core page's fields by section: the header, the questions and the answers."""
    return {
        "header": [field for field in fields if field["name"] in HEADER_FIELDS],
        "questions": [
            field for field in fields if field["name"] not in HEADER_FIELDS + ANSWER_FIELDS
        ],
        "answers": sorted(
            (field for field in fields if field["name"] in ANSWER_FIELDS),
            key=lambda field: ANSWER_FIELDS.index(field["name"]),
        ),
    }


def _forms(kinds: Mapping[str, Kind[Any] | CoreKind[Any]]) -> list[dict[str, Any]]:
    """Return one form for each kind, in the given order."""
    forms = []
    for kind, spec in kinds.items():
        properties = spec.options.model_json_schema()["properties"]
        # no seed field: each sheet gets a random one
        fields = [_field(n, s) for n, s in properties.items() if n != "seed"]
        # A field marked as under another goes in that field's cell of the grid, so it stays
        # under it (see fields.html).
        for field in fields:
            field["nested"] = [each for each in fields if each["under"] == field["name"]]
        form: dict[str, Any] = {
            "heading": HEADINGS[kind],
            "url_name": f"api:{kind}_pdf",
            # Core kinds refuse bad options before drawing anything, so the page checks them
            # before opening a tab (see builder.html). Legacy kinds draw at once.
            "check_first": isinstance(spec, CoreKind),
            "fields": [field for field in fields if not field["under"]],
        }
        # the legacy page's forms list their fields as they come
        if isinstance(spec, CoreKind):
            form["sections"] = _sections(form["fields"])
        forms.append(form)
    return forms


# Every sheet's intro, under its heading. What a field does is its hint, under the field: its
# description in the options class.
OPENS_IN_A_TAB = (
    "The PDF opens in a new tab, where you can print or save it. Every click makes a new sheet."
)

# Each sheet's data for its scripts in builder.html, beyond its form. The self-check tiles
# script's data goes to every sheet with tiles (see sheet).
SCRIPT_DATA: dict[str, dict[str, Any]] = {
    "basic_operations": {
        # each combination of ticked operations, as their values joined by commas -> its title
        "operation_titles": {
            ",".join(operation.value for operation in ticked): operations_name(ticked)
            for size in range(1, len(Operation) + 1)
            for ticked in combinations(Operation, size)
        },
    },
    "word_problems": {
        # each representation's value -> the title of word problems drawn with it, and mixed's
        "representation_titles": {
            **{
                representation.value: word_problems_title(representation)
                for representation in Representation
            },
            "mixed": WORD_PROBLEMS_NAME,
        },
        # each value of a representation offered as multiple choice -> the title of word problems
        # choosing it
        "choice_titles": {
            representation.value: word_problems_title(representation, choices=True)
            for representation in CHOICE_NAMES
        },
        # each representation's value -> the values of the operations it can show
        "representation_operations": {
            representation.value: [operation.value for operation in Operation if operation in shown]
            for representation, shown in REPRESENTATION_OPERATIONS.items()
        },
        # the most equal groups a strip diagram has room for, below the field's own limit
        "strip_largest_groups": WORD_PROBLEM_STRIP_LARGEST_GROUPS,
    },
    "place_value": {"distinct_forms": True},
    "input_output_tables": {"choice_fields": True},
    # the question types a self-check tiles sheet can ask
    "prime_composite": {"tile_types": [question_type.value for question_type in TILE_TYPES]},
    "order_of_operations": {
        "tile_types": [question_type.value for question_type in ORDER_OF_OPERATIONS_TILE_TYPES]
    },
    "fraction_number_lines": {
        "tile_types": [question_type.value for question_type in FRACTION_NUMBER_LINES_TILE_TYPES]
    },
    "comparing_fractions": {
        "tile_types": [question_type.value for question_type in COMPARING_FRACTIONS_TILE_TYPES]
    },
    "slope_and_intercepts": {"intercept_answers": True, "blank_grids": True},
    "writing_linear_equations": {"blank_grids": True, "statements": True},
    "data_graphs": {
        # tiles go one to each word problem, so the page's own script sets the problems
        "word_problem_tiles": SLOTS,
        # each combination of ticked displays, as their values joined by commas -> the
        # questions it can make
        "question_availability": {
            ",".join(ticked): list(available_parts([DataDisplay(each) for each in ticked]))
            for size in range(len(SHEET_DISPLAYS) + 1)
            for ticked in combinations(SHEET_DISPLAYS, size)
        },
    },
}


def home(request: HttpRequest) -> HttpResponse:
    return render(request, "worksheets/home.html")


def sheet(request: HttpRequest, kind: str) -> HttpResponse:
    """Return a sheet's page: its heading, intro and form, with its scripts' data."""
    forms = _forms({kind: CORE_KINDS[kind]})
    context = {
        "page_title": HEADINGS[kind],
        "intro": OPENS_IN_A_TAB,
        "forms": forms,
        **SCRIPT_DATA.get(kind, {}),
    }
    has_tiles = any(field["name"] == "self_check_tiles" for field in forms[0]["fields"])
    if has_tiles and "word_problem_tiles" not in context:
        context["self_check_tiles_problems"] = SLOTS
    return render(request, "worksheets/builder.html", context)


def legacy(request: HttpRequest) -> HttpResponse:
    context = {
        "page_title": "Legacy PDF generators",
        "intro": "Pick a worksheet and set its options. The PDF opens in a new tab, where you "
        "can print or save it. Each click makes a new sheet.",
        "forms": _forms(LEGACY_KINDS),
    }
    return render(request, "worksheets/builder.html", context)
