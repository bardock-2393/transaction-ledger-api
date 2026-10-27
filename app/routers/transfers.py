from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import services
from app.database import get_db
from app.money import to_cents
from app.schemas import TransferCreate, TransferRead
from app.serializers import transaction_to_read

router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.post("", response_model=TransferRead, status_code=status.HTTP_201_CREATED)
def create_transfer(payload: TransferCreate, db: Session = Depends(get_db)) -> TransferRead:
    debit_txn, credit_txn, transfer_id = services.transfer(
        db,
        payload.from_account_id,
        payload.to_account_id,
        to_cents(payload.amount),
        payload.description,
    )
    return TransferRead(
        transfer_id=transfer_id,
        debit=transaction_to_read(debit_txn),
        credit=transaction_to_read(credit_txn),
    )
