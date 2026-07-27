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

    def test_nouvel_essai_du_catalogue_apres_echec(self, qgis_app, monkeypatch):
        # Finding 1 : un échec transitoire ne doit pas laisser le catalogue
        # vide pour toute la session — nouvel essai à l'ouverture suivante.
        QSettings().setValue("locale/userLocale", "fr_FR")
        # Indépendant du links.yaml local (gitignoré, absent du checkout CI)
        monkeypatch.setattr(
            plugin_mod.FluxCEN, "load_urls",
            lambda self, path: ("https://tenantcen.sharepoint.com/flux.csv", "https://styles/"),
        )
        monkeypatch.setattr(
            plugin_mod.FluxCEN, "_authcfg_id", lambda self: "abc1234",
        )
        monkeypatch.setattr(
            plugin_mod.FluxCEN, "_fetch_bytes",
            lambda self, url, resource_name="ressource": (_ for _ in ()).throw(IOError("réseau coupé")),
        )
        iface_mock = MagicMock()
        iface_mock.mainWindow.return_value = None
        plugin = plugin_mod.FluxCEN(iface_mock)
        plugin.iface = iface_mock
        plugin._deferred_startup()          # 1ʳᵉ ouverture : tout échoue
        assert plugin.dlg.comboBox.count() == 1  # seule "toutes les catégories"

        csv_bytes = (
            "service;categorie;Nom_couche_plugin;nom_technique;url;source;style;metadonnees;nom_bdd;nom_schema\n"
            "WFS;Zonages;ZNIEFF;znieff1;https://data.geopf.fr/wfs;INPN;;;;\n"
        ).encode("utf-8")
        monkeypatch.setattr(
            plugin_mod.FluxCEN, "_fetch_bytes",
            lambda self, url, resource_name="ressource": csv_bytes,
        )
        plugin._deferred_startup()          # 2ᵉ ouverture : le réseau est revenu
        assert plugin.dlg.comboBox.count() == 2  # catégorie "Zonages" chargée

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


CSV_HEADER = "service;categorie;Nom_couche_plugin;nom_technique;url;source;style;metadonnees;nom_bdd;nom_schema\n"


class TestInitialisationFluxRobuste:
    """Finding 3 : jamais d'exception sur liste filtrée vide, correspondance
    même quand les cellules du CSV ne sont pas normalisées (espaces)."""

    @pytest.fixture
    def plugin(self, qgis_app, monkeypatch):
        QSettings().setValue("locale/userLocale", "fr_FR")
        monkeypatch.setattr(
            plugin_mod.FluxCEN, "_fetch_bytes",
            lambda self, url, resource_name="ressource": (_ for _ in ()).throw(IOError("pas de réseau")),
        )
        iface_mock = MagicMock()
        iface_mock.mainWindow.return_value = None
        obj = plugin_mod.FluxCEN(iface_mock)
        obj.iface = iface_mock
        obj._startup_done = True
        return obj

    def test_cellules_avec_espaces(self, plugin):
        # la catégorie du combo est normalisée (strip), la cellule non
        plugin._catalog_text = CSV_HEADER + "WFS; Zonages ;ZNIEFF;znieff1;https://x;INPN;;;;\n"
        plugin.dlg.comboBox.addItem("Zonages")
        plugin.dlg.comboBox.setCurrentIndex(plugin.dlg.comboBox.count() - 1)
        assert plugin.dlg.tableWidget.rowCount() == 1

    def test_categorie_sans_ligne_ne_plante_pas(self, plugin):
        plugin._catalog_text = CSV_HEADER + "WFS;Zonages;ZNIEFF;znieff1;https://x;INPN;;;;\n"
        plugin.dlg.comboBox.addItem("Inexistante")
        plugin.dlg.comboBox.setCurrentIndex(plugin.dlg.comboBox.count() - 1)
        assert plugin.dlg.tableWidget.rowCount() == 0

    def test_catalogue_reduit_a_l_entete(self, plugin):
        plugin._catalog_text = CSV_HEADER
        plugin.initialisation_flux()
        assert plugin.dlg.tableWidget.rowCount() == 0

    def test_ligne_courte_du_catalogue_distant(self, plugin):
        # Le catalogue est un fichier vivant sur SharePoint : une ligne à moins
        # de 10 colonnes (voire moins de 4) ne doit jamais vider le tableau.
        plugin._catalog_text = CSV_HEADER + (
            "WFS;Zonages;ZNIEFF;znieff1;https://x;INPN;;https://meta;;\n"
            "WMS;Cartographie;Ligne courte\n"      # 3 colonnes seulement
            ";;\n"                                  # quasi vide
            "WFS;Zonages;ZNIEFF2;znieff2;https://x;INPN;;https://meta;;\n"
        )
        plugin.initialisation_flux()               # aucune exception
        assert plugin.dlg.tableWidget.rowCount() == 3  # la ligne courte reste visible, paddée

    def test_url_metadonnees_de_la_bonne_ligne(self, plugin):
        # Finding 4 : en vue filtrée, l'icône Infos doit porter l'URL de la
        # ligne affichée, pas celle du catalogue complet.
        plugin._catalog_text = CSV_HEADER + (
            "WFS;Autre;AAA;aaa;https://x;S;;https://meta/autre;;\n"
            "WFS;Zonages;ZNIEFF;znieff1;https://x;INPN;;https://meta/znieff;;\n"
        )
        plugin.dlg.comboBox.addItem("Zonages")
        plugin.dlg.comboBox.setCurrentIndex(plugin.dlg.comboBox.count() - 1)
        from qgis.PyQt.QtCore import Qt
        item = plugin.dlg.tableWidget.item(0, 7)
        assert item.data(Qt.UserRole) == "https://meta/znieff"
