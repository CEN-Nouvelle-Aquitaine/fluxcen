<!--
Sync Impact Report
==================
Version change: 1.1.0 → 1.2.0
Modified principles:
  - VI. Compatibilité et versionnement : plancher QGIS abaissé de 3.44 à 3.34
    (plancher technique transitoire, décision #55 entérinée : la mise à niveau
    du parc CEN vers 3.44 LTR est prévue mais non achevée). Retour à 3.44 par
    amendement dédié une fois la migration du parc terminée.
Added sections: aucune
Removed sections: aucune
Templates:
  - .specify/templates/plan-template.md ✅ compatible
  - .specify/templates/spec-template.md ✅ compatible
  - .specify/templates/tasks-template.md ✅ compatible
  - .specify/templates/checklist-template.md ✅ compatible
Follow-up TODOs:
  - Repasser le plancher à 3.44 (Principe VI) quand la mise à niveau du parc
    est achevée ; aligner alors metadata.txt et l'image CI.
  - CI : le Principe II exige les tests sur la version minimale supportée ;
    l'image de référence devient qgis/qgis:3.34 (3.44 en complément).
  - Contrainte « Distribution » : à amender vers l'URL du dépôt privé lors de
    la migration (spec 002-plugin-delivery, tâche T033).
-->

# FluxCEN Constitution

