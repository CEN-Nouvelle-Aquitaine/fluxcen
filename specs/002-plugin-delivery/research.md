# Research: Système de delivery privé du plugin FluxCEN

**Date**: 2026-08-18 | **Plan**: [plan.md](plan.md)

Recherche menée par trois agents parallèles (client QGIS, hébergement, CI/CD) le 2026-08-18. Les sources sont listées en fin de document.

## R1. Capacités d'authentification du gestionnaire d'extensions QGIS

**Decision**: s'appuyer sur l'authcfg du dépôt de plugins : QGIS l'applique au fetch de `plugins.xml` ET au téléchargement du zip.

**Rationale**: vérifié dans le code source (branche `release-3_44`) : `installer_data.py` (`Repositories.requestFetching()`) et `qgsplugininstallerinstallingdialog.py` (`requestDownloading()`) passent tous deux par `QgsApplication.authManager().updateNetworkRequest()` puis `QgsNetworkAccessManager`. N'importe quelle méthode d'auth fonctionne, dont OAuth2 (header `Authorization: Bearer`, refresh silencieux via `refreshSynchronous()` tant que le refresh token est valide).

**Contraintes découvertes** (structurent toute la conception) :
- L'URL de dépôt ne doit contenir aucune query string : QGIS concatène brutalement `?qgis=x.y`.
- QGIS 3.34 ne suit pas les 302 sur `plugins.xml` (seul le 301 est géré) ; 3.44 les suit. Pour le zip, 301/302 sont suivis (max 4) mais **l'authcfg est réappliqué à chaque redirection**, donc le Bearer est rejoué vers l'hôte cible.
- Défaut QGIS #64885 (non corrigé) : plantage possible si le check des dépôts au démarrage déclenche le flow OAuth2 interactif. Parade : check au démarrage désactivé + provisioning qui garantit un jeton valide avant activation du dépôt.

**Alternatives considered**: aucune (c'est le comportement du client imposé ; les contraintes ci-dessus éliminent des options d'hébergement, voir R2).

## R2. Service de distribution

**Decision**: Azure Function (plan Flex Consumption, `francecentral`) derrière Easy Auth, servant `plugins.xml` et les zips en 200 direct depuis un Blob Storage privé (managed identity). Audience du jeton : scope custom exposé par l'app registration « QGIS » existante.

**Rationale**:
- Easy Auth accepte les Bearer tokens Entra de clients non-navigateur et valide audience et issuer sans code.
- Réponse en 200 direct : supprime d'un coup les trois pièges de R1 (302, query string, rejeu du Bearer).
- Restriction beta appliquée côté serveur via le claim `groups` du jeton (~30 lignes de logique pure).
- Coût ≈ 0 € à ce trafic (franchise Flex Consumption), Easy Auth gratuit.
- Un authcfg ne porte qu'une audience : l'app « QGIS » expose un scope `api://…/plugins.read` et reste son propre client autorisé ; le flux PKCE, le port 17070 et l'app ne changent pas.

**Alternatives considered**:
- **SharePoint/Graph direct** (`/content`) : rejeté. 302 vers URL pré-signée `tempauth` ; QGIS rejoue le Bearer Graph sur cette URL (401 « invalid audience » documenté côté SDK Microsoft) ; 3.34 ne suit pas les 302 sur le XML ; aucun précédent public.
- **Liens de partage SharePoint** (objet de la feature 001) : rejetés comme URL de dépôt. Query string interdite + auth par cookies.
- **SharePoint REST `/_api/web/GetFileByServerRelativeUrl('…')/$value`** : répond 200 direct avec Bearer d'audience SPO (`https://{tenant}.sharepoint.com/AllSites.Read`). **Plan B conservé** (zéro infra, permissions par dossier) mais non retenu : jamais éprouvé publiquement avec le plugin manager, et audience différente de l'API custom.
- **Azure Static Web Apps** : auth par cookie, inutilisable par un client non-navigateur.
- **Blob Storage direct** : exige l'audience `storage.azure.com` et le header `x-ms-version`, que QGIS n'envoie pas.
- **APIM Consumption** : fonctionnellement équivalent à Easy Auth ici, plus complexe (policies XML). Rien de plus.
- **Azure Artifacts** (cible pressentie initialement) : inadapté à la distribution end-user (outillage az/PAT requis, audience DevOps, pas de GET simple). Écarté définitivement.
- **AWS** : rien de natif Entra, code custom à maintenir. Écarté.
- **Basic auth sur serveur web** : éprouvé côté QGIS mais gestion de mots de passe hors SSO Entra, contraire à l'objectif.

