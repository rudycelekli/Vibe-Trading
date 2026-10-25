"""The generated shadow signal engine must gate on the RSI its rules were mined with."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

from src.shadow_account.codegen import render_signal_engine, validate_generated
from src.shadow_account.indicators import compute_rsi
from src.shadow_account.models import ShadowProfile, ShadowRule

_CLOSES = [
    100.0, 101.0, 99.5, 102.0, 101.0, 103.0, 100.0, 104.0, 101.5, 105.0,
    102.0, 106.0, 103.0, 107.0, 104.5, 106.0, 108.0, 103.5, 107.0, 109.0,
]


def _engine(tmp_path: Path, rsi_min: float, rsi_max: float):
    rule = ShadowRule(
        rule_id="R1",
        human_text="RSI band",
        entry_condition={
            "market": "china_a",
            "entry_hour": {"min": 0, "max": 23},
            "entry_rsi14": {"min": rsi_min, "max": rsi_max},
        },
        exit_condition={"holding_days": {"min": 1, "max": 1}},
        holding_days_range=(1, 1),
        support_count=10,
        coverage_rate=0.5,
        sample_trades=("600519@2026-01-10",),
    )
    profile = ShadowProfile(
        shadow_id="shadow_rsi",
        created_at="2026-01-01T00:00:00",
        journal_hash="rsi",
        source_market="china_a",
        profitable_roundtrips=10,
        total_roundtrips=20,
        date_range=("2025-01-01", "2026-01-01"),
        profile_text="rsi",
        rules=(rule,),
        preferred_markets=("china_a",),
        typical_holding_days=(1.0, 1.0),
    )
    source = render_signal_engine(profile)
    ok, err = validate_generated(source)
    assert ok, err
    path = tmp_path / "signal_engine.py"
    path.write_text(source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("shadow_rsi_engine", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.SignalEngine()


@pytest.mark.unit
def test_generated_rsi_matches_the_extractor_rsi(tmp_path: Path) -> None:
    close = pd.Series(_CLOSES, index=pd.date_range("2026-01-02", periods=len(_CLOSES), freq="B"))
    generated = _engine(tmp_path, 0.0, 100.0)._compute_rsi(close)
    pd.testing.assert_series_equal(generated, compute_rsi(close), check_names=False)


@pytest.mark.unit
def test_generated_engine_enters_inside_the_mined_rsi_band(tmp_path: Path) -> None:
    index = pd.date_range("2026-01-02", periods=len(_CLOSES), freq="B")
    close = pd.Series(_CLOSES, index=index)
    mined = float(compute_rsi(close).iloc[-1])
    engine = _engine(tmp_path, mined - 0.2, mined + 0.2)
    frame = pd.DataFrame({"open": close, "high": close, "low": close, "close": close, "volume": 1.0})

    signal = engine.generate({"600519.SH": frame})["600519.SH"]

    assert signal.iloc[-1] == pytest.approx(1.0)
