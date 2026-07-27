# -*- coding: utf-8 -*-
"""Tests unitaires purs de core.ms_urls (aucun import qgis).

Contrat : specs/001-sharepoint-share-urls/contracts/core-functions.md
"""
# pylint: disable=missing-class-docstring,missing-function-docstring,too-few-public-methods,redefined-outer-name,protected-access,wrong-import-position,wrong-import-order,unused-argument
import pytest

from core.ms_urls import (
    UrlClass,
    build_style_url,
    classify_url,
    is_microsoft_url,
    is_sharepoint_sharing_link,
    sharing_link_to_graph_item_url,
    sharing_link_to_graph_url,
)

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


# Jetons attendus, calculés indépendamment de l'implémentation
# (base64 du lien complet, padding retiré, / → _, + → -, préfixe u!).
TOKEN_SIMPLE = "u!aHR0cHM6Ly90ZW5hbnQuc2hhcmVwb2ludC5jb20veA"
TOKEN_SHARING_LINK = (
    "u!aHR0cHM6Ly9jb25zZXJ2YXRvaXJlbmEtbXkuc2hhcmVwb2ludC5jb20vOng6L3IvcGVyc29uYWwvc2Vydmlj"
    "ZXNfY29uc2VydmF0b2lyZW5hX29ubWljcm9zb2Z0X2NvbS9Eb2N1bWVudHMvZmx1eC5jc3Y_ZD13YjFjMzBiZmVm"
    "OTA2NGYxYTk3NGRjMDliOTk5MjI5MzcmY3NmPTEmd2ViPTEmZT1WWkRKREg"
)
GRAPH_SHARES = "https://graph.microsoft.com/v1.0/shares/"


class TestIsSharepointSharingLink:
    def test_lien_de_partage(self):
        assert is_sharepoint_sharing_link(SHARING_LINK) is True
        assert is_sharepoint_sharing_link("https://tenant.sharepoint.com/x") is True

    @pytest.mark.parametrize("url", [
        GRAPH_URL,                            # Graph : déjà exploitable, pas un lien à résoudre
        "http://tenant.sharepoint.com/x",     # http interdit
        "https://sharepoint.com.evil.tld/x",
        "https://exemple.org/x",
        "",
    ])
    def test_non_lien_de_partage(self, url):
        assert is_sharepoint_sharing_link(url) is False


class TestSharingLinkToGraphUrl:
    def test_encodage_exemple_connu(self):
        assert (sharing_link_to_graph_url("https://tenant.sharepoint.com/x")
                == GRAPH_SHARES + TOKEN_SIMPLE + "/driveItem/content")

    def test_parametres_du_lien_conserves(self):
        # Le lien complet (avec ?d=…&csf=1&web=1&e=…) est encodé tel quel.
        assert (sharing_link_to_graph_url(SHARING_LINK)
                == GRAPH_SHARES + TOKEN_SHARING_LINK + "/driveItem/content")

    def test_retour_dans_le_perimetre_microsoft(self):
        assert is_microsoft_url(sharing_link_to_graph_url(SHARING_LINK)) is True

    @pytest.mark.parametrize("url", [GRAPH_URL, "https://exemple.org/x", "", "http://tenant.sharepoint.com/x"])
    def test_valueerror_hors_sharepoint(self, url):
        with pytest.raises(ValueError):
            sharing_link_to_graph_url(url)


class TestSharingLinkToGraphItemUrl:
    FOLDER = "https://tenant.sharepoint.com/x"

    def test_adressage_par_chemin(self):
        assert (sharing_link_to_graph_item_url(self.FOLDER, "style_znieff.qml")
                == GRAPH_SHARES + TOKEN_SIMPLE + "/driveItem:/style_znieff.qml:/content")

    def test_percent_encoding_du_nom(self):
        url = sharing_link_to_graph_item_url(self.FOLDER, "zones humides été.qml")
        assert url == GRAPH_SHARES + TOKEN_SIMPLE + "/driveItem:/zones%20humides%20%C3%A9t%C3%A9.qml:/content"

    def test_retour_dans_le_perimetre_microsoft(self):
        assert is_microsoft_url(sharing_link_to_graph_item_url(self.FOLDER, "a.qml")) is True

    @pytest.mark.parametrize("filename", ["", "a/b.qml", "a\\b.qml", "../secret.qml", "a..b.qml"])
    def test_valueerror_nom_invalide(self, filename):
        with pytest.raises(ValueError):
            sharing_link_to_graph_item_url(self.FOLDER, filename)

    def test_valueerror_hors_sharepoint(self):
        with pytest.raises(ValueError):
            sharing_link_to_graph_item_url("https://exemple.org/dossier", "a.qml")


class TestBuildStyleUrl:
    def test_url_directe_concatenation_historique(self):
        base = "https://raw.githubusercontent.com/x/styles_couches/"
        assert build_style_url(base, "style_znieff") == base + "style_znieff.qml"

    def test_lien_de_partage_de_dossier(self):
        assert (build_style_url("https://tenant.sharepoint.com/x", "style_znieff")
                == GRAPH_SHARES + TOKEN_SIMPLE + "/driveItem:/style_znieff.qml:/content")
