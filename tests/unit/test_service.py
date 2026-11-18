from unittest.mock import Mock
import pytest
from fastapi import HTTPException
from src.services.wallet import WalletService
from src.repositories.sqlite_repo import WalletRepository


@pytest.fixture
def service():
    repo = WalletRepository(":memory:")
    svc = WalletService(repo, Mock(is_valid=Mock(return_value=True)), Mock())
    yield svc
    repo.close()


def test_success_and_idempotency(service):
    a = service.create_account("Ana", "100.00")
    b = service.create_account("Bia", "0")
    first = service.transfer(a["id"], b["id"], "30.00", "key-1")
    second = service.transfer(a["id"], b["id"], "30.00", "key-1")
    assert first["replayed"] is False
    assert second["replayed"] is True
    assert service.get_account(a["id"])["balance"] == "70.00"
    assert service.get_account(b["id"])["balance"] == "30.00"
    service.gateway.notify.assert_called_once_with(first)


def test_insufficient_funds(service):
    a = service.create_account("Ana", "2")
    b = service.create_account("Bia", "0")
    with pytest.raises(HTTPException) as error:
        service.transfer(a["id"], b["id"], "3", "key-2")
    assert error.value.status_code == 409
    assert service.get_account(a["id"])["balance"] == "2.00"


def test_conflicting_key(service):
    a = service.create_account("Ana", "10")
    b = service.create_account("Bia", "0")
    service.transfer(a["id"], b["id"], "1", "key-3")
    with pytest.raises(HTTPException) as error:
        service.transfer(a["id"], b["id"], "2", "key-3")
    assert error.value.status_code == 409


def test_same_account_and_missing_account(service):
    a = service.create_account("Ana", "10")
    with pytest.raises(HTTPException) as error:
        service.transfer(a["id"], a["id"], "1", "same")
    assert error.value.status_code == 422
    with pytest.raises(HTTPException) as error:
        service.transfer(a["id"], 9999, "1", "missing")
    assert error.value.status_code == 404


def test_invalid_registry_and_account(service):
    service.registry.is_valid.return_value = False
    with pytest.raises(HTTPException):
        service.create_account("A", "1")
    with pytest.raises(HTTPException):
        service.get_account(999)


def test_statement_filters(service):
    a = service.create_account("Ana", "10")
    b = service.create_account("Bia", "0")
    service.transfer(a["id"], b["id"], "2", "k-filter")
    assert len(service.statement(a["id"], None, None, "debit")) == 1
    assert len(service.statement(a["id"], None, None, "credit")) == 1
    assert service.statement(a["id"], "2099-01-01", None, None) == []
    assert service.statement(a["id"], None, "2000-01-01", None) == []


def test_gateway_exception_does_not_revert_committed_transaction(service):
    a = service.create_account("Ana", "10")
    b = service.create_account("Bia", "0")
    service.gateway.notify.side_effect = RuntimeError("unavailable")
    service.transfer(a["id"], b["id"], "1", "gateway-down")
    assert service.get_account(b["id"])["balance"] == "1.00"


def test_idempotency_key_length(service):
    a = service.create_account("Ana", "10")
    b = service.create_account("Bia", "0")
    with pytest.raises(HTTPException) as error:
        service.transfer(a["id"], b["id"], "1", "x" * 256)
    assert error.value.status_code == 422


def test_invalid_statement_date_range(service):
    a = service.create_account("Ana", "10")
    with pytest.raises(HTTPException) as error:
        service.statement(a["id"], "2026-12-31", "2026-01-01", None)
    assert error.value.status_code == 422
