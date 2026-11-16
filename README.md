# SendLab skill

An [Agent Skill](https://agentskills.io) that teaches coding agents to integrate the [SendLab](https://sendlab.ai)
SMS API correctly: retries that never send twice, `sent` vs `delivered`, verified and de-duplicated webhooks, test
keys and the simulator, segments and pricing, opt-out links, and migrations from other providers.

Works with Claude Code, Codex, Cursor, GitHub Copilot and any agent that reads `SKILL.md` skills.

## Install

Any agent, with the [skills CLI](https://github.com/vercel-labs/skills):

```bash
npx skills add sendlab-ai/sendlab-skill
```

Claude Code, as a plugin:

```text
/plugin marketplace add sendlab-ai/sendlab-skill
/plugin install sendlab@sendlab
```

Or copy [`skills/sendlab`](skills/sendlab) into your agent's skills folder, for example `.claude/skills/sendlab` in
your repository or `~/.claude/skills/sendlab` for every project.

## What's inside

| Skill | Covers |
|---|---|
| [`sendlab`](skills/sendlab/SKILL.md) | `POST /v1/messages`, the `reference` idempotency key, errors and retries, statuses, webhooks, test mode, cost, opt-outs, common use cases (OTP, reminders, notifications, campaigns, two-way) and links to the migration guides |

The skill calls the HTTP API directly. There's no SDK to install.

## Prerequisites

- A SendLab account with an activated sender
- An API key in `SENDLAB_API_KEY` (`sl_test_...` for development and CI, `sl_live_...` to send real messages)
- For webhooks, the endpoint's signing secret in `SENDLAB_WEBHOOK_SECRET`

## Want the agent to send messages itself?

This skill helps an agent write code. To let an agent send and check messages directly, connect SendLab's hosted
MCP server at `https://api.sendlab.ai/mcp`. See [Connect to MCP](https://sendlab.ai/docs/ai/mcp).

## Evals

[`evals/sendlab`](evals/sendlab) holds test cases (prompt, expected outcome, graders) in the layout
`claude plugin eval` reads. They're kept outside the skill folder so they aren't installed with it.

## Links

- Docs: https://sendlab.ai/docs
- API reference (OpenAPI): https://api.sendlab.ai/openapi.json
- Agent skill docs: https://sendlab.ai/docs/ai/agent-skill

## License

MIT
