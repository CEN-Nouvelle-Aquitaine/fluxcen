# Infrastructure du système de delivery FluxCEN

IaC **Terraform** (standard des projets CEN récents) du dépôt de plugins
privé (spec `specs/002-plugin-delivery/`). Providers : `azurerm` (ressources),
`azuread` (objets Entra, ex-scripts de bootstrap absorbés), `azapi`
(uniquement l'Easy Auth `authsettingsV2`, pas encore couvert par azurerm sur
Flex Consumption).

## Prérequis (une fois)

1. **Souscription Azure** active rattachée au tenant CEN
   (`898a7ac2-f878-44ab-80f0-1e1852b7bebd`). Création au portail si absente.
2. **Outils** : `terraform` ≥ 1.7, `az` CLI connecté (compte pouvant créer
   resource groups, assigner des rôles et modifier les app registrations).
3. **Backend d'état** : le POC tourne en état local ; avant l'industrialisation,
   brancher le backend standard CEN (celui des landing zones) via
   `terraform init -backend-config=...` (bloc `backend` dans `versions.tf`).
4. **Import de l'app « QGIS »** : l'app existante est reprise en gestion par un
   bloc `import` déclaratif (`entra.tf`). Renseigner son object id :

   ```bash
   cp terraform.tfvars.example terraform.tfvars
   az ad app show --id 80c3a908-e890-4575-9a46-785116e160f9 --query id -o tsv
   # → coller la valeur dans qgis_app_object_id
   ```

   Seules les propriétés de base (nom, audience, claim groups) sont gérées ;
   les redirect URIs et le caractère client public de l'app ne sont pas touchés
   (ressources granulaires azuread).

## Déploiement

```bash
cd infra
terraform init
terraform plan    # vérifier notamment le premier import de l'app QGIS
terraform apply
```

Sorties : `function_url` (base des dépôts QGIS, `REPO_BASE_URL` de la CI),
`storage_account_name` (`STORAGE_ACCOUNT`), `beta_group_id`, `ci_client_id`
(`AZURE_CLIENT_ID`).

Créées : `rg-fluxcen-delivery-{env}` avec Storage privé (conteneur `plugins`,
versioning), Function Flex Consumption Python 3.11 (managed identity, lecture
du conteneur), Easy Auth (Bearer Entra, audience `api://80c3a908-…`) ; côté
Entra : scope `plugins.read` + pré-autorisation sur l'app « QGIS », groupe
`FluxCEN-Beta` (liste de diffusion des testeurs), app CI `fluxcen-ci` avec federated credentials OIDC GitHub
(environnements `release` et `infra`) et ses rôles.

Code de la Function : `delivery/function/` (déployé par
`func azure functionapp publish` ou `az functionapp deployment`).

## CI (GitHub Actions)

Auth 100 % OIDC, aucun secret. Variables GitHub (`Settings → Variables`) :
`AZURE_CLIENT_ID` (= sortie `ci_client_id`), `AZURE_TENANT_ID`,
`AZURE_SUBSCRIPTION_ID`, `QGIS_APP_OBJECT_ID`, `DELIVERY_ENV`,
`STORAGE_ACCOUNT`, `REPO_BASE_URL`, et pour l'apply en CI :
`TF_STATE_RG`/`TF_STATE_SA`/`TF_STATE_CONTAINER`. Environnements GitHub :
`release` (publication par tag) et `infra` (apply avec approbation).
Secret d'environnement `release` : `LINKS_YAML` (contenu du
`config/yaml/links.yaml` de production, injecté dans le zip à la release,
FR-016 ; ce n'est pas un secret d'authentification, SC-005 reste tenu).

Note : les IDs ci-dessus sont des identifiants publics (adressage), pas des
secrets ; l'authentification est portée par le trust OIDC (federated
credentials, `infra/ci.tf`).

## Destruction / recréation (SC-006)

```bash
terraform destroy   # puis terraform apply, et re-publier un artefact
```

Attention : l'app « QGIS » étant importée, `destroy` la détruirait. Pour un
cycle destroy/apply de POC, retirer d'abord l'app de l'état :
`terraform state rm azuread_application_registration.qgis` (et ses ressources
granulaires), ou cibler le destroy sur le module azurerm.

Retour arrière d'un catalogue : versioning de blobs actif, restaurer une
version précédente de `stable/plugins.xml` (portail ou `az storage blob`).
