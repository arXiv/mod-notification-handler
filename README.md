# mod-notification-handler
handles communicating with moderators related to moderatering submissions

jobs:
three cloud run jobs live in this repo and share one container image. each has its own entrypoint
under `app/<job>/main.py`

| job | trigger | what it does | state |
|-----|---------|--------------|-------|
| `mod_actions` | pubsub, every 10 min | emails moderators about actions taken on submissions | implemented |
| `new_subs` | pubsub | emails moderators about new submissions | stub |
| `daily_update` | scheduled daily, no pubsub | once-a-day digest for mods who don't want per-action email | stub |

layout:
```
app/
  shared/       code every job uses: config, pubsub, moderators, submission, schema, utils/
  mod_actions/  the implemented job
  new_subs/     stub
  daily_update/ stub
```
anything specific to one job's payload shape, templates, or email-preference rules goes in that
job's package. `shared/` is only for what all three genuinely use.

running:
currently there isnt a setup for this to be run locally because it requires a pubsub queue to pull data from

testing:
tests are set up to run on most individual functions and use test data in data.sql.
`tests/` mirrors `app/` — `tests/shared/` and `tests/mod_actions/`

```
poetry install
poetry run coverage run -m pytest
```

deploying:
happens automatically on merge — `develop` deploys development, `main` deploys production, via
`.github/workflows/automatic-deploy.yaml`. `manual-deploy.yaml` does the same on demand for a chosen
environment and commit. both call `_deploy.yaml`, which builds the image, tags it with the commit sha,
and passes that tag to terraform, which sets it on the cloud run jobs.

all the infrastructure is terraform, in `cicd/terraform` — the jobs, their schedulers, pubsub, iam,
and the env vars.
the image is generic — it contains all three jobs and picks none of them. each job sets its own
`command`/`args` in terraform

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

pubsub (one subscription per pubsub-driven job):
GCP_PROJECT_ID                      — default "arxiv-development"
PUBSUB_SUBSCRIPTION_ID_MOD_ACTIONS  — default "mod-notification-handler"
PUBSUB_SUBSCRIPTION_ID_NEW_SUBS     — not yet set up
PUBSUB_BATCH_SIZE                   — default 300
PUBSUB_MAX_PULL_SEC                 — default 60

optional:
MAIL_FROM
LOG_LEVEL
