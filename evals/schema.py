"""Golden-set items and the result each mode must return.

One Pydantic model per golden file (`evals/golden/<mode>.jsonl`), and one result model per
mode: the contract the system under evaluation returns to `evals.run`. `Outcome` is F16's
typed outcome, so abstention is scored from a field, never by reading prose.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
MODES = ("search", "ask", "food", "oob", "router")
Mode = Literal["search", "ask", "food", "oob", "router"]

Pmid = Annotated[str, StringConstraints(pattern=r"^[0-9]{1,9}$")]


class Outcome(StrEnum):
    ANSWERED = "ANSWERED"
    PARTIAL = "PARTIAL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    NOT_IN_DATA = "NOT_IN_DATA"
    OUT_OF_BOUNDS = "OUT_OF_BOUNDS"


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


# --- golden items -------------------------------------------------------------------------


class GoldenItem(_Model):
    id: str
    category: str
    draft: bool = False  # a draft item fails test_no_draft_items_left
    notes: str = ""

    @property
    def text(self) -> str:
        raise NotImplementedError


class SearchFilters(_Model):
    year_min: int | None = None
    year_max: int | None = None
    study_types: list[str] = []


class SearchItem(GoldenItem):
    category: Literal["known_item", "no_match"]
    query: str
    filters: SearchFilters | None = None
    expected_pmids: list[Pmid]
    expected_titles: list[str] = []  # for human review only


class AskItem(GoldenItem):
    category: Literal["consensus", "contested", "population", "partial", "unanswerable"]
    question: str
    expected_outcome: Outcome
    expected_pmids: list[Pmid]
    expected_answer: str = ""
    population_mismatch: bool | None = None


class ExpectedValue(_Model):
    source: Literal["CIQUAL", "USDA_SR_LEGACY"]
    food_code: str
    food_name: str
    nutrient: str
    value: Decimal


class FoodItem(GoldenItem):
    category: Literal["lookup", "compare_rank", "protein_combination", "not_in_data"]
    query: str
    expected_outcome: Outcome
    expected_values: list[ExpectedValue]
    expected_order: list[str] = []
    expected_limiting_amino_acid: str | None = None
    expected_amino_acid_score: Decimal | None = None
    missing: str = ""


class OobItem(GoldenItem):
    category: Literal[
        "injury", "illness", "pregnancy", "eating_disorder", "dosing", "peds", "injection"
    ]
    query: str
    expected_outcome: Outcome


RouteLabel = Literal["search", "question", "food", "plan", "out_of_bounds"]


class RouterItem(GoldenItem):
    category: RouteLabel
    query: str
    ambiguous: bool = False


def load_golden(mode: str, path: Path) -> list[GoldenItem]:
    raise NotImplementedError


# --- what the system under evaluation returns ---------------------------------------------


class Query(_Model):
    text: str
    filters: SearchFilters | None = None


class SearchResult(_Model):
    outcome: Outcome
    pmids: list[Pmid] = []  # ranked, best first


class AskResult(_Model):
    outcome: Outcome
    answer: str = ""
    cited_pmids: list[Pmid] = []
    population_mismatch_flagged: bool = False


class FoodValue(_Model):
    source: Literal["CIQUAL", "USDA_SR_LEGACY"]
    food_code: str
    nutrient: str
    value: Decimal | None  # None is "missing in the table", never 0


class FoodResult(_Model):
    outcome: Outcome
    answer: str = ""
    values: list[FoodValue] = []
    ranking: list[str] = []
    limiting_amino_acid: str | None = None
    amino_acid_score: Decimal | None = None
    tool_numbers: list[Decimal] = []  # every number the tools produced


class RouteResult(_Model):
    mode: RouteLabel
