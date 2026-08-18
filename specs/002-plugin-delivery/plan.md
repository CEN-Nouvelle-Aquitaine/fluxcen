# Implementation Plan: Système de delivery privé du plugin FluxCEN

**Branch**: `002-plugin-delivery` | **Date**: 2026-08-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-plugin-delivery/spec.md`

## Summary

Distribuer FluxCEN via un dépôt de plugins QGIS privé servi par une Azure Function derrière Easy Auth (Entra ID, Bearer). Deux canaux (interne, beta) ; la beta est restreinte par groupe Entra via le claim `groups`. Publication par tag depuis le dépôt GitHub privé (OIDC, zéro secret). Toute l'infrastructure est en IaC Terraform (standard des projets CEN récents ; le provider azuread absorbe aussi les objets Entra). Le provisioning des postes passe par un `startup.py` déployé par Intune. Un POC valide la chaîne complète (auth, catalogue, zip, restriction beta) avant industrialisation. Ce choix découle de la recherche (voir research.md) : le branchement direct SharePoint/Graph est écarté à cause du rejeu du header Bearer sur la redirection 302 et de l'absence de suivi des 302 en QGIS 3.34.

## Technical Context

**Language/Version**: Python 3.11 (Azure Function, modèle v2) ; Python ≥ 3.9 embarqué QGIS (startup.py) ; Terraform ≥ 1.7 (IaC : providers azurerm, azuread, azapi) ; YAML (GitHub Actions)

**Primary Dependencies**: `azure-functions` (runtime Function) ; PyQGIS uniquement pour `startup.py` ; `qgis-plugin-ci` + `qgis-plugin-repo` (CI seulement) ; aucune dépendance nouvelle dans le plugin lui-même

**Storage**: Azure Blob Storage (conteneur privé : zips + `plugins.xml` par canal), lu par la Function via managed identity

**Testing**: `pytest` pour la logique de la Function (autorisation par canal, parsing du principal, validation de chemin) ; `pytest` + `pytest-qgis` pour la logique du provisioning ; POC manuel scripté (quickstart.md)

**Target Platform**: Azure Functions Flex Consumption, région `francecentral` ; clients QGIS ≥ 3.34 sous Windows/macOS/Linux ; postes gérés par Intune

**Project Type**: infrastructure + micro-service HTTP + script de provisioning client (monorepo avec le plugin)

**Performance Goals**: négligeables : < 200 utilisateurs, artefacts de quelques Mo, quelques releases par mois. Le plan Flex Consumption absorbe cela dans la franchise gratuite

**Constraints**: une seule audience de jeton par authcfg (audience = API custom de l'app « QGIS » existante) ; réponses en 200 direct, jamais de redirection (QGIS 3.34 ne suit pas les 302 sur `plugins.xml`) ; pas de query string dans l'URL de dépôt (QGIS concatène `?qgis=x.y`) ; aucun secret de longue durée en CI (OIDC) ; la vérification des dépôts au démarrage de QGIS reste désactivée (défaut QGIS #64885)

**Scale/Scope**: 2 canaux, 1 Function, 1 compte de stockage, 1 resource group ; ~150 postes à provisionner ; POC sur un resource group dédié détruit/recréé à volonté

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Verdict | Justification |
|---|---|---|
| I. Intégration native QGIS | PASS | `startup.py` n'utilise que PyQGIS (`QgsAuthMethodConfig`, `QgsSettings`, `QgsApplication.authManager()`). Le téléchargement des plugins est fait par le gestionnaire d'extensions de QGIS lui-même (`QgsNetworkAccessManager` + authcfg). Le code de la Function est hors périmètre QGIS (côté serveur) : le principe I ne lui impose rien. |
| II. TDD | PASS | Logique de la Function (choix de canal, contrôle du groupe beta, validation des chemins) écrite en fonctions pures testées par pytest avant implémentation. Logique du provisioning (idempotence, sonde de port, construction de l'authcfg) testée avec pytest-qgis. Les tests tournent en CI sur l'image `qgis/qgis`. |
| III. Architecture en couches | PASS | Function : logique pure séparée du handler HTTP. `startup.py` : logique pure séparée des appels QGIS. |
| IV. Sécurité et secrets | PASS | Aucun secret : OIDC en CI, managed identity Function→Blob, PKCE côté client, authcfg géré par `QgsAuthManager`. HTTPS partout. Le contrôle beta est appliqué côté serveur (claim `groups` du jeton validé par Easy Auth). |
| V. YAGNI | PASS | Une seule Function, pas d'APIM, pas de framework web, pas de base de données. Le catalogue est un fichier statique en blob. L'ajout d'un composant serveur est justifié dans Complexity Tracking. |
| VI. Compatibilité | PASS | Constitution amendée en v1.2.0 (2026-08-18) : plancher transitoire 3.34 entériné (mise à niveau du parc vers 3.44 prévue mais non achevée). La conception (200 direct, pas de redirection) fonctionne dès 3.34. |
| VII. Qualité et observabilité | PASS | Function : `logging` standard vers Application Insights (inclus Flex). `startup.py` : `QgsMessageLog` onglet FluxCEN. Messages utilisateur en français. |
| Contrainte « Distribution » | AMENDEMENT REQUIS | La constitution nomme `https://sig.dsi-cen.org/qgis/` comme dépôt de distribution. Cette feature le remplace. L'amendement de la constitution fait partie de la phase de migration (FR-015), pas du POC. |

