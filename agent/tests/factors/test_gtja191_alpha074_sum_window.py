"""GTJA #74 sums the price blend and the volume mean over 20 days.

The 40-day volume mean is shortened to 10, and that shortening used to leak
into both SUM windows. The report, and the factor's own note, keep those
sums at 20.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.factors.base import rank, ts_corr, ts_mean
from src.factors.zoo.gtja191 import alpha_074


def _panel() -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(74)
    idx = pd.bdate_range("2024-01-01", periods=40)
    cols = ["A", "B", "C", "D"]
    low = pd.DataFrame(20 + rng.normal(0, 1, (40, 4)).cumsum(axis=0), index=idx, columns=cols)
    vwap = low + rng.uniform(0.2, 1.5, (40, 4))
    volume = pd.DataFrame(rng.uniform(1e5, 5e5, (40, 4)), index=idx, columns=cols)
    return {"low": low, "vwap": vwap, "volume": volume}


def test_sum_windows_stay_at_20_while_the_volume_mean_stays_short():
    panel = _panel()
    low, vwap, volume = panel["low"], panel["vwap"], panel["volume"]
    price = low * 0.35 + vwap * 0.65
    vol_mean = ts_mean(volume, 10)
    expected = rank(ts_corr(price.rolling(20, min_periods=20).sum(),
                            vol_mean.rolling(20, min_periods=20).sum(), 7))
    expected = expected + rank(ts_corr(rank(vwap), rank(volume), 6))
    shortened = rank(ts_corr(price.rolling(10, min_periods=10).sum(),
                             vol_mean.rolling(10, min_periods=10).sum(), 7))
    shortened = shortened + rank(ts_corr(rank(vwap), rank(volume), 6))

    got = alpha_074.compute(panel)

    pd.testing.assert_frame_equal(got, expected, check_exact=False, rtol=1e-9)
    tail = got.iloc[30:]
    assert tail.notna().any().any()
    finite = tail.notna() & shortened.iloc[30:].notna()
    assert finite.any().any()
    assert not np.allclose(tail.where(finite).to_numpy(),
                           shortened.iloc[30:].where(finite).to_numpy(),
                           equal_nan=True)
