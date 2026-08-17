# Tasks: Support des liens de partage SharePoint et restriction de l'auth Microsoft

**Input**: Design documents from `/specs/001-sharepoint-share-urls/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: inclus et obligatoires — le TDD est non négociable (Constitution, Principe II). Chaque tâche de
test doit être écrite et **échouer** avant la tâche d'implémentation correspondante.

**Organization**: tâches groupées par user story (US1 = liens de partage, US2 = restriction d'auth,
US3 = diagnostic/robustesse), chacune livrable et testable indépendamment.

**Révision 2026-07-27** : intègre les remédiations de `/speckit-analyze` validées par l'utilisateur —
liens de partage de **dossier** pour les styles (U1), gate CI pylint bloquante (C1), sort des URL
`data:` précisé (I1), critère de test « aucun réseau à l'import » opérationnalisé (A1).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallélisable (fichiers différents, aucune dépendance sur une tâche inachevée)
- **[Story]**: US1 / US2 / US3 (traçabilité vers spec.md)

## Path Conventions

Plugin QGIS à plat (le dépôt est le plugin) : code à la racine (`FluxCEN.py`), logique pure dans `core/`,
tests dans `tests/` — cf. plan.md « Project Structure ».

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: infrastructure de test et squelette du package de logique pure

- [X] T001 Créer le package `core/` avec `core/__init__.py` vide (aucun import qgis autorisé dans ce package)
- [X] T002 Créer l'infrastructure de test : `tests/__init__.py`, `tests/conftest.py` (fixtures pytest-qgis), `tests/data/` avec un `flux_minimal.csv` (3 lignes : WMS, WFS, PostGIS) et un `links_test.yaml`, et la configuration pytest dans `pyproject.toml` (testpaths, markers `unit`/`integration`)
- [X] T003 [P] Rendre la CI bloquante dans `.github/workflows/quality.yml` : ajouter le job de tests (conteneur `qgis/qgis:3.44`, `pip3 install pytest pytest-qgis`, `pytest tests/`) **sans** `continue-on-error`, et retirer `continue-on-error: true` du job pylint existant (gate constitutionnelle lint + tests)

**Checkpoint**: `pytest tests/` s'exécute (0 test collecté) en local et en CI ; pylint bloquant

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: classification d'URL du périmètre Microsoft — socle partagé par US1 (conversion) et US2
(filtrage d'auth)

**⚠️ CRITICAL**: aucune user story ne peut démarrer avant la fin de cette phase

- [X] T004 Écrire les tests unitaires **échouants** de `is_microsoft_url()` et `classify_url()` dans `tests/test_ms_urls.py` : cas nominaux (`https://graph.microsoft.com/…`, `https://<tenant>.sharepoint.com/…`, `https://<tenant>-my.sharepoint.com/…`) et cas hostiles du contrat (`http://`, `data:`, `sharepoint.com.evil.tld`, `notsharepoint.com`, `https://sharepoint.com@evil.tld/`, casse mixte, chaîne vide, URL malformée → jamais d'exception)
- [X] T005 Implémenter `is_microsoft_url()`, `classify_url()` et l'enum `UrlClass` dans `core/ms_urls.py` (stdlib uniquement, `urllib.parse.urlsplit`) jusqu'au vert de T004, conformément à `contracts/core-functions.md`

**Checkpoint**: fondation prête — les user stories peuvent démarrer (en parallèle si besoin)

---

## Phase 3: User Story 1 - Configurer une ressource avec un lien de partage SharePoint (Priority: P1) 🎯 MVP

**Goal**: un lien « Copier le lien » SharePoint collé dans `links.yaml` est résolu et téléchargé de façon
transparente via l'API Graph et l'authcfg QGIS — fichier unique (catalogue, changelog, version) comme
dossier partagé (styles) ; les URL Graph historiques restent fonctionnelles.

**Independent Test**: configurer `github_urls.flux_csv` avec un lien de partage du tenant CEN, ouvrir le
plugin, vérifier que les catégories de flux s'affichent (quickstart.md, étapes 1-4).

### Tests for User Story 1 (écrits d'abord, échouants)

