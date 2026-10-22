# PHP 5.3 validation

Linux x86_64 NTS CLI/CGI and Apache 2.2/mod_php only. No ZTS runtime acceptance,
sanitizer run, independent review, or complete application UAT is claimed.

- `results/candidate-http.json`: final eight RPMs installed in an isolated
  CentOS 6 lab; 20/20 including a 1,999 MiB streaming upload with matching SHA-256.
- `results/baseline-http.json`: signed original 5.3.3-50.el6_10 RPMs, 19/19.
- The same 271 vendor-prepared PHPTs on build-tree CLI/CGI give
  261 PASS / 9 FAIL / 1 SKIP before and after. All statuses match. The nine
  existing failures are session encoding expectations and vendor-removed
  `php_egg_logo_guid`; they remain failures, not waived passes.
- Signed original eight RPMs were reinstalled with `--oldpackage` in the lab,
  checked with `rpm -V` and `httpd -t`, then upgraded to the candidate again.

`results/artifact-manifest.json` identifies the eight accepted packages and
manual patch. The SPEC also builds optional packages; these results do not
accept every output or another ABI/distribution.

Prepare dependencies in a disposable CentOS 6 x86_64 container with signature
checking enabled, no host mounts or SSH agent. Build as a non-root identity
using `../build/build-rpms.sh SRPM /new/topdir`. Disconnect network after public
dependencies are prepared. Preserve full build logs: a successful vendor RPM
build alone does not prove all PHPTs passed.

For the Apache comparison, copy `fixtures` into `/lab`, copy `fixture.php` to
`/lab/www/fixture.php` and each `www/{parts,warn,probe}/fixture.php`, create
private `state/{sessions,uploads}` directories for Apache UID/GID 48, and build
`ko_lab.c` using the matching `php-devel` headers. Load it only in this lab.
Use the supplied isolated httpd/php configuration, not production settings.

The runner needs modern Python 3 and Podman on the lab host. Mount only the
container's storage root via `podman mount`, obtain its PID with `podman inspect`,
and enter **only its network namespace**:

```sh
nsenter --net="/proc/$CONTAINER_PID/ns/net" python3 /path/to/run_http_podman.py \
  --php53 --container "$LAB_CONTAINER" --rootfs "$CONTAINER_ROOTFS" \
  --output /private/lab/baseline.json
# Same invocation for the candidate with --candidate --large-mib 1999.
```

The runner starts/stops Apache through `podman exec`. It has a fixed loopback
endpoint; never use host PID kill commands with container PID numbers. Reserve
at least 3 GiB temporary disk space. No published ports or production data.

The selected PHPT list is `selected-tests.txt`. Run the vendor `run-tests.php`
from the vendor-prepared tree with clean temporary directories, CLI/CGI paths
pointing at the corresponding build, `-n`, UTC timezone and mbstring loaded.
The checked-in logs and comparison record the exact observed results.
