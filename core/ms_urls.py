# -*- coding: utf-8 -*-
"""Classification et conversion des URL du périmètre Microsoft.

Fonctions pures (stdlib uniquement) — contrat :
specs/001-sharepoint-share-urls/contracts/core-functions.md

Le périmètre d'authentification Microsoft est limité aux hôtes
``graph.microsoft.com`` et ``*.sharepoint.com`` en HTTPS : seules les requêtes
vers ces destinations peuvent porter la configuration d'authentification
Microsoft (jamais d'expansion du jeton hors de ce périmètre).
"""
import base64
from enum import Enum
from urllib.parse import quote, urlsplit

_GRAPH_HOST = "graph.microsoft.com"
_SHAREPOINT_SUFFIX = ".sharepoint.com"
_GRAPH_SHARES_PREFIX = "https://graph.microsoft.com/v1.0/shares/"


class UrlClass(Enum):
    """Classe d'une URL de ressource, déterminée par son nom d'hôte exact."""

    SHAREPOINT_SHARING_LINK = "sharepoint_sharing_link"
    GRAPH = "graph"
    OTHER = "other"


def https_hostname(url):
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
    hostname = https_hostname(url)
    if hostname is None:
        return False
    return hostname == _GRAPH_HOST or hostname.endswith(_SHAREPOINT_SUFFIX)


def classify_url(url):
    """Classe une URL de ressource : lien de partage SharePoint, Graph, ou autre."""
    hostname = https_hostname(url)
    if hostname is None:
        return UrlClass.OTHER
    if hostname.endswith(_SHAREPOINT_SUFFIX):
        return UrlClass.SHAREPOINT_SHARING_LINK
    if hostname == _GRAPH_HOST:
        return UrlClass.GRAPH
    return UrlClass.OTHER


def is_sharepoint_sharing_link(url):
    """Vraie ssi l'URL est un lien SharePoint à résoudre via l'API Graph."""
    return classify_url(url) is UrlClass.SHAREPOINT_SHARING_LINK


def is_graph_shares_url(url):
    """Vraie ssi l'URL est un appel Graph ``/shares/`` (lien de partage résolu).

    Ces appels reçoivent l'en-tête ``Prefer: redeemSharingLinkIfNecessary``,
    que l'URL ait été convertie à la volée ou pré-construite (styles).
    """
    if https_hostname(url) != _GRAPH_HOST:
        return False
    try:
        path = urlsplit(url).path
    except ValueError:
        return False
    return path.startswith("/v1.0/shares/")


def _share_token(url):
    """Encode un lien de partage en jeton ``u!<base64url non paddé>`` (API Graph)."""
    encoded = base64.b64encode(url.encode("utf-8")).decode("ascii")
    return "u!" + encoded.rstrip("=").replace("/", "_").replace("+", "-")


def sharing_link_to_graph_url(url):
    """Convertit un lien de partage (fichier) en URL Graph de téléchargement."""
    if not is_sharepoint_sharing_link(url):
        raise ValueError("Pas un lien de partage SharePoint HTTPS")
    return _GRAPH_SHARES_PREFIX + _share_token(url) + "/driveItem/content"


def sharing_link_to_graph_item_url(folder_share_url, filename):
    """Résout un fichier à l'intérieur d'un dossier partagé (adressage par chemin).

    ``filename`` provient du catalogue distant : tout séparateur de chemin ou
    séquence ``..`` est rejeté pour empêcher de sortir du dossier partagé.
    """
    if not is_sharepoint_sharing_link(folder_share_url):
        raise ValueError("Pas un lien de partage SharePoint HTTPS")
    if (not filename or not isinstance(filename, str)
            or "/" in filename or "\\" in filename or ".." in filename):
        raise ValueError("Nom de fichier de style invalide")
    return (_GRAPH_SHARES_PREFIX + _share_token(folder_share_url)
            + "/driveItem:/" + quote(filename) + ":/content")


_DATABASE_EXCLUDED_AUTH_METHODS = frozenset({"OAuth2"})


def is_database_auth_method(method):
    """Vraie ssi une méthode d'authentification QGIS est utilisable pour une BDD.

    Les méthodes web (OAuth2 — dont Microsoft Entra ID) ne peuvent rien
    injecter dans une connexion PostgreSQL : les appliquer fait échouer la
    connexion et déclenche la fenêtre d'identification de secours de QGIS
    (FR-011). Basic et les méthodes par certificat restent légitimes.
    """
    return method not in _DATABASE_EXCLUDED_AUTH_METHODS


def build_style_url(styles_base, style_name):
    """URL de téléchargement d'un style ``<style_name>.qml``.

    ``styles_base`` est soit une URL directe (concaténation historique), soit un
    lien de partage de dossier SharePoint (résolution par chemin via Graph).
    """
    filename = style_name + ".qml"
    if is_sharepoint_sharing_link(styles_base):
        return sharing_link_to_graph_item_url(styles_base, filename)
    return styles_base + filename
