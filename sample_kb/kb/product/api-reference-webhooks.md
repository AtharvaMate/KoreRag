---
doc_id: api-reference-webhooks
team: engineering
access_control: public
content_type: reference
updated_at: 2026-05-30
---

# API Reference — Webhooks

## Event Catalog

| Event type | Fired when |
|---|---|
| `payment.succeeded` | A payment completes successfully |
| `payment.failed` | A payment attempt fails |
| `payment.refunded` | A refund is issued, full or partial |
| `subscription.created` | A new subscription is created |
| `subscription.canceled` | A subscription is canceled |
| `invoice.payment_failed` | A recurring invoice charge fails |

## Delivery Guarantees

Webhook delivery is at-least-once, not exactly-once. Your endpoint must be
idempotent — use the `event.id` field to deduplicate events you've already
processed.

## Retry Schedule

If your endpoint does not return a 2xx response, Northwind retries delivery
with exponential backoff: 1 min, 5 min, 30 min, 2 hr, 6 hr, then once daily for
up to 3 days, after which the event is marked as failed and appears in the
dashboard's Failed Events view.

## Payload Example

```json
{
  "id": "evt_1Hxxxxxxxxxxxxxx",
  "type": "payment.succeeded",
  "created": 1750000000,
  "data": {
    "object": {
      "id": "pay_1Hxxxxxxxxxxxxxx",
      "amount": 2500,
      "currency": "usd"
    }
  }
}
```

See `runbook-webhook-delivery-failures.md` for troubleshooting delivery
issues.
