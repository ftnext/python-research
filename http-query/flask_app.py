# /// script
# requires-python = ">=3.10"
# dependencies = ["Flask==3.1.3", "Werkzeug==3.1.9"]
# ///
"""uv run --python 3.13 http-query/flask_app.py [--check]"""

import sys
from importlib.metadata import version

from flask import Flask, request
from flask.views import MethodView

app = Flask(__name__)


@app.route("/search", methods=["QUERY"])
def search():
    return {"method": request.method, "filters": request.get_json()}


class Search(MethodView):
    # query() is not in MethodView's automatically detected methods.
    methods = ["QUERY"]

    def query(self):
        return search()


app.add_url_rule("/class-search", view_func=Search.as_view("class_search"))


def check():
    class AutoSearch(MethodView):
        def query(self):
            return search()

    app.add_url_rule("/auto-class-search", view_func=AutoSearch.as_view("auto_search"))
    client = app.test_client()
    for url in ("/search", "/class-search"):
        response = client.open(url, method="QUERY", json={"term": "python"})
        assert response.status_code == 200, response.data
        assert response.json == {"method": "QUERY", "filters": {"term": "python"}}
        assert client.get(url).status_code == 405
        options = client.options(url)
        assert options.status_code == 200
        assert set(options.headers["Allow"].split(", ")) == {"QUERY", "OPTIONS"}
    assert AutoSearch.methods is None
    assert client.open("/auto-class-search", method="QUERY", json={}).status_code == 405
    print(f"Flask {version('flask')} / Werkzeug {version('werkzeug')}: "
          "QUERY body=200; GET/auto MethodView=405; OPTIONS Allow=QUERY, OPTIONS")


if __name__ == "__main__":
    if sys.argv[1:] == ["--check"]:
        check()
    else:
        app.run(host="127.0.0.1", port=8001)
