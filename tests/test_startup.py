# -*- coding: utf-8 -*-
"""Tests d'intégration de robustesse au démarrage (T020 — US3, FR-008/FR-009).

Nécessitent QGIS (ignorés sans bindings, exécutés en CI).
"""
from unittest.mock import MagicMock

import pytest

pytest.importorskip("qgis.core")
pytestmark = pytest.mark.integration

import importlib  # noqa: E402

from qgis.PyQt.QtCore import QSettings  # noqa: E402

import fluxcen.FluxCEN as plugin_mod  # noqa: E402


def _raise(*_args, **_kwargs):
    raise AssertionError("accès réseau interdit pendant l'import du module")


class TestAucunReseauALImport:
    def test_reload_sans_reseau_ni_socket(self, monkeypatch):
        # Toute requête via la pile QGIS pendant l'import ferait échouer le test.
        monkeypatch.setattr("qgis.core.QgsBlockingNetworkRequest.get", _raise)
        module = importlib.reload(plugin_mod)
        # Le test de connectivité socket au niveau module a été supprimé.
        assert not hasattr(module, "socket")


class TestEchecReseauNonFatal:
    def test_instanciation_et_initgui_sans_reseau(self, qgis_app, monkeypatch):
        QSettings().setValue("locale/userLocale", "fr_FR")
        # Tout téléchargement échoue systématiquement.
        monkeypatch.setattr(
            plugin_mod.FluxCEN, "_fetch_bytes",
            lambda self, url, resource_name="ressource": (_ for _ in ()).throw(IOError("réseau coupé")),
        )
        iface_mock = MagicMock()
        plugin = plugin_mod.FluxCEN(iface_mock)   # aucune exception
        plugin.iface = iface_mock
        plugin.initGui()                          # aucune exception, aucun réseau
        assert plugin is not None
