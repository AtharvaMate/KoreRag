---
doc_id: pii-handling-guidelines
team: security
access_control: legal,security
content_type: policy
confidentiality: internal
updated_at: 2026-01-25
---

# PII Handling Guidelines (Internal)

## Classification

| Data type | Classification |
|---|---|
| Full card number | Restricted — never stored, tokenized at the edge |
| Government ID (KYC) | Restricted |
| Name, email, billing address | Confidential |
| Support ticket free-text | Confidential (may contain incidental PII) |
| Aggregate/anonymized analytics | Internal |

## Logging Rules

Application logs must never contain full card numbers, government ID numbers,
or raw authentication tokens. Log scrubbing middleware redacts known PII
patterns automatically, but engineers are still responsible for not logging
raw request bodies containing customer PII.

## Access Principle

Access to Confidential and Restricted data follows least-privilege: engineers
debugging a production issue should use scoped, time-limited access grants
rather than standing access to customer data stores.

## Support Ticket Handling

Support agents should avoid asking customers to paste full card numbers into
ticket text; if a customer does so anyway, the agent must redact it manually
and flag the ticket for the data-scrubbing job.

**This document is internal only.**
