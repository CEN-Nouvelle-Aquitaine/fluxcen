# -*- coding: utf-8 -*-
"""Tests d'intégration de FluxCEN._fetch_bytes (résolution des liens de partage
et filtrage du périmètre d'authentification Microsoft).

Nécessitent QGIS (ignorés sur un poste sans bindings ; exécutés en CI sur
l'image qgis/qgis:3.44). La pile réseau est remplacée par un faux
QgsBlockingNetworkRequest : on vérifie la requête émise, pas le réseau.
"""
# pylint: disable=missing-class-docstring,missing-function-docstring,too-few-public-methods,redefined-outer-name,protected-access,wrong-import-position,wrong-import-order,unused-argument
import pytest

pytest.importorskip("qgis.core")
pytestmark = pytest.mark.integration

import fluxcen.FluxCEN as plugin_mod  # noqa: E402  (après importorskip)
from fluxcen.core.errors import ErrorFamily, FetchError  # noqa: E402

SHARING_LINK = (
    "https://conservatoirena-my.sharepoint.com/:x:/r/personal/tests/Documents/flux.csv"
    "?d=w0000&csf=1&web=1&e=TEST"
)
GRAPH_URL = "https://graph.microsoft.com/v1.0/sites/abc/drive/root:/flux.csv:/content"


class FakeReply:
    def __init__(self, data=b"payload"):
        self._data = data

    def content(self):
        return self._data


class FakeBlocking:
    """Double de QgsBlockingNetworkRequest : capture les requêtes émises.

    `responses` associe un fragment d'URL au contenu à retourner (défaut
    b"payload") ; `requests` accumule toutes les QNetworkRequest émises.
    """

    NoError = 0
    last = None
    requests = []
    responses = {}

    def __init__(self):
        self.authcfg = None
        self.request = None
        FakeBlocking.last = self

    def setAuthCfg(self, authcfg):
        self.authcfg = authcfg

    def get(self, request):
        self.request = request
        FakeBlocking.requests.append(request)
        return FakeBlocking.NoError

    def errorMessage(self):
        return ""

    def reply(self):
        url = self.request.url().toString()
        for fragment, data in FakeBlocking.responses.items():
            if fragment in url:
                return FakeReply(data)
        return FakeReply()


def make_plugin(tmp_path, authcfg="abc1234"):
    """Instance minimale de FluxCEN sans GUI : uniquement plugin_path + config."""
    cfg_dir = tmp_path / "config" / "yaml"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "links.yaml").write_text(
        f"auth:\n  authcfg: \"{authcfg}\"\n", encoding="utf-8"
    )
    obj = plugin_mod.FluxCEN.__new__(plugin_mod.FluxCEN)
    obj.plugin_path = str(tmp_path)
    obj._styles_folder_ref = None
    return obj


@pytest.fixture
def fake_network(monkeypatch):
    monkeypatch.setattr(plugin_mod, "QgsBlockingNetworkRequest", FakeBlocking)
    FakeBlocking.last = None
    FakeBlocking.requests = []
    FakeBlocking.responses = {}
    return FakeBlocking


def sent_url(fake):
    return fake.last.request.url().toString()


def prefer_header(fake):
    return bytes(fake.last.request.rawHeader(b"Prefer"))


class TestResolutionLienDePartage:
    """T007 — US1 : conversion des liens de partage avant la requête."""

    def test_lien_de_partage_converti_en_url_graph(self, tmp_path, fake_network):
        plugin = make_plugin(tmp_path)
        data = plugin._fetch_bytes(SHARING_LINK)
        assert data == b"payload"
        url = sent_url(fake_network)
        assert url.startswith("https://graph.microsoft.com/v1.0/shares/u!")
        assert url.endswith("/driveItem/content")

    def test_en_tete_prefer_sur_lien_converti(self, tmp_path, fake_network):
        plugin = make_plugin(tmp_path)
        plugin._fetch_bytes(SHARING_LINK)
        assert prefer_header(fake_network) == b"redeemSharingLinkIfNecessary"

    def test_url_graph_directe_inchangee(self, tmp_path, fake_network):
        plugin = make_plugin(tmp_path)
        plugin._fetch_bytes(GRAPH_URL)
        assert sent_url(fake_network) == GRAPH_URL
        assert prefer_header(fake_network) == b""


