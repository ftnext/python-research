# /// script
# requires-python = ">=3.12"
# dependencies = ["Django==6.1.2"]
# ///
"""QUERY via explicit method registration; keep Django's CSRF middleware enabled.

uv run --python 3.13 http-query/django_app.py --check
uv run --python 3.13 http-query/django_app.py runserver 127.0.0.1:8000 --noreload
"""

import json
import sys

import django
from django.conf import settings

settings.configure(
    SECRET_KEY="local-query-example-only",
    ROOT_URLCONF=__name__,
    ALLOWED_HOSTS=["127.0.0.1", "localhost", "testserver"],
    MIDDLEWARE=["django.middleware.csrf.CsrfViewMiddleware"],
)
django.setup()

from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.urls import path
from django.views import View
from django.views.decorators.http import require_GET, require_http_methods, require_safe


@require_GET
def csrf_token(request):
    return JsonResponse({"csrf_token": get_token(request)})


@require_http_methods(["QUERY"])
def search(request):
    filters = json.loads(request.body)
    return JsonResponse({"method": request.method, "filters": filters})


class DefaultSearch(View):
    """Defining query() alone does not enable QUERY in Django 6.1.2."""

    def query(self, request):
        return search(request)


class Search(DefaultSearch):
    http_method_names = ["query", "options"]


urlpatterns = [
    path("csrf", csrf_token),
    path("search", search),
    path("class-search", Search.as_view()),
    path("default-class-search", DefaultSearch.as_view()),
    path("safe-search", require_safe(search)),
]


def check():
    from django.test import Client

    client = Client(enforce_csrf_checks=True)
    payload = '{"term":"python"}'
    assert client.generic("QUERY", "/search", payload, "application/json").status_code == 403
    token = client.get("/csrf").json()["csrf_token"]
    for url in ("/search", "/class-search"):
        response = client.generic(
            "QUERY", url, payload, "application/json", HTTP_X_CSRFTOKEN=token
        )
        assert response.status_code == 200, response.content
        assert response.json() == {"method": "QUERY", "filters": {"term": "python"}}
        assert client.get(url).status_code == 405
    for url in ("/default-class-search", "/safe-search"):
        assert client.generic(
            "QUERY", url, payload, "application/json", HTTP_X_CSRFTOKEN=token
        ).status_code == 405
    assert set(client.options("/class-search").headers["Allow"].split(", ")) == {
        "QUERY", "OPTIONS"
    }
    print(f"Django {django.get_version()}: QUERY body=200; no CSRF token=403; "
          "GET/default View/require_safe=405; OPTIONS Allow=QUERY, OPTIONS")


if __name__ == "__main__":
    if sys.argv[1:] == ["--check"]:
        check()
    else:
        from django.core.management import execute_from_command_line

        execute_from_command_line(sys.argv)
