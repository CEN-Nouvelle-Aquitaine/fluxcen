output "function_url" {
  description = "Base des dépôts QGIS (REPO_BASE_URL de la CI)"
  value       = "https://${azurerm_function_app_flex_consumption.delivery.default_hostname}"
}

output "storage_account_name" {
  description = "Variable STORAGE_ACCOUNT de la CI"
  value       = azurerm_storage_account.delivery.name
}

output "beta_group_id" {
  description = "Groupe Entra FluxCEN-Beta"
  value       = azuread_group.beta.object_id
}

output "ci_client_id" {
  description = "Variable AZURE_CLIENT_ID de la CI (app fluxcen-ci)"
  value       = azuread_application_registration.ci.client_id
}
