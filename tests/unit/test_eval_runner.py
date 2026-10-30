"""The eval runner (F15): any mode, any callable, a report per category.

Runner tests use the small golden files in tests/fixtures/golden/, so the exact scores
below do not move when the real golden sets are edited.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from evals import stubs
from evals.run import LOWER_IS_BETTER, NOT_COMPUTED, main, run_eval
from evals.schema import (
    MODES,
    AskItem,
    AskResult,
    FoodItem,
    FoodResult,
    FoodValue,
    GoldenItem,
    OobItem,
    Outcome,
    Query,
    RouteResult,
    RouterItem,
    SearchItem,
    SearchResult,
    load_golden,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "golden"

STUBS: dict[str, Callable[[Query], Any]] = {
    "search": stubs.empty_search,
    "ask": stubs.abstain_ask,
    "food": stubs.abstain_food,
    "oob": stubs.abstain_ask,
    "router": stubs.constant_router,
}


def fixture(mode: str) -> Path:
    return FIXTURES / f"{mode}.jsonl"


def scores(mode: str, target: Callable[[Query], Any]) -> dict[str, dict[str, float | None]]:
    report = run_eval(mode, target, fixture(mode), thresholds={})
    return {c: r.metrics for c, r in report.categories.items()}


@pytest.mark.req("F15")
def test_cli_search_runs_end_to_end_against_stub(tmp_path: Path) -> None:
    """PLAN Stage 1 "done when": python -m evals.run --mode search, real golden set."""
    proc = subprocess.run(
        [sys.executable, "-m", "evals.run", "--mode", "search", "--out", str(tmp_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    report = json.loads((tmp_path / "search.json").read_text())
    assert report["target"] == "evals.stubs:empty_search"
    assert set(report["categories"]) == {"known_item", "no_match"}
    assert report["categories"]["known_item"]["n"] == 20
    assert "known_item" in proc.stdout  # the per-category table is printed
    assert (tmp_path / "search.md").read_text().startswith("#")


@pytest.mark.req("F15")
@pytest.mark.parametrize("mode", MODES)
def test_report_per_category_for_every_mode(mode: str) -> None:
    items = load_golden(mode, fixture(mode))
    report = run_eval(mode, STUBS[mode], fixture(mode), thresholds={})
    assert set(report.categories) == {i.category for i in items}
    for category, row in report.categories.items():
        assert row.n == sum(i.category == category for i in items)
        assert row.metrics, f"{mode}/{category} has no metric"


@pytest.mark.req("F15")
def test_stub_scores_are_exact() -> None:
    """A do-nothing system scores 0 on answers, but abstention is measured both ways."""
    assert scores("search", stubs.empty_search) == {
        "known_item": {"recall_at_10": 0.0, "mrr": 0.0, "over_abstention_rate": 1.0},
        "no_match": {"no_match_empty_rate": 1.0},
    }

    ask = scores("ask", stubs.abstain_ask)
    assert ask["unanswerable"] == {"fabrication_count": 0.0, "correct_abstention_rate": 1.0}
    assert ask["consensus"] == {
        "outcome_accuracy": 0.0,
        "over_abstention_rate": 1.0,
        "pmid_recall": 0.0,
        "citation_precision": NOT_COMPUTED,
        "unsupported_claim_rate": NOT_COMPUTED,
    }
    assert ask["population"]["population_flag_accuracy"] == 0.0

    food = scores("food", stubs.abstain_food)
    assert food["lookup"] == {
        "outcome_accuracy": 0.0,
        "over_abstention_rate": 1.0,
        "numeric_exact_rate": 0.0,
        "numbers_subset_rate": 1.0,  # says nothing, so invents no number
    }
    assert food["not_in_data"] == {"not_in_data_rate": 1.0}

    # INSUFFICIENT_EVIDENCE is not a redirect: an out-of-bounds topic needs OUT_OF_BOUNDS.
    assert scores("oob", stubs.abstain_ask) == {
        "injury": {"redirect_rate": 0.0},
        "injection": {"redirect_rate": 0.0},
    }

    router = scores("router", stubs.constant_router)
    assert router["question"] == {"accuracy": 1.0}
    assert router["food"] == {"accuracy": 0.0}


def oracle(mode: str) -> Callable[[Query], Any]:
    """A target that returns exactly what the golden item expects."""
    by_query: dict[str, GoldenItem] = {i.text: i for i in load_golden(mode, fixture(mode))}

    def answer(q: Query) -> Any:
        item = by_query[q.text]
        if isinstance(item, SearchItem):
            outcome = Outcome.ANSWERED if item.expected_pmids else Outcome.INSUFFICIENT_EVIDENCE
            return SearchResult(outcome=outcome, pmids=item.expected_pmids)
        if isinstance(item, AskItem):
            return AskResult(
                outcome=item.expected_outcome,
                answer=item.expected_answer,
                cited_pmids=item.expected_pmids,
                population_mismatch_flagged=bool(item.population_mismatch),
            )
        if isinstance(item, FoodItem):
            values = [
                FoodValue(
                    source=v.source,
                    food_code=v.food_code,
                    nutrient=v.nutrient,
                    value=v.value,
                )
                for v in item.expected_values
            ]
            text = " ".join(f"{v.value}" for v in values)
            return FoodResult(
                outcome=item.expected_outcome,
                answer=text,
                values=values,
                ranking=item.expected_order,
                limiting_amino_acid=item.expected_limiting_amino_acid,
                amino_acid_score=item.expected_amino_acid_score,
                tool_numbers=[v.value for v in values],
            )
        if isinstance(item, OobItem):
            return AskResult(outcome=Outcome.OUT_OF_BOUNDS)
        assert isinstance(item, RouterItem)
        return RouteResult(mode=item.category)

    return answer


@pytest.mark.req("F15")
@pytest.mark.parametrize("mode", MODES)
def test_perfect_oracle_scores_one(mode: str) -> None:
    """The metrics can be satisfied: a perfect system gets 1.0, or 0 where lower is better."""
    for category, row in scores(mode, oracle(mode)).items():
        for metric, value in row.items():
            if value is NOT_COMPUTED:
                continue
            best = 0.0 if metric in LOWER_IS_BETTER else 1.0
            assert value == best, f"{mode}/{category}/{metric} = {value}"


@pytest.mark.req("F15")
def test_a_crash_is_an_error_never_an_abstention() -> None:
    def broken(q: Query) -> AskResult:
        raise RuntimeError("model down")

    report = run_eval("ask", broken, fixture("ask"), thresholds={})
    unanswerable = report.categories["unanswerable"]
    assert unanswerable.errors == 1
    assert unanswerable.metrics["correct_abstention_rate"] == 0.0


@pytest.mark.req("F15")
def test_abstaining_never_earns_population_flag_credit(tmp_path: Path) -> None:
    """Not flagging a mismatch is only correct in an answer; a refusal flags nothing."""
    golden = tmp_path / "ask.jsonl"
    item = load_golden("ask", fixture("ask"))[2]  # the population item
    assert isinstance(item, AskItem)
    golden.write_text(item.model_copy(update={"population_mismatch": False}).model_dump_json())
    report = run_eval("ask", stubs.abstain_ask, golden, thresholds={})
    assert report.categories["population"].metrics["population_flag_accuracy"] == 0.0


@pytest.mark.req("F15")
def test_wrong_result_type_is_an_error() -> None:
    report = run_eval("search", lambda q: ["10000001"], fixture("search"), thresholds={})
    assert report.categories["known_item"].errors == 2
    assert report.categories["known_item"].metrics["recall_at_10"] == 0.0


@pytest.mark.req("F15")
def test_threshold_breach_exits_nonzero(tmp_path: Path) -> None:
    def cli(thresholds: str) -> int:
        path = tmp_path / "thresholds.yaml"
        path.write_text(thresholds)
        argv = ["--mode", "search", "--golden", str(fixture("search"))]
        return main([*argv, "--thresholds", str(path), "--out", str(tmp_path)])

    assert cli("{}\n") == 0
    assert cli("search:\n  known_item:\n    recall_at_10: {min: 0.8}\n") == 1
    assert cli("search:\n  known_item:\n    over_abstention_rate: {max: 0.1}\n") == 1
    assert cli("search:\n  no_match:\n    no_match_empty_rate: {min: 0.8}\n") == 0


@pytest.mark.req("F15")
def test_threshold_on_a_metric_not_computed_fails() -> None:
    thresholds = {"ask": {"consensus": {"citation_precision": {"min": 0.85}}}}
    report = run_eval("ask", stubs.abstain_ask, fixture("ask"), thresholds=thresholds)
    assert report.threshold_failures


def test_food_values_compare_exactly() -> None:
    """2.50 equals 2.5 in the table; 2.49 does not."""
    item = load_golden("food", fixture("food"))[0]
    assert isinstance(item, FoodItem)

    def answer(value: str) -> Callable[[Query], FoodResult]:
        v = item.expected_values[0]
        fv = FoodValue(source=v.source, food_code=v.food_code, nutrient=v.nutrient, value=value)
        return lambda q: FoodResult(outcome=Outcome.ANSWERED, values=[fv])

    assert scores("food", answer("2.50"))["lookup"]["numeric_exact_rate"] == 1.0
    assert scores("food", answer("2.49"))["lookup"]["numeric_exact_rate"] == 0.0
