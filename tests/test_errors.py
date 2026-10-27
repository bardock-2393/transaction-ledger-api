def test_error_envelope_shape_is_consistent(client):
    resp = client.get("/accounts/9999/balance")
    body = resp.json()
    assert set(body.keys()) == {"error"}
    assert set(body["error"].keys()) == {"code", "message", "details"}


def test_invalid_request_body_type_mismatch_422(client, account):
    resp = client.post(
        f"/accounts/{account['id']}/transactions",
        json={"type": "credit", "amount": "oops", "reference_id": "r1"},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_duplicate_transaction_error_includes_existing_transaction(client, account):
    client.post(
        f"/accounts/{account['id']}/transactions",
        json={"type": "credit", "amount": "10.00", "reference_id": "dup"},
    )
    resp = client.post(
        f"/accounts/{account['id']}/transactions",
        json={"type": "credit", "amount": "10.00", "reference_id": "dup"},
    )
    assert resp.status_code == 409
    details = resp.json()["error"]["details"]
    assert details["transaction"]["reference_id"] == "dup"
