#!/bin/sh
# Execute inside a dependency-prepared, isolated Rocky 10 x86_64 builder.
set -eu
if [ "$#" != 4 ]; then
    echo "usage: $0 ROCKY_SOURCE_RPM PHP_TAR_XZ PHP_TAR_ASC NEW_TOPDIR" >&2
    exit 2
fi
if [ "$(id -u)" = 0 ] || [ "$(uname -m)" != x86_64 ]; then
    echo "non-root x86_64 builder required" >&2
    exit 2
fi
here=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
srpm=$(CDPATH='' cd -- "$(dirname -- "$1")" && pwd)/$(basename -- "$1")
tarball=$(CDPATH='' cd -- "$(dirname -- "$2")" && pwd)/$(basename -- "$2")
signature=$(CDPATH='' cd -- "$(dirname -- "$3")" && pwd)/$(basename -- "$3")
top=$4
case "$top" in /*) ;; *) echo "TOPDIR must be absolute" >&2; exit 2;; esac
if [ -e "$top" ]; then echo "TOPDIR already exists" >&2; exit 2; fi
printf '%s  %s\n' d4350267bdedbe046d2f3cafe054be9b0ddc7077136f0be76a3910da95ea8e34 "$srpm" | sha256sum -c -
printf '%s  %s\n' dd54693aa334c5c4d72e9aee96b082c2473750a18a6c1d105789c93a3b1692fd "$tarball" | sha256sum -c -
rpm -K "$srpm"
mkdir -p "$top"/BUILD "$top"/RPMS "$top"/SOURCES "$top"/SPECS "$top"/SRPMS
rpm -iv --define "_topdir $top" "$srpm"
gpgv --keyring "$top/SOURCES/php-keyring.gpg" "$signature" "$tarball"
cp "$tarball" "$top/SOURCES/php-8.3.36.tar.xz"
cp "$signature" "$top/SOURCES/php-8.3.36.tar.xz.asc"
patch --fuzz=0 -p1 -d "$top/SPECS" < "$here/packaging/spec.patch"
# The vendor SPEC records tests but does not fail the build on every test failure.
# Inspect raw logs and run the separate installed-RPM acceptance suite.
exec rpmbuild -ba --define "_topdir $top" --define 'dist .el10_2' \
    --define '_smp_mflags -j2' "$top/SPECS/php.spec"
