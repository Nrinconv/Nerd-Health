"""Stand-in systems. They do nothing useful, so their scores are the floor."""

from __future__ import annotations

from evals.schema import AskResult, FoodResult, Query, RouteResult, SearchResult


def empty_search(q: Query) -> SearchResult:
    raise NotImplementedError


def abstain_ask(q: Query) -> AskResult:
    raise NotImplementedError


def abstain_food(q: Query) -> FoodResult:
    raise NotImplementedError


def constant_router(q: Query) -> RouteResult:
    raise NotImplementedError
