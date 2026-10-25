"""Figures quoted from read_document text are observed evidence (#2050).

The reader returns the PDF as one JSON string. Generic leaf intake skips that
string, so a correct quarterly-report analysis was redacted in full. A number
that appears in the text is evidence; a number that does not is still refused.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.agent.grounding import GroundingLedger

pytestmark = pytest.mark.unit

_TEXT = (
    "营业收入（元） 574,666,588.59 同比 -26.79%。"
    "归母净利润 35,595,441.35。每股收益 0.0444。"
    "期初 100.50 期末 40.25。"
)


def _ledger(tmp_path: Path) -> GroundingLedger:
    ledger = GroundingLedger(run_dir=tmp_path, user_message="解读一下这份季报")
    ledger.ingest_tool_result(
        tool_name="read_document",
        arguments={"file_path": "/reports/q3.pdf"},
        result=json.dumps(
            {
                "status": "ok",
                "file": "q3.pdf",
                "format": "pdf",
                "char_count": 16666,
                "total_pages": 15,
                "pages_read": 15,
                "ocr_pages": 0,
                "text": _TEXT,
            }
        ),
        call_id="doc-1",
        success=True,
    )
    return ledger


def _block(*lines: str) -> str:
    return "\n\n```figures\n" + "\n".join(lines) + "\n```"


def test_document_text_numbers_are_recorded(tmp_path: Path) -> None:
    ledger = _ledger(tmp_path)

    amounts = {
        record.value
        for record in ledger._evidence
        if record.field == "document.text" and record.source == "document:q3.pdf"
    }
    percents = {
        record.value
        for record in ledger._evidence
        if record.field == "document.text.percent"
    }

    assert 574_666_588.59 in amounts
    assert 35_595_441.35 in amounts
    assert 0.0444 in amounts
    assert -26.79 in percents
    assert 16666 not in amounts


def test_a_declared_document_figure_matches_the_text(tmp_path: Path) -> None:
    ledger = _ledger(tmp_path)
    answer = (
        "营业收入 574,666,588.59 元，同比 -26.79%，归母净利润 35,595,441.35，每股收益 0.0444。"
        + _block(
            "574666588.59 | observed | 营业收入 | doc-1",
            "-26.79% | observed | 同比 | doc-1",
            "35595441.35 | observed | 净利润 | doc-1",
            "0.0444 | observed | EPS | doc-1",
        )
    )

    result = ledger.validate_final_answer(answer)

    assert result.valid, result.issues


def test_an_undeclared_document_figure_is_observed(tmp_path: Path) -> None:
    ledger = _ledger(tmp_path)

    result = ledger.validate_final_answer("营业收入 574,666,588.59 元，同比 -26.79%。")

    assert result.valid, result.issues


def test_a_figure_the_document_does_not_contain_is_refused(tmp_path: Path) -> None:
    ledger = _ledger(tmp_path)
    answer = "营业收入 999,999.99 元。" + _block(
        "999999.99 | observed | 营业收入 | doc-1"
    )

    result = ledger.validate_final_answer(answer)

    assert result.valid is False
    assert result.issues[0]["code"] == "numeric_claim_conflict"
    assert result.issues[0]["reason"] == "not_in_referenced_call"


def test_a_difference_of_two_document_amounts_can_anchor(tmp_path: Path) -> None:
    ledger = _ledger(tmp_path)
    answer = (
        "期初 100.50 元，期末 40.25 元，变动 60.25 元。"
        + _block(
            "100.50 | observed | 期初 | doc-1",
            "40.25 | observed | 期末 | doc-1",
            "60.25 | derived | 100.50 - 40.25 | doc-1",
        )
    )

    result = ledger.validate_final_answer(answer)

    assert result.valid, result.issues


def test_another_call_cannot_borrow_a_document_number(tmp_path: Path) -> None:
    ledger = _ledger(tmp_path)
    ledger.ingest_tool_result(
        tool_name="get_market_data",
        arguments={"symbol": "000001.SZ"},
        result=json.dumps(
            {
                "000001.SZ": [
                    {
                        "trade_date": "2026-09-09",
                        "open": 10.0,
                        "high": 11.0,
                        "low": 9.0,
                        "close": 10.5,
                        "volume": 1000,
                    }
                ]
            }
        ),
        call_id="mkt-1",
        success=True,
    )
    answer = "000001.SZ 收盘 574,666,588.59 元。" + _block(
        "574666588.59 | observed | close | mkt-1"
    )

    result = ledger.validate_final_answer(answer)

    assert result.valid is False
    assert result.issues[0]["reason"] == "not_in_referenced_call"
