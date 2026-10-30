"""Golden-set items and the result each mode must return.

One Pydantic model per golden file (`evals/golden/<mode>.jsonl`), and one result model per
mode: the contract the system under evaluation returns to `evals.run`. `Outcome` is F16's
typed outcome, so abstention is scored from a field, never by reading prose.
"""

from __future__ import annotations

import json
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

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
        """What the system under evaluation receives."""
        return str(getattr(self, "query", ""))


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

    @model_validator(mode="after")
    def _pmids_match_category(self) -> Self:
        if self.category == "known_item" and not self.expected_pmids:
            raise ValueError("a known-item query needs at least one expected PMID")
        if self.category == "no_match" and self.expected_pmids:
            raise ValueError("a no-match query has no expected PMID")
        return self


class AskItem(GoldenItem):
    category: Literal["consensus", "contested", "population", "partial", "unanswerable"]
    question: str
    expected_outcome: Outcome
    expected_pmids: list[Pmid]
    expected_answer: str = ""
    population_mismatch: bool | None = None

    @property
    def text(self) -> str:
        return self.question

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        expected = ASK_OUTCOMES[self.category]
        if self.expected_outcome is not expected:
            raise ValueError(f"{self.category} items expect {expected}")
        if self.category == "unanswerable" and self.expected_pmids:
            raise ValueError("an unanswerable item has no expected PMID")
        if self.category != "unanswerable" and not self.expected_pmids:
            raise ValueError("an answerable item needs at least one expected PMID")
        if self.category == "population" and self.population_mismatch is None:
            raise ValueError("a population item must state population_mismatch")
        return self


ASK_OUTCOMES: dict[str, Outcome] = {
    "consensus": Outcome.ANSWERED,
    "contested": Outcome.ANSWERED,
    "population": Outcome.ANSWERED,
    "partial": Outcome.PARTIAL,
    "unanswerable": Outcome.INSUFFICIENT_EVIDENCE,
}


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

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.category == "not_in_data":
            if self.expected_outcome is not Outcome.NOT_IN_DATA:
                raise ValueError("not_in_data items expect NOT_IN_DATA")
            if self.expected_values:
                raise ValueError("a not_in_data item has no expected value")
            if not self.missing:
                raise ValueError("a not_in_data item must say what is missing")
            return self
        if self.expected_outcome is not Outcome.ANSWERED:
            raise ValueError(f"{self.category} items expect ANSWERED")
        if not self.expected_values:
            raise ValueError("an answerable food item needs expected values from the table")
        codes = {v.food_code for v in self.expected_values}
        if not set(self.expected_order) <= codes:
            raise ValueError("expected_order may only use food codes from expected_values")
        if self.category == "protein_combination" and (
            self.expected_limiting_amino_acid is None or self.expected_amino_acid_score is None
        ):
            raise ValueError("a protein combination needs the limiting amino acid and score")
        return self


class OobItem(GoldenItem):
    category: Literal[
        "injury", "illness", "pregnancy", "eating_disorder", "dosing", "peds", "injection"
    ]
    query: str
    expected_outcome: Outcome

    @model_validator(mode="after")
    def _redirect(self) -> Self:
        if self.expected_outcome is not Outcome.OUT_OF_BOUNDS:
            raise ValueError("an out-of-bounds item always expects OUT_OF_BOUNDS")
        return self


RouteLabel = Literal["search", "question", "food", "plan", "out_of_bounds"]


class RouterItem(GoldenItem):
    category: RouteLabel
    query: str
    ambiguous: bool = False


ITEM_MODELS: dict[str, type[GoldenItem]] = {
    "search": SearchItem,
    "ask": AskItem,
    "food": FoodItem,
    "oob": OobItem,
    "router": RouterItem,
}


def load_golden(mode: str, path: Path) -> list[GoldenItem]:
    """Parse and validate a golden file; the error names the line that failed."""
    model = ITEM_MODELS[mode]
    items: list[GoldenItem] = []
    for n, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            items.append(model.model_validate(json.loads(line)))
        except ValueError as e:  # json.JSONDecodeError and ValidationError both are
            raise ValueError(f"{path}:{n}: {e}") from e
    return items


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
    # untruncated, rounded to 2 decimals half up (evals/golden/SOURCES.md)
    amino_acid_score: Decimal | None = None
    tool_numbers: list[Decimal] = []  # every number the tools produced


class RouteResult(_Model):
    mode: RouteLabel
