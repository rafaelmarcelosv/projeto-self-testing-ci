from unittest.mock import Mock

from fastapi.testclient import TestClient

from src.main import create_app


class FixedRegistryStub:
    def is_valid(self, owner):
        return owner in {"Ana", "Bia"}


def test_stub_and_mock_with_memory_database():
    gateway = Mock()
    app = create_app(database=":memory:", registry=FixedRegistryStub(), gateway=gateway)
    with TestClient(app) as client:
        assert client.post("/accounts", json={"owner": "Intruso", "initial_balance": "1"}).status_code == 422
        a = client.post("/accounts", json={"owner": "Ana", "initial_balance": "50"}).json()
        b = client.post("/accounts", json={"owner": "Bia", "initial_balance": "0"}).json()
        response = client.post("/transfers", headers={"Idempotency-Key": "abc"}, json={"source_id": a["id"], "target_id": b["id"], "amount": "20"})
        assert response.status_code == 201
        assert gateway.notify.call_count == 1
        gateway.notify.assert_called_once_with(response.json())
        assert client.get(f"/accounts/{b['id']}").json()["balance"] == "20.00"
    app.state.repo.close()
