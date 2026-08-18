# Ressources Azure du service de distribution.

locals {
  tags = merge(var.common_tags, {
    Environment = var.env
    Repository  = var.github_repo
  })
}

resource "azurerm_resource_group" "delivery" {
  name     = "rg-fluxcen-delivery-${var.env}"
  location = var.location
  tags     = local.tags
}

# --- Stockage : catalogues + artefacts (privé) -----------------------------

resource "random_id" "storage" {
  byte_length = 4
  keepers     = { env = var.env }
}

resource "azurerm_storage_account" "delivery" {
  name                            = substr("stfluxcen${var.env}${random_id.storage.hex}", 0, 24)
  resource_group_name             = azurerm_resource_group.delivery.name
  location                        = azurerm_resource_group.delivery.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false

  blob_properties {
    versioning_enabled = true # retour arrière sur plugins.xml
  }

  tags = local.tags
}

resource "azurerm_storage_container" "plugins" {
  name               = "plugins"
  storage_account_id = azurerm_storage_account.delivery.id
}

resource "azurerm_storage_container" "releases" {
  name               = "function-releases"
  storage_account_id = azurerm_storage_account.delivery.id
}

# --- Function App (Flex Consumption, Python 3.11) --------------------------

resource "azurerm_service_plan" "delivery" {
  name                = "plan-fluxcen-delivery-${var.env}"
  resource_group_name = azurerm_resource_group.delivery.name
  location            = azurerm_resource_group.delivery.location
  os_type             = "Linux"
  sku_name            = "FC1"
  tags                = local.tags
}

resource "azurerm_function_app_flex_consumption" "delivery" {
  name                = "func-fluxcen-delivery-${var.env}"
  resource_group_name = azurerm_resource_group.delivery.name
  location            = azurerm_resource_group.delivery.location
  service_plan_id     = azurerm_service_plan.delivery.id

  storage_container_type     = "blobContainer"
  storage_container_endpoint = "${azurerm_storage_account.delivery.primary_blob_endpoint}${azurerm_storage_container.releases.name}"
  # Connection string pour le stockage runtime : le mode managed identity du
  # runtime Flex n'est pas encore fiable dans azurerm (storage_uses_managed_
  # identity ignoré). La lecture du conteneur `plugins` par le code, elle,
  # passe bien par la managed identity (role assignment ci-dessous).
  storage_authentication_type = "StorageAccountConnectionString"
  storage_access_key          = azurerm_storage_account.delivery.primary_access_key

  runtime_name           = "python"
  runtime_version        = "3.11"
  maximum_instance_count = 40
  instance_memory_in_mb  = 2048

  https_only = true

  app_settings = {
    STORAGE_ACCOUNT_URL = azurerm_storage_account.delivery.primary_blob_endpoint
  }

  site_config {}

  identity {
    type = "SystemAssigned"
  }

  tags = local.tags
}

# Lecture des plugins par le code de la Function (managed identity).
resource "azurerm_role_assignment" "function_read_plugins" {
  scope                = azurerm_storage_container.plugins.id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = azurerm_function_app_flex_consumption.delivery.identity[0].principal_id
}

# --- Easy Auth : Bearer Entra obligatoire, 401 sinon -----------------------
# Via azapi : auth_settings_v2 n'est pas (encore) porté par azurerm sur la
# ressource Flex Consumption. Payload identique à la config App Service
# authsettingsV2 documentée.

# azapi_update_resource, pas azapi_resource : authsettingsV2 existe
# implicitement sur tout site, on le modifie au lieu de le créer.
resource "azapi_update_resource" "easy_auth" {
  type      = "Microsoft.Web/sites/config@2024-04-01"
  name      = "authsettingsV2"
  parent_id = azurerm_function_app_flex_consumption.delivery.id

  body = {
    properties = {
      platform = {
        enabled = true # sans ce bloc, Easy Auth reste désactivé
      }
      globalValidation = {
        requireAuthentication       = true
        unauthenticatedClientAction = "Return401"
      }
      identityProviders = {
        azureActiveDirectory = {
          enabled = true
          registration = {
            clientId     = var.qgis_client_id
            openIdIssuer = "https://login.microsoftonline.com/${var.tenant_id}/v2.0"
          }
          validation = {
            # Les deux formes d'audience : jetons v1 (api://...) et v2 (GUID nu),
            # selon requestedAccessTokenVersion de l'app.
            allowedAudiences = ["api://${var.qgis_client_id}", var.qgis_client_id]
          }
        }
      }
    }
  }
}
