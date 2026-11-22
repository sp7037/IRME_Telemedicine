from django.conf import settings
from django.db import connection, DatabaseError
from django.db.migrations.executor import MigrationExecutor
from django.http import FileResponse, Http404, JsonResponse
from django.views.decorators.http import require_safe


@require_safe
def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        executor = MigrationExecutor(connection)
        if executor.migration_plan(executor.loader.graph.leaf_nodes()):
            return JsonResponse({"status": "migrations_pending"}, status=503)
    except DatabaseError:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})


@require_safe
def spa(request, route=""):
    if route.startswith(("api/", "media/", "static/", ".")) or "." in route.rsplit("/", 1)[-1]:
        raise Http404
    index = settings.FRONTEND_DIST / "index.html"
    if not index.is_file():
        raise Http404("Frontend build is not installed.")
    response = FileResponse(index.open("rb"), content_type="text/html")
    response["Cache-Control"] = "no-store"
    return response
