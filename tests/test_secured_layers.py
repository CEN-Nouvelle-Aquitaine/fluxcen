# -*- coding: utf-8 -*-
"""Tests d'intégration de FR-012 : une couche du périmètre sécurisé CEN sans
configuration d'authentification adaptée n'est jamais créée ni ajoutée au
projet (revue de PR) — fini la couche vide + fenêtre d'identification native.

Nécessitent QGIS (ignorés sans bindings, exécutés en CI). Les classes de
couches et le projet sont remplacés par des doubles : on vérifie la création,
pas le rendu.
"""
# pylint: disable=missing-class-docstring,missing-function-docstring,too-few-public-methods,redefined-outer-name,protected-access,wrong-import-position,wrong-import-order,unused-argument
from unittest.mock import MagicMock

import pytest

pytest.importorskip("qgis.core")
pytestmark = pytest.mark.integration

import fluxcen.FluxCEN as plugin_mod  # noqa: E402

SECURED_URL = "https://opendata.cen-nouvelle-aquitaine.org/geoserver/fonciercen/ows?VERSION=1.3.0&REQUEST=GetCapabilities"
PUBLIC_URL = "https://data.geopf.fr/wms-r/wms?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities"


class FakeLayer:
    """Double de QgsRasterLayer/QgsVectorLayer : enregistre les créations."""

    calls = []

    def __init__(self, uri, name, provider):
        FakeLayer.calls.append((uri, name, provider))

    def isValid(self):
        return True

    def triggerRepaint(self):
        pass


@pytest.fixture
def plugin(qgis_app, monkeypatch):
    monkeypatch.setattr(plugin_mod, "iface", MagicMock())
    monkeypatch.setattr(plugin_mod, "QgsRasterLayer", FakeLayer)
    monkeypatch.setattr(plugin_mod, "QgsVectorLayer", FakeLayer)
    monkeypatch.setattr(plugin_mod, "QgsProject", MagicMock())
    FakeLayer.calls = []
    instance = plugin_mod.FluxCEN.__new__(plugin_mod.FluxCEN)
    instance._selected_service_authcfg = None
    return instance


class TestCoucheSecuriseeSansAuthcfg:
    def test_wms_non_creee(self, plugin, monkeypatch):
        monkeypatch.setattr(plugin, "_select_service_authcfg", lambda: None)
        plugin.handle_wms_layer(0, "Sites CEN", "fonciercen:sites", SECURED_URL, None)
        assert FakeLayer.calls == []

    def test_wfs_non_creee(self, plugin, monkeypatch):
        monkeypatch.setattr(plugin, "_select_service_authcfg", lambda: None)
        plugin.handle_wfs_layer(0, "Sites CEN", "fonciercen:sites", SECURED_URL, None)
        assert FakeLayer.calls == []


class TestCoucheSecuriseeAvecAuthcfg:
    def test_wms_creee_avec_authcfg(self, plugin, monkeypatch):
        monkeypatch.setattr(plugin, "_select_service_authcfg", lambda: "basic01")
        plugin.handle_wms_layer(0, "Sites CEN", "fonciercen:sites", SECURED_URL, None)
        assert len(FakeLayer.calls) == 1
        assert "authcfg=basic01" in FakeLayer.calls[0][0]

    def test_wfs_creee_avec_authcfg(self, plugin, monkeypatch):
        monkeypatch.setattr(plugin, "_select_service_authcfg", lambda: "basic01")
        plugin.handle_wfs_layer(0, "Sites CEN", "fonciercen:sites", SECURED_URL, None)
        assert len(FakeLayer.calls) == 1
        assert "authcfg=basic01" in FakeLayer.calls[0][0]


class TestCouchePubliqueSansConfig:
    def test_wms_publique_creee_sans_auth(self, plugin, monkeypatch):
        # Hors périmètre sécurisé : jamais de sélection d'authcfg (FR-010)
        monkeypatch.setattr(plugin, "_select_service_authcfg", _raise_if_called)
        plugin.handle_wms_layer(0, "Orthos", "ORTHOIMAGERY.ORTHOPHOTOS", PUBLIC_URL, None)
        assert len(FakeLayer.calls) == 1
        assert "authcfg" not in FakeLayer.calls[0][0]


def _raise_if_called(*_args, **_kwargs):
    raise AssertionError("_select_service_authcfg ne doit pas être appelée hors périmètre sécurisé")
