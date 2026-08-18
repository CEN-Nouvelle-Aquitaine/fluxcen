# -*- coding: utf-8 -*-
"""Tests du provisioning des postes (spec 002, T023).

Contrat : specs/002-plugin-delivery/contracts/provisioning.md.
Partie pure : sans QGIS. Partie intégration : pytest-qgis (skip sans QGIS).
"""
# pylint: disable=missing-class-docstring,missing-function-docstring,too-few-public-methods
import json
import socket

import pytest

from delivery.provisioning import provision

BASE_URL = "https://func-fluxcen-delivery-poc.azurewebsites.net"


# --- Pur : configuration canonique de l'authcfg delivery -------------------

@pytest.mark.unit
class TestCanonicalConfig:
    def test_scope_api_delivery(self):
        cfg = provision.canonical_oauth2_config(17070)
        assert cfg["scope"] == (
            "api://80c3a908-e890-4575-9a46-785116e160f9/plugins.read offline_access")

    def test_pkce_sans_secret(self):
        cfg = provision.canonical_oauth2_config(17070)
        assert cfg["grantFlow"] == 3
        assert cfg["clientSecret"] == ""
        assert cfg["persistToken"] is True

    def test_port_reporte(self):
        assert provision.canonical_oauth2_config(17071)["redirectPort"] == 17071


@pytest.mark.unit
class TestConfigNeedsUpdate:
    def test_canon_conforme(self):
        stored = json.dumps(provision.canonical_oauth2_config(17070))
        assert provision.config_needs_update(stored) is False

    def test_port_de_repli_admis(self):
        stored = json.dumps(provision.canonical_oauth2_config(17072))
        assert provision.config_needs_update(stored) is False

    def test_scope_errone_repare(self):
        cfg = provision.canonical_oauth2_config(17070)
        cfg["scope"] = "https://graph.microsoft.com/Files.Read.All offline_access"
        assert provision.config_needs_update(json.dumps(cfg)) is True

    def test_secret_vestigial_repare(self):
        cfg = provision.canonical_oauth2_config(17070)
        cfg["clientSecret"] = "secret-oublie"
        assert provision.config_needs_update(json.dumps(cfg)) is True

    def test_json_illisible_repare(self):
        assert provision.config_needs_update("pas du json") is True


@pytest.mark.unit
class TestPorts:
    def test_port_occupe_bascule(self):
        blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        blocker.bind(("127.0.0.1", provision.REDIRECT_PORTS[0]))
        try:
            port = provision.pick_free_port(provision.port_is_free)
            assert port in provision.REDIRECT_PORTS[1:]
        finally:
            blocker.close()


@pytest.mark.unit
class TestDesiredRepositories:
    def test_stable_seul_par_defaut(self):
        repos = provision.desired_repositories(BASE_URL)
        assert repos == {
            "FluxCEN (interne)": f"{BASE_URL}/stable/plugins.xml",
        }

    def test_beta_sur_demande(self):
        repos = provision.desired_repositories(BASE_URL, beta=True)
        assert repos["FluxCEN (beta)"] == f"{BASE_URL}/beta/plugins.xml"
        assert "FluxCEN (interne)" in repos

    def test_slash_final_normalise(self):
        repos = provision.desired_repositories(BASE_URL + "/")
        assert repos["FluxCEN (interne)"] == f"{BASE_URL}/stable/plugins.xml"


# Les tests d'intégration QgsSettings vivent dans test_provisioning_qgis.py
# (importorskip au niveau module, pattern du dépôt).
