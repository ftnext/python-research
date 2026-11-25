# Async HTTP client benchmark

Python 3.13.7; Linux-6.8.0-1060-aws-x86_64-with-glibc2.35; 10 server workers; HTTP/1.1 over localhost.

5 rounds, 1000 serial requests, 100 concurrent requests × 10 batches per case.

Each cell is the median of per-round mean times; brackets show the minimum–maximum of those means. Ratio = reuse / no reuse; below 1 is faster.

## Parallel (ms/batch)

| Client | No reuse | Reuse | Ratio | Per-round ratio range |
|---|---:|---:|---:|---:|
| httpx | 99.72 [92.62–107.36] | 559.36 [557.32–579.62] | 5.61 | 5.33–6.02 |
| httpxyz | 110.30 [108.26–123.58] | 141.01 [135.49–151.34] | 1.28 | 1.17–1.37 |
| httpx2 | 69.56 [68.64–70.33] | 114.76 [113.22–119.61] | 1.65 | 1.61–1.71 |
| niquests-10 | 82.55 [78.44–97.62] | 49.70 [45.39–53.56] | 0.60 | 0.50–0.60 |
| niquests-100 | 73.49 [68.26–95.46] | 54.44 [45.27–68.30] | 0.74 | 0.64–0.83 |
| aiohttp | 19.06 [17.66–22.70] | 8.13 [7.51–10.12] | 0.43 | 0.36–0.46 |

## Serial (ms/request)

| Client | No reuse | Reuse | Ratio | Per-round ratio range |
|---|---:|---:|---:|---:|
| httpx | 1.50 [1.39–1.53] | 0.76 [0.73–0.79] | 0.51 | 0.49–0.54 |
| httpxyz | 1.46 [1.39–1.53] | 0.73 [0.72–1.02] | 0.50 | 0.47–0.69 |
| httpx2 | 1.08 [1.01–1.13] | 0.51 [0.46–0.60] | 0.47 | 0.42–0.59 |
| niquests-10 | 1.11 [1.08–1.24] | 0.59 [0.56–0.67] | 0.53 | 0.47–0.59 |
| niquests-100 | 1.08 [1.07–1.38] | 0.57 [0.56–0.75] | 0.52 | 0.52–0.54 |
| aiohttp | 0.39 [0.37–0.40] | 0.14 [0.14–0.20] | 0.35 | 0.35–0.50 |

## Versions

| Package | Version |
|---|---|
| aiohappyeyeballs | 2.7.1 |
| aiohttp | 3.14.5 |
| aiosignal | 1.4.0 |
| anyio | 4.16.0 |
| attrs | 26.1.0 |
| certifi | 2026.11.20 |
| charset-normalizer | 3.5.3 |
| frozenlist | 1.8.0 |
| h11 | 0.16.0 |
| httpcore | 1.0.9 |
| httpcore2 | 2.16.2 |
| httpcorexyz | 1.2.1 |
| httpx | 0.28.1 |
| httpx2 | 2.16.2 |
| httpxyz | 0.42.1 |
| idna | 3.20 |
| jh2 | 5.0.15 |
| multidict | 7.2.1 |
| niquests | 3.21.3 |
| propcache | 0.5.4 |
| qh3 | 2.1.0 |
| truststore | 0.10.5 |
| typing_extensions | 4.16.0 |
| urllib3-future | 2.25.907 |
| wassima | 2.1.5 |
| yarl | 1.25.1 |

## Method

- One client/session per measurement, reused across all requests/batches.
- Warmup uses a separate client. First measured connections/batches are included.
- Every response is checked for HTTP 200 and the complete expected body.
- HTTPX-family clients use explicit Limits(), or zero keep-alive retention.
- aiohttp uses force_close; Niquests uses Connection: close to disable reuse.
- Niquests uses AsyncSession, multiplexed=False, HTTP/2 and HTTP/3 disabled.
- niquests-10 and niquests-100 specify pool_maxsize; other settings are defaults.
- A separate five-request check verifies one vs five TCP connections for every client.
- Cases are shuffled each round using the recorded seed. No CPU pinning.
- Batch timings are not individual-request latency. Results apply to this local workload.
- Raw timings and environment are saved alongside this report.
