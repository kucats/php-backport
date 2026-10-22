#!/bin/sh
# Public inputs only; use inside an isolated matching-OS x86_64 builder.
set -eu
if test "$#" != 2; then echo "usage: $0 SOURCE_RPM NEW_TOPDIR" >&2; exit 2; fi
if test "$(id -u)" = 0; then echo "run as a non-root build identity" >&2; exit 2; fi
if test "$(uname -m)" != x86_64; then echo "x86_64 builder required" >&2; exit 2; fi
here=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
srpm=$(CDPATH='' cd -- "$(dirname -- "$1")" && pwd)/$(basename -- "$1")
top=$2
case "$top" in /*) ;; *) echo "TOPDIR must be absolute" >&2; exit 2;; esac
if test -e "$top"; then echo "TOPDIR already exists" >&2; exit 2; fi
printf '%s  %s\n' 'ddd0f179582dda7b9f0ef2936948e62455509a7ee651ecc24e33468a20b9b10a' "$srpm" | sha256sum -c -
rpm -K "$srpm"
mkdir -p "$top"/BUILD "$top"/RPMS "$top"/SOURCES "$top"/SPECS "$top"/SRPMS
rpm -iv --define "_topdir $top" "$srpm"
:
patch --fuzz=0 -p1 -d "$top/SPECS" < "$here/packaging/spec.patch"
cp "$here/patches/php-5.3.3-cve-2026-109618-109619.patch" "$top/SOURCES/"
# Dependency installation belongs to the container preparation phase.
# Keep GPG verification enabled, then disconnect build networks.
# Exit status alone does not prove the vendor's tests passed: retain raw logs.
exec rpmbuild -ba --define "_topdir $top" --define "dist .el6_10"  \
  --define '_smp_mflags -j1' "$top/SPECS/php.spec"
