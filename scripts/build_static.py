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
    for name, html in pages.items():
        old = '<a href="/api/metrics">/api/metrics</a>'
        new = '<a href="metrics.json">metrics.json</a>'
        if old in html:
            html = html.replace(old, new)
        old2 = ' &middot;\n      health at <a href="/healthz">/healthz</a>'
        if old2 in html:
            html = html.replace(old2, "")
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
