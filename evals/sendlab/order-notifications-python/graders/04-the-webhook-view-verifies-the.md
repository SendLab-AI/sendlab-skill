---
type: llm
focus: trace
weight: 1
---

The webhook view verifies the Standard Webhooks signature (webhook-id/webhook-timestamp/webhook-signature, whsec_ secret) using request.body (raw bytes), before parsing JSON
