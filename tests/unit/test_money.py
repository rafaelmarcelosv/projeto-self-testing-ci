import pytest
from fastapi import HTTPException
from src.domain.models import money, to_cents


@pytest.mark.parametrize("value,expected", [("1", 100), ("0.01", 1), ("25.50", 2550), ("1.00", 100)])
def test_to_cents(value, expected):
    assert to_cents(value) == expected


@pytest.mark.parametrize("value", ["-1", "0", "1.234", "abc", "NaN", "Infinity"])
def test_invalid_values(value):
    with pytest.raises(HTTPException):
        to_cents(value)


def test_zero_allowed_only_when_specified():
    assert to_cents("0", allow_zero=True) == 0


def test_money_format():
    assert money(1234) == "12.34"
