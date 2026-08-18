# Provisioning des postes (Intune)

Déploie le dépôt de plugins FluxCEN privé sur un poste QGIS sans aucune
manipulation de l'utilisateur. Contrat : `specs/002-plugin-delivery/contracts/provisioning.md`.

## Fichiers à déployer

Copier dans le profil QGIS du poste (`%APPDATA%\QGIS\QGIS3\profiles\default\python\`
sous Windows, `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/`
sous macOS) :

| Fichier | Rôle |
|---|---|
| `startup.py` | exécuté par QGIS à chaque démarrage ; appelle `provision.py` |
| `provision.py` | crée/répare l'authcfg « FluxCEN delivery » et enregistre les dépôts |
| `fluxcen-beta.enabled` | optionnel : fichier vide, sa présence active le dépôt beta |

Avant déploiement, ajuster `FLUXCEN_DELIVERY_URL` dans `startup.py`
(URL de la Function, sortie du déploiement Bicep).

## Comportement

- Idempotent : rejouable à chaque démarrage, ne réécrit rien si conforme.
- Répare : port de redirection occupé (AnyDesk sur 7070 : liste 17070-17072),
  URL de dépôt dérivée, authcfg au mauvais scope ou avec secret vestigial.
- Ne touche pas à l'authcfg Graph du plugin (`g2b2197`).
- Laisse « vérifier les mises à jour au démarrage » désactivé (défaut QGIS #64885).
- N'empêche jamais le démarrage de QGIS ; journalise dans l'onglet FluxCEN.

## Intune

Déploiement en « platform script » / fichier géré : copie des fichiers
ci-dessus, ré-exécution sans précaution (idempotent). Retrait : supprimer
`startup.py` et `provision.py` du profil (l'authcfg et les dépôts restent,
les retirer via QGIS si nécessaire).

## Plan B sans Intune

Envoyer un zip « plugin bootstrap » à installer une fois par l'utilisateur :
il exécute la même logique `provision.provision(...)` à l'installation.
À construire seulement si un poste échappe à Intune (YAGNI).
