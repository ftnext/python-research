# HTTPクライアントのベンチマーク

Pythonの非同期HTTPクライアントについて、HTTP/1.1の接続再利用が直列・並列リクエストの所要時間に与える影響を、実行日ごとに記録します。測定コードは [ftnext/gfx-benchmark-python-httpx-vs-aiohttp](https://github.com/ftnext/gfx-benchmark-python-httpx-vs-aiohttp) を参照しています。

| 実行日（JST） | 環境 | 内容 |
| --- | --- | --- |
| [2026-11-25](2026-11-25/) | Ubuntu 22.04.5、Python 3.13.7 | 元のロックでの再測定と、当日時点のPyPI最新安定版の比較 |
