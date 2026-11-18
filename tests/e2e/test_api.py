from concurrent.futures import ThreadPoolExecutor
from datetime import date


def test_full_http_flow(client):
    a = client.post("/accounts", json={"owner": "Maria", "initial_balance": "100"})
    b = client.post("/accounts", json={"owner": "Joao", "initial_balance": "5"})
    assert (a.status_code, b.status_code) == (201, 201)
    a_id, b_id = a.json()["id"], b.json()["id"]
    payload = {"source_id": a_id, "target_id": b_id, "amount": "20.50"}
    response = client.post("/transfers", json=payload, headers={"Idempotency-Key": "e2e"})
    assert response.status_code == 201
    assert client.post("/transfers", json=payload, headers={"Idempotency-Key": "e2e"}).json()["replayed"]
    assert client.get(f"/accounts/{a_id}").json()["balance"] == "79.50"
    assert client.get(f"/accounts/{b_id}").json()["balance"] == "25.50"
    entries = client.get(f"/accounts/{a_id}/statement", params={"type": "debit", "start": date.today().isoformat(), "end": date.today().isoformat()})
    assert entries.status_code == 200
    assert len(entries.json()) == 1
    assert entries.json()[0]["amount"] == "20.50"


def test_http_validation(client):
    assert client.get("/accounts/999").status_code == 404
    assert client.post("/accounts", json={"owner": "X", "initial_balance": "0"}).status_code == 422
    assert client.post("/transfers", json={"source_id": 1, "target_id": 2, "amount": "1"}).status_code == 422
    assert client.get("/accounts/999/statement?type=other").status_code == 422


def test_50_concurrent_http_requests_do_not_overdraw(client):
    a = client.post("/accounts", json={"owner": "Maria", "initial_balance": "25"}).json()
    b = client.post("/accounts", json={"owner": "Joao", "initial_balance": "0"}).json()
    def send(i):
        return client.post("/transfers", json={"source_id": a["id"], "target_id": b["id"], "amount": "1"}, headers={"Idempotency-Key": f"parallel-{i}"}).status_code
    with ThreadPoolExecutor(max_workers=50) as pool:
        statuses = list(pool.map(send, range(50)))
    assert statuses.count(201) == 25
    assert statuses.count(409) == 25
    assert client.get(f"/accounts/{a['id']}").json()["balance"] == "0.00"
    assert client.get(f"/accounts/{b['id']}").json()["balance"] == "25.00"
