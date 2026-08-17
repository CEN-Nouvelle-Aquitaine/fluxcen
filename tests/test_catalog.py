# -*- coding: utf-8 -*-
"""Tests unitaires purs de core.catalog (parsing/validation du catalogue de flux).

Data-model : specs/001-sharepoint-share-urls/data-model.md (CatalogueFlux).
"""
# pylint: disable=missing-class-docstring,missing-function-docstring,too-few-public-methods,redefined-outer-name,protected-access,wrong-import-position,wrong-import-order,unused-argument
import pathlib

from core.catalog import (
    FluxRow,
    extract_categories,
    parse_catalog,
    parse_table_row,
)

DATA_DIR = pathlib.Path(__file__).resolve().parent / "data"

WFS_CELLS = ["WFS", "Zonages", "ZNIEFF de type 1", "znieff1",
             "https://data.geopf.fr/wfs/ows?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities",
             "INPN", "style_znieff", "https://example.org/meta", "", ""]


def cells(**overrides):
    row = list(WFS_CELLS)
    indexes = {"service": 0, "categorie": 1, "nom_couche": 2, "nom_technique": 3,
               "url": 4, "source": 5, "style": 6, "metadonnees": 7,
               "nom_bdd": 8, "nom_schema": 9}
    for key, value in overrides.items():
        row[indexes[key]] = value
    return row


class TestParseTableRow:
    def test_ligne_wfs_valide(self):
        row = parse_table_row(WFS_CELLS)
        assert isinstance(row, FluxRow)
        assert row.service == "WFS"
        assert row.nom_technique == "znieff1"
        assert row.style == "style_znieff"

    def test_wms_avec_variante(self):
        # le catalogue réel contient des services "WMS..." (startswith)
        assert parse_table_row(cells(service="WMS 1.3.0")) is not None

    def test_service_inconnu_ignore(self):
        assert parse_table_row(cells(service="WCS")) is None

    def test_colonnes_manquantes_ignorees(self):
        assert parse_table_row(WFS_CELLS[:6]) is None

    def test_champs_obligatoires(self):
        for field in ("service", "categorie", "nom_couche", "nom_technique", "url"):
            assert parse_table_row(cells(**{field: ""})) is None

    def test_postgis_sans_url_valide(self):
        row = parse_table_row(cells(service="PostGIS", url="",
                                    nom_bdd="bdcen", nom_schema="foncier"))
        assert row is not None
        assert row.nom_bdd == "bdcen"

    def test_postgis_sans_bdd_ou_schema_ignore(self):
        assert parse_table_row(cells(service="PostGIS", url="", nom_schema="")) is None
        assert parse_table_row(cells(service="PostGIS", url="", nom_bdd="")) is None

    def test_style_traversee_de_chemin_rejete(self):
        # le nom vient du catalogue distant et sert à construire une URL :
        # tout séparateur ou ".." le neutralise (style absent), sans invalider la ligne
        for bad in ("a/b", "a\\b", "../etc", "a..b"):
            row = parse_table_row(cells(style=bad))
            assert row is not None
            assert row.style is None

    def test_style_trop_court_absent(self):
        assert parse_table_row(cells(style=" x ")).style is None
        assert parse_table_row(cells(style="")).style is None


class TestParseCatalog:
    def test_fichier_minimal(self):
        text = (DATA_DIR / "flux_minimal.csv").read_text(encoding="utf-8")
        rows, warnings = parse_catalog(text)
        assert [r.service for r in rows] == ["WMS", "WFS", "PostGIS"]
        assert warnings == []

    def test_ligne_invalide_ignoree_avec_warning(self):
        text = ("service;categorie;Nom_couche_plugin;nom_technique;url;source;style;metadonnees;nom_bdd;nom_schema\n"
                "WCS;Cat;Nom;tech;https://exemple.org;src;;;;\n"
                + ";".join(WFS_CELLS) + "\n")
        rows, warnings = parse_catalog(text)
        assert len(rows) == 1
        assert len(warnings) == 1
        assert "2" in warnings[0]  # numéro de ligne dans le message

    def test_jamais_d_exception_sur_contenu_hostile(self):
        rows, _ = parse_catalog("pas;un;vrai;catalogue")
        assert rows == []


class TestExtractCategories:
    def test_categories_uniques_triees(self):
        text = (DATA_DIR / "flux_minimal.csv").read_text(encoding="utf-8")
        assert extract_categories(text) == ["Cartographie", "Foncier", "Zonages"]

