# -*- coding: utf-8 -*-
"""Tests d'intégration de FR-011 : aucune configuration d'authentification web
(OAuth2 / Microsoft Entra ID) n'est jamais appliquée à une connexion PostGIS.

Nécessitent QGIS (ignorés sans bindings, exécutés en CI). Le gestionnaire
d'authentification est remplacé par un factice : on vérifie l'authcfg posée
sur l'URI, pas la connexion.
"""
# pylint: disable=missing-class-docstring,missing-function-docstring,too-few-public-methods,redefined-outer-name,protected-access,wrong-import-position,wrong-import-order,unused-argument
from unittest.mock import MagicMock

import pytest

pytest.importorskip("qgis.core")
pytestmark = pytest.mark.integration

from qgis.core import QgsDataSourceUri  # noqa: E402
from qgis.PyQt.QtCore import QSettings  # noqa: E402

import fluxcen.FluxCEN as plugin_mod  # noqa: E402

OAUTH_ID = "g2b2197"
BASIC_ID = "basic01"


class FakeAuthConfig:
    def __init__(self, method, name):
        self._method = method
        self._name = name

    def method(self):
        return self._method

    def name(self):
        return self._name


class FakeAuthManager:
    def __init__(self, configs):
        self._configs = configs

    def availableAuthMethodConfigs(self):
        return self._configs


@pytest.fixture
def plugin(qgis_app, monkeypatch):
    """Instance minimale + neutralisation des dialogues et du iface global."""
    monkeypatch.setattr(plugin_mod, "iface", MagicMock())
    monkeypatch.setattr(plugin_mod, "QMessageBox", MagicMock())
    monkeypatch.setattr(plugin_mod, "alert", MagicMock())  # popups centralisées (#46)
    QSettings().remove("FluxCEN/default_auth_id")
    yield plugin_mod.FluxCEN.__new__(plugin_mod.FluxCEN)
    QSettings().remove("FluxCEN/default_auth_id")


def set_auth_manager(monkeypatch, configs):
    fake_app = MagicMock()
    fake_app.authManager.return_value = FakeAuthManager(configs)
    monkeypatch.setattr(plugin_mod, "QgsApplication", fake_app)


class TestFr011PostgisSansAuthMicrosoft:
    def test_config_oauth2_seule_jamais_appliquee(self, plugin, monkeypatch):
        set_auth_manager(monkeypatch, {OAUTH_ID: FakeAuthConfig("OAuth2", "Entra CEN")})
        uri = QgsDataSourceUri()
        result = plugin.apply_authentication_if_needed(uri)
        assert uri.authConfigId() == ""
        assert not result

    def test_default_qsettings_oauth2_ignoree(self, plugin, monkeypatch):
        set_auth_manager(monkeypatch, {OAUTH_ID: FakeAuthConfig("OAuth2", "Entra CEN")})
        QSettings().setValue("FluxCEN/default_auth_id", OAUTH_ID)
        uri = QgsDataSourceUri()
        result = plugin.apply_authentication_if_needed(uri)
        assert uri.authConfigId() == ""
        assert not result

    def test_config_basic_appliquee(self, plugin, monkeypatch):
        set_auth_manager(monkeypatch, {
            OAUTH_ID: FakeAuthConfig("OAuth2", "Entra CEN"),
            BASIC_ID: FakeAuthConfig("Basic", "BDD CEN"),
        })
        uri = QgsDataSourceUri()
        result = plugin.apply_authentication_if_needed(uri)
        assert uri.authConfigId() == BASIC_ID
        assert result is True

    def test_default_qsettings_basic_appliquee(self, plugin, monkeypatch):
        set_auth_manager(monkeypatch, {
            OAUTH_ID: FakeAuthConfig("OAuth2", "Entra CEN"),
            BASIC_ID: FakeAuthConfig("Basic", "BDD CEN"),
        })
        QSettings().setValue("FluxCEN/default_auth_id", BASIC_ID)
        uri = QgsDataSourceUri()
        result = plugin.apply_authentication_if_needed(uri)
        assert uri.authConfigId() == BASIC_ID
        assert result is True
