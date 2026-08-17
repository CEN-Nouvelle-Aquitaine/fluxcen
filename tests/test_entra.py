# -*- coding: utf-8 -*-
"""Tests unitaires purs de core.entra (FR-013 : configuration Microsoft canonique).

Data-model : specs/001-sharepoint-share-urls/data-model.md
(ConfigurationMicrosoftCanonique). Aucun import qgis.
"""
# pylint: disable=missing-class-docstring,missing-function-docstring,too-few-public-methods,redefined-outer-name,protected-access,wrong-import-position,wrong-import-order,unused-argument
import json

from core.entra import (
    AUTHCFG_ID,
    AUTHCFG_NAME,
    REDIRECT_PORTS,
    canonical_oauth2_config,
    config_needs_update,
    pick_free_port,
)


class TestCanonicalConfig:
    """La config canonique est un client public PKCE : jamais de secret."""

    def test_identifiants_canoniques(self):
        assert AUTHCFG_ID == "g2b2197"
        assert AUTHCFG_NAME == "Microsoft CEN"

    def test_client_public_pkce_sans_secret(self):
        config = canonical_oauth2_config(REDIRECT_PORTS[0])
        assert config["grantFlow"] == 3  # Authorization Code PKCE
        assert config["clientSecret"] == ""
        assert config["clientId"] == "80c3a908-e890-4575-9a46-785116e160f9"

    def test_endpoints_tenant_v2(self):
        config = canonical_oauth2_config(REDIRECT_PORTS[0])
        tenant = "898a7ac2-f878-44ab-80f0-1e1852b7bebd"
        assert config["requestUrl"] == (
            f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize")
        assert config["tokenUrl"] == (
            f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token")
        assert config["scope"] == "https://graph.microsoft.com/Files.Read.All offline_access"

    def test_redirection_loopback_port_parametre(self):
        config = canonical_oauth2_config(17071)
        assert config["redirectHost"] == "127.0.0.1"
        assert config["redirectPort"] == 17071
        assert config["redirectUrl"] == "qgis-client"

    def test_ports_declares_evitent_7070(self):
        # 7070 est le port d'écoute d'AnyDesk : jamais dans la liste
        assert 7070 not in REDIRECT_PORTS
        assert len(REDIRECT_PORTS) >= 2


class TestConfigNeedsUpdate:
    """Mise à jour ssi la config stockée diverge du canon (le port reste
    libre de varier dans la liste déclarée)."""

    def stored(self, **overrides):
        config = canonical_oauth2_config(REDIRECT_PORTS[0])
        config.update(overrides)
        return json.dumps(config)

    def test_config_canonique_inchangee(self):
        assert config_needs_update(self.stored()) is False

    def test_port_alternatif_de_la_liste_accepte(self):
        assert config_needs_update(self.stored(redirectPort=REDIRECT_PORTS[1])) is False

    def test_secret_vestigial_declenche_maj(self):
        assert config_needs_update(self.stored(clientSecret="vieux-secret")) is True

    def test_port_hors_liste_declenche_maj(self):
        # ancien port 7070 (volé par AnyDesk) : à réparer
        assert config_needs_update(self.stored(redirectPort=7070)) is True

    def test_client_id_different_declenche_maj(self):
        assert config_needs_update(self.stored(clientId="autre")) is True

    def test_json_invalide_declenche_maj(self):
        assert config_needs_update("pas du json") is True
        assert config_needs_update("") is True


class TestPickFreePort:
    def test_premier_port_libre(self):
        assert pick_free_port(lambda port: True) == REDIRECT_PORTS[0]

    def test_saute_les_ports_occupes(self):
        occupied = {REDIRECT_PORTS[0]}
        assert pick_free_port(lambda port: port not in occupied) == REDIRECT_PORTS[1]

    def test_aucun_port_libre(self):
        assert pick_free_port(lambda port: False) is None
