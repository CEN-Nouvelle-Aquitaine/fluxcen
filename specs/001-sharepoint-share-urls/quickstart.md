# Quickstart: 001-sharepoint-share-urls

## Pour l'administrateur (après implémentation)

1. Dans SharePoint, naviguer jusqu'au fichier (ex. `flux.csv`) → **Partager** → **Copier le lien**.
2. Coller le lien tel quel dans `config/yaml/links.yaml`, clé `github_urls.flux_csv`.
3. Vérifier que `auth.authcfg` référence la config OAuth2 Entra ID de QGIS (voir `links_example.yaml`).
4. Ouvrir le plugin FluxCEN : le catalogue se charge (éventuelle fenêtre de connexion Microsoft au
   premier accès, portée par QGIS).

## Pour le développeur

### Environnement de test

```bash
# Tests purs sur un poste SANS QGIS : installer pytest seul
# (pytest-qgis importe qgis à la collecte et échouerait)
pip install pytest
pytest tests/test_ms_urls.py tests/test_catalog.py tests/test_errors.py

# Suite complète (nécessite QGIS ≥ 3.44 installé, ou l'image Docker) :
pip install pytest pytest-qgis
pytest tests/

# macOS avec QGIS-LTR.app : utiliser le Python embarqué de QGIS
APP=/Applications/QGIS-LTR.app
export PYTHONHOME=$APP/Contents/Frameworks
export QGIS_PREFIX_PATH=$APP/Contents/MacOS
export QT_QPA_PLATFORM=offscreen
$APP/Contents/MacOS/python3.12 -m pip install --user pytest pytest-qgis  # une seule fois
$APP/Contents/MacOS/python3.12 -m pytest tests/
docker run --rm -v "$PWD":/src -w /src qgis/qgis:3.44 sh -c \
  "pip3 install pytest pytest-qgis && pytest tests/"
```

### Vérification de bout en bout

1. Configurer `links.yaml` avec un lien de partage SharePoint du tenant CEN.
2. Lancer QGIS ≥ 3.44 avec le plugin (symlink du dépôt dans le dossier plugins du profil).
3. Démarrage : aucune requête réseau, aucun gel, plugin chargé même hors ligne.
4. Ouvrir FluxCEN : catalogue téléchargé et catégories affichées.
5. Onglet réseau (débogueur QGIS / proxy local) : l'en-tête d'auth n'apparaît que vers
   `graph.microsoft.com` / `*.sharepoint.com` ; styles publics partent anonymes.
6. Ajouter une couche WMS/WFS tierce : aucune authcfg attachée à l'URI de la couche.
7. Panneau Journal (`QgsMessageLog`, onglet « FluxCEN ») : messages sans jeton ni URL complète.

### Traçabilité exigences → tests (T027, vérifiée le 2026-07-27)

| Exigence | Tests verts |
|---|---|
| FR-001 (liens de partage, fichiers + dossier styles) | `test_ms_urls.py::TestSharingLinkToGraphUrl/TestSharingLinkToGraphItemUrl/TestBuildStyleUrl` |
| FR-002 (résolution automatique via auth QGIS) | `test_fetch.py::TestResolutionLienDePartage` |
| FR-003 (rétrocompat URL Graph) | `test_fetch.py::test_url_graph_directe_inchangee` |
| FR-004 (auth restreinte au périmètre Microsoft) | `test_fetch.py::TestFiltragePerimetreAuth` |
| FR-005 (correspondance de domaine stricte) | `test_ms_urls.py::TestIsMicrosoftUrl` (cas hostiles) |
| FR-006 (HTTPS obligatoire, data: toléré) | `test_fetch.py::test_http_rejete_sans_requete`, `test_data_url_toleree_sans_auth` |
| FR-007 (aucun secret dans logs/messages) | `test_errors.py::test_jamais_d_url_complete_ni_de_jeton` |
| FR-008 (échec non fatal) | `test_startup.py::TestEchecReseauNonFatal` |
| FR-009 (aucun réseau au démarrage) | `test_startup.py::TestAucunReseauALImport` (+ initGui sous fetch défaillant) |
| FR-010 (couches WMS/WFS sans authcfg) | `test_layers.py` (URI pures + garde sur le code) |
| FR-011 (jamais d'auth web/Microsoft sur PostGIS) | `test_ms_urls.py::TestIsDatabaseAuthMethod`, `test_postgis_auth.py` |
| FR-012 (auth non web sur le service sécurisé CEN) | `test_catalog.py::TestIsCenSecuredService`, `TestBuildWmsUriAuthcfg` |

### Cas d'erreur à rejouer

| Scénario | Résultat attendu |
|---|---|
| Lien de partage invalide/expiré | message « lien invalide », plugin utilisable |
| Compte sans accès au fichier | message « accès refusé » |
| `authcfg` vide + URL SharePoint | message « configurez l'authentification » |
| Réseau coupé au démarrage de QGIS | QGIS démarre, plugin chargé, message à l'ouverture du dialogue |
| URL `http://` dans links.yaml | rejet explicite, aucune requête authentifiée |
