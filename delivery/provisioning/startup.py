# -*- coding: utf-8 -*-
"""startup.py FluxCEN — déployé par Intune dans profiles/default/python/.

QGIS exécute ce fichier à chaque démarrage. Il provisionne l'authcfg de
delivery et les dépôts de plugins, puis rend la main : aucune exception ne
doit s'échapper (contrat provisioning.md : innocuité). provision.py doit être
déployé à côté de ce fichier.
"""
import os
import sys

# URL du service de distribution (posée au déploiement Intune).
FLUXCEN_DELIVERY_URL = "https://func-fluxcen-delivery-poc.azurewebsites.net"

# Canal beta : activé par fichier marqueur déposé par Intune à côté du script.
_BETA_MARKER = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "fluxcen-beta.enabled")

try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import provision
    provision.provision(FLUXCEN_DELIVERY_URL, beta=os.path.exists(_BETA_MARKER))
except Exception:  # pylint: disable=broad-except
    pass  # jamais bloquer le démarrage de QGIS, provision journalise déjà
