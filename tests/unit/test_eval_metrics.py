"""The metric functions, on hand-built cases with known answers."""

from __future__ import annotations

from decimal import Decimal

import pytest

from evals import metrics
from evals.schema import Outcome


def test_recall_at_10_counts_expected_pmids_in_the_top_10() -> None:
    top = [str(i) for i in range(20)]
    assert metrics.recall_at_k(["3", "15"], top, k=10) == 0.5
    assert metrics.recall_at_k(["3"], top, k=10) == 1.0
    assert metrics.recall_at_k(["3"], [], k=10) == 0.0


def test_reciprocal_rank_of_first_expected_pmid() -> None:
    assert metrics.reciprocal_rank(["c", "x"], ["a", "b", "c"]) == pytest.approx(1 / 3)
    assert metrics.reciprocal_rank(["z"], ["a"]) == 0.0


def test_abstention_outcomes() -> None:
    assert metrics.is_abstention(Outcome.INSUFFICIENT_EVIDENCE)
    assert metrics.is_abstention(Outcome.NOT_IN_DATA)
    assert metrics.is_abstention(Outcome.OUT_OF_BOUNDS)
    assert not metrics.is_abstention(Outcome.ANSWERED)
    assert not metrics.is_abstention(Outcome.PARTIAL)  # a partial answer is not a refusal


def test_numbers_in_text_handles_decimals_and_commas() -> None:
    assert metrics.numbers_in("Lentils: 2,5 mg iron and 9.10 g protein per 100 g") == {
        Decimal("2.5"),
        Decimal("9.1"),
        Decimal("100"),
    }


def test_comma_before_three_digits_is_a_thousands_separator() -> None:
    """'1,400 mg' must not pass as the tool's 1.4: that would let a 1000x error through."""
    assert metrics.numbers_in("1,400 mg and 12,345,678 and 1,400.5") == {
        Decimal("1400"),
        Decimal("12345678"),
        Decimal("1400.5"),
    }
    assert not metrics.numbers_subset("1,400 mg", [Decimal("1.4")])
    assert metrics.numbers_subset("1,400 mg", [Decimal("1400")])


def test_numbers_subset() -> None:
    tool = [Decimal("2.5"), Decimal("100")]
    assert metrics.numbers_subset("2.5 mg per 100 g", tool)
    assert not metrics.numbers_subset("about 3 mg per 100 g", tool)
    assert metrics.numbers_subset("", tool)


def test_mean_of_nothing_is_none_not_zero() -> None:
    assert metrics.mean([]) is None
    assert metrics.mean([1.0, 0.0]) == 0.5
