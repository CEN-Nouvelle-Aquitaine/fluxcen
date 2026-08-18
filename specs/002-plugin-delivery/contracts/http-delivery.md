# Contrat HTTP : service de distribution

**Consommateur** : gestionnaire d'extensions QGIS (≥ 3.34) avec authcfg OAuth2. **Fournisseur** : Azure Function derrière Easy Auth.

## Règles transverses

- Toutes les routes sont préfixées par **`/api`** (préfixe standard Azure Functions, conservé par décision du 2026-08-18) : l'URL de dépôt est `https://{host}/api/{channel}/plugins.xml`.
- HTTPS uniquement. Toute réponse de contenu est un **200 direct** : jamais de 3xx.
- Authentification : header `Authorization: Bearer <jeton>` d'audience `api://80c3a908-…`. Validée par Easy Auth avant le code de la Function.
- Les URLs ne comportent aucune query string obligatoire. QGIS ajoute `?qgis=x.y` au fetch du catalogue : le paramètre est ignoré par le serveur.
- `{channel}` ∈ {`stable`, `beta`}. `{filename}` ∈ {`plugins.xml`, `FluxCEN.<version>.zip`} ; tout autre motif → 404 (validation stricte, pas de traversée de chemin).

## GET /api/{channel}/plugins.xml

| Cas | Réponse |
|---|---|
| Jeton valide, canal `stable` | 200, `Content-Type: text/xml`, corps = catalogue du canal |
| Jeton valide, canal `beta`, membre du groupe | 200, catalogue beta (beta + stable) |
| Jeton valide, canal `beta`, non-membre | 403, corps vide |
| Jeton absent / invalide / mauvaise audience | 401 (émis par Easy Auth) |
| Canal inconnu | 404 |

## GET /api/{channel}/FluxCEN.{version}.zip

| Cas | Réponse |
|---|---|
| Jeton valide, droits du canal OK, blob présent | 200, `Content-Type: application/zip`, corps = artefact |
| Jeton valide, non-membre (beta) | 403 |
| Blob absent | 404 |
| Jeton absent / invalide | 401 |

## Sémantique d'autorisation

1. Easy Auth rejette (401) tout appel sans jeton Entra valide pour l'audience configurée. Le code de la Function ne voit jamais ces requêtes.
2. Pour `beta`, la Function lit le header `x-ms-client-principal` (posé par Easy Auth), décode les claims et exige `BETA_GROUP_ID` dans `groups`. Absence du claim = 403.
3. Aucune autorisation en plus pour `stable` : toute identité du tenant validée passe.

## Engagements de compatibilité

- Les chemins `/api/{channel}/plugins.xml` et le schéma des `download_url` sont stables : les postes provisionnés ne sont jamais reconfigurés pour un changement interne du service. Le préfixe `/api` fait partie du contrat.
- Un zip publié est immuable (même URL = même contenu).
