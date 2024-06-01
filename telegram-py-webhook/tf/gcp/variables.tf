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

variable "project" {}
variable "region" {}

variable "BOT_TOKEN" {}
variable "TELEGRAM_SECRET_TOKEN" {}
variable "ADMIN" {}
variable "WH" {}
variable "REDIS_HOST" {}
variable "REDIS_PORT" {}
variable "REDIS_PASSWORD" {}
