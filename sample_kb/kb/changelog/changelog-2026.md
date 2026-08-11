---
doc_id: changelog-2026
team: product
access_control: public
content_type: changelog
updated_at: 2026-06-20
---

# Changelog — 2026

## 2026-06-15
- Added `ADDON-REGION-005` (Multi-Region Failover) to the Enterprise add-ons
  catalog.
- Reduced default webhook retry backoff for the first retry from 5 minutes to
  1 minute based on customer feedback.

## 2026-05-01
- Refund processing time improved from 10 business days to 5-7 business days
  following a payment-processor upgrade.
- New error code `ERR-5311` (risk_manual_review) introduced, distinct from
  `ERR-5310` (risk_declined), to distinguish declines from manual-review holds.

## 2026-03-22
- Circuit-breaker trip threshold for payment processor timeouts reduced from
  15% to 8% error rate, following the 2026-03-14 checkout incident.

## 2026-01-01
- Refund Policy v2 takes effect, replacing v1. Key changes: extended refund
  window (14 to 30 days for Starter/Growth), 5% early-termination fee added
  for annual plan cancellations, faster processing time.

## 2025-11-10
- SOC 2 Type II audit period for FY2025-2026 begins.
