---
doc_id: runbook-payment-service-outage
team: engineering
access_control: engineering
content_type: runbook
confidentiality: internal
updated_at: 2026-03-15
---

# Runbook — Payment Service Outage / ERR-4092

## Symptom

Elevated rate of `ERR-4092` (downstream processor timeout) returned from
`POST /v2/payments`, visible in the payments-service dashboard as a spike in
the `processor_timeout_total` metric.

## Immediate Triage

1. Check the processor status page (processor-status.example.com) for an
   ongoing incident on their end first — this is the most common root cause.
2. Check `payments-service` pod health in the `prod-payments` namespace:
   `kubectl get pods -n prod-payments`
3. Check the circuit breaker state in the payments-service Grafana dashboard —
   if the breaker has tripped open, requests are failing fast by design and
   the fix is upstream (the processor), not the service itself.

## Mitigation

If the processor confirms an incident, enable the secondary processor
failover flag: `feature_flags.payments.secondary_processor_failover = true`.
This routes new transactions through the backup processor at a slightly
higher per-transaction fee, logged for later reconciliation.

## Escalation

If ERR-4092 rate exceeds 10% of total payment volume for more than 5 minutes
and failover does not resolve it, page the payments on-call and open a SEV-1
per `incident-response-policy.md`.

## Related

- `error-code-reference.md` — full error code catalog
- `postmortem-2026-03-14-checkout-outage.md` — prior incident of this type
