# Everything this service owns, in whichever environment you point it at.
#
# One config serves both. The environment is chosen by two files at the command line:
# envs/<env>.backend.hcl picks the state, envs/<env>.tfvars picks the values.
# Nothing environment-specific belongs in this file.

locals {
  # Facts about this service, identical in every environment.
  topic_name                 = "mod-notify"
  subscription_name          = "mod-notification-handler"
  image_name                 = "mod-notification-handler"
  cloudbuild_service_account = "cloudbuild-sa"

  halon_secret_name     = "HALON_CREDS"
  archival_email_secret = "mod-notification-archival-email"
  mod_reply_to_secret   = "mod-notification-mod-reply-to"

  labels = {
    arxiv-system    = "eust"
    arxiv-subsystem = "eust-modapi"
  }

  service_account_id = "mod-notification-handler"

  # Cloud Build overwrites this tag on every merge, and the job ignores changes to it afterwards.
  image = "gcr.io/${var.project_id}/${local.image_name}:latest"

  # Shared by all three jobs. Change the database here and every job picks it up.
  shared_env_vars = {
    ENV             = var.env_name
    GCP_PROJECT_ID  = var.project_id
    SEND_EMAILS     = title(tostring(var.send_emails))
    REDIRECT_EMAILS = title(tostring(var.redirect_emails))
  }

  shared_secret_env_vars = merge(
    {
      CLASSIC_DB_URI = var.db_secret_name
      HALON_CREDS    = local.halon_secret_name
      ARCHIVAL_EMAIL = local.archival_email_secret
      MOD_REPLY_TO   = local.mod_reply_to_secret
    },
    # Omitted entirely rather than set empty when an environment has no redirect
    # address — the app reads it as Optional[str] and "" is not None.
    var.redirect_recipient_secret == null ? {} : { REDIRECT_RECIPIENT = var.redirect_recipient_secret },
  )
}

# ---------------------------------------------------------------------------
# Service account
# ---------------------------------------------------------------------------

resource "google_service_account" "job" {
  account_id   = local.service_account_id
  project      = var.project_id
  display_name = "mod-notification-handler"
  description  = "handles sending notifications to moderators"
}

