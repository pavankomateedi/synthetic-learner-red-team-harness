"""Render the dashboard to a static site (for GitHub Pages / any static host).

The dashboard is deterministic, server-rendered HTML with no client-side JS, so
a static export is identical to the live FastAPI app. Writes index.html,
metrics.json, and .nojekyll into the output directory.

    python scripts/build_static.py <output_dir> [seeds]
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
    seeds = sys.argv[2] if len(sys.argv) > 2 else "25"
    os.environ["SLH_WEB_SEEDS"] = seeds

    # Import after the env var is set so the cached loop uses the right seeds.
    from slh import web

    web._loop.cache_clear()
    pages = {
        "index.html":   web.dashboard().body.decode("utf-8"),
        "teacher.html": web.dashboard_teacher().body.decode("utf-8"),
        "parents.html": web.dashboard_parents().body.decode("utf-8"),
    }
    metrics = web.api_metrics().body.decode("utf-8")

    # Re-point dynamic endpoints at the static artifact (no server on Pages).
    # Any page that should contain the API link MUST have it rewritten; if the
    # target string drifts we fail loudly instead of silently shipping a broken
    # absolute link on GitHub Pages.
    api_old = '<a href="/api/metrics">/api/metrics</a>'
    api_new = '<a href="metrics.json">metrics.json</a>'
    pages_expected_to_link = {"index.html"}  # only the engineering view links it today
    for name, html in pages.items():
        if name in pages_expected_to_link:
            if api_old not in html:
                raise SystemExit(
                    f"build_static: page {name!r} was expected to contain "
                    f"{api_old!r} for rewrite to {api_new!r}, but it's not there. "
                    "The dashboard footer has drifted -- update either the "
                    "footer in slh/web.py or this rewrite target so the static "
                    "export doesn't ship a broken absolute /api/metrics link."
                )
            html = html.replace(api_old, api_new)
        pages[name] = html

    out.mkdir(parents=True, exist_ok=True)
    for name, html in pages.items():
        (out / name).write_text(html, encoding="utf-8")
    (out / "metrics.json").write_text(metrics, encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")
    sizes = ", ".join(f"{n}={len(h)}b" for n, h in pages.items())
    print(f"wrote 3 pages -> {out} ({sizes}), metrics.json, .nojekyll")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
