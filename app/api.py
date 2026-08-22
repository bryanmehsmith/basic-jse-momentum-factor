"""Tiny JSON API backing the "live yfinance refresh" toggle in the static frontend.

The frontend (frontend/) does the actual momentum signal, backtest, and
performance math client-side in JS against a bundled monthly snapshot
(frontend/js/data/prices.json). This process exists only for the one case that
JS in a browser cannot do itself: pulling fresh prices from Yahoo Finance. It
wraps the existing `get_prices()` fallback chain (fresh cache -> live download
-> stale cache -> bundled snapshot) unchanged, resamples to month-end, and
hands the frontend the same JSON shape as the bundled snapshot file.

Started on demand and reaped when idle by the same launcher.py machinery the
other Streamlit demos use (see demos.json's "api" kind). Deliberately stdlib
only, no web framework, to keep this process's memory footprint small: it is
the price paid only by a visitor who actually flips the live-refresh toggle.
"""

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import pandas as pd

from momentum_factor.data import get_prices

DEFAULT_PORT = 8501
MAX_TICKERS = 25


def monthly_payload(tickers: list[str], start: str, force_refresh: bool) -> dict:
    prices = get_prices(tickers, start=start, force_refresh=force_refresh)
    monthly = prices.resample("ME").last()
    return {
        "dates": [d.strftime("%Y-%m-%d") for d in monthly.index],
        "prices": {
            ticker: [None if pd.isna(v) else round(float(v), 4) for v in monthly[ticker]]
            for ticker in monthly.columns
        },
    }


class Handler(BaseHTTPRequestHandler):
    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.rstrip("/") != "/prices":
            self._json(404, {"error": f"unknown route {parsed.path!r}"})
            return

        query = parse_qs(parsed.query)
        tickers = [t for t in query.get("tickers", [""])[0].split(",") if t]
        start = query.get("start", ["2015-01-01"])[0]
        force_refresh = query.get("refresh", ["false"])[0].lower() == "true"

        if not tickers:
            self._json(400, {"error": "at least one ticker is required"})
            return
        if len(tickers) > MAX_TICKERS:
            self._json(400, {"error": f"too many tickers requested (max {MAX_TICKERS})"})
            return

        try:
            self._json(200, monthly_payload(tickers, start, force_refresh))
        except Exception as exc:
            print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
            self._json(502, {"error": "internal error"})

    def log_message(self, format: str, *args) -> None:
        pass


def main() -> None:
    # Defaults to loopback-only: in the demo-site deployment, launcher.py starts
    # this process for Caddy to reverse_proxy to on the same host, and it should
    # never be reachable except through that proxy. The standalone Dockerfile in
    # this repo passes --host=0.0.0.0 instead, since there Docker's own port
    # mapping is the access boundary.
    host = "127.0.0.1"
    port = DEFAULT_PORT
    for arg in sys.argv[1:]:
        if arg.startswith("--port="):
            port = int(arg.split("=", 1)[1])
        elif arg.startswith("--host="):
            host = arg.split("=", 1)[1]
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
