# Every value that makes production different from development.
#
#   terraform init -backend-config=envs/production.backend.hcl -reconfigure
#   terraform plan -var-file=envs/production.tfvars

project_id = "arxiv-production"
region     = "us-central1"

# ---------------------------------------------------------------------------
# Application config
# ---------------------------------------------------------------------------

env_name = "PRODUCTION"

send_emails     = true
redirect_emails = false

# ---------------------------------------------------------------------------
# External dependencies — referenced, never created
# ---------------------------------------------------------------------------

# Deliberate escape hatch: set redirect_emails = true above to route production mail to
# this address instead of real moderators, for testing against production data. Inert
# while redirect_emails is false. Both halves live here, so turning it on is a reviewable
# diff rather than a silent console change.
redirect_recipient_secret = "test-email-group-address"

db_secret_name    = "arxiv-production-rep11-db-readonly_URI"
cloudsql_instance = "arxiv-production:us-central1:arxiv-production-rep11"

# ---------------------------------------------------------------------------
# Build trigger
# ---------------------------------------------------------------------------

# TODO dev's trigger is global and this one is us-east1. Consolidating them is a
# destroy-and-recreate, so do it as a separate change after the import converges.
build_trigger_location    = "us-east1"
build_trigger_branch      = "^main$"
build_trigger_description = "builds cloud run job that sends emails to mods"

# Only read by imports.tf. Goes away with it.
build_trigger_id = "62cf038d-dfab-483b-92eb-9e5744577517"

# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

# Every job inherits the shared config above. A job may add its own `env_vars` block to
# override individual keys, but in production that should be rare and deliberate — a
# per-job override here is a job not behaving like the rest of production.

jobs = {
  mod_actions = {
    job_name = "mod-notification-handler"
    # Twice as often as dev, deliberately — production ships moderator mail faster.
    schedule        = "*/5 * * * *"
    timeout_seconds = 300
    # No command/args: uses the image CMD, python -m app.mod_actions.main.
  }

  # Not yet provisioned. Only add these here once the job has proven itself in dev.
  #
  # daily_update = {
  #   job_name        = "mod-notification-daily-update"
  #   command         = ["python"]
  #   args            = ["-m", "app.daily_update.main"]
  #   schedule        = "0 8 * * *"
  #   timeout_seconds = 300
  # }
  #
  # new_subs = {
  #   job_name        = "mod-notification-new-subs"
  #   command         = ["python"]
  #   args            = ["-m", "app.new_subs.main"]
  #   schedule        = "*/5 * * * *"
  #   timeout_seconds = 300
  # }
}
