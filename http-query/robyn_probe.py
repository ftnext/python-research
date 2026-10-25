# /// script
# requires-python = ">=3.10"
# dependencies = ["robyn==0.88.0"]
# ///
"""Unsupported-method probe, not a QUERY application.

uv run --python 3.13 http-query/robyn_probe.py
uv run --python 3.13 http-query/robyn_probe.py --serve
"""

import sys
from importlib.metadata import version

from robyn import HttpMethod, Robyn

# Robyn parses sys.argv itself; consume our flag before constructing the app.
serve = sys.argv[1:] == ["--serve"]
sys.argv = [sys.argv[0]]
app = Robyn(__file__)


@app.get("/health")
def health():
    return "GET works"


def check():
    assert not hasattr(HttpMethod, "QUERY")
    assert not hasattr(app, "query")
    try:
        app.add_route("QUERY", "/search", lambda: "QUERY works")
    except KeyError as exc:
        assert exc.args == ("QUERY",)
    else:
        raise AssertionError("QUERY registration succeeded: re-evaluate support")
    print(f"Robyn {version('robyn')}: no HttpMethod.QUERY / app.query; "
          "add_route('QUERY', ...) raises KeyError('QUERY')", flush=True)


if __name__ == "__main__":
    check()
    if serve:
        app.start(host="127.0.0.1", port=8002)
