def _add_transaction(client, account_id, **overrides):
    payload = {
        "type": "credit",
        "amount": "50.00",
        "description": "test",
        "reference_id": "ref-1",
    }
    payload.update(overrides)
    return client.post(f"/accounts/{account_id}/transactions", json=payload)


def test_credit_increases_balance(client, account):
    resp = _add_transaction(client, account["id"], type="credit", amount="50.00")
    assert resp.status_code == 201
    balance = client.get(f"/accounts/{account['id']}/balance").json()["balance"]
    assert balance == "50.00"


def test_debit_decreases_balance(client, account):
    _add_transaction(client, account["id"], type="credit", amount="100.00", reference_id="r1")
    resp = _add_transaction(client, account["id"], type="debit", amount="30.00", reference_id="r2")
    assert resp.status_code == 201
    balance = client.get(f"/accounts/{account['id']}/balance").json()["balance"]
    assert balance == "70.00"


def test_debit_rejected_when_insufficient_balance_and_balance_unchanged(client, account):
    resp = _add_transaction(client, account["id"], type="debit", amount="150.00", reference_id="r1")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INSUFFICIENT_BALANCE"
    balance = client.get(f"/accounts/{account['id']}/balance").json()["balance"]
    assert balance == "0.00"


def test_duplicate_reference_id_same_account_returns_409_no_new_row_no_balance_change(client, account):
    first = _add_transaction(client, account["id"], type="credit", amount="50.00", reference_id="dup")
    assert first.status_code == 201

    second = _add_transaction(client, account["id"], type="credit", amount="50.00", reference_id="dup")
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "DUPLICATE_TRANSACTION"

    balance = client.get(f"/accounts/{account['id']}/balance").json()["balance"]
    assert balance == "50.00"

    history = client.get(f"/accounts/{account['id']}/transactions").json()
    assert history["pagination"]["total_records"] == 1


def test_same_reference_id_allowed_across_different_accounts(client, account):
    other = client.post("/accounts", json={"name": "Other"}).json()
    resp1 = _add_transaction(client, account["id"], reference_id="shared")
    resp2 = _add_transaction(client, other["id"], reference_id="shared")
    assert resp1.status_code == 201
    assert resp2.status_code == 201


def test_create_transaction_unknown_account_404(client):
    resp = _add_transaction(client, 9999)
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "ACCOUNT_NOT_FOUND"


def test_invalid_transaction_type_422(client, account):
    resp = _add_transaction(client, account["id"], type="withdrawal")
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_amount_must_be_positive_422(client, account):
    for bad_amount in ["0", "-5.00"]:
        resp = _add_transaction(client, account["id"], amount=bad_amount, reference_id=bad_amount)
        assert resp.status_code == 422

    resp = _add_transaction(client, account["id"], amount="not-a-number", reference_id="bad")
    assert resp.status_code == 422


def test_missing_required_fields_422(client, account):
    resp = client.post(f"/accounts/{account['id']}/transactions", json={"type": "credit", "amount": "1.00"})
    assert resp.status_code == 422


def test_no_put_patch_delete_routes_on_transactions(client, account):
    _add_transaction(client, account["id"])
    path = f"/accounts/{account['id']}/transactions"
    # The only route registered at this path accepts GET/POST; PUT/PATCH/DELETE
    # are never wired up anywhere, so transactions cannot be edited or deleted.
    assert client.put(path, json={}).status_code == 405
    assert client.patch(path, json={}).status_code == 405
    assert client.delete(path).status_code == 405
