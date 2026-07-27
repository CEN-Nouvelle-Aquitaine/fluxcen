# -*- coding: utf-8 -*-
"""Tests d'intégration de robustesse au démarrage (T020 — US3, FR-008/FR-009).

Nécessitent QGIS (ignorés sans bindings, exécutés en CI).
"""
# pylint: disable=missing-class-docstring,missing-function-docstring,too-few-public-methods,redefined-outer-name,protected-access,wrong-import-position,wrong-import-order,unused-argument
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
        iface_mock.mainWindow.return_value = None  # parent Qt valide pour QAction
        plugin = plugin_mod.FluxCEN(iface_mock)   # aucune exception
        plugin.iface = iface_mock
        plugin.initGui()                          # aucune exception, aucun réseau
        assert plugin is not None

    def test_construction_silencieuse_ni_reseau_ni_erreur(self, qgis_app, monkeypatch):
        # Régression : comboBox.addItem() dans __init__ déclenche
        # currentIndexChanged → initialisation_flux() s'exécutait pendant la
        # construction, avant l'initialisation de _catalog_text (AttributeError
        # affichée « Échec du chargement de “catalogue des flux” »).
        QSettings().setValue("locale/userLocale", "fr_FR")
        monkeypatch.setattr(
            plugin_mod.FluxCEN, "_fetch_bytes",
            lambda self, url, resource_name="ressource": (_ for _ in ()).throw(
                AssertionError("aucun réseau ne doit avoir lieu pendant __init__")),
        )
        iface_mock = MagicMock()
        iface_mock.mainWindow.return_value = None
        plugin = plugin_mod.FluxCEN(iface_mock)
        # Aucune notification d'erreur ne doit avoir été émise à la construction.
        iface_mock.messageBar.return_value.pushMessage.assert_not_called()
        assert plugin._catalog_text is None
