# Data Model: Système de delivery privé du plugin FluxCEN

**Date**: 2026-08-18 | **Plan**: [plan.md](plan.md)

Aucune base de données. L'état du système vit dans quatre supports : le Blob Storage (catalogues et artefacts), Entra ID (identités et groupe), la configuration de la Function (Bicep), et le poste QGIS (authcfg + dépôts enregistrés).

## Canal

| Champ | Type | Règles |
|---|---|---|
| nom | `stable` \| `beta` | Seules valeurs admises ; tout autre segment d'URL → 404. Le canal « interne » de la spec correspond au segment `stable` (nommage URL neutre, indépendant de l'organisation) |
| préfixe blob | chemin | `stable/` ou `beta/` dans le conteneur `plugins` |
| règle d'accès | politique | `stable` : toute identité du tenant validée par Easy Auth ; `beta` : en plus, claim `groups` contenant `BETA_GROUP_ID` |

## Catalogue (`plugins.xml`)

Un par canal, stocké en blob (`{canal}/plugins.xml`). Format : XML du dépôt de plugins QGIS.

| Champ XML | Règles |
|---|---|
| `name` | `FluxCEN` (constant) |
| `version` | SemVer `x.y.z` ou `x.y.z-beta.n` ; ordre PEP 440 respecté par QGIS |
| `download_url` | URL absolue de la Function : `https://{host}/{canal}/FluxCEN.{version}.zip` ; jamais de query string |
| `qgis_minimum_version` | `3.34` (aligné sur `metadata.txt`) |
| `experimental` | `False` sur les deux canaux (la restriction beta est un contrôle d'accès serveur, pas un flag client) |

Invariants :
- Le catalogue `beta` liste la dernière beta ET la dernière stable (fusion `qgis-plugin-repo merge`).
- Le catalogue `stable` ne liste jamais de pré-version.
- Toute version listée a son zip présent dans le même préfixe (publication atomique : zip d'abord, XML ensuite).

## Artefact

| Champ | Règles |
|---|---|
| nom de blob | `{canal}/FluxCEN.{version}.zip` |
| contenu | zip du plugin, sans `__pycache__`, `tests/`, `infra/`, `delivery/`, `.specify/`, `.claude/` |
| version | identique à `metadata.txt` du zip et au tag Git (`v` retiré) |
| immuabilité | un zip publié n'est jamais réécrit ; republier une version = nouveau tag correctif |

## Groupe d'accès

| Champ | Règles |
|---|---|
| objet | groupe de sécurité Entra `FluxCEN-Beta` (créé par `bootstrap-entra.sh`) |
| propagation | son `object id` est passé à la Function en app setting `BETA_GROUP_ID` (Bicep param) |
| claim | l'app registration émet `groups` (`groupMembershipClaims: SecurityGroup`) |
| retrait | effet au prochain renouvellement de jeton (≤ 1 h + refresh) ; accepté |

## Configuration de poste (provisioning)

| Élément | Règles |
|---|---|
| authcfg « FluxCEN delivery » | OAuth2 Authorization Code PKCE, app `80c3a908-…`, tenant CEN, scope `api://80c3a908-…/plugins.read offline_access`, secret vide, jeton persistant, redirect `127.0.0.1:{port}/qgis-client` |
| port de redirect | 17070 par défaut ; si occupé (sonde bind), repli sur le premier libre d'une liste fixe ; Entra ignore le port des URI loopback (RFC 8252), aucun changement portail |
| distinction | authcfg distinct de l'authcfg Graph du plugin (feature 001, scope `Files.Read.All`) : une audience par authcfg, même app registration |
| dépôts enregistrés | `QgsSettings` `app/plugin_repositories/FluxCEN (interne)` → `https://{host}/stable/plugins.xml` + authcfg ; entrée beta ajoutée seulement si demandé (paramètre de déploiement Intune) |
| check au démarrage | `checkOnStart` laissé à `false` (défaut QGIS #64885) |
| idempotence | ré-exécution sans effet si l'état est conforme ; répare authcfg ou dépôts dérivés ; ne touche à rien d'autre |

## Configuration d'infrastructure (Terraform : azurerm + azuread + azapi)

| Ressource | Points clés |
|---|---|
| Resource group | `rg-fluxcen-delivery-{env}` (`poc`, puis `prod`), `francecentral` |
| Storage Account | conteneur privé `plugins` ; accès public désactivé ; versioning de blobs activé (retour arrière) |
| Function App | Flex Consumption, Python 3.11 ; managed identity système avec rôle `Storage Blob Data Reader` sur le conteneur |
| Easy Auth (`authsettingsV2`, via azapi) | provider Entra, `clientId` = app « QGIS », audience `api://80c3a908-…` ; `unauthenticatedClientAction: Return401` |
| App settings | `BETA_GROUP_ID`, `STORAGE_ACCOUNT_URL` |
| Objets Entra (azuread) | app « QGIS » importée (`prevent_destroy`) : scope `plugins.read`, claim groups, pré-autorisation ; groupe `FluxCEN-Beta` ; app CI `fluxcen-ci` |
| Identité CI | federated credentials GitHub OIDC (environnements `release` et `infra`) ; `Storage Blob Data Contributor` sur le conteneur ; Owner sur le resource group |
| Backend d'état | local pour le POC ; standard CEN (landing zones) à brancher avant industrialisation |
