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

additonal environment variables needed:
CLASSIC_DB_URI
HALON_CREDS
SEND_EMAILS
ARCHIVAL_EMAIL
MOD_REPLY_TO

optional:
MAIL_FROM
ENV
LOG_LEVEL
REDIRECT_RECIPIENT

