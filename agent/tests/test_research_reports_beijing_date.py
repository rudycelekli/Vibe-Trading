"""The default report window ends on the Beijing date, not the host's date."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch
from zoneinfo import ZoneInfo

from src.tools import research_reports_tool as rrt
from src.tools.research_reports_tool import ResearchReportsTool

# 21:00 on 2026-10-25 in New York is already 09:00 on 2026-10-26 in Beijing.
_INSTANT = datetime(2026, 10, 26, 1, 0, tzinfo=timezone.utc)


class _NewYorkHostDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        local = _INSTANT.astimezone(tz or ZoneInfo("America/New_York"))
        return local if tz is not None else local.replace(tzinfo=None)


def test_default_window_ends_on_the_beijing_date(monkeypatch):
    monkeypatch.setattr(rrt, "datetime", _NewYorkHostDatetime)
    captured: dict = {}

    def _fake_get_json(url, params=None, **kwargs):
        captured.update(params or {})
        return {"data": []}

    with (
        patch.object(rrt, "get_json", side_effect=_fake_get_json),
        patch.object(rrt, "resolve_secid", return_value="1.600519"),
        patch.object(rrt, "_fetch_consensus_eps", return_value=[]),
    ):
        ResearchReportsTool().execute(code="600519.SH")

    assert captured["endTime"] == "20261026"
    assert captured["beginTime"] == "20241026"
