"""Worksheet PDF endpoints: ``GET /api/worksheets/<kind>.pdf``, one per registry kind.

The query parameters are that kind's options. A legacy kind takes a seed, and with none
a random 6-digit one is used. The seed goes in the filename for debugging; it is not a
promise that the same URL makes the same sheet later.

Kinds built on the core take no seed. A request without a ``sheet`` token is redirected to the
same URL with a random one. The server ignores the token: it only gives each sheet its own URL,
which the edge cache and the browser keep for a few hours, so a sheet can be opened and
printed again from its address.
"""

# No `from __future__ import annotations` here: Ninja reads each endpoint's
# Query[...] annotation at runtime, and it refers to a local variable.
import random
import secrets
from collections.abc import Callable
from typing import Any

from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.utils.text import slugify
from ninja import Query, Router

from .registry import CORE_KINDS, LEGACY_KINDS, CoreKind, Kind

router = Router(tags=["worksheets"])

CACHE_SECONDS = 24 * 60 * 60

# Tells the OpenAPI docs the response is a PDF, not JSON.
PDF_RESPONSE = {
    "responses": {
        200: {
            "description": "The worksheet PDF, shown in the browser rather than downloaded.",
            "content": {"application/pdf": {"schema": {"type": "string", "format": "binary"}}},
        }
    }
}


def _pdf_response(content: bytes, *filename_parts: str) -> HttpResponse:
    """The PDF, shown in the browser, named from the non-empty parts joined by dashes."""
    response = HttpResponse(content, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="{"-".join(filter(None, filename_parts))}.pdf"'
    )
    return response


def _add_route(
    name: str, kind: Kind[Any] | CoreKind[Any], view: Callable[..., HttpResponse]
) -> None:
    router.get(
        f"/{name}.pdf",
        operation_id=f"{name}_pdf",
        url_name=f"{name}_pdf",
        summary=kind.options.model_fields["title"].default,
        openapi_extra=PDF_RESPONSE,
    )(view)


def _add_legacy_endpoint(name: str, kind: Kind[Any]) -> None:
    def pdf(request: HttpRequest, options: Query[kind.options]) -> HttpResponse:  # type: ignore[name-defined]
        seed = options.seed if options.seed is not None else random.randrange(100_000, 1_000_000)
        # e.g. strip-day-2-sheet-a-123456.pdf; the base-ten worksheet has no label
        return _pdf_response(
            kind.render(options, seed), name, slugify(getattr(options, "label", "")), str(seed)
        )

    _add_route(name, kind, pdf)


def _add_core_endpoint(name: str, kind: CoreKind[Any]) -> None:
    def pdf(request: HttpRequest, options: Query[kind.options]) -> HttpResponse:  # type: ignore[name-defined]
        if not request.GET.get("sheet"):
            # Leverage edge caching the URL to retain pdf at the URL for (in theory) CACHE_SECONDS
            query = request.GET.copy()
            query["sheet"] = secrets.token_hex(4)  # 16^8 combinations
            redirect = HttpResponseRedirect(f"{request.path}?{query.urlencode()}")
            redirect["Cache-Control"] = "no-store"
            return redirect
        response = _pdf_response(kind.render(options), name, slugify(options.label))
        response["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
        return response

    _add_route(name, kind, pdf)


for _name, _kind in LEGACY_KINDS.items():
    _add_legacy_endpoint(_name, _kind)
for _name, _core_kind in CORE_KINDS.items():
    _add_core_endpoint(_name, _core_kind)
