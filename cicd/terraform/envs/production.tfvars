# Every value that makes production different from development.
#
#   terraform init -reconfigure -backend-config="bucket=prod-arxiv-terraform-state"
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
# Jobs
# ---------------------------------------------------------------------------
#
# `image` is not set here — CI passes it with -var on every apply.

# Every job inherits the shared config above. A job may add its own `env_vars` block to
# override individual keys, but in production that should be rare and deliberate — a
# per-job override here is a job not behaving like the rest of production.

jobs = {
  mod_actions = {
    job_name = "mod-notification-handler"
    command  = ["python"]
    args     = ["-m", "app.mod_actions.main"]
    # Twice as often as dev, deliberately — production ships moderator mail faster.
    schedule        = "*/5 * * * *"
    timeout_seconds = 300
    max_retries     = 0
  }

  daily_update = {
    job_name        = "mod-daily-digest"
    command         = ["python"]
    args            = ["-m", "app.daily_update.main"]
    schedule        = "20 14 * * 1-5"    #weekdays, 20 min after the daily freeze
    time_zone       = "America/New_York" #needs to follow daylight savings
    timeout_seconds = 1200
    max_retries     = 5 # this job exits non-zero only when nothing was delivered

    # Production data, test address. Remove this line to go live to real moderators.
    env_vars = { REDIRECT_EMAILS = "True" }
  }

  # Not yet provisioned. Only add these here once the job has proven itself in dev.
  #
  # new_subs = {
  #   job_name        = "mod-notification-new-subs"
  #   command         = ["python"]
  #   args            = ["-m", "app.new_subs.main"]
  #   schedule        = "*/5 * * * *"
  #   timeout_seconds = 300
  # }
}
