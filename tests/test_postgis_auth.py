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
from qgis.PyQt.QtWidgets import QDialog  # noqa: E402

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
    instance = plugin_mod.FluxCEN.__new__(plugin_mod.FluxCEN)
    instance._selected_service_authcfg = None  # cache de session (revue de PR)
    yield instance


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

    def test_config_basic_appliquee(self, plugin, monkeypatch):
        set_auth_manager(monkeypatch, {
            OAUTH_ID: FakeAuthConfig("OAuth2", "Entra CEN"),
            BASIC_ID: FakeAuthConfig("Basic", "BDD CEN"),
        })
        uri = QgsDataSourceUri()
        result = plugin.apply_authentication_if_needed(uri)
        assert uri.authConfigId() == BASIC_ID
        assert result is True


class TestCacheDeSession:
    """Revue de PR : plus de défaut persistant en QSettings — recherche vivante
    dans le gestionnaire + choix mémorisé pour la session (même modèle que
    ``_styles_folder_ref``)."""

    def test_choix_unique_memorise_pour_la_session(self, plugin, monkeypatch):
        set_auth_manager(monkeypatch, {BASIC_ID: FakeAuthConfig("Basic", "BDD CEN")})
        plugin.apply_authentication_if_needed(QgsDataSourceUri())
        assert plugin._selected_service_authcfg == BASIC_ID

    def test_cache_evite_le_dialogue(self, plugin, monkeypatch):
        # Deux configs adaptées mais un choix déjà fait cette session :
        # aucun dialogue ne doit s'ouvrir
        set_auth_manager(monkeypatch, {
            BASIC_ID: FakeAuthConfig("Basic", "BDD CEN"),
            "basic02": FakeAuthConfig("Basic", "Autre"),
        })
        monkeypatch.setattr(plugin_mod, "AuthSelectionDialog", _raise_if_instantiated)
        plugin._selected_service_authcfg = BASIC_ID
        uri = QgsDataSourceUri()
        assert plugin.apply_authentication_if_needed(uri) is True
        assert uri.authConfigId() == BASIC_ID

    def test_plusieurs_configs_dialogue_une_seule_fois(self, plugin, monkeypatch):
        set_auth_manager(monkeypatch, {
            BASIC_ID: FakeAuthConfig("Basic", "BDD CEN"),
            "basic02": FakeAuthConfig("Basic", "Autre"),
        })
        calls = []

        class FakeDialog:
            def __init__(self, configs):
                calls.append(1)
                self.selected_auth_id = BASIC_ID

            def exec_(self):
                return QDialog.Accepted

        monkeypatch.setattr(plugin_mod, "AuthSelectionDialog", FakeDialog)
        plugin.apply_authentication_if_needed(QgsDataSourceUri())
        plugin.apply_authentication_if_needed(QgsDataSourceUri())
        assert calls == [1]

    def test_annulation_du_dialogue_non_memorisee(self, plugin, monkeypatch):
        set_auth_manager(monkeypatch, {
            BASIC_ID: FakeAuthConfig("Basic", "BDD CEN"),
            "basic02": FakeAuthConfig("Basic", "Autre"),
        })

        class CancelDialog:
            def __init__(self, configs):
                self.selected_auth_id = None

            def exec_(self):
                return 0  # QDialog.Rejected

        monkeypatch.setattr(plugin_mod, "AuthSelectionDialog", CancelDialog)
        assert plugin.apply_authentication_if_needed(QgsDataSourceUri()) is None
        assert plugin._selected_service_authcfg is None

    def test_cache_invalide_apres_suppression_de_la_config(self, plugin, monkeypatch):
        # La config choisie a disparu du gestionnaire : re-résolution vivante
        set_auth_manager(monkeypatch, {BASIC_ID: FakeAuthConfig("Basic", "BDD CEN")})
        plugin._selected_service_authcfg = "gone123"
        uri = QgsDataSourceUri()
        assert plugin.apply_authentication_if_needed(uri) is True
        assert uri.authConfigId() == BASIC_ID

    def test_garde_defaut_qsettings_supprime(self):
        # Garde sur le motif de code : plus aucun défaut persistant ni bouton
        # de choix par défaut (revue de PR)
        import pathlib
        source = (pathlib.Path(__file__).resolve().parents[1] / "FluxCEN.py").read_text(encoding="utf-8")
        assert "default_auth_id" not in source
        assert "choose_default_authentication" not in source
        assert "commandLinkButton_5" not in source


def _raise_if_instantiated(*_args, **_kwargs):
    raise AssertionError("AuthSelectionDialog ne doit pas s'ouvrir : choix déjà en cache")
