# Identité CI GitHub Actions → Azure : trust OIDC, zéro secret
# (ex-bootstrap-ci.sh, absorbé dans l'IaC).

resource "azuread_application_registration" "ci" {
  display_name = "fluxcen-ci"
}

resource "azuread_service_principal" "ci" {
  client_id = azuread_application_registration.ci.client_id
}

resource "azuread_application_federated_identity_credential" "github" {
  for_each = toset(["release", "infra"])

  application_id = azuread_application_registration.ci.id
  display_name   = "github-${each.key}"
  issuer         = "https://token.actions.githubusercontent.com"
  subject        = "repo:${var.github_repo}:environment:${each.key}"
  audiences      = ["api://AzureADTokenExchange"]
}

# release.yml : publication des artefacts dans le conteneur `plugins`.
resource "azurerm_role_assignment" "ci_publish" {
  scope                = azurerm_storage_container.plugins.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azuread_service_principal.ci.object_id
}

# infra.yml : terraform apply sur le resource group. Owner car le plan
# contient des role assignments (Contributor ne suffit pas).
resource "azurerm_role_assignment" "ci_infra" {
  scope                = azurerm_resource_group.delivery.id
  role_definition_name = "Owner"
  principal_id         = azuread_service_principal.ci.object_id
}
