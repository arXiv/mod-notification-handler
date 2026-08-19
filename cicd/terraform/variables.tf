# Declarations only. Values live in envs/<env>.tfvars.

variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

# ---------------------------------------------------------------------------
# Application config — the per-environment surface
# ---------------------------------------------------------------------------

variable "env_name" {
  description = "Value of the ENV variable: DEVELOP or PRODUCTION."
  type        = string
}

variable "send_emails" {
  description = "Master switch. False means no email is ever sent, though messages are still acked."
  type        = bool
}

variable "redirect_emails" {
  description = "True sends every email to redirect_recipient instead of the real moderators."
  type        = bool
}

variable "redirect_recipient_secret" {
  description = "Secret Manager secret holding the address redirected mail goes to. Null in any environment that should not have one — the variable is then omitted from the job entirely rather than set empty."
  type        = string
  default     = null
}

# ---------------------------------------------------------------------------
# External dependencies — referenced, never created here
# ---------------------------------------------------------------------------

variable "db_secret_name" {
  description = "Secret Manager secret holding CLASSIC_DB_URI."
  type        = string
}

variable "cloudsql_instance" {
  description = "Cloud SQL connection name, project:region:instance."
  type        = string
}

# ---------------------------------------------------------------------------
# Build trigger
# ---------------------------------------------------------------------------

variable "build_trigger_location" {
  description = "Region the trigger lives in. Currently 'global' in dev and 'us-east1' in prod — consolidating these is a queued follow-up change, not part of the import."
  type        = string
}

variable "build_trigger_branch" {
  description = "Regex for the branch that deploys this environment."
  type        = string
}

variable "build_trigger_description" {
  description = "Free text on the trigger. Differs between environments; kept as-is so the import converges."
  type        = string
}

variable "build_trigger_id" {
  description = "UUID of the existing Cloud Build trigger. Only used by imports.tf — Cloud Build triggers import by uuid, not by name. Can be removed along with imports.tf once both environments are adopted."
  type        = string
}

# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

variable "jobs" {
  description = <<-EOT
    One entry per Cloud Run job. Adding new_subs or daily_update means adding an entry
    here in each environment's .tfvars — no changes to main.tf.
  EOT
  type = map(object({
    job_name        = string
    schedule        = string
    timeout_seconds = number

    # Empty command and args mean the container uses the image's CMD. That is how
    # mod_actions runs today; new_subs and daily_update override both to start their
    # own entrypoint.
    command = optional(list(string), [])
    args    = optional(list(string), [])

    # Per-job overrides, merged over the shared values in main.tf. A key here wins.
    # Use this to run a new job against test settings while the others stay on the
    # real ones — e.g. env_vars = { REDIRECT_EMAILS = "True" }, with the address itself
    # overridden via secret_env_vars since addresses are not committed to this repo.
    # Delete the override to put the job back on shared config.
    env_vars        = optional(map(string), {})
    secret_env_vars = optional(map(string), {})
  }))
}
