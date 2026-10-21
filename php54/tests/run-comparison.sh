#!/bin/sh
# Run run_http.py against the original and the rebuilt RPMs, each in its own
# disposable container without network. Synthetic fixture data only.
set -eu

script_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
context=${PHP_BACKPORT_DOCKER_CONTEXT:?Set PHP_BACKPORT_DOCKER_CONTEXT to an isolated lab context}
image=${PHP_BACKPORT_IMAGE:?Set PHP_BACKPORT_IMAGE to the image kept by build-rpms.sh}
rpm_dir=${PHP_BACKPORT_RPM_DIR:?Set PHP_BACKPORT_RPM_DIR to the build output directory}
output=${PHP_BACKPORT_RESULT_DIR:?Set PHP_BACKPORT_RESULT_DIR to a new result directory}
large_mib=${PHP_BACKPORT_LARGE_MIB:-0}
release=5.4.16-48.el7.kucsec1
if [ -e "$output" ]; then
    printf 'Refusing to overwrite existing output: %s\n' "$output" >&2
    exit 1
fi
mkdir -p "$output"
container="php54-backport-test-$$"
cleanup() {
    docker --context "$context" rm -f "$container" >/dev/null 2>&1 || true
}
trap cleanup EXIT HUP INT TERM

run() {
    mode=$1
    docker --context "$context" create --platform linux/amd64 \
        --name "$container" --network none --memory 1g --pids-limit 256 \
        "$image" sleep infinity >/dev/null
    docker --context "$context" start "$container" >/dev/null
    docker --context "$context" exec "$container" \
        mkdir -p /lab/www/parts /lab/www/warn /lab/www/probe /lab/state /lab/rpms
    for f in httpd.conf ko_lab.c run_http.py; do
        docker --context "$context" cp "$script_dir/$f" "$container:/lab/$f"
    done
    for d in . parts warn probe; do
        docker --context "$context" cp "$script_dir/fixture.php" "$container:/lab/www/$d/fixture.php"
    done
    flag=
    if [ "$mode" = candidate ]; then
        flag=--candidate
        for p in php php-common php-cli php-mbstring php-devel; do
            docker --context "$context" cp \
                "$rpm_dir/RPMS/x86_64/$p-$release.x86_64.rpm" "$container:/lab/rpms/"
        done
        docker --context "$context" exec "$container" sh -c 'rpm -Uvh /lab/rpms/*.rpm'
        docker --context "$context" exec "$container" sh -c \
            "rpm -q php php-common php-cli php-mbstring php-devel | grep -c '$release' | grep -qx 5"
    fi
    docker --context "$context" exec "$container" sh -c '
        set -e
        php -v
        php -r "exit(function_exists(\"mb_strlen\") ? 0 : 1);"
        gcc -shared -fPIC $(php-config --includes) /lab/ko_lab.c -o /lab/ko_lab.so
        echo extension=/lab/ko_lab.so > /etc/php.d/99-ko-lab.ini
        httpd -t -f /lab/httpd.conf'
    status=0
    docker --context "$context" exec "$container" python3 /lab/run_http.py \
        $flag --large-mib "$large_mib" --output "/lab/state/$mode.json" || status=$?
    docker --context "$context" cp "$container:/lab/state/$mode.json" "$output/$mode.json" || true
    docker --context "$context" cp "$container:/lab/state/error.log" "$output/$mode-error.log" || true
    docker --context "$context" rm -f "$container" >/dev/null
    return "$status"
}

failed=0
run baseline || failed=1
run candidate || failed=1
exit "$failed"
