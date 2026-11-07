"""Research mode (pit=False) must keep the same alias priority as PIT mode."""

from __future__ import annotations

import pytest

from backtest.loaders._fundamental_schema import SEC_CONCEPT_MAP
from backtest.loaders.fundamentals_loader import _extract_concept_series


def _facts(values: dict[str, float], *, start: str | None) -> dict[str, object]:
    def row(value: float) -> dict[str, object]:
        item: dict[str, object] = {"end": "2023-12-31", "filed": "2024-02-01", "val": value, "form": "10-K"}
        if start is not None:
            item["start"] = start
        return item

    return {"facts": {"us-gaap": {name: {"units": {"USD": [row(v)]}} for name, v in values.items()}}}


@pytest.mark.parametrize("pit", [True, False])
def test_flow_alias_priority_is_the_same_in_both_modes(pit: bool) -> None:
    first, *rest = SEC_CONCEPT_MAP["revenue"]
    facts = _facts({first: 1000.0, rest[-1]: 900.0}, start="2023-01-01")
    series = _extract_concept_series(facts, SEC_CONCEPT_MAP["revenue"], "annual", pit=pit)
    assert series["value"].tolist() == [1000.0]


@pytest.mark.parametrize("pit", [True, False])
def test_instant_alias_priority_is_the_same_in_both_modes(pit: bool) -> None:
    first, *rest = SEC_CONCEPT_MAP["total_debt"]
    facts = _facts({first: 5000.0, rest[-1]: 300.0}, start=None)
    series = _extract_concept_series(facts, SEC_CONCEPT_MAP["total_debt"], "annual", pit=pit)
    assert series["value"].tolist() == [5000.0]
