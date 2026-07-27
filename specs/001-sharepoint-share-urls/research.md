# Research: Support des liens de partage SharePoint et restriction de l'auth Microsoft

**Date**: 2026-07-27 | **Feature**: 001-sharepoint-share-urls

## R1 — Résolution d'un lien de partage SharePoint en téléchargement

**Decision**: convertir côté plugin le lien de partage en appel Microsoft Graph
`GET https://graph.microsoft.com/v1.0/shares/{token}/driveItem/content`, où `{token}` = `"u!"` +
base64url **non paddé** du lien de partage complet (base64 standard, puis `=` retirés, `/`→`_`, `+`→`-`).
Ajouter l'en-tête `Prefer: redeemSharingLinkIfNecessary` pour garantir l'accès le temps de la requête.

**Rationale**: mécanisme documenté et stable de l'API Graph v1.0
(<https://learn.microsoft.com/en-us/graph/api/shares-get>), déjà validé manuellement sur le tenant CEN le
2026-07-15 (l'URL Graph actuelle de `links.yaml` était construite à la main avec ce même schéma). La
conversion est une fonction pure (chaîne → chaîne), sans réseau, donc testable unitairement sans QGIS.
L'appel reste sur `graph.microsoft.com` → l'auth Microsoft reste dans le périmètre autorisé.

**Extension dossiers (styles)** : pour un lien de partage vers un **dossier**, un fichier est adressé par
chemin sous la ressource partagée : `GET /shares/{token}/driveItem:/{nom-fichier}:/content` (adressage par
chemin des driveItems, documenté par l'API Graph). Le nom de fichier est encodé (percent-encoding) et
validé en amont (pas de `/`, `\` ni `..` — il provient du catalogue distant).

**Alternatives considered**:
- Ajouter `?download=1` au lien de partage : non documenté pour les tenants d'entreprise avec
  authentification déléguée, dépend des cookies de session navigateur — non fiable hors navigateur.
- Appel `/shares/{token}/driveItem` puis lecture de `@microsoft.graph.downloadUrl` : deux requêtes au lieu
  d'une ; `/content` fait la même chose en une seule (302 vers l'URL de téléchargement pré-authentifiée).

## R2 — Détection des URL du périmètre Microsoft

**Decision**: fonction pure basée sur `urllib.parse.urlsplit(url)` : scheme `https` obligatoire, puis
`hostname == "graph.microsoft.com"` ou `hostname.endswith(".sharepoint.com")` (hostname normalisé en
minuscules par `urlsplit`). Un lien de partage SharePoint est détecté par `hostname.endswith(".sharepoint.com")`
(couvre `<tenant>.sharepoint.com` et `<tenant>-my.sharepoint.com`).

**Rationale**: `urlsplit().hostname` est la seule analyse fiable (résiste à `sharepoint.com.evil.tld`, aux
userinfo `https://sharepoint.com@evil.tld`, à la casse). Stdlib uniquement (Principe I). Le test
`endswith(".sharepoint.com")` exige un point de séparation, donc `notsharepoint.com` et
`sharepoint.com.evil.tld` sont exclus (exigence FR-005).

**Alternatives considered**:
- Expression régulière sur l'URL brute : fragile (userinfo, ports, casse), rejetée.
- Liste blanche configurable dans `links.yaml` : YAGNI — les deux domaines suffisent ; extension possible
  plus tard sans casser le contrat.

## R3 — Application de l'authcfg et redirections

**Decision**: dans le point d'entrée unique de téléchargement (`_fetch_bytes`), n'appeler
`setAuthCfg(authcfg)` que si l'URL (après conversion éventuelle du lien de partage) appartient au périmètre
Microsoft (R2). L'expansion de l'authcfg reste entièrement déléguée à `QgsAuthManager` via
`QgsBlockingNetworkRequest.setAuthCfg` (Principe IV).

**Rationale**: `Graph /content` répond 302 vers une URL de téléchargement pré-authentifiée sur
`*.sharepoint.com` ; la pile Qt/QGIS suit la redirection et Qt ne rejoue pas l'en-tête `Authorization` vers
un hôte différent (comportement de sécurité Qt ≥ 5.9, QGIS 3.44 est sous Qt 5.15). L'URL redirigée étant
elle-même dans le périmètre Microsoft, aucun cas de fuite par redirection n'est introduit. À couvrir par un
test d'intégration si un serveur de test est disponible ; sinon documenté comme comportement plateforme.

**Alternatives considered**:
- Interdire les redirections : casse `/content` qui repose dessus.
- Vérifier le domaine de chaque redirection dans le plugin : Qt gère déjà la non-propagation de
  l'`Authorization` inter-hôtes ; duplication inutile (YAGNI).

## R4 — Couches WMS/WFS : suppression de l'attachement indiscriminé

**Decision**: supprimer la logique « première authcfg disponible attachée à toute couche » de
`handle_wms_layer` / `handle_wfs_layer`. Les couches WMS/WFS du catalogue sont chargées sans authcfg
(aucun domaine du catalogue actuel n'appartient au périmètre Microsoft). Aucun mécanisme d'auth par couche
n'est réintroduit dans cette évolution.

**Rationale**: choix de périmètre validé par l'utilisateur (« Inclure »). Le catalogue référence ~60
domaines tiers publics (IGN, BRGM, Carmen…) qui fonctionnent sans auth ; l'attachement actuel est une pure
fuite sans bénéfice fonctionnel. Si un flux authentifié apparaît un jour, une colonne dédiée du CSV sera
spécifiée alors (YAGNI).

**Alternatives considered**:
- Filtrer par domaine et garder l'attachement pour les couches Microsoft : aucun flux WMS/WFS Microsoft
  n'existe dans le catalogue ; code mort dès l'écriture.
- Restaurer l'ancien filtre « fonciercen / drone » du changelog v5.x : ces couches n'existent plus dans le
  CSV actuel sous cette forme ; à re-spécifier si le besoin revient.

**Correctif 2026-07-27 (revue de code + confirmation utilisateur)** : la décision ci-dessus était trop
large — le catalogue contient ~40 couches WFS `fonciercen` sur `opendata.cen-nouvelle-aquitaine.org`,
geoserver **authentifié**. FR-012 restaure une authentification ciblée : uniquement pour ce domaine
(`is_cen_secured_service()`, correspondance d'hôte exacte), avec une configuration **non web** choisie par
le mécanisme filtré de FR-011 (`_select_service_authcfg()`). La config Microsoft reste exclue partout.

## R4bis — Couches PostGIS : filtrage des méthodes d'authentification (amendement 2026-07-27)

**Decision**: `apply_authentication_if_needed()` (chemin PostGIS) et le dialogue de choix de la
configuration par défaut ne considèrent que les configurations dont la méthode
(`QgsAuthMethodConfig.method()`) est adaptée à une connexion base de données — la méthode `OAuth2`
(Microsoft Entra ID) est exclue. Une configuration par défaut mémorisée (QSettings) devenue inadaptée est
ignorée avec un message journalisé.

**Rationale**: découvert lors de la validation T028 — avec la config Entra présente dans QGIS, la logique
« première config disponible / config par défaut » attachait l'authcfg OAuth2 à l'URI PostGIS ; la méthode
OAuth2 de QGIS ne peut rien injecter dans une connexion libpq, la connexion échoue et QGIS affiche sa
fenêtre d'identification de secours exposant l'URI complète. Liste noire (`OAuth2`) plutôt que liste
blanche : les méthodes Basic et certificats (PKI) sont toutes légitimes pour PostgreSQL.

**Alternatives considered**:
- Liste blanche `Basic` uniquement : casserait les authentifications par certificat, légitimes pour
  PostgreSQL.
- Supprimer tout le mécanisme d'auth PostGIS : hors périmètre, les couches foncières en dépendent.

## R5 — Robustesse au démarrage (FR-008, FR-009)

**Decision**: supprimer tout accès réseau de l'import du module et de `FluxCEN.__init__` (y compris le
test de connectivité `socket` au niveau module). Les téléchargements (catalogue, version, changelog) sont
déclenchés au premier affichage du dialogue (`run`) et à l'ouverture de la popup de bienvenue, chacun
enveloppé dans `try/except` avec message `QgsMessageLog` + barre de message. Le catalogue est mis en cache
en mémoire pour la session (plus de re-téléchargement à chaque changement de catégorie).

**Rationale**: aujourd'hui deux fetchs hors `try/except` dans `__init__` (`FluxCEN.py:162`, `178`) font
échouer `classFactory` et désactivent le plugin ; c'est aussi le problème n°2 connu de la branche (crash
QGIS au démarrage via le flux OAuth interactif déclenché pendant le chargement). Déplacer le réseau vers
une action utilisateur rend l'éventuel dialogue OAuth légitime et supprime le gel du démarrage (FR-009).
Une requête bloquante courte lors d'un clic utilisateur reste acceptable ; `QgsTask` n'est pas requis pour
ce volume (fichiers < 100 Ko) — réévaluer si le catalogue grossit.

**Alternatives considered**:
- `QgsTask` / téléchargement asynchrone complet : complexité (signaux, états partiels du dialogue) non
  justifiée pour ~100 Ko au clic ; YAGNI. Le gel interdit est celui du **démarrage de QGIS**, traité par le
  report du réseau.
- Cache disque persistant : hors périmètre, le cache mémoire suffit aux exigences.

## R6 — Première suite de tests du dépôt

**Decision**: `tests/` à la racine avec `pytest` + `pytest-qgis` ; la logique pure (module de manipulation
d'URL, classification d'erreurs, parsing CSV) est testée sans QGIS ; un petit nombre de tests d'intégration
utilisent le fixture `qgis_app` de `pytest-qgis` pour `_fetch_bytes` (avec un serveur HTTP local ou des
mocks de `QgsBlockingNetworkRequest`). CI : job de test ajouté à `.github/workflows/quality.yml` sur
l'image `qgis/qgis:3.44`, bloquant (`continue-on-error` retiré pour ce job).

**Rationale**: Principe II (TDD) et III (couche logique porte la couverture). `pytest-qgis` requiert
QGIS ≥ 3.34, compatible avec la cible 3.44. Rendre le job bloquant donne enfin une gate CI réelle.

**Alternatives considered**:
- `unittest` seul sans pytest-qgis : perd les fixtures QGIS headless et la convention constitutionnelle.
- Tout tester via mocks sans QGIS : les chemins `QgsBlockingNetworkRequest`/authcfg resteraient non
  couverts ; garder un socle d'intégration minimal.

## R7 — Découpage en modules (architecture Principe III)

**Decision**: extraire la logique pure dans un nouveau module `core/` du plugin :
- `core/ms_urls.py` : `is_microsoft_url()`, `is_sharepoint_sharing_link()`, `sharing_link_to_graph_url()`
  (fonctions pures, stdlib uniquement, sans import qgis).
- `core/catalog.py` : parsing du CSV de flux (extraction de `parse_table_row` et du parsing des
  catégories), validation des lignes.
`FluxCEN.py` conserve le rôle de contrôleur/UI et consomme ces fonctions.

**Rationale**: `FluxCEN.py` fait 1007 lignes monolithiques ; la constitution impose la couche logique
séparée et testable. L'extraction est limitée à ce que la feature touche (YAGNI — pas de refonte globale).

**Alternatives considered**:
- Tout laisser dans `FluxCEN.py` : violerait le Principe III et rendrait le TDD impraticable.
- Refonte complète en package : hors périmètre de la feature.

## Scopes / permissions

Le scope OAuth2 existant `Files.Read.All` (config authcfg `g2b2197`) suffit pour `GET /shares/…/driveItem/content`
en délégué lecture seule ; aucun changement de configuration Entra requis. (La doc liste
`Files.ReadWrite` comme « least privileged » pour l'API shares générale, mais la lecture de contenu
fonctionne avec `Files.Read.All`, validé sur le tenant CEN le 2026-07-15.)
