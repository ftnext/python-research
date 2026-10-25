#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = ["httpxyz==0.42.1"]
# ///
"""Probe eMudhra demo chains and www.python.org using httpxyz's default TLS verifier.

    uv run --python 3.14 httpxyz_checker.py
    SSL_CERT_FILE=/opt/homebrew/etc/ca-certificates/cert.pem uv run --python 3.14 httpxyz_checker.py

Native CA environment variables are honored. No custom SSLContext or verify=False
is used. Proxies and redirects are disabled; any HTTP status means TLS succeeded.
Exit: 1 = demo accepted; 0 = all demos rejected and control accepted (review
reasons); 2 = inconclusive. No global certificate configuration is changed.
"""

import argparse
from importlib.metadata import distributions
import math
import os
import ssl
import sys


DEMO_HOSTS = (
    "dv-g3b-emudhra.we-have-a-problem.com",
    "dv-g3b-aaa-emudhra.we-have-a-problem.com",
    "dv-g3b-noct-emudhra.we-have-a-problem.com",
    "dv-g3b-aaa-noct-emudhra.we-have-a-problem.com",
)
CONTROL = "www.python.org"
CA_VARIABLES = ("SSL_CERT_FILE", "SSL_CERT_DIR", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE")


def classify_error(exc):
    """Inspect wrapped TLS errors; DNS/timeouts/general TLS errors stay UNKNOWN."""
    pending, seen = [exc], set()
    verification_marker = None
    while pending:
        error = pending.pop()
        if id(error) in seen:
            continue
        seen.add(id(error))
        # aiohttp wrappers inherit this type without verify_code/message.
        if (isinstance(error, ssl.SSLCertVerificationError)
                and hasattr(error, "verify_code")
                and hasattr(error, "verify_message")):
            return "REJECTED", f"code={error.verify_code}: {error.verify_message}"
        # Some backends preserve only OpenSSL's verification marker in text.
        if "CERTIFICATE_VERIFY_FAILED" in str(error):
            verification_marker = f"{type(error).__name__}: {error}"
        for nested in (error.__cause__, error.__context__,
                       getattr(error, "reason", None),
                       getattr(error, "certificate_error", None), *error.args):
            if isinstance(nested, BaseException):
                pending.append(nested)
    if verification_marker is not None:
        return "REJECTED", verification_marker
    return "UNKNOWN", f"{type(exc).__name__}: {exc}"


def report(results):
    control_ok = results[0][1] == "ACCEPTED"
    demo_states = [state for _, state, _ in results[1:]]
    accepted = demo_states.count("ACCEPTED")
    rejected = demo_states.count("REJECTED")
    unknown = demo_states.count("UNKNOWN")
    if accepted:
        label, code = "ACTION REQUIRED", 1
    elif not control_ok or unknown:
        label, code = "INCONCLUSIVE", 2
    else:
        label, code = "REVIEW REQUIRED", 0
    print(f"[{label}] {accepted} accepted / {rejected} certificate rejections / {unknown} inconclusive")
    for host, state, detail in results:
        role = "CONTROL " if host == CONTROL else ""
        print(f"{role}{state} {host}: {detail}")
    print("Scope: these four demo chains only; rejection reasons require review.")
    print("Expiry/hostname errors alone do not establish distrust of compromised intermediates.")
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=5.0,
                        help="Per-request/socket timeout in seconds (default: 5)")
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be finite and positive")

    # Keep native CA environment handling enabled, but force direct requests.
    # This affects only this process, including libraries imported below.
    for name in list(os.environ):
        if name.lower() in {"http_proxy", "https_proxy", "all_proxy"}:
            os.environ.pop(name)
    os.environ["NO_PROXY"] = "*"
    os.environ["no_proxy"] = "*"
    print("Python:", sys.version.split()[0], sys.executable)
    print("OpenSSL:", ssl.OPENSSL_VERSION)
    print("stdlib default CA paths (not necessarily this client's CA source):",
          ssl.get_default_verify_paths())
    print("Packages:", ", ".join(sorted(
        f"{dist.metadata['Name']}=={dist.version}" for dist in distributions()
    )))
    for name in CA_VARIABLES:
        print(f"{name}={os.environ.get(name)!r}")
    print("Proxy: disabled; redirects: disabled; TLS verification: library default")
    try:
        results = check(args.timeout)
    except (OSError, ValueError, RuntimeError, ssl.SSLError) as exc:
        print(f"[INCONCLUSIVE] Client/CA initialization failed: {type(exc).__name__}: {exc}")
        return 2
    return report(results)


def check(timeout):
    import httpxyz

    results = []
    with httpxyz.Client(timeout=timeout, follow_redirects=False) as client:
        for host in (CONTROL, *DEMO_HOSTS):
            try:
                with client.stream("GET", f"https://{host}/") as response:
                    state, detail = "ACCEPTED", f"TLS succeeded; HTTP {response.status_code}"
            except (httpxyz.RequestError, OSError) as exc:
                state, detail = classify_error(exc)
            results.append((host, state, detail))
    return results


if __name__ == "__main__":
    sys.exit(main())
