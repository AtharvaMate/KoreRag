---
doc_id: support-macros-common-issues
team: support
access_control: public
content_type: faq
updated_at: 2026-05-15
---

# Support Macros — Common Issues

## "My payment shows as failed but the customer says they were charged"

This is almost always a timing mismatch between the authorization hold and
final capture. Ask the customer to check their bank statement 24-48 hours
later — the hold typically drops off if the payment ultimately failed on our
side. If it's still showing after 48 hours, escalate to payments engineering
with the payment ID.

## "I'm getting ERR-2004 but I have funds in my account"

ERR-2004 (insufficient_funds) is returned directly by the card issuer, not
calculated by Northwind. This usually means either a temporary hold from
another transaction reduced available balance, or the card has a per-transaction
limit lower than the attempted amount. Direct the customer to their bank.

## "Webhooks stopped arriving"

First check the dashboard's Failed Events view for the customer's endpoint —
if events show as failed with a specific HTTP status, that's usually
self-explanatory (404 = wrong URL, 401/403 = auth issue on their side, 5xx =
their server error). If events show as "delivered" but the customer insists
they didn't receive them, the issue is downstream of us (their infrastructure,
firewall, or proxy) — see `runbook-webhook-delivery-failures.md` for the
long-tail proxy-header-stripping cause.

## "Can you give me a refund outside the policy window?"

Support agents cannot override the refund policy unilaterally. Escalate
exception requests to a team lead, who can approve case-by-case exceptions up
to $500; anything above that requires billing-team sign-off.
