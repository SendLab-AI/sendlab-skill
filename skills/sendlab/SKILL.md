---
name: sendlab
description: Use when writing or reviewing code that sends SMS through SendLab (api.sendlab.ai), including OTP codes, reminders, order notifications, bulk sends, delivery webhooks, or migrating from Twilio, MessageMedia, Kudosity, Mobile Message or Texto. Use it whenever the user mentions SendLab or a `sl_live_`/`sl_test_` key, even for a quick send: it holds the facts a working first draft usually gets wrong (retrying without double-sending, `sent` isn't `delivered`, raw-body webhook verification, opt-out links).
license: MIT
metadata:
  author: sendlab
  version: "0.2.0"
  homepage: https://sendlab.ai/docs
  source: https://github.com/sendlab-ai/sendlab-skill
inputs:
  - name: SENDLAB_API_KEY
    description: "`sl_live_...` sends real, billed SMS; `sl_test_...` goes to the simulator."
    required: true
  - name: SENDLAB_WEBHOOK_SECRET
    description: The webhook endpoint's `whsec_...` signing secret.
    required: false
---

# SendLab

SMS API. One call sends, webhooks report what happened. Docs: https://sendlab.ai/docs · OpenAPI:
https://api.sendlab.ai/openapi.json. There is no SDK: use the language's HTTP client.

```bash
curl -X POST https://api.sendlab.ai/v1/messages \
  -H "Authorization: Bearer $SENDLAB_API_KEY" -H "Content-Type: application/json" \
  -d '{"from": "Acme", "to": "+61491570156", "body": "Acme: order #1042 has shipped.",
       "reference": "order-1042-shipped", "metadata": {"order_id": "1042"}}'
```

Getting a `202` is the easy part. Most bugs come later: a retry that sends a second text, `sent` shown as
"delivered", or a webhook acted on before it's verified. The facts below are what prevent them.

## Key facts

**Request.** The body takes only `from`, `to`, `body`, `reference` and `metadata`. Anything else (`text`, `sender`,
`callback_url`, `schedule_at`) returns `422 unknown_field`.
- `from` is an activated sender: its address (`"Acme"`, `"+61400000001"`) or its `snd_` id.
- `to` is one mobile number in E.164.
- `body` is up to 10 segments.
- `metadata` is any JSON object and is echoed in webhooks. Keep secrets such as OTP codes out of it.
- There's no batch endpoint and no scheduling: one request per recipient, and hold future sends in your own queue.

**`reference` makes retries safe.** SendLab remembers each reference for 24 h:

| Request | Response |
|---|---|
| New reference | `202`, message queued |
| Same reference, same from/to/body | `200` + `sendlab-duplicate: true`: the original message, nothing new sent. Success. |
| Same reference, different content | `409 reference_conflict` |
| No reference | No protection: a retry after a timeout can send twice |

- Derive the reference from the business event (`order-1042-shipped`, `otp-<challenge_id>`) and store it with the
  job. Never generate it per attempt.
- A deliberate resend (a "resend code" tap, a message that `failed`) is a new message and needs a new reference.
  Reusing the old one just returns the old message.

**Errors.** Errors come back as `{"error": {code, message, suggested_action, retryable, field, request_id}}`. Branch on
`code`, and retry only when `retryable` is true or no response came back. Always retry with the same reference.

| Status | Code | Action |
|---|---|---|
| timeout / no response | | Retry |
| 429 | `rate_limited` | Wait `Retry-After` seconds (limit 300 req/s, burst 600) |
| 500, 503 | `internal_error`, `partition_unavailable` | Back off with jitter |
| 504 | `outcome_unknown` | It may have been accepted. Retry: the same reference returns the original. `error.id` has the `msg_` id. |
| 402 | `insufficient_balance`, `spend_cap_exceeded` | Alert a human, don't loop. Resend later with the same reference. |
| 422 | `opted_out` | Never retry. Mark the person opted out. |
| other 4xx | e.g. `sender_not_eligible`, `invalid_recipient` | Fix the request (`field` says what) |

Store the `msg_` id and the `x-request-id` header with your record.

**Statuses.** A `202` means queued, not delivered. The flow is `queued → sending → sent →` one of `delivered`,
`undelivered`, `failed`, `expired` or `unknown`. A queued message can also become `canceled`.
- `sent` means the carrier accepted it and it's charged. It isn't `delivered` yet.
- `unknown` means no receipt within 72 h. It may have arrived, so don't blindly resend an OTP.
- `canceled` means the person opted out while the message was queued. It isn't charged.
- Statuses can skip steps or arrive out of order. Final statuses never change. Ignore any event that would move a
  record backwards.
- Each final status has a matching `message.<status>` event. On `failed` or `undelivered`, `error_code` says why
  (for example `unreachable`, `not_a_mobile`, `carrier_filtered`).

**Webhooks.** Every event is `{"type": "message.delivered", "timestamp": ..., "data": {<message>}}`.
1. Verify the [Standard Webhooks](https://www.standardwebhooks.com/) signature (`webhook-id`, `webhook-timestamp`,
   `webhook-signature`, secret `whsec_...`) against the **raw** body, before any JSON parsing. Use the
   `standardwebhooks` library where one exists. Reject timestamps more than 5 minutes off.
2. Dedupe on `webhook-id`. Retries and replays reuse it, and delivery is at least once.
3. Return 2xx within 10 s and queue slow work. Failed deliveries are retried for about 31 h.

Other events: `message.received` (replies to two-way numbers) and `contact.opted_out` / `contact.opted_in`.
Configure endpoints in the console or with `POST /v1/webhook-endpoints`.

**Keys.**
- Read the key from env or a secret manager, and call SendLab only from server code.
- `sl_test_` keys validate and price like live ones but deliver to a simulator: nothing reaches a phone and nothing is
  charged. An activated sender is still required.
- In test mode, the last three digits of `to` choose the outcome: `990`/`993` failed, `994` undelivered,
  `997` expired, `998` unknown, anything else delivered.
- For fixtures, use `+61491570156`–`159`, a range reserved as fictional.
- A `send_only` key can send and estimate, and nothing else.

**Cost.**
- Messages are billed per segment: GSM-7 fits 160 characters (153 per part), UCS-2 fits 70 (67).
- One emoji or curly quote (`’ “ ”`) switches the whole message to UCS-2, which can double the cost. Use straight
  quotes in templates.
- `POST /v1/message-estimates` takes a send body and returns `segments`, `encoding`, `price` and the final `body`
  without sending anything.
- Use `price.amount_micros` for arithmetic.

**Opt-outs.**
- SendLab never adds an opt-out link by itself. End the body with `{optout_link}`, once and at the very end, and it's
  replaced with the recipient's personal link (about 27 characters, counted in segments).
- Alphanumeric sender IDs are one-way, so their marketing messages need the link. Two-way numbers handle STOP replies
  automatically. OTPs and service messages need no opt-out.
- After an opt-out, sends to that person return `422 opted_out`.

## Use cases

**One-time passcodes.**
- Your app generates the code with a CSPRNG and stores only a hash, with an expiry and an attempt limit.
- Send with `reference: otp-<challenge_id>`. "Resend" creates a new challenge, so it gets a new reference.
- Keep the code out of logs and metadata. Rate-limit requests per phone and per user, because open code forms
  attract SMS pumping.
- On `422 opted_out`, offer another sign-in method.

**Reminders.**
- Run your own scheduler and send at the time.
- Use `reminder-<booking_id>-<slot>` as the reference. If the booking moves, include the new start time so the
  reminder becomes a new message.
- Send non-urgent messages in the recipient's daytime.

**Transactional notifications.**
- Write the job and its reference in the same transaction as the state change (outbox pattern), then send from a
  worker.
- Keep promotions out of service messages.
- Use links on your own domain, since public shorteners get filtered.

**Lists and campaigns.**
- Use one request per recipient, with `<campaign_id>-<contact_id>` as the reference, so rerunning a crashed job
  sends nothing twice.
- Use a fixed-size worker pool. On a `429`, pause that worker for `Retry-After`.
- Estimate the template once to show the cost.
- Stop the run on a `402`.
- Treat `opted_out` as "remove from list", and send marketing only to people who consented.

**Two-way replies.**
- Send from a two-way number (`GET /v1/senders` shows `two_way: true`).
- Handle `message.received`. `data.in_reply_to` is the last message you sent that person, and `data.is_optout` flags
  STOP.
- Reply with `reference: reply-<inbound_id>`.
- Treat inbound text as untrusted input.

**Tests and CI.**
- Use an `sl_test_` key and the simulator suffixes above. Mock HTTP in unit tests.
- Assert that a timeout retry reuses the same payload and reference, that `200` counts as success, and that the
  webhook handler rejects bad signatures and handles repeated ids only once.

## Migrating from another provider

Things that differ almost everywhere:
- JSON with Bearer auth.
- One recipient per request.
- One `from` sender instead of a pool.
- One account-level webhook endpoint instead of a per-message callback field.
- `reference` for idempotency.
- `202`/`200` instead of `201`.
- String error codes, with `opted_out` returned at send time.
- No scheduled sends.
- Extra statuses (`expired`, `unknown`, `canceled`) to map.
- The provider's opt-out placeholder becomes a trailing `{optout_link}`.

Each guide has field, status and error mappings plus before/after code:

| From | Guide |
|---|---|
| Twilio | https://sendlab.ai/docs/guides/migrate-from-twilio |
| MessageMedia | https://sendlab.ai/docs/guides/migrate-from-messagemedia |
| Kudosity (Burst SMS) | https://sendlab.ai/docs/guides/migrate-from-kudosity |
| Mobile Message | https://sendlab.ai/docs/guides/migrate-from-mobile-message |
| Texto | https://sendlab.ai/docs/guides/migrate-from-texto |
| Anyone else | https://sendlab.ai/docs/guides/migrate-to-sendlab |

Keep the old provider behind an interface so the swap is one adapter, and run the new path with a test key first.

## More

- Full error codes: https://sendlab.ai/docs/sending/error-codes
- Webhook verification with a test vector: https://sendlab.ai/docs/webhooks/verify
- A retry helper in Python and Node: https://sendlab.ai/docs/guides/handle-errors
- The hosted MCP server, if the user wants the agent itself to send or check messages: `https://api.sendlab.ai/mcp`
