---
doc_id: api-authentication
team: engineering
access_control: public
content_type: prose
updated_at: 2026-04-20
---

# API Authentication

Northwind Cloud APIs are authenticated using API keys passed as a Bearer token.

```
Authorization: Bearer sk_live_51Hxxxxxxxxxxxxxxxxxx
```

## Key Types

| Key prefix | Environment | Usage |
|---|---|---|
| `sk_test_` | Test mode | Server-side, safe to use with fake card numbers |
| `sk_live_` | Live mode | Server-side only, moves real money |
| `pk_test_` / `pk_live_` | Either | Publishable, safe for client-side use |

## Rotating Keys

API keys can be rotated from Settings > API Keys. Rotating a key immediately
invalidates the old one — there is no grace period, so coordinate rotations
with a deploy that updates the key in your environment simultaneously.

## Webhook Signature Verification

Every webhook request includes a `Northwind-Signature` header. Verify it using
your webhook signing secret before trusting the payload — unverified webhook
payloads must be treated as untrusted input, since the endpoint URL is not
itself a secret.

```python
from northwind import Webhook

event = Webhook.construct_event(
    payload=request.body,
    signature=request.headers["Northwind-Signature"],
    secret="whsec_...",
)
```

## Rate Limits

The default rate limit is 100 requests/second per API key on Growth and
Enterprise plans, and 25 requests/second on Starter. Exceeding the limit
returns HTTP 429 with a `Retry-After` header.
