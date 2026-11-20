"""Middleware."""

from collections.abc import Callable

from django.http import HttpRequest
from django.http.response import HttpResponseBase


def clacks_overhead(
    get_response: Callable[[HttpRequest], HttpResponseBase],
) -> Callable[[HttpRequest], HttpResponseBase]:
    """Add "X-Clacks-Overhead: GNU Terry Pratchett" to every response that lacks it.

    A response that already carries the header keeps its own value.
    """

    def middleware(request: HttpRequest) -> HttpResponseBase:
        response = get_response(request)
        response.headers.setdefault("X-Clacks-Overhead", "GNU Terry Pratchett")
        return response

    return middleware
