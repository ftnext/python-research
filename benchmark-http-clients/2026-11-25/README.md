# 2026-11-25（JST） HTTPクライアントのベンチマーク

Ubuntu 22.04.5（x86_64、8 vCPU）、Python 3.13.7で、localhostのHTTP/1.1サーバーを10ワーカーで起動しました。元のロックと当日時点のPyPI最新安定版を、同じコードと測定条件で順に実行しました。[測定に使ったフォークのリビジョン](https://github.com/ftnext/gfx-benchmark-python-httpx-vs-aiohttp/tree/09606418cf8d8f45968b20e5a6d03dd783109b1e) · [元のmacOS実験](https://nikkie-ftnext.hatenablog.com/entry/gfx-benchmark-python-httpx-vs-aiohttp-add-httpx2-httpxyz-niquests)

各依存セットで、ランダム化した順に全条件を5ラウンドずつ測定しました。1条件あたり、各ラウンドで直列1,000件と100件並列×10バッチを測定しています。報告値はラウンドごとの平均の中央値です。別途、クライアントごとに5件を直列で送信し、再利用ありで1接続、なしで5接続になることを確認しました。

## 並列リクエスト

所要時間は100件をまとめた1バッチあたりのミリ秒です。倍率は接続再利用あり÷なしです。

| 2026-11-25時点のクライアント | 再利用なし | 再利用あり | 倍率 | 元のロックでの倍率 |
| --- | ---: | ---: | ---: | ---: |
| HTTPX 0.28.1 | 99.72 | 559.36 | 5.61 | 5.62 |
| HTTPXYZ 0.42.1 | 110.30 | 141.01 | 1.28 | 1.13 |
| HTTPX2 2.16.2 | 69.56 | 114.76 | 1.65 | 1.37 |
| Niquests 3.21.3（プール10） | 82.55 | 49.70 | 0.60 | 0.53 |
| Niquests 3.21.3（プール100） | 73.49 | 54.44 | 0.74 | 0.62 |
| aiohttp 3.14.5 | 19.06 | 8.13 | 0.43 | 0.44 |

両方の依存セットで、並列ではHTTPX・HTTPXYZ・HTTPX2が再利用ありで遅く、Niquestsとaiohttpは速くなりました。直列では全クライアントが速くなり、HTTPX2 2.16.2は1.08 ms/件から0.51 ms/件に短縮しました。

## レポートと測定データ

| 依存セット | 並列・直列の詳細 | 生データ | 実行環境 | 接続チェック |
| --- | --- | --- | --- | --- |
| PyPI最新安定版 | [レポート](current/REPORT.md) | [計測値](current/measurements.json) | [環境・バージョン](current/environment.json) | [接続数](current/connection-check.json) |
| 元のロック | [レポート](locked/REPORT.md) | [計測値](locked/measurements.json) | [環境・バージョン](locked/environment.json) | [接続数](locked/connection-check.json) |

## 再現手順

`python-research` のルートで実行します。出力ディレクトリは新規作成できる名前を指定します。

```sh
report_dir="$(pwd)/benchmark-http-clients/2026-11-25"
git clone https://github.com/ftnext/gfx-benchmark-python-httpx-vs-aiohttp.git
cd gfx-benchmark-python-httpx-vs-aiohttp
git checkout --detach 09606418cf8d8f45968b20e5a6d03dd783109b1e
uv venv --python 3.13.7 .venv

uv pip sync --python .venv/bin/python requirements.lock.txt
.venv/bin/python -u benchmark.py --workers 10 --output results-locked-rerun

uv pip sync --python .venv/bin/python "$report_dir/current/requirements.lock.txt"
.venv/bin/python -u benchmark.py --workers 10 --output results-current-rerun
```

測定コードとロックファイルのSHA-256、実際の実行コマンドは [provenance.json](provenance.json) に記録しています。
