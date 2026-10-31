"""The golden sets: valid against their schema, with the counts PLAN §7 Stage 1 asks for.

These read the real files in evals/golden/. The schema rules themselves are tested on
hand-built items, so a broken rule cannot hide behind well-formed content.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from evals.schema import (
    GOLDEN_DIR,
    MODES,
    AskItem,
    FoodItem,
    OobItem,
    SearchItem,
    load_golden,
)


def golden(mode: str) -> Path:
    return GOLDEN_DIR / f"{mode}.jsonl"


@pytest.mark.parametrize("mode", MODES)
def test_golden_file_validates(mode: str) -> None:
    items = load_golden(mode, golden(mode))
    assert items, f"{mode}.jsonl is empty"
    ids = [i.id for i in items]
    assert len(ids) == len(set(ids)), f"duplicate ids in {mode}.jsonl"


@pytest.mark.parametrize("mode", MODES)
def test_no_draft_items_left(mode: str) -> None:
    drafts = [i.id for i in load_golden(mode, golden(mode)) if i.draft]
    assert drafts == [], f"{mode}.jsonl still has draft items: {drafts}"


EXPECTED_COUNTS: dict[str, dict[str, int]] = {
    "search": {"known_item": 20, "no_match": 5},
    "ask": {"consensus": 8, "contested": 8, "population": 5, "partial": 3, "unanswerable": 8},
    "food": {"lookup": 8, "compare_rank": 4, "protein_combination": 3, "not_in_data": 5},
}


@pytest.mark.parametrize("mode", sorted(EXPECTED_COUNTS))
def test_category_counts(mode: str) -> None:
    counts = Counter(i.category for i in load_golden(mode, golden(mode)))
    assert dict(counts) == EXPECTED_COUNTS[mode]


def test_oob_covers_every_topic_and_two_injections() -> None:
    counts = Counter(i.category for i in load_golden("oob", golden("oob")))
    assert sum(counts.values()) == 10
    assert counts["injection"] == 2
    topics = ("injury", "illness", "pregnancy", "eating_disorder", "dosing", "peds")
    assert all(counts[t] >= 1 for t in topics), counts


def test_router_covers_every_mode_with_ambiguous_items() -> None:
    items = load_golden("router", golden("router"))
    assert len(items) == 30
    labels = {i.category for i in items}
    assert labels == {"search", "question", "food", "plan", "out_of_bounds"}
    assert any(getattr(i, "ambiguous", False) for i in items)


# --- schema rules, on hand-built items ---------------------------------------------------


def search(**kw: Any) -> dict[str, Any]:
    return {"id": "x", "category": "known_item", "query": "q", "expected_pmids": ["123"], **kw}


def test_known_item_needs_a_pmid() -> None:
    with pytest.raises(ValidationError):
        SearchItem.model_validate(search(expected_pmids=[]))


def test_no_match_item_has_no_pmid() -> None:
    with pytest.raises(ValidationError):
        SearchItem.model_validate(search(category="no_match"))
    SearchItem.model_validate(search(category="no_match", expected_pmids=[]))


def test_pmid_is_digits() -> None:
    with pytest.raises(ValidationError):
        SearchItem.model_validate(search(expected_pmids=["PMC123"]))


def test_unknown_field_is_rejected() -> None:
    with pytest.raises(ValidationError):
        SearchItem.model_validate(search(expected_pmid=["123"]))


def ask(**kw: Any) -> dict[str, Any]:
    base = {
        "id": "x",
        "category": "consensus",
        "question": "q",
        "expected_outcome": "ANSWERED",
        "expected_pmids": ["123"],
        "expected_answer": "a",
    }
    return {**base, **kw}


@pytest.mark.parametrize(
    ("category", "outcome"),
    [
        ("consensus", "INSUFFICIENT_EVIDENCE"),
        ("partial", "ANSWERED"),
        ("unanswerable", "ANSWERED"),
        ("unanswerable", "PARTIAL"),
    ],
)
def test_ask_outcome_must_match_category(category: str, outcome: str) -> None:
    with pytest.raises(ValidationError):
        AskItem.model_validate(ask(category=category, expected_outcome=outcome))


def test_unanswerable_item_has_no_expected_pmids() -> None:
    with pytest.raises(ValidationError):
        AskItem.model_validate(
            ask(category="unanswerable", expected_outcome="INSUFFICIENT_EVIDENCE")
        )


def test_population_item_states_whether_it_is_a_mismatch() -> None:
    with pytest.raises(ValidationError):
        AskItem.model_validate(ask(category="population"))
    AskItem.model_validate(ask(category="population", population_mismatch=False))


def food(**kw: Any) -> dict[str, Any]:
    value = {
        "source": "CIQUAL",
        "food_code": "1",
        "food_name": "n",
        "nutrient": "Iron (mg/100 g)",
        "value": "2.5",
    }
    base = {
        "id": "x",
        "category": "lookup",
        "query": "q",
        "expected_outcome": "ANSWERED",
        "expected_values": [value],
    }
    return {**base, **kw}


def test_food_lookup_needs_an_expected_value() -> None:
    with pytest.raises(ValidationError):
        FoodItem.model_validate(food(expected_values=[]))


def test_not_in_data_item_names_what_is_missing() -> None:
    nid = {"category": "not_in_data", "expected_outcome": "NOT_IN_DATA", "expected_values": []}
    with pytest.raises(ValidationError):
        FoodItem.model_validate(food(**nid))
    FoodItem.model_validate(food(**nid, missing="no such food"))


def test_protein_combination_needs_limiting_amino_acid_and_score() -> None:
    with pytest.raises(ValidationError):
        FoodItem.model_validate(food(category="protein_combination"))


def test_compare_rank_order_uses_codes_from_its_values() -> None:
    with pytest.raises(ValidationError):
        FoodItem.model_validate(food(category="compare_rank", expected_order=["999"]))


def test_oob_item_always_expects_a_redirect() -> None:
    with pytest.raises(ValidationError):
        OobItem.model_validate(
            {"id": "x", "category": "injury", "query": "q", "expected_outcome": "ANSWERED"}
        )
