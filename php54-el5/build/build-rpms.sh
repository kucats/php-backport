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
printf '%s  %s\n' '616c8247bc99f1b8127861a750fdf51ef05cfd76c98b975cd1acac5e39f59107' "$srpm" | sha256sum -c -
rpm -K "$srpm"
mkdir -p "$top"/BUILD "$top"/RPMS "$top"/SOURCES "$top"/SPECS "$top"/SRPMS
rpm -iv --define "_topdir $top" "$srpm"
cp "$top/SPECS/php-art.spec" "$top/SPECS/php.spec"
patch --fuzz=0 -p1 -d "$top/SPECS" < "$here/packaging/spec.patch"
cp "$here/patches/php-5.4.45-el5-cve-2026-109618-109619.patch" "$top/SOURCES/"
# Dependency installation belongs to the container preparation phase.
# Keep GPG verification enabled, then disconnect build networks.
# Exit status alone does not prove the vendor's tests passed: retain raw logs.
exec rpmbuild -ba --define "_topdir $top" --define "dist .el5" --define "rhel 5" --define "runselftest 0" \
  --define '_smp_mflags -j1' "$top/SPECS/php.spec"
