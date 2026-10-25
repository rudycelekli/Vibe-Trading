"""The upcoming-unlock window starts on the Beijing date, not the UTC date."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

from backtest.loaders import eastmoney_client
from src.tools import lockup_expiry_tool

# 18:00 UTC on 2026-10-25 is already 02:00 on 2026-10-26 in Beijing.
_INSTANT = datetime(2026, 10, 25, 18, 0, tzinfo=timezone.utc)


class _FrozenDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        return _INSTANT.astimezone(tz) if tz is not None else _INSTANT.replace(tzinfo=None)


def test_market_calendar_window_starts_on_the_beijing_date(monkeypatch):
    monkeypatch.setattr(lockup_expiry_tool, "datetime", _FrozenDatetime)
    empty = {"success": True, "result": {"data": [], "count": 0}}

    with patch.object(eastmoney_client, "get_json", return_value=empty) as get_json:
        lockup_expiry_tool._fetch_lockups(None, 7)

    assert get_json.call_args.kwargs["params"]["filter"] == (
        "(FREE_DATE>='2026-10-26')(FREE_DATE<='2026-11-02')"
    )
