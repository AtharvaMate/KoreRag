---
doc_id: support-ticket-transcript-002
team: support
access_control: public
content_type: ticket_transcript
updated_at: 2026-06-18
---

# Support Ticket #51087

**Customer:** We're on the Enterprise plan and our webhook endpoint hasn't
received any events in about 6 hours. This is urgent, we're a payments
company and this is affecting our reconciliation.

**Agent:** Escalating this immediately given Enterprise Sev-1 response time.
Can you share your endpoint URL and roughly when the last successful delivery
was?

**Customer:** https://api.ourcompany.com/webhooks/northwind — last successful
one was around 08:15 UTC.

**Agent:** Checking our delivery logs now... I see repeated delivery attempts
to that URL since 08:20 UTC, all failing with a TLS handshake error. Does that
line up with anything on your end — cert rotation, load balancer change?

**Customer:** Oh — yes, we rotated our TLS cert this morning at 8am UTC.
Let me check if the new cert chain is complete.

**Agent:** That would do it. Once that's fixed, let me know and I'll trigger a
manual redelivery of everything queued since 08:15 so you don't lose any
events — they're not dropped, just queued for retry per our standard
schedule.

**Customer:** Fixed the cert chain, should be good now.

**Agent:** Confirmed — new deliveries are succeeding. Manually redelivered the
14 queued events from the gap window, all confirmed 200 OK on your end now.

**Resolution:** Customer-side TLS certificate chain issue after cert
rotation. All queued events manually redelivered successfully. Ticket closed.
