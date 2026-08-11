---
doc_id: runbook-webhook-delivery-failures
team: engineering
access_control: engineering
content_type: runbook
confidentiality: internal
updated_at: 2026-02-28
---

# Runbook — Webhook Delivery Failures

## Symptom

Customer reports missing webhook events, or the internal
`webhook_delivery_failed_total` metric is elevated.

## Triage Steps

1. Query the webhook delivery log for the affected `endpoint_id`:
   ```
   SELECT * FROM webhook_deliveries
   WHERE endpoint_id = '<id>' AND status != 'delivered'
   ORDER BY created_at DESC LIMIT 50;
   ```
2. Check the HTTP response code the customer's endpoint returned. Common
   causes:
   - Non-2xx response (endpoint bug on customer side — not actionable by us
     beyond notifying the customer)
   - TLS handshake failure (expired certificate on customer endpoint)
   - Connection timeout (customer endpoint under load or firewalled)
3. Confirm the event was actually queued for delivery on our side by checking
   the `event.id` in the events table — if it's missing entirely, this is a
   producer-side bug, not a delivery bug, and should be escalated differently.

## Manual Redelivery

Support agents can trigger manual redelivery of a specific event from the
dashboard's Failed Events view. This does not count against the automatic
retry schedule described in `api-reference-webhooks.md`.

## Known Long-Tail Cause

Endpoints hosted behind aggressive corporate proxies that strip the
`Northwind-Signature` header before it reaches the customer's application are
a recurring long-tail cause — direct the customer to check proxy header
allowlists before assuming a bug on our side.
