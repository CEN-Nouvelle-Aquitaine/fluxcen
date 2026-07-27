# -*- coding: utf-8 -*-
"""Tests des URI de couches WMS/WFS (T014 — US2, FR-010).

Les URI sont construites par des fonctions pures de core.catalog : aucune
configuration d'authentification ne doit y figurer pour un domaine hors
périmètre Microsoft. Un test de garde vérifie en outre que l'attachement
indiscriminé de la première authcfg a bien disparu de FluxCEN.py.
"""
import pathlib

from core.catalog import build_wfs_uri_params, build_wms_uri, extract_service_version

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


class TestGardeAttachementIndiscrimine:
    def test_first_authcfg_supprime_du_plugin(self):
        # FR-010 : l'attachement de la « première authcfg disponible » à toute
        # couche WMS/WFS est supprimé — garde sur le motif de code lui-même.
        source = (pathlib.Path(__file__).resolve().parents[1] / "FluxCEN.py").read_text(encoding="utf-8")
        assert "first_authcfg" not in source
