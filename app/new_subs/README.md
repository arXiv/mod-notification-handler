# new_subs

Emails moderators about new submissions. One Pub/Sub message per submission, one email per
submission.

**Scaffold, not finished.** The flow and the ack contract are real; the inclusion checks, the
recipient rules and the email itself are placeholders.

## Push, not pull

**This job is a Cloud Run service, not a Cloud Run job.** A message is delivered as each
submission arrives, instead of a scheduler waking a job that pulls a batch.

The image is still the shared one — this is a normal Cloud Run service, not
a buildpack-deployed Cloud Run function, so `mysqlclient` keeps the Dockerfile's build deps.

The message carries the whole `arXiv_submissions` row and its categories, so this job never reads
the submission back from the database. `main.NewSubParams.to_submission` turns it into a
`SubmissionBase`, and everything downstream works on that.

```
submit_info → Pub/Sub topic → Eventarc trigger → main.handle_new_submission
    → NewSubParams.to_submission               the message carries the whole row
    → process.process_new_submission
        → filters.notify_about                 is this worth an email
        → moderators.get_recipients            who gets it
        → email_content.render_email → shared.utils.email.send_email
```

Returning from the handler acks; raising doesn't. Retry handled by subscription redelivery.
