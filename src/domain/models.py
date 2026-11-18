from decimal import Decimal, InvalidOperation
from fastapi import HTTPException


def to_cents(value: str, allow_zero: bool = False) -> int:
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError, TypeError):
        raise HTTPException(422, "Valor inválido")
    if not number.is_finite() or number.as_tuple().exponent < -2:
        raise HTTPException(422, "Use no máximo duas casas decimais")
    cents = int(number * 100)
    if cents < 0 or (cents == 0 and not allow_zero):
        raise HTTPException(422, "O valor deve ser positivo")
    return cents


def money(cents: int) -> str:
    return f"{Decimal(cents) / 100:.2f}"
