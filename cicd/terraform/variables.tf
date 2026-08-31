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
# Jobs
# ---------------------------------------------------------------------------

variable "image" {
  description = <<-EOT
    Full container image reference including tag, e.g.
    gcr.io/arxiv-development/mod-notification-handler/<sha>.

    Deliberately has no default. CI builds the image and passes the tag in, so Terraform
    owns this field and `plan` reports what is actually deployed. A default would let a
    hand-run apply silently retag a job to something stale.
  EOT
  type        = string
}

variable "jobs" {
  description = <<-EOT
    One entry per Cloud Run job. Adding new_subs or daily_update means adding an entry
    here in each environment's .tfvars — no changes to main.tf.
  EOT
  type = map(object({
    job_name        = string
    schedule        = string
    timeout_seconds = number

    # Retries of a failed execution. Only worth raising for a job that exits non-zero
    max_retries = optional(number, 1)

    # Both required. Every job states its own entrypoint
    command = list(string)
    args    = list(string)

    # Per-job overrides, merged over the shared values in main.tf. A key here wins.
    # Use this to run a new job against test settings while the others stay on the
    # real ones — e.g. env_vars = { REDIRECT_EMAILS = "True" }, with the address itself
    # overridden via secret_env_vars since addresses are not committed to this repo.
    # Delete the override to put the job back on shared config.
    env_vars        = optional(map(string), {})
    secret_env_vars = optional(map(string), {})
  }))
}
