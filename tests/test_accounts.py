def test_create_account_balance_defaults_to_zero_and_client_cannot_set_it(client):
    resp = client.post("/accounts", json={"name": "Bob", "balance": "999.00"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["balance"] == "0.00"
    assert body["name"] == "Bob"
    assert "id" in body
    assert "created_at" in body


def test_create_account_requires_name(client):
    resp = client.post("/accounts", json={})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_get_balance_unknown_account_404(client):
    resp = client.get("/accounts/9999/balance")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "ACCOUNT_NOT_FOUND"


def test_get_balance(client, account):
    resp = client.get(f"/accounts/{account['id']}/balance")
    assert resp.status_code == 200
    assert resp.json() == {"account_id": account["id"], "balance": "0.00"}
