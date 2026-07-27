# Implementation Plan: Support des liens de partage SharePoint et restriction de l'auth Microsoft

**Branch**: `001-sharepoint-share-urls` | **Date**: 2026-07-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-sharepoint-share-urls/spec.md`

## Summary

Permettre de configurer les ressources distantes du plugin (catalogue `flux.csv`, styles, changelog,
version) avec des liens de partage SharePoint copiés depuis l'interface web, convertis par le plugin en
appels Microsoft Graph (`/shares/{u!…}/driveItem/content`) téléchargés via `QgsBlockingNetworkRequest` et
l'authcfg QGIS. Simultanément, restreindre strictement l'application de l'auth Microsoft au périmètre
`graph.microsoft.com` / `*.sharepoint.com` : dans `_fetch_bytes` (ressources) et en supprimant
l'attachement indiscriminé de la première authcfg aux couches WMS/WFS. La robustesse au démarrage (réseau
différé, erreurs non fatales, cache mémoire du catalogue) fait partie du périmètre (FR-008/FR-009).
Approche technique détaillée dans [research.md](research.md).

## Technical Context

**Language/Version**: Python embarqué par QGIS 3.44 (≥ 3.9 garanti, 3.12 sur les installeurs officiels)

**Primary Dependencies**: PyQGIS (`qgis.core`, `qgis.PyQt` exclusivement), stdlib (`urllib.parse`,
`base64`, `csv`, `io`). Aucune dépendance externe (Principe I).

**Storage**: fichiers de config locaux `config/yaml/links.yaml` (gitignoré) ; cache mémoire de session
pour le catalogue ; base d'auth chiffrée QGIS (authcfg, jamais manipulée directement)

**Testing**: `pytest` + `pytest-qgis` (première suite du dépôt), tests sous `tests/`, CI GitHub Actions
sur image `qgis/qgis:release-3_44`, job bloquant

**Target Platform**: QGIS Desktop ≥ 3.44 (LTR), Windows / macOS / Linux

**Project Type**: plugin QGIS (mono-dépôt, code plugin à la racine)

**Performance Goals**: démarrage de QGIS sans aucune requête réseau du plugin ; téléchargement du
catalogue (~100 Ko) au premier clic < 5 s sur réseau nominal ; une seule récupération du catalogue par
session (cache)

**Constraints**: pas de blocage du thread GUI au démarrage ; HTTPS obligatoire ; aucun secret dans les
logs/messages ; rétrocompatibilité du format `links.yaml` existant (URL Graph, authcfg)

**Scale/Scope**: ~60 domaines tiers dans le catalogue, 1 fichier `FluxCEN.py` de 1007 lignes à découper a
minima, 2 nouveaux modules purs, ~6 sites d'appel réseau existants à couvrir

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principe | Statut | Application dans ce plan |
|---|----------|--------|--------------------------|
| I | Intégration native QGIS | ✅ | Réseau via `QgsBlockingNetworkRequest` uniquement ; conversion de lien = stdlib pure ; aucune dépendance externe ; réseau retiré du démarrage (plus de `socket` au niveau module) |
| II | TDD non négociable | ✅ | Tests écrits d'abord pour `core/ms_urls.py`, `core/catalog.py`, filtrage d'auth ; première suite `pytest`+`pytest-qgis` ; CI bloquante |
| III | Architecture en couches | ✅ | Logique pure extraite dans `core/` (sans import qgis) ; `FluxCEN.py` reste contrôleur/UI ; pas de logique dans les handlers de signaux |
| IV | Sécurité & secrets | ✅ | Expansion authcfg déléguée à `QgsAuthManager` ; filtrage strict du périmètre Microsoft avant `setAuthCfg` ; HTTPS obligatoire ; messages d'erreur sans URL complète ni jeton |
| V | YAGNI | ✅ | Pas de `QgsTask` (fichiers < 100 Ko au clic), pas de cache disque, pas de liste blanche configurable, pas de refonte globale de `FluxCEN.py` — justifications dans research.md (R3, R4, R5, R7) |
| VI | Compatibilité 3.44 / SemVer | ✅ | APIs utilisées disponibles en 3.44 ; `metadata.txt` passera à `qgisMinimumVersion=3.44` (TODO constitutionnel repris ici) ; version plugin incrémentée en MINEUR |
| VII | Qualité & observabilité | ✅ | `QgsMessageLog` (onglet « FluxCEN ») remplace les `print()` sur les chemins touchés ; messages français par famille d'erreur ; pylint sans nouvelle violation |

**Gate initiale : PASS** — aucune violation, tableau Complexity Tracking vide.

**Re-check post-Phase 1 : PASS** — le design (data-model, contrats) n'introduit ni dépendance externe, ni
abstraction non requise ; les contrats de fonctions pures renforcent le Principe III.

## Project Structure

### Documentation (this feature)

```text
specs/001-sharepoint-share-urls/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── links-yaml.md
│   └── core-functions.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
FluxCEN.py               # contrôleur + UI (existant, modifié) :
                         #   _fetch_bytes() : filtrage périmètre Microsoft + résolution lien de partage
                         #   __init__ / import module : réseau supprimé (déféré vers run())
                         #   initialisation_flux() : cache mémoire du catalogue
                         #   handle_wms_layer()/handle_wfs_layer() : attachement authcfg supprimé
                         #   parse_table_row() : déplacé vers core/catalog.py
core/
├── __init__.py          # nouveau package de logique pure (aucun import qgis)
├── ms_urls.py           # is_microsoft_url(), is_sharepoint_sharing_link(),
│                        # sharing_link_to_graph_url()
└── catalog.py           # parsing/validation du CSV de flux (parse_table_row, catégories)

config/yaml/
└── links_example.yaml   # documentation mise à jour : lien de partage accepté tel quel

tests/
├── conftest.py          # fixtures pytest-qgis
├── data/                # CSV de flux minimal, links.yaml de test
├── test_ms_urls.py      # unitaires purs (périmètre Microsoft, conversion lien de partage)
├── test_catalog.py      # unitaires purs (parsing CSV)
└── test_fetch.py        # intégration : _fetch_bytes avec/sans authcfg selon domaine

.github/workflows/
└── quality.yml          # job pytest ajouté (image qgis/qgis:release-3_44, bloquant)

metadata.txt             # qgisMinimumVersion=3.44, version MINEUR+1, changelog
```

**Structure Decision**: plugin QGIS à plat (structure historique conservée) ; la seule évolution
structurelle est le package `core/` de logique pure exigé par le Principe III, plus le répertoire `tests/`
constitutionnel. Pas de `src/` : le dépôt EST le plugin déployé, le zip de release exclut `tests/`,
`specs/`, `.specify/`.

## Complexity Tracking

Aucune violation de la Constitution Check — tableau vide.