- [X] T006 [P] [US1] Compléter `tests/test_ms_urls.py` avec les tests **échouants** de `is_sharepoint_sharing_link()`, `sharing_link_to_graph_url()` et `sharing_link_to_graph_item_url()` : encodage `u!` + base64url non paddé vérifié sur un exemple connu, paramètres `?d=…&csf=1&web=1` conservés dans l'encodage, adressage par chemin `…/driveItem:/<nom>.qml:/content` avec percent-encoding du nom, `ValueError` sur URL hors SharePoint et sur nom de fichier contenant `/`, `\` ou `..`, propriété « le retour satisfait `is_microsoft_url` »
- [X] T007 [P] [US1] Écrire les tests d'intégration **échouants** de la résolution dans `tests/test_fetch.py` : `_fetch_bytes` sur un lien de partage convertit l'URL avant la requête et ajoute l'en-tête `Prefer: redeemSharingLinkIfNecessary` ; une URL Graph directe part inchangée (monkeypatch de `QgsBlockingNetworkRequest.get` pour capturer la `QNetworkRequest` émise)

### Implementation for User Story 1

- [X] T008 [US1] Implémenter `is_sharepoint_sharing_link()`, `sharing_link_to_graph_url()` et `sharing_link_to_graph_item_url()` dans `core/ms_urls.py` jusqu'au vert de T006
- [X] T009 [US1] Modifier `_fetch_bytes()` dans `FluxCEN.py` (~ligne 499) : classification de l'URL via `core.ms_urls.classify_url`, conversion des liens de partage en URL Graph, en-tête `Prefer: redeemSharingLinkIfNecessary` sur les URL converties, jusqu'au vert de T007 (le comportement authcfg existant est conservé tel quel — le filtrage est US2)
- [X] T010 [US1] Adapter la construction des URL de style dans `FluxCEN.py` (`parse_table_row`/`chargement_flux`, ~ligne 858) : si `styles_couches` est un lien de partage SharePoint → `sharing_link_to_graph_item_url(styles_couches, nom_style + ".qml")`, sinon concaténation historique ; couvert par les tests de T006 + un cas d'intégration dans `tests/test_fetch.py`
- [X] T011 [P] [US1] Mettre à jour `config/yaml/links_example.yaml` : documenter le collage direct d'un lien de partage (fichier et dossier pour les styles, exemples de `contracts/links-yaml.md`), conserver l'exemple Graph historique en variante, signaler que le nom de clé `github_urls` est historique

**Checkpoint**: MVP — un lien de partage collé fonctionne de bout en bout, les URL Graph restent valides

---

## Phase 4: User Story 2 - L'auth Microsoft ne sort jamais du périmètre Microsoft (Priority: P1)

**Goal**: l'authcfg Microsoft n'accompagne que les requêtes vers `graph.microsoft.com` / `*.sharepoint.com`
(ressources ET couches WMS/WFS) ; HTTPS obligatoire pour toute requête authentifiée.

**Independent Test**: configuration mélangeant URL SharePoint et URL publiques → seules les requêtes
Microsoft portent l'auth ; ajout d'une couche WMS tierce → aucune authcfg dans l'URI (quickstart.md,
étapes 5-6).

### Tests for User Story 2 (écrits d'abord, échouants)

