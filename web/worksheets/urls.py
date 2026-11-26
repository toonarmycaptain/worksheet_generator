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
    path("algebra-and-functions/", RedirectView.as_view(pattern_name="input_output_tables")),
    path(
        "algebra-and-functions/input-output-tables/",
        views.sheet,
        {"kind": "input_output_tables"},
        name="input_output_tables",
    ),
    path(
        "algebra-and-functions/slope-and-intercepts/",
        views.sheet,
        {"kind": "slope_and_intercepts"},
        name="slope_and_intercepts",
    ),
    path(
        "algebra-and-functions/writing-linear-equations/",
        views.sheet,
        {"kind": "writing_linear_equations"},
        name="writing_linear_equations",
    ),
    path(
        "algebra-and-functions/graphing-linear-equations/",
        views.sheet,
        {"kind": "graphing_linear_equations"},
        name="graphing_linear_equations",
    ),
    path(
        "algebra-and-functions/order-of-operations/",
        views.sheet,
        {"kind": "order_of_operations"},
        name="order_of_operations",
    ),
    path("factors-and-primes/", RedirectView.as_view(pattern_name="prime_composite")),
    path(
        "factors-and-primes/prime-and-composite-numbers/",
        views.sheet,
        {"kind": "prime_composite"},
        name="prime_composite",
    ),
    path("fractions/", RedirectView.as_view(pattern_name="naming_fractions")),
    path(
        "fractions/naming-fractions/",
        views.sheet,
        {"kind": "naming_fractions"},
        name="naming_fractions",
    ),
    path(
        "fractions/fractions-on-a-number-line/",
        views.sheet,
        {"kind": "fraction_number_lines"},
        name="fraction_number_lines",
    ),
    path(
        "fractions/comparing-fractions/",
        views.sheet,
        {"kind": "comparing_fractions"},
        name="comparing_fractions",
    ),
    # where input-output tables were before they had a group of their own
    path("input-output-tables/", RedirectView.as_view(pattern_name="input_output_tables")),
    path("legacy/", views.legacy, name="legacy"),
]
