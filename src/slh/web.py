"""FastAPI dashboard for the Synthetic Learner Red Team Harness.

Serves the baseline -> improved comparison, the PRD-8.2 counter-metrics, the
per-persona breakdown, the golden-set status, and the failure reports — all
rendered straight from the in-memory harness objects (no markdown dependency).

Run locally:
    uvicorn slh.web:app --reload
    # or
    slh-web

The harness run is cached on first request (it is deterministic, so there is
nothing to refresh unless the seed count changes). Set the seed count with the
SLH_WEB_SEEDS env var.
"""

from __future__ import annotations

import html
import os
from functools import lru_cache

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

from .comparator import ComparisonReport
from .evaluator import DIMENSIONS, TutorMetrics
from .goldenset import check_behaviors, check_population
from .harness import LoopResult, run_improvement_loop
from .report import FAILURE_THRESHOLDS

app = FastAPI(title="Synthetic Learner Red Team Harness", version="1.0.0")


def _seeds() -> int:
    try:
        return max(1, int(os.environ.get("SLH_WEB_SEEDS", "25")))
    except ValueError:
        return 25


@lru_cache(maxsize=4)
def _loop(seeds: int) -> LoopResult:
    return run_improvement_loop(n_seeds=seeds)


def _golden(loop: LoopResult) -> tuple[int, int]:
    results = check_population({"v1": loop.baseline, "v2": loop.improved},
                              loop.comparison) + check_behaviors()
    passed = sum(1 for r in results if r.passed)
    return passed, len(results)


# --- HTML helpers ----------------------------------------------------------

_CSS = """
:root{--bg:#0f1419;--card:#1a212b;--line:#2a3441;--ink:#e6edf3;--mut:#8b98a5;
--good:#2ea043;--bad:#f85149;--warn:#d29922;--accent:#58a6ff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.5 ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.wrap{max-width:1040px;margin:0 auto;padding:32px 20px 80px}
h1{font-size:26px;margin:0 0 4px}h2{font-size:17px;margin:34px 0 12px;color:var(--ink)}
.sub{color:var(--mut);margin:0 0 24px}
.banner{padding:16px 20px;border-radius:12px;border:1px solid var(--line);
background:var(--card);display:flex;gap:24px;flex-wrap:wrap;align-items:center}
.banner .big{font-size:20px;font-weight:650}
.pill{padding:2px 10px;border-radius:999px;font-size:12px;font-weight:600}
.pill.good{background:rgba(46,160,67,.15);color:var(--good)}
.pill.bad{background:rgba(248,81,73,.15);color:var(--bad)}
.pill.warn{background:rgba(210,153,34,.15);color:var(--warn)}
table{width:100%;border-collapse:collapse;background:var(--card);
border:1px solid var(--line);border-radius:12px;overflow:hidden}
th,td{padding:10px 14px;text-align:left;border-bottom:1px solid var(--line);font-size:14px}
th{color:var(--mut);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.04em}
tr:last-child td{border-bottom:0}
td.num{font-variant-numeric:tabular-nums;text-align:right}
.delta-up{color:var(--good)}.delta-down{color:var(--bad)}.delta-flat{color:var(--mut)}
code{background:#0d1117;padding:1px 6px;border-radius:5px;font-size:13px;color:var(--accent)}
.cell-fail{color:var(--bad);font-weight:600}.cell-ok{color:var(--mut)}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.foot{margin-top:40px;color:var(--mut);font-size:13px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
@media(max-width:720px){.grid{grid-template-columns:1fr}}
"""


def _esc(x: object) -> str:
    return html.escape(str(x))


def _pill(verdict: str) -> str:
    cls = {"pass": "good", "fail": "bad", "warn": "warn"}.get(verdict, "warn")
    return f'<span class="pill {cls}">{_esc(verdict)}</span>'


def _page(title: str, body: str) -> str:
    return (f"<!doctype html><html lang=en><head><meta charset=utf-8>"
            f"<meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<title>{_esc(title)}</title><style>{_CSS}</style></head>"
            f"<body><div class=wrap>{body}</div></body></html>")


def _metrics_table(cmp: ComparisonReport) -> str:
    rows = []
    for d in cmp.deltas:
        if d.regressed:
            cls, status = "delta-down", "regression"
        elif d.improved_flag:
            cls, status = "delta-up", "improved"
        else:
            cls, status = "delta-flat", "~flat"
        rows.append(
            f"<tr><td><code>{_esc(d.name)}</code></td>"
            f"<td class=num>{d.baseline:.3f}</td>"
            f"<td class=num>{d.improved:.3f}</td>"
            f"<td class='num {cls}'>{d.oriented_delta:+.3f}</td>"
            f"<td class={cls}>{status}</td></tr>")
    return ("<table><tr><th>Dimension</th><th>Baseline</th><th>Improved</th>"
            "<th>&Delta; (better)</th><th>Status</th></tr>"
            + "".join(rows) + "</table>")


def _counter_table(cmp: ComparisonReport) -> str:
    rows = [
        f"<tr><td><code>{_esc(c.name)}</code></td><td>{_esc(c.question)}</td>"
        f"<td>{_pill(c.verdict)}</td><td>{_esc(c.detail)}</td></tr>"
        for c in cmp.counter_metrics
    ]
    return ("<table><tr><th>Counter-metric</th><th>Question</th><th>Verdict</th>"
            "<th>Detail</th></tr>" + "".join(rows) + "</table>")


