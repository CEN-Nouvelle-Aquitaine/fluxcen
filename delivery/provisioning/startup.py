# -*- coding: utf-8 -*-
"""startup.py FluxCEN — déployé par Intune dans profiles/default/python/.

QGIS exécute ce fichier à chaque démarrage. Il provisionne l'authcfg de
delivery et les dépôts de plugins, puis rend la main : aucune exception ne
doit s'échapper (contrat provisioning.md : innocuité). provision.py doit être
déployé à côté de ce fichier.
"""
import os
import sys

# URL de base du service de distribution, préfixe /api inclus (posée au
# déploiement Intune). Dépôt unique : les beta-testeurs cochent simplement
# « Afficher aussi les extensions expérimentales » (standard communautaire).
FLUXCEN_DELIVERY_URL = "https://func-fluxcen-delivery-poc.azurewebsites.net/api"

try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import provision
    provision.provision(FLUXCEN_DELIVERY_URL)
except Exception:  # pylint: disable=broad-except
    pass  # jamais bloquer le démarrage de QGIS, provision journalise déjà
