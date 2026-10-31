"""Stand-in systems. They do nothing useful, so their scores are the floor.

Until a stage delivers the real mode, `python -m evals.run` targets these by default.
"""

from __future__ import annotations

from evals.schema import AskResult, FoodResult, Outcome, Query, RouteResult, SearchResult


def empty_search(q: Query) -> SearchResult:
    return SearchResult(outcome=Outcome.INSUFFICIENT_EVIDENCE)


def abstain_ask(q: Query) -> AskResult:
    return AskResult(outcome=Outcome.INSUFFICIENT_EVIDENCE)


def abstain_food(q: Query) -> FoodResult:
    return FoodResult(outcome=Outcome.NOT_IN_DATA)


def constant_router(q: Query) -> RouteResult:
    return RouteResult(mode="question")
