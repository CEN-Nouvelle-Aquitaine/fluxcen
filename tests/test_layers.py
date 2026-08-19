# -*- coding: utf-8 -*-
"""Tests des URI de couches WMS/WFS (T014 — US2, FR-010 / FR-012).

Les URI sont construites par des fonctions pures de core.layer_builder :
aucune configuration d'authentification ne doit y figurer pour un domaine
hors périmètre Microsoft ; le périmètre sécurisé du CEN est le seul à
recevoir une authcfg explicite. Un test de garde vérifie en outre que
l'attachement indiscriminé de la première authcfg a bien disparu de
FluxCEN.py.
"""
# pylint: disable=missing-class-docstring,missing-function-docstring,too-few-public-methods,redefined-outer-name,protected-access,wrong-import-position,wrong-import-order,unused-argument
import pathlib

from core.layer_builder import (
    build_wfs_uri_params,
    build_wms_uri,
    extract_service_version,
    is_cen_secured_service,
)

WMS_URL = "https://data.geopf.fr/wms-r/wms?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities"
WFS_URL = "https://data.geopf.fr/wfs/ows?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities"


class TestExtractServiceVersion:
    def test_version_presente(self):
        assert extract_service_version(WMS_URL) == "1.3.0"

    def test_version_absente_valeur_historique(self):
        assert extract_service_version("https://exemple.org/wms") == "1.0.0"


class TestBuildWmsUri:
    def test_uri_complete(self):
        uri = build_wms_uri(WMS_URL, "ORTHOIMAGERY.ORTHOPHOTOS")
        assert uri.startswith(f"url={WMS_URL}&")
        assert "layers=ORTHOIMAGERY.ORTHOPHOTOS" in uri
        assert "version=1.3.0" in uri

    def test_jamais_d_authcfg(self):
        assert "authcfg" not in build_wms_uri(WMS_URL, "couche")


class TestBuildWfsUriParams:
    def test_parametres(self):
        params = build_wfs_uri_params(WFS_URL, "znieff1")
        assert params == {"url": WFS_URL, "version": "2.0.0",
                          "typename": "znieff1", "request": "GetFeature"}

    def test_jamais_d_authcfg(self):
        assert "authcfg" not in build_wfs_uri_params(WFS_URL, "znieff1")


class TestIsCenSecuredService:
    """FR-012 : espaces de travail sécurisés du geoserver CEN."""

    def test_espaces_securises(self):
        for url in (
            "https://opendata.cen-nouvelle-aquitaine.org/geoserver/fonciercen/wfs",
            "https://opendata.cen-nouvelle-aquitaine.org/fonciercen/wfs",
            "https://opendata.cen-nouvelle-aquitaine.org/chirokollect/wfs",
            "https://opendata.cen-nouvelle-aquitaine.org/data_gods_dsne/wfs",
        ):
            assert is_cen_secured_service(url) is True

    def test_espaces_publics_du_meme_geoserver(self):
        """Le reste du geoserver est public : aucune authentification (revue de PR)."""
        for url in (
            "https://opendata.cen-nouvelle-aquitaine.org/geoserver/agriculture/wfs",
            "https://opendata.cen-nouvelle-aquitaine.org/administratif/wms",
            "https://opendata.cen-nouvelle-aquitaine.org/geoserver/fond_carto/wms",
            "https://opendata.cen-nouvelle-aquitaine.org/geoserver/ows?SERVICE=WMS",
            "https://opendata.cen-nouvelle-aquitaine.org/",
        ):
            assert is_cen_secured_service(url) is False

    def test_hors_perimetre(self):
        for url in (
            "https://data.geopf.fr/wfs/ows?SERVICE=WFS",
            "https://opendata.cen-nouvelle-aquitaine.org.evil.tld/fonciercen/wfs",
            "http://opendata.cen-nouvelle-aquitaine.org/geoserver/fonciercen/wfs",  # http
            "",
        ):
            assert is_cen_secured_service(url) is False


class TestBuildWmsUriAuthcfg:
    """FR-012 : authcfg optionnelle dans l'URI WMS, uniquement si fournie."""

    URL = "https://opendata.cen-nouvelle-aquitaine.org/geoserver/ows?VERSION=1.3.0&REQUEST=GetCapabilities"

    def test_avec_authcfg(self):
        assert build_wms_uri(self.URL, "couche", authcfg="abc1234").endswith("&authcfg=abc1234")

    def test_sans_authcfg(self):
        assert "authcfg" not in build_wms_uri(self.URL, "couche")


class TestGardeAttachementIndiscrimine:
    def test_first_authcfg_supprime_du_plugin(self):
        # FR-010 : l'attachement de la « première authcfg disponible » à toute
        # couche WMS/WFS est supprimé — garde sur le motif de code lui-même.
        source = (pathlib.Path(__file__).resolve().parents[1] / "FluxCEN.py").read_text(encoding="utf-8")
        assert "first_authcfg" not in source
