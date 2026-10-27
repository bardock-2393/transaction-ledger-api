from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (CheckConstraint("balance_cents >= 0", name="ck_balance_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    balance_cents: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=_utcnow)

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="account")


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("account_id", "reference_id", name="uq_account_reference"),
        CheckConstraint("type IN ('credit', 'debit')", name="ck_type_valid"),
        CheckConstraint("amount_cents > 0", name="ck_amount_positive"),
        Index("ix_transactions_account_created", "account_id", "created_at", "id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    type: Mapped[str] = mapped_column(nullable=False)
    amount_cents: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
    reference_id: Mapped[str] = mapped_column(nullable=False)
    transfer_id: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=_utcnow)

    account: Mapped["Account"] = relationship(back_populates="transactions")
