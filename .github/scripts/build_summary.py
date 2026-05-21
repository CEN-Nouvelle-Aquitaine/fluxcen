#!/usr/bin/env python3
"""Builds the GitHub Actions Summary for the Quality workflow.

Reads:
- Step outcomes from env vars named OUTCOME_<step_id> (set by the workflow).
- Log files from $LOG_DIR/<step_id>.log.

Emits Markdown to stdout (typically redirected to $GITHUB_STEP_SUMMARY).

To add a new check step:
1. Add the step in quality.yml with `id:` matching a value in STEPS below.
2. Pipe its output to `$LOG_DIR/<step_id>.log` via `tee`.
3. Add OUTCOME_<step_id> in the Summary step env mapping.
4. Append `(<step_id>, '<human label>')` to STEPS.
"""
import os
import re
import sys
from collections import Counter
from pathlib import Path

# Ordered list of (step_id, human_label) — single source of truth.
STEPS = [
    ('pylint', 'Lint — pylint'),
    ('metadata', 'Metadata'),
    ('yaml_check', 'YAML'),
    ('gitleaks', 'Security — gitleaks'),
    ('resources', 'Resources'),
]

STATUS_LABELS = {
    'success': 'OK',
    'failure': 'Problèmes détectés',
    'skipped': 'Ignoré',
    'cancelled': 'Annulé',
}

SEVERITY_LABELS = {
    'E': 'Errors',
    'W': 'Warnings',
    'R': 'Refactor',
    'C': 'Convention',
    'I': 'Info',
    'F': 'Fatal',
}

LOG_DIR = Path(os.environ.get('LOG_DIR', '/tmp/quality'))

# Pylint output line: `path/file.py:25:0: C0301: msg (rule-name)`
PYLINT_MSG_RE = re.compile(r':\s*([CRWEIF])\d+:\s*.+\((.+?)\)\s*$', re.MULTILINE)
PYLINT_SCORE_RE = re.compile(r'rated at (-?\d+(?:\.\d+)?)/10')


def status(outcome):
    return STATUS_LABELS.get(outcome, outcome or '—')


def parse_pylint(log_text):
    severities = Counter()
    rules = Counter()
    for match in PYLINT_MSG_RE.finditer(log_text):
        severities[match.group(1)] += 1
        rules[match.group(2)] += 1
    score_match = PYLINT_SCORE_RE.search(log_text)
    score = score_match.group(1) if score_match else None
    return severities, rules.most_common(5), score


def render_table(out):
    out.write('## État des lieux qualité\n\n')
    out.write('| Étape | Statut |\n')
    out.write('|---|---|\n')
    for step_id, label in STEPS:
        outcome = os.environ.get(f'OUTCOME_{step_id}', '')
        out.write(f'| {label} | {status(outcome)} |\n')
    out.write('\n')


def render_pylint_summary(out, log_text):
    severities, top_rules, score = parse_pylint(log_text)
    if not severities and not score:
        out.write('_Aucune violation détectée._\n\n')
        return
    if score:
        out.write(f'**Score** : {score}/10  \n')
    if severities:
        parts = [f'{SEVERITY_LABELS.get(k, k)} ({k}) : {v}'
                 for k, v in sorted(severities.items())]
        out.write('**Violations** : ' + ', '.join(parts) + '\n\n')
    if top_rules:
        out.write('**Top règles déclenchées** :\n')
        for rule, count in top_rules:
            out.write(f'- `{rule}` × {count}\n')
        out.write('\n')


def render_details(out, step_id, label):
    log_path = LOG_DIR / f'{step_id}.log'
    out.write(f'<details><summary>Détails — {label}</summary>\n\n')
    if not log_path.exists():
        out.write('_Aucun log produit._\n\n</details>\n\n')
        return
    log_text = log_path.read_text()
    if step_id == 'pylint':
        render_pylint_summary(out, log_text)
    out.write('```\n')
    out.write(log_text)
    if not log_text.endswith('\n'):
        out.write('\n')
    out.write('```\n\n</details>\n\n')


def main():
    out = sys.stdout
    render_table(out)
    for step_id, label in STEPS:
        render_details(out, step_id, label)


if __name__ == '__main__':
    main()
