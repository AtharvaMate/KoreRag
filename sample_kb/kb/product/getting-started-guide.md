---
doc_id: getting-started-guide
team: product
access_control: public
content_type: prose
updated_at: 2026-05-12
---

# Getting Started with Northwind Cloud

This guide walks a new merchant through their first integration.

## Step 1 — Create an Account

Sign up at dashboard.northwindcloud.com. You will receive a test-mode API key
immediately; live-mode keys are issued after identity verification (typically
1-2 business days).

## Step 2 — Install the SDK

```bash
pip install northwind-sdk
```

```python
from northwind import Client

client = Client(api_key="sk_test_...")
```

## Step 3 — Create Your First Charge

```python
charge = client.payments.create(
    amount=2500,          # amount in cents
    currency="usd",
    source="tok_visa",
    description="First test charge",
)
print(charge.status)  # "succeeded"
```

## Step 4 — Set Up a Webhook Endpoint

Register an HTTPS endpoint in the dashboard under Settings > Webhooks. See
`api-reference-webhooks.md` for the full event catalog and payload schema.

## Step 5 — Go Live

Once your integration passes the pre-launch checklist in the dashboard, submit
a request for live-mode API keys. Live keys are prefixed `sk_live_` and
`pk_live_`.

## Common First-Integration Mistakes

- Using a test-mode key in a production environment (charges will silently
  fail to move real money).
- Not verifying webhook signatures, which allows forged events to be accepted.
- Hardcoding API keys directly in client-side code — always keep secret keys
  server-side only.
