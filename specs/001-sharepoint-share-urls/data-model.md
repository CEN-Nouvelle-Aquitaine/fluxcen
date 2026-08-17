# Data Model: 001-sharepoint-share-urls

**Date**: 2026-07-27 | **Plan**: [plan.md](plan.md)

## Entités

### RessourceDistante (configuration `links.yaml`)

Fichier nécessaire au plugin, identifié par une URL dans `config/yaml/links.yaml`.

| Champ (clé YAML) | Type | Règles |
|---|---|---|
| `github_urls.flux_csv` | URL | HTTPS obligatoire ; lien de partage SharePoint, URL Graph ou URL quelconque |
| `github_urls.styles_couches` | URL (préfixe) ou lien de partage de dossier SharePoint | HTTPS obligatoire ; URL directe : concaténée avec `<nom_style>.qml` ; lien de partage de dossier : le fichier `<nom_style>.qml` est résolu par chemin à l'intérieur du dossier partagé |
| `auth.authcfg` | chaîne (7 car.) ou vide | identifiant opaque de la config d'auth QGIS ; jamais les secrets eux-mêmes |

**Invariant** : le format existant reste valide sans modification (rétrocompatibilité FR-003) ; seule la
*capacité* d'y mettre un lien de partage est ajoutée.

### ClassificationUrl (résultat de `core/ms_urls.py`)

Toute URL de ressource est classée avant émission de la requête. Classification par nom d'hôte exact
(`urllib.parse.urlsplit().hostname`, minuscules) :

| Classe | Condition | Auth Microsoft | Transformation |
|---|---|---|---|
| `SHAREPOINT_SHARING_LINK` | scheme https ET hostname se termine par `.sharepoint.com` | oui | convertie en URL Graph `/shares/u!<b64url>/driveItem/content` |
| `GRAPH` | scheme https ET hostname == `graph.microsoft.com` | oui | aucune |
| `OTHER` | tout le reste (y compris http, `data:`, domaines trompeurs) | **non** | aucune |

**Transitions** : `SHAREPOINT_SHARING_LINK → GRAPH` (conversion pure, sans réseau) — pour un fichier,
conversion directe ; pour le dossier des styles, résolution en deux étapes
(`sharing_link_to_graph_metadata_url` puis `drive_item_child_content_url`, cf. research R1). Les classes `GRAPH` et `OTHER` sont terminales. Une URL de partage de
dossier n'est pas distinguable syntaxiquement d'une URL de fichier : c'est le site d'usage
(`styles_couches`) qui détermine la conversion appliquée.

### CatalogueFlux (contenu de `flux.csv`, parsé par `core/catalog.py`)

CSV `;`, 10 colonnes : `service;categorie;Nom_couche_plugin;nom_technique;url;source;style;metadonnees;nom_bdd;nom_schema`.

| Attribut | Colonne | Validation |
|---|---|---|
| service | 0 | ∈ {WMS, WFS, PostGIS} (ligne ignorée + log sinon) |
| catégorie | 1 | non vide |
| nom couche / nom technique | 2 / 3 | non vide |
| url | 4 | non vide pour WMS/WFS |
| style | 6 | optionnel ; nom de fichier sans séparateur de chemin ni `..` (l'URL de style dérivée est classée comme toute URL — jamais d'auth Microsoft hors périmètre) |
| métadonnées | 7 | optionnel |
| bdd / schéma | 8 / 9 | requis pour PostGIS |

**Cycle de vie** : téléchargé au premier affichage du dialogue → parsé → mis en cache mémoire pour la
session → invalidé uniquement au rechargement du plugin.

### ErreurTelechargement (classification des échecs, FR-008 / SC-006)

| Famille | Détection | Message utilisateur (français, sans URL complète ni jeton) |
|---|---|---|
| `LIEN_INVALIDE` | réponse 400/404 ou conversion impossible | « Le lien configuré pour <nom ressource> est invalide ou expiré » |
| `ACCES_REFUSE` | 401/403 après auth | « Accès refusé à <nom ressource> : vérifiez vos droits SharePoint » |
| `AUTH_MANQUANTE` | périmètre Microsoft sans authcfg configurée (cas résiduel : provisionnement FR-013 indisponible) | « Configurez l'authentification Microsoft dans QGIS (voir documentation) » |
| `AUTH_PROVISIONNEMENT` | échec d'écriture de la config canonique dans le gestionnaire QGIS (mot de passe principal refusé, système d'auth indisponible — FR-013) | « L'installation de la configuration d'authentification Microsoft dans QGIS a échoué » |
| `PORT_REDIRECTION` | tous les ports de redirection déclarés occupés par d'autres logiciels (FR-013) | « Les ports de redirection de l'authentification Microsoft sont occupés par un autre logiciel » |
| `RESEAU` | timeout, DNS, connexion | « <nom ressource> inaccessible : vérifiez votre connexion » |

Chaque famille est journalisée dans `QgsMessageLog` (onglet « FluxCEN ») avec le nom d'hôte seul.

### ConfigurationMicrosoftCanonique (FR-013, `core/entra.py`)

Paramètres OAuth2 de référence, embarqués dans le plugin (identifiants publics, aucun secret) :
ID `g2b2197`, nom « Microsoft CEN », flux Authorization Code PKCE (`grantFlow: 3`), client public
Entra (`clientSecret` vide), endpoints v2.0 du tenant, portée Graph `Files.Read.All offline_access`,
redirection `127.0.0.1:<port>/qgis-client` avec `<port>` choisi dans la liste déclarée
(17070, 17071, 17072) en évitant les ports occupés (ex. AnyDesk sur 7070). **Cycle de vie** : vérifiée
à chaque accès Microsoft ; absente → créée ; différente du canon (hors port valide et libre) → mise à
jour ; jamais touchée au démarrage de QGIS.