class TestFiltragePerimetreAuth:
    """T012 — US2 : l'authcfg ne sort jamais du périmètre Microsoft (FR-004/FR-006)."""

    def test_authcfg_pour_graph(self, tmp_path, fake_network):
        plugin = make_plugin(tmp_path, authcfg="abc1234")
        plugin._fetch_bytes(GRAPH_URL)
        assert fake_network.last.authcfg == "abc1234"

    def test_authcfg_pour_lien_de_partage(self, tmp_path, fake_network):
        plugin = make_plugin(tmp_path, authcfg="abc1234")
        plugin._fetch_bytes(SHARING_LINK)
        assert fake_network.last.authcfg == "abc1234"

    @pytest.mark.parametrize("url", [
        "https://raw.githubusercontent.com/CEN/fluxcen/main/styles_couches/a.qml",
        "https://sharepoint.com.evil.tld/x",
        "https://graph.microsoft.com.evil.tld/x",
    ])
    def test_jamais_d_authcfg_hors_perimetre(self, tmp_path, fake_network, url):
        plugin = make_plugin(tmp_path, authcfg="abc1234")
        plugin._fetch_bytes(url)
        assert fake_network.last.authcfg is None

    def test_http_rejete_sans_requete(self, tmp_path, fake_network):
        plugin = make_plugin(tmp_path, authcfg="abc1234")
        with pytest.raises(Exception) as excinfo:
            plugin._fetch_bytes("http://exemple.org/flux.csv")
        assert "HTTPS" in str(excinfo.value)
        assert fake_network.last is None  # aucune requête émise

    def test_data_url_toleree_sans_auth(self, tmp_path, fake_network):
        plugin = make_plugin(tmp_path, authcfg="abc1234")
        data = plugin._fetch_bytes("data:text/plain,version=5.2")
        assert data == b"payload"
        assert fake_network.last.authcfg is None


class TestPreferSurUrlSharesPreConvertie:
    """Finding 5 : l'en-tête Prefer accompagne toute URL Graph /shares/,
    y compris celles pré-construites (résolution du dossier des styles)."""

    def test_url_metadata_dossier_partage(self, tmp_path, fake_network):
        from fluxcen.core.ms_urls import sharing_link_to_graph_metadata_url
        plugin = make_plugin(tmp_path)
        meta_url = sharing_link_to_graph_metadata_url("https://tenant.sharepoint.com/dossier")
        plugin._fetch_bytes(meta_url, "dossier des styles")
        assert prefer_header(fake_network) == b"redeemSharingLinkIfNecessary"


FOLDER_LINK = "https://tenant.sharepoint.com/:f:/r/sites/x/styles_couches?csf=1&web=1&e=Z"
META_JSON = b'{"id": "ITEM123", "parentReference": {"driveId": "b!DRIVE456"}}'


class TestResolutionStyleDossierPartage:
    """Deux étapes validées contre le tenant réel (2026-07-27) : Graph rejette
    l'adressage par chemin sous /shares — résolution driveId/itemId d'abord."""

    def test_deux_requetes_puis_url_drives(self, tmp_path, fake_network):
        plugin = make_plugin(tmp_path)
        fake_network.responses["$select=id,parentReference"] = META_JSON
        style_url = plugin._style_url(FOLDER_LINK, "RPG")
        assert style_url == ("https://graph.microsoft.com/v1.0/drives/b!DRIVE456"
                             "/items/ITEM123:/RPG.qml:/content")
        urls = [r.url().toString() for r in fake_network.requests]
        assert len(urls) == 1  # une seule requête réseau : la résolution
        assert "/shares/u!" in urls[0] and "$select=id,parentReference" in urls[0]

    def test_resolution_en_cache_pour_la_session(self, tmp_path, fake_network):
        plugin = make_plugin(tmp_path)
        fake_network.responses["$select=id,parentReference"] = META_JSON
        plugin._style_url(FOLDER_LINK, "RPG")
        plugin._style_url(FOLDER_LINK, "znieff2")
        assert len(fake_network.requests) == 1  # le dossier n'est résolu qu'une fois

    def test_url_directe_sans_reseau(self, tmp_path, fake_network):
        plugin = make_plugin(tmp_path)
        base = "https://raw.githubusercontent.com/x/styles_couches/"
        assert plugin._style_url(base, "RPG") == base + "RPG.qml"
        assert fake_network.requests == []


class TestSchemasRefuses:
    """Finding 6 : seuls https et data: sont acceptés ; message sans userinfo."""

    @pytest.mark.parametrize("url", [
        "ftp://exemple.org/flux.csv",
        "file:///etc/passwd",
        "http://exemple.org/flux.csv",
    ])
    def test_schema_refuse_sans_requete(self, tmp_path, fake_network, url):
        plugin = make_plugin(tmp_path)
        with pytest.raises(Exception):
            plugin._fetch_bytes(url)
        assert fake_network.last is None

    def test_message_sans_userinfo(self, tmp_path, fake_network):
        plugin = make_plugin(tmp_path)
        with pytest.raises(Exception) as excinfo:
            plugin._fetch_bytes("ftp://utilisateur:motdepasse@exemple.org/x")
        assert "motdepasse" not in str(excinfo.value)


class TestAuthManquante:
    """T024 — US3 : périmètre Microsoft sans authcfg → erreur d'orientation, sans requête."""

    def test_url_microsoft_sans_authcfg(self, tmp_path, fake_network):
        plugin = make_plugin(tmp_path, authcfg="")
        with pytest.raises(FetchError) as excinfo:
            plugin._fetch_bytes(SHARING_LINK, "catalogue des flux")
        assert excinfo.value.family is ErrorFamily.AUTH_MANQUANTE
        assert fake_network.last is None  # aucune requête émise
