from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

AMOUNT_DESCRIPTION = (
    "Decimal amount, 2 decimal places. Send as a JSON string (e.g. \"10.50\") "
    "to avoid floating-point precision loss."
)


class AccountCreate(BaseModel):
    name: str = Field(min_length=1)


class AccountRead(BaseModel):
    id: int
    name: str
    balance: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class BalanceRead(BaseModel):
    account_id: int
    balance: Decimal


class TransactionCreate(BaseModel):
    type: Literal["credit", "debit"]
    amount: Decimal = Field(gt=0, description=AMOUNT_DESCRIPTION)
    description: str | None = None
    reference_id: str = Field(min_length=1)


class TransactionRead(BaseModel):
    id: int
    account_id: int
    type: str
    amount: Decimal
    description: str | None
    reference_id: str
    transfer_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class Pagination(BaseModel):
    page: int
    limit: int
    total_records: int
    total_pages: int


class TransactionListResponse(BaseModel):
    data: list[TransactionRead]
    pagination: Pagination


class TransferCreate(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: Decimal = Field(gt=0, description=AMOUNT_DESCRIPTION)
    description: str | None = None


class TransferRead(BaseModel):
    transfer_id: str
    debit: TransactionRead
    credit: TransactionRead
