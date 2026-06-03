"""Value objects for domain model"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RoleVO(str, Enum):
    """Role value object"""
    ANALISTA = "ANALISTA"
    JEFE_QA = "JEFE_QA"
    ADMIN = "ADMIN"
    GERENTE = "GERENTE"


@dataclass(frozen=True)
class EmailVO:
    """Email value object - immutable"""
    value: str

    def __post_init__(self):
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, self.value):
            raise ValueError(f"Invalid email format: {self.value}")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class PhoneVO:
    """Phone number value object - immutable"""
    value: str

    def __post_init__(self):
        import re
        # Colombian phone number format
        if not re.match(r'^\+?57\d{10}$', self.value.replace(" ", "")):
            raise ValueError(f"Invalid Colombian phone format: {self.value}")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class CurrencyVO:
    """Currency value object - immutable"""
    amount: float
    currency: str = "COP"

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
        if self.currency not in ("COP", "USD", "EUR"):
            raise ValueError(f"Unsupported currency: {self.currency}")

    def __add__(self, other: "CurrencyVO") -> "CurrencyVO":
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return CurrencyVO(self.amount + other.amount, self.currency)

    def __sub__(self, other: "CurrencyVO") -> "CurrencyVO":
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different currencies")
        return CurrencyVO(self.amount - other.amount, self.currency)

    def __str__(self) -> str:
        return f"{self.amount:.2f} {self.currency}"


@dataclass(frozen=True)
class QuantityVO:
    """Quantity value object - immutable"""
    value: int

    def __post_init__(self):
        if self.value <= 0:
            raise ValueError("Quantity must be positive")

    def __add__(self, other: "QuantityVO") -> "QuantityVO":
        return QuantityVO(self.value + other.value)

    def __sub__(self, other: "QuantityVO") -> "QuantityVO":
        result = self.value - other.value
        if result < 0:
            raise ValueError("Cannot subtract more than available quantity")
        return QuantityVO(result)

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class PercentageVO:
    """Percentage value object - immutable"""
    value: float

    def __post_init__(self):
        if not (0 <= self.value <= 100):
            raise ValueError("Percentage must be between 0 and 100")

    def __str__(self) -> str:
        return f"{self.value:.1f}%"
