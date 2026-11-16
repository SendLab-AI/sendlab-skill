---
tags: [skill-creator]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

I need a Django app piece for SendLab SMS: when an order ships, text the customer (Order.customer_phone, Order.id), and record the delivery status as it comes back via webhooks. Our celery workers sometimes retry tasks and we've been burned by double-sends with our old provider. Write the celery task, the webhook view, and the model fields we need. Sender is our number +61400000001.
