import json

import pytest

from benchmark_runner.server import (
    BenchmarkInput,
    Job,
    _finish_from_reports,
    _guidellm_command,
    _is_child,
)


def make_job() -> Job:
    return Job(
        run_id="benchmark-20260907-120000-a1b2c3d4",
        request=BenchmarkInput(
            model="qwen3-8b",
            prompt_tokens=16,
            output_tokens=8,
            concurrency=1,
            max_requests=2,
            max_duration_seconds=30,
        ),
    )


def test_guidellm_command_has_allowlisted_target_and_reports() -> None:
    command = _guidellm_command(make_job())
    backend = json.loads(command[command.index("--backend") + 1])

    assert command[0:2] == ["guidellm", "run"]
    assert "kind=max_requests,count=2" in command
    assert "kind=max_duration,seconds=30" in command
    assert all(
        "/results/benchmark-20260907-120000-a1b2c3d4" in item
        for item in command
        if "path=" in item
    )
    assert backend["extras"]["body"]["chat_template_kwargs"] == {"enable_thinking": False}
    assert "docker" not in command


def test_finish_from_reports_marks_only_successful_run(tmp_path) -> None:
    job = make_job()
    report_dir = tmp_path / job.run_id
    report_dir.mkdir()
    for filename in ("benchmarks.html", "benchmarks.csv"):
        (report_dir / filename).write_text("report", encoding="utf-8")
    (report_dir / "benchmarks.json").write_text(
        json.dumps(
            {"benchmarks": [{"scheduler_state": {"successful_requests": 2, "errored_requests": 0}}]}
        ),
        encoding="utf-8",
    )

    _finish_from_reports(job, report_dir, 0)

    assert job.status == "completed"
    assert job.files == ["benchmarks.html", "benchmarks.json", "benchmarks.csv"]
    manifest = json.loads(
        (report_dir / "run-manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["status"] == "completed"


def test_finish_from_reports_rejects_errors(tmp_path) -> None:
    job = make_job()
    report_dir = tmp_path / job.run_id
    report_dir.mkdir()
    for filename in ("benchmarks.html", "benchmarks.csv", "benchmarks.json"):
        (report_dir / filename).write_text("{}", encoding="utf-8")
    (report_dir / "benchmarks.json").write_text(
        json.dumps(
            {"benchmarks": [{"scheduler_state": {"successful_requests": 0, "errored_requests": 1}}]}
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError):
        _finish_from_reports(job, report_dir, 0)


def test_report_path_must_stay_under_job_directory(tmp_path) -> None:
    run_root = tmp_path / "benchmark"
    run_root.mkdir()

    assert _is_child(run_root / "benchmarks.json", run_root)
    assert not _is_child(run_root.parent / "secret.txt", run_root)
