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
    drive_item_child_content_url,
    is_database_auth_method,
    is_microsoft_url,
    is_sharepoint_sharing_link,
    parse_drive_item_ref,
    select_web_authcfg,
    sharing_link_to_graph_metadata_url,
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


class TestResolutionDossierPartage:
    """Résolution en 2 étapes, validée contre le tenant réel le 2026-07-27 :
    l'adressage par chemin sous /shares est rejeté par Graph (400,
    "Resource not found for the segment 'driveItem:'")."""

    FOLDER = "https://tenant.sharepoint.com/x"
    META_JSON = ('{"id": "ITEM123", "name": "styles_couches", '
                 '"parentReference": {"driveId": "b!DRIVE456"}, "folder": {"childCount": 22}}')

    def test_metadata_url(self):
        assert (sharing_link_to_graph_metadata_url(self.FOLDER)
                == GRAPH_SHARES + TOKEN_SIMPLE + "/driveItem?$select=id,parentReference")

    def test_metadata_url_hors_sharepoint(self):
        with pytest.raises(ValueError):
            sharing_link_to_graph_metadata_url("https://exemple.org/dossier")

    def test_parse_drive_item_ref(self):
        assert parse_drive_item_ref(self.META_JSON) == ("b!DRIVE456", "ITEM123")

    @pytest.mark.parametrize("payload", [
        "", "pas du json", "{}", '{"id": "X"}',
        '{"id": "", "parentReference": {"driveId": "D"}}',
        '{"id": "X", "parentReference": {}}',
    ])
    def test_parse_drive_item_ref_invalide(self, payload):
        with pytest.raises(ValueError):
            parse_drive_item_ref(payload)

    def test_child_content_url(self):
        assert (drive_item_child_content_url("b!DRIVE456", "ITEM123", "RPG.qml")
                == "https://graph.microsoft.com/v1.0/drives/b!DRIVE456/items/ITEM123:/RPG.qml:/content")

    def test_child_content_url_percent_encoding(self):
        # cas réel du dossier CEN : "RPG _2024.qml" (espace dans le nom)
        url = drive_item_child_content_url("b!DRIVE456", "ITEM123", "RPG _2024.qml")
        assert url.endswith("/items/ITEM123:/RPG%20_2024.qml:/content")

    @pytest.mark.parametrize("filename", ["", "a/b.qml", "a\\b.qml", "../x.qml", "a..b.qml"])
    def test_child_content_url_nom_invalide(self, filename):
        with pytest.raises(ValueError):
            drive_item_child_content_url("b!DRIVE456", "ITEM123", filename)

    @pytest.mark.parametrize("drive_id,item_id", [("", "I"), ("D", ""), ("D/../x", "I"), ("D", "I?x=1")])
    def test_child_content_url_ids_invalides(self, drive_id, item_id):
        with pytest.raises(ValueError):
            drive_item_child_content_url(drive_id, item_id, "a.qml")

    def test_urls_dans_le_perimetre_microsoft(self):
        assert is_microsoft_url(sharing_link_to_graph_metadata_url(self.FOLDER)) is True
        assert is_microsoft_url(drive_item_child_content_url("D", "I", "a.qml")) is True


class TestIsDatabaseAuthMethod:
    """FR-011 : les méthodes d'auth web ne sont jamais utilisables pour une BDD."""

    def test_oauth2_exclue(self):
        assert is_database_auth_method("OAuth2") is False

    @pytest.mark.parametrize("method", ["Basic", "PKI-Paths", "PKI-PKCS#12", "Identity-Cert"])
    def test_methodes_bdd_acceptees(self, method):
        assert is_database_auth_method(method) is True


class TestSelectWebAuthcfg:
    """Découverte de la configuration Microsoft (OAuth2) dans le gestionnaire
    d'authentification QGIS : la configuration distribuée au CEN garde son ID
    à l'import, le plugin la trouve sans links.yaml (revue de PR, issue #39)."""

    def test_unique_config_web_retenue(self):
        assert select_web_authcfg({"g2b2197": "OAuth2"}) == "g2b2197"

    def test_config_web_parmi_des_configs_bdd(self):
        assert select_web_authcfg({
            "basic01": "Basic",
            "g2b2197": "OAuth2",
            "pki0001": "PKI-Paths",
        }) == "g2b2197"

    def test_aucune_config_web(self):
        assert select_web_authcfg({}) == ""
        assert select_web_authcfg({"basic01": "Basic"}) == ""

    def test_plusieurs_configs_web_ambigu(self):
        # Deux OAuth2 : impossible de choisir à l'aveugle, aucune n'est retenue
        assert select_web_authcfg({"g2b2197": "OAuth2", "autre01": "OAuth2"}) == ""


class TestBuildStyleUrl:
    def test_url_directe_concatenation_historique(self):
        base = "https://raw.githubusercontent.com/x/styles_couches/"
        assert build_style_url(base, "style_znieff") == base + "style_znieff.qml"

    def test_lien_de_partage_refuse(self):
        # la résolution d'un dossier partagé exige le réseau : c'est le
        # contrôleur qui la porte, jamais cette fonction pure
        with pytest.raises(ValueError):
            build_style_url("https://tenant.sharepoint.com/x", "style_znieff")
