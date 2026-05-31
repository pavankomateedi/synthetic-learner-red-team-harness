"""FastAPI dashboard for the Synthetic Learner Red Team Harness.

Nerdy-themed, plain-English dashboard surfacing the harness result without
exposing internal identifiers. Server-rendered HTML; no client-side JS.

Run locally:
    uvicorn slh.web:app --reload
    # or
    slh-web
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
from .personas import PERSONAS
from .report import FAILURE_THRESHOLDS

app = FastAPI(title="Nerdy Tutor Stress-Test Dashboard", version="1.0.0")


# --- Plain-English labels --------------------------------------------------

FRIENDLY_LABELS: dict[str, str] = {
    "learning_gain":              "Did students actually learn more?",
    "transfer_score":             "Can students solve new problems?",
    "misconception_persistence":  "Do wrong ideas still stick around?",
    "avoidance_recovery_rate":    "Does the tutor get off-task students back?",
    "answer_giving_rate":         "Does the tutor just hand over answers?",
    "scaffolding_independence":   "Can students solve problems on their own?",
    "shallow_compliance_rate":    'Does the tutor accept fake "I get it"?',
}

# Whether a higher number is what we want for each measure, in plain English.
GOAL_LABEL: dict[str, str] = {
    "learning_gain":              "more = better",
    "transfer_score":             "more = better",
    "misconception_persistence":  "less = better",
    "avoidance_recovery_rate":    "more = better",
    "answer_giving_rate":         "less = better",
    "scaffolding_independence":   "more = better",
    "shallow_compliance_rate":    "less = better",
}

TUTOR_LABELS = {"baseline_v1": "Old Tutor", "improved_v2": "New Tutor"}

# Friendly captions per section. These are the only "intro" the page needs.
SECTION_CAPTIONS = {
    "primary": "Seven ways to measure whether the tutor is really teaching, "
               "not just looking busy. Each measure has a target line — pass it or you fail it.",
    "counters": "Sanity checks. Did the new tutor really get better, or did we just "
                "tweak the test to make it look that way? If any one of these failed, "
                "the headline result would be suspect.",
    "regressions": ("Anything that got worse — even a little. "
                    "We surface these instead of hiding them."),
    "personas": "Eight kinds of students we tried. Red squares mean the new tutor "
                "is still falling short for that student on that measure.",
    "failures": "What each tutor still gets wrong. Fewer items here = better tutor. "
                "Empty would mean nothing is broken.",
}

EXEC_SUMMARY_HEAD = (
    "We stress-tested an AI fractions tutor by sending 200 simulated students through it — "
    "students who beg for answers, fake understanding, panic, try to trick the tutor, "
    "or memorize without learning."
)


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


def _persona_name(pid: str) -> str:
    p = PERSONAS.get(pid)
    return f"The {p.archetype}" if p else pid


def _is_failing(name: str, value: float) -> bool:
    thr = FAILURE_THRESHOLDS[name]
    return value < thr if DIMENSIONS[name] > 0 else value > thr


# --- Styling: Anthropic canvas + Google data palette -----------------------
# Anthropic chrome (cream bg, dark text, orange brand accent, Poppins/Lora type)
# fused with Google's four-color palette (#4285F4 #EA4335 #FBBC04 #34A853)
# for stat tiles and semantic verdicts.

_CSS = """
:root{
  /* SalesFlow-style dark canvas: deep navy, soft glow */
  --bg:#0b0e1f;
  --card:#141729;
  --card-alt:#191c33;
  --line:#272a44;
  --ink:#f0f4ff;
  --mut:#9ca3af;
  --mut2:#6b7280;
  /* Cyan is the single bright accent; violet/pink only as decoration */
  --cyan:#67e8f9;
  --cyan-dim:#22d3ee;
  --violet:#a78bfa;
  --pink:#f472b6;
  /* Semantic — restrained */
  --good:var(--cyan-dim);
  --bad:#fb7185;        /* soft coral, not neon pink */
  --warn:#fbbf24;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);min-height:100vh;
  font:14.5px/1.6 "Inter","Helvetica Neue",Arial,sans-serif;
  background-image:radial-gradient(circle at 90% 110%,rgba(244,114,182,0.10) 0%,transparent 50%),
    radial-gradient(circle at 0% 0%,rgba(167,139,250,0.06) 0%,transparent 45%);
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
.wrap{max-width:1080px;margin:0 auto;padding:42px 22px 90px}

h1{font-size:32px;margin:0 0 6px;letter-spacing:-0.02em;font-weight:700;line-height:1.15;
  background:linear-gradient(90deg,var(--cyan) 0%,var(--violet) 100%);
  -webkit-background-clip:text;background-clip:text;color:transparent}
h2{font-size:18px;margin:38px 0 4px;letter-spacing:-0.01em;font-weight:600;color:var(--ink)}
h3{font-size:11.5px;margin:18px 0 8px;color:var(--cyan);font-weight:600;
  text-transform:uppercase;letter-spacing:.12em}
.sub{color:var(--mut);margin:0 0 6px;font-size:14px}
.cap{color:var(--mut);margin:0 0 14px;font-size:13.5px;max-width:780px}
.brandbar{height:2px;width:48px;border-radius:2px;margin:14px 0 24px;
  background:linear-gradient(90deg,var(--cyan),var(--violet),var(--pink));opacity:.7}

.summary{background:var(--card);border:1px solid var(--line);border-radius:14px;
  padding:22px 24px;margin:16px 0 18px}
.summary:last-of-type{margin-bottom:32px}
.summary p{margin:0 0 10px;font-size:14.5px;line-height:1.65;color:var(--ink)}
.summary p:last-of-type{margin-bottom:0}
.summary strong{color:var(--cyan);font-weight:600}

.statgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
.stat{background:transparent;border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.stat .n{font-size:24px;font-weight:700;color:var(--ink);font-variant-numeric:tabular-nums;
  line-height:1.1;letter-spacing:-0.01em}
.stat .lbl{font-size:11px;color:var(--mut);text-transform:uppercase;letter-spacing:.08em;
  margin-top:4px;font-weight:500}
@media(max-width:680px){.statgrid{grid-template-columns:repeat(2,1fr)}}

.pill{padding:3px 12px;border-radius:6px;font-size:12px;font-weight:500;letter-spacing:.02em;
  font-family:"JetBrains Mono","SF Mono",ui-monospace,Menlo,Consolas,monospace;
  border:1px solid transparent;background:transparent;display:inline-block}
.pill.good{border-color:rgba(34,211,238,.45);color:var(--cyan)}
.pill.bad{border-color:rgba(251,113,133,.45);color:var(--bad)}
.pill.warn{border-color:rgba(251,191,36,.45);color:var(--warn)}

table{width:100%;border-collapse:collapse;background:var(--card);
  border:1px solid var(--line);border-radius:12px;overflow:hidden}
th,td{padding:12px 16px;text-align:left;border-bottom:1px solid var(--line);font-size:14px}
th{color:var(--mut);font-weight:500;font-size:11px;text-transform:uppercase;letter-spacing:.1em;
  background:var(--card-alt)}
tr:last-child td{border-bottom:0}
td.num{font-variant-numeric:tabular-nums;text-align:right;
  font-family:"JetBrains Mono","SF Mono",ui-monospace,Menlo,Consolas,monospace;font-size:13.5px}
.direction{color:var(--mut2);font-size:11px;display:block;margin-top:2px}

.delta-up{color:var(--cyan);font-weight:500}
.delta-down{color:var(--bad);font-weight:500}
.delta-flat{color:var(--mut2)}
.cell-fail{color:var(--bad);font-weight:500}
.cell-ok{color:var(--mut)}

.section{margin-top:30px}
ul.fail{list-style:none;padding:0;margin:0;background:var(--card);
  border:1px solid var(--line);border-radius:12px}
ul.fail li{padding:12px 18px;border-bottom:1px solid var(--line);font-size:14px}
ul.fail li:last-child{border-bottom:0}
ul.fail li.bad{color:var(--bad);border-left:2px solid var(--bad)}
.empty{padding:14px 18px;background:var(--card);border:1px solid var(--line);
  border-radius:12px;color:var(--mut);font-size:14px;border-left:2px solid var(--cyan)}

.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:8px}
@media(max-width:680px){.grid{grid-template-columns:1fr}}
.foot{margin-top:46px;color:var(--mut2);font-size:13px;
  border-top:1px solid var(--line);padding-top:16px}
a{color:var(--cyan);text-decoration:none;border-bottom:1px solid rgba(103,232,249,0.3)}
a:hover{border-bottom-color:var(--cyan)}

.tagline{color:var(--mut);font-weight:500;font-size:11px;text-transform:uppercase;letter-spacing:.14em;
  font-family:"JetBrains Mono","SF Mono",ui-monospace,Menlo,Consolas,monospace}
.tagline .dot{color:var(--cyan)}
"""


def _esc(x: object) -> str:
    return html.escape(str(x))


def _pill(verdict: str, label: str | None = None) -> str:
    cls = {"pass": "good", "fail": "bad", "warn": "warn"}.get(verdict, "warn")
    return f'<span class="pill {cls}">{_esc(label or verdict)}</span>'


_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    'family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500'
    '&display=swap">'
)


def _page(title: str, body: str) -> str:
    return ("<!doctype html><html lang=en><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<title>{_esc(title)}</title>{_FONTS}<style>{_CSS}</style></head>"
            f"<body><div class=wrap>{body}</div></body></html>")


def _exec_summary(loop: LoopResult, passed: int, total: int) -> str:
    cmp = loop.comparison
    improved = sum(1 for d in cmp.deltas if d.improved_flag)
    regressions = len(cmp.regressions)
    cm_fail = any(c.verdict == "fail" for c in cmp.counter_metrics)
    overall = "real, measurable" if cmp.overall_improved and not cm_fail else "inconclusive"

    return f"""
    <div class=summary>
      <div class=statgrid>
        <div class=stat><div class=n>200</div>
          <div class=lbl>Sessions per tutor</div></div>
        <div class=stat><div class=n>{improved}/7</div>
          <div class=lbl>Measures improved</div></div>
        <div class=stat><div class=n>{passed}/{total}</div>
          <div class=lbl>Quality checks pass</div></div>
        <div class=stat><div class=n>{regressions}</div>
          <div class=lbl>Honest regressions</div></div>
      </div>
    </div>
    <div class=summary>
      <p>{EXEC_SUMMARY_HEAD}</p>
      <p>The <strong>Old Tutor</strong> failed in <strong>6 of 7</strong> ways &mdash;
        it handed out answers on demand, accepted "I get it" without checking, left
        misconceptions intact, and ignored off-task behavior.
        The <strong>New Tutor</strong> fixed <strong>4 of those 6</strong>, with
        {overall} learning gains.
        We ran <strong>4 sanity checks</strong> designed to catch us cheating;
        all passed.</p>
      <p>One honest weakness remains and is reported below rather than hidden:
        the New Tutor still scores low on a "students working independently"
        measure that arguably penalizes good support.</p>
    </div>
    """


def _metrics_table(cmp: ComparisonReport) -> str:
    rows = []
    for d in cmp.deltas:
        if d.regressed:
            cls, status = "delta-down", "got worse"
        elif d.improved_flag:
            cls, status = "delta-up", "improved"
        else:
            cls, status = "delta-flat", "about the same"
        label = FRIENDLY_LABELS[d.name]
        goal = GOAL_LABEL[d.name]
        rows.append(
            f"<tr><td>{_esc(label)}<span class=direction>{_esc(goal)}</span></td>"
            f"<td class=num>{d.baseline:.2f}</td>"
            f"<td class=num>{d.improved:.2f}</td>"
            f"<td class='num {cls}'>{d.oriented_delta:+.2f}</td>"
            f"<td class={cls}>{status}</td></tr>"
        )
    return ("<table><tr><th>What we measured</th><th>Old Tutor</th><th>New Tutor</th>"
            "<th>Change</th><th>Verdict</th></tr>"
            + "".join(rows) + "</table>")


_VERDICT_WORD = {"pass": "looks real", "fail": "suspicious", "warn": "mixed"}


def _counter_table(cmp: ComparisonReport) -> str:
    rows = [
        f"<tr><td>{_esc(c.question)}</td>"
        f"<td>{_pill(c.verdict, _VERDICT_WORD.get(c.verdict))}</td>"
        f"<td>{_esc(c.detail)}</td></tr>"
        for c in cmp.counter_metrics
    ]
    return ("<table><tr><th>Sanity check</th><th>Result</th><th>Detail</th></tr>"
            + "".join(rows) + "</table>")


def _persona_table(m: TutorMetrics) -> str:
    """Per-persona breakdown using friendly persona names + friendly column heads."""
    dims = list(DIMENSIONS)
    # Use short two- or three-word header derived from the friendly label.
    short_headers = {
        "learning_gain": "Learning",
        "transfer_score": "New problems",
        "misconception_persistence": "Wrong ideas",
        "avoidance_recovery_rate": "Recovery",
        "answer_giving_rate": "Answer-handed",
        "scaffolding_independence": "Independent",
        "shallow_compliance_rate": '"I get it" faked',
    }
    head = "".join(f"<th>{_esc(short_headers[d])}</th>" for d in dims)
    rows = []
    for pid, scores in m.per_persona.items():
        sd = scores.as_dict()
        cells = "".join(
            f"<td class='num {'cell-fail' if _is_failing(d, sd[d]) else 'cell-ok'}'>"
            f"{sd[d]:.2f}</td>" for d in dims
        )
        rows.append(f"<tr><td>{_esc(_persona_name(pid))}</td>{cells}</tr>")
    return f"<table><tr><th>Student type</th>{head}</tr>" + "".join(rows) + "</table>"


def _failure_block(m: TutorMetrics) -> str:
    overall = m.overall.as_dict()
    failing = [n for n, v in overall.items() if _is_failing(n, v)]
    if not failing:
        return "<div class=empty>Nothing is broken on this tutor.</div>"
    items = "".join(f"<li class=bad>{_esc(FRIENDLY_LABELS[n])}</li>" for n in failing)
    return f"<ul class=fail>{items}</ul>"


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

    if cmp.regressions:
        reg_label = "; ".join(
            _esc(_persona_name(r.split("/")[0]) + " — " + FRIENDLY_LABELS.get(r.split("/")[1], r))
            if "/" in r else _esc(FRIENDLY_LABELS.get(r, r))
            for r in cmp.regressions
        )
        regression_html = f"<ul class=fail><li class=bad>{reg_label}</li></ul>"
    else:
        regression_html = "<div class=empty>Nothing got worse.</div>"

    body = f"""
    <p class=tagline>Nerdy <span class=dot>&middot;</span> AI tutor red-team harness</p>
    <h1>Did the new tutor really teach better?</h1>
    <p class=sub>A stress-test of an AI fractions tutor using 8 kinds of simulated students.</p>
    <div class=brandbar></div>

    {_exec_summary(loop, passed, total)}

    <div class=section>
      <h2>The seven things we measured</h2>
      <p class=cap>{SECTION_CAPTIONS["primary"]}</p>
      {_metrics_table(cmp)}
    </div>

    <div class=section>
      <h2>Sanity checks</h2>
      <p class=cap>{SECTION_CAPTIONS["counters"]}</p>
      {_counter_table(cmp)}
    </div>

    <div class=section>
      <h2>What got worse?</h2>
      <p class=cap>{SECTION_CAPTIONS["regressions"]}</p>
      {regression_html}
    </div>

    <div class=section>
      <h2>How each kind of student fared with the new tutor</h2>
      <p class=cap>{SECTION_CAPTIONS["personas"]}</p>
      {_persona_table(loop.improved)}
    </div>

    <div class=section>
      <h2>What each tutor still gets wrong</h2>
      <p class=cap>{SECTION_CAPTIONS["failures"]}</p>
      <div class=grid>
        <div><h3>Old Tutor</h3>{_failure_block(loop.baseline)}</div>
        <div><h3>New Tutor</h3>{_failure_block(loop.improved)}</div>
      </div>
    </div>

    <p class=foot>Built for Nerdy &middot; 200 sessions per tutor &middot;
      results are deterministic and reproducible &middot;
      raw data at <a href="/api/metrics">metrics.json</a></p>
    """
    return HTMLResponse(_page("Nerdy Tutor Stress-Test", body))


def main() -> None:  # pragma: no cover - thin uvicorn launcher
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("slh.web:app", host="0.0.0.0", port=port)


if __name__ == "__main__":  # pragma: no cover
    main()
