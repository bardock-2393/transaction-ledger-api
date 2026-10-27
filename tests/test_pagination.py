def _add(client, account_id, type_, amount, ref):
    return client.post(
        f"/accounts/{account_id}/transactions",
        json={"type": type_, "amount": amount, "reference_id": ref},
    )


def test_history_filter_by_type(client, account):
    _add(client, account["id"], "credit", "10.00", "c1")
    _add(client, account["id"], "credit", "10.00", "c2")
    _add(client, account["id"], "debit", "5.00", "d1")

    credits = client.get(f"/accounts/{account['id']}/transactions?type=credit").json()
    assert credits["pagination"]["total_records"] == 2
    assert all(t["type"] == "credit" for t in credits["data"])

    debits = client.get(f"/accounts/{account['id']}/transactions?type=debit").json()
    assert debits["pagination"]["total_records"] == 1

    both = client.get(f"/accounts/{account['id']}/transactions").json()
    assert both["pagination"]["total_records"] == 3


def test_history_pagination_shape(client, account):
    for i in range(5):
        _add(client, account["id"], "credit", "1.00", f"r{i}")

    page1 = client.get(f"/accounts/{account['id']}/transactions?page=1&limit=2").json()
    assert page1["pagination"] == {"page": 1, "limit": 2, "total_records": 5, "total_pages": 3}
    assert len(page1["data"]) == 2

    page3 = client.get(f"/accounts/{account['id']}/transactions?page=3&limit=2").json()
    assert len(page3["data"]) == 1


def test_history_sort_is_latest_first_with_id_tiebreak(client, account, session_factory):
    import datetime

    from app.models import Transaction

    db = session_factory()
    try:
        same_time = datetime.datetime.now(datetime.timezone.utc)
        for i in range(3):
            db.add(
                Transaction(
                    account_id=account["id"],
                    type="credit",
                    amount_cents=100,
                    description=None,
                    reference_id=f"tie-{i}",
                    created_at=same_time,
                )
            )
        db.commit()
    finally:
        db.close()

    resp = client.get(f"/accounts/{account['id']}/transactions").json()
    ids = [t["id"] for t in resp["data"]]
    assert ids == sorted(ids, reverse=True)


def test_invalid_pagination_params_422(client, account):
    assert client.get(f"/accounts/{account['id']}/transactions?page=0").status_code == 422
    assert client.get(f"/accounts/{account['id']}/transactions?limit=0").status_code == 422
    assert client.get(f"/accounts/{account['id']}/transactions?limit=1000").status_code == 422
