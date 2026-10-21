#!/usr/bin/env python3
"""Modify the public CentOS 7 source spec; fail on an unexpected baseline."""
import pathlib
import sys

source, target = map(pathlib.Path, sys.argv[1:])
text = source.read_text()
patch = 'php-5.4.16-cve-2026-109618-109619.patch'
anchors = {
    'Release: 48%{?dist}': 'Release: 48%{?dist}.kucsec1',
    'Patch167: php-5.4.16-CVE-2019-11043.patch':
        'Patch167: php-5.4.16-CVE-2019-11043.patch\nPatch999: ' + patch,
    '%patch167 -p1 -b .cve11043':
        '%patch167 -p1 -b .cve11043\n%patch999 -p1 -b .kucsec1',
}
for old, new in anchors.items():
    if text.count(old) != 1:
        raise SystemExit('Unexpected spec anchor: ' + old)
    text = text.replace(old, new)
target.write_text(text)
