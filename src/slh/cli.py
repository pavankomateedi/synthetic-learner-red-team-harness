"""Command-line entry point for the harness.

    slh compare            run the full baseline->improved loop, print + write reports
    slh run --tutor v1     evaluate a single tutor and print its dimensions
    slh check              run the golden set (population + behavior) and report pass/fail
"""

from __future__ import annotations

import argparse
import contextlib
import sys
from pathlib import Path

# The Markdown comparison report contains emoji; force stdout to UTF-8 so the
# Windows console doesn't choke when we echo it. No-op if already UTF-8.
if hasattr(sys.stdout, "reconfigure"):
    with contextlib.suppress(Exception):  # best effort, never block the CLI
        sys.stdout.reconfigure(encoding="utf-8")

from .evaluator import DIMENSIONS, TutorMetrics, evaluate
from .goldenset import check_behaviors, check_population
from .harness import DEFAULT_SEEDS, run_improvement_loop, run_population
from .report import comparison_report, failure_report


def _print_dimensions(m: TutorMetrics) -> None:
    print(f"# {m.tutor_name}  (n={m.n_sessions})")
    for name in DIMENSIONS:
        direction = "higher=better" if DIMENSIONS[name] > 0 else "lower=better"
        print(f"  {name:28s} {m.overall.as_dict()[name]:6.3f}  ({direction})")


def _cmd_run(args: argparse.Namespace) -> int:
    metrics = evaluate(run_population(args.tutor, n_seeds=args.seeds))
    _print_dimensions(metrics)
    return 0


def _cmd_compare(args: argparse.Namespace) -> int:
    loop = run_improvement_loop(n_seeds=args.seeds)
    _print_dimensions(loop.baseline)
    print()
    _print_dimensions(loop.improved)
    print()
    report_md = comparison_report(loop.comparison)
    print(report_md)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "failure_report_baseline.md").write_text(
        failure_report(loop.baseline), encoding="utf-8")
    (out / "failure_report_improved.md").write_text(
        failure_report(loop.improved), encoding="utf-8")
    (out / "baseline_vs_improved.md").write_text(report_md, encoding="utf-8")
    print(f"\nReports written to {out}/")
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    loop = run_improvement_loop(n_seeds=args.seeds)
    metrics = {"v1": loop.baseline, "v2": loop.improved}
    results = check_population(metrics, loop.comparison) + check_behaviors()
    failed = 0
    for r in results:
        mark = "PASS" if r.passed else "FAIL"
        if not r.passed:
            failed += 1
        print(f"[{mark}] {r.name}  -- {r.detail}")
    print(f"\n{len(results) - failed}/{len(results)} checks passed.")
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="slh", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seeds", type=int, default=DEFAULT_SEEDS,
                        help=f"seeds per persona (default {DEFAULT_SEEDS})")
    sub = parser.add_subparsers(dest="command")

    p_run = sub.add_parser("run", help="evaluate a single tutor")
    p_run.add_argument("--tutor", default="v1", help="v1 | v2")
    p_run.set_defaults(func=_cmd_run)

    p_cmp = sub.add_parser("compare", help="run the full improvement loop")
    p_cmp.add_argument("--out", default="docs", help="output dir for reports")
    p_cmp.set_defaults(func=_cmd_compare)

    p_chk = sub.add_parser("check", help="run the golden set")
    p_chk.set_defaults(func=_cmd_check)

    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        args.out = "docs"
        return _cmd_compare(args)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
