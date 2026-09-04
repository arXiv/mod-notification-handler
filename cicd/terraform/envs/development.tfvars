# Every value that makes development different from production.
#
#   terraform init -reconfigure -backend-config="bucket=dev-arxiv-terraform-state"
#   terraform plan -var-file=envs/development.tfvars

project_id = "arxiv-development"
region     = "us-central1"

# ---------------------------------------------------------------------------
# Application config
# ---------------------------------------------------------------------------

env_name = "DEVELOP"

send_emails     = true
redirect_emails = true

# ---------------------------------------------------------------------------
# External dependencies — referenced, never created
# ---------------------------------------------------------------------------

# Secret holding the address every email goes to instead of the real moderators.
redirect_recipient_secret = "test-email-group-address"

db_secret_name    = "modapi-dev-db-uri-for-cloudrun"
cloudsql_instance = "arxiv-development:us-east4:arxiv-db-dev"

# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------
#
# `image` is not set here — CI passes it with -var on every apply.

# Every job inherits the shared config above — database, mail server, reply-to. An
# `env_vars` block on a job overrides individual keys for that job only, which is how a
# new job runs against test settings while the others stay on the real ones.

jobs = {
  mod_actions = {
    job_name        = "mod-notification-handler"
    command         = ["python"]
    args            = ["-m", "app.mod_actions.main"]
    schedule        = "*/10 * * * *"
    timeout_seconds = 540
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
  }

  # Not yet provisioned. Uncomment when the job is ready to exist — nothing in
  # main.tf needs to change.
  #
  # new_subs = {
  #   job_name        = "mod-notification-new-subs"
  #   command         = ["python"]
  #   args            = ["-m", "app.new_subs.main"]
  #   schedule        = "*/10 * * * *"
  #   timeout_seconds = 540
  # }
}
