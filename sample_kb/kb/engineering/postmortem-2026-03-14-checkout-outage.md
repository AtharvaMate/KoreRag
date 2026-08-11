---
doc_id: postmortem-2026-03-14-checkout-outage
team: engineering
access_control: engineering
content_type: postmortem
confidentiality: internal
updated_at: 2026-03-19
---

# Postmortem — Checkout Outage, 2026-03-14

## Summary

Between 14:02 and 14:47 UTC on 2026-03-14, approximately 22% of payment
requests failed with `ERR-4092`, caused by a latency spike at our primary
card-network processor. This was a SEV-1 incident, classified per
`incident-response-policy.md`.

## Timeline (UTC)

- 14:02 — Processor timeout rate begins climbing, alert fires.
- 14:06 — On-call engineer acknowledges, begins triage per
  `runbook-payment-service-outage.md`.
- 14:11 — Processor status page confirms a regional incident on their end.
- 14:14 — Secondary processor failover flag enabled.
- 14:19 — Error rate begins declining as traffic shifts to secondary
  processor.
- 14:47 — Primary processor incident resolved; failover flag disabled,
  traffic returns to primary.

## Root Cause

External: a regional outage at our primary payment processor. Our system
behaved as designed — the circuit breaker and failover mechanism limited
customer impact to the initial 12-minute detection-and-response window.

## Impact

Roughly 3,400 transactions failed during the detection window before failover
completed; all were retriable by the customer and no funds were lost or
double-charged.

## Action Items

1. Reduce circuit-breaker trip threshold from 15% to 8% error rate to detect
   this class of incident faster. **Owner: payments-infra. Status: shipped
   2026-03-22.**
2. Add automated failover (no manual flag flip) for processor-confirmed
   incidents. **Owner: payments-infra. Status: in progress, targeted Q3 2026.**
3. Update `runbook-payment-service-outage.md` with the faster triage path
   used here. **Status: done.**
