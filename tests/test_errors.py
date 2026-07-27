# -*- coding: utf-8 -*-
"""Tests unitaires purs de core.errors (familles d'erreurs de téléchargement).

Data-model : specs/001-sharepoint-share-urls/data-model.md (ErreurTelechargement).
"""
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

    def test_message_reseau(self):
        message = FetchError(ErrorFamily.RESEAU, "changelog",
                             host="raw.githubusercontent.com").user_message()
        assert "connexion" in message

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
