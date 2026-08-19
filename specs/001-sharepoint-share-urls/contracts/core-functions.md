# Contrat : fonctions pures `core/ms_urls.py`

Module de logique pure — **aucun import `qgis`**, stdlib uniquement. Toutes les fonctions sont
déterministes, sans réseau ni I/O. C'est le contrat testé en premier (TDD).

## `is_microsoft_url(url: str) -> bool`

Vraie ssi l'URL appartient au périmètre d'authentification Microsoft.

- `True` : scheme `https` ET (`hostname == "graph.microsoft.com"` OU hostname finissant par
  `".sharepoint.com"`), hostname issu de `urllib.parse.urlsplit`, insensible à la casse.
- `False` : tout le reste — `http://`, `data:`, hostname `None`, `sharepoint.com.evil.tld`,
  `notsharepoint.com`, `https://sharepoint.com@evil.tld/…` (userinfo), chaîne vide, URL malformée
  (aucune exception ne s'échappe : toute erreur d'analyse → `False`).

## `is_sharepoint_sharing_link(url: str) -> bool`

Vraie ssi l'URL est un lien SharePoint à résoudre via Graph : scheme `https` ET hostname finissant par
`".sharepoint.com"`. (Tout lien SharePoint configuré est traité comme lien de partage à résoudre ;
`graph.microsoft.com` retourne `False` — déjà exploitable tel quel.)

## `sharing_link_to_graph_url(url: str) -> str`

Convertit un lien de partage en URL Graph de téléchargement.

- Encodage : base64 UTF-8 du lien complet → padding `=` retiré, `/`→`_`, `+`→`-` → préfixe `u!`.
- Retour : `https://graph.microsoft.com/v1.0/shares/u!<token>/driveItem/content`.
- Précondition : `is_sharepoint_sharing_link(url)` vraie ; sinon `ValueError`.
- Propriété : le retour satisfait toujours `is_microsoft_url`.

## Résolution d'un dossier partagé (cas `styles_couches`) — 2 étapes

*(Corrigé le 2026-07-27 : l'adressage par chemin sous `/shares` est rejeté par Graph — validé contre le
tenant réel.)*

### `sharing_link_to_graph_metadata_url(folder_share_url: str) -> str`
- Retour : `…/shares/u!<token>/driveItem?$select=id,parentReference`.
- Précondition : `is_sharepoint_sharing_link(folder_share_url)` vraie, sinon `ValueError`.

### `parse_drive_item_ref(json_text: str) -> tuple[str, str]`
- Extrait `(driveId, itemId)` de la réponse driveItem ; `ValueError` sur JSON invalide, champs absents ou
  vides (réponse réseau, jamais présumée sûre).

