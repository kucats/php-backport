#!/bin/sh
# Run only in a disposable lab with the accepted RPMs installed.
set -eu
if [ "$#" != 1 ]; then echo "usage: $0 PHP_8_3_36_SOURCE_DIRECTORY" >&2; exit 2; fi
here=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
source_dir=$1
TMPDIR=$(mktemp -d /tmp/php83-phpt.XXXXXX)
export TMPDIR
export NO_INTERACTION=1 REPORT_EXIT_STATUS=1 SKIP_ONLINE_TESTS=1
export TEST_PHP_EXECUTABLE=/usr/bin/php TEST_PHP_CGI_EXECUTABLE="$here/php-cgi-mb"
cd "$source_dir"
# DOM must load before xmlreader; keep PDO before pdo_sqlite too.
exec php -n run-tests.php -q -n -d date.timezone=UTC \
    -d extension_dir=/usr/lib64/php/modules -d extension=mbstring.so \
    -d extension=pdo.so -d extension=pdo_sqlite.so -d extension=xml.so \
    -d extension=dom.so -d extension=xmlreader.so -d extension=simplexml.so \
    -r "$here/selected-tests.txt"
