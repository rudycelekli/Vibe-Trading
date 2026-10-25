"""yfinance symbol translation for US class shares (#1351).

Yahoo/yfinance serve US class shares only in hyphen form (``BRK-B``);
the dot form (``BRK.B``) returns empty data, so the ``.US`` conversion
must fold internal dots to hyphens.
"""

from backtest.loaders.yfinance_loader import _to_yfinance_symbol


def test_class_shares_map_to_hyphen_form() -> None:
    assert _to_yfinance_symbol("BRK.B.US") == "BRK-B"
    assert _to_yfinance_symbol("BRK.A.US") == "BRK-A"
    assert _to_yfinance_symbol("BF.B.US") == "BF-B"


def test_plain_tickers_unchanged() -> None:
    assert _to_yfinance_symbol("AAPL.US") == "AAPL"
    assert _to_yfinance_symbol("AAPL") == "AAPL"


def test_crypto_and_suffix_forms_untouched() -> None:
    assert _to_yfinance_symbol("BTC-USDT") == "BTC-USD"
    assert _to_yfinance_symbol("TD.TO") == "TD.TO"


def test_hkex_five_digit_codes_use_yahoo_four_digit_ticker() -> None:
    # HKEX prints 00700. Yahoo's chart 404s that form and serves 0700.HK.
    # A genuine five-digit counter (80700, the RMB line) has nothing to drop.
    assert _to_yfinance_symbol("00700.HK") == "0700.HK"
    assert _to_yfinance_symbol("00005.HK") == "0005.HK"
    assert _to_yfinance_symbol("80700.HK") == "80700.HK"
