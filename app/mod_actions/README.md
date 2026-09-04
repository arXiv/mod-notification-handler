# mod_actions

Emails moderators about actions taken on submissions — comments, proposals, promotions,
rejections. Triggered every few minutes, pulls pending messages off a Pub/Sub queue, groups them
by submission, and sends one email per submission so a moderator gets one coherent notification
instead of many.

## Pipeline

```
Pub/Sub → shared.pubsub.get_messages → process.process_messages
    → _convert_messages    parse and group by submission
    → _build_email_tasks   resolve recipients, drop the sole actor
    → shared.submission.get_submission_info
    → _send_email_tasks → email_content.render_email → shared.utils.email.send_email
```

## Acking

Ack semantics are the thing to be careful with:

| outcome | acked? |
|---|---|
| send succeeded | yes |
| all recipients refused | yes — terminal |
| parse failure | yes — retrying won't fix it |
| submission missing from the db | no — redelivers |
| render or send raised | no — redelivers |

## Running locally

Not currently possible — it needs a Pub/Sub queue to pull from. Tests are the only way to exercise it.
