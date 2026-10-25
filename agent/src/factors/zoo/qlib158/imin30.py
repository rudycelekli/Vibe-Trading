# Adapted from microsoft/qlib@d5379c520f66a39953bad76234a7019a72796fd0:qlib/contrib/data/handler.py
# (Apache-2.0). Copyright (c) Microsoft Corporation.
# ============================================================
# 中文名称: 最低价位置 30日
# 简要说明: IdxMin(low, 30)/30。最早一根为 1/30，最近一根为 1。
# 典型用途: 值接近 1 表示最低价出现在最近一根。
# ============================================================
"""qlib158 IMIN30: formula = \\mathrm{IdxMin}(\\mathrm{low}, 30) / 30."""
from __future__ import annotations

import pandas as pd
from src.factors.base import ts_idxmin

__alpha_meta__ = {
    'id': 'qlib158_imin30',
    'theme': ['momentum'],
    'formula_latex': '\\\\mathrm{IdxMin}(\\\\mathrm{low}, 30) / 30',
    'columns_required': ['low'],
    'universe': ['equity_us', 'equity_cn', 'equity_hk', 'equity_in', 'equity_kr'],
    'frequency': ['1d'],
    'decay_horizon': 30,
    'min_warmup_bars': 30,
}


def compute(panel: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return qlib158 IMIN30 on the supplied OHLCV panel."""
    lo = panel['low']
    return ts_idxmin(lo, 30) / float(30)
