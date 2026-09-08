# daily_update

One email per moderator, once a day: everything still open in the moderation queue that they
cover. 

Not deployed yet — the terraform entry is written but commented out in `cicd/terraform/envs/*.tfvars`.

## Pipeline

```
main.py → process.send_daily_reports
    → moderators.get_digest_recipients    who wants a digest, and what they cover
    → submissions.get_open_submissions    every open submission, one pass
    → filters.report_on                   drop what the digest doesn't cover
    → shared.moderators.get_mod_emails    addresses, one query
    → per moderator: filters.get_subs_for_mod → digest_email.send_digest
                                                  → report_content.render_report
                                                  → shared.utils.email.send_email
```


## Looking at a digest locally

No queue needed — this job reads the database directly, so a digest can be rendered from the
seeded test data:

```bash
poetry run python -m scripts.preview_digest                       # every digest moderator
poetry run python -m scripts.preview_digest digest-cat@example.com
```

Writes `preview/<address>.txt` and `.html`. Nothing is sent and no real database is touched —
it copies `tests/data.sql` into a temp SQLite file, the same way the test fixture does.


Seeded moderators worth previewing: `digest-cat@example.com` (a category mod, all three
sections), `digest-archive@example.com` (a whole archive), `digest-empty@example.com` (nothing
to report).

## Retries

Each send retries transient relay failures (`SEND_ATTEMPTS` in `digest_email.py`). A run that
delivers nothing exits non-zero so Cloud Run reruns the job; a run that delivered *some* digests
always exits zero, because a rerun would send those moderators a second copy.
