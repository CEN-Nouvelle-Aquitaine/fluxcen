# -*- coding: utf-8 -*-
"""Tests unitaires purs de core.ms_urls (aucun import qgis).

Contrat : specs/001-sharepoint-share-urls/contracts/core-functions.md
"""
import pytest

from core.ms_urls import UrlClass, classify_url, is_microsoft_url

GRAPH_URL = "https://graph.microsoft.com/v1.0/sites/abc/drive/root:/fluxcen/flux.csv:/content"
SHARING_LINK = (
    "https://conservatoirena-my.sharepoint.com/:x:/r/personal/"
    "services_conservatoirena_onmicrosoft_com/Documents/flux.csv"
    "?d=wb1c30bfef9064f1a974dc09b99922937&csf=1&web=1&e=VZDJDH"
)


class TestIsMicrosoftUrl:
    @pytest.mark.parametrize("url", [
        GRAPH_URL,
        "https://graph.microsoft.com/v1.0/shares/u!abc/driveItem/content",
        SHARING_LINK,
        "https://tenant.sharepoint.com/sites/x/doc.csv",
        "https://tenant-my.sharepoint.com/personal/x/doc.csv",
        "https://TENANT.SharePoint.COM/sites/x",  # insensible à la casse
    ])
    def test_perimetre_microsoft(self, url):
        assert is_microsoft_url(url) is True

    @pytest.mark.parametrize("url", [
        "http://tenant.sharepoint.com/sites/x",          # http interdit
        "http://graph.microsoft.com/v1.0/x",             # http interdit
        "data:text/plain,version=5.2",                   # pas un serveur
        "https://sharepoint.com.evil.tld/x",             # suffixe trompeur
        "https://notsharepoint.com/x",                   # sous-chaîne trompeuse
        "https://sharepoint.com/x",                      # pas un domaine tenant
        "https://sharepoint.com@evil.tld/x",             # userinfo trompeur
        "https://graph.microsoft.com.evil.tld/x",        # suffixe trompeur
        "https://raw.githubusercontent.com/x/y",         # domaine tiers
        "",                                              # vide
        "pas une url",                                   # malformée
        "https://[malformed",                            # urlsplit lève ValueError
    ])
    def test_hors_perimetre(self, url):
        assert is_microsoft_url(url) is False

    def test_jamais_d_exception(self):
        for url in (None, 42, b"https://x", object()):
            assert is_microsoft_url(url) is False


class TestClassifyUrl:
    def test_lien_de_partage(self):
        assert classify_url(SHARING_LINK) is UrlClass.SHAREPOINT_SHARING_LINK

    def test_graph(self):
        assert classify_url(GRAPH_URL) is UrlClass.GRAPH

    @pytest.mark.parametrize("url", [
        "https://raw.githubusercontent.com/x/y",
        "data:text/plain,version=5.2",
        "http://tenant.sharepoint.com/x",  # http : jamais Microsoft
        "",
    ])
    def test_other(self, url):
        assert classify_url(url) is UrlClass.OTHER

    def test_coherence_avec_is_microsoft_url(self):
        for url in (SHARING_LINK, GRAPH_URL, "https://exemple.org/x", ""):
            assert (classify_url(url) is not UrlClass.OTHER) == is_microsoft_url(url)
