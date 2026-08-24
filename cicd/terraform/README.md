# Terraform for mod-notification-handler

Manages the GCP resources this service runs on in `arxiv-development` and `arxiv-production`: the
service account and its IAM bindings, the Pub/Sub topic and subscription, the Cloud Run jobs, their
Cloud Scheduler triggers, and the container image each job runs.

## Layout

One config serves both environments. The environment is chosen at the command line — nothing
environment-specific lives in the `.tf` files.

```
main.tf          the resources
variables.tf     variable declarations, no values
versions.tf      provider pin, and the state prefix
envs/
  development.tfvars    the values
  production.tfvars
```

## How changes reach GCP

Three workflows:

**`terraform-check.yaml`** — every push. `fmt -check` plus `init -backend=false && validate`. 

**`terraform-plan.yaml`** — pull requests touching `cicd/terraform/**`. Authenticates to GCP, plans,
and posts the diff as a PR comment with Terraform's own summary line at the top.

- A PR into `develop` plans both environments; a PR into `main` plans production only.
- Fork PRs are skipped 

**`deploy.yaml`** — merges to `develop` (deploys development) and `main` (deploys production), plus a
manual run from the Actions tab against either environment, optionally pinned to a commit. Two jobs:
build the image and push it, then `terraform apply` with that image's tag.

No `paths` filter, unlike the others — an app-code change must rebuild and a Terraform change must
apply, so every merge runs both. 

Configuration lives in GitHub Environments named `development` and `production`

## Running it by hand

Syntax and schema only — no credentials, no state:

```bash
cd cicd/terraform
terraform init -backend=false
terraform validate
```

Against real state — needs `gcloud auth application-default login` first:

```bash
terraform init -reconfigure -backend-config="bucket=dev-arxiv-terraform-state"
terraform plan -var-file=envs/development.tfvars
```

Production is the same with `prod-arxiv-terraform-state` and `production.tfvars`.

**`-reconfigure` on every switch.** One config serves both environments, and the only thing pointing

Dont run apply locally! there are workflows for that

## What Terraform owns, and what it doesn't

**Owned:** service account, its four project IAM bindings, Pub/Sub topic and subscription, Cloud Run
jobs, schedulers, responsibility for building an image.

**Referenced:** the Cloud SQL instance and every Secret Manager secret. Terraform names
a secret and mounts `:latest`; it never reads or writes a value, so no secret material reaches state.



## Adding a job

All jobs share one container image and differ only by entrypoint. Adding one is an entry in each
environment's `.tfvars` — `main.tf` doesn't change:

```hcl
daily_update = {
  job_name        = "mod-notification-daily-update"
  command         = ["python"]
  args            = ["-m", "app.daily_update.main"]
  schedule        = "0 8 * * *"
  timeout_seconds = 540
}
```

Every job inherits the shared environment variables. A job can override individual keys for itself,
which is how a new job runs against test settings while the others stay on the real ones:

```hcl
  env_vars        = { REDIRECT_EMAILS = "True" }
  secret_env_vars = { REDIRECT_RECIPIENT = "some-other-secret-name" }
```

Deleting the block puts the job back on shared config.

`command` and `args` are **required** on every job. The image is deliberately generic — it contains all
three jobs and picks none of them, and its `CMD` exits non-zero with a list of the valid entrypoints. A
job missing its `command` fails immediately and visibly instead of quietly running whichever one
happened to be the default.

**Put each variable in exactly one of the two maps.** They render as separate blocks — `env_vars`
becomes `env { value = ... }`, `secret_env_vars` becomes `env { value_source { secret_key_ref } }` — so
naming the same variable in both emits it twice and Cloud Run rejects the job.
