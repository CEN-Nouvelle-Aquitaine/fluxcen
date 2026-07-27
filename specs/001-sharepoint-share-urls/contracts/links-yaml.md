# Contrat : configuration `config/yaml/links.yaml` (interface administrateur)

Interface exposée aux administrateurs du plugin — un fichier YAML local, gitignoré.

## Clés (inchangées)

```yaml
github_urls:
  flux_csv: "<URL>"        # catalogue de flux (CSV ;)
  styles_couches: "<URL>"  # préfixe des styles .qml
  info_changelog: "<URL>"  # changelog HTML
depot_plugins_url:
  last_version: "<URL>"    # information de version
auth:
  authcfg: "abc1234"       # ID de config d'auth QGIS (7 car.), vide = jamais d'auth
```

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
