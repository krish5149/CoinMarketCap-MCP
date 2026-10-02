import pytest

from coinmarketcap_mcp.server import clean_code, round_or_none


def test_clean_code_uppercases_and_trims():
    assert clean_code(" btc ", "symbol") == "BTC"


def test_clean_code_rejects_bad_characters():
    with pytest.raises(ValueError):
        clean_code("BTC/USD", "symbol")


def test_round_or_none_rounds_numbers():
    assert round_or_none(1.23456, 2) == 1.23


def test_round_or_none_keeps_missing_values_as_none():
    assert round_or_none(None) is None
    assert round_or_none("n/a") is None
