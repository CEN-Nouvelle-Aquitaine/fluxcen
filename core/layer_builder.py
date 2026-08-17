# -*- coding: utf-8 -*-
"""Construction des URI de couches WMS/WFS et périmètre sécurisé du CEN.

Fonctions pures (stdlib uniquement) — centralisation de la création de
couches (issue #52). Le parsing du catalogue reste dans ``core/catalog.py``.
"""
import re
from typing import Optional

from .ms_urls import https_hostname

_DEFAULT_SERVICE_VERSION = "1.0.0"

# Services cartographiques du CEN nécessitant une authentification (FR-012) —
# jamais la configuration Microsoft, uniquement une méthode non web (FR-011).
_CEN_SECURED_HOSTS = frozenset({"opendata.cen-nouvelle-aquitaine.org"})


def extract_service_version(url: str) -> str:
    """Version du service extraite de l'URL (motif historique VERSION=…&REQUEST)."""
    match = re.search("VERSION=(.+?)&REQUEST", url)
    return match.group(1) if match else _DEFAULT_SERVICE_VERSION


def is_cen_secured_service(url: str) -> bool:
    """Vraie ssi l'URL cible un service cartographique sécurisé du CEN (FR-012)."""
    return https_hostname(url) in _CEN_SECURED_HOSTS


def build_wms_uri(url: str, nom_technique: str, version: Optional[str] = None,
                  authcfg: Optional[str] = None) -> str:
    """URI de couche WMS.

    ``authcfg`` n'est ajoutée que si elle est fournie explicitement — réservée
    au périmètre sécurisé du CEN (FR-012), jamais par défaut (FR-010).
    """
    version = version or extract_service_version(url)
    uri = (
        f"url={url}&"
        f"service=WMS&"
        f"version={version}&"
        f"crs=EPSG:2154&"
        f"format=image/png&"
        f"layers={nom_technique}&"
        f"styles"
    )
    if authcfg:
        uri += f"&authcfg={authcfg}"
    return uri


def build_wfs_uri_params(url: str, typename: str, version: Optional[str] = None) -> dict:
    """Paramètres d'URI de couche WFS — sans aucune configuration d'authentification (FR-010)."""
    return {
        "url": url,
        "version": version or extract_service_version(url),
        "typename": typename,
        "request": "GetFeature",
    }
