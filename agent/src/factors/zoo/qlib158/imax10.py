# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 最高价位置 10日
# 简要说明: IdxMax(high, 10)/10。最早一根为 1/10，最近一根为 1。
# 典型用途: 值接近 1 表示最高价出现在最近一根。
# ============================================================
"""qlib158 IMAX10: formula = \\mathrm{IdxMax}(\\mathrm{high}, 10) / 10."""
from __future__ import annotations

import pandas as pd
from src.factors.base import ts_idxmax

__alpha_meta__ = {
    'id': 'qlib158_imax10',
    'theme': ['momentum'],
    'formula_latex': '\\\\mathrm{IdxMax}(\\\\mathrm{high}, 10) / 10',
    'columns_required': ['high'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk', 'equity_in', 'equity_kr'],
    'frequency': ['1d'],
    'decay_horizon': 10,
    'min_warmup_bars': 10,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 IMAX10 on the supplied OHLCV panel."""
    h = panel['high']
    return ts_idxmax(h, 10) / float(10)
