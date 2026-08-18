# Quickstart : POC du service de distribution

**Objectif** : valider les 5 points du protocole de POC (research.md R7) sur un environnement jetable, avant toute industrialisation.

## Étape 0 : simulation locale, sans Azure ni push

Valide le mécanisme côté QGIS (authcfg appliqué au catalogue ET au zip, mise à jour en un clic) et le contrat HTTP, sur le poste :

```bash
# 1. Construire le zip (les exclusions export-ignore s'appliquent).
#    Note FR-016 : ce zip de POC ne contient pas config/yaml/links.yaml
#    (injecté par la CI en vrai) ; copier son links.yaml local dans le
#    plugin installé pour tester le chargement du catalogue.
git archive --worktree-attributes --format=zip --prefix=FluxCEN/ \
  -o /tmp/FluxCEN.5.3.0.zip HEAD

# 2. Lancer le dépôt simulé (contrat complet : 401/403/200)
python3 delivery/poc_local_repo.py --zip /tmp/FluxCEN.5.3.0.zip

# 3. Rejouer le contrat
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8787/api/stable/plugins.xml                 # 401
curl -s -o /dev/null -w "%{http_code}\n" -H "Authorization: Bearer poc-interne" \
  "http://127.0.0.1:8787/api/stable/plugins.xml?qgis=3.44"                                                # 200
curl -s -o /dev/null -w "%{http_code}\n" -H "Authorization: Bearer poc-interne" \
  http://127.0.0.1:8787/api/beta/plugins.xml                                                              # 403
```

Dans QGIS : créer un authcfg **API Header** avec la paire `Authorization` = `Bearer poc-interne`, ajouter le dépôt `http://127.0.0.1:8787/api/stable/plugins.xml` avec cet authcfg, vérifier que FluxCEN apparaît et s'installe. Relancer le serveur avec `--version 5.3.1` (même zip) pour vérifier la détection de mise à jour. Le serveur journalise chaque header `Authorization` reçu : preuve que QGIS l'envoie bien sur le XML et sur le zip.

La logique de la Function se teste sans Azure : `pytest tests/test_function_app.py` (SDK requis : `pip install azure-functions azure-storage-blob azure-identity`). Et `terraform plan` dans `infra/` simule la création des ressources sans rien créer (requiert `az login`).

## Prérequis (une fois, manuels et documentés)

1. Souscription Azure active rattachée au tenant CEN (`az account show` la confirme). Si aucune n'existe : création au portail (hors IaC, prérequis de bootstrap).
2. `terraform` ≥ 1.7 et `az` CLI connecté avec un compte pouvant créer un resource group, assigner des rôles et modifier les app registrations.
3. `infra/terraform.tfvars` : renseigner `qgis_app_object_id` (voir `infra/README.md`). L'IaC gère aussi les objets Entra : scope `plugins.read`, claim groups, groupe `FluxCEN-Beta`, identité CI.

## Déploiement

```bash
cd infra
terraform init
terraform plan   # contrôler l'import de l'app « QGIS » au premier passage
terraform apply  # env=poc par défaut
```

Sortie attendue : `function_url` (`https://<app>.azurewebsites.net`). Déposer ensuite un jeu d'essai dans le blob : un zip de FluxCEN et un `plugins.xml` par canal (le workflow `release.yml` le fera en cible ; pour le POC, `az storage blob upload` suffit).

## Vérifications

Terminal (jeton obtenu via le flow device code ou copié depuis la base d'auth QGIS) :

```bash
# 1. Sans jeton → 401
curl -si https://<app>.azurewebsites.net/api/stable/plugins.xml | head -1

# 2. Avec jeton, stable → 200 + XML
curl -si -H "Authorization: Bearer $TOKEN" https://<app>.azurewebsites.net/api/stable/plugins.xml | head -1

# 3. Beta, compte non-membre → 403 ; membre → 200
curl -si -H "Authorization: Bearer $TOKEN" https://<app>.azurewebsites.net/api/beta/plugins.xml | head -1
```

Dans QGIS (3.34 puis 3.44) :

1. Créer l'authcfg « FluxCEN delivery » (PKCE, scope `api://…/plugins.read offline_access`, port 17070) : mêmes réglages que la config validée g2b2197, seul le scope change.
2. Extensions → Paramètres → Ajouter le dépôt `https://<app>.azurewebsites.net/api/stable/plugins.xml` avec cet authcfg.
3. Vérifier : la liste se charge, FluxCEN apparaît, l'installation aboutit, puis publier une version supérieure et vérifier la détection et la mise à jour en un clic.
4. Laisser expirer le jeton d'accès (~1 h) et refaire une mise à jour : aucun prompt (refresh silencieux).

## Résultats du POC (2026-08-18, env poc réel)

| Point | Résultat |
|---|---|
| 1. Catalogue authentifié dans QGIS | ✅ 3.44 (3.34 restant à faire, conteneur) |
| 2. Installation et mise à jour du zip | ✅ mise à jour 5.3.0 → 5.3.1 en un clic |
| 3. 401 sans jeton / hors tenant | ✅ curl |
| 4. Beta : 403 non-membre / 200 membre | ✅ des deux côtés (ajout au groupe + purge des jetons) |
| 5. Refresh silencieux | à confirmer à l'usage (~1 h) |

Enseignements consignés : `azapi_update_resource` + `platform.enabled` pour l'Easy Auth ; préfixe `/api` gardé (standard Azure) ; artefact auto-suffisant requis (FR-016, injection de links.yaml) ; après modification d'appartenance au groupe beta, l'effet attend un jeton **neuf** (purge des jetons dans Options → Authentification → Utilitaires, sinon ~1 h) ; ne jamais mettre à jour un plugin installé en lien symbolique (l'installeur remplace l'entrée) ; **un seul candidat par plugin et par catalogue** (la 2e entrée d'un même plugins.xml écrase la 1re) : le repli beta→stable passe par la fusion multi-dépôts de QGIS, vérifiée en réel (la plus haute version des deux dépôts gagne).

## Critère d'arrêt

- **5/5 verts** : industrialisation (provisioning Intune, workflow release, migration).
- **Un point rouge insoluble** : activer le plan B SharePoint REST `/$value` (research.md R2) et re-dérouler ce quickstart contre lui.

## Nettoyage

```bash
cd infra
terraform state rm azuread_application_registration.qgis  # ne pas détruire l'app de prod importée
terraform destroy
```

Recréer ensuite par `terraform apply` seul : c'est la preuve de SC-006.