resource "google_project_iam_member" "job" {
  for_each = toset([
    "roles/cloudsql.client",              # connect to the classic DB
    "roles/pubsub.subscriber",            # pull from the subscription
    "roles/run.invoker",                  # Cloud Scheduler invokes the job as this SA
    "roles/secretmanager.secretAccessor", # read the DB URI and SMTP creds
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.job.email}"
}

# ---------------------------------------------------------------------------
# Pub sub
# ---------------------------------------------------------------------------

# modapi publishes here when an email notification should be sent.
resource "google_pubsub_topic" "mod_notify" {
  name    = local.topic_name
  project = var.project_id
  labels  = local.labels
}

resource "google_pubsub_subscription" "mod_actions" {
  name    = local.subscription_name
  project = var.project_id
  topic   = google_pubsub_topic.mod_notify.id
  labels  = local.labels

  # Long enough for a full batch to be pulled, rendered, and sent before redelivery.
  ack_deadline_seconds = 600

  enable_exactly_once_delivery = true
  message_retention_duration   = "86400s"

  # Empty ttl means the subscription never expires on its own.
  expiration_policy {
    ttl = ""
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
}

# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

# One Cloud Run job per entry in var.jobs. They share one container image and differ
# only by command/args, schedule, and timeout.
resource "google_cloud_run_v2_job" "jobs" {
  for_each = var.jobs

  name     = each.value.job_name
  project  = var.project_id
  location = var.region
  labels   = local.labels

  template {
    parallelism = 1
    task_count  = 1

    # Executions carry their own copy of the labels, separate from the job's. gcloud set
    # both on the live jobs; dropping these would strip them from every execution.
    labels = local.labels

    template {
      service_account       = google_service_account.job.email
      max_retries           = 1
      timeout               = "${each.value.timeout_seconds}s"
      execution_environment = "EXECUTION_ENVIRONMENT_GEN2"

      # Attaches the existing Cloud SQL instance. 
      # TODO verify against `terraform plan` during import. The live jobs were created
      # with the v1 `run.googleapis.com/cloudsql-instances` annotation; this is the v2
      # spelling of the same thing, and the provider may report it differently.
      volumes {
        name = "cloudsql"
        cloud_sql_instance {
          instances = [var.cloudsql_instance]
        }
      }

      containers {
        # Matches the name gcloud generated on the live jobs. Import will fail to
        # converge if this differs.
        name  = "${each.value.job_name}-1"
        image = local.image

        # null, not [], so Terraform omits the field entirely and the container falls
        # through to the image's CMD — which is how mod_actions runs today.
        command = length(each.value.command) > 0 ? each.value.command : null
        args    = length(each.value.args) > 0 ? each.value.args : null

        # Two dynamic blocks of the same type concatenate — plain vars first, then the
        # secret-backed ones. In both, a job's own entry overrides the shared value for
        # that one key and inherits the rest, so the database and mail credentials stay
        # defined once.
        dynamic "env" {
          for_each = merge(local.shared_env_vars, each.value.env_vars)
          content {
            name  = env.key
            value = env.value
          }
        }

        dynamic "env" {
          for_each = merge(local.shared_secret_env_vars, each.value.secret_env_vars)
          content {
            name = env.key
            value_source {
              secret_key_ref {
                secret  = env.value
                version = "latest"
              }
            }
          }
        }

        volume_mounts {
          name       = "cloudsql"
          mount_path = "/cloudsql"
        }

        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
      }
    }
  }

  lifecycle {
    # Cloud Build runs `gcloud run jobs update --image=...:$COMMIT_SHA` on every merge.
    # Without this, Terraform would see that new tag as drift and revert it — the two
    # would undo each other on every run. Terraform owns the job's shape; Cloud Build
    # owns which image is in it.
    ignore_changes = [
      template[0].template[0].containers[0].image,
      client,
      client_version,
    ]
  }
}

# One scheduler per job, firing it on its own cron.
resource "google_cloud_scheduler_job" "jobs" {
  for_each = var.jobs

  name        = "${each.value.job_name}-scheduler-trigger"
  project     = var.project_id
  region      = var.region
  description = "Runs the ${each.value.job_name} Cloud Run job."

  schedule         = each.value.schedule
  time_zone        = "Etc/UTC"
  attempt_deadline = "180s"

  retry_config {
    min_backoff_duration = "5s"
    max_backoff_duration = "3600s"
    max_doublings        = 5
    max_retry_duration   = "0s"
  }

  http_target {
    http_method = "POST"

    # Triggers one execution of the job. The Run Admin API returns immediately, which
    # is why the 180s attempt deadline can be shorter than the job's own timeout.
    uri = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${google_cloud_run_v2_job.jobs[each.key].name}:run"

    # No headers block: Cloud Scheduler sets User-Agent itself. `gcloud describe` reports
    # it, but it isn't user-managed, so declaring it here creates a diff for nothing.

    # The job's own service account holds roles/run.invoker, so it can invoke itself.
    oauth_token {
      service_account_email = google_service_account.job.email
      scope                 = "https://www.googleapis.com/auth/cloud-platform"
    }
  }
}

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

# Builds the image and runs `gcloud run jobs update` on merge. Terraform owns the
# trigger's definition; Cloud Build still does the building.
resource "google_cloudbuild_trigger" "deploy" {
  name        = "mod-notification-handler"
  project     = var.project_id
  location    = var.build_trigger_location
  description = var.build_trigger_description

  filename        = "cicd/cloudbuild.yaml"
  service_account = "projects/${var.project_id}/serviceAccounts/${local.cloudbuild_service_account}@${var.project_id}.iam.gserviceaccount.com"

  # Cloud Build triggers have no labels field; they use tags instead.
  tags = ["mod-notify"]

  github {
    owner = "arXiv"
    name  = "mod-notification-handler"
    push {
      branch = var.build_trigger_branch
    }
  }

  substitutions = {
    _DEPLOY_REGION = var.region
    _JOB_NAME      = local.image_name

    # Deliberately not setting _JOB_NAMES while there is only one job — cloudbuild.yaml
    # declares a default that covers it. Add this line when a second job exists and the
    # trigger needs to deploy more than one:
    #
    #   _JOB_NAMES = join(" ", [for job in var.jobs : job.job_name])
    #
    # Map iteration is ordered by key, so that value is stable across plans.
  }

  include_build_logs = "INCLUDE_BUILD_LOGS_WITH_STATUS"
}
