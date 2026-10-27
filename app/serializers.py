from app.models import Account, Transaction
from app.money import from_cents
from app.schemas import AccountRead, TransactionRead


def account_to_read(account: Account) -> AccountRead:
    return AccountRead(
        id=account.id,
        name=account.name,
        balance=from_cents(account.balance_cents),
        created_at=account.created_at,
    )


def transaction_to_read(txn: Transaction) -> TransactionRead:
    return TransactionRead(
        id=txn.id,
        account_id=txn.account_id,
        type=txn.type,
        amount=from_cents(txn.amount_cents),
        description=txn.description,
        reference_id=txn.reference_id,
        transfer_id=txn.transfer_id,
        created_at=txn.created_at,
    )
