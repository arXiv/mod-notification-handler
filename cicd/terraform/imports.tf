# Adoption of the resources that already exist, in whichever environment you target.
#
# These tell Terraform "the block on the left already exists in GCP as the id on the
# right" — they do not create anything. `terraform plan` then reads each real resource
# and reports where this config disagrees with it. Edit main.tf / the .tfvars until plan
# reports no changes, then apply: that writes state and touches nothing live.
#
# Ids are built from variables so one file covers both environments. Terraform ignores
# an import block whose resource is already in state, so this file can stay in place
# while you do development first and production second.
#
# Delete it once both environments have been imported.

import {
  to = google_service_account.job
  id = "projects/${var.project_id}/serviceAccounts/${local.service_account_email}"
}

# google_project_iam_member ids are space-separated: "<project> <role> <member>".
import {
  to = google_project_iam_member.job["roles/cloudsql.client"]
  id = "${var.project_id} roles/cloudsql.client serviceAccount:${local.service_account_email}"
}

import {
  to = google_project_iam_member.job["roles/pubsub.subscriber"]
  id = "${var.project_id} roles/pubsub.subscriber serviceAccount:${local.service_account_email}"
}

import {
  to = google_project_iam_member.job["roles/run.invoker"]
  id = "${var.project_id} roles/run.invoker serviceAccount:${local.service_account_email}"
}

import {
  to = google_project_iam_member.job["roles/secretmanager.secretAccessor"]
  id = "${var.project_id} roles/secretmanager.secretAccessor serviceAccount:${local.service_account_email}"
}

import {
  to = google_pubsub_topic.mod_notify
  id = "projects/${var.project_id}/topics/${local.topic_name}"
}

import {
  to = google_pubsub_subscription.mod_actions
  id = "projects/${var.project_id}/subscriptions/${local.subscription_name}"
}

# mod_actions is the only job that already exists. new_subs and daily_update will be
# created by Terraform, so they get no import block — adding one for a job that doesn't
# exist yet makes plan fail.
import {
  to = google_cloud_run_v2_job.jobs["mod_actions"]
  id = "projects/${var.project_id}/locations/${var.region}/jobs/${var.jobs["mod_actions"].job_name}"
}

import {
  to = google_cloud_scheduler_job.jobs["mod_actions"]
  id = "projects/${var.project_id}/locations/${var.region}/jobs/${var.jobs["mod_actions"].job_name}-scheduler-trigger"
}

# Build triggers import by uuid, not by name — hence build_trigger_id in the .tfvars.
# The two environments' triggers also live in different locations.
import {
  to = google_cloudbuild_trigger.deploy
  id = "projects/${var.project_id}/locations/${var.build_trigger_location}/triggers/${var.build_trigger_id}"
}
