
from django.conf import settings
from django.http import FileResponse, Http404
from django.views.decorators.http import require_GET


@require_GET
def react_frontend(request):
    index_file = (
        settings.BASE_DIR
        / "frontend"
        / "dist"
        / "index.html"
    )

    if not index_file.is_file():
        raise Http404("React build not found.")

    return FileResponse(
        index_file.open("rb"),
        content_type="text/html",
    )
