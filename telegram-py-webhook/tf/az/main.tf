variable "functionapp_name" {
  default = "bot-function"
}

variable "function_zip" {
  default = "bot_package.zip"
}

variable "region" {
  default = "UK West"
}

variable "BOT_TOKEN" {}
variable "TELEGRAM_SECRET_TOKEN" {}
variable "WHEEL" {}
variable "REDIS_HOST" {}
variable "REDIS_PORT" {}
variable "REDIS_PASSWORD" {}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "bot" {
  name     = "botfunction"
  location = var.region
}

resource "azurerm_storage_account" "bot" {
  name                     = "botfunctionsa"
  resource_group_name      = azurerm_resource_group.bot.name
  location                 = azurerm_resource_group.bot.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_service_plan" "bot" {
  name                = "botfunction"
  location            = azurerm_resource_group.bot.location
  resource_group_name = azurerm_resource_group.bot.name
  os_type             = "Linux"
  sku_name            = "Y1"
}

resource "azurerm_linux_function_app" "bot" {
  name                       = var.functionapp_name
  location                   = azurerm_resource_group.bot.location
  resource_group_name        = azurerm_resource_group.bot.name
  service_plan_id            = azurerm_service_plan.bot.id
  storage_account_name       = azurerm_storage_account.bot.name
  storage_account_access_key = azurerm_storage_account.bot.primary_access_key
  site_config {
    application_stack {
      python_version = "3.11"
    }
  }
  zip_deploy_file = "../../${var.function_zip}"
  app_settings = {
    BOT_TOKEN             = var.BOT_TOKEN
    TELEGRAM_SECRET_TOKEN = var.TELEGRAM_SECRET_TOKEN
    WHEEL                 = var.WHEEL
    WHERE                 = "az"
    REDIS_HOST            = var.REDIS_HOST
    REDIS_PORT            = var.REDIS_PORT
    REDIS_PASSWORD        = var.REDIS_PASSWORD
    UPDATED_AT            = timestamp()
  }
}

output "function_app_name" {
  value = azurerm_linux_function_app.bot.name
}

output "function_app_default_hostname" {
  value = azurerm_linux_function_app.bot.default_hostname
}