## R3. Outil IaC

**Decision** (révisée 2026-08-18, décision d'Antoine): **Terraform** (providers `azurerm` + `azuread` + `azapi`). Le premier choix (Bicep) est remplacé.

**Rationale**: alignement avec la pratique CEN : Terraform est le standard des projets récents (landing zones AWS) et l'outil agnostique du cloud ; Azure n'est présent au CEN que via Microsoft 365, pas comme backend principal. Bonus décisif : le provider `azuread` pilote les objets Entra (scope API, claim `groups`, groupe beta, federated credentials), ce qui absorbe dans l'IaC les deux scripts de bootstrap prévus initialement. L'app « QGIS » existante est reprise par un bloc `import` déclaratif + ressources granulaires (`azuread_application_registration`, `_permission_scope`, `_identifier_uri`, `_pre_authorized`), sans toucher à ses autres propriétés, avec `prevent_destroy`.

**Alternatives considered**: Bicep (natif, zéro backend d'état, mais hors standard d'équipe et aveugle aux objets Entra) ; ClickOps portail (non auditable, contraire à FR-011).

**Limites assumées**: backend d'état à brancher sur le standard CEN avant industrialisation (état local pour le POC) ; `authsettingsV2` (Easy Auth) passe par `azapi` tant que `azurerm` ne le porte pas sur la ressource Flex Consumption ; le stockage runtime de la Function reste en connection string (bug provider sur le mode managed identity du runtime Flex), la lecture des plugins par le code restant en managed identity.

## R4. Canaux et versionnage

**Decision** (corrigée au POC) : deux dépôts logiques servis par la même Function : `/api/stable/plugins.xml` (tout le tenant) et `/api/beta/plugins.xml` (groupe Entra beta). Chaque catalogue ne liste QUE la dernière version de son canal ; les beta-testeurs enregistrent les deux dépôts et la fusion multi-dépôts de QGIS propose la plus haute (vérifié en réel : le format de dépôt n'admet qu'une entrée par plugin et par catalogue, la seconde écrase la première). Versions SemVer avec suffixe pré-release (`5.4.0-beta.1`) ; le canal est déduit du tag (`v5.4.0` → stable, `v5.4.0-beta.1` → beta).

**Rationale**: le flag `experimental` de QGIS est un filtre d'affichage global côté client, pas un contrôle d'accès : inutilisable pour restreindre la beta. `version_compare.py` de QGIS ordonne en PEP 440 : `5.4.0-beta.1 < 5.4.0`, donc un beta-testeur rebascule automatiquement sur la stable quand elle dépasse sa beta. Un seul dépôt à enregistrer pour les beta-testeurs.

**Alternatives considered**: un seul dépôt avec flag `experimental` (pas un contrôle d'accès, et impose une manip utilisateur) ; deux Function séparées (double infra sans bénéfice).

## R5. Pipeline de publication

**Decision**: un workflow `release.yml` déclenché par tag : `qgis-plugin-ci package` construit le zip et génère `plugins.xml` (`--plugin-repo-url`), `qgis-plugin-repo merge` maintient le catalogue multi-versions du canal beta, upload vers Blob via `azure/login` en OIDC (federated credential sur le repo), release GitHub privée en miroir. `infra.yml` déploie le Bicep sur changement de `infra/`.

**Rationale**: `qgis-plugin-ci` est l'outil officiel (génération de dépôt custom supportée, détection automatique des suffixes pré-release) ; OIDC supprime tout secret stocké (FR-010, SC-005) ; le miroir GitHub Releases conserve un historique gratuit des artefacts.

**Ajout post-POC (FR-016)**: le POC a montré que le zip issu de `git archive` ne contient pas `config/yaml/links.yaml` (liens du catalogue, volontairement hors git : gitignore + contrôle CI) et que le plugin installé est alors sans catalogue. Décision : injection à la release : le workflow écrit le fichier depuis le secret d'environnement `LINKS_YAML` puis `asset_paths` de qgis-plugin-ci l'ajoute au zip. Alternatives rejetées : committer le fichier (casse l'invariant CI, expose les liens à tout lecteur du repo), dépôt par Intune (changer un lien = redéployer le parc), endpoint de config sur la Function (mécanisme de plus, YAGNI).

**Alternatives considered**: script maison de génération XML (réinvention) ; publication vers SharePoint via Graph `Sites.Selected` (retenu dans la recherche comme viable, mais devenu inutile : la cible est le blob ; à ressusciter seulement si le plan B SharePoint est activé).

## R6. Provisioning des postes

**Decision**: `startup.py` déployé par Intune dans le profil QGIS (`profiles/default/python/startup.py`). Idempotent : crée ou répare l'authcfg de delivery (OAuth2 PKCE, scope `api://…/plugins.read`, port 17070 avec sonde et repli), enregistre le dépôt stable (et beta si l'utilisateur est du groupe), laisse le check au démarrage désactivé. Logique dans `provision.py` (testable), `startup.py` réduit à l'appel.

**Rationale**: l'authcfg vit dans la base d'authentification chiffrée de QGIS : impossible à livrer par fichier ini ; un code PyQGIS au démarrage est la pratique standard en parc géré. La sonde de port répond au piège AnyDesk/7070 déjà documenté (Entra ignore le port des URI de loopback, RFC 8252 : aucun changement portail au repli).

**Alternatives considered**: plugin bootstrap distribué en zip (plan B si Intune indisponible pour un poste) ; `QGIS_GLOBAL_SETTINGS_FILE` (ne couvre pas l'authcfg) ; déploiement de la base d'auth complète (`QGIS_AUTH_DB_DIR_PATH`) (lourd, fragile).

**Note**: l'authcfg de delivery est distinct de l'authcfg Graph du plugin (feature 001, scope `Files.Read.All`) : une audience par authcfg. Même app registration, deux configs.

## R7. Périmètre du POC

**Decision**: resource group dédié `rg-fluxcen-delivery-poc`, détruit/recréé à volonté par le Bicep. Le POC valide : (1) fetch du catalogue authentifié dans QGIS 3.34 et 3.44, (2) installation et mise à jour du zip, (3) 401 sans jeton / hors tenant, (4) 403 beta pour un non-membre, (5) refresh silencieux du jeton. Critère d'arrêt : les 5 points verts = industrialisation ; un point rouge insoluble = activation du plan B SharePoint `/$value`.

**Rationale**: FR-014 impose le POC avant industrialisation ; le resource group jetable prouve en même temps SC-006 (recréation depuis zéro).

## Sources principales

- Code QGIS : `installer_data.py`, `qgsplugininstallerinstallingdialog.py`, `version_compare.py`, `qgsauthoauth2method.cpp` (github.com/qgis/QGIS, branche release-3_44)
- Issues QGIS : #64885 (crash OAuth2 au démarrage), #52729 (refresh expiré)
- Microsoft Learn : Easy Auth + Entra (`configure-authentication-provider-aad`), authsettingsV2 (`allowedPrincipals.groups`), Graph driveItem `/content` (302 pré-signé), autorisation Blob (audience + `x-ms-version`), SWA auth custom (cookies), APIM `validate-azure-ad-token`, workload identity federation GitHub
- Bug 302+Bearer : msgraph-sdk-dotnet #3057, Microsoft Q&A (401 `download.aspx`)
- Outillage : github.com/qgis/qgis-plugin-ci (option `--plugin-repo-url`), pypi.org/project/qgis-plugin-repo (merge), docs.qgis.org 3.44 (dépôts authentifiés)
