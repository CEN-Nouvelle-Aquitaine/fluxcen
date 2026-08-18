# Objets Entra ID (ex-bootstrap-entra.sh, absorbé dans l'IaC).
#
# L'app « QGIS » existe déjà (validée en réel, feature 001) : elle est
# importée dans azuread_application_registration, qui ne gère que ses
# propriétés de base ; les ajouts (scope API, pré-autorisation, identifier
# URI) passent par les ressources granulaires, sans toucher au reste de
# l'app (redirect URIs, client public...).

import {
  to = azuread_application_registration.qgis
  id = "/applications/${var.qgis_app_object_id}"
}

resource "azuread_application_registration" "qgis" {
  display_name     = "QGIS"
  sign_in_audience = "AzureADMyOrg"

  # Émission du claim `groups` dans les jetons : la Function restreint le
  # canal beta dessus.
  group_membership_claims = ["SecurityGroup"]

  # App de production utilisée par tout le parc : un destroy la supprimerait
  # du tenant. Pour un cycle destroy/apply de POC : terraform state rm
  # (voir README).
  lifecycle {
    prevent_destroy = true
  }
}

resource "azuread_application_identifier_uri" "qgis_api" {
  application_id = azuread_application_registration.qgis.id
  identifier_uri = "api://${var.qgis_client_id}"
}

# UUID fixe du scope : jamais régénéré (idempotence entre applies).
resource "azuread_application_permission_scope" "plugins_read" {
  application_id = azuread_application_registration.qgis.id
  scope_id       = "7f1e0a3c-5b2d-4c8e-9f4a-1d6b8e2c0a55"
  value          = "plugins.read"

  type                       = "User"
  admin_consent_display_name = "Lire le dépôt de plugins FluxCEN"
  admin_consent_description  = "Accès en lecture au catalogue et aux archives du plugin FluxCEN."
  user_consent_display_name  = "Lire le dépôt de plugins FluxCEN"
  user_consent_description   = "Accès en lecture au catalogue et aux archives du plugin FluxCEN."
}

# L'app est son propre client : pas de prompt de consentement pour le scope.
resource "azuread_application_pre_authorized" "qgis_self" {
  application_id       = azuread_application_registration.qgis.id
  authorized_client_id = var.qgis_client_id
  permission_ids       = [azuread_application_permission_scope.plugins_read.scope_id]
}

resource "azuread_group" "beta" {
  display_name     = "FluxCEN-Beta"
  mail_nickname    = "fluxcen-beta"
  security_enabled = true
}
