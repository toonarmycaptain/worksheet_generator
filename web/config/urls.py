"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
from feedback.views import feedback
from ninja import NinjaAPI
from worksheets import views
from worksheets.api import router as worksheets_router

api = NinjaAPI(title="Worksheet generator", urls_namespace="api")
api.add_router("/worksheets/", worksheets_router)

urlpatterns = [
    path("", views.home, name="home"),
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
    path("legacy/", views.legacy, name="legacy"),
    path("feedback/", feedback, name="feedback"),
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
