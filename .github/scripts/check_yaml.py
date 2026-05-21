#!/usr/bin/env python3
# Called by the Quality workflow on every pull request targeting main.
# Performs two checks:
#   1. Parses config/yaml/links_example.yaml and config/yaml/config_db_example.yaml
#      and fails if either contains invalid YAML syntax or is missing.
#   2. Fails if config/yaml/links.yaml or config/yaml/config_db.yaml is present in
#      the working tree (safety net — these files must never be committed).
# Exits with code 1 and prints GitHub Actions error annotations on any violation.
import os
import sys
import yaml

errors = []

for path in ('config/yaml/links_example.yaml', 'config/yaml/config_db_example.yaml'):
    try:
        with open(path, encoding='utf-8') as f:
            yaml.safe_load(f)
        print(f'{path} OK')
    except yaml.YAMLError as exc:
        errors.append(f'{path}: erreur de syntaxe YAML — {exc}')
    except FileNotFoundError:
        errors.append(f'{path}: fichier introuvable')

for path in ('config/yaml/links.yaml', 'config/yaml/config_db.yaml'):
    if os.path.exists(path):
        errors.append(f'{path}: fichier commité — ne doit pas être versionné (voir .gitignore)')
    else:
        print(f'{path} OK — non commité')

if errors:
    for e in errors:
        print(f'::error::{e}')
    sys.exit(1)
