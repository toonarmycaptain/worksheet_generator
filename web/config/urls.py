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
from ninja import NinjaAPI
from worksheets import views
from worksheets.api import router as worksheets_router

api = NinjaAPI(title="Worksheet generator", urls_namespace="api")
api.add_router("/worksheets/", worksheets_router)

urlpatterns = [
    path("", views.home, name="home"),
    path("arithmetic/", views.arithmetic, name="arithmetic"),
    path("legacy/", views.legacy, name="legacy"),
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
