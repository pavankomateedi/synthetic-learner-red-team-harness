"""Report rendering, harness orchestration, and CLI tests."""

from slh.cli import main
from slh.harness import run_improvement_loop, run_population
from slh.report import comparison_report, failure_report


def test_run_population_size():
    results = run_population("v1", n_seeds=3)
    from slh.personas import all_personas
    assert len(results) == len(all_personas()) * 3


def test_failure_report_flags_baseline_failures():
    loop = run_improvement_loop(n_seeds=5)
    md = failure_report(loop.baseline)
    assert "Failure Mode Report" in md
    assert "answer_giving_rate" in md          # baseline failure surfaced
    assert "Answer-Giving" in md               # mapped to PRD 13 taxonomy


def test_comparison_report_has_required_sections():
    loop = run_improvement_loop(n_seeds=5)
    md = comparison_report(loop.comparison)
    for section in ("Primary + supporting metrics", "Regression check",
                    "Counter-metrics", "Interpretation"):
        assert section in md


def test_cli_check_returns_zero(capsys):
    assert main(["--seeds", "8", "check"]) == 0
    assert "checks passed" in capsys.readouterr().out


def test_cli_run_prints_dimensions(capsys):
    assert main(["--seeds", "4", "run", "--tutor", "v2"]) == 0
    assert "improved_v2" in capsys.readouterr().out


def test_cli_compare_writes_reports(tmp_path, capsys):
    rc = main(["--seeds", "5", "compare", "--out", str(tmp_path)])
    assert rc == 0
    assert (tmp_path / "baseline_vs_improved.md").exists()
    assert (tmp_path / "failure_report_baseline.md").exists()
    assert (tmp_path / "failure_report_improved.md").exists()


def test_cli_default_runs_compare(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["--seeds", "4"]) == 0
    assert (tmp_path / "docs" / "baseline_vs_improved.md").exists()
