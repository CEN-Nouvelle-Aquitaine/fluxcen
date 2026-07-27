# -*- coding: utf-8 -*-
"""Classification et conversion des URL du périmètre Microsoft.

Fonctions pures (stdlib uniquement) — contrat :
specs/001-sharepoint-share-urls/contracts/core-functions.md

Le périmètre d'authentification Microsoft est limité aux hôtes
``graph.microsoft.com`` et ``*.sharepoint.com`` en HTTPS : seules les requêtes
vers ces destinations peuvent porter la configuration d'authentification
Microsoft (jamais d'expansion du jeton hors de ce périmètre).
"""
from enum import Enum
from urllib.parse import urlsplit

_GRAPH_HOST = "graph.microsoft.com"
_SHAREPOINT_SUFFIX = ".sharepoint.com"


class UrlClass(Enum):
    """Classe d'une URL de ressource, déterminée par son nom d'hôte exact."""

    SHAREPOINT_SHARING_LINK = "sharepoint_sharing_link"
    GRAPH = "graph"
    OTHER = "other"


def _https_hostname(url):
    """Retourne le nom d'hôte (minuscules) si l'URL est HTTPS, sinon None.

    Toute erreur d'analyse est absorbée : une URL malformée est simplement
    hors périmètre, jamais une exception.
    """
    if not isinstance(url, str):
        return None
    try:
        parts = urlsplit(url)
    except ValueError:
        return None
    if parts.scheme.lower() != "https":
        return None
    try:
        hostname = parts.hostname
    except ValueError:
        return None
    return hostname.lower() if hostname else None


def is_microsoft_url(url):
    """Vraie ssi l'URL appartient au périmètre d'authentification Microsoft."""
    hostname = _https_hostname(url)
    if hostname is None:
        return False
    return hostname == _GRAPH_HOST or hostname.endswith(_SHAREPOINT_SUFFIX)


def classify_url(url):
    """Classe une URL de ressource : lien de partage SharePoint, Graph, ou autre."""
    hostname = _https_hostname(url)
    if hostname is None:
        return UrlClass.OTHER
    if hostname.endswith(_SHAREPOINT_SUFFIX):
        return UrlClass.SHAREPOINT_SHARING_LINK
    if hostname == _GRAPH_HOST:
        return UrlClass.GRAPH
    return UrlClass.OTHER
