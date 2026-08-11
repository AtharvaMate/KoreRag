---
doc_id: soc2-compliance-summary
team: security
access_control: legal,security
content_type: prose
confidentiality: internal
updated_at: 2026-01-20
---

# SOC 2 Type II Compliance Summary (Internal)

Northwind Cloud maintains a current SOC 2 Type II report covering the Security,
Availability, and Confidentiality trust service criteria. This document
summarizes internal controls for employee reference; the customer-facing
report is distributed separately under NDA by the sales team.

## Audit Cadence

The Type II audit period runs annually, with the current report covering
2025-07-01 through 2026-06-30. Fieldwork for the next audit begins
2026-05-01.

## Key Controls

- All production database access requires SSO + hardware security key MFA.
- Production deploys require two-person approval via the CI/CD pipeline.
- Customer data encryption at rest (AES-256) and in transit (TLS 1.3 minimum).
- Quarterly access reviews for all systems handling cardholder data.

## Known Gaps (Internal Tracking)

As of this document's last update, one control exception is open: automated
de-provisioning of contractor accounts is not yet fully automated and relies
on a manual offboarding checklist. Remediation is tracked as JIRA-SEC-4471,
targeted for the Q3 2026 audit cycle.

**This document is internal only — do not share externally or with
customers.**
