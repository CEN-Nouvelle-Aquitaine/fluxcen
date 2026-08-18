# Système de delivery FluxCEN (spec 002-plugin-delivery).
# Terraform : standard des projets CEN récents (landing zones AWS).

terraform {
  required_version = ">= 1.7"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 3.0"
    }
    # azapi : uniquement pour authsettingsV2 (Easy Auth), pas encore couvert
    # par azurerm sur azurerm_function_app_flex_consumption. À migrer vers le
    # bloc natif auth_settings_v2 quand le provider le portera sur Flex.
    azapi = {
      source  = "azure/azapi"
      version = "~> 2.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Backend d'état : brancher le standard CEN (celui des landing zones) via
  # `terraform init -backend-config=...`. En attendant, état local pour le POC.
  # backend "azurerm" {}
}

provider "azurerm" {
  features {}
  # CI : auth OIDC via ARM_USE_OIDC / ARM_CLIENT_ID / ARM_TENANT_ID /
  # ARM_SUBSCRIPTION_ID (aucun secret). En local : az CLI.
}

provider "azuread" {}

provider "azapi" {}
