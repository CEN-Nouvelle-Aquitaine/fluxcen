# -*- coding: utf-8 -*-
"""Construction des URI de couches WMS/WFS et périmètre sécurisé du CEN.

Fonctions pures (stdlib uniquement) — centralisation de la création de
couches (issue #52). Le parsing du catalogue reste dans ``core/catalog.py``.
"""
import re
from typing import Optional
from urllib.parse import urlsplit

from .ms_urls import https_hostname

_DEFAULT_SERVICE_VERSION = "1.0.0"

# Geoserver du CEN : la majorité de ses espaces de travail est publique.
_CEN_GEOSERVER_HOST = "opendata.cen-nouvelle-aquitaine.org"

# Seuls ces espaces de travail exigent une authentification (FR-012, liste
# exhaustive confirmée par le CEN en revue de PR) : jamais la configuration
# Microsoft, uniquement une méthode non web (FR-011). Les autres espaces
# restent accessibles sans authentification.
_CEN_SECURED_WORKSPACES = frozenset({
    "fonciercen",
    "chirokollect",
    "data_gods_dsne",
})


def extract_service_version(url: str) -> str:
    """Version du service extraite de l'URL (motif historique VERSION=…&REQUEST)."""
    match = re.search("VERSION=(.+?)&REQUEST", url)
    return match.group(1) if match else _DEFAULT_SERVICE_VERSION


def cen_workspace(url: str) -> Optional[str]:
    """Espace de travail geoserver ciblé par l'URL, None hors du geoserver CEN.

    Les deux formes du catalogue sont acceptées : ``/geoserver/<workspace>/…``
    et ``/<workspace>/…``.
    """
    if https_hostname(url) != _CEN_GEOSERVER_HOST:
        return None
    segments = [part for part in urlsplit(url).path.split("/") if part]
    if segments and segments[0] == "geoserver":
        segments = segments[1:]
    return segments[0] if len(segments) > 1 else None


def is_cen_secured_service(url: str) -> bool:
    """Vraie ssi l'URL cible un espace de travail sécurisé du geoserver CEN (FR-012)."""
    return cen_workspace(url) in _CEN_SECURED_WORKSPACES


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
