import os

from fastapi import FastAPI

from src.controllers.api import router
from src.repositories.sqlite_repo import WalletRepository
from src.services.gateways import AntifraudGateway, RegistrationStub
from src.services.wallet import WalletService


def create_app(database=None, gateway=None, registry=None):
    app = FastAPI(title="Wallet API", version="1.0.0")
    repo = WalletRepository(database if database is not None else os.environ.get("DATABASE_PATH", "wallet.db"))
    app.state.repo = repo
    app.state.service = WalletService(repo, registry or RegistrationStub(), gateway or AntifraudGateway())
    app.include_router(router)
    return app


app = create_app()
