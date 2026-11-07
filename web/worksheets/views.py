"""
The site's pages: a home page, and a page of forms for each group of worksheet builders.

Each form opens its PDF in a new tab. The forms are generated from each kind's options schema,
so their defaults, limits and labels always match what the API accepts. Temporary, like the
registry: the React front end replaces these pages.
"""

from collections.abc import Mapping
from itertools import combinations
from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from core.basic_operations.data import Operation
from core.basic_operations.representation import (
    REPRESENTATION_OPERATIONS,
    Representation,
    operations_name,
    word_problems_title,
)
from core.self_check_tiles import SLOTS
from core.wrong_answers import WRONG_ANSWER_COUNT

from .registry import CORE_KINDS, LEGACY_KINDS, CoreKind, Kind

# Home page entries: each builder's title, description and page (a URL name).
BUILDERS = [
    {
        "title": "Basic Operations",
        "description": "Addition, subtraction, multiplication and division questions, as a "
        "printable multiple-choice sheet, or an answer sheet for self-check tiles. Division can "
        "also leave out the dividend or the divisor for students to fill in. All four also come "
        "as word problems.",
        "url_name": "basic_operations",
    },
    {
        "title": "Place Value",
        "description": "Write numbers in standard, expanded, unit or word form, or in expanded "
        "notation, from another of those forms.",
        "url_name": "place_value",
    },
]

HEADINGS = {
    "basic_operations": "Addition, Subtraction, Multiplication and Division",
    "place_value": "Write the Number in Another Form",
    "word_problems": "Word Problems",
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
    field = {"name": name, "label": schema["title"], "value": schema["default"]}
    if schema.get("type") == "array":
        # A list of choices renders as a checkbox for each, and the page sends those ticked.
        labels = schema.get("labels", {})
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


def _forms(kinds: Mapping[str, Kind[Any] | CoreKind[Any]]) -> list[dict[str, Any]]:
    """Return one form for each kind, in the given order."""
    forms = []
    for kind, spec in kinds.items():
        properties = spec.options.model_json_schema()["properties"]
        forms.append(
            {
                "heading": HEADINGS[kind],
                "url_name": f"api:{kind}_pdf",
                # Core kinds refuse bad options before drawing anything, so the page checks
                # them before opening a tab (see builder.html). Legacy kinds draw at once.
                "check_first": isinstance(spec, CoreKind),
                # no seed field: each sheet gets a random one
                "fields": [_field(n, s) for n, s in properties.items() if n != "seed"],
            }
        )
    return forms


def home(request: HttpRequest) -> HttpResponse:
    return render(request, "worksheets/home.html", {"builders": BUILDERS})


def basic_operations(request: HttpRequest) -> HttpResponse:
    context = {
        "page_title": "Basic Operations",
        "intro": "Tick the operations and pick the size of the numbers. The PDF opens in a new "
        "tab, where you can print or save it. Every click makes a new sheet. Tick Self-check "
        "tile answers to swap the choices for an answer bank and a picture to match against the "
        f"flipped case. That sets the questions to {SLOTS}, one for each tile: ask for fewer, "
        "such as 2 or 4, and the other tiles go unused. With division by itself, Missing number "
        "can leave out the dividend or the divisor instead of the answer, as a square to write "
        "it in. Division uses the largest dividend and divisor instead of the largest number.",
        "forms": _forms(
            {
                "basic_operations": CORE_KINDS["basic_operations"],
                "word_problems": CORE_KINDS["word_problems"],
            }
        ),
        "self_check_tiles_problems": SLOTS,
        # each combination of ticked operations, as their values joined by commas -> its title
        "operation_titles": {
            ",".join(operation.value for operation in ticked): operations_name(ticked)
            for size in range(1, len(Operation) + 1)
            for ticked in combinations(Operation, size)
        },
        # each representation's value -> the title of word problems drawn with it
        "representation_titles": {
            representation.value: word_problems_title(representation)
            for representation in Representation
        },
        # each representation's value -> the values of the operations it can show
        "representation_operations": {
            representation.value: [operation.value for operation in Operation if operation in shown]
            for representation, shown in REPRESENTATION_OPERATIONS.items()
        },
    }
    return render(request, "worksheets/builder.html", context)


def place_value(request: HttpRequest) -> HttpResponse:
    context = {
        "page_title": "Place Value",
        "intro": "Pick the form each number is shown in and the form to write it in. Mixed "
        "picks a form for each question, never the same one twice in a question. The PDF opens "
        "in a new tab, where you can print or save it. Every click makes a new sheet. Tick "
        f"Multiple choice to list {WRONG_ANSWER_COUNT + 1} choices under each number instead of "
        "an answer line: the "
        "wrong ones are random numbers from the range. Tick Self-check tile answers to swap "
        "the answer lines or choices for an answer bank and a picture to "
        f"match against the flipped case. That sets the questions to {SLOTS}, one for each "
        "tile: ask for fewer, such as 2 or 4, and the other tiles go unused.",
        "forms": _forms({"place_value": CORE_KINDS["place_value"]}),
        "self_check_tiles_problems": SLOTS,
        "distinct_forms": True,
    }
    return render(request, "worksheets/builder.html", context)


def legacy(request: HttpRequest) -> HttpResponse:
    context = {
        "page_title": "Legacy PDF generators",
        "intro": "Pick a worksheet and set its options. The PDF opens in a new tab, where you "
        "can print or save it. Every click makes a new sheet.",
        "forms": _forms(LEGACY_KINDS),
    }
    return render(request, "worksheets/builder.html", context)
