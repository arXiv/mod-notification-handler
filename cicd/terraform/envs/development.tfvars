# Every value that makes development different from production.
#
#   terraform init -backend-config=envs/development.backend.hcl -reconfigure
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
# Build trigger
# ---------------------------------------------------------------------------

build_trigger_location    = "global"
build_trigger_branch      = "^develop$"
build_trigger_description = "Build and deploy a cloud run job for processing notifcations for moderators"

# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

# Every job inherits the shared config above — database, mail server, reply-to. An
# `env_vars` block on a job overrides individual keys for that job only, which is how a
# new job runs against test settings while the others stay on the real ones.

jobs = {
  mod_actions = {
    job_name        = "mod-notification-handler"
    schedule        = "*/10 * * * *"
    timeout_seconds = 540
    # No command/args: uses the image CMD, python -m app.mod_actions.main.
  }

  # Not yet provisioned. Uncomment when the job is ready to exist — nothing in
  # main.tf needs to change.
  #
  # daily_update = {
  #   job_name        = "mod-notification-daily-update"
  #   command         = ["python"]
  #   args            = ["-m", "app.daily_update.main"]
  #   schedule        = "0 8 * * *"
  #   timeout_seconds = 540
  #
  #   # While this job is still being tested: everything it sends comes to one inbox,
  #   # and the other jobs are unaffected. Delete these two lines to put it back on
  #   # the shared settings.
  #   env_vars = {
  #     REDIRECT_EMAILS    = "True"
  #     REDIRECT_RECIPIENT = "TODO test email"
  #   }
  # }
  #
  # new_subs = {
  #   job_name        = "mod-notification-new-subs"
  #   command         = ["python"]
  #   args            = ["-m", "app.new_subs.main"]
  #   schedule        = "*/10 * * * *"
  #   timeout_seconds = 540
  # }
}
