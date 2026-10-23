"""The form page: one form per worksheet kind, each opening its PDF in a new tab.

The forms are built from each kind's options schema, so their defaults, limits and
labels always match what the API accepts. Temporary, like the registry: the React
front end replaces this page.
"""

from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .registry import KINDS

HEADINGS = {
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


def legacy(request: HttpRequest) -> HttpResponse:
    forms = []
    for kind, spec in KINDS.items():
        properties = spec.options.model_json_schema()["properties"]
        forms.append(
            {
                "heading": HEADINGS[kind],
                "url_name": f"api:{kind}_pdf",
                # no seed field: each sheet gets a random one
                "fields": [_field(n, s) for n, s in properties.items() if n != "seed"],
            }
        )
    return render(request, "worksheets/legacy.html", {"forms": forms})
