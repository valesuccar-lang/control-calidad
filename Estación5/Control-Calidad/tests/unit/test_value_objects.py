"""Tests for domain value objects"""
import pytest
from app.domain.value_objects import RoleVO, EmailVO, PhoneVO, CurrencyVO, QuantityVO, PercentageVO


def test_role_vo():
    assert RoleVO.ANALISTA == "ANALISTA"
    assert RoleVO.JEFE_QA == "JEFE_QA"


def test_email_vo_valid():
    e = EmailVO("user@example.com")
    assert str(e) == "user@example.com"


def test_email_vo_invalid():
    with pytest.raises(ValueError):
        EmailVO("not-an-email")


def test_phone_vo_valid():
    p = PhoneVO("+573123456789")  # +57 + 10 digits
    assert str(p) == "+573123456789"


def test_phone_vo_invalid():
    with pytest.raises(ValueError):
        PhoneVO("123456")


def test_currency_vo():
    a = CurrencyVO(100.0, "COP")
    b = CurrencyVO(50.0, "COP")
    assert str(a) == "100.00 COP"
    c = a + b
    assert c.amount == 150.0
    d = a - b
    assert d.amount == 50.0


def test_currency_vo_invalid():
    with pytest.raises(ValueError):
        CurrencyVO(-1.0)
    with pytest.raises(ValueError):
        CurrencyVO(10.0, "BTC")


def test_currency_vo_mixed_currencies():
    a = CurrencyVO(100.0, "COP")
    b = CurrencyVO(50.0, "USD")
    with pytest.raises(ValueError):
        a + b
    with pytest.raises(ValueError):
        a - b


def test_quantity_vo():
    q = QuantityVO(10)
    assert str(q) == "10"
    r = q + QuantityVO(5)
    assert r.value == 15
    s = q - QuantityVO(3)
    assert s.value == 7


def test_quantity_vo_invalid():
    with pytest.raises(ValueError):
        QuantityVO(0)
    with pytest.raises(ValueError):
        QuantityVO(5) - QuantityVO(10)


def test_percentage_vo():
    p = PercentageVO(75.5)
    assert str(p) == "75.5%"


def test_percentage_vo_invalid():
    with pytest.raises(ValueError):
        PercentageVO(-1.0)
    with pytest.raises(ValueError):
        PercentageVO(101.0)
