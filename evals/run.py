"""Run a golden set against a callable and write a per-category report.

python -m evals.run --mode search [--target module:callable] [--golden path]
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from evals.schema import Query

NOT_COMPUTED = None
LOWER_IS_BETTER = frozenset({"fabrication_count", "over_abstention_rate"})


class CategoryReport(BaseModel):
    n: int
    errors: int = 0
    metrics: dict[str, float | None]


class Report(BaseModel):
    mode: str
    golden: str
    target: str
    categories: dict[str, CategoryReport]
    threshold_failures: list[str] = []


def run_eval(
    mode: str,
    target: Callable[[Query], Any],
    golden: Path,
    thresholds: dict[str, Any],
    target_name: str = "",
) -> Report:
    raise NotImplementedError


def main(argv: Sequence[str] | None = None) -> int:
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
