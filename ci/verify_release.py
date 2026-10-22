#!/usr/bin/env python3
"""Verify published GitHub Releases against their checksums and this repo.

Release tags are named <series>-<version_release> (e.g. php54-5.4.16-48.el7.kucsec1)
and carry SHA256SUMS and release-manifest.json. For each release this checks:

- every asset's SHA-256 matches SHA256SUMS, release-manifest.json and the
  digest GitHub reports, and no asset is missing from or extra to the lists;
- the manifest's series/version_release agree with the tag, RPM headers
  agree with the file names (when `rpm` is installed);
- patch assets are byte-identical to <series>/patches/ at source_commit;
- when <series>/tests/results/artifact-manifest.json describes the same
  release, the tested RPM hashes recorded there equal the published ones;
- every release tag linked from a series README exists.

Usage: verify_release.py [--repo owner/name] [TAG ...]   (default: all releases)
Needs the `gh` CLI with a token, and full git history for source_commit.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from series import ROOT, all_series

TAG_RE = re.compile(r'^(php\d+(?:-el\d+)?)-(.+)$')
LINK_RE = re.compile(r'releases/tag/([A-Za-z0-9._-]+)')
CONTROL = {'SHA256SUMS', 'release-manifest.json'}
errors = []


def fail(tag, message):
    errors.append(f'{tag}: {message}')
    print(f'::error::{tag}: {message}')


def note(tag, message):
    print(f'{tag}: {message}')


def gh_json(*args):
    out = subprocess.run(['gh', *args], check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def git_show(commit, path):
    run = subprocess.run(['git', 'show', f'{commit}:{path}'], cwd=ROOT, capture_output=True)
    return run.stdout if run.returncode == 0 else None


def read_sums(path):
    sums = {}
    for line in path.read_text().splitlines():
        digest, name = line.split(None, 1)
        sums[name.lstrip('*')] = digest
    return sums


def verify(repo, release):
    tag = release['tag_name']
    match = TAG_RE.match(tag)
    if not match:
        fail(tag, 'tag is not <series>-<version_release>')
        return
    series, version_release = match.groups()
    if not (ROOT / series).is_dir():
        fail(tag, f'no {series}/ directory in this repository')
        return
    assets = {a['name']: a for a in release['assets']}
    missing_control = CONTROL - assets.keys()
    if missing_control:
        fail(tag, f'missing {sorted(missing_control)}')
        return

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        subprocess.run(['gh', 'release', 'download', tag, '--repo', repo, '--dir', str(tmp)],
                       check=True)
        actual = {name: sha256(tmp / name) for name in assets}
        for name, asset in assets.items():
            digest = asset.get('digest') or ''
            if digest and digest != 'sha256:' + actual[name]:
                fail(tag, f'{name}: GitHub digest {digest} != downloaded sha256:{actual[name]}')
            if (tmp / name).stat().st_size != asset['size']:
                fail(tag, f'{name}: size differs from GitHub asset metadata')

        payload = set(assets) - CONTROL
        sums = read_sums(tmp / 'SHA256SUMS')
        for name in sorted(set(sums) | payload | {'release-manifest.json'}):
            if name not in sums:
                fail(tag, f'{name}: not listed in SHA256SUMS')
            elif name not in actual:
                fail(tag, f'{name}: listed in SHA256SUMS but not attached')
            elif sums[name] != actual[name]:
                fail(tag, f'{name}: SHA256SUMS {sums[name]} != actual {actual[name]}')

        manifest = json.loads((tmp / 'release-manifest.json').read_text())
        if manifest.get('series') != series:
            fail(tag, f'manifest series {manifest.get("series")!r} != {series!r}')
        if manifest.get('version_release') != version_release:
            fail(tag, f'manifest version_release {manifest.get("version_release")!r} != {version_release!r}')
        files = manifest.get('files', {})
        if set(files) != payload:
            fail(tag, f'manifest files differ from assets: '
                      f'only in manifest {sorted(set(files) - payload)}, '
                      f'only attached {sorted(payload - set(files))}')
        for name, entry in files.items():
            if name in actual and (entry['sha256'] != actual[name]
                                   or entry['bytes'] != (tmp / name).stat().st_size):
                fail(tag, f'{name}: release-manifest.json hash/size mismatch')

        if shutil.which('rpm'):
            for name in sorted(n for n in payload if n.endswith('.rpm')):
                nvra = subprocess.run(
                    ['rpm', '-qp', '--nosignature', '--nodigest', '--qf',
                     '%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH}', str(tmp / name)],
                    check=True, capture_output=True, text=True).stdout
                if name.endswith('.src.rpm'):
                    nvra = nvra.rsplit('.', 1)[0] + '.src'
                if nvra + '.rpm' != name:
                    fail(tag, f'{name}: RPM header says {nvra}')
                if version_release not in nvra:
                    fail(tag, f'{name}: release {version_release} not in RPM header')

        commit = manifest.get('source_commit')
        if not commit or subprocess.run(['git', 'cat-file', '-e', f'{commit}^{{commit}}'],
                                        cwd=ROOT).returncode:
            fail(tag, f'source_commit {commit!r} is not in this repository')
            commit = None
        for name, entry in files.items():
            if entry.get('kind') != 'patch' or name not in actual:
                continue
            blob = git_show(commit, f'{series}/patches/{name}') if commit else None
            if blob is None:
                fail(tag, f'{name}: not found in {series}/patches/ at source_commit')
            elif hashlib.sha256(blob).hexdigest() != actual[name]:
                fail(tag, f'{name}: differs from {series}/patches/ at source_commit')

        local = ROOT / series / 'tests' / 'results' / 'artifact-manifest.json'
        if local.is_file():
            tested = json.loads(local.read_text())
            if tested.get('candidate_release') == version_release:
                for path, entry in tested.get('files', {}).items():
                    if path.startswith('original-'):
                        continue
                    name = Path(path).name
                    if name not in actual:
                        fail(tag, f'tested artifact {name} is not attached')
                    elif entry['sha256'] != actual[name]:
                        fail(tag, f'tested {name} {entry["sha256"]} != published {actual[name]}')
                if tested.get('patch_sha256') not in {actual[n] for n in payload if n.endswith('.patch')}:
                    fail(tag, 'tested patch_sha256 is not among the published patches')
                note(tag, f'matches {local.relative_to(ROOT)}')
    note(tag, f'{len(payload)} assets verified')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', default='kucats/php-backport')
    parser.add_argument('tags', nargs='*')
    args = parser.parse_args()
    releases = gh_json('api', '--paginate', '--slurp', f'repos/{args.repo}/releases')
    releases = [r for page in releases for r in page if not r.get('draft')]
    by_tag = {r['tag_name']: r for r in releases}

    for series in all_series():
        readme = ROOT / series / 'README.md'
        text = readme.read_text() if readme.is_file() else ''
        for linked in sorted(set(LINK_RE.findall(text))):
            if linked not in by_tag:
                fail(linked, f'linked from {series}/README.md but no such release')

    tags = args.tags or sorted(by_tag)
    for tag in tags:
        if tag not in by_tag:
            fail(tag, 'release not found')
            continue
        verify(args.repo, by_tag[tag])
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
