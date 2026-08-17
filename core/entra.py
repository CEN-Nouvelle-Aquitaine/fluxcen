# -*- coding: utf-8 -*-
"""Configuration Microsoft Entra ID canonique de FluxCEN (FR-013).

Fonctions pures (stdlib uniquement) — data-model :
specs/001-sharepoint-share-urls/data-model.md (ConfigurationMicrosoftCanonique).

Le plugin provisionne lui-même cette configuration dans le gestionnaire
d'authentification QGIS (pattern Mergin Maps) : identifiant fixe, flux
Authorization Code PKCE, client public Entra — **aucun secret nulle part**,
le client ID et le tenant sont des identifiants publics par conception.
La release est la source de vérité : une mise à jour de l'authentification
passe par une release du plugin.
"""
import json
import socket
from typing import Callable, Optional

AUTHCFG_ID = "g2b2197"
AUTHCFG_NAME = "Microsoft CEN"

_CLIENT_ID = "80c3a908-e890-4575-9a46-785116e160f9"
_TENANT = "898a7ac2-f878-44ab-80f0-1e1852b7bebd"
_TOKEN_URL = f"https://login.microsoftonline.com/{_TENANT}/oauth2/v2.0/token"

# Ports de redirection loopback, essayés dans l'ordre. Entra ignore le port
# des URI ``127.0.0.1`` (RFC 8252) : aucun changement côté portail. Le 7070
# historique est exclu : AnyDesk (souvent déployé) écoute dessus et tue le
# flux OAuth sans aucun message.
REDIRECT_PORTS = (17070, 17071, 17072)


def canonical_oauth2_config(port: int) -> dict:
    """Paramètres OAuth2 canoniques (clé ``oauth2config`` du gestionnaire QGIS).

    Calqués sur la configuration validée en réel le 2026-08-17 :
    ``grantFlow`` 3 = Authorization Code PKCE, secret vide (client public).
    """
    return {
        "accessMethod": 0,  # jeton porté en en-tête Authorization
        "apiKey": "",
        "clientId": _CLIENT_ID,
        "clientSecret": "",
        "configType": 1,  # configuration personnalisée (non prédéfinie)
        "customHeader": "",
        "description": "",
        "grantFlow": 3,  # Authorization Code PKCE
        "id": "",
        "name": "",
        "objectName": "",
        "password": "",
        "persistToken": True,
        "queryPairs": {},
        "redirectHost": "127.0.0.1",
        "redirectPort": port,
        "redirectUrl": "qgis-client",
        "refreshTokenUrl": _TOKEN_URL,
        "requestTimeout": 30,
        "requestUrl": f"https://login.microsoftonline.com/{_TENANT}/oauth2/v2.0/authorize",
        "scope": "https://graph.microsoft.com/Files.Read.All offline_access",
        "tokenUrl": _TOKEN_URL,
        "username": "",
        "version": 1,
    }


def stored_redirect_port(stored_json: str) -> Optional[int]:
    """Port de redirection d'une config stockée, ou None si illisible."""
    try:
        port = json.loads(stored_json).get("redirectPort")
        return port if isinstance(port, int) else None
    except (ValueError, AttributeError):
        return None


# Clés comparées entre config stockée et canon. Les clés de présentation
# (id, name, objectName, description, version) sont exclues : QGIS peut les
# resérialiser différemment, elles ne doivent pas déclencher de mise à jour.
_COMPARED_KEYS = frozenset({
    "accessMethod", "apiKey", "clientId", "clientSecret", "configType",
    "customHeader", "grantFlow", "password", "persistToken", "queryPairs",
    "redirectHost", "redirectUrl", "refreshTokenUrl", "requestTimeout",
    "requestUrl", "scope", "tokenUrl", "username",
})


def config_needs_update(stored_json: str) -> bool:
    """Vraie ssi la config stockée diverge du canon.

    Le port de redirection est libre de varier dans ``REDIRECT_PORTS``
    (auto-réparation en cas de port occupé) ; toute autre divergence sur les
    clés fonctionnelles — dont un secret vestigial — déclenche la mise à jour.
    """
    try:
        stored = json.loads(stored_json)
    except ValueError:
        return True
    if not isinstance(stored, dict):
        return True
    port = stored.get("redirectPort")
    if port not in REDIRECT_PORTS:
        return True
    reference = canonical_oauth2_config(port)
    return any(stored.get(key) != reference[key] for key in _COMPARED_KEYS)


def port_is_free(port: int) -> bool:
    """Vraie ssi le port loopback est libre (sonde par bind local)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def pick_free_port(is_free: Callable[[int], bool]) -> Optional[int]:
    """Premier port libre de ``REDIRECT_PORTS``, ou None s'ils sont tous occupés."""
    for port in REDIRECT_PORTS:
        if is_free(port):
            return port
    return None
