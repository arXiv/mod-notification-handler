# mod-notification-handler
handles communicating with moderators related to moderatering submissions

running:
currently there isnt a setup for this to be run locally because it requires a pubsub queue to pull data from

testing:
tests are set up to run on most individual functions and use test data in data.sql

```
poetry install
poetry run coverage run -m pytest
```

deploying:
happens automatically on merge to major branches through GCP build triggers to a cloud run job
(currently only setup in development)
if cloud run job does not exist slightly different command (create rather than update) needs to be run for first build

additonal environment variables needed:
CLASSIC_DB_URI
HALON_CREDS
SEND_EMAILS
ARCHIVAL_EMAIL
MOD_REPLY_TO

email redirect (controls where emails are sent):
REDIRECT_EMAILS       — default True; when True, all emails go to REDIRECT_RECIPIENT instead of real moderators
REDIRECT_RECIPIENT    — required when REDIRECT_EMAILS=True
ENV                   — set to PRODUCTION to allow sending to real recipients (required when REDIRECT_EMAILS=False)

pubsub:
GCP_PROJECT_ID           — default "arxiv-development"
PUBSUB_SUBSCRIPTION_ID   — default "mod-notification-handler"
PUBSUB_BATCH_SIZE        — default 300
PUBSUB_MAX_PULL_SEC      — default 60

optional:
MAIL_FROM
LOG_LEVEL

