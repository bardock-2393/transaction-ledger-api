def _fund(client, account_id, amount="100.00", ref="seed"):
    return client.post(
        f"/accounts/{account_id}/transactions",
        json={"type": "credit", "amount": amount, "reference_id": ref},
    )


def test_transfer_success_moves_balance_both_sides(client):
    a = client.post("/accounts", json={"name": "A"}).json()
    b = client.post("/accounts", json={"name": "B"}).json()
    _fund(client, a["id"], amount="100.00")
    _fund(client, b["id"], amount="50.00")

    resp = client.post(
        "/transfers",
        json={"from_account_id": a["id"], "to_account_id": b["id"], "amount": "30.00"},
    )
    assert resp.status_code == 201

    a_balance = client.get(f"/accounts/{a['id']}/balance").json()["balance"]
    b_balance = client.get(f"/accounts/{b['id']}/balance").json()["balance"]
    assert a_balance == "70.00"
    assert b_balance == "80.00"


def test_transfer_insufficient_balance_rolls_back_nothing_persisted(client):
    a = client.post("/accounts", json={"name": "A"}).json()
    b = client.post("/accounts", json={"name": "B"}).json()
    _fund(client, a["id"], amount="10.00")

    resp = client.post(
        "/transfers",
        json={"from_account_id": a["id"], "to_account_id": b["id"], "amount": "30.00"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INSUFFICIENT_BALANCE"

    assert client.get(f"/accounts/{a['id']}/balance").json()["balance"] == "10.00"
    assert client.get(f"/accounts/{b['id']}/balance").json()["balance"] == "0.00"

    b_history = client.get(f"/accounts/{b['id']}/transactions").json()
    assert b_history["pagination"]["total_records"] == 0


def test_transfer_unknown_account_404(client):
    a = client.post("/accounts", json={"name": "A"}).json()
    _fund(client, a["id"], amount="100.00")

    resp = client.post(
        "/transfers",
        json={"from_account_id": a["id"], "to_account_id": 9999, "amount": "10.00"},
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "ACCOUNT_NOT_FOUND"
    assert client.get(f"/accounts/{a['id']}/balance").json()["balance"] == "100.00"
