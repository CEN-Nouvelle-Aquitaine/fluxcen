# -*- coding: utf-8 -*-
"""Tests d'intégration du provisioning : écriture des dépôts dans QgsSettings.

Contrat : specs/002-plugin-delivery/contracts/provisioning.md (idempotence,
réparation, checkOnStart). Nécessitent QGIS (ignorés sans bindings ;
exécutés en CI sur l'image qgis/qgis).
"""
# pylint: disable=wrong-import-position,redefined-outer-name,missing-function-docstring,unused-argument
import pytest

pytest.importorskip("qgis.core")
pytestmark = pytest.mark.integration

from qgis.core import QgsSettings  # noqa: E402

from delivery.provisioning import provision  # noqa: E402

BASE_URL = "https://func-fluxcen-delivery-poc.azurewebsites.net"
REPO_PREFIX = "app/plugin_repositories/FluxCEN (interne)/"


@pytest.fixture
def settings(qgis_app):
    s = QgsSettings()
    s.remove("app/plugin_repositories/FluxCEN (interne)")
    s.remove("app/plugin_repositories/FluxCEN (beta)")
    s.remove("app/plugin_installer/checkOnStart")
    yield s


def test_poste_vierge_puis_idempotence(settings):
    changed = provision.ensure_repositories(settings, BASE_URL, "f2deliv")
    assert changed is True
    assert settings.value(REPO_PREFIX + "url") == f"{BASE_URL}/stable/plugins.xml"
    assert settings.value(REPO_PREFIX + "authcfg") == "f2deliv"

    # Ré-exécution : aucune écriture (contrat : idempotence)
    assert provision.ensure_repositories(settings, BASE_URL, "f2deliv") is False


def test_url_derivee_reparee(settings):
    provision.ensure_repositories(settings, BASE_URL, "f2deliv")
    settings.setValue(REPO_PREFIX + "url", "https://ancienne-url/plugins.xml")

    assert provision.ensure_repositories(settings, BASE_URL, "f2deliv") is True
    assert settings.value(REPO_PREFIX + "url") == f"{BASE_URL}/stable/plugins.xml"


def test_depot_beta_obsolete_nettoye(settings):
    # Postes provisionnés pendant le POC : l'ancien dépôt beta est retiré.
    settings.setValue("app/plugin_repositories/FluxCEN (beta)/url",
                      f"{BASE_URL}/beta/plugins.xml")
    assert provision.ensure_repositories(settings, BASE_URL, "f2deliv") is True
    assert not settings.value("app/plugin_repositories/FluxCEN (beta)/url")


def test_check_on_start_desactive(settings):
    settings.setValue("app/plugin_installer/checkOnStart", True)
    provision.ensure_repositories(settings, BASE_URL, "f2deliv")
    assert settings.value("app/plugin_installer/checkOnStart", type=bool) is False
