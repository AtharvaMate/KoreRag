---
doc_id: incident-response-policy
team: security
access_control: security,engineering
content_type: policy
confidentiality: internal
updated_at: 2026-03-05
---

# Incident Response Policy (Internal)

## Severity Definitions

| Severity | Definition | Initial response |
|---|---|---|
| SEV-1 | Full service outage or confirmed data breach | Page on-call immediately, incident commander assigned within 5 min |
| SEV-2 | Partial degradation affecting a subset of customers | Page on-call, response within 30 min |
| SEV-3 | Minor issue, no customer-visible impact | Ticket filed, addressed next business day |

## Security Incident Escalation

Any suspected unauthorized access to production systems or customer data must
be escalated to the security team immediately via the #security-incidents
channel and treated as a SEV-1 regardless of apparent scope, until scoping is
complete.

## Post-Incident Process

Every SEV-1 and SEV-2 incident requires a written postmortem within 5 business
days, following the template in `postmortem-2026-03-14-checkout-outage.md`.
Postmortems are blameless and reviewed in the weekly engineering sync.

## Customer Notification

Data breaches affecting customer PII must be reported to affected customers
within 72 hours per GDPR requirements, coordinated jointly by security and
legal. See `gdpr-data-processing.md` for the regulatory notification
obligations.

**This document is internal only.**
