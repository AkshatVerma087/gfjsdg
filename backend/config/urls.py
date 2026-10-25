"""URL Configuration for Wind Forecast Monitor."""

from django.urls import path, re_path

from core.health import health_view, ready_view
from core.spa import spa_index_view
from wind.api import api

urlpatterns = [
    path("api/v1/health", health_view, name="health"),
    path("api/v1/ready", ready_view, name="ready"),
    path("api/v1/", api.urls),
    # Catch-all client-side route for SPA
    re_path(r"^(?!api/).*$", spa_index_view, name="spa"),
]
