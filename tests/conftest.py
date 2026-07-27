# -*- coding: utf-8 -*-
"""Configuration pytest de FluxCEN.

Les tests purs (test_ms_urls, test_catalog, test_errors) n'importent que ``core``
et tournent sans QGIS. Les tests d'intégration (test_fetch, test_layers,
test_startup) utilisent ``pytest.importorskip("qgis.core")`` et les fixtures de
pytest-qgis : ils sont ignorés sur un poste sans QGIS et s'exécutent en CI.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

# `import core...` (tests purs) et `import fluxcen...` (tests d'intégration,
# le répertoire du dépôt porte le nom du package plugin).
for path in (str(ROOT), str(ROOT.parent)):
    if path not in sys.path:
        sys.path.insert(0, path)

DATA_DIR = pathlib.Path(__file__).resolve().parent / "data"
