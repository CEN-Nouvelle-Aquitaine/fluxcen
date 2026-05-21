#!/usr/bin/env python3
# Called by the Quality workflow on every pull request targeting main.
# Reads metadata.txt and enforces three rules:
#   1. Line 9 must start with "version=" and match X.Y.Z (stable) or X.Y.Z-betaN (beta, N >= 1).
#   2. If the version is a beta, experimental=True must also be present in the file.
#   3. The version must be strictly greater than the one currently on main
#      (semver order: stable > any beta of the same X.Y.Z; betas ordered by N).
# Exits with code 1 and prints GitHub Actions error annotations on any violation.
import re
import subprocess
import sys

VERSION_RE = re.compile(r'^(\d+)\.(\d+)\.(\d+)(?:-beta(\d+))?$')


def parse_version(v):
    m = VERSION_RE.match(v.strip())
    if not m:
        return None
    major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
    beta_n = int(m.group(4)) if m.group(4) else None
    return (major, minor, patch, beta_n)


def cmp_key(parsed):
    major, minor, patch, beta_n = parsed
    # stable > toute beta du même X.Y.Z ; betas triées par N croissant
    if beta_n is None:
        return (major, minor, patch, 1, 0)
    return (major, minor, patch, 0, beta_n)


def version_from_metadata(content):
    lines = content.splitlines()
    if len(lines) < 9:
        return None
    line = lines[8]  # ligne 9, index 8 (blank lines comprises)
    if not line.startswith('version='):
        return None
    return line[len('version='):]


def experimental_value(content):
    for line in content.splitlines():
        if line.strip().startswith('experimental='):
            return line.strip()[len('experimental='):]
    return None


errors = []

with open('metadata.txt', encoding='utf-8') as f:
    current = f.read()

version_str = version_from_metadata(current)
if version_str is None:
    print('::error::metadata.txt: ligne 9 ne commence pas par "version="')
    sys.exit(1)

parsed = parse_version(version_str)
if parsed is None:
    errors.append(
        f'metadata.txt: version="{version_str}" ne respecte pas le format '
        'X.Y.Z (stable) ou X.Y.Z-betaN (bêta, N ≥ 1)'
    )
else:
    _, _, _, beta_n = parsed
    if beta_n is not None:
        experimental = experimental_value(current)
        if experimental != 'True':
            errors.append(
                f'metadata.txt: version bêta "{version_str}" détectée mais '
                f'experimental=True absent ou incorrect (valeur: "{experimental}")'
            )

# Comparer avec main
try:
    main_content = subprocess.check_output(
        ['git', 'show', 'origin/main:metadata.txt'],
        text=True, stderr=subprocess.DEVNULL
    )
    main_version_str = version_from_metadata(main_content)
    if main_version_str and parsed:
        main_parsed = parse_version(main_version_str)
        if main_parsed and cmp_key(parsed) <= cmp_key(main_parsed):
            errors.append(
                f'metadata.txt: version="{version_str}" n\'est pas strictement '
                f'supérieure à celle de main ("{main_version_str}")'
            )
except subprocess.CalledProcessError:
    pass  # origin/main non disponible

if errors:
    for e in errors:
        print(f'::error::{e}')
    sys.exit(1)

print(f'metadata.txt OK — version={version_str}')
