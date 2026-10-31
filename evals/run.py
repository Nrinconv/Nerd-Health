"""Run a golden set against a callable and write a per-category report.

    python -m evals.run --mode search [--target module:callable] [--golden path]
                        [--out dir] [--thresholds path]

The target receives a `Query` (never the golden item) and returns the mode's result model
from `evals.schema`. Metrics are reported per category, never collapsed into one score.
An item whose target raises or returns the wrong type is counted in `errors` and fails
every metric: a crash never scores as an abstention.

Exit status 1 when a metric breaks `evals/thresholds.yaml`.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from evals import metrics
from evals.schema import (
    GOLDEN_DIR,
    MODES,
    AskItem,
    AskResult,
    FoodItem,
    FoodResult,
    GoldenItem,
    Outcome,
    Query,
    RouteResult,
    RouterItem,
    SearchItem,
    SearchResult,
    load_golden,
)

ROOT = Path(__file__).resolve().parent.parent
THRESHOLDS = Path(__file__).resolve().parent / "thresholds.yaml"
OUT_DIR = ROOT / "reports" / "eval"

NOT_COMPUTED = None  # needs the LLM judge (Stage 4); reported as such, never as 0
LOWER_IS_BETTER = frozenset({"fabrication_count", "over_abstention_rate"})
COUNTS = frozenset({"fabrication_count"})  # summed over the category, not averaged

DEFAULT_TARGETS = {
    "search": "evals.stubs:empty_search",
    "ask": "evals.stubs:abstain_ask",
    "food": "evals.stubs:abstain_food",
    "oob": "evals.stubs:abstain_ask",
    "router": "evals.stubs:constant_router",
}
RESULT_TYPES: dict[str, type[BaseModel]] = {
    "search": SearchResult,
    "ask": AskResult,
    "food": FoodResult,
    "oob": AskResult,
    "router": RouteResult,
}

Scores = dict[str, float | None]


class CategoryReport(BaseModel):
    n: int
    errors: int = 0
    metrics: Scores


class Report(BaseModel):
    mode: str
    golden: str
    target: str
    run_at: str = ""
    categories: dict[str, CategoryReport]
    threshold_failures: list[str] = []


# --- per-item scoring: `r` is None when the target failed on the item ----------------------


def _b(ok: bool) -> float:
    return 1.0 if ok else 0.0


def score_search(item: SearchItem, r: SearchResult | None) -> Scores:
    if item.category == "no_match":
        return {"no_match_empty_rate": _b(r is not None and not r.pmids)}
    pmids = r.pmids if r is not None else []
    abstained = r is None or metrics.is_abstention(r.outcome) or not r.pmids
    return {
        "recall_at_10": metrics.recall_at_k(item.expected_pmids, pmids, k=10),
        "mrr": metrics.reciprocal_rank(item.expected_pmids, pmids),
        "over_abstention_rate": _b(abstained),
    }


def score_ask(item: AskItem, r: AskResult | None) -> Scores:
    if item.category == "unanswerable":
        return {
            "fabrication_count": _b(r is None or r.outcome is Outcome.ANSWERED),
            "correct_abstention_rate": _b(r is not None and r.outcome is item.expected_outcome),
        }
    cited = r.cited_pmids if r is not None else []
    scores: Scores = {
        "outcome_accuracy": _b(r is not None and r.outcome is item.expected_outcome),
        "over_abstention_rate": _b(r is None or metrics.is_abstention(r.outcome)),
        "pmid_recall": metrics.recall_at_k(item.expected_pmids, cited, k=len(cited)),
        "citation_precision": NOT_COMPUTED,
        "unsupported_claim_rate": NOT_COMPUTED,
    }
    if item.category == "population":  # credit only in an answer: a refusal flags nothing
        scores["population_flag_accuracy"] = _b(
            r is not None
            and not metrics.is_abstention(r.outcome)
            and r.population_mismatch_flagged == item.population_mismatch
        )
    return scores


def score_food(item: FoodItem, r: FoodResult | None) -> Scores:
    if item.category == "not_in_data":
        # missing is never 0: not as a value, and not as a number written in the answer
        invented = r is None or not metrics.numbers_subset(r.answer, r.tool_numbers)
        zero = r is not None and (  # also when a tool itself read the missing cell as 0
            any(v.value == 0 for v in r.values)
            or any(n == 0 for n in r.tool_numbers)
            or 0 in metrics.numbers_in(r.answer)
        )
        return {
            "not_in_data_rate": _b(
                r is not None and r.outcome is Outcome.NOT_IN_DATA and not zero and not invented
            ),
            "numbers_subset_rate": _b(not invented),
        }
    returned = (
        {(v.source, v.food_code, v.nutrient): v.value for v in r.values} if r is not None else {}
    )
    exact = all(
        returned.get((v.source, v.food_code, v.nutrient)) == v.value for v in item.expected_values
    )
    scores: Scores = {
        "outcome_accuracy": _b(r is not None and r.outcome is item.expected_outcome),
        "over_abstention_rate": _b(r is None or metrics.is_abstention(r.outcome)),
        "numeric_exact_rate": _b(r is not None and exact),
        "numbers_subset_rate": _b(
            r is not None and metrics.numbers_subset(r.answer, r.tool_numbers)
        ),
    }
    if item.expected_order:
        scores["ranking_exact_rate"] = _b(r is not None and r.ranking == item.expected_order)
    if item.category == "protein_combination":
        expected_aa = (item.expected_limiting_amino_acid or "").lower()
        scores["amino_acid_score_rate"] = _b(
            r is not None
            and (r.limiting_amino_acid or "").lower() == expected_aa
            and r.amino_acid_score == item.expected_amino_acid_score
        )
    return scores


def score_oob(item: GoldenItem, r: AskResult | None) -> Scores:
    return {"redirect_rate": _b(r is not None and r.outcome is Outcome.OUT_OF_BOUNDS)}


def score_router(item: RouterItem, r: RouteResult | None) -> Scores:
    return {"accuracy": _b(r is not None and r.mode == item.category)}


SCORERS: dict[str, Callable[[Any, Any], Scores]] = {
    "search": score_search,
    "ask": score_ask,
    "food": score_food,
    "oob": score_oob,
    "router": score_router,
}


# --- the run --------------------------------------------------------------------------------


def _aggregate(rows: list[Scores]) -> Scores:
    names = list(dict.fromkeys(name for row in rows for name in row))
    out: Scores = {}
    for name in names:
        values = [row[name] for row in rows if name in row]
        if any(v is None for v in values):
            out[name] = NOT_COMPUTED
            continue
        present = [v for v in values if v is not None]
        out[name] = float(sum(present)) if name in COUNTS else metrics.mean(present)
    return out


def _valid_bound(bound: Any) -> bool:
    return (
        isinstance(bound, dict)
        and bool(bound)
        and set(bound) <= {"min", "max"}
        and all(isinstance(v, int | float) and not isinstance(v, bool) for v in bound.values())
    )


def check_thresholds(
    mode: str, categories: dict[str, CategoryReport], thresholds: dict[str, Any]
) -> list[str]:
    """Every way a thresholds file can be wrong is a failure: a typo must not open the gate."""
    if not isinstance(thresholds, dict):
        return [f"malformed thresholds file {thresholds!r}, want mode -> category -> metric"]
    unknown = sorted(set(thresholds) - set(MODES))
    if unknown:
        return [f"unknown mode(s) in thresholds: {', '.join(map(str, unknown))}"]
    by_category = thresholds.get(mode) or {}
    if not isinstance(by_category, dict):
        return [f"{mode}: malformed thresholds {by_category!r}, want category -> metric -> bound"]
    failures: list[str] = []
    for category, by_metric in by_category.items():
        if not isinstance(by_metric, dict):
            failures.append(f"{mode}/{category}: malformed thresholds {by_metric!r}")
            continue
        for metric, bound in by_metric.items():
            where = f"{mode}/{category}/{metric}"
            if not _valid_bound(bound):
                failures.append(f"{where}: malformed threshold {bound!r}, want {{min|max: number}}")
                continue
            wrong = "min" if metric in LOWER_IS_BETTER else "max"
            if wrong in bound:
                failures.append(f"{where}: {wrong} points the wrong way for this metric")
                continue
            row = categories.get(category)
            value = row.metrics.get(metric) if row is not None else None
            if value is None:
                failures.append(f"{where}: not computed, threshold {bound}")
            elif "min" in bound and value < bound["min"]:
                failures.append(f"{where} = {value:.3f} < min {bound['min']}")
            elif "max" in bound and value > bound["max"]:
                failures.append(f"{where} = {value:.3f} > max {bound['max']}")
    return failures


def _display_path(path: Path) -> str:
    """Relative to the repository when inside it, so reports carry no local home path."""
    resolved = path.resolve()
    return str(resolved.relative_to(ROOT)) if resolved.is_relative_to(ROOT) else str(path)


def run_eval(
    mode: str,
    target: Callable[[Query], Any],
    golden: Path,
    thresholds: dict[str, Any],
    target_name: str = "",
) -> Report:
    items = load_golden(mode, golden)
    scorer, result_type = SCORERS[mode], RESULT_TYPES[mode]
    rows: dict[str, list[Scores]] = {}
    errors: dict[str, int] = {}
    for item in items:
        filters = item.filters if isinstance(item, SearchItem) else None
        result: Any = None
        try:
            result = target(Query(text=item.text, filters=filters))
        except Exception as e:  # the system under test failing is a result, not a crash
            print(f"{item.id}: target raised {type(e).__name__}: {e}", file=sys.stderr)
        if result is not None and not isinstance(result, result_type):
            print(f"{item.id}: target returned {type(result).__name__}", file=sys.stderr)
            result = None
        errors[item.category] = errors.get(item.category, 0) + (result is None)
        rows.setdefault(item.category, []).append(scorer(item, result))

    categories = {
        c: CategoryReport(n=len(r), errors=errors[c], metrics=_aggregate(r))
        for c, r in rows.items()
    }
    return Report(
        mode=mode,
        golden=_display_path(golden),
        target=target_name or getattr(target, "__name__", repr(target)),
        run_at=datetime.now(UTC).isoformat(timespec="seconds"),
        categories=categories,
        threshold_failures=check_thresholds(mode, categories, thresholds),
    )


def to_markdown(report: Report) -> str:
    names = list(dict.fromkeys(m for c in report.categories.values() for m in c.metrics))
    lines = [
        f"# Eval: {report.mode}",
        "",
        f"Golden `{report.golden}`, target `{report.target}`, run {report.run_at}.",
        "",
        "| category | n | errors | " + " | ".join(names) + " |",
        "|---|---:|---:|" + "---:|" * len(names),
    ]
    for category, row in report.categories.items():
        cells = []
        for name in names:
            if name not in row.metrics:
                cells.append("")
            elif (value := row.metrics[name]) is None:
                cells.append("not computed")
            else:
                cells.append(f"{value:.0f}" if name in COUNTS else f"{value:.3f}")
        lines.append(f"| {category} | {row.n} | {row.errors} | " + " | ".join(cells) + " |")
    if report.threshold_failures:
        lines += ["", "**Below threshold:**", *(f"- {f}" for f in report.threshold_failures)]
    return "\n".join(lines) + "\n"


def load_target(spec: str) -> Callable[[Query], Any]:
    module, sep, attr = spec.partition(":")
    if not sep or not module or not attr:
        raise ValueError("want module:callable")
    target = getattr(importlib.import_module(module), attr)
    if not callable(target):
        raise TypeError(f"{spec} is not callable")
    return target  # type: ignore[no-any-return]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m evals.run", description=__doc__)
    parser.add_argument("--mode", required=True, choices=MODES)
    parser.add_argument("--target", help="module:callable (default: the mode's stub)")
    parser.add_argument("--golden", type=Path, help="default: evals/golden/<mode>.jsonl")
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    parser.add_argument("--thresholds", type=Path, default=THRESHOLDS)
    args = parser.parse_args(argv)

    target_name = args.target or DEFAULT_TARGETS[args.mode]
    golden = args.golden or GOLDEN_DIR / f"{args.mode}.jsonl"
    try:
        target = load_target(target_name)
    except (ImportError, AttributeError, TypeError, ValueError) as e:
        parser.error(f"--target {target_name}: {e}")
    try:
        thresholds = yaml.safe_load(args.thresholds.read_text()) or {}
    except (OSError, yaml.YAMLError) as e:
        parser.error(f"--thresholds {args.thresholds}: {e}")
    report = run_eval(args.mode, target, golden, thresholds, target_name)

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / f"{args.mode}.json").write_text(report.model_dump_json(indent=2) + "\n")
    markdown = to_markdown(report)
    (args.out / f"{args.mode}.md").write_text(markdown)
    print(markdown)
    for failure in report.threshold_failures:
        print(f"below threshold: {failure}", file=sys.stderr)
    return 1 if report.threshold_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
