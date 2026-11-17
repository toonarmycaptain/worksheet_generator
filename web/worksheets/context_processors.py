"""Template context for every page, including those of other apps, such as feedback."""

from typing import Any

from django.http import HttpRequest

from .views import BUILDERS, HEADINGS


def catalogue(request: HttpRequest) -> dict[str, Any]:
    """
    Return the worksheets catalogue, for the sidebar in base.html and the home page's cards.

    Each builder has its title, description and sheets, each sheet its title and URL name. The
    sheet whose page this is, if any, is marked current, and so is its builder.
    """
    match = request.resolver_match
    page = match.url_name if match else None
    return {
        "catalogue": [
            {
                "title": builder["title"],
                "description": builder["description"],
                "current": page in builder["sheets"],
                "sheets": [
                    {"title": HEADINGS[kind], "url_name": kind, "current": kind == page}
                    for kind in builder["sheets"]
                ],
            }
            for builder in BUILDERS
        ]
    }
