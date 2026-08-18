# Tasks: Système de delivery privé du plugin FluxCEN

**Input**: Design documents from `/specs/002-plugin-delivery/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: inclus (TDD obligatoire par la constitution, Principe II) pour toute la logique Python. L'infrastructure (Bicep, workflows, scripts az) se valide par le protocole de POC du quickstart.

**Organization**: tâches groupées par user story ; chaque story est un incrément testable indépendamment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallélisable (fichiers différents, aucune dépendance sur une tâche inachevée)
- **[Story]**: US1 à US5, mappées sur spec.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: squelette des nouveaux répertoires et outillage, sans logique

- [X] T001 Créer l'arborescence `infra/`, `delivery/function/`, `delivery/provisioning/` conformément au plan (fichiers vides ou stubs minimaux)
- [X] T002 [P] Créer `delivery/function/requirements.txt` (azure-functions, azure-storage-blob, azure-identity) et `delivery/function/host.json`
- [X] T003 [P] Ajouter la configuration d'exclusion du zip de release (infra/, delivery/, tests/, .specify/, .claude/, __pycache__) dans la config `qgis-plugin-ci` (`pyproject.toml`)
- [X] T004 [P] Étendre la config pytest existante pour découvrir `tests/test_delivery_logic.py` (pytest pur, sans QGIS) sans casser la suite pytest-qgis

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: socle Entra + Azure sans lequel aucune story ne fonctionne

- [X] T005 Écrire `infra/entra.tf` (Terraform, provider azuread) : import déclaratif de l'app « QGIS » (`azuread_application_registration`, claim groups, `prevent_destroy`), scope `plugins.read` + identifier URI + pré-autorisation (ressources granulaires), groupe `FluxCEN-Beta`
- [X] T006 Écrire `infra/main.tf` + `versions.tf` + `variables.tf` + `outputs.tf` : resource group `rg-fluxcen-delivery-{env}` (francecentral), Storage Account (conteneur privé `plugins`, versioning), Function App Flex Consumption Python 3.11 (managed identity + rôle `Storage Blob Data Reader`), Easy Auth `authsettingsV2` via azapi (audience `api://80c3a908-…`, `Return401`), app settings `BETA_GROUP_ID` et `STORAGE_ACCOUNT_URL` ; `terraform validate` vert
- [X] T007 Déployer l'environnement POC : `terraform.tfvars` (object id de l'app QGIS), `terraform init && terraform apply` (env=poc) ; consigner l'URL de la Function dans `specs/002-plugin-delivery/quickstart.md`

**Checkpoint**: `curl` sans jeton sur `https://<app>.azurewebsites.net/stable/plugins.xml` répond 401 (Easy Auth actif avant toute ligne de code)

---

## Phase 3: User Story 1 - Mise à jour du plugin avec son compte Microsoft (P1) 🎯 MVP

**Goal**: un agent installe et met à jour FluxCEN depuis QGIS avec son identité Entra, sans saisie ni réglage

**Independent Test**: quickstart.md, vérifications 1, 2 (curl) et parcours QGIS complet sur le canal stable

- [X] T008 [P] [US1] Écrire les tests rouges de la logique de service dans `tests/test_delivery_logic.py` : validation stricte de `{channel}`/`{filename}` (contrat http-delivery.md : motifs admis, 404 sinon, aucune traversée de chemin), mapping canal→préfixe blob, content-type par extension
- [X] T009 [US1] Implémenter `delivery/function/logic.py` (fonctions pures) jusqu'au vert des tests T008
- [X] T010 [US1] Implémenter `delivery/function/function_app.py` : route unique `GET /{channel}/{filename}`, appel de la logique, lecture du blob via managed identity, réponses 200/404 en direct (jamais de 3xx), logs `logging` standard
- [X] T011 [US1] Déployer la Function sur le POC et publier un jeu d'essai dans le blob (`stable/plugins.xml` + un zip FluxCEN 5.3.0) via `az storage blob upload`
- [X] T012 [US1] Valider au terminal : 401 sans jeton, 200 + XML avec jeton (quickstart vérifs 1-2), 404 sur chemin invalide
- [ ] T013 [US1] Valider dans QGIS 3.44 (poste local) puis 3.34 (conteneur `qgis/qgis:3.34` ou installeur LTR archivé, plancher du parc) : authcfg delivery (scope `api://…/plugins.read`), ajout du dépôt stable, chargement de la liste, installation, publication d'une 5.3.1 d'essai, détection et mise à jour en un clic (quickstart parcours QGIS 1-3)
- [ ] T014 [US1] Valider le refresh silencieux : jeton d'accès expiré (~1 h), mise à jour sans prompt (quickstart parcours 4) ; consigner les résultats du POC dans `specs/002-plugin-delivery/quickstart.md`

**Checkpoint**: protocole de POC points 1, 2, 3 (401) et 5 verts → US1 livrable seule (dépôt stable opérationnel)

---

## Phase 4: User Story 3 - Accès beta restreint à un groupe (P2)

