import math

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app import services
from app.database import get_db
from app.errors import DuplicateTransaction
from app.models import Account
from app.money import from_cents, to_cents
from app.schemas import (
    AccountCreate,
    AccountRead,
    BalanceRead,
    Pagination,
    TransactionCreate,
    TransactionListResponse,
    TransactionRead,
)
from app.serializers import account_to_read, transaction_to_read

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)) -> AccountRead:
    account = Account(name=payload.name)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account_to_read(account)


@router.get("/{account_id}/balance", response_model=BalanceRead)
def get_balance(account_id: int, db: Session = Depends(get_db)) -> BalanceRead:
    account = services.get_balance(db, account_id)
    return BalanceRead(account_id=account.id, balance=from_cents(account.balance_cents))


@router.post(
    "/{account_id}/transactions", response_model=TransactionRead, status_code=status.HTTP_201_CREATED
)
def create_account_transaction(
    account_id: int, payload: TransactionCreate, db: Session = Depends(get_db)
) -> TransactionRead:
    result = services.create_transaction(
        db,
        account_id,
        payload.type,
        to_cents(payload.amount),
        payload.description,
        payload.reference_id,
    )
    if result.is_duplicate:
        raise DuplicateTransaction(
            "A transaction with this reference_id already exists for this account",
            details={"transaction": transaction_to_read(result.transaction).model_dump(mode="json")},
        )
    return transaction_to_read(result.transaction)


@router.get("/{account_id}/transactions", response_model=TransactionListResponse)
def get_account_transactions(
    account_id: int,
    type: str | None = Query(default=None, pattern="^(credit|debit)$"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> TransactionListResponse:
    items, total_records = services.list_transactions(db, account_id, type, page, limit)
    total_pages = math.ceil(total_records / limit) if total_records else 0
    return TransactionListResponse(
        data=[transaction_to_read(t) for t in items],
        pagination=Pagination(
            page=page, limit=limit, total_records=total_records, total_pages=total_pages
        ),
    )
