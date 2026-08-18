# -*- coding: utf-8 -*-
"""Provisioning du poste : authcfg delivery + dépôts de plugins FluxCEN.

Contrat : specs/002-plugin-delivery/contracts/provisioning.md.
Déployé par Intune avec startup.py, AVANT que le plugin soit installé :
ce module est volontairement autonome (il ne peut pas importer ``core.entra``
du plugin) ; les primitives canoniques en sont reprises, avec le scope de
l'API de delivery à la place du scope Graph. Les imports QGIS restent locaux
aux fonctions pour garder la partie pure testable sans QGIS.
"""
import json
import socket
from typing import Callable, Optional

# Authcfg dédié au dépôt de plugins : distinct de l'authcfg Graph du plugin
# (g2b2197, feature 001) — une audience de jeton par authcfg.
AUTHCFG_ID = "f2deliv"
AUTHCFG_NAME = "FluxCEN delivery"

_CLIENT_ID = "80c3a908-e890-4575-9a46-785116e160f9"
_TENANT = "898a7ac2-f878-44ab-80f0-1e1852b7bebd"
_TOKEN_URL = f"https://login.microsoftonline.com/{_TENANT}/oauth2/v2.0/token"
SCOPE = f"api://{_CLIENT_ID}/plugins.read offline_access"

# Alignés sur core/entra.py : 7070 exclu (AnyDesk), Entra ignore le port des
# URI loopback (RFC 8252).
REDIRECT_PORTS = (17070, 17071, 17072)

_STABLE_REPO = "FluxCEN (interne)"
_BETA_REPO = "FluxCEN (beta)"
_REPO_GROUP = "app/plugin_repositories"
_CHECK_ON_START_KEY = "app/plugin_installer/checkOnStart"


def canonical_oauth2_config(port: int) -> dict:
    """Paramètres OAuth2 canoniques (mêmes réglages validés que g2b2197,
    seul le scope change : audience API de delivery)."""
    return {
        "accessMethod": 0,  # jeton porté en en-tête Authorization
        "apiKey": "",
        "clientId": _CLIENT_ID,
        "clientSecret": "",
        "configType": 1,
        "customHeader": "",
        "description": "",
        "extraTokens": {},
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
        "scope": SCOPE,
        "tokenUrl": _TOKEN_URL,
        "username": "",
        "version": 1,
    }


_COMPARED_KEYS = frozenset({
    "accessMethod", "apiKey", "clientId", "clientSecret", "configType",
    "customHeader", "grantFlow", "password", "persistToken", "queryPairs",
    "redirectHost", "redirectUrl", "refreshTokenUrl", "requestTimeout",
    "requestUrl", "scope", "tokenUrl", "username",
})


def _norm(value):
    """Normalise la sérialisation QGIS : une chaîne vide devient ``null``."""
    return "" if value is None else value


def config_needs_update(stored_json: str) -> bool:
    """Vraie ssi la config stockée diverge du canon (port de repli admis)."""
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
    return any(_norm(stored.get(key)) != _norm(reference[key])
               for key in _COMPARED_KEYS)


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
    """Premier port libre de ``REDIRECT_PORTS``, ou None si tous occupés."""
    for port in REDIRECT_PORTS:
        if is_free(port):
            return port
    return None


def desired_repositories(base_url: str, beta: bool = False) -> dict:
    """Dépôts à enregistrer : nom → URL de catalogue (jamais de query string)."""
    base = base_url.rstrip("/")
    repos = {_STABLE_REPO: f"{base}/stable/plugins.xml"}
    if beta:
        repos[_BETA_REPO] = f"{base}/beta/plugins.xml"
    return repos


def ensure_repositories(settings, base_url: str, authcfg_id: str,
                        beta: bool = False) -> bool:
    """Enregistre/répare les dépôts dans QgsSettings. Renvoie True si modifié."""
    changed = False
    for name, url in desired_repositories(base_url, beta).items():
        prefix = f"{_REPO_GROUP}/{name}/"
        desired = {"url": url, "authcfg": authcfg_id, "enabled": True}
        for key, value in desired.items():
            if settings.value(prefix + key) != value:
                settings.setValue(prefix + key, value)
                changed = True
    # FR-013 : jamais de vérification des dépôts au démarrage (défaut QGIS
    # #64885 : le flow OAuth interactif déclenché au démarrage peut planter).
    if settings.value(_CHECK_ON_START_KEY, type=bool):
        settings.setValue(_CHECK_ON_START_KEY, False)
        changed = True
    return changed


def ensure_authcfg(manager) -> Optional[str]:
    """Provisionne/répare l'authcfg delivery. Renvoie l'id, ou None si échec.

    Même logique que le provisionnement Graph du plugin (FluxCEN.py,
    _ensure_microsoft_authcfg) : ID fixe, réparation silencieuse si dérive ou
    port occupé, la release est la source de vérité.
    """
    # pylint: disable-next=import-outside-toplevel
    from qgis.core import QgsAuthMethodConfig  # import local : partie pure testable sans QGIS

    exists = AUTHCFG_ID in manager.availableAuthMethodConfigs()
    if exists:
        loaded = QgsAuthMethodConfig()
        manager.loadAuthenticationConfig(AUTHCFG_ID, loaded, True)
        stored_json = loaded.configMap().get("oauth2config", "")
        try:
            stored_port = json.loads(stored_json).get("redirectPort")
        except (ValueError, AttributeError):
            stored_port = None
        if (not config_needs_update(stored_json)
                and stored_port is not None and port_is_free(stored_port)):
            return AUTHCFG_ID
    port = pick_free_port(port_is_free)
    if port is None:
        return None
    config = QgsAuthMethodConfig()
    config.setId(AUTHCFG_ID)
    config.setName(AUTHCFG_NAME)
    config.setMethod("OAuth2")
    config.setConfigMap({"oauth2config": json.dumps(canonical_oauth2_config(port))})
    stored = (manager.updateAuthenticationConfig(config) if exists
              else manager.storeAuthenticationConfig(config, True))
    return AUTHCFG_ID if stored else None


def provision(base_url: str, beta: bool = False) -> None:
    """Point d'entrée du startup.py : authcfg + dépôts, journalisé, sans levée."""
    # pylint: disable-next=import-outside-toplevel
    from qgis.core import QgsApplication, QgsMessageLog, QgsSettings, Qgis

    def log(message, level=Qgis.Info):
        """Journalise dans l'onglet FluxCEN (constitution, Principe VII)."""
        QgsMessageLog.logMessage(message, "FluxCEN", level)

    try:
        authcfg_id = ensure_authcfg(QgsApplication.authManager())
        if authcfg_id is None:
            log("Provisioning delivery : aucun port de redirection libre, "
                "configuration d'authentification non posée.", Qgis.Warning)
            return
        if ensure_repositories(QgsSettings(), base_url, authcfg_id, beta):
            log("Dépôt de plugins FluxCEN provisionné.")
    except Exception as exc:  # pylint: disable=broad-exception-caught
        # Innocuité (contrat) : ne jamais bloquer le démarrage de QGIS.
        log(f"Provisioning delivery en échec : {exc}", Qgis.Warning)
