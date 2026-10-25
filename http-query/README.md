# Python WebフレームワークのHTTP QUERYメソッド対応

調査日: **2026-10-26（JST）**。各フレームワークのPyPI最新安定版を対象に、公式ドキュメント・リリース版ソースと実行結果を照合した。将来の対応予定や開発ブランチの実装は、リリース済みの対応とは区別する。

ここでいうQUERYはHTTPメソッドであり、URLのクエリパラメーターやORMのqueryではない。「明示的にルートを登録してリクエスト本文を処理できる」ことと、「専用API・安全なメソッドとしての扱い・スキーマ等まで標準対応している」ことは分けて記録する。検索処理自体はアプリケーションで副作用を起こさないように実装する必要がある。

## 一覧

| フレームワーク | 確認版 | QUERYの受付・本文処理 | 標準APIなどの制約 |
| --- | --- | --- | --- |
| Django | 6.1.2 | 明示設定により可能 | Viewの既定メソッドに含まれない。CSRF検証対象、require_safeも対象外 |
| Flask | 3.1.3 / Werkzeug 3.1.9 | `methods=["QUERY"]` で可能 | MethodViewのメソッド自動検出には含まれない |

Starlette・FastAPIは既存調査を参照する（今回の再検証対象外）。

- [Starlette 1.7.0のQUERY対応](https://nikkie-ftnext.hatenablog.com/entry/starlette-1-7-0-http-query-method-support): HTTPEndpoint、CORS、OpenAPI 3.2などの対応を調査済み。
- [FastAPIの2026年9月時点の調査](https://nikkie-ftnext.hatenablog.com/entry/fastapi-progress-support-http-query-method-202609): OpenAPIやドキュメントUIを含む対応状況を調査済み。現在の最新版の判定としては扱わない。

## Django 6.1.2

**結論: 汎用APIでQUERYを受け付けられるが、QUERYが標準で組み込まれているわけではない。**

- 関数ビューは `@require_http_methods(["QUERY"])` で登録し、`request.body` からJSON本文を読める。
- クラスビューは `query()` を定義するだけでは405。`http_method_names` に小文字の `"query"` を追加するとディスパッチされる。
- `CsrfViewMiddleware` が検証を省略するのはGET・HEAD・OPTIONS・TRACE。QUERYはトークンなしでは403になる。サンプルはミドルウェアを有効にしたまま、Cookieと `X-CSRFToken` を送って200を確認する。
- `require_safe` はGET・HEAD専用のためQUERYを通さない。

根拠: [PyPIの確認版](https://pypi.org/project/Django/6.1.2/)、[Viewの既定メソッドとdispatch](https://docs.djangoproject.com/en/6.1/ref/class-based-views/base/#django.views.generic.base.View.http_method_names)、[HTTPデコレーター](https://docs.djangoproject.com/en/6.1/topics/http/decorators/)、[CSRFの仕様](https://docs.djangoproject.com/en/6.1/ref/csrf/)、[6.1.2のView実装](https://github.com/django/django/blob/6.1.2/django/views/generic/base.py)。QUERYの標準対応を追う入口は [Django #37232](https://code.djangoproject.com/ticket/37232)。

### サンプルと再現方法

リポジトリルートから実行する。各スクリプトはPEP 723で直接依存の確認版を固定している。今回の検証環境はmacOS arm64 / CPython 3.13.17。`uv` とPython 3.13を使用する。

```sh
uv run --python 3.13 http-query/django_app.py --check
uv run --python 3.13 http-query/django_app.py runserver 127.0.0.1:8000 --noreload
```

別ターミナルから、CSRF用Cookieとトークンを取得してQUERYを送る。

```sh
cookie_jar=$(mktemp)
token=$(curl -fsS -c "$cookie_jar" http://127.0.0.1:8000/csrf \
  | python3 -c 'import json, sys; print(json.load(sys.stdin)["csrf_token"])')
curl -i -X QUERY http://127.0.0.1:8000/search \
  -b "$cookie_jar" -H "X-CSRFToken: $token" \
  -H 'Content-Type: application/json' -d '{"term":"python"}'
rm "$cookie_jar"
```

[django_app.py](django_app.py) は関数ビュー `/search` とクラスビュー `/class-search` を提供する。両方とも200と `{"method": "QUERY", "filters": {"term": "python"}}` を返す。入力は正常なJSONを前提とする最小サンプル。

`--check` の確認結果（Django Client、CSRF強制検証あり）:

```text
Django 6.1.2: QUERY body=200; no CSRF token=403; GET/default View/require_safe=405; OPTIONS Allow=QUERY, OPTIONS
```

デフォルト設定を示す `/default-class-search`、`require_safe` を示す `/safe-search` も含む。クラスビューのOPTIONSは `Allow: QUERY, OPTIONS` を返す。CORS、キャッシュ、外部プロキシ、本番WSGI/ASGIサーバー、追加パッケージ（Django REST framework等）は今回の確認範囲外。

## Flask 3.1.3 / Werkzeug 3.1.9

**結論: `@app.route(..., methods=["QUERY"])` でQUERYを登録でき、JSON本文も通常のAPIで読める。専用デコレーターの追加を待つ必要はない。**

Flaskの `methods` とWerkzeugの `Rule` はメソッド文字列を受け取るため、QUERY専用の実装がなくてもルーティングできる。`request.get_json()` で本文を処理でき、Flaskが自動提供するOPTIONSのAllowにもQUERYが載る。

ただし `MethodView` の自動検出対象はget・post・head・options・delete・put・trace・patch。`query()` のみを定義するとQUERYのルートにはならず405になる。クラスで `methods = ["QUERY"]` を明示すれば、既存の `dispatch_request()` が `query()` に振り分ける。

根拠: [Flaskの確認版](https://pypi.org/project/Flask/3.1.3/)、[Werkzeugの確認版](https://pypi.org/project/Werkzeug/3.1.9/)、[Flaskルート登録API](https://flask.palletsprojects.com/en/stable/api/#flask.Flask.add_url_rule)、[MethodViewの公式説明](https://flask.palletsprojects.com/en/stable/views/#method-dispatching-and-apis)、[Flask 3.1.3の検出・dispatch実装](https://github.com/pallets/flask/blob/3.1.3/src/flask/views.py)、[Werkzeug 3.1.9のRule実装](https://github.com/pallets/werkzeug/blob/3.1.9/src/werkzeug/routing/rules.py)。

### サンプルと再現方法

```sh
uv run --python 3.13 http-query/flask_app.py --check
uv run --python 3.13 http-query/flask_app.py
```

別ターミナルから送信する。

```sh
curl -i -X QUERY http://127.0.0.1:8001/search \
  -H 'Content-Type: application/json' -d '{"term":"python"}'
curl -i -X OPTIONS http://127.0.0.1:8001/search
```

[flask_app.py](flask_app.py) は関数ビュー `/search` とMethodView `/class-search` を提供する。両方とも200と `{"method":"QUERY","filters":{"term":"python"}}` を返す。Flask本体にはDjangoのような標準CSRFミドルウェアがなく、この例もCSRF拡張を使用していない。

`--check` の確認結果（Flask test client）:

```text
Flask 3.1.3 / Werkzeug 3.1.9: QUERY body=200; GET/auto MethodView=405; OPTIONS Allow=QUERY, OPTIONS
```

Allowのメソッド順序は不定。CORS・CSRF・OpenAPIの拡張パッケージや本番WSGIサーバーのQUERY対応までは、この結果から判断できない。
