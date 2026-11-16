---
tags: [skill-creator]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

We're adding SMS login codes to our Express + TypeScript app using SendLab. Write the module that creates a 6-digit code, texts it via SendLab and verifies it, plus a "resend code" endpoint. Postgres is available through a `db` helper with query(sql, params). Our sender ID in SendLab is "Acme". Put it in src/auth/sms-otp.ts and add a short README note on config and how we should test it.
