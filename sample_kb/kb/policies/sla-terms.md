---
doc_id: sla-terms
team: legal
access_control: public
content_type: policy
updated_at: 2026-03-01
---

# Service Level Agreement (SLA)

## Uptime Commitment

| Plan | Monthly uptime commitment | Service credit for breach |
|---|---|---|
| Starter | 99.5% | None |
| Growth | 99.9% | 10% of monthly fee per 0.1% below target |
| Enterprise | 99.95% | 25% of monthly fee per 0.1% below target |

## Definition of Downtime

Downtime is measured as any period during which the Payments API returns a
5xx error rate above 5% for more than 60 consecutive seconds, as recorded by
Northwind's independent uptime monitor. Scheduled maintenance windows
(announced at least 72 hours in advance) do not count toward downtime.

## Support Response Times

| Severity | Starter | Growth | Enterprise |
|---|---|---|---|
| Sev-1 (full outage) | Best effort | 1 hour | 15 minutes |
| Sev-2 (degraded) | Best effort | 4 hours | 1 hour |
| Sev-3 (minor/question) | 2 business days | 1 business day | 4 hours |

## Credit Requests

Service credits must be requested within 30 days of the incident via a
support ticket referencing the specific downtime window.
