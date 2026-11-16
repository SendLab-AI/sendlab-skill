---
type: llm
focus: trace
weight: 1
---

Retries only on timeouts/connection errors or responses with error.retryable true, honouring Retry-After on 429; non-retryable 4xx are not retried
