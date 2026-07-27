# -*- coding: utf-8 -*-
"""Parsing et validation du catalogue de flux, construction des URI de couches.

Fonctions pures (stdlib uniquement) — data-model :
specs/001-sharepoint-share-urls/data-model.md (CatalogueFlux).

Le catalogue est un CSV ``;`` de 10 colonnes :
service;categorie;Nom_couche_plugin;nom_technique;url;source;style;metadonnees;nom_bdd;nom_schema
Son contenu est distant, donc non fiable : toute ligne invalide est ignorée
(avec avertissement), jamais convertie en exception.
"""
import csv
import io
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .ms_urls import https_hostname

_EXPECTED_COLUMNS = 10
_DEFAULT_SERVICE_VERSION = "1.0.0"

# Services cartographiques du CEN nécessitant une authentification (FR-012) —
# jamais la configuration Microsoft, uniquement une méthode non web (FR-011).
_CEN_SECURED_HOSTS = frozenset({"opendata.cen-nouvelle-aquitaine.org"})


@dataclass(frozen=True)
class FluxRow:  # pylint: disable=too-many-instance-attributes
    """Ligne validée du catalogue de flux (les 10 colonnes du CSV)."""

    service: str
    categorie: str
    nom_couche: str
    nom_technique: str
    url: str
    source: str
    style: Optional[str]
    metadonnees: str
    nom_bdd: str
    nom_schema: str


def _clean_style(style: str) -> Optional[str]:
    """Nom de style validé, ou None s'il est absent ou dangereux.

    Le nom provient du catalogue distant et sert à construire une URL de
    téléchargement : séparateurs de chemin et ``..`` sont neutralisés.
    """
    style = (style or "").strip()
    if len(style) < 2:
        return None
    if "/" in style or "\\" in style or ".." in style:
        return None
    return style


def parse_table_row(cells: List[str]) -> Optional[FluxRow]:
    """Valide une ligne du catalogue ; None si elle doit être ignorée."""
    if len(cells) < _EXPECTED_COLUMNS:
        return None
    values = [(cell or "").strip() for cell in cells[:_EXPECTED_COLUMNS]]
    (service, categorie, nom_couche, nom_technique, url,
     source, style, metadonnees, nom_bdd, nom_schema) = values

    if not (service.startswith("WMS") or service in ("WFS", "PostGIS")):
        return None
    if not (categorie and nom_couche and nom_technique):
        return None
    if service == "PostGIS":
        if not (nom_bdd and nom_schema):
            return None
    elif not url:
        return None

    return FluxRow(service, categorie, nom_couche, nom_technique, url,
                   source, _clean_style(style), metadonnees, nom_bdd, nom_schema)


def parse_catalog(csv_text: str) -> Tuple[List[FluxRow], List[str]]:
    """Parse le catalogue complet ; retourne (lignes valides, avertissements)."""
    rows: List[FluxRow] = []
    warnings: List[str] = []
    reader = csv.reader(io.StringIO(csv_text), delimiter=";")
    for line_number, cells in enumerate(reader, start=1):
        if line_number == 1 or not any(cell.strip() for cell in cells):
            continue  # en-tête ou ligne vide
        row = parse_table_row(cells)
        if row is None:
            warnings.append(
                f"ligne {line_number} du catalogue ignorée "
                "(service inconnu ou champs manquants)")
        else:
            rows.append(row)
    return rows, warnings


def extract_categories(csv_text: str) -> List[str]:
    """Catégories uniques du catalogue, triées."""
    reader = csv.DictReader(io.StringIO(csv_text), delimiter=";")
    categories = {(row.get("categorie") or "").strip() for row in reader}
    categories.discard("")
    return sorted(categories)


def extract_service_version(url: str) -> str:
    """Version du service extraite de l'URL (motif historique VERSION=…&REQUEST)."""
    match = re.search("VERSION=(.+?)&REQUEST", url)
    return match.group(1) if match else _DEFAULT_SERVICE_VERSION


def is_cen_secured_service(url: str) -> bool:
    """Vraie ssi l'URL cible un service cartographique sécurisé du CEN (FR-012)."""
    return https_hostname(url) in _CEN_SECURED_HOSTS


def parse_version(text: str) -> str:
    """Extrait le numéro de version d'un metadata.txt ou d'un fichier de version.

    Cherche la première ligne ``version=X`` ; à défaut, retourne la première
    ligne non vide sans ``=`` (fichier de version brut). Remplace l'ancien
    accès par index de ligne en dur, fragile.
    """
    fallback = ""
    for line in (text or "").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("version="):
            return stripped.split("=", 1)[1].strip()
        if not fallback and "=" not in stripped and not stripped.startswith("["):
            fallback = stripped
    return fallback


def build_wms_uri(url: str, nom_technique: str, version: Optional[str] = None,
                  authcfg: Optional[str] = None) -> str:
    """URI de couche WMS.

    ``authcfg`` n'est ajoutée que si elle est fournie explicitement — réservée
    au périmètre sécurisé du CEN (FR-012), jamais par défaut (FR-010).
    """
    version = version or extract_service_version(url)
    uri = (
        f"url={url}&"
        f"service=WMS&"
        f"version={version}&"
        f"crs=EPSG:2154&"
        f"format=image/png&"
        f"layers={nom_technique}&"
        f"styles"
    )
    if authcfg:
        uri += f"&authcfg={authcfg}"
    return uri


def build_wfs_uri_params(url: str, typename: str, version: Optional[str] = None) -> dict:
    """Paramètres d'URI de couche WFS — sans aucune configuration d'authentification (FR-010)."""
    return {
        "url": url,
        "version": version or extract_service_version(url),
        "typename": typename,
        "request": "GetFeature",
    }
