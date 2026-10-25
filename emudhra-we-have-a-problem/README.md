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
| httpx | 0.28.1 | 0/4 | 成功 | 既定で拒否のため未実施 |
| aiohttp | 3.14.5 | 4/4 | 成功 | `SSL_CERT_FILE`: 0/4、control成功 |
| httpx2 | 2.16.0 | 0/4 | 成功 | 既定で拒否のため未実施 |
| httpxyz | 0.42.1 | 0/4 | 成功 | 既定で拒否のため未実施 |
| niquests | 3.21.2 | 4/4 | 成功 | `REQUESTS_CA_BUNDLE`: 0/4、control成功 |
| urllib3 | 2.8.0 | 4/4 | 成功 | `SSL_CERT_FILE`: 0/4、control成功 |

## CA取得元と証明書検証の全体像

実験に使った各スクリプトのuv仮想環境内のソースを確認した結果。
以下は、このmacOS環境と記載バージョンにおける、CA環境変数や独自SSLContextを指定しない既定設定の経路を示す。

| ライブラリ | 既定のCA取得元 | 接続先の検証 |
| --- | --- | --- |
| requests 2.34.2 | certifi | OpenSSL |
| urllib3 2.8.0（直接使用） | OpenSSLの既定パス | OpenSSL |
| httpx 0.28.1 | certifi | OpenSSL |
| aiohttp 3.14.5 | OpenSSLの既定パス | OpenSSL |
| httpx2 2.16.0 | macOSの信頼ストア | macOS Security framework |
| httpxyz 0.42.1 | certifi | OpenSSL |
| niquests 3.21.2 | wassimaがmacOSから抽出 | TLSバックエンド＋独自の条件付き失効確認 |

CA証明書をOSから取得することと、接続先チェーンの信頼性評価をOSに委譲することは異なる。
httpx2は後者で、niquestsは前者。niquestsの独自OCSP／CRL処理は接続先のleaf証明書を対象とし、チェーン中の全中間CAを順番に失効確認する処理ではない。

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

## httpx 0.28.1

