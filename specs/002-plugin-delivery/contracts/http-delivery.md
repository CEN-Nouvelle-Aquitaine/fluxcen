# Contrat HTTP : service de distribution

**Consommateur** : gestionnaire d'extensions QGIS (≥ 3.34) avec authcfg OAuth2. **Fournisseur** : Azure Function derrière Easy Auth.

**Modèle** (révisé le 2026-08-18, standard communautaire) : **dépôt unique**. Les préversions sont des entrées `experimental="True"` du même catalogue ; l'opt-in beta se fait côté client (case « Afficher aussi les extensions expérimentales »). Toute identité du tenant validée par Easy Auth accède au dépôt : aucune autorisation supplémentaire côté service.

## Règles transverses

- Toutes les routes sont préfixées par **`/api`** (standard Azure Functions, décision du 2026-08-18) : l'URL de dépôt est `https://{host}/api/stable/plugins.xml`.
- HTTPS uniquement. Toute réponse de contenu est un **200 direct** : jamais de 3xx.
- Authentification : header `Authorization: Bearer <jeton>` d'audience `api://80c3a908-…`. Validée par Easy Auth avant le code de la Function.
- Les URLs ne comportent aucune query string obligatoire. QGIS ajoute `?qgis=x.y` au fetch du catalogue : le paramètre est ignoré par le serveur.
- Le segment de chemin est `stable` (canal unique, nom historique) ; `{filename}` ∈ {`plugins.xml`, `FluxCEN.<version>.zip`, préversions incluses} ; tout autre motif → 404 (validation stricte, pas de traversée de chemin).

## GET /api/stable/plugins.xml

| Cas | Réponse |
|---|---|
| Jeton valide | 200, `Content-Type: text/xml`, corps = catalogue (entrée stable + entrée experimental éventuelle) |
| Jeton absent / invalide / mauvaise audience | 401 (émis par Easy Auth) |
| Segment inconnu (dont l'ancien `beta`) | 404 |

## GET /api/stable/FluxCEN.{version}.zip

| Cas | Réponse |
|---|---|
| Jeton valide, blob présent | 200, `Content-Type: application/zip`, corps = artefact (versions finales et préversions) |
| Blob absent | 404 |
| Jeton absent / invalide | 401 |

## Engagements de compatibilité

- Le chemin `/api/stable/plugins.xml` et le schéma des `download_url` sont stables : les postes provisionnés ne sont jamais reconfigurés pour un changement interne du service. Le préfixe `/api` fait partie du contrat.
- Un zip publié est immuable (même URL = même contenu).
