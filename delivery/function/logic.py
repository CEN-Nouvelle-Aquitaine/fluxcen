# -*- coding: utf-8 -*-
"""Logique pure du service de distribution FluxCEN.

Contrat : specs/002-plugin-delivery/contracts/http-delivery.md.
Aucune dépendance Azure ni réseau : tout est testable en pytest pur.
"""
from __future__ import annotations

import base64
import binascii
import json
import re

CHANNELS = frozenset({"stable", "beta"})

# plugins.xml, ou FluxCEN.<x.y.z>[-préversion].zip ; rien d'autre (pas de
# traversée possible : aucun séparateur de chemin n'est admis par le motif).
_FILENAME_RE = re.compile(
    r"^(plugins\.xml|FluxCEN\.\d+\.\d+\.\d+(-[0-9A-Za-z]+(\.[0-9A-Za-z]+)*)?\.zip)$"
)


def resolve_blob(channel: str, filename: str) -> str | None:
    """Chemin du blob pour (canal, fichier), ou None si hors contrat (404)."""
    if channel not in CHANNELS or not _FILENAME_RE.match(filename or ""):
        return None
    return f"{channel}/{filename}"


def content_type(filename: str) -> str:
    """Content-Type d'un fichier admis par le contrat (xml ou zip)."""
    return "text/xml" if filename.endswith(".xml") else "application/zip"


def parse_groups(principal_b64: str | None) -> set[str]:
    """Groupes du claim `groups` d'un header x-ms-client-principal Easy Auth.

    Tout header absent, non décodable ou mal formé vaut « aucun groupe » :
    l'autorisation beta échouera alors en 403, jamais en erreur serveur.
    """
    if not principal_b64:
        return set()
    try:
        principal = json.loads(base64.b64decode(principal_b64))
        return {
            c["val"]
            for c in principal.get("claims", [])
            if c.get("typ") == "groups" and c.get("val")
        }
    except (ValueError, binascii.Error, TypeError, AttributeError):
        return set()


def is_authorized(channel: str, groups: set[str], beta_group_id: str) -> bool:
    """Le canal stable est ouvert à toute identité validée ; beta exige le groupe."""
    return channel != "beta" or beta_group_id in groups
