# First file Terraform reads. `terraform init` acts on it.

terraform {
  required_version = "~> 1.13"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.2"
    }
  }

  # Partial backend config: the prefix is fixed, the bucket is not. One config serves
  # both environments, so the bucket is supplied at init time — from a GitHub variable
  # in CI, or inline when running by hand:
  #
  #   terraform init -reconfigure -backend-config="bucket=dev-arxiv-terraform-state"
  #
  # This block cannot use variables — Terraform reads it before variables exist.
  backend "gcs" {
    prefix = "mod-notification-handler"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
