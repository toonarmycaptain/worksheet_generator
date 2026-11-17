"""URL configuration for the worksheets section, which config/urls.py includes under worksheets/."""

from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("", views.home, name="worksheets"),
    # one page per sheet, named after its kind; a group of several sheets sends its own path on
    # to its first, and a group of one shows its sheet there
    path("basic-operations/", RedirectView.as_view(pattern_name="basic_operations")),
    path(
        "basic-operations/arithmetic/",
        views.sheet,
        {"kind": "basic_operations"},
        name="basic_operations",
    ),
    path(
        "basic-operations/word-problems/",
        views.sheet,
        {"kind": "word_problems"},
        name="word_problems",
    ),
    path(
        "basic-operations/strip-choice/", views.sheet, {"kind": "strip_choice"}, name="strip_choice"
    ),
    path(
        "basic-operations/base-ten-blocks/",
        views.sheet,
        {"kind": "base_ten_blocks"},
        name="base_ten_blocks",
    ),
    path(
        "basic-operations/multiplication-models/",
        views.sheet,
        {"kind": "multiplication_models"},
        name="multiplication_models",
    ),
    path("place-value/", views.sheet, {"kind": "place_value"}, name="place_value"),
    path("data-and-graphs/", views.sheet, {"kind": "data_graphs"}, name="data_graphs"),
    path(
        "input-output-tables/",
        views.sheet,
        {"kind": "input_output_tables"},
        name="input_output_tables",
    ),
    path("legacy/", views.legacy, name="legacy"),
]
