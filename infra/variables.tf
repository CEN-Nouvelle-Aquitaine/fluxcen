variable "env" {
  description = "Environnement (poc ou prod)"
  type        = string
  default     = "poc"
  validation {
    condition     = contains(["poc", "prod"], var.env)
    error_message = "env doit valoir poc ou prod."
  }
}

variable "location" {
  description = "Région Azure"
  type        = string
  default     = "francecentral"
}

variable "tenant_id" {
  description = "Tenant Entra du CEN"
  type        = string
  default     = "898a7ac2-f878-44ab-80f0-1e1852b7bebd"
}

variable "qgis_client_id" {
  description = "Client id de l'app registration « QGIS » (client public PKCE existant)"
  type        = string
  default     = "80c3a908-e890-4575-9a46-785116e160f9"
}

variable "qgis_app_object_id" {
  description = "Object id de l'app « QGIS » (az ad app show --id <client_id> --query id) ; requis pour l'import initial"
  type        = string
}

# Même convention que les landing zones AWS CEN (00-bootstrap/variables.tf) :
# clés PascalCase, Project/Environment/ManagedBy activées en cost allocation.
variable "common_tags" {
  description = "Common tags to apply to all resources."
  type        = map(string)
  default = {
    Project   = "fluxcen-delivery"
    ManagedBy = "Terraform"
  }

  validation {
    condition     = can(var.common_tags["Project"]) && can(var.common_tags["ManagedBy"])
    error_message = "Common tags must include at least 'Project' and 'ManagedBy' keys."
  }
}

variable "github_repo" {
  description = "Dépôt GitHub (owner/repo) autorisé par les federated credentials"
  type        = string
  default     = "CEN-Nouvelle-Aquitaine/fluxcen"
}