def _is_failing(name: str, value: float) -> bool:
    thr = FAILURE_THRESHOLDS[name]
    return value < thr if DIMENSIONS[name] > 0 else value > thr


def _persona_table(m: TutorMetrics) -> str:
    dims = list(DIMENSIONS)
    head = "".join(f"<th>{_esc(d.split('_')[0])}</th>" for d in dims)
    rows = []
    for pid, scores in m.per_persona.items():
        sd = scores.as_dict()
        cells = "".join(
            f"<td class='num {'cell-fail' if _is_failing(d, sd[d]) else 'cell-ok'}'>"
            f"{sd[d]:.2f}</td>" for d in dims)
        rows.append(f"<tr><td>{_esc(pid)}</td>{cells}</tr>")
    return (f"<table><tr><th>Persona</th>{head}</tr>" + "".join(rows) + "</table>")


def _failure_section(m: TutorMetrics) -> str:
    overall = m.overall.as_dict()
    failing = [n for n, v in overall.items() if _is_failing(n, v)]
    if not failing:
        return "<p class=sub>No dimension below its failure threshold.</p>"
    items = "".join(f"<li><code>{_esc(n)}</code> = {overall[n]:.3f}</li>" for n in failing)
    return f"<ul>{items}</ul>"


# --- routes ----------------------------------------------------------------

@app.get("/healthz")
def healthz() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.get("/api/metrics")
def api_metrics() -> JSONResponse:
    loop = _loop(_seeds())
    passed, total = _golden(loop)
    return JSONResponse({
        "seeds": _seeds(),
        "n_sessions_per_tutor": loop.baseline.n_sessions,
        "golden": {"passed": passed, "total": total},
        "baseline": loop.baseline.overall.as_dict(),
        "improved": loop.improved.overall.as_dict(),
        "deltas": {d.name: d.oriented_delta for d in loop.comparison.deltas},
        "regressions": loop.comparison.regressions,
        "counter_metrics": {c.name: c.verdict for c in loop.comparison.counter_metrics},
        "overall_improved": loop.comparison.overall_improved,
    })


@app.get("/", response_class=HTMLResponse)
def dashboard() -> HTMLResponse:
    loop = _loop(_seeds())
    cmp = loop.comparison
    passed, total = _golden(loop)
    n_improved = sum(1 for d in cmp.deltas if d.improved_flag)

    verdict_ok = cmp.overall_improved
    verdict_pill = (f'<span class="pill {"good" if verdict_ok else "warn"}">'
                    f'{"real improvement" if verdict_ok else "inconclusive"}</span>')
    golden_pill = (f'<span class="pill {"good" if passed == total else "bad"}">'
                   f'{passed}/{total} golden checks</span>')
    cm_fail = any(c.verdict == "fail" for c in cmp.counter_metrics)
    cm_pill = (f'<span class="pill {"bad" if cm_fail else "good"}">'
               f'{"a counter-metric FAILED" if cm_fail else "all counter-metrics pass"}</span>')

    if cmp.regressions:
        reg_items = "".join(f"<li class=cell-fail><code>{_esc(r)}</code></li>"
                            for r in cmp.regressions)
        regression_html = f"<ul>{reg_items}</ul>"
    else:
        regression_html = "<p class=sub>No regressions (overall or per persona).</p>"

    body = f"""
    <h1>Synthetic Learner Red Team Harness</h1>
    <p class=sub>AI fractions tutor &mdash; baseline <code>{_esc(cmp.baseline_name)}</code>
      vs improved <code>{_esc(cmp.improved_name)}</code> &middot;
      {loop.baseline.n_sessions} sessions/tutor &middot; {_seeds()} seeds &times; 8 personas</p>

    <div class=banner>
      <div class=big>Verdict</div>{verdict_pill}{golden_pill}{cm_pill}
    </div>

    <h2>Primary + supporting metrics (PRD &sect;8.1)</h2>
    {_metrics_table(cmp)}

    <h2>Counter-metrics &mdash; anti-gaming (PRD &sect;8.2)</h2>
    {_counter_table(cmp)}

    <h2>Regression check</h2>
    {regression_html}

    <h2>Per-persona breakdown (red = below failure threshold)</h2>
    {_persona_table(loop.improved)}

    <h2 class=grid-h>Failure modes</h2>
    <div class=grid>
      <div><h3>Baseline V1</h3>{_failure_section(loop.baseline)}</div>
      <div><h3>Improved V2</h3>{_failure_section(loop.improved)}</div>
    </div>

    <p class=foot>{n_improved}/7 dimensions improved meaningfully &middot;
      {len(cmp.regressions)} regression(s) &middot;
      JSON at <a href="/api/metrics">/api/metrics</a> &middot;
      health at <a href="/healthz">/healthz</a></p>
    """
    return HTMLResponse(_page("Synthetic Learner Red Team Harness", body))


def main() -> None:  # pragma: no cover - thin uvicorn launcher
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("slh.web:app", host="0.0.0.0", port=port)


if __name__ == "__main__":  # pragma: no cover
    main()
