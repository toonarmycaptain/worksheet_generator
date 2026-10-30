"""The pages: a home page, and one page of forms for each class of worksheet builder.

Each form opens its PDF in a new tab. The forms are built from each kind's options
schema, so their defaults, limits and labels always match what the API accepts.
Temporary, like the registry: the React front end replaces these pages.
"""

from collections.abc import Mapping
from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .registry import CORE_KINDS, LEGACY_KINDS, CoreKind, Kind

# What each home page entry says, and the page it opens (a url name).
BUILDERS = [
    {
        "title": "Arithmetic",
        "description": "Addition, subtraction and multiplication questions, as a printable "
        "multiple-choice sheet.",
        "url_name": "arithmetic",
    },
]

HEADINGS = {
    "arithmetic": "Addition, Subtraction and Multiplication",
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

# JSON schema limit -> HTML input attribute
LIMITS = {"minimum": "min", "maximum": "max", "minLength": "minlength", "maxLength": "maxlength"}


def _field(name: str, schema: dict[str, Any]) -> dict[str, Any]:
    """How to show one option, from its entry in the options' JSON schema."""
    field = {"name": name, "label": schema["title"], "value": schema["default"]}
    if "enum" in schema:
        return field | {"input": "select", "choices": schema["enum"]}
    if schema["type"] == "boolean":
        return field | {"input": "checkbox"}
    attrs = {html: schema[limit] for limit, html in LIMITS.items() if limit in schema}
    if schema["type"] == "integer" or "minLength" in schema:
        attrs["required"] = "required"  # an empty box would be rejected by the API
    return field | {"input": "number" if schema["type"] == "integer" else "text", "attrs": attrs}


def _forms(kinds: Mapping[str, Kind[Any] | CoreKind[Any]]) -> list[dict[str, Any]]:
    """One form for each kind, in the order given."""
    forms = []
    for kind, spec in kinds.items():
        properties = spec.options.model_json_schema()["properties"]
        forms.append(
            {
                "heading": HEADINGS[kind],
                "url_name": f"api:{kind}_pdf",
                # no seed field: each sheet gets a random one
                "fields": [_field(n, s) for n, s in properties.items() if n != "seed"],
            }
        )
    return forms


def home(request: HttpRequest) -> HttpResponse:
    return render(request, "worksheets/home.html", {"builders": BUILDERS})


def arithmetic(request: HttpRequest) -> HttpResponse:
    context = {
        "page_title": "Arithmetic",
        "intro": "Pick the operation and the size of the numbers. The PDF opens in a new tab, "
        "where you can print or save it. Every click makes a new sheet.",
        "forms": _forms({"arithmetic": CORE_KINDS["arithmetic"]}),
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