- [X] T012 [P] [US2] Compléter `tests/test_fetch.py` avec les tests **échouants** du filtrage : `setAuthCfg` appelé pour URL Graph/SharePoint avec authcfg non vide ; jamais appelé pour `raw.githubusercontent.com` ni domaine trompeur ; URL `http://` → exception explicite sans requête émise ; URL `data:` tolérée, traitée sans authentification (FR-006 précisé)
- [X] T013 [P] [US2] Écrire les tests unitaires **échouants** du parsing catalogue dans `tests/test_catalog.py` : 10 colonnes conformes au data-model, ligne à service inconnu ignorée sans exception, nom de style contenant `/`, `\` ou `..` rejeté (traité comme absent), lignes PostGIS sans bdd/schéma ignorées
- [X] T014 [P] [US2] Écrire les tests **échouants** des handlers de couches dans `tests/test_layers.py` : l'URI produite par la construction de couche WMS et WFS ne contient jamais `authcfg` pour un domaine hors périmètre Microsoft (fixtures pytest-qgis, couche non résolue acceptable — on teste l'URI)

### Implementation for User Story 2

- [X] T015 [US2] Implémenter le filtrage dans `_fetch_bytes()` (`FluxCEN.py`) : `setAuthCfg` uniquement si `is_microsoft_url(url_finale)` et authcfg non vide ; rejet des URL `http:` avant toute requête ; `data:` traité sans auth ; jusqu'au vert de T012
- [X] T016 [US2] Créer `core/catalog.py` : déplacer et adapter `parse_table_row` (`FluxCEN.py:841-866`) et le parsing des catégories, avec validation du data-model (service, colonnes, nom de style) jusqu'au vert de T013
- [X] T017 [US2] Brancher `core/catalog.py` dans `FluxCEN.py` : `initialisation_flux()` (~ligne 567) et `chargement_flux()` (~ligne 806) consomment `parse_catalog`/`parse_table_row` du nouveau module ; supprimer le code déplacé
- [X] T018 [US2] Supprimer l'attachement indiscriminé de la première authcfg dans `handle_wms_layer` (`FluxCEN.py:887-894`) et `handle_wfs_layer` (`FluxCEN.py:931-937`) — les couches WMS/WFS se chargent sans authcfg (research.md R4) ; jusqu'au vert de T014

### Amendement 2026-07-27 — FR-011 : PostGIS ne reçoit jamais l'auth Microsoft (découvert en T028)

- [X] T029 [US2] Écrire les tests **échouants** de FR-011 : test pur de `is_database_auth_method()` dans `tests/test_ms_urls.py` (`OAuth2` → False ; `Basic`, `PKI-Paths` → True) et tests d'intégration dans `tests/test_postgis_auth.py` — `apply_authentication_if_needed()` avec un gestionnaire d'auth factice : config OAuth2 seule → aucune authcfg sur l'URI ; config par défaut QSettings pointant vers OAuth2 → ignorée ; config Basic → appliquée
- [X] T030 [US2] Implémenter FR-011 : `is_database_auth_method()` dans `core/ms_urls.py`, helper `_database_auth_configs()` dans `FluxCEN.py` filtrant `availableAuthMethodConfigs()` par méthode, utilisé par `apply_authentication_if_needed()` (défaut inadapté ignoré + log) et par `choose_default_authentication()` (le dialogue ne propose plus les configs web) ; jusqu'au vert de T029

### Amendement revue de code 2026-07-27 — FR-012 et corrections

- [X] T031 [US2] Écrire les tests **échouants** de FR-012 : `is_cen_secured_service()` dans `tests/test_catalog.py` (hôte `opendata.cen-nouvelle-aquitaine.org` → True ; geopf/évil/http → False) et `build_wms_uri(..., authcfg=)` (paramètre présent ssi fourni)
- [X] T032 [US2] Implémenter FR-012 : `is_cen_secured_service()` + paramètre `authcfg` de `build_wms_uri()` dans `core/catalog.py` ; `_select_service_authcfg()` extrait de `apply_authentication_if_needed()` dans `FluxCEN.py` ; `handle_wms_layer`/`handle_wfs_layer` attachent la config sélectionnée uniquement pour le périmètre sécurisé CEN ; jusqu'au vert de T031
- [X] T033 [US3] Écrire les tests **échouants** des corrections de la revue : nouvel essai du catalogue à l'ouverture suivante après échec (finding 1) ; `initialisation_flux` sans exception sur catégorie inexistante/catalogue vide et correspondance avec cellules non normalisées (finding 3) ; en-tête `Prefer` sur toute URL Graph `/shares/` y compris pré-convertie (finding 5) ; rejet `ftp://`/`file://` sans requête et sans userinfo dans le message (finding 6) ; `parse_version()` (finding 10)
- [X] T034 [US3] Implémenter les corrections : retry du catalogue tant que non obtenu ; réécriture du peuplement du tableau (garde liste vide, correspondance strip, URL de métadonnées de la bonne ligne — finding 4, tooltip unifié) ; en-tête `Prefer` par détection d'URL `/shares/` ; garde de schéma via analyse d'URL (https/data uniquement, nom d'hôte sans userinfo) ; `parse_version()` dans `core/catalog.py` remplaçant l'index 8 en dur ; clarification du mode anonyme dans `links_example.yaml` (finding 7) ; jusqu'au vert de T033

### Amendement revue de PR #55 (2026-08-17) — extraction `core/layer_builder.py`

- [X] T037 Extraire la construction de couches de `core/catalog.py` vers `core/layer_builder.py` (`build_wms_uri`, `build_wfs_uri_params`, `extract_service_version`, `is_cen_secured_service`) : `catalog.py` reste limité au parsing du CSV (issue #52). Tests déplacés vers `tests/test_layers.py`, contrats et plan mis à jour, comportement inchangé
- [X] T038 Découverte automatique de la configuration Microsoft dans le gestionnaire d'auth QGIS (issue #39) : `select_web_authcfg()` dans `core/ms_urls.py` (tests purs), `_authcfg_id()` interroge le gestionnaire au lieu d'exiger `auth.authcfg` dans links.yaml (la clé reste une surcharge optionnelle, tests d'intégration dans `tests/test_fetch.py`) ; message `AUTH_MANQUANTE` ramené à la seule action à portée de l'utilisateur (data-model) ; contrats et `links_example.yaml` mis à jour

### Amendement 2026-07-27 (validation T028) — résolution des dossiers partagés en 2 étapes

- [X] T035 [US1] Écrire les tests **échouants** de la résolution 2 étapes (l'adressage par chemin sous `/shares` est rejeté par Graph, constaté sur le tenant réel) : `sharing_link_to_graph_metadata_url`/`parse_drive_item_ref`/`drive_item_child_content_url` dans `tests/test_ms_urls.py` (dont nom à espace « RPG _2024.qml » et réponses JSON hostiles), `_style_url` dans `tests/test_fetch.py` (deux étapes, cache de session, URL directe sans réseau)
- [X] T036 [US1] Implémenter : les trois fonctions pures dans `core/ms_urls.py` (remplacent `sharing_link_to_graph_item_url`), `FluxCEN._style_url()` avec cache `(driveId, itemId)`, échec de résolution non bloquant (couche chargée sans style + log) ; jusqu'au vert de T035

**Checkpoint**: US1 et US2 fonctionnent indépendamment — aucun jeton hors périmètre Microsoft, aucune
config Microsoft sur les connexions base de données, couches sécurisées CEN authentifiées (non web)

---

## Phase 5: User Story 3 - Diagnostic clair en cas d'échec (Priority: P2)

**Goal**: messages d'erreur français par famille (lien invalide / accès refusé / réseau / auth manquante),
aucun réseau au démarrage de QGIS, un échec de téléchargement n'empêche jamais le chargement du plugin.

**Independent Test**: lien invalide, fichier non partagé, réseau coupé → trois messages distincts, plugin
chargé dans tous les cas (quickstart.md, « Cas d'erreur à rejouer »).

### Tests for User Story 3 (écrits d'abord, échouants)

- [X] T019 [P] [US3] Écrire les tests unitaires **échouants** de la classification d'erreurs dans `tests/test_errors.py` : mapping (code HTTP, contexte) → famille (`LIEN_INVALIDE` 400/404, `ACCES_REFUSE` 401/403, `RESEAU` timeout/DNS, `AUTH_MANQUANTE` périmètre Microsoft sans authcfg) et vérification que le message produit ne contient ni jeton ni URL complète (nom d'hôte seul)
- [X] T020 [P] [US3] Écrire le test d'intégration **échouant** de robustesse au démarrage dans `tests/test_startup.py` : (a) monkeypatch de `QgsBlockingNetworkRequest` levant à tout appel, posé **avant** `importlib.reload` du module `FluxCEN` → l'import ne déclenche aucune requête et n'importe plus `socket` ; (b) instanciation du plugin + `initGui` (fixtures pytest-qgis, `iface` mocké) avec `_fetch_bytes` levant systématiquement → aucune exception ne s'échappe

### Implementation for User Story 3

- [X] T021 [US3] Créer `core/errors.py` : familles d'erreurs et `classify_error()` + construction des messages français du data-model, jusqu'au vert de T019
- [X] T022 [US3] Supprimer le réseau du chargement dans `FluxCEN.py` : retirer le test de connectivité `socket` au niveau module (~lignes 48-58) et son import ; déplacer les fetchs de `__init__` (~lignes 162, 178) vers le premier `run()` ; envelopper chaque fetch dans try/except → famille d'erreur + barre de message ; jusqu'au vert de T020
- [X] T023 [US3] Mettre en cache mémoire le catalogue dans `FluxCEN.py` : `initialisation_flux()` (~ligne 573) réutilise le CSV téléchargé une fois par session au lieu de re-télécharger à chaque changement de catégorie
- [X] T024 [US3] Journalisation : helper `QgsMessageLog` (onglet « FluxCEN ») dans `FluxCEN.py`, remplacement des `print()` sur les chemins modifiés (dont `chargement_flux` ~lignes 836-838), gestion du cas `AUTH_MANQUANTE` (authcfg vide + URL Microsoft → message d'orientation, pas de requête)

**Checkpoint**: les trois user stories sont indépendamment fonctionnelles

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: conformité constitution, métadonnées de release, validation finale

- [X] T025 [P] Mettre à jour `metadata.txt` : `qgisMinimumVersion=3.44`, version plugin incrémentée en MINEUR (5.2 → 5.3), `changelog` décrivant liens de partage + restriction d'auth (TODO constitutionnel soldé)
- [X] T026 [P] Passer `pylint` (config `pylintrc` du dépôt) sur `FluxCEN.py`, `core/` et `tests/` — aucune nouvelle violation
- [X] T027 Vérifier la couverture des exigences : chaque FR-001…FR-010 de spec.md tracée vers au moins un test vert ; compléter les tests manquants le cas échéant
- [ ] T028 Dérouler la validation manuelle de `quickstart.md` (bout en bout + cas d'erreur, y compris un style résolu depuis un dossier partagé) dans un QGIS 3.44 réel avec le tenant CEN, consigner le résultat dans `specs/001-sharepoint-share-urls/quickstart.md` (section résultats à ajouter)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** : aucune dépendance
- **Foundational (Phase 2)** : dépend de Phase 1 — **bloque toutes les user stories**
- **US1 (Phase 3)** : après Phase 2 ; indépendante de US2/US3
- **US2 (Phase 4)** : après Phase 2 ; indépendante de US1 (le filtrage s'applique aux URL Graph
  existantes même sans conversion de liens) — T015 et T009 touchent tous deux `_fetch_bytes`, à
  séquencer si menées en parallèle
- **US3 (Phase 5)** : après Phase 2 ; indépendante fonctionnellement, mais T022-T024 touchent
  `FluxCEN.py` — à séquencer après T009/T010/T015/T017/T018 si un seul développeur
- **Polish (Phase 6)** : après les user stories retenues

### Within Each User Story

- Tests écrits et **échouants** avant l'implémentation (Red-Green-Refactor)
- Logique pure (`core/`) avant le branchement contrôleur (`FluxCEN.py`)

### Parallel Opportunities

- T003 (CI) en parallèle de T001/T002
- Tous les tests d'une même story marqués [P] : T006+T007, T012+T013+T014, T019+T020
- T011 (doc exemple) en parallèle du reste de US1
- T025+T026 en parallèle en Polish
- US1 et US2 parallélisables entre deux développeurs (attention partagée : `_fetch_bytes`)

---

## Parallel Example: User Story 2

```bash
# Écrire les trois groupes de tests échouants ensemble :
Task: "T012 tests filtrage authcfg dans tests/test_fetch.py"
Task: "T013 tests parsing catalogue dans tests/test_catalog.py"
Task: "T014 tests URI de couches dans tests/test_layers.py"
# Puis implémentation séquentielle : T015 (FluxCEN.py) → T016 (core/catalog.py) → T017 → T018
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phases 1-2 (Setup + Foundational)
2. Phase 3 (US1) → **STOP et VALIDER** : lien de partage fonctionnel de bout en bout
3. Démo possible avec le `links.yaml` réel du CEN (déjà un lien de partage aujourd'hui)

### Incremental Delivery

1. Setup + Foundational → socle testé
2. US1 → MVP démontrable (le plugin refonctionne avec le lien de partage réel)
3. US2 → fuite de jetons éliminée (ressources + couches) — fort enjeu sécurité, à livrer avec US1 dans la
   même release
4. US3 → robustesse démarrage + messages — solde les deux problèmes connus de la branche
5. Polish → release 5.3 publiable sur le dépôt CEN

**Suggested MVP scope**: Phases 1-3 (T001-T011). Recommandation : ne pas publier de release sans la
Phase 4 (US2), la spec classant la fuite de jetons en P1 au même titre que US1.

---

## Notes

- 28 tâches : Setup 3, Foundational 2, US1 6, US2 7, US3 6, Polish 4
- Commits atomiques par tâche ou groupe logique, messages **sans co-auteur** (constitution)
- `FluxCEN.py` est touché par T009, T010, T015, T017, T018, T022, T023, T024 : jamais deux de ces tâches
  en parallèle
- Les numéros de lignes de `FluxCEN.py` sont ceux de l'état actuel de la branche et glisseront au fil des
  tâches
