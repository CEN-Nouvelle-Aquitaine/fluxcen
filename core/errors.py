# -*- coding: utf-8 -*-
"""Familles d'erreurs de téléchargement et messages utilisateur.

Fonctions pures (stdlib uniquement) — data-model :
specs/001-sharepoint-share-urls/data-model.md (ErreurTelechargement).

Les messages ne contiennent jamais d'URL complète ni de jeton : uniquement le
nom logique de la ressource et, au besoin, le nom d'hôte (FR-007).
"""
from enum import Enum
from typing import Optional


class ErrorFamily(Enum):
    """Famille d'un échec de téléchargement de ressource distante."""

    LIEN_INVALIDE = "lien_invalide"
    ACCES_REFUSE = "acces_refuse"
    AUTH_MANQUANTE = "auth_manquante"
    AUTH_PROVISIONNEMENT = "auth_provisionnement"
    PORT_REDIRECTION = "port_redirection"
    RESEAU = "reseau"


_MESSAGES = {
    ErrorFamily.LIEN_INVALIDE:
        "Le lien configuré pour « {resource} » est invalide ou expiré ({host}).",
    ErrorFamily.ACCES_REFUSE:
        "Accès refusé à « {resource} » ({host}) : vérifiez vos droits SharePoint.",
    ErrorFamily.AUTH_MANQUANTE:
        "« {resource} » nécessite une authentification Microsoft : configurez-la "
        "dans QGIS (Préférences > Authentification, voir documentation).",
    ErrorFamily.AUTH_PROVISIONNEMENT:
        "« {resource} » : l'installation de la configuration d'authentification "
        "Microsoft dans QGIS a échoué (mot de passe principal refusé ou système "
        "d'authentification indisponible).",
    ErrorFamily.PORT_REDIRECTION:
        "« {resource} » : les ports de redirection de l'authentification "
        "Microsoft sont tous occupés par un autre logiciel (ex. outil de prise "
        "en main à distance). Fermez-le puis réessayez.",
    ErrorFamily.RESEAU:
        "« {resource} » inaccessible ({host}) : vérifiez votre connexion.",
}


class FetchError(Exception):
    """Échec de téléchargement d'une ressource distante, classé par famille."""

    def __init__(self, family: ErrorFamily, resource_name: str, host: str = ""):
        self.family = family
        self.resource_name = resource_name
        self.host = host
        super().__init__(self.user_message())

    def user_message(self) -> str:
        """Message utilisateur en français, sans URL complète ni jeton."""
        return _MESSAGES[self.family].format(
            resource=self.resource_name, host=self.host or "hôte inconnu")


def classify_http_status(status: Optional[int]) -> ErrorFamily:
    """Famille d'erreur déduite du statut HTTP (None = pas de réponse : réseau)."""
    if status in (400, 404):
        return ErrorFamily.LIEN_INVALIDE
    if status in (401, 403):
        return ErrorFamily.ACCES_REFUSE
    return ErrorFamily.RESEAU
