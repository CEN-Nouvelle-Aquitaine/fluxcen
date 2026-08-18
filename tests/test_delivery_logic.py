# -*- coding: utf-8 -*-
"""Tests de la logique pure du service de distribution (spec 002, T008).

Contrat : specs/002-plugin-delivery/contracts/http-delivery.md (dépôt unique,
standard communautaire : les préversions sont des entrées experimental du
même catalogue). Tests purs, sans QGIS ni Azure.
"""
# pylint: disable=missing-class-docstring,missing-function-docstring
import pytest

from delivery.function import logic

pytestmark = pytest.mark.unit


class TestResolveBlob:
    def test_catalogue(self):
        assert logic.resolve_blob("stable", "plugins.xml") == "stable/plugins.xml"

    def test_zip_version_finale(self):
        assert (logic.resolve_blob("stable", "FluxCEN.5.3.0.zip")
                == "stable/FluxCEN.5.3.0.zip")

    def test_zip_preversion(self):
        assert (logic.resolve_blob("stable", "FluxCEN.5.4.0-beta.1.zip")
                == "stable/FluxCEN.5.4.0-beta.1.zip")

    @pytest.mark.parametrize("channel", [
        "beta",          # ancien canal supprimé (design POC abandonné)
        "Stable", "prod", "", "stable/..", "STABLE",
    ])
    def test_canal_inconnu(self, channel):
        assert logic.resolve_blob(channel, "plugins.xml") is None

    @pytest.mark.parametrize("filename", [
        "plugins.XML",                 # casse stricte
        "autre.xml",                   # nom hors contrat
        "FluxCEN.zip",                 # version absente
        "FluxCEN.5.3.zip",             # version à 2 composants
        "FluxCEN.5.3.0.zip.exe",       # extension piégée
        "../stable/plugins.xml",       # traversée
        "..%2Fplugins.xml",            # traversée encodée
        "FluxCEN.5.3.0/../x.zip",      # traversée interne
        "",                            # vide
    ])
    def test_fichier_hors_contrat(self, filename):
        assert logic.resolve_blob("stable", filename) is None


class TestContentType:
    def test_xml(self):
        assert logic.content_type("plugins.xml") == "text/xml"

    def test_zip(self):
        assert logic.content_type("FluxCEN.5.3.0.zip") == "application/zip"
