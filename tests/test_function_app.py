# -*- coding: utf-8 -*-
"""Tests in-process du handler HTTP de la Function (spec 002).

Exécutent le vrai `serve()` avec des requêtes forgées et un blob simulé :
valident le contrat http-delivery.md (200/403/404, content-types) sans Azure.
Le 401 est hors périmètre : il est émis par Easy Auth en amont du code.

Nécessitent le SDK azure-functions (ignorés sinon ; voir quickstart,
« Simulation locale »).
"""
# pylint: disable=wrong-import-position,missing-class-docstring,missing-function-docstring,redefined-outer-name,too-few-public-methods,import-outside-toplevel
import base64
import json
import pathlib
import sys

import pytest

func = pytest.importorskip("azure.functions")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "delivery" / "function"))

import function_app  # noqa: E402

pytestmark = pytest.mark.unit

BETA_GROUP = "11111111-2222-3333-4444-555555555555"
XML = b"<?xml version='1.0'?><plugins></plugins>"


class FakeBlob:
    def __init__(self, payload):
        self._payload = payload

    def readall(self):
        return self._payload


class FakeContainer:
    """Simule le conteneur blob : stable/plugins.xml et un zip existent."""

    BLOBS = {
        "stable/plugins.xml": XML,
        "beta/plugins.xml": XML,
        "stable/FluxCEN.5.3.0.zip": b"PK\x03\x04fake",
    }

    def download_blob(self, path):
        try:
            return FakeBlob(self.BLOBS[path])
        except KeyError as exc:
            from azure.core.exceptions import ResourceNotFoundError
            raise ResourceNotFoundError() from exc


@pytest.fixture(autouse=True)
def fake_azure(monkeypatch):
    monkeypatch.setattr(function_app, "_container", FakeContainer)
    monkeypatch.setenv("BETA_GROUP_ID", BETA_GROUP)


def principal(groups):
    claims = [{"typ": "groups", "val": g} for g in groups]
    return base64.b64encode(json.dumps({"claims": claims}).encode()).decode()


def request(channel, filename, groups=None):
    headers = {}
    if groups is not None:
        headers["x-ms-client-principal"] = principal(groups)
    return func.HttpRequest(
        method="GET",
        url=f"https://local/{channel}/{filename}",
        headers=headers,
        route_params={"channel": channel, "filename": filename},
        body=b"",
    )


def test_stable_catalogue_200_xml():
    resp = function_app.serve(request("stable", "plugins.xml"))
    assert resp.status_code == 200
    assert resp.mimetype == "text/xml"
    assert resp.get_body() == XML


def test_stable_zip_200_zip():
    resp = function_app.serve(request("stable", "FluxCEN.5.3.0.zip"))
    assert resp.status_code == 200
    assert resp.mimetype == "application/zip"


def test_beta_membre_200():
    resp = function_app.serve(request("beta", "plugins.xml", groups=[BETA_GROUP]))
    assert resp.status_code == 200


def test_beta_non_membre_403():
    resp = function_app.serve(request("beta", "plugins.xml", groups=["autre"]))
    assert resp.status_code == 403


def test_beta_sans_principal_403():
    resp = function_app.serve(request("beta", "plugins.xml"))
    assert resp.status_code == 403


def test_blob_absent_404():
    resp = function_app.serve(request("stable", "FluxCEN.9.9.9.zip"))
    assert resp.status_code == 404


def test_chemin_hors_contrat_404():
    resp = function_app.serve(request("stable", "../../etc/passwd"))
    assert resp.status_code == 404
