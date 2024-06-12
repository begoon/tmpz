variable "project" {}
variable "region" {}
variable "instance_name" {}
variable "database_name" {}
variable "user_name" {}
variable "user_password" {}

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "4.0.0"
    }
  }
}

resource "google_sql_database_instance" "instance" {
  name             = var.instance_name
  database_version = "POSTGRES_15"
  project          = var.project
  region           = var.region

  settings {
    tier              = "db-f1-micro"
    availability_type = "ZONAL"
    disk_autoresize   = false
    disk_size         = 10
    disk_type         = "PD_HDD"

    ip_configuration {
      authorized_networks {
        value = "0.0.0.0/0"
      }
    }
  }
}

resource "google_sql_database" "database" {
  name     = var.database_name
  instance = google_sql_database_instance.instance.name
  project  = var.project
}

resource "google_sql_user" "master" {
  name     = var.user_name
  instance = google_sql_database_instance.instance.name
  password = var.user_password
  type     = "BUILT_IN"
}

output "connection_name" {
  value = google_sql_database_instance.instance.connection_name
}

output "dsn_name" {
  value = google_sql_database_instance.instance.connection_name
}

output "user_name" {
  value = google_sql_user.master.name
}

output "user_password" {
  value = nonsensitive(google_sql_user.master.password)
}

output "instance_name" {
  value = google_sql_database_instance.instance.name
}

output "public_ip_address" {
  value = google_sql_database_instance.instance.public_ip_address
}
