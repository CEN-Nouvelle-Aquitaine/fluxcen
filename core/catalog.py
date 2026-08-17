# -*- coding: utf-8 -*-
"""Parsing et validation du catalogue de flux.

Fonctions pures (stdlib uniquement) — data-model :
specs/001-sharepoint-share-urls/data-model.md (CatalogueFlux).
La construction des URI de couches est dans ``core/layer_builder.py``.

Le catalogue est un CSV ``;`` de 10 colonnes :
service;categorie;Nom_couche_plugin;nom_technique;url;source;style;metadonnees;nom_bdd;nom_schema
Son contenu est distant, donc non fiable : toute ligne invalide est ignorée
(avec avertissement), jamais convertie en exception.
"""
import csv
import io
from dataclasses import dataclass
from typing import List, Optional, Tuple

_EXPECTED_COLUMNS = 10


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


