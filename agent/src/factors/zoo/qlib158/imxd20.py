# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 极值跨度 20日
# 简要说明: (IdxMax(high, 20) - IdxMin(low, 20))/20，两次极值都取窗口内第一次出现的位置。
# 典型用途: 衡量20日内从最低点到最高点所需的时间，反映趋势持续性。
# ============================================================
"""qlib158 IMXD20: formula = (\\mathrm{IdxMax}(\\mathrm{high}, 20) - \\mathrm{IdxMin}(\\mathrm{low}, 20)) / 20."""
from __future__ import annotations

import pandas as pd
from src.factors.base import ts_idxmax, ts_idxmin

__alpha_meta__ = {
    'id': 'qlib158_imxd20',
    'theme': ['momentum'],
    'formula_latex': '(\\\\mathrm{IdxMax}(\\\\mathrm{high}, 20) - \\\\mathrm{IdxMin}(\\\\mathrm{low}, 20)) / 20',
    'columns_required': ['high', 'low'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk', 'equity_in', 'equity_kr'],
    'frequency': ['1d'],
    'decay_horizon': 20,
    'min_warmup_bars': 20,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 IMXD20 on the supplied OHLCV panel."""
    h = panel['high']
    lo = panel['low']
    return (ts_idxmax(h, 20) - ts_idxmin(lo, 20)) / float(20)
