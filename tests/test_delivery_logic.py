# -*- coding: utf-8 -*-
"""Tests de la logique pure du service de distribution (spec 002, T008/T015).

Contrat : specs/002-plugin-delivery/contracts/http-delivery.md.
Tests purs, sans QGIS ni Azure.
"""
# pylint: disable=missing-class-docstring,missing-function-docstring
import base64
import json

import pytest

from delivery.function import logic

pytestmark = pytest.mark.unit


# --- T008 : validation de chemin et résolution de blob ---------------------

class TestResolveBlob:
    def test_stable_catalogue(self):
        assert logic.resolve_blob("stable", "plugins.xml") == "stable/plugins.xml"

    def test_beta_catalogue(self):
        assert logic.resolve_blob("beta", "plugins.xml") == "beta/plugins.xml"

    def test_zip_version_finale(self):
        assert (logic.resolve_blob("stable", "FluxCEN.5.3.0.zip")
                == "stable/FluxCEN.5.3.0.zip")

    def test_zip_preversion(self):
        assert (logic.resolve_blob("beta", "FluxCEN.5.4.0-beta.1.zip")
                == "beta/FluxCEN.5.4.0-beta.1.zip")

    @pytest.mark.parametrize("channel", ["Stable", "prod", "", "stable/..", "STABLE"])
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


# --- T015 : autorisation beta par claim groups -----------------------------

BETA_GROUP = "11111111-2222-3333-4444-555555555555"


def principal_b64(groups):
    """Encode un header x-ms-client-principal comme le pose Easy Auth."""
    claims = [{"typ": "groups", "val": g} for g in groups]
    claims.append({"typ": "name", "val": "Test User"})
    return base64.b64encode(json.dumps({"claims": claims}).encode()).decode()


class TestParsePrincipal:
    def test_extrait_les_groupes(self):
        header = principal_b64([BETA_GROUP, "autre-groupe"])
        assert logic.parse_groups(header) == {BETA_GROUP, "autre-groupe"}

    def test_sans_claim_groups(self):
        assert logic.parse_groups(principal_b64([])) == set()

    @pytest.mark.parametrize("header", [None, "", "pas-du-base64!", "aGVsbG8="])
    def test_header_absent_ou_invalide(self, header):
        assert logic.parse_groups(header) == set()


class TestIsAuthorized:
    def test_stable_toujours_autorise(self):
        assert logic.is_authorized("stable", set(), BETA_GROUP) is True

    def test_beta_membre(self):
        assert logic.is_authorized("beta", {BETA_GROUP}, BETA_GROUP) is True

    def test_beta_non_membre(self):
        assert logic.is_authorized("beta", {"autre"}, BETA_GROUP) is False

    def test_beta_claim_absent(self):
        assert logic.is_authorized("beta", set(), BETA_GROUP) is False
