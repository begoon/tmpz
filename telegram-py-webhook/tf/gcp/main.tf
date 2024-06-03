variable "function_name" {
  default = "bot"
}

variable "function_entry_point" {
  default = "function_handler"
}

variable "function_zip" {
  default = "bot_package.zip"
}

variable "is_public" {
  default = true
}

variable "project" {
  default = "freemynd-karta"
}

variable "region" {
  default = "europe-west2"
}

variable "BOT_TOKEN" {}
variable "TELEGRAM_SECRET_TOKEN" {}
variable "WHEEL" {}
variable "REDIS_HOST" {}
variable "REDIS_PORT" {}
variable "REDIS_PASSWORD" {}

provider "google" {
  project = var.project
  region  = var.region
}

resource "google_storage_bucket" "bucket" {
  name     = "${var.function_name}-function"
  location = var.region
}

resource "google_storage_bucket_object" "zip" {
  name = var.function_zip

  bucket = google_storage_bucket.bucket.name
  source = "../../${var.function_zip}"
}

resource "google_cloudfunctions2_function" "function" {
  name     = var.function_name
  location = var.region

  build_config {
    runtime     = "python311"
    entry_point = var.function_entry_point
    source {
      storage_source {
        bucket = google_storage_bucket.bucket.name
        object = google_storage_bucket_object.zip.name
      }
    }
  }

  service_config {
    min_instance_count               = 0
    max_instance_count               = 1
    available_memory                 = "256M"
    timeout_seconds                  = 60
    max_instance_request_concurrency = 1
    ingress_settings                 = "ALLOW_ALL"
    environment_variables = {
      BOT_TOKEN             = var.BOT_TOKEN
      TELEGRAM_SECRET_TOKEN = var.TELEGRAM_SECRET_TOKEN
      WHEEL                 = var.WHEEL
      WHERE                 = "gcp"
      REDIS_HOST            = var.REDIS_HOST
      REDIS_PORT            = var.REDIS_PORT
      REDIS_PASSWORD        = var.REDIS_PASSWORD
      UPDATED_AT            = timestamp()
    }
  }
}

# https://discuss.hashicorp.com/t/difference-between-google-project-iam-binding-and-google-project-iam-member/49645/2
resource "google_cloudfunctions2_function_iam_member" "invoker" {
  count          = var.is_public ? 1 : 0
  project        = google_cloudfunctions2_function.function.project
  location       = google_cloudfunctions2_function.function.location
  cloud_function = google_cloudfunctions2_function.function.name
  role           = "roles/cloudfunctions.invoker"
  member         = "allUsers"
}

resource "google_cloud_run_service_iam_member" "cloud_run_invoker" {
  count    = var.is_public ? 1 : 0
  project  = google_cloudfunctions2_function.function.project
  location = google_cloudfunctions2_function.function.location
  service  = google_cloudfunctions2_function.function.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "function_url" {
  value = google_cloudfunctions2_function.function.url
}

output "service_url" {
  value = google_cloudfunctions2_function.function.service_config[0].uri
}
