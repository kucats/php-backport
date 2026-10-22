# PHP 8.3.36 validation

Final Rocky 10 x86_64 eight-RPM installation, NTS CLI/CGI/FPM. The vendor SPEC
uses signed official PHP 8.3.36 source; no EOL manual engine patch is applied.

- Isolated Nginx/FPM HTTP: 17/17, including 1,999 MiB upload with matching SHA-256
  and 2 MiB peak PHP memory. Signed 8.3.33 control: 16/16 (no large upload).
- Selected upstream PHPT 483: 452 PASS / 30 SKIP / 1 XFAIL / 0 FAIL / 0 WARN.
  The log and per-test statuses include skips/XFAIL without counting them as passes.
- A plain upstream static-extension control passed the nine initially disputed
  OOM tests. Final installed-RPM tests pass all nine too. Earlier failures came
  from shared-extension load order / absent CGI mbstring, not a changed EXPECT.
- Signed original eight-RPM downgrade and candidate reinstall passed in the lab,
  including configuration hash preservation and `php-fpm -t`.

The fixed PHPT harness loads DOM before xmlreader and PDO before pdo_sqlite.
Some upstream CGI tests explicitly use `-n`, which would drop the CLI's shared
mbstring load; `php-cgi-mb` supplies the same extension to those child processes.
A fresh TMPDIR avoids previous tests' session files with incompatible ownership.
Neither expected results nor upstream test bodies were changed.

Install the eight candidate RPMs in an isolated matching-OS lab, unpack the
verified upstream tar to a writable test directory, then run:

```sh
sh tests/run-selected-phpt.sh /lab/php-8.3.36 > /lab/phpt.log 2>&1
```

Paths assume execution from `php83/`. The wrapper runs `/usr/bin/php-cgi`.
The accepted test list is checked in. Dependencies needed by skipped optional
extensions are not part of this runtime's eight-package acceptance.

For HTTP, place `fixtures` at `/lab`, copy `fixture.php` into
`/lab/www/fixture.php` and `www/{parts,warn}/fixture.php`; use the supplied
Nginx/FPM/INI configuration and synthetic private state directories. Run
`python3 /lab/run_http.py --candidate --large-mib 1999 --output /lab/result.json`
inside a disposable network-disconnected container with no published ports,
agent, host bind mounts or production configuration. The runner starts/stops
its own Nginx and FPM. Use a separate signed-original container for baseline.
Reserve at least 3 GiB disk space. Do not run OOM fixtures against live services.

Build using `build/build-rpms.sh SRPM php-8.3.36.tar.xz php-8.3.36.tar.xz.asc /new/topdir`
in a dependency-prepared isolated Rocky 10 x86_64 builder, non-root, with public
signing keys trusted and the build network disconnected. A zero RPM build exit
alone is insufficient because the vendor SPEC reports, but tolerates, PHPT
failures. Preserve logs and use installed-RPM acceptance separately.

No ZTS/optional-SAPI runtime validation, sanitizer run, independent audit or
complete application UAT is claimed. These results do not accept every optional
RPM built by the SPEC.