**Goal**: le canal beta n'est accessible qu'aux membres du groupe Entra `FluxCEN-Beta`, contrôle côté serveur

**Independent Test**: quickstart vérif 3 : deux comptes (membre / non-membre), 200 vs 403 sur `/beta/plugins.xml`

**Note**: passée avant US2 car elle complète le contrat HTTP que la CI (US2) publiera ; US2 et US3 restent indépendantes

- [X] T015 [P] [US3] Écrire les tests rouges dans `tests/test_delivery_logic.py` : décodage du header `x-ms-client-principal`, extraction des claims `groups`, décision beta (membre → autorisé, non-membre → 403, claim absent → 403, canal stable → toujours autorisé)
- [X] T016 [US3] Implémenter le contrôle beta dans `delivery/function/logic.py` + branchement dans `function_app.py` jusqu'au vert de T015
- [X] T017 [US3] Déployer, publier un `beta/plugins.xml` d'essai (dernière beta seule), ajouter un compte de test au groupe `FluxCEN-Beta`
- [ ] T018 [US3] Valider : membre → 200 sur `/api/beta/plugins.xml` et installation de la préversion dans QGIS (✅ 2026-08-18 : 403 non-membre, 200 membre, 5.4.0-beta.1 `upgradeable`) ; reste : retrait du groupe → 403 après renouvellement du jeton (data-model : effet ≤ 1 h)

**Checkpoint**: protocole de POC point 4 vert → les 5 points du POC sont verts, critère d'arrêt atteint, industrialisation validée

---

## Phase 5: User Story 2 - Publication automatique par les mainteneurs (P2)

**Goal**: un tag `vX.Y.Z(-beta.N)` publie sur le bon canal en < 10 min, zéro secret stocké

**Independent Test**: poser un tag de préversion et un tag final sur un commit de test ; vérifier le contenu des deux catalogues et la release GitHub miroir

