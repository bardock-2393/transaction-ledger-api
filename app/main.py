from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.database import Base, engine
from app.errors import AppError, app_error_handler, validation_error_handler
from app.routers import accounts, transfers

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Transaction Ledger API",
    description="A simple ledger API for accounts, transactions, and transfers.",
)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)

app.include_router(accounts.router)
app.include_router(transfers.router)