certifi 2026.10.19のバンドルを使用。4件とも `code=20: unable to get local issuer certificate`。
[HTTPXの環境変数](https://www.python-httpx.org/environment_variables/)は `SSL_CERT_FILE` / `SSL_CERT_DIR`。`trust_env=False` はCA環境変数も無効化するため使用していない。

```sh
uv run --python 3.14 emudhra-we-have-a-problem/httpx_checker.py
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
anyio==4.15.1, certifi==2026.10.19, h11==0.16.0, httpcore==1.0.9, httpx==0.28.1, idna==3.20, typing_extensions==4.16.0
```

検証: 実サーバー5ホストへの接続、構文、ラップされた証明書エラー（検証属性を持たないラッパーも含む）、一般TLS/DNS/タイムアウトをUNKNOWNにする分類、例外の循環参照、終了コード0/1/2、無効なtimeout（0・負数・NaN・無限大）を確認。

## aiohttp 3.14.5

既定はstdlibの `ssl.create_default_context()` からシステムPEMを読み込み、4件とも成功した。
Homebrew指定では4件とも `code=20: unable to get local issuer certificate` に変わり、controlは成功。終了コードは `1 → 0`。
[aiohttpのSSL設定](https://docs.aiohttp.org/en/stable/client_advanced.html#ssl-control-for-tcp-sockets)も参照。
`ClientConnectorCertificateError` は `SSLCertVerificationError` を継承するが `verify_code` 等を持たないため、内包する `certificate_error` を辿って記録する。

```sh
uv run --python 3.14 emudhra-we-have-a-problem/aiohttp_checker.py
SSL_CERT_FILE=/opt/homebrew/etc/ca-certificates/cert.pem \
  uv run --python 3.14 emudhra-we-have-a-problem/aiohttp_checker.py
```

| ホスト | 既定 | Homebrew (`SSL_CERT_FILE`) |
| --- | --- | --- |
| dv-g3b-emudhra.we-have-a-problem.com | ACCEPTED | REJECTED |
| dv-g3b-aaa-emudhra.we-have-a-problem.com | ACCEPTED | REJECTED |
| dv-g3b-noct-emudhra.we-have-a-problem.com | ACCEPTED | REJECTED |
| dv-g3b-aaa-noct-emudhra.we-have-a-problem.com | ACCEPTED | REJECTED |
| www.python.org | ACCEPTED | ACCEPTED |

既定設定の終了コード: `1`。実測時の依存パッケージ:

```text
aiohappyeyeballs==2.7.1, aiohttp==3.14.5, aiosignal==1.4.0, attrs==26.1.0, frozenlist==1.8.0, idna==3.20, multidict==7.1.0, propcache==0.5.4, yarl==1.25.1
```

検証: 実サーバー5ホストへの接続、構文、ラップされた証明書エラー（検証属性を持たないラッパーも含む）、一般TLS/DNS/タイムアウトをUNKNOWNにする分類、例外の循環参照、終了コード0/1/2、無効なtimeout（0・負数・NaN・無限大）を確認。

## httpx2 2.16.0

インストール済み `httpx2._config.create_ssl_context()` → `httpcore2._ssl.default_ssl_context()` のソースを確認。
macOSでは `truststore.SSLContext` を使用する。4件ともmacOSの信頼性評価で拒否され、理由は `code=-67820: “<対象ホスト>” certificate is blocked`。
これはcertifiやシステムPEMだけで検証する経路とは異なる。[httpcore2](https://pypi.org/project/httpcore2/)も参照。
同ソースは `SSL_CERT_FILE` / `SSL_CERT_DIR` が指定されるとstdlibのSSLContextに切り替えるが、今回は切替実測はしていない。

```sh
uv run --python 3.14 emudhra-we-have-a-problem/httpx2_checker.py
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
anyio==4.15.1, h11==0.16.0, httpcore2==2.16.0, httpx2==2.16.0, idna==3.20, truststore==0.10.5, typing_extensions==4.16.0
```

検証: 実サーバー5ホストへの接続、構文、ラップされた証明書エラー（検証属性を持たないラッパーも含む）、一般TLS/DNS/タイムアウトをUNKNOWNにする分類、例外の循環参照、終了コード0/1/2、無効なtimeout（0・負数・NaN・無限大）を確認。

## httpxyz 0.42.1

certifi 2026.10.19のバンドルを使用。4件とも `code=20: unable to get local issuer certificate`。
[HTTPXYZの環境変数](https://httpxyz.org/environment_variables/)は `SSL_CERT_FILE` / `SSL_CERT_DIR`。`trust_env` は既定のまま維持している。

```sh
uv run --python 3.14 emudhra-we-have-a-problem/httpxyz_checker.py
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
anyio==4.15.1, certifi==2026.10.19, h11==0.16.0, httpcorexyz==1.2.1, httpxyz==0.42.1, idna==3.20, typing_extensions==4.16.0
```

検証: 実サーバー5ホストへの接続、構文、ラップされた証明書エラー（検証属性を持たないラッパーも含む）、一般TLS/DNS/タイムアウトをUNKNOWNにする分類、例外の循環参照、終了コード0/1/2、無効なtimeout（0・負数・NaN・無限大）を確認。

## niquests 3.21.2

既定ではwassimaでmacOSのルートを抽出したCAバンドルを使用し、4件とも成功した。
インストール済み `niquests.adapters.HTTPAdapter.cert_verify()` と `wassima._os._macos` を確認。ルートを抽出してTLSバックエンドへ渡す経路であり、httpx2のmacOSネイティブ信頼性評価と同一ではない。
Homebrewを `REQUESTS_CA_BUNDLE` で指定すると4件とも `code=20: unable to get local issuer certificate` に変わり、controlは成功。終了コードは `1 → 0`。
追加比較として `SSL_CERT_FILE` だけをHomebrewに指定した場合は4件とも成功のままで、終了コード `1`。stdlibの表示パスが変わっても、このライブラリのCA切替を意味しない。
[NiquestsのCA設定](https://niquests.readthedocs.io/en/latest/user/advanced.html#ssl-cert-verification)と[Wassima](https://github.com/jawah/wassima)も参照。

```sh
uv run --python 3.14 emudhra-we-have-a-problem/niquests_checker.py
REQUESTS_CA_BUNDLE=/opt/homebrew/etc/ca-certificates/cert.pem \
  uv run --python 3.14 emudhra-we-have-a-problem/niquests_checker.py
SSL_CERT_FILE=/opt/homebrew/etc/ca-certificates/cert.pem \
  uv run --python 3.14 emudhra-we-have-a-problem/niquests_checker.py
```

| ホスト | 既定 | Homebrew (`REQUESTS_CA_BUNDLE`) | Homebrew (`SSL_CERT_FILE`のみ) |
| --- | --- | --- | --- |
| dv-g3b-emudhra.we-have-a-problem.com | ACCEPTED | REJECTED | ACCEPTED |
| dv-g3b-aaa-emudhra.we-have-a-problem.com | ACCEPTED | REJECTED | ACCEPTED |
| dv-g3b-noct-emudhra.we-have-a-problem.com | ACCEPTED | REJECTED | ACCEPTED |
| dv-g3b-aaa-noct-emudhra.we-have-a-problem.com | ACCEPTED | REJECTED | ACCEPTED |
| www.python.org | ACCEPTED | ACCEPTED | ACCEPTED |

既定設定の終了コード: `1`。実測時の依存パッケージ:

```text
charset-normalizer==3.5.2, h11==0.16.0, jh2==5.0.15, niquests==3.21.2, qh3==2.0.4, urllib3-future==2.25.903, wassima==2.1.5
```

検証: 実サーバー5ホストへの接続、構文、ラップされた証明書エラー（検証属性を持たないラッパーも含む）、一般TLS/DNS/タイムアウトをUNKNOWNにする分類、例外の循環参照、終了コード0/1/2、無効なtimeout（0・負数・NaN・無限大）を確認。

## urllib3 2.8.0

`urllib3.PoolManager()` を直接使用し、独自SSLContextやCA指定を渡さず検証した。
このスクリプト専用のuv環境に入るパッケージは `urllib3==2.8.0` のみで、certifiは導入しない。
既定では4件ともHTTP 200で接続成功。Homebrewを `SSL_CERT_FILE` で指定すると、
4件とも `code=20: unable to get local issuer certificate` で拒否され、controlは引き続きHTTP 200。終了コードは `1 → 0`。

インストール済み `urllib3.util.ssl_.ssl_wrap_socket()` のソースを確認すると、
CAやSSLContextが未指定のときに `SSLContext.load_default_certs()` を呼ぶ。
このmacOS環境ではOpenSSLの既定パスのシステムPEMを使い、`SSL_CERT_FILE` はOpenSSL経由で反映される。
Requestsは `requests.adapters.HTTPAdapter.cert_verify()` でcertifiのCAパスをurllib3へ明示的に渡すため、
同じurllib3 2.8.0でもRequests経由の既定結果とは異なる。
[urllib3のTLS設定](https://urllib3.readthedocs.io/en/stable/advanced-usage.html#custom-tls-certificates)も参照。

プロキシを使わないPoolManagerで、リダイレクト・リトライ・本文の事前読み込みを無効化。
レスポンスはヘッダー取得後に閉じる。CA環境変数はスクリプトからAPI引数に変換せず、既定の処理に任せる。

```sh
uv run --python 3.14 emudhra-we-have-a-problem/urllib3_checker.py
SSL_CERT_FILE=/opt/homebrew/etc/ca-certificates/cert.pem \
  uv run --python 3.14 emudhra-we-have-a-problem/urllib3_checker.py
```

| ホスト | 既定 | Homebrew (`SSL_CERT_FILE`) |
| --- | --- | --- |
| dv-g3b-emudhra.we-have-a-problem.com | ACCEPTED | REJECTED |
| dv-g3b-aaa-emudhra.we-have-a-problem.com | ACCEPTED | REJECTED |
| dv-g3b-noct-emudhra.we-have-a-problem.com | ACCEPTED | REJECTED |
| dv-g3b-aaa-noct-emudhra.we-have-a-problem.com | ACCEPTED | REJECTED |
| www.python.org | ACCEPTED | ACCEPTED |

実測時の依存パッケージ:

```text
urllib3==2.8.0
```

検証: 既定・Homebrew指定での実サーバー5ホストへの接続、構文、ラップされた証明書エラー、
一般TLS/DNS/タイムアウトをUNKNOWNにする分類、終了コード0/1/2、無効なtimeout（0・負数・NaN・無限大）を確認。

## CAの内容と結果の解釈

接続実験に加え、同じ環境で各バンドルを `ssl.SSLContext.load_verify_locations()` に読み込み、
`get_ca_certs()` のsubject commonNameを調べた。wassimaは `generate_ca_bundle()` の戻り値を調べた。

| CAソース | CA数 | emSign ECC Root CA - G3 | AAA Certificate Services |
| --- | --- | --- | --- |
| システムPEM | 128 | 含む | 含む |
| Homebrew PEM | 189 | 含まない | 含まない |
| certifi 2026.10.19 | 120 | 含まない | 含まない |
| wassima 2.1.5の生成バンドル | 158 | 含む | 含む |

この実測では **aiohttp・niquests・urllib3にデモチェーンを受け入れる挙動があり、適切なCA環境変数でHomebrewを指定すると拒否に変わった**。
urllibも同じ変化を示した。requests/httpx/httpxyzは今回取得したcertifiで既に拒否し、httpx2はmacOSの検証機能でブロックした。
「OSの証明書を使う」だけでは、PEMの鮮度やOSのブロック情報が適用されるかは判断できない。

Homebrew・certifiでの `unable to get local issuer certificate` と対象2ルートが含まれない事実は整合する。
これはルートを除外した今回のチェーンに対する結果であり、すべての侵害中間CA・別チェーン・過去バージョンを網羅しない。
CAバンドルの差し替えは他サイトの信頼性にも影響し得る。HTTP/2・HTTP/3の各経路や非同期版の別APIは個別に強制して検証していない。
