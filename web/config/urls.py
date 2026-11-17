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
from django.urls import include, path
from django.views.generic import TemplateView
from feedback.views import feedback
from ninja import NinjaAPI
from worksheets.api import router as worksheets_router

api = NinjaAPI(title="Worksheet generator", urls_namespace="api")
api.add_router("/worksheets/", worksheets_router)

urlpatterns = [
    # the maths site's landing page, with a card for each section; worksheets is the first
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("worksheets/", include("worksheets.urls")),
    path("feedback/", feedback, name="feedback"),
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
