# eMudhra TLS 接続実験

2026-10-25（JST）に、uv の python-build-standalone と各HTTPクライアントの既定の証明書検証で実測した記録。
[デモサイト](https://emudhra.we-have-a-problem.com/)の4チェーンを調べる。
この結果を、ライブラリの全バージョン・全OS・すべての侵害された中間CAへの評価には一般化しない。

## 実行環境・判定方法

- macOS 26.7.1 / build 25G241 / Apple Silicon
- uv 0.13.5 (46776a95d 2026-10-21)、CPython 3.14.9、OpenSSL 3.5.9 (29 Sep 2026)
- Python: uv管理の `cpython-3.14-macos-aarch64-none`。第三者ライブラリはスクリプト別のuv環境に分離。
- 既定のOpenSSL CA: `/private/etc/ssl/cert.pem`（`/etc/ssl/cert.pem`の実体、mtime 2026-09-25）。CAディレクトリ: `/private/etc/ssl/certs`。
- Homebrew ca-certificates 2026-10-20: `/opt/homebrew/etc/ca-certificates/cert.pem`（mtime 2026-10-22）。今回更新操作はしていない。
- システムPEM SHA-256: `9dae8d76e55cb08991f2b672d58999ea15560d910759c16b544f843bdffbb994`
- Homebrew PEM SHA-256: `19092144dab12d4ac3d3e5fbcf6a11cbac12b536e32c4ba8cc7d03da8f6de066`
- 既定設定の実験では `SSL_CERT_FILE` / `SSL_CERT_DIR` / `REQUESTS_CA_BUNDLE` / `CURL_CA_BUNDLE` をすべて未設定にした。
- 各スクリプトはプロキシの環境変数をプロセス内で無効化し、リダイレクトを追跡しない。CA環境変数はライブラリが解釈する。`verify=False` や独自SSLContextの注入はしない。
- GETのレスポンスヘッダーを得た時点でTLS成功。HTTPエラーも成功に含み、本文は読み込まない。今回の成功はすべてHTTP 200。
- `--timeout` の既定は5秒。aiohttpはリクエスト全体、同期クライアントは接続・読み込み等のタイムアウトで、スクリプト全体の制限ではない。
- `ACCEPTED`: TLS成功、`REJECTED`: 証明書検証失敗、`UNKNOWN`: DNS・タイムアウトなど判定不能。
- 終了コード: `1` = デモが1件以上成功、`0` = デモ4件が証明書検証で拒否されcontrol成功（理由の確認が必要）、`2` = 成功したデモがなく通信不明/control失敗/CA初期化失敗。期限切れやホスト名不一致だけでは今回の対策を確認できない。

**macOSのPEMファイル・Keychainのルート抽出・macOS自身による信頼性評価は区別する。**
`ssl.get_default_verify_paths()` はstdlibの候補パスであり、各ライブラリの実際のCA参照先とは限らない。

## 再実行

リポジトリルートで実行する。各新規スクリプトはPEP 723 inline script metadataで対象ライブラリのバージョンを固定。
推移依存とPythonのパッチバージョンは固定していないため、再実行時は出力されるバージョンも確認する。
`urllib_checker.py` は既存のstdlibスクリプトをそのまま使用する。

```sh
env -u SSL_CERT_FILE -u SSL_CERT_DIR -u REQUESTS_CA_BUNDLE -u CURL_CA_BUNDLE \
  uv run --python 3.14 emudhra-we-have-a-problem/requests_checker.py
```

ファイル名を対象の `<library>_checker.py` に置き換える。CA切替は各項目のコマンドを使い、ほかのCA環境変数を解除して実行する。
この実験ではsandbox内の書込先を限定するため `UV_CACHE_DIR=/private/tmp/emudhra-uv-cache` を追加した（TLS設定には使わない）。
各スクリプトはPython/OpenSSL・全インストール済みパッケージ・CA環境変数・5ホストの結果と検証理由を出力する。

## 基準: urllib（既存スクリプト）

```sh
uv run --python 3.14 emudhra-we-have-a-problem/urllib_checker.py --verbose
SSL_CERT_FILE=/opt/homebrew/etc/ca-certificates/cert.pem \
  uv run --python 3.14 emudhra-we-have-a-problem/urllib_checker.py --verbose
```

| ホスト | 既定 | Homebrew (`SSL_CERT_FILE`) |
| --- | --- | --- |
| dv-g3b-emudhra.we-have-a-problem.com | ACCEPTED | REJECTED |
| dv-g3b-aaa-emudhra.we-have-a-problem.com | ACCEPTED | REJECTED |
| dv-g3b-noct-emudhra.we-have-a-problem.com | ACCEPTED | REJECTED |
| dv-g3b-aaa-noct-emudhra.we-have-a-problem.com | ACCEPTED | REJECTED |
| www.python.org (control) | ACCEPTED | ACCEPTED |

終了コードは既定 `1`、Homebrew `0`。Homebrewでの4件の拒否理由は `code=20: unable to get local issuer certificate`。

## サードパーティライブラリの実測一覧

| ライブラリ | バージョン | 既定のデモ成功数 | control | Homebrewで再試行 |
| --- | --- | --- | --- | --- |
| requests | 2.34.2 | 0/4 | 成功 | 既定で拒否のため未実施 |

## requests 2.34.2

certifi 2026.10.19のバンドルを使用。4件とも `code=20: unable to get local issuer certificate`。
[RequestsのCA設定](https://requests.readthedocs.io/en/latest/user/advanced/#ssl-cert-verification)は `REQUESTS_CA_BUNDLE`（フォールバックは `CURL_CA_BUNDLE`）。今回は既定で拒否したため切替実測はしていない。

```sh
uv run --python 3.14 emudhra-we-have-a-problem/requests_checker.py
```

| ホスト | 既定 |
| --- | --- |
| dv-g3b-emudhra.we-have-a-problem.com | REJECTED |
| dv-g3b-aaa-emudhra.we-have-a-problem.com | REJECTED |
| dv-g3b-noct-emudhra.we-have-a-problem.com | REJECTED |
| dv-g3b-aaa-noct-emudhra.we-have-a-problem.com | REJECTED |
| www.python.org | ACCEPTED |

既定設定の終了コード: `0`。実測時の依存パッケージ:

```text
certifi==2026.10.19, charset-normalizer==3.5.2, idna==3.20, requests==2.34.2, urllib3==2.8.0
```

検証: 実サーバー5ホストへの接続、構文、ラップされた証明書エラー（検証属性を持たないラッパーも含む）、一般TLS/DNS/タイムアウトをUNKNOWNにする分類、例外の循環参照、終了コード0/1/2、無効なtimeout（0・負数・NaN・無限大）を確認。
