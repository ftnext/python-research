#!/usr/bin/env python3
"""Check whether this Python accepts eMudhra's compromised demo TLS chains.

Run with the Python interpreter you want to check; only the standard library is
required. Uses urllib.request with ssl.create_default_context(), contacting four
public demo hosts and www.python.org as a connectivity control. Two demo hosts
serve certificates not logged to Certificate Transparency (CT).

Examples:
    python urllib_checker.py
    uv run --python 3.14 python urllib_checker.py --verbose
    SSL_CERT_FILE=/opt/homebrew/etc/ca-certificates/cert.pem python urllib_checker.py

CA sources depend on the Python distribution and environment. Set SSL_CERT_FILE
or SSL_CERT_DIR to select CA sources. No certificates or settings are modified.
Connections are direct (HTTP(S)_PROXY is ignored) and redirects are not followed.
An HTTP response, including an HTTP error, means TLS verification succeeded.

Results and exit status:
    1 / ACTION REQUIRED: at least one demo chain was accepted.
    0 / REVIEW REQUIRED: all four chains failed certificate verification and the
        control succeeded. Review the reasons: expiry or hostname mismatch alone
        does not establish that the compromised intermediates are distrusted.
    2 / INCONCLUSIVE: no demo chain was accepted, but a connection/control check
        failed or the CA configuration could not be loaded.

This tests these four chains using this interpreter's stdlib TLS configuration,
not all compromised intermediates or TLS security in general. It does not test
pip, uv itself, Requests, or browsers. Results depend on the demo servers' current
certificates and availability. --verbose shows CA settings and per-host results.
ANSI colors are enabled on terminals unless NO_COLOR is set.

Reference: https://emudhra.we-have-a-problem.com/
"""

import argparse
from collections import Counter
import http.client
import os
import ssl
import sys
import urllib.error
import urllib.request


DEMO_HOSTS = (
    "dv-g3b-emudhra.we-have-a-problem.com",
    "dv-g3b-aaa-emudhra.we-have-a-problem.com",
    "dv-g3b-noct-emudhra.we-have-a-problem.com",
    "dv-g3b-aaa-noct-emudhra.we-have-a-problem.com",
)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def probe(context, host, timeout):
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=context),
        NoRedirect(),
    )
    try:
        with opener.open("https://{}/".format(host), timeout=timeout) as response:
            return "ACCEPTED", "TLS succeeded; HTTP {}".format(response.status)
    except urllib.error.HTTPError as exc:
        # An HTTP response (including an unfollowed redirect) means that TLS
        # verification of the original host already succeeded.
        exc.close()
        return "ACCEPTED", "TLS succeeded; HTTP {}".format(exc.code)
    except (urllib.error.URLError, OSError, http.client.HTTPException) as exc:
        reason = exc.reason if isinstance(exc, urllib.error.URLError) else exc
        if isinstance(reason, ssl.SSLCertVerificationError):
            return "REJECTED", "code={}: {}".format(
                reason.verify_code, reason.verify_message
            )
        return "UNKNOWN", "{}: {}".format(type(exc).__name__, exc)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--timeout", type=float, default=5.0,
                        help="Socket timeout in seconds (default: 5)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Show CA settings and per-host results")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")

    def colored(message, code):
        # ANSI only; keep redirected logs and NO_COLOR output readable.
        if sys.stdout.isatty() and "NO_COLOR" not in os.environ:
            message = "\033[{}m{}\033[0m".format(code, message)
        return message

    def heading(message, code):
        print(colored(message, code))

    paths = ssl.get_default_verify_paths()
    cafile = paths.cafile
    try:
        context = ssl.create_default_context()
    except (OSError, ssl.SSLError) as exc:
        heading("[INCONCLUSIVE] Cannot load CA configuration", "1;33")
        print("Reason:", exc)
        return 2

    control_state, control_detail = probe(context, "www.python.org", args.timeout)
    results = [(host, *probe(context, host, args.timeout)) for host in DEMO_HOSTS]
    accepted = sum(state == "ACCEPTED" for _, state, _ in results)
    rejected = sum(state == "REJECTED" for _, state, _ in results)
    unknown = sum(state == "UNKNOWN" for _, state, _ in results)
    noct_accepted = sum(state == "ACCEPTED" and "-noct-" in host
                        for host, state, _ in results)
    control_ok = control_state == "ACCEPTED"

    if accepted:
        heading("[ACTION REQUIRED] Compromised certificate chains accepted ({}/4)".format(accepted),
                "1;31")
        print("This Python TLS verifier accepted chains using compromised intermediates.")
        if noct_accepted:
            print("Certificates not logged to Certificate Transparency were also accepted ({}/2).".format(noct_accepted))
        print("Action: select an updated CA bundle and run this check again.")
        exit_code = 1
    elif unknown or not control_ok:
        heading("[INCONCLUSIVE] Check connectivity and error details", "1;33")
        print("Network errors or a failed control check prevent a conclusion.")
        exit_code = 2
    else:
        heading("[REVIEW REQUIRED] Certificate verification rejected all demo chains (4/4)", "1;33")
        print("Review the reasons below to confirm they match the expected rejection.")
        print("Expiry or hostname mismatch alone does not establish that this issue is fixed.")
        exit_code = 0

    print()
    print("Python:", sys.version.split()[0])
    print("CA file resolved:", os.path.realpath(cafile) if cafile else
          "None (CA directories or other sources; see --verbose)")
    print("Control (www.python.org):", "connection succeeded" if control_ok else "check failed")
    accepted_text = "{} accepted".format(accepted)
    if exit_code == 1:
        accepted_text = colored(accepted_text, "31")
    print("Results: {} / {} certificate rejections / {} inconclusive".format(
        accepted_text, rejected, unknown))
    if not control_ok:
        print("Control error:", control_detail)
    for detail, count in Counter(detail for _, state, detail in results
                                 if state == "REJECTED").items():
        message = "Rejection reason ({} connections): {}".format(count, detail)
        if exit_code == 0:
            heading(message, "33")
        else:
            print(message)
    for detail, count in Counter(detail for _, state, detail in results
                                 if state == "UNKNOWN").items():
        print("Connection error ({} connections): {}".format(count, detail))

    if args.verbose:
        print("\n--- Details ---")
        print("Python executable:", sys.executable)
        print("OpenSSL:", ssl.OPENSSL_VERSION)
        print("Default CA paths:", paths)
        for name in ("SSL_CERT_FILE", "SSL_CERT_DIR"):
            print("{}={!r}".format(name, os.environ.get(name)))
        print("Verifier: ssl.create_default_context() defaults")
        print("CONTROL {} www.python.org: {}".format(control_state, control_detail))
        for host, state, detail in results:
            print("{} {}: {}".format(state, host, detail))
    else:
        print("For details, run with --verbose.")
    print("Scope: direct connections using stdlib ssl; (pip, uv, and Requests are not tested.)")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
