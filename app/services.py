from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import AccountNotFound, InsufficientBalance
from app.models import Account, Transaction


@dataclass
class TransactionResult:
    transaction: Transaction
    is_duplicate: bool


def get_account_or_404(db: Session, account_id: int) -> Account:
    account = db.get(Account, account_id)
    if account is None:
        raise AccountNotFound(f"Account {account_id} not found")
    return account


def create_transaction(
    db: Session,
    account_id: int,
    type: str,
    amount_cents: int,
    description: str | None,
    reference_id: str,
    transfer_id: str | None = None,
    *,
    commit: bool = True,
) -> TransactionResult:
    account = get_account_or_404(db, account_id)

    if type == "debit" and account.balance_cents < amount_cents:
        raise InsufficientBalance(
            f"Account {account_id} has insufficient balance for this debit",
            details={"balance_cents": account.balance_cents, "requested_cents": amount_cents},
        )

    txn = Transaction(
        account_id=account_id,
        type=type,
        amount_cents=amount_cents,
        description=description,
        reference_id=reference_id,
        transfer_id=transfer_id,
    )
    db.add(txn)
    account.balance_cents += amount_cents if type == "credit" else -amount_cents

    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        existing = db.execute(
            select(Transaction).where(
                Transaction.account_id == account_id,
                Transaction.reference_id == reference_id,
            )
        ).scalar_one()
        return TransactionResult(existing, is_duplicate=True)

    if commit:
        db.commit()
    return TransactionResult(txn, is_duplicate=False)


def get_balance(db: Session, account_id: int) -> Account:
    return get_account_or_404(db, account_id)


def list_transactions(
    db: Session,
    account_id: int,
    type: str | None,
    page: int,
    limit: int,
) -> tuple[list[Transaction], int]:
    get_account_or_404(db, account_id)

    filters = [Transaction.account_id == account_id]
    if type is not None:
        filters.append(Transaction.type == type)

    total_records = db.execute(
        select(func.count()).select_from(Transaction).where(*filters)
    ).scalar_one()

    items = (
        db.execute(
            select(Transaction)
            .where(*filters)
            .order_by(Transaction.created_at.desc(), Transaction.id.desc())
            .limit(limit)
            .offset((page - 1) * limit)
        )
        .scalars()
        .all()
    )
    return list(items), total_records


def transfer(
    db: Session,
    from_account_id: int,
    to_account_id: int,
    amount_cents: int,
    description: str | None,
) -> tuple[Transaction, Transaction, str]:
    transfer_id = str(uuid4())

    debit_result = create_transaction(
        db,
        from_account_id,
        "debit",
        amount_cents,
        description or f"Transfer to account {to_account_id}",
        reference_id=f"transfer:{transfer_id}:debit",
        transfer_id=transfer_id,
        commit=False,
    )
    credit_result = create_transaction(
        db,
        to_account_id,
        "credit",
        amount_cents,
        description or f"Transfer from account {from_account_id}",
        reference_id=f"transfer:{transfer_id}:credit",
        transfer_id=transfer_id,
        commit=False,
    )
    db.commit()
    return debit_result.transaction, credit_result.transaction, transfer_id