### `drive_item_child_content_url(drive_id: str, item_id: str, filename: str) -> str`
- Retour : `https://graph.microsoft.com/v1.0/drives/<driveId>/items/<itemId>:/<filename encodé>:/content`.
- `filename` non vide, sans `/`, `\` ni `..`, sinon `ValueError` ; identifiants validés (percent-encoding
  strict). Le retour satisfait toujours `is_microsoft_url`.

Côté contrôleur : `FluxCEN._style_url()` porte la résolution (métadonnées via `_fetch_bytes`, cache
`(driveId, itemId)` par session) ; `build_style_url()` refuse un lien de partage en entrée (URL directes
uniquement).

## `classify_url(url: str) -> UrlClass`

Retourne `SHAREPOINT_SHARING_LINK`, `GRAPH` ou `OTHER` (cf. data-model.md). Fonction de commodité
cohérente avec les trois fonctions ci-dessus.

## Fonctions ajoutées par les amendements du 2026-07-27

### `https_hostname(url: str) -> Optional[str]`
Nom d'hôte (minuscules) si l'URL est HTTPS, sinon `None` ; absorbe toute erreur d'analyse. Socle partagé
de toutes les décisions de périmètre (`ms_urls`, `catalog`).

### `is_graph_shares_url(url: str) -> bool`
Vraie ssi l'URL est un appel Graph `/v1.0/shares/…` — ces requêtes reçoivent l'en-tête
`Prefer: redeemSharingLinkIfNecessary`, qu'elles soient converties à la volée ou pré-construites.

### `is_database_auth_method(method: str) -> bool`
FR-011 : fausse pour les méthodes web (`OAuth2`, dont Microsoft Entra ID), vraie pour `Basic` et les
méthodes par certificat — seules candidates pour les connexions BDD et le service sécurisé CEN.

# Contrat : `core/entra.py` (FR-013)

Configuration Microsoft canonique embarquée — identifiants publics uniquement, aucun secret
(client public Entra + PKCE). Le contrôleur (`_ensure_microsoft_authcfg`) provisionne cette
configuration sous l'ID fixe `AUTHCFG_ID = "g2b2197"` au premier accès Microsoft.

## `canonical_oauth2_config(port: int) -> dict`
Paramètres OAuth2 de référence (`grantFlow` 3 = PKCE, `clientSecret` vide, redirection
`127.0.0.1:<port>/qgis-client`). Calqués sur la configuration validée en réel le 2026-08-17.

## `config_needs_update(stored_json: str) -> bool`
Vraie ssi la config stockée diverge du canon sur les clés fonctionnelles (`_COMPARED_KEYS`) ou si son
port sort de `REDIRECT_PORTS`. Les clés de présentation (id, name, …) ne déclenchent jamais de mise à
jour (pas de boucle de resérialisation). JSON illisible → mise à jour.

## `pick_free_port(is_free) -> int | None` / `port_is_free(port) -> bool`
Premier port libre de `REDIRECT_PORTS` (7070 exclu : AnyDesk). `None` si tous occupés →
famille d'erreur `PORT_REDIRECTION`. Le prédicat est injecté pour les tests.

### `build_style_url(styles_base: str, style_name: str) -> str`
Concaténation `styles_base + style_name + ".qml"` pour les URL directes uniquement ; `ValueError` sur un
lien de partage (résolution réseau portée par le contrôleur) et sur un nom de style invalide.

## Contrat d'usage côté contrôleur (`FluxCEN._fetch_bytes`)

1. `classify_url(url)` ; si `SHAREPOINT_SHARING_LINK` → `url = sharing_link_to_graph_url(url)`, avec
   en-tête `Prefer: redeemSharingLinkIfNecessary`.
2. `setAuthCfg(authcfg)` appelé **uniquement** si `is_microsoft_url(url)` (URL finale) et authcfg non
   vide. Sinon requête anonyme.
3. Périmètre Microsoft sans authcfg → erreur `AUTH_MANQUANTE` sans émettre de requête authentifiée.
4. Les messages d'erreur n'incluent que le nom d'hôte et le nom logique de la ressource.

# Contrat : `core/catalog.py`

## `parse_catalog(csv_text: str) -> list[FluxRow]` / `parse_table_row(row: list[str]) -> FluxRow`

- Entrée : texte CSV `;` conforme au data-model (10 colonnes, en-tête sautée).
- Ligne invalide (colonnes manquantes, service inconnu) : ignorée + entrée de log, jamais d'exception qui
  interrompt les autres lignes.
- `style` : rejeté (traité comme absent + log) s'il contient `/`, `\` ou `..` — le nom vient d'un fichier
  distant et sert à construire une URL.

## `extract_categories(csv_text: str) -> list[str]`

Catégories uniques du catalogue, normalisées (`strip`) et triées — alimente le menu déroulant.

# Contrat : `core/layer_builder.py`

Construction des URI de couches et périmètre sécurisé du CEN — extrait de
`core/catalog.py` en revue de PR (issue #52), contrats inchangés.

## `extract_service_version(url: str) -> str`

Version du service extraite de l'URL (motif historique `VERSION=…&REQUEST`), `"1.0.0"` à défaut.

## `cen_workspace(url: str) -> Optional[str]`

Espace de travail geoserver ciblé par l'URL HTTPS, `None` hors de `opendata.cen-nouvelle-aquitaine.org`
(correspondance d'hôte exacte). Les deux formes du catalogue sont acceptées : `/geoserver/<workspace>/…`
et `/<workspace>/…`.

## `is_cen_secured_service(url: str) -> bool`

FR-012 : vraie ssi `cen_workspace(url)` fait partie des espaces de travail sécurisés
(`fonciercen`, `chirokollect`, `data_gods_dsne` : liste exhaustive confirmée par le CEN en revue de PR).
Seules ces couches reçoivent une configuration d'authentification (non web) ; le reste du geoserver
est public et reste chargé sans authentification.

## `build_wms_uri(url, nom_technique, version=None, authcfg=None) -> str` / `build_wfs_uri_params(url, typename, version=None) -> dict`

URI de couches sans aucune configuration d'authentification par défaut (FR-010) ; `authcfg` n'est ajoutée
à l'URI WMS que si elle est fournie explicitement (périmètre sécurisé CEN, FR-012). Pour le WFS,
l'attachement éventuel se fait côté contrôleur (`uri.setAuthConfigId`).
