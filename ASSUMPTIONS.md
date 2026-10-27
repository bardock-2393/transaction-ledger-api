# Assumptions

- **No authentication/authorization.** The spec never mentions users, roles, or
  auth — every endpoint is open. Out of scope for a 3-4 hour take-home.

- **Single implicit currency, 2 decimal places.** The spec never mentions
  currency or multi-currency support, so amounts are a single unlabeled decimal
  currency. Stored as integer cents internally (`amount_cents`/`balance_cents`)
  to avoid floating-point rounding bugs; exposed over the API as decimal
  strings (e.g. `"10.50"`). Clients should send amounts as **JSON strings**,
  not bare numbers, to avoid float precision loss before the value reaches the
  server.

- **IDs are database autoincrement integers, not UUIDs.** The spec only
  requires uniqueness. Autoincrement ints are simpler and, as a side benefit,
  give a free, monotonic tie-breaker for the "latest-first" sort requirement
  when two transactions share a `created_at` timestamp
  (`ORDER BY created_at DESC, id DESC`).

- **`created_at` is UTC, ISO-8601.** No timezone was specified, so everything
  is generated and stored in UTC.

- **Duplicate `reference_id` returns HTTP 409 Conflict**, with the pre-existing
  transaction embedded in `error.details.transaction`. The spec frames this
  both as an idempotency concern ("indicate the transaction already exists")
  and, separately, as an error-handling case needing a status code. 409 was
  chosen to satisfy the latter while still giving the client the existing
  transaction to treat the call as idempotent. (A pure idempotent-replay
  design — `200 OK` with a `duplicate: true` flag — was considered and is a
  one-line change in `app/routers/accounts.py` if preferred.)

- **HTTP status code mapping** used consistently for all errors:

  | Scenario | Status | `error.code` |
  |---|---|---|
  | Account not found | 404 | `ACCOUNT_NOT_FOUND` |
  | Invalid request body / type / amount / missing fields / bad pagination params | 422 | `VALIDATION_ERROR` |
  | Debit exceeds balance | 400 | `INSUFFICIENT_BALANCE` |
  | Duplicate `(account_id, reference_id)` | 409 | `DUPLICATE_TRANSACTION` |

  Every error response has the same envelope:
  `{"error": {"code": "...", "message": "...", "details": {...}}}`.

- **Transaction immutability** is enforced simply by never exposing
  PUT/PATCH/DELETE routes for transactions — there is no code path that can
  modify or remove a transaction once created.

- **Pagination defaults**: `page` defaults to 1, `limit` defaults to 20 with a
  max of 100 (`limit > 100` or `limit < 1` or `page < 1` → 422). These bounds
  aren't in the spec; they're a reasonable default to prevent unbounded
  result sets.

- **Money-transfer bonus**: implemented as two linked transaction rows (a
  debit on the source account, a credit on the destination account) sharing a
  generated `transfer_id`, created in a single atomic database transaction via
  the same `create_transaction` primitive used by the regular transaction
  endpoint. The transfer endpoint does not take a client-supplied
  `reference_id`/idempotency key — the spec's idempotency requirement is
  scoped to the per-account `reference_id` transaction endpoint, not transfers.

- **Atomicity implementation**: SQLite's `BEGIN IMMEDIATE` is issued at the
  start of every write transaction (see `app/database.py`), taking the
  database write lock before any read happens. This serializes concurrent
  writes to the same account and is what makes the insufficient-balance check
  and the insert+balance-update race-free, rather than relying on
  check-then-act logic with no lock.
