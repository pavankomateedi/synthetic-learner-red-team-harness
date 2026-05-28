"""Improvement comparator (PRD 9, 10.1 "Improvement Comparator", 8.2 counter-
metrics).

Given baseline and improved :class:`TutorMetrics`, it produces:
  * per-dimension deltas (overall and per persona),
  * a **regression check** -- any dimension/persona that moved the wrong way,
  * the five **counter-metrics** from PRD 8.2, each rendered as an explicit
    pass / warn / fail verdict with the numbers behind it.

The counter-metrics are deliberately capable of returning WARN/FAIL so the
report cannot only ever flatter the change.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .evaluator import DIMENSIONS, TutorMetrics

# Thresholds (documented in docs/evaluation_method.md).
MEANINGFUL_DELTA = 0.05   # below this, a change is "noise", not improvement
REGRESSION_EPS = 0.02     # a wrong-direction move larger than this is a regression


@dataclass
class DimensionDelta:
    name: str
    baseline: float
    improved: float
    delta: float            # signed, in the metric's raw units
    direction: int          # +1 higher-better, -1 lower-better
    improved_flag: bool     # moved meaningfully in the better direction
    regressed: bool         # moved in the worse direction beyond eps

    @property
    def oriented_delta(self) -> float:
        """Delta re-signed so positive always means 'better'."""
        return self.delta * self.direction


@dataclass
class CounterMetric:
    name: str
    question: str
    verdict: str            # "pass" | "warn" | "fail"
    detail: str


@dataclass
class ComparisonReport:
    baseline_name: str
    improved_name: str
    deltas: list[DimensionDelta]
    regressions: list[str]                # "dimension" or "persona/dimension"
    counter_metrics: list[CounterMetric]
    per_persona_regressions: dict[str, list[str]] = field(default_factory=dict)

    @property
    def overall_improved(self) -> bool:
        gains = [d for d in self.deltas if d.improved_flag]
        return len(gains) >= 1 and not self.regressions_in_primary

    @property
    def regressions_in_primary(self) -> bool:
        return any(r in DIMENSIONS for r in self.regressions)

    def delta(self, name: str) -> DimensionDelta:
        return next(d for d in self.deltas if d.name == name)


def _deltas(base: dict[str, float], imp: dict[str, float]) -> list[DimensionDelta]:
    out: list[DimensionDelta] = []
    for name, direction in DIMENSIONS.items():
        b, i = base[name], imp[name]
        delta = i - b
        oriented = delta * direction
        out.append(DimensionDelta(
            name=name, baseline=b, improved=i, delta=delta, direction=direction,
            improved_flag=oriented >= MEANINGFUL_DELTA,
            regressed=oriented < -REGRESSION_EPS,
        ))
    return out


def _counter_metrics(base: TutorMetrics, imp: TutorMetrics,
                     deltas: list[DimensionDelta]) -> list[CounterMetric]:
    by = {d.name: d for d in deltas}
    cms: list[CounterMetric] = []

    # 1. If scores improve, did transfer also improve?
    score_up = by["learning_gain"].oriented_delta > 0
    transfer_delta = imp.overall.transfer_score - base.overall.transfer_score
    if score_up and transfer_delta < -REGRESSION_EPS:
        v, d = "fail", "Scores rose but transfer fell -- likely benchmark gaming."
    elif score_up and transfer_delta >= 0:
        v, d = "pass", f"Scores up and transfer up (+{transfer_delta:.3f})."
    else:
        v, d = "warn", f"Scores not clearly up; transfer delta {transfer_delta:+.3f}."
    cms.append(CounterMetric("transfer_tracks_score",
                             "If scores improve, did transfer also improve?", v, d))

    # 2. If the tutor gives more hints, did independence decline?
    hint_delta = ((imp.mean_hints_first_half + imp.mean_hints_second_half)
                  - (base.mean_hints_first_half + base.mean_hints_second_half))
    indep_delta = by["scaffolding_independence"].oriented_delta
    if hint_delta > 0 and indep_delta < -REGRESSION_EPS:
        v, d = "fail", "More hints AND lower independence -- scaffolding trap."
    else:
        v, d = "pass", (f"Hint usage delta {hint_delta:+.2f}/item; "
                        f"independence delta {indep_delta:+.3f}.")
    cms.append(CounterMetric("hints_vs_independence",
                             "If the tutor gives more hints, did independence decline?", v, d))

    # 3. Did the gain show up on novel transfer items, not just drilled ones?
    lg_delta = by["learning_gain"].oriented_delta
    if imp.transfer_gain <= REGRESSION_EPS and lg_delta > MEANINGFUL_DELTA:
        v, d = "warn", ("Instruction gain without transfer gain -- "
                        "possible overfit to drilled items.")
    else:
        v, d = "pass", (f"Transfer gain {imp.transfer_gain:+.3f} vs in-lesson gain "
                        f"{lg_delta:+.3f}.")
    cms.append(CounterMetric("synthetic_overfit",
                             "If synthetic learners perform better, did the system overfit?",
                             v, d))

    # 4. Would a human educator agree? (proxy rubric -- needs real validation.)
    sound = (by["answer_giving_rate"].oriented_delta >= 0
             and by["misconception_persistence"].oriented_delta >= 0
             and by["avoidance_recovery_rate"].oriented_delta >= 0)
    v = "pass" if sound else "warn"
    d = ("Changes are pedagogically sound by proxy rubric (less answer-giving, "
         "fewer surviving misconceptions, better recovery). PROXY ONLY -- "
         "requires human educator sign-off.") if sound else (
         "Some pedagogically-relevant dimensions did not improve; human review needed.")
    cms.append(CounterMetric("educator_agreement",
                             "If the evaluator reports improvement, would a human educator agree?",
                             v, d))

    # 5. If off-task behavior is redirected, is agency/rapport preserved?
    recovery_up = by["avoidance_recovery_rate"].oriented_delta > 0
    not_by_coercion = by["answer_giving_rate"].oriented_delta >= 0
    if recovery_up and not_by_coercion:
        v, d = "pass", ("Redirection improved without resorting to answer-giving "
                        "(rapport-preserving recovery).")
    elif recovery_up:
        v, d = "warn", "Recovery improved but answer-giving also rose -- check coercion."
    else:
        v, d = "warn", "Recovery did not clearly improve."
    cms.append(CounterMetric("agency_preserved",
                             "If off-topic behavior is redirected, is agency/rapport preserved?",
                             v, d))
    return cms


def compare(base: TutorMetrics, imp: TutorMetrics) -> ComparisonReport:
    """Produce the full before/after comparison with regression + counter-metrics."""
    deltas = _deltas(base.overall.as_dict(), imp.overall.as_dict())
    regressions = [d.name for d in deltas if d.regressed]

    per_persona_reg: dict[str, list[str]] = {}
    for pid, base_scores in base.per_persona.items():
        if pid not in imp.per_persona:
            continue
        pdeltas = _deltas(base_scores.as_dict(), imp.per_persona[pid].as_dict())
        regs = [d.name for d in pdeltas if d.regressed]
        if regs:
            per_persona_reg[pid] = regs
            regressions += [f"{pid}/{r}" for r in regs]

    return ComparisonReport(
        baseline_name=base.tutor_name,
        improved_name=imp.tutor_name,
        deltas=deltas,
        regressions=regressions,
        counter_metrics=_counter_metrics(base, imp, deltas),
        per_persona_regressions=per_persona_reg,
    )


__all__ = ["ComparisonReport", "DimensionDelta", "CounterMetric", "compare",
           "MEANINGFUL_DELTA", "REGRESSION_EPS"]
