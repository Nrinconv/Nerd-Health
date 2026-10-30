"""The traceability rules are the project's guardrail, so they are tested like code."""

from __future__ import annotations

from typing import Any

from traceability import VERIFIED, check_stages, load  # scripts/ is on the pytest path


def spec(stage_status: str = "done", **req: object) -> dict[str, Any]:
    return {
        "stages": [{"id": 0, "name": "A", "status": stage_status}],
        "requirements": [{"id": "F1", "stage": 0, "text": "t", **req}],
    }


def result(outcome: str, req_id: str = "F1") -> dict[str, dict[str, Any]]:
    return {"tests/t.py::test_x": {"reqs": [req_id], "outcome": outcome}}


def errors_for(spec_: dict[str, Any], results: dict[str, dict[str, Any]]) -> list[str]:
    stages, reqs, errors = load(spec_, results)
    return errors + check_stages(stages, reqs)


def test_done_stage_with_passing_test_is_clean() -> None:
    assert errors_for(spec(), result("passed")) == []


def test_done_stage_without_a_test_is_an_error() -> None:
    assert any("no test" in e for e in errors_for(spec(), {}))


def test_failing_test_blocks_a_done_stage() -> None:
    assert any("failing" in e for e in errors_for(spec(), result("failed")))


def test_skipped_and_xfail_never_count_as_verified() -> None:
    for outcome in ("skipped", "xfail", "not run"):
        assert any("not passing" in e for e in errors_for(spec(), result(outcome)))


def test_in_progress_stage_tolerates_missing_tests() -> None:
    assert errors_for(spec("in_progress"), {}) == []


def test_manual_requirement_needs_evidence_to_close() -> None:
    assert any("no evidence" in e for e in errors_for(spec(verification="manual"), {}))
    assert errors_for(spec(verification="manual", evidence="ci.yml: coverage gate"), {}) == []


def test_unknown_requirement_in_results_is_an_error() -> None:
    assert any("unknown requirement" in e for e in errors_for(spec(), result("passed", "F99")))


def test_stage_cannot_close_before_an_earlier_one() -> None:
    s = {
        "stages": [
            {"id": 0, "name": "A", "status": "in_progress"},
            {"id": 1, "name": "B", "status": "done"},
        ],
        "requirements": [],
    }
    assert any("stage 0 is not" in e for e in errors_for(s, {}))


def test_status_of_a_passing_requirement() -> None:
    _, reqs, _ = load(spec(), result("passed"))
    assert reqs[0].status == VERIFIED
