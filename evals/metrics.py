"""Metric functions. Pure: no I/O, no model calls."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from decimal import Decimal

from evals.schema import Outcome


def recall_at_k(expected: Sequence[str], ranked: Sequence[str], k: int = 10) -> float:
    raise NotImplementedError


def reciprocal_rank(expected: Sequence[str], ranked: Sequence[str]) -> float:
    raise NotImplementedError


def is_abstention(outcome: Outcome) -> bool:
    raise NotImplementedError


def numbers_in(text: str) -> set[Decimal]:
    raise NotImplementedError


def numbers_subset(text: str, tool_numbers: Iterable[Decimal]) -> bool:
    raise NotImplementedError


def mean(values: Sequence[float]) -> float | None:
    raise NotImplementedError
