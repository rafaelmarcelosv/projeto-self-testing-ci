from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, Field

router = APIRouter()


class AccountInput(BaseModel):
    owner: str
    initial_balance: str = "0.00"


class TransferInput(BaseModel):
    source_id: int = Field(gt=0)
    target_id: int = Field(gt=0)
    amount: str


def service(request: Request):
    return request.app.state.service


@router.post("/accounts", status_code=201)
def create_account(payload: AccountInput, svc=Depends(service)):
    return svc.create_account(payload.owner, payload.initial_balance)


@router.get("/accounts/{account_id}")
def get_account(account_id: int, svc=Depends(service)):
    return svc.get_account(account_id)


@router.post("/transfers", status_code=201)
def transfer(payload: TransferInput, idempotency_key: str = Header(...), svc=Depends(service)):
    return svc.transfer(payload.source_id, payload.target_id, payload.amount, idempotency_key)


@router.get("/accounts/{account_id}/statement")
def statement(account_id: int, start: date | None = None, end: date | None = None, type: Literal["debit", "credit"] | None = None, svc=Depends(service)):
    return svc.statement(account_id, start.isoformat() if start else None, end.isoformat() if end else None, type)
