"""Worksheet PDF endpoints: ``GET /api/worksheets/<kind>.pdf``, one per registry kind.

The query parameters are that kind's options. With no seed, a random 6-digit one is
used. The seed goes in the filename for debugging; it is not a promise that the same
URL makes the same sheet later.
"""

# No `from __future__ import annotations` here: Ninja reads each endpoint's
# Query[...] annotation at runtime, and it refers to a local variable.
import random
from typing import Any

from django.http import HttpRequest, HttpResponse
from django.utils.text import slugify
from ninja import Query, Router

from .registry import KINDS, Kind

router = Router(tags=["worksheets"])

# Tells the OpenAPI docs the response is a PDF, not JSON.
PDF_RESPONSE = {
    "responses": {
        200: {
            "description": "The worksheet PDF, shown in the browser rather than downloaded.",
            "content": {"application/pdf": {"schema": {"type": "string", "format": "binary"}}},
        }
    }
}


def _add_endpoint(name: str, kind: Kind[Any]) -> None:
    def pdf(request: HttpRequest, options: Query[kind.options]) -> HttpResponse:  # type: ignore[name-defined]
        seed = options.seed if options.seed is not None else random.randrange(100_000, 1_000_000)
        response = HttpResponse(kind.render(options, seed), content_type="application/pdf")
        # e.g. strip-day-2-sheet-a-123456.pdf; the base-ten worksheet has no label
        stem = "-".join(filter(None, [name, slugify(getattr(options, "label", "")), str(seed)]))
        response["Content-Disposition"] = f'inline; filename="{stem}.pdf"'
        return response

    router.get(
        f"/{name}.pdf",
        operation_id=f"{name}_pdf",
        url_name=f"{name}_pdf",
        summary=kind.options.model_fields["title"].default,
        openapi_extra=PDF_RESPONSE,
    )(pdf)


for _name, _kind in KINDS.items():
    _add_endpoint(_name, _kind)
