# mod-notification-handler
handles communicating with moderators related to moderatering submissions

jobs:
three cloud run jobs live in this repo and share one container image. each has its own entrypoint
under `app/<job>/main.py`, and its own README

| job | trigger | what it does | state |
|-----|---------|--------------|-------|
| [`mod_actions`](app/mod_actions/README.md) | pubsub, every 10 min | emails moderators about actions taken on submissions | implemented |
| [`new_subs`](app/new_subs/README.md) | pubsub | emails moderators about new submissions | stub |
| [`daily_update`](app/daily_update/README.md) | scheduled daily, no pubsub | once-a-day digest of open submissions | implemented, not deployed |

layout:
```
app/
  shared/       code every job uses: config, pubsub, moderators, submission, templates, utils/
  mod_actions/  the implemented job
  new_subs/     stub
  daily_update/ the digest job
scripts/        local tooling, not shipped in the image
```
anything specific to one job's payload shape, templates, or email-preference rules goes in that
job's package. `shared/` is only for what all three genuinely use.

testing:
tests are set up to run on most individual functions and use test data in data.sql.
`tests/` mirrors `app/` — `tests/shared/`, `tests/mod_actions/`, `tests/daily_update/`

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

Variable meanings:

email redirect (controls where emails are sent):
REDIRECT_EMAILS       — default True; when True, all emails go to REDIRECT_RECIPIENT instead of real moderators
REDIRECT_RECIPIENT    — required when REDIRECT_EMAILS=True
ENV                   — set to PRODUCTION to allow sending to real recipients (required when REDIRECT_EMAILS=False)
