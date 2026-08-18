# Contrat : script de provisioning des postes

**Support** : `delivery/provisioning/startup.py` (+ `provision.py`), déployé par Intune dans `profiles/default/python/startup.py`. S'exécute dans l'interpréteur Python de QGIS à chaque démarrage.

## Entrées

| Entrée | Source | Défaut |
|---|---|---|
| URL de base du service | constante dans le script (posée au déploiement) | requis |
| liste des ports de repli | constante | `[17070, 17071, 17072]` (alignée sur `core/entra.py` du plugin, feature 001) |

## Postconditions (état garanti après exécution)

1. Un authcfg « FluxCEN delivery » existe : OAuth2 PKCE, app `80c3a908-…`, scope `api://80c3a908-…/plugins.read offline_access`, secret vide, jeton persistant, redirect `127.0.0.1:{port}/qgis-client` avec `{port}` libre (sonde par bind).
2. Le dépôt `FluxCEN (interne)` → `{base}/stable/plugins.xml` est enregistré avec cet authcfg (où `{base}` inclut le préfixe `/api` du service). L'ancien dépôt `FluxCEN (beta)` (design POC abandonné) est retiré s'il existe. L'opt-in beta ne relève pas du provisioning : c'est la case « extensions expérimentales » de QGIS.
3. `checkOnStart` des dépôts reste `false`.
4. L'authcfg Graph du plugin (feature 001) n'est ni lu ni modifié.

## Propriétés

- **Idempotence** : deux exécutions successives = même état ; aucune écriture si l'état est déjà conforme.
- **Réparation** : port devenu occupé, URL de dépôt dérivée ou authcfg supprimé → l'écart est corrigé au démarrage suivant.
- **Innocuité** : toute erreur est journalisée dans `QgsMessageLog` (onglet FluxCEN) et n'empêche jamais le démarrage de QGIS (aucune exception propagée).
- **Silence** : aucune interaction utilisateur ; le premier flow OAuth interactif n'est déclenché que par une action volontaire (installation/mise à jour du plugin), jamais par le script.

## Tests (pytest-qgis)

- Poste vierge → postconditions 1 à 3 vérifiées.
- Ré-exécution sur poste conforme → aucune modification (comparaison avant/après).
- Port 17070 occupé (socket de test) → authcfg créé sur le premier port de repli.
- Authcfg présent mais scope erroné → réparé sans toucher aux autres authcfg.
