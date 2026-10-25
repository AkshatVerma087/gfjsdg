"""Single Page Application (SPA) fallback view for production serving."""

from pathlib import Path

from django.http import HttpResponse

BASE_DIR = Path(__file__).resolve().parent.parent
SPA_INDEX = BASE_DIR.parent / "frontend" / "dist" / "index.html"


def spa_index_view(request):
    """Serve the built frontend SPA index.html for client-side routing."""
    if SPA_INDEX.exists():
        content = SPA_INDEX.read_text(encoding="utf-8")
        return HttpResponse(content, content_type="text/html")
    # If frontend has not been built yet (e.g. in standalone backend test)
    return HttpResponse(
        "<html><body><h2>Wind Forecast Monitor API is running.</h2>"
        "<p>Access API docs at <a href='/api/v1/docs'>/api/v1/docs</a></p></body></html>",
        content_type="text/html",
    )
