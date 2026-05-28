"""Report generators (PRD 10.1 "Failure Report Generator"; deliverables 12).

* :func:`failure_report` -- structured analysis of educational failures a tutor
  exposes, clustered by persona x dimension and mapped to the PRD 13 taxonomy,
  with concrete recommendations.
* :func:`comparison_report` -- before/after table, regression check, and the
  counter-metric verdicts, rendered as Markdown.
"""

from __future__ import annotations

from .comparator import ComparisonReport
from .evaluator import DIMENSIONS, TutorMetrics

# When does a dimension count as "failing" for a tutor? (Documented in
# docs/evaluation_method.md.) Direction is taken from DIMENSIONS.
FAILURE_THRESHOLDS: dict[str, float] = {
    "learning_gain": 0.05,            # below -> not enough learning
    "transfer_score": 0.40,           # below -> weak transfer
    "misconception_persistence": 0.50,  # above -> misconceptions survive
    "avoidance_recovery_rate": 0.50,  # below -> fails to recover avoidance
    "answer_giving_rate": 0.30,       # above -> gives answers
    "scaffolding_independence": 0.40,  # below -> hint-dependent
    "shallow_compliance_rate": 0.30,  # above -> accepts "I get it"
}

# Map each failing dimension to the PRD 13 taxonomy + a recommendation.
_TAXONOMY: dict[str, tuple[str, str]] = {
    "learning_gain": ("Curriculum: weak instruction",
                      "Increase active practice; reduce answer-giving."),
    "transfer_score": ("Curriculum: Transfer Gap (13.2)",
                       "Add varied practice and require justification on novel items."),
    "misconception_persistence": ("Curriculum: Misconception Survival (13.2)",
                                  "Diagnose the specific error and remediate it directly."),
    "avoidance_recovery_rate": ("Tutor: Off-Task Tolerance (13.1)",
                                "Add explicit redirect / refuse / re-engage moves."),
    "answer_giving_rate": ("Tutor: Answer-Giving + Hint Cascade (13.1)",
                           "Withhold answers; cap hints; require an attempt."),
    "scaffolding_independence": ("Curriculum: Scaffolding Trap (13.2)",
                                 "Fade scaffolding; cap hints per item."),
    "shallow_compliance_rate": ("Tutor: Shallow Compliance Acceptance (13.1)",
                                "Replace 'do you understand?' with a justification probe."),
}


def _is_failing(name: str, value: float) -> bool:
    thr = FAILURE_THRESHOLDS[name]
    return value < thr if DIMENSIONS[name] > 0 else value > thr


def _fmt(name: str, value: float) -> str:
    arrow = "higher=better" if DIMENSIONS[name] > 0 else "lower=better"
    return f"{value:.3f} ({arrow})"


def failure_report(metrics: TutorMetrics) -> str:
    """Markdown failure-mode report for one tutor, with persona clusters."""
    lines: list[str] = []
    lines.append(f"# Failure Mode Report — `{metrics.tutor_name}`")
    lines.append("")
    lines.append(f"Population: {metrics.n_sessions} sessions "
                 f"({len(metrics.per_persona)} personas).")
    lines.append("")

    # Overall failing dimensions.
    overall = metrics.overall.as_dict()
    failing = [n for n, v in overall.items() if _is_failing(n, v)]
    lines.append("## Overall failing dimensions")
    lines.append("")
    if not failing:
        lines.append("_No dimension is below its failure threshold._")
    else:
        lines.append("| Dimension | Value | Failure mode (PRD 13) | Recommendation |")
        lines.append("|---|---|---|---|")
        for n in failing:
            tax, rec = _TAXONOMY[n]
            lines.append(f"| `{n}` | {_fmt(n, overall[n])} | {tax} | {rec} |")
    lines.append("")

    # Failure clusters by persona x dimension.
    lines.append("## Failure clusters (persona × dimension)")
    lines.append("")
    lines.append("| Persona | Failing dimensions |")
    lines.append("|---|---|")
    for pid, scores in metrics.per_persona.items():
        sd = scores.as_dict()
        pf = [n for n, v in sd.items() if _is_failing(n, v)]
        cell = ", ".join(f"`{n}`" for n in pf) if pf else "—"
        lines.append(f"| {pid} | {cell} |")
    lines.append("")
    return "\n".join(lines)


def _verdict_icon(v: str) -> str:
    return {"pass": "✅ pass", "warn": "⚠️ warn", "fail": "❌ fail"}.get(v, v)


def comparison_report(report: ComparisonReport) -> str:
    """Markdown before/after comparison with regression + counter-metrics."""
    lines: list[str] = []
    lines.append(f"# Baseline vs. Improved — `{report.baseline_name}` → "
                 f"`{report.improved_name}`")
    lines.append("")

    lines.append("## Primary + supporting metrics")
    lines.append("")
    lines.append("| Dimension | Baseline | Improved | Δ (better-oriented) | Status |")
    lines.append("|---|---|---|---|---|")
    for d in report.deltas:
        if d.regressed:
            status = "🔻 regression"
        elif d.improved_flag:
            status = "🟢 improved"
        else:
            status = "➖ ~flat"
        lines.append(f"| `{d.name}` | {d.baseline:.3f} | {d.improved:.3f} "
                     f"| {d.oriented_delta:+.3f} | {status} |")
    lines.append("")

    lines.append("## Regression check")
    lines.append("")
    if not report.regressions:
        lines.append("_No regressions detected (overall or per persona)._")
    else:
        lines.append("Regressions detected:")
        for r in report.regressions:
            lines.append(f"- `{r}`")
    lines.append("")

    lines.append("## Counter-metrics (anti-gaming, PRD 8.2)")
    lines.append("")
    lines.append("| Counter-metric | Question | Verdict | Detail |")
    lines.append("|---|---|---|---|")
    for cm in report.counter_metrics:
        lines.append(f"| `{cm.name}` | {cm.question} | {_verdict_icon(cm.verdict)} | {cm.detail} |")
    lines.append("")

    verdict = ("real improvement" if report.overall_improved
               else "inconclusive / not a clear improvement")
    lines.append(f"## Interpretation\n\n**Verdict: {verdict}.** "
                 f"{len([d for d in report.deltas if d.improved_flag])} dimension(s) "
                 f"improved meaningfully; {len(report.regressions)} regression(s).")
    lines.append("")
    return "\n".join(lines)


__all__ = ["failure_report", "comparison_report", "FAILURE_THRESHOLDS"]