- [X] T019 [US2] Écrire `infra/ci.tf` : app `fluxcen-ci` + service principal, federated credentials GitHub OIDC pour les environnements `release` ET `infra`, rôle `Storage Blob Data Contributor` sur le conteneur `plugins`, rôle Owner sur le resource group (apply CI avec role assignments)
- [X] T020 [US2] Écrire `.github/workflows/release.yml` : déclenchement sur tag `v*`, canal déduit du suffixe de version, injection de `config/yaml/links.yaml` depuis le secret `LINKS_YAML` + `asset_paths` qgis-plugin-ci (FR-016), `qgis-plugin-ci package` avec `--plugin-repo-url` du canal, un catalogue par canal (un seul candidat par plugin et par catalogue, contrainte du format vérifiée au POC ; repli beta→stable par fusion multi-dépôts QGIS), upload blob via `azure/login` OIDC (zip d'abord, XML ensuite : publication atomique), `concurrency: {group: release, cancel-in-progress: false}` pour sérialiser les tags rapprochés (edge case spec), release GitHub miroir (`--prerelease` pour les beta)
- [X] T021 [US2] Écrire `.github/workflows/infra.yml` : fmt/validate sur PR, `terraform apply` OIDC (ARM_USE_OIDC) sur main avec approbation (environnement `infra`), garde explicite tant que le backend d'état CEN n'est pas branché
- [ ] T022 [US2] Valider en conteneur puis sur le POC : tag `v5.3.2-beta.1` → seul le catalogue beta bouge ; tag `v5.3.2` → stable et beta à jour ; vérifier l'absence de secret d'authentification dans les réglages du repo (SC-005) et le délai < 10 min (SC-004) ; vérifier que le zip contient `config/yaml/links.yaml` injecté (FR-016). Prérequis : créer le secret `LINKS_YAML` dans l'environnement GitHub `release` (contenu = le links.yaml de production)

**Checkpoint**: publication de bout en bout sans intervention manuelle après le tag

---

## Phase 6: User Story 4 - Provisioning des postes sans manipulation (P3)

**Goal**: un poste Intune est opérationnel au premier lancement de QGIS

**Independent Test**: contrat provisioning.md, section Tests + exécution sur un poste vierge

- [X] T023 [P] [US4] Écrire les tests rouges dans `tests/test_provisioning.py` (pytest-qgis) : poste vierge → postconditions 1-3 du contrat ; ré-exécution → aucune écriture ; port 17070 occupé → repli ; authcfg au scope erroné → réparé sans toucher aux autres authcfg
- [X] T024 [US4] Implémenter `delivery/provisioning/provision.py` (logique pure : construction authcfg, sonde de port par bind, comparaison d'état, enregistrement des dépôts dans `QgsSettings`) jusqu'au vert de T023
- [X] T025 [US4] Implémenter `delivery/provisioning/startup.py` : appel de `provision.py` sous try/except intégral, journalisation `QgsMessageLog` onglet FluxCEN, aucune exception propagée (contrat : innocuité)
- [X] T026 [US4] Documenter et packager le déploiement Intune dans `delivery/provisioning/README.md` : copie vers `profiles/default/python/startup.py`, activation beta par fichier marqueur, procédure de retrait ; plan B plugin bootstrap zip mentionné
- [ ] T027 [US4] Valider sur un poste réel géré : premier lancement → dépôt présent et fonctionnel sans manipulation (SC-007) ; poste avec AnyDesk (port 7070/17070 occupé) → repli vérifié

**Checkpoint**: US4 livrable ; l'embarquement d'un agent ne demande plus aucune action manuelle

---

## Phase 7: User Story 5 - Infrastructure reproductible (P3)

**Goal**: tout le système se recrée depuis le code versionné, prérequis exclus

**Independent Test**: quickstart nettoyage + redéploiement, puis re-parcours US1

- [X] T028 [US5] Rédiger `infra/README.md` : prérequis exhaustifs (souscription, outils, backend d'état CEN, import de l'app QGIS), procédure de déploiement env POC et prod, procédure de destruction (précaution `state rm` sur l'app importée)
- [ ] T029 [US5] Valider SC-006 : `terraform destroy` du POC (après `state rm` de l'app QGIS importée), recréation complète par `terraform apply` + re-publication d'un artefact + re-parcours du quickstart US1, chronométré < 1 h ; corriger le Terraform si une étape manuelle non documentée apparaît
- [ ] T030 [US5] Valider la réparation de dérive : modification manuelle d'un réglage au portail (ex. app setting), `terraform apply` → état restauré (acceptance US5 scénario 2)

**Checkpoint**: environnement jetable prouvé ; le POC peut être promu en prod par simple changement de paramètre

---

## Phase 8: Polish & Migration

**Purpose**: bascule des utilisateurs existants et mise en conformité documentaire (FR-015, SC-008)

- [ ] T031 Déployer l'environnement prod (`env=prod`) via `infra.yml` et re-dérouler les vérifications curl du quickstart
- [ ] T032 Publier sur l'ancienne URL publique (`sig.dsi-cen.org/qgis/`) une version de transition dont la description et le changelog pointent vers la nouvelle procédure d'installation
- [ ] T033 Amender la constitution (PR dédiée) : contrainte « Distribution » vers l'URL du dépôt privé ; incrément MINEUR (le Principe VI a déjà été amendé en v1.2.0 : plancher transitoire 3.34)
- [ ] T034 Décommissionner l'ancienne URL après la période de transition annoncée ; vérifier SC-008 (plus aucun téléchargement) puis retirer la version de transition
- [ ] T035 [P] Nettoyage final : `pylint` vert sur tout le nouveau code Python, suite pytest + pytest-qgis verte en conteneur `qgis/qgis:3.34` (plancher, constitution v1.2.0) et `qgis/qgis:3.44` en complément, aucun fichier de dev dans le zip de release (inspection du zip produit par T020)

---

## Dependencies & Execution Order

- **Phase 1 → Phase 2 → Phase 3 (US1)** : chaîne bloquante. Rien ne se teste sans le socle Entra/Azure.
- **Phase 4 (US3)** dépend de Phase 3 (la Function existe). **Phase 5 (US2)** dépend de Phase 2 seulement : T019-T021 peuvent s'écrire en parallèle de Phase 3/4, la validation T022 attend T011.
- **Phase 6 (US4)** dépend de Phase 3 (une URL de dépôt stable à enregistrer). Indépendante de US2/US3.
- **Phase 7 (US5)** dépend de Phase 2 ; sa validation complète (T029) est plus probante après Phase 5.
- **Phase 8** dépend de toutes les autres.

```text
Setup (T001-T004)
  └─ Foundational (T005-T007)
       ├─ US1 (T008-T014) ── US3 (T015-T018)
       ├─ US2 rédaction (T019-T021) ── US2 validation (T022, après T011)
       ├─ US4 (T023-T027, après T011)
       └─ US5 (T028-T030)
            └─ Polish & Migration (T031-T035)
```

## Parallel Opportunities

- **Setup** : T002, T003, T004 en parallèle après T001.
- **Après T007** : T008 (tests US1), T019-T021 (workflows US2) et T028 (doc US5) en parallèle.
- **Tests d'abord, en parallèle des autres stories** : T015 (US3) et T023 (US4) sont des fichiers de tests distincts, rédigeables pendant l'implémentation d'US1.

## Implementation Strategy

**MVP = Phase 1 + 2 + 3 (US1)** : dépôt stable authentifié opérationnel dans QGIS. C'est le cœur du POC ; s'il échoue de façon insoluble, activer le plan B SharePoint `/$value` (research.md R2) sans avoir écrit US2-US5.

Ensuite, ordre de valeur : US3 (clôt le protocole de POC 5/5), US2 (supprime les manipulations de release), US4 (industrialise l'embarquement), US5 (prouve la reproductibilité), migration.

## Format Validation

- Toutes les tâches suivent `- [ ] TNNN [P?] [USn?] description + chemin de fichier`.
- Labels story présents uniquement dans les phases US (T008-T030), absents en Setup/Foundational/Polish.
