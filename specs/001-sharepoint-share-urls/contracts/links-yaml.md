# Contrat : configuration `config/yaml/links.yaml` (interface administrateur)

Interface exposée aux administrateurs du plugin — un fichier YAML local, gitignoré.

## Clés

*(Mise à jour 2026-07-27 : les clés `info_changelog` et `depot_plugins_url.last_version` ont été
supprimées par la simplification du versionning sur `main`, PR #48/#49.)*

```yaml
github_urls:
  flux_csv: "<URL>"        # catalogue de flux (CSV ;)
  styles_couches: "<URL>"  # préfixe des styles .qml (URL directe ou lien de partage de dossier)
auth:
  authcfg: ""              # optionnel : surcharge de l'ID de config d'auth QGIS (7 car.)
```

La clé `auth.authcfg` est **optionnelle** (FR-013) : le plugin provisionne lui-même la configuration
Microsoft canonique (ID `g2b2197`) dans le gestionnaire d'authentification QGIS au premier accès —
aucune action utilisateur. La clé reste une surcharge de **dépannage** : prioritaire si renseignée
**et** présente dans le gestionnaire ; un ID périmé est ignoré (retour au provisionnement).

## Valeurs d'URL acceptées (évolution de cette feature)

Chaque clé d'URL accepte indifféremment :

1. **Lien de partage SharePoint collé tel quel** depuis « Partager → Copier le lien » (avec ses
   paramètres `?d=…&csf=1&web=1&e=…`) — résolu automatiquement par le plugin via l'authentification QGIS.
   Pour `styles_couches`, le lien de partage peut désigner un **dossier** : les fichiers `.qml` sont
   résolus par leur nom à l'intérieur du dossier partagé.
2. **URL Microsoft Graph historique** (`https://graph.microsoft.com/v1.0/…/content`) — comportement
   inchangé (rétrocompatibilité).
3. **URL HTTPS quelconque** (hébergement public, ex. styles/changelog actuels) — téléchargée **sans**
   authentification Microsoft. Les URL `data:` (contenu embarqué) restent tolérées, jamais authentifiées ;
   les URL `http:` sont rejetées.

## Garanties

- Un `links.yaml` de la version précédente fonctionne sans aucune modification.
- L'authentification Microsoft référencée par `auth.authcfg` n'est appliquée qu'aux URL du périmètre
  Microsoft (`*.sharepoint.com`, `graph.microsoft.com`) ; toute autre URL est appelée anonymement.
- URL non HTTPS : rejetée avec message explicite, aucune requête authentifiée émise.
- Le fichier ne contient jamais de secret (l'authcfg est un identifiant opaque) ; la CI échoue s'il est
  commité (`check_yaml.py` existant).

## Exemple documenté (`links_example.yaml` à mettre à jour)

```yaml
github_urls:
  # Collez ici le lien "Partager" de SharePoint, tel quel :
  flux_csv: "https://<tenant>.sharepoint.com/:x:/r/personal/…/flux.csv?d=w…&csf=1&web=1&e=…"
  styles_couches: "https://raw.githubusercontent.com/CEN-Nouvelle-Aquitaine/fluxcen/main/styles_couches/"
  info_changelog: "https://raw.githubusercontent.com/CEN-Nouvelle-Aquitaine/fluxcen/main/html/info_changelog.html"
depot_plugins_url:
  last_version: "https://sig.dsi-cen.org/qgis/fluxcen/version.txt"
auth:
  authcfg: "abc1234"
```
