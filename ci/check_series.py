#!/usr/bin/env python3
"""Offline consistency checks for every series directory.

- the series is listed in the root README table and has its own README.md;
- every tests/results/*.json parses, and stored runner results are all PASS;
- tests/results/artifact-manifest.json's patch_sha256 matches the patch in
  patches/ (the manifest records the hashes of the tested build);
- tests/compare_phpt.py, when present, still reproduces its committed output
  (the workflow checks `git diff` afterwards).
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from series import ROOT, all_series

errors = []


def fail(series, message):
    errors.append(f'{series}: {message}')
    print(f'::error::{series}: {message}')


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(name):
    base = ROOT / name
    root_readme = (ROOT / 'README.md').read_text()
    if f'({name}/)' not in root_readme:
        fail(name, 'not listed in the root README table')
    if not (base / 'README.md').is_file():
        fail(name, 'missing README.md')

    results = base / 'tests' / 'results'
    for path in sorted(results.glob('*.json')):
        try:
            data = json.loads(path.read_text())
        except ValueError as e:
            fail(name, f'{path.relative_to(ROOT)} is not valid JSON: {e}')
            continue
        if isinstance(data, dict) and {'passed', 'total', 'tests'} <= data.keys():
            failed = [t['name'] for t in data['tests'] if not t.get('pass')]
            if data['passed'] != data['total'] or failed:
                fail(name, f'{path.relative_to(ROOT)}: {data["passed"]}/{data["total"]} {failed}')
            else:
                print(f'{path.relative_to(ROOT)}: {data["passed"]}/{data["total"]}')

    manifest_path = results / 'artifact-manifest.json'
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text())
        patches = {sha256(p): p.name for p in (base / 'patches').glob('*.patch')}
        expected = manifest.get('patch_sha256')
        if expected and expected not in patches:
            fail(name, f'no patch in patches/ matches manifest patch_sha256 {expected}')
        elif expected:
            print(f'{name}/patches/{patches[expected]}: matches artifact manifest')

    compare = base / 'tests' / 'compare_phpt.py'
    if compare.is_file():
        run = subprocess.run([sys.executable, str(compare)], cwd=ROOT,
                             capture_output=True, text=True)
        if run.returncode:
            fail(name, f'compare_phpt.py failed:\n{run.stdout}{run.stderr}')
        else:
            print(f'{compare.relative_to(ROOT)}: comparison_pass')


def main():
    names = all_series()
    if not names:
        fail('repo', 'no series directories found')
    for name in names:
        check(name)
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
