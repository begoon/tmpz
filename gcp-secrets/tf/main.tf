variable "project" {}
variable "region" {}
variable "secret_value" {}
variable "image" {}

terraform {
  required_version = ">= 1.1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 2.0.0"
    }
  }
}

resource "google_secret_manager_secret" "secret" {
  project   = var.project
  secret_id = "ephemeral-secret"

  version_destroy_ttl = "86400s"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "secret_value" {
  secret      = google_secret_manager_secret.secret.id
  secret_data = var.secret_value
}

output "secret" {
  value = {
    id    = google_secret_manager_secret.secret.id
    name  = google_secret_manager_secret.secret.name
    value = nonsensitive(google_secret_manager_secret_version.secret_value.secret_data)
  }
}

# ---

resource "google_cloud_run_v2_service" "service" {
  name     = "secret-accessor-service"
  project  = var.project
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"


  template {
    volumes {
      name = "secrets"
      secret {
        secret       = google_secret_manager_secret.secret.secret_id
        default_mode = 292 # 0444
        items {
          version = "latest"
          path    = "ephemeral-secret"
        }
      }
    }

    containers {
      image = var.image
      env {
        name  = "INGESTED_ENVIRONMENT_VARIABLE"
        value = "-value-"
      }
      env {
        name = "INGESTED_SECRET_VARIABLE"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secret.secret_id
            version = "latest"
          }
        }
      }
      volume_mounts {
        name       = "secrets"
        mount_path = "/secrets"
      }
    }
  }
}

resource "google_cloud_run_v2_service_iam_binding" "public" {
  depends_on = [google_cloud_run_v2_service.service]
  name       = google_cloud_run_v2_service.service.name
  project    = var.project
  location   = var.region
  role       = "roles/run.invoker"
  members    = ["allUsers"]
}

data "google_project" "project" {
  project_id = var.project
}

resource "google_secret_manager_secret_iam_member" "secret-iam-member" {
  secret_id  = google_secret_manager_secret.secret.id
  role       = "roles/secretmanager.secretAccessor"
  member     = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
  depends_on = [google_secret_manager_secret.secret]
}

output "project" {
  value = {
    id     = data.google_project.project.project_id
    number = data.google_project.project.number
  }
}

output "service_url" {
  value = google_cloud_run_v2_service.service.uri
}
