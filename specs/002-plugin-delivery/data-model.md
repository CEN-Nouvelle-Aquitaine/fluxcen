# Data Model: Système de delivery privé du plugin FluxCEN

**Date**: 2026-08-18 | **Plan**: [plan.md](plan.md)

Aucune base de données. L'état du système vit dans quatre supports : le Blob Storage (catalogues et artefacts), Entra ID (identités et groupe), la configuration de la Function (Bicep), et le poste QGIS (authcfg + dépôts enregistrés).

## Dépôt (unique, révisé 2026-08-18)

| Champ | Type | Règles |
|---|---|---|
| segment d'URL | `stable` | Seule valeur admise (nom historique du canal unique) ; tout autre segment → 404 |
| préfixe blob | chemin | `stable/` dans le conteneur `plugins` (catalogue + tous les zips, préversions incluses) |
| règle d'accès | politique | toute identité du tenant validée par Easy Auth ; les préversions sont en opt-in client (flag `experimental`), aucun contrôle serveur supplémentaire |

## Catalogue (`plugins.xml`)

Un par canal, stocké en blob (`{canal}/plugins.xml`). Format : XML du dépôt de plugins QGIS.

| Champ XML | Règles |
|---|---|
| `name` | `FluxCEN` (constant) |
| `version` | SemVer `x.y.z` ou `x.y.z-beta.n` ; ordre PEP 440 respecté par QGIS |
| `download_url` | URL absolue de la Function : `https://{host}/api/{canal}/FluxCEN.{version}.zip` (préfixe `/api` standard Azure Functions) ; jamais de query string |
| `qgis_minimum_version` | `3.34` (aligné sur `metadata.txt`) |
| `experimental` | `False` pour les versions finales, `True` pour les préversions (posé automatiquement par qgis-plugin-ci sur les suffixes pré-release) |

Invariants (corrigés au POC du 2026-08-18) :
- Le catalogue porte **au plus deux entrées** pour FluxCEN : une stable (`experimental=False`) et une préversion (`experimental=True`, flaguée automatiquement par qgis-plugin-ci). C'est la paire prévue par le format de dépôt QGIS (standard communautaire).
- Une release ne remplace que l'entrée de sa nature (fusion `qgis-plugin-repo merge` avec le catalogue existant).
- QGIS propose la version la plus haute visible : les préversions n'apparaissent qu'avec l'option « extensions expérimentales » cochée.
- Toute version listée a son zip présent dans le même préfixe (publication atomique : zip d'abord, XML ensuite).

## Artefact

| Champ | Règles |
|---|---|
| nom de blob | `{canal}/FluxCEN.{version}.zip` |
| contenu | zip du plugin, sans `__pycache__`, `tests/`, `infra/`, `delivery/`, `.specify/`, `.claude/` ; AVEC `config/yaml/links.yaml` injecté par la CI à la publication (FR-016 : artefact auto-suffisant, fichier jamais versionné) |
| version | identique à `metadata.txt` du zip et au tag Git (`v` retiré) |
| immuabilité | un zip publié n'est jamais réécrit ; republier une version = nouveau tag correctif |

## Groupe FluxCEN-Beta (liste de diffusion)

| Champ | Règles |
|---|---|
| objet | groupe Entra `FluxCEN-Beta` (Terraform), **communication uniquement** : annonces aux testeurs |
| rôle technique | aucun depuis la révision 2026-08-18 (plus de claim `groups`, plus de `BETA_GROUP_ID`) |

## Configuration de poste (provisioning)

| Élément | Règles |
|---|---|
| authcfg « FluxCEN delivery » | OAuth2 Authorization Code PKCE, app `80c3a908-…`, tenant CEN, scope `api://80c3a908-…/plugins.read offline_access`, secret vide, jeton persistant, redirect `127.0.0.1:{port}/qgis-client` |
| port de redirect | 17070 par défaut ; si occupé (sonde bind), repli sur le premier libre d'une liste fixe ; Entra ignore le port des URI loopback (RFC 8252), aucun changement portail |
| distinction | authcfg distinct de l'authcfg Graph du plugin (feature 001, scope `Files.Read.All`) : une audience par authcfg, même app registration |
| dépôt enregistré | `QgsSettings` `app/plugin_repositories/FluxCEN (interne)` → `https://{host}/api/stable/plugins.xml` + authcfg ; l'ancien dépôt beta du POC est retiré s'il existe |
| check au démarrage | `checkOnStart` laissé à `false` (défaut QGIS #64885) |
| idempotence | ré-exécution sans effet si l'état est conforme ; répare authcfg ou dépôts dérivés ; ne touche à rien d'autre |

## Configuration d'infrastructure (Terraform : azurerm + azuread + azapi)

| Ressource | Points clés |
|---|---|
| Resource group | `rg-fluxcen-delivery-{env}` (`poc`, puis `prod`), `francecentral` |
| Storage Account | conteneur privé `plugins` ; accès public désactivé ; versioning de blobs activé (retour arrière) |
| Function App | Flex Consumption, Python 3.11 ; managed identity système avec rôle `Storage Blob Data Reader` sur le conteneur |
| Easy Auth (`authsettingsV2`, via azapi) | provider Entra, `clientId` = app « QGIS », audience `api://80c3a908-…` ; `unauthenticatedClientAction: Return401` |
| App settings | `STORAGE_ACCOUNT_URL` |
| Objets Entra (azuread) | app « QGIS » importée (`prevent_destroy`) : scope `plugins.read`, pré-autorisation ; groupe `FluxCEN-Beta` (diffusion) ; app CI `fluxcen-ci` |
| Identité CI | federated credentials GitHub OIDC (environnements `release` et `infra`) ; `Storage Blob Data Contributor` sur le conteneur ; Owner sur le resource group |
| Backend d'état | local pour le POC ; standard CEN (landing zones) à brancher avant industrialisation |