**Verdict global** : GATE PASS. Reste un point au suivi : amendement de la contrainte « Distribution » (nouvelle URL) à faire lors de la migration (T033) ; le Principe VI a été amendé en v1.2.0.

## Project Structure

### Documentation (this feature)

```text
specs/002-plugin-delivery/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
infra/
├── versions.tf                 # providers azurerm/azuread/azapi, backend (standard CEN à brancher)
├── variables.tf / outputs.tf
├── main.tf                     # resource group, storage, Function Flex, Easy Auth (azapi), rôles
├── entra.tf                    # app « QGIS » importée (granulaire : scope plugins.read, claim groups), groupe beta
├── ci.tf                       # app fluxcen-ci, federated credentials OIDC GitHub, rôles CI
└── terraform.tfvars.example

delivery/
├── function/
│   ├── function_app.py         # handler HTTP unique GET /{channel}/{filename}
│   ├── logic.py                # fonctions pures : autorisation canal, parsing principal, validation chemin
│   ├── host.json
│   └── requirements.txt        # azure-functions, azure-storage-blob, azure-identity
└── provisioning/
    ├── startup.py              # déployé par Intune dans le profil QGIS ; importe provision.py
    └── provision.py            # logique pure : authcfg delivery, enregistrement dépôts, sonde de port, idempotence

.github/workflows/
├── release.yml                 # tag → build zip (qgis-plugin-ci) → plugins.xml du canal → upload blob (OIDC)
└── infra.yml                   # déploiement Bicep sur changement de infra/ (OIDC, environnement approuvé)

tests/
├── test_delivery_logic.py      # pytest pur (logique Function)
└── test_provisioning.py        # pytest-qgis (logique provisioning)
```

**Structure Decision**: monorepo. Le plugin reste à la racine (layout existant inchangé) ; l'infra et le code de delivery vivent dans `infra/` et `delivery/`. Le zip de release exclut `infra/`, `delivery/`, `tests/`, `.specify/`, `.claude/` conformément à la contrainte de distribution de la constitution (configuration d'exclusion de `qgis-plugin-ci`).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Ajout d'un composant serveur (Azure Function) là où un hébergement statique suffisait jusqu'ici | Seul moyen de servir un dépôt de plugins à un client non-navigateur en Bearer Entra avec restriction par groupe : Easy Auth valide le jeton, la Function applique le contrôle beta côté serveur et répond en 200 direct | SharePoint/Graph direct (zéro infra) rejeté : Graph répond 302 vers une URL pré-signée, QGIS rejoue le header Bearer sur la redirection (401 « invalid audience » attendu) et QGIS 3.34 ne suit pas les 302 sur plugins.xml ; Blob direct rejeté (audience storage + header `x-ms-version` que QGIS n'envoie pas) ; Basic auth sur serveur web rejeté (gestion de mots de passe hors Entra, contraire à l'objectif SSO). Piste SharePoint REST `/$value` (200 direct, audience SPO) conservée en plan B documenté dans research.md, non retenue car jamais éprouvée publiquement avec le plugin manager |
| Provider `azapi` en plus d'azurerm/azuread (une seule ressource : `authsettingsV2`) | `azurerm` ne porte pas encore `auth_settings_v2` sur `azurerm_function_app_flex_consumption` ; l'Easy Auth est le cœur du système | Attendre le support natif laisserait le POC sans authentification ; configurer l'auth hors IaC violerait FR-011. À migrer vers le bloc natif dès disponibilité |
