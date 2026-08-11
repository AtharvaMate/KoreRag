---
doc_id: error-code-reference
team: engineering
access_control: engineering,support
content_type: reference
confidentiality: internal
updated_at: 2026-06-01
---

# Internal Error Code Reference

| Code | Name | Meaning | Customer-facing? |
|---|---|---|---|
| ERR-2001 | invalid_source | Payment source invalid or expired | Yes |
| ERR-2004 | insufficient_funds | Card/account has insufficient funds | Yes |
| ERR-2010 | already_refunded | Refund attempted on an already-refunded payment | Yes |
| ERR-3005 | rate_limited | API key exceeded its rate limit | Yes |
| ERR-4092 | processor_timeout | Downstream processor did not respond in time | Yes |
| ERR-4093 | processor_unreachable | Downstream processor connection failed entirely | Yes |
| ERR-5001 | internal_error | Unhandled internal server error | Yes (generic message only) |
| ERR-5310 | risk_declined | Risk engine declined the transaction | Yes |
| ERR-5311 | risk_manual_review | Risk engine flagged for manual review | Yes |
| ERR-9001 | internal_config_error | Internal misconfiguration, not customer-caused | No — internal only |
| ERR-9002 | internal_migration_lock | Resource locked during an internal data migration | No — internal only |

## Notes

- ERR-4092 and ERR-4093 are the two most common causes of a payments-related
  SEV-1; see `runbook-payment-service-outage.md`.
- ERR-9001 and ERR-9002 must never be shown to customers verbatim — the API
  translates these to a generic ERR-5001 message externally while logging the
  real code internally for engineering triage.
