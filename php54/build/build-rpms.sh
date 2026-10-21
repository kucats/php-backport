#!/bin/sh
# Public interpreter sources only; use an isolated Docker context.
set -eu

script_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
series_dir=$(CDPATH='' cd -- "$script_dir/.." && pwd)
context=${PHP_BACKPORT_DOCKER_CONTEXT:?Set PHP_BACKPORT_DOCKER_CONTEXT to an isolated lab context}
output=${PHP_BACKPORT_OUTPUT_DIR:-"$series_dir/out"}
if [ -e "$output" ]; then
    printf 'Refusing to overwrite existing output: %s\n' "$output" >&2
    exit 1
fi
mkdir -p "$output"
output=$(CDPATH='' cd -- "$output" && pwd)
work=$(mktemp -d)
container="php54-backport-build-$$"
# PHP_BACKPORT_KEEP_IMAGE=<tag> keeps the builder image (original RPMs +
# php-devel) for the isolated comparison in tests/run-comparison.sh.
keep_image=${PHP_BACKPORT_KEEP_IMAGE:-}
image=${keep_image:-"php54-backport-builder:local-$$"}
cleanup() {
    docker --context "$context" rm -f "$container" >/dev/null 2>&1 || true
    if [ -z "$keep_image" ]; then
        docker --context "$context" image rm "$image" >/dev/null 2>&1 || true
    fi
    rm -rf "$work"
}
trap cleanup EXIT HUP INT TERM

srpm=php-5.4.16-48.el7.src.rpm
curl --fail --location --silent --show-error \
    "https://vault.centos.org/7.9.2009/os/Source/SPackages/$srpm" \
    --output "$work/$srpm"
python3 - "$work/$srpm" <<'PY'
import hashlib, pathlib, sys
p = pathlib.Path(sys.argv[1])
expected = '84cfffd22e99e87e1f25f5e69f74108d762bab94759ef62079092382c89c06f1'
if hashlib.sha256(p.read_bytes()).hexdigest() != expected:
    raise SystemExit('Source RPM checksum mismatch')
PY
cp "$script_dir/Dockerfile" "$script_dir/CentOS-Vault.repo" "$work/"
docker --context "$context" build --platform linux/amd64 -t "$image" "$work"
docker --context "$context" create --platform linux/amd64 \
    --name "$container" --network none --memory 3g --pids-limit 512 \
    "$image" sleep infinity >/dev/null
docker --context "$context" start "$container" >/dev/null
docker --context "$context" cp \
    "$container:/build/rpmbuild/SPECS/php.spec" "$work/original.spec"
python3 "$script_dir/make_spec.py" "$work/original.spec" "$work/php.spec"
docker --context "$context" cp "$work/php.spec" \
    "$container:/build/rpmbuild/SPECS/php.spec"
docker --context "$context" cp \
    "$series_dir/patches/php-5.4.16-cve-2026-109618-109619.patch" \
    "$container:/build/rpmbuild/SOURCES/php-5.4.16-cve-2026-109618-109619.patch"
docker --context "$context" exec "$container" chown -R builder:builder /build
status=0
docker --context "$context" exec -u builder "$container" sh -c \
    'rpmbuild -ba --define "_topdir /build/rpmbuild" --define "runselftest 0" --define "_smp_mflags -j3" /build/rpmbuild/SPECS/php.spec > /build/rpmbuild.log 2>&1' \
    || status=$?
docker --context "$context" cp "$container:/build/rpmbuild.log" "$output/build.log"
if [ "$status" -ne 0 ]; then
    printf 'Build failed; see %s/build.log\n' "$output" >&2
    exit "$status"
fi
docker --context "$context" cp "$container:/build/rpmbuild/RPMS" "$output/"
docker --context "$context" cp "$container:/build/rpmbuild/SRPMS" "$output/"
printf 'RPMs and log: %s\n' "$output"
printf 'Full vendor self-tests were disabled; run isolated acceptance separately.\n'
