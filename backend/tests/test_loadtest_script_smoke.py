from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_loadtest(*args: str) -> subprocess.CompletedProcess[str]:
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "loadtest.py"
    cmd = [
        sys.executable,
        str(script_path),
        "--dry-run",
        "--base-url",
        "http://localhost:3301",
        "--requests",
        "40",
        "--concurrency",
        "8",
        *args,
    ]
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def test_dry_run_trend_without_history_has_single_record(tmp_path: Path) -> None:
    trend_path = tmp_path / "trend.md"
    result = _run_loadtest("--trend-out", str(trend_path))

    assert result.returncode == 0, result.stderr
    trend_text = trend_path.read_text(encoding="utf-8")
    assert "- Captured Runs: 1" in trend_text
    assert "- Window Size: 1" in trend_text
    assert trend_text.count("| dry-run |") == 1


def test_dry_run_history_appends_and_trend_includes_all_records(tmp_path: Path) -> None:
    history_path = tmp_path / "history.jsonl"
    trend_path = tmp_path / "trend.md"

    first = _run_loadtest(
        "--requests",
        "20",
        "--history-out",
        str(history_path),
        "--trend-out",
        str(trend_path),
    )
    second = _run_loadtest(
        "--requests",
        "30",
        "--history-out",
        str(history_path),
        "--trend-out",
        str(trend_path),
    )

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr

    rows = [line for line in history_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 2
    records = [json.loads(line) for line in rows]
    assert [record["requests"] for record in records] == [20, 30]
    assert all(record["mode"] == "dry-run" for record in records)

    trend_text = trend_path.read_text(encoding="utf-8")
    assert "- Captured Runs: 2" in trend_text
    assert trend_text.count("| dry-run |") == 2


def test_dry_run_trend_history_window_limits_table_rows(tmp_path: Path) -> None:
    history_path = tmp_path / "history.jsonl"
    trend_path = tmp_path / "trend.md"

    for requests in ("10", "11", "12"):
        result = _run_loadtest(
            "--requests",
            requests,
            "--history-out",
            str(history_path),
            "--trend-out",
            str(trend_path),
            "--history-window",
            "2",
        )
        assert result.returncode == 0, result.stderr

    trend_text = trend_path.read_text(encoding="utf-8")
    assert "- Captured Runs: 3" in trend_text
    assert "- Window Size: 2" in trend_text
    assert trend_text.count("| dry-run |") == 2


def test_dry_run_writes_custom_alert_targets_to_outputs(tmp_path: Path) -> None:
    summary_path = tmp_path / "summary.json"
    history_path = tmp_path / "history.jsonl"

    result = _run_loadtest(
        "--target-success-rate",
        "0.995",
        "--target-p95-ms",
        "800",
        "--out",
        str(summary_path),
        "--history-out",
        str(history_path),
    )

    assert result.returncode == 0, result.stderr

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["targets"] == {"success_rate": 0.995, "p95_latency_ms": 800.0}

    history_rows = [line for line in history_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(history_rows) == 1
    history_record = json.loads(history_rows[0])
    assert history_record["target_success_rate"] == 0.995
    assert history_record["target_p95_ms"] == 800.0
