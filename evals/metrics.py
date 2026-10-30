"""Metric functions. Pure: no I/O, no model calls."""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from decimal import Decimal

from evals.schema import Outcome

ABSTENTIONS = frozenset({Outcome.INSUFFICIENT_EVIDENCE, Outcome.NOT_IN_DATA, Outcome.OUT_OF_BOUNDS})
# A comma before exactly three digits groups thousands ("1,400"); any other comma is a
# decimal point ("2,5"). Reading "1,400" as 1.4 would let a 1000x error pass as tool output.
_NUMBER = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?(?!\d)|\d+(?:[.,]\d+)?")


def recall_at_k(expected: Sequence[str], ranked: Sequence[str], k: int = 10) -> float:
    """Share of the expected PMIDs found in the first k results."""
    top = set(ranked[:k])
    return sum(p in top for p in expected) / len(expected)


def reciprocal_rank(expected: Sequence[str], ranked: Sequence[str]) -> float:
    """1 / rank of the first expected PMID; 0 if none is returned."""
    wanted = set(expected)
    for rank, pmid in enumerate(ranked, start=1):
        if pmid in wanted:
            return 1 / rank
    return 0.0


def is_abstention(outcome: Outcome) -> bool:
    """PARTIAL answers the supported part, so it is not an abstention."""
    return outcome in ABSTENTIONS


def numbers_in(text: str) -> set[Decimal]:
    """Every number written in the text, normalised (2,50 and 2.5 are the same number)."""
    return {Decimal(_plain(m)).normalize() for m in _NUMBER.findall(text)}


def _plain(number: str) -> str:
    if re.fullmatch(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?", number):
        return number.replace(",", "")
    return number.replace(",", ".")


def numbers_subset(text: str, tool_numbers: Iterable[Decimal]) -> bool:
    """True when every number in the text was produced by a tool."""
    return numbers_in(text) <= {n.normalize() for n in tool_numbers}


def mean(values: Sequence[float]) -> float | None:
    """None when there is nothing to average: no data is not a score of 0."""
    return sum(values) / len(values) if values else None
