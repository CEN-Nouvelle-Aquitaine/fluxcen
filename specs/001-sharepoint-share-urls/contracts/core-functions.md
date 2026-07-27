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