Plugin QGIS du CEN Nouvelle-Aquitaine : centralisation des flux WFS/WMS/OGC API
avec authentification (OAuth2 Entra ID via la pile d'authentification QGIS).

## Core Principles

### I. Intégration native QGIS d'abord

Toute fonctionnalité DOIT s'appuyer en priorité sur les API PyQGIS et Qt fournies
par QGIS plutôt que sur des bibliothèques tierces.

- Les requêtes réseau DOIVENT passer par `QgsNetworkAccessManager` (ou
  `QgsBlockingNetworkRequest`) — jamais `requests`, `urllib` ou `httplib2` pour
  des flux authentifiés. C'est la seule voie qui respecte le proxy, les
  certificats et l'infrastructure d'authentification de QGIS.
- Aucune dépendance Python externe non livrée avec QGIS ne DOIT être ajoutée
  sans justification écrite dans le plan (les utilisateurs ne peuvent pas
  `pip install` facilement dans l'environnement QGIS).
- Les traitements longs DOIVENT utiliser `QgsTask` ou des requêtes asynchrones ;
  bloquer le thread GUI est interdit.

**Rationale** : un plugin qui contourne la pile QGIS casse le proxy, l'auth et
la portabilité Windows/macOS/Linux des postes du CEN.

### II. Test-First — TDD (NON-NÉGOCIABLE)

Le cycle Red-Green-Refactor est obligatoire pour tout code de logique métier.

- Les tests DOIVENT être écrits et échouer avant l'implémentation.
- Framework : `pytest` + `pytest-qgis` pour l'environnement QGIS headless ;
  aucun test ne DOIT exiger le lancement manuel de l'interface QGIS.
- Les tests DOIVENT être exécutables en CI (GitHub Actions, image Docker
  `qgis/qgis`) sur la version QGIS minimale supportée.
- Un bug corrigé DOIT d'abord être reproduit par un test qui échoue.

**Rationale** : le plugin est déployé sur un parc de postes hétérogène ; la
régression silencieuse d'un flux ou de l'auth coûte cher en support.

### III. Architecture en couches testable

Le code DOIT être organisé en trois couches à responsabilité claire :

1. **Logique** : fonctions pures ou classes sans dépendance à `iface`
   (parsing du CSV des flux, construction d'URI, filtrage par mots-clés).
   Cette couche porte l'essentiel de la couverture de tests.
2. **Contrôleur** : lit les entrées depuis l'interface, appelle la logique,
   pousse les résultats vers le GUI.
3. **UI** : dialogs et widgets (`.ui` + classes Qt), le plus mince possible.

La logique métier ne DOIT jamais être écrite directement dans les handlers de
signaux Qt.

**Rationale** : la couche logique est peu coûteuse à tester et concentre les
bugs ; le GUI se teste peu et mal.

### IV. Sécurité et gestion des secrets

- Aucun secret (mot de passe, token, client secret, certificat) ne DOIT figurer
  dans le code, le CSV des flux, `metadata.txt` ou l'historique Git.
- Les identifiants DOIVENT être stockés dans la base d'authentification
  chiffrée de QGIS et référencés uniquement par leur `authcfg` ; l'expansion de
  l'`authcfg` DOIT être laissée à `QgsAuthManager` (jamais d'expansion précoce
  ni de log d'URI complète).
- OAuth2 : flux Authorization Code + PKCE obligatoire ; aucun client secret
  embarqué dans le plugin.
- Toutes les URL de flux DOIVENT être en HTTPS ; la validation TLS ne DOIT
  jamais être désactivée.
- Les entrées externes (CSV de flux distant, réponses de services) DOIVENT être
  validées avant usage ; les erreurs réseau DOIVENT être gérées sans exposer de
  données sensibles dans les messages.

**Rationale** : le plugin manipule des flux fonciers sensibles et une auth
Entra ID d'entreprise ; une fuite d'authcfg ou de token compromet le SI du CEN.

### V. Simplicité — YAGNI

- N'implémenter que ce que la spec courante exige ; aucune abstraction
  « pour plus tard », aucune option de configuration sans cas d'usage réel.
- Préférer la modification du CSV de configuration des flux à l'ajout de code.
- Toute complexité ajoutée (nouveau pattern, nouvelle couche, nouvelle
  dépendance) DOIT être justifiée dans la section « Complexity Tracking » du
  plan, avec l'alternative simple rejetée et la raison.
- Le code mort, les fichiers `__pycache__`, les ressources inutilisées DOIVENT
  être supprimés du dépôt.

**Rationale** : le plugin est maintenu par une petite équipe ; chaque ligne non
indispensable est une dette.

### VI. Compatibilité et versionnement

- Version QGIS minimale supportée : **3.34 (LTR)**, plancher technique
  transitoire tant que la mise à niveau du parc CEN vers 3.44 n'est pas
  achevée ; `metadata.txt` DOIT déclarer `qgisMinimumVersion=3.34` (format
  majeur.mineur uniquement, sans patch). Le retour du plancher à 3.44 se fait
  par amendement dédié à la fin de la migration du parc.
- Toute API PyQGIS utilisée DOIT exister en 3.34 ; les API dépréciées DOIVENT
  être évitées pour préparer la migration Qt6/QGIS 4 (viser
  `qgisMaximumVersion=4.99` à terme).
- Versionnement du plugin : SemVer `MAJEUR.MINEUR.CORRECTIF`, incrémenté et
  consigné dans le `changelog` de `metadata.txt` à chaque release.
- Le plugin DOIT fonctionner à l'identique sous Windows, macOS et Linux
  (chemins via `os.path`/`pathlib`, encodage UTF-8 explicite).

**Rationale** : le parc réel impose 3.34 aujourd'hui ; viser les API communes
à 3.34-3.44 minimise à la fois le support du parc actuel et le coût de la
bascule Qt6/QGIS 4 une fois la mise à niveau achevée.

### VII. Qualité et observabilité

- PEP 8 appliqué ; lint obligatoire via `pylint` (configuration `pylintrc` du
  dépôt) sans nouvelle violation introduite.
- Journalisation via `QgsMessageLog` (onglet dédié « FluxCEN ») et le module
  `logging` de Python ; pas de `print()` dans le code livré.
- Les messages utilisateur (barre de message, dialogs) DOIVENT être en
  français, actionnables, et distinguer erreur utilisateur / erreur réseau /
  bug interne.
- Les chaînes destinées à l'utilisateur DEVRAIENT passer par l'API de
  traduction Qt (`tr()`) pour permettre une i18n future.

**Rationale** : le diagnostic à distance sur les postes des utilisateurs CEN
repose entièrement sur des logs exploitables.

## Contraintes techniques

- **Langage** : Python (version embarquée par QGIS 3.44, ≥ 3.9 garanti) ;
  annotations de type sur toute nouvelle fonction publique.
- **Stack** : PyQGIS, PyQt (via `qgis.PyQt` exclusivement — jamais d'import
  direct `PyQt5`/`PyQt6`), `QgsAuthManager`, `QgsNetworkAccessManager`.
- **Structure** : `metadata.txt` conforme aux champs obligatoires du dépôt de
  plugins QGIS ; ressources compilées (`resources.py`) régénérées via `pyrcc`
  et non éditées à la main ; tests sous `tests/` avec `conftest.py` et données
  de test sous `tests/data/`.
- **Distribution** : dépôt de plugins personnalisé du CEN
  (`https://sig.dsi-cen.org/qgis/`) ; le paquet zip ne DOIT contenir ni
  `__pycache__`, ni fichiers de dev (`.specify/`, `.claude/`, tests exclus du
  zip de release).

## Workflow de développement

- Cycle Spec-Kit : `specify → clarify → plan → tasks → implement` ; la
  « Constitution Check » du plan DOIT être validée avant la phase de recherche
  et revalidée après le design.
- Travail sur branche de fonctionnalité ; `main` reste toujours releasable ;
  merge via Pull Request avec revue.
- Gates de CI avant merge : lint (`pylint`) + suite de tests
  (`pytest` + `pytest-qgis`) verts sur la version QGIS minimale supportée
  (3.34 ; 3.44 en complément recommandé).
- Une release = tag Git + incrément SemVer + changelog dans `metadata.txt` +
  zip publié sur le dépôt CEN.
- **Commits** : les messages de commit ne DOIVENT contenir aucune mention de
  co-auteur (`Co-Authored-By:`, `Co-authored-by:` ou équivalent), y compris
  pour les commits générés par des outils ou assistants IA. Le message décrit
  le changement, rien d'autre ; l'auteur Git est le seul identifiant de
  provenance.

## Governance

Cette constitution prévaut sur toute autre pratique du dépôt. Toute PR et toute
revue DOIVENT vérifier la conformité aux principes ci-dessus ; une dérogation
DOIT être justifiée dans la section « Complexity Tracking » du plan concerné.

Amendements : proposition par PR modifiant ce fichier, avec justification,
incrément de version sémantique de la constitution
(MAJEUR : retrait/redéfinition incompatible d'un principe ; MINEUR : ajout ou
extension matérielle ; CORRECTIF : clarification), et propagation vérifiée dans
les templates `.specify/templates/`.

Revue de conformité : à chaque exécution de `/speckit-plan` (gate
« Constitution Check ») et à chaque revue de PR.

**Version**: 1.2.0 | **Ratified**: 2026-07-27 | **Last Amended**: 2026-08-18
