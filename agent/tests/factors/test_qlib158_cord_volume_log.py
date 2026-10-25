"""qlib CORD logs ``volume / previous + 1``, not ``(volume + 1) / (previous + 1)``.

Upstream, pinned by the factor header:
``Corr($close/Ref($close,1), Log($volume/Ref($volume, 1)+1), d)``.
The two logs are different series. Volume 10 then 100 is ``log(11)`` in the
published formula and ``log(101/11)`` in the old one, so the correlation moves.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.factors.base import safe_div
from src.factors.zoo.qlib158 import cord5, cord10, cord20, cord30, cord60

_CASES = [(cord5, 5), (cord10, 10), (cord20, 20), (cord30, 30), (cord60, 60)]


def _panel(window: int) -> dict[str, pd.DataFrame]:
    bars = window + 1
    index = pd.bdate_range("2024-01-01", periods=bars)
    close = pd.DataFrame({"A": np.linspace(10.0, 20.0, bars)}, index=index)
    # Three volume levels. Two levels make the two logs affine, so their
    # correlations match even though the series differ.
    levels = (10.0, 100.0, 30.0)
    volume = pd.DataFrame({"A": [levels[bar % 3] for bar in range(bars)]}, index=index)
    return {"close": close, "volume": volume}


def _corr(left: pd.DataFrame, right: pd.DataFrame, window: int) -> float:
    return float(left.rolling(window, min_periods=window).corr(right).iloc[-1, 0])


@pytest.mark.parametrize("module, window", _CASES)
def test_cord_logs_the_volume_ratio_plus_one(module, window: int) -> None:
    panel = _panel(window)
    close, volume = panel["close"], panel["volume"]
    price = safe_div(close, close.shift(1))
    published = np.log(safe_div(volume, volume.shift(1)) + 1.0)
    shifted_ones = np.log(safe_div(volume + 1.0, volume.shift(1) + 1.0))

    got = float(module.compute(panel).iloc[-1, 0])

    assert got == pytest.approx(_corr(price, published, window))
    assert got != pytest.approx(_corr(price, shifted_ones, window))
