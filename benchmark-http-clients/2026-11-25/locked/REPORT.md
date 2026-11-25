# Async HTTP client benchmark

Python 3.13.7; Linux-6.8.0-1060-aws-x86_64-with-glibc2.35; 10 server workers; HTTP/1.1 over localhost.

5 rounds, 1000 serial requests, 100 concurrent requests × 10 batches per case.

Each cell is the median of per-round mean times; brackets show the minimum–maximum of those means. Ratio = reuse / no reuse; below 1 is faster.

## Parallel (ms/batch)

| Client | No reuse | Reuse | Ratio | Per-round ratio range |
|---|---:|---:|---:|---:|
| httpx | 101.02 [97.85–109.67] | 567.23 [564.83–576.15] | 5.62 | 5.21–5.89 |
| httpxyz | 124.65 [112.19–132.94] | 140.68 [135.84–141.08] | 1.13 | 1.06–1.26 |
| httpx2 | 84.12 [68.43–110.56] | 115.52 [110.70–123.13] | 1.37 | 1.11–1.62 |
| niquests-10 | 86.30 [83.02–112.75] | 46.07 [43.76–49.25] | 0.53 | 0.41–0.57 |
| niquests-100 | 78.03 [70.26–89.85] | 48.49 [46.50–55.98] | 0.62 | 0.59–0.75 |
| aiohttp | 18.98 [18.04–23.99] | 8.39 [7.20–10.93] | 0.44 | 0.31–0.50 |

## Serial (ms/request)

| Client | No reuse | Reuse | Ratio | Per-round ratio range |
|---|---:|---:|---:|---:|
| httpx | 1.50 [1.44–1.64] | 0.77 [0.75–1.20] | 0.51 | 0.46–0.80 |
| httpxyz | 1.57 [1.38–1.65] | 0.73 [0.72–0.82] | 0.47 | 0.44–0.57 |
| httpx2 | 1.22 [1.05–1.48] | 0.49 [0.47–0.52] | 0.40 | 0.35–0.47 |
| niquests-10 | 1.17 [1.08–1.37] | 0.59 [0.55–0.62] | 0.50 | 0.43–0.56 |
| niquests-100 | 1.17 [1.15–1.29] | 0.64 [0.62–0.72] | 0.55 | 0.51–0.58 |
| aiohttp | 0.37 [0.36–0.49] | 0.16 [0.13–0.20] | 0.44 | 0.30–0.53 |

## Versions

| Package | Version |
|---|---|
| aiohappyeyeballs | 2.7.1 |
| aiohttp | 3.12.15 |
| aiosignal | 1.4.0 |
| anyio | 4.15.1 |
| attrs | 26.1.0 |
| certifi | 2026.7.22 |
| charset-normalizer | 3.5.1 |
| frozenlist | 1.8.0 |
| h11 | 0.16.0 |
| httpcore | 1.0.9 |
| httpcore2 | 2.12.0 |
| httpcorexyz | 1.2.1 |
| httpx | 0.28.1 |
| httpx2 | 2.12.0 |
| httpxyz | 0.31.2 |
| idna | 3.20 |
| jh2 | 5.0.14 |
| multidict | 6.9.0 |
| niquests | 3.21.1 |
| propcache | 0.5.4 |
| qh3 | 2.0.3 |
| truststore | 0.10.4 |
| typing_extensions | 4.16.0 |
| urllib3-future | 2.24.908 |
| wassima | 2.1.4 |
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
