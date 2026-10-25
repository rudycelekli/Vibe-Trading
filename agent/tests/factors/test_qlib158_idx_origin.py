"""qlib IMAX/IMIN count the first extreme from 1, not a 0-based recent tie.

``IdxMax($high, d)/d`` is ``argmax() + 1`` on a window ordered oldest to
newest (qlib ``ops.py``). The oldest bar is ``1/d`` and the current bar is 1.
A 0-based index prints 0.8 for a 5-day high that is today, and a tie that
keeps the newer bar prints the other extreme.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.factors.zoo.qlib158 import imax10, imax20, imax30, imax5, imax60
from src.factors.zoo.qlib158 import imin10, imin20, imin30, imin5, imin60
from src.factors.zoo.qlib158 import imxd10, imxd20, imxd30, imxd5, imxd60

_IMAX = [(imax5, 5), (imax10, 10), (imax20, 20), (imax30, 30), (imax60, 60)]
_IMIN = [(imin5, 5), (imin10, 10), (imin20, 20), (imin30, 30), (imin60, 60)]
_IMXD = [(imxd5, 5), (imxd10, 10), (imxd20, 20), (imxd30, 30), (imxd60, 60)]


def _frame(values: list[float]) -> pd.DataFrame:
    index = pd.bdate_range("2024-01-01", periods=len(values))
    return pd.DataFrame({"A": values}, index=index, dtype=float)


@pytest.mark.parametrize("module, window", _IMAX)
def test_a_high_on_the_current_bar_is_one(module, window: int) -> None:
    high = _frame([float(bar) for bar in range(1, window + 1)])

    got = module.compute({"high": high}).iloc[-1, 0]

    assert got == 1.0
    assert got != (window - 1) / window


@pytest.mark.parametrize("module, window", _IMAX)
def test_a_tied_high_keeps_the_earlier_bar(module, window: int) -> None:
    high = [float(window)] + [1.0] * (window - 2) + [float(window)]

    got = module.compute({"high": _frame(high)}).iloc[-1, 0]

    assert got == pytest.approx(1.0 / window)
    assert got != 1.0


@pytest.mark.parametrize("module, window", _IMIN)
def test_a_low_on_the_current_bar_is_one(module, window: int) -> None:
    low = _frame([float(bar) for bar in range(window, 0, -1)])

    got = module.compute({"low": low}).iloc[-1, 0]

    assert got == 1.0


@pytest.mark.parametrize("module, window", _IMXD)
def test_the_span_uses_the_first_of_each_extreme(module, window: int) -> None:
    high = [float(window)] + [1.0] * (window - 2) + [float(window)]
    low = [float(window)] + [1.0] + [float(window)] * (window - 2)
    panel = {"high": _frame(high), "low": _frame(low)}

    got = module.compute(panel).iloc[-1, 0]

    # First high is bar 1, first low is bar 2.
    assert got == pytest.approx((1 - 2) / window)
    assert not np.isclose(got, (window - 2) / window)
