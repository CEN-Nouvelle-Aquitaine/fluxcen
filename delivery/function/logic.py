# -*- coding: utf-8 -*-
"""Logique pure du service de distribution FluxCEN.

Contrat : specs/002-plugin-delivery/contracts/http-delivery.md. Dépôt unique
(standard communautaire QGIS) : les préversions sont des entrées
``experimental`` du même catalogue, l'opt-in se fait côté client. Toute
identité du tenant validée par Easy Auth accède au dépôt : aucune
autorisation supplémentaire côté code.
Aucune dépendance Azure ni réseau : tout est testable en pytest pur.
"""
from __future__ import annotations

import re

# Segment historique unique du dépôt (URL stable, contrat).
CHANNELS = frozenset({"stable"})

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
