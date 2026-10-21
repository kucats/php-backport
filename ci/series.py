#!/usr/bin/env python3
"""Discover version series directories (php54/, php56/, php74/, ...).

Usage:
  series.py                         every series, as a JSON list
  series.py --buildable             only series with a CI build entry point
  series.py --buildable --changed-from <git-rev>
                                    buildable series touched since <git-rev>;
                                    all of them if shared CI files changed
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
SERIES_RE = re.compile(r'^php\d+$')
# A series joins the build matrix by providing both entry points.
BUILD_ENTRY = ('build/build-rpms.sh', 'tests/run-comparison.sh')
SHARED_PREFIXES = ('ci/', '.github/workflows/build.yml')


def all_series():
    return sorted(p.name for p in ROOT.iterdir()
                  if p.is_dir() and SERIES_RE.match(p.name))


def buildable(name):
    return all((ROOT / name / entry).is_file() for entry in BUILD_ENTRY)


def changed_files(rev):
    out = subprocess.run(['git', 'diff', '--name-only', rev, 'HEAD'], cwd=ROOT,
                         check=True, capture_output=True, text=True).stdout
    return [line for line in out.splitlines() if line]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--buildable', action='store_true')
    parser.add_argument('--changed-from')
    args = parser.parse_args()
    names = all_series()
    if args.buildable:
        names = [n for n in names if buildable(n)]
    if args.changed_from:
        files = changed_files(args.changed_from)
        if not any(f.startswith(SHARED_PREFIXES) for f in files):
            names = [n for n in names if any(f.startswith(n + '/') for f in files)]
    json.dump(names, sys.stdout)
    print()


if __name__ == '__main__':
    main()
