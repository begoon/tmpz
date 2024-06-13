variable "region" {}
variable "project" {}
variable "topic_name" {}


terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "5.3.0"
    }
    curl = {
      source  = "anschoewe/curl"
      version = "1.0.2"
    }
  }
}

provider "curl" {
}

data "curl" "tunnels" {
  http_method = "GET"
  uri         = "http://localhost:4040/api/tunnels"
}

locals {
  tunnel_data = jsondecode(data.curl.tunnels.response)
}

output "tunnel" {
  value = local.tunnel_data.tunnels[0].public_url
}

provider "google" {
  project = var.project
  region  = var.region
}

data "google_project" "project" {
  project_id = var.project
}

locals {
  compute_service_account = "${data.google_project.project.number}-compute@developer.gserviceaccount.com"
  pubsub_service_account  = "service-${data.google_project.project.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

resource "google_pubsub_topic" "topic_dlq" {
  name = "${var.topic_name}-dlq"
}

resource "google_pubsub_subscription" "subscription_dlq" {
  name  = "${var.topic_name}-sub-dlq"
  topic = google_pubsub_topic.topic_dlq.id

  push_config {
    push_endpoint = "${local.tunnel_data.tunnels[0].public_url}/dlq"
    no_wrapper {
      write_metadata = true
    }
  }
}

resource "google_pubsub_topic" "topic" {
  name = var.topic_name
}

resource "google_pubsub_subscription" "subscription" {
  name  = "${var.topic_name}-sub"
  topic = google_pubsub_topic.topic.id

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.topic_dlq.id
    max_delivery_attempts = 5
  }

  push_config {
    push_endpoint = local.tunnel_data.tunnels[0].public_url
    oidc_token {
      service_account_email = local.compute_service_account
      audience              = "https://pubsub.googleapis.com/google.pubsub.v1.Publisher"
    }
    no_wrapper {
      write_metadata = true
    }
  }
}

resource "google_pubsub_subscription_iam_member" "subscription_aim_member" {
  subscription = google_pubsub_subscription.subscription.id
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:${local.pubsub_service_account}"
}

resource "google_pubsub_topic_iam_member" "topic_dlq_aim_member" {
  topic  = google_pubsub_topic.topic_dlq.id
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${local.pubsub_service_account}"
}

output "topic" {
  value = {
    topic        = google_pubsub_topic.topic.id
    subscription = google_pubsub_subscription.subscription.id
  }
}
