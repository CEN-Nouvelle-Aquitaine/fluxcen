# -*- coding: utf-8 -*-
"""Tests unitaires purs de core.errors (familles d'erreurs de téléchargement).

Data-model : specs/001-sharepoint-share-urls/data-model.md (ErreurTelechargement).
"""
# pylint: disable=missing-class-docstring,missing-function-docstring,too-few-public-methods,redefined-outer-name,protected-access,wrong-import-position,wrong-import-order,unused-argument
import pytest

from core.errors import ErrorFamily, FetchError, classify_http_status


class TestClassifyHttpStatus:
    @pytest.mark.parametrize("status,family", [
        (400, ErrorFamily.LIEN_INVALIDE),
        (404, ErrorFamily.LIEN_INVALIDE),
        (401, ErrorFamily.ACCES_REFUSE),
        (403, ErrorFamily.ACCES_REFUSE),
        (500, ErrorFamily.RESEAU),
        (None, ErrorFamily.RESEAU),   # timeout, DNS, connexion : pas de statut HTTP
    ])
    def test_mapping(self, status, family):
        assert classify_http_status(status) is family


class TestFetchError:
    def test_message_lien_invalide(self):
        err = FetchError(ErrorFamily.LIEN_INVALIDE, "catalogue des flux",
                         host="tenant.sharepoint.com")
        message = err.user_message()
        assert "catalogue des flux" in message
        assert "invalide" in message

    def test_message_acces_refuse(self):
        message = FetchError(ErrorFamily.ACCES_REFUSE, "catalogue des flux",
                             host="tenant.sharepoint.com").user_message()
        assert "droits" in message

    def test_message_auth_manquante_oriente_utilisateur(self):
        message = FetchError(ErrorFamily.AUTH_MANQUANTE, "catalogue des flux",
                             host="graph.microsoft.com").user_message()
        assert "authentification" in message.lower()
        # Data-model (ErreurTelechargement) : la seule action proposée est la
        # configuration dans QGIS — links.yaml n'est plus requis, la config
        # est découverte dans le gestionnaire d'auth (revue de PR, issue #39)
        assert "links.yaml" not in message

    def test_message_reseau(self):
        message = FetchError(ErrorFamily.RESEAU, "changelog",
                             host="raw.githubusercontent.com").user_message()
        assert "connexion" in message

    def test_message_provisionnement(self):
        # FR-013 : échec d'écriture de la config canonique — jamais un faux
        # diagnostic réseau
        message = FetchError(ErrorFamily.AUTH_PROVISIONNEMENT, "catalogue des flux",
                             host="graph.microsoft.com").user_message()
        assert "installation" in message.lower() or "enregistr" in message.lower()
        assert "connexion" not in message.lower()

    def test_message_port_redirection(self):
        # FR-013 : ports de redirection occupés (ex. AnyDesk sur 7070)
        message = FetchError(ErrorFamily.PORT_REDIRECTION, "catalogue des flux",
                             host="graph.microsoft.com").user_message()
        assert "port" in message.lower()
        assert "logiciel" in message.lower()
        assert "connexion" not in message.lower()

    def test_jamais_d_url_complete_ni_de_jeton(self):
        # Le message ne contient que le nom d'hôte, jamais l'URL complète
        # (qui peut porter des paramètres sensibles) ni de jeton.
        for family in ErrorFamily:
            err = FetchError(family, "ressource", host="tenant.sharepoint.com")
            message = err.user_message()
            assert "https://" not in message
            assert "?" not in message

    def test_est_une_exception(self):
        with pytest.raises(FetchError):
            raise FetchError(ErrorFamily.RESEAU, "ressource", host="exemple.org")
