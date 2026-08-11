---
doc_id: api-reference-payments
team: engineering
access_control: public
content_type: reference
updated_at: 2026-06-10
---

# API Reference — Payments

## Create a Payment

`POST /v2/payments`

| Field | Type | Required | Description |
|---|---|---|---|
| amount | integer | yes | Amount in the smallest currency unit (cents for USD) |
| currency | string | yes | ISO 4217 currency code, e.g. `usd`, `eur`, `gbp` |
| source | string | yes | Tokenized payment source |
| description | string | no | Free-text description shown in the dashboard |
| metadata | object | no | Arbitrary key-value pairs, max 50 keys |

## Refund a Payment

`POST /v2/payments/{payment_id}/refund`

| Field | Type | Required | Description |
|---|---|---|---|
| amount | integer | no | Partial refund amount; omit for a full refund |
| reason | string | no | One of `requested_by_customer`, `duplicate`, `fraudulent` |

Refunds typically settle back to the customer's original payment method within
5-10 business days depending on the card network.

## Retrieve a Payment

`GET /v2/payments/{payment_id}`

## Common Error Codes

| Code | Meaning |
|---|---|
| ERR-2001 | Invalid or expired payment source |
| ERR-2004 | Insufficient funds |
| ERR-2010 | Payment already refunded |
| ERR-4092 | Downstream processor timeout — see runbook-payment-service-outage.md |
| ERR-5310 | Risk engine declined the transaction |

Full error taxonomy lives in `error-code-reference.md`.
