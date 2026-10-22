# Atomic PHP 5.4.45 / EL5 validation

The accepted candidate is the final eight-RPM installation on CentOS 5 x86_64
NTS CLI/CGI and Apache 2.2/mod_php. Apache tests passed 20/20, including the
1,999 MiB streamed upload, ordinary sessions, mbstring, multipart limits,
request-state cleanup and four injected OOM paths. OOM terminates the child
without PHP shutdown callbacks; the parent and next request recover.

The unpatched control was rebuilt from the same vendor-prepared 5.4.45 tree,
with all affected shared extensions rebuilt too. Its CLI/CGI/module files were
copied into a separate lab; its RPM database still identifies the candidate.
It is a **build-tree runtime comparison**, not an original 5.4.36 RPM control.
MySQL modules use the vendor Apache build's libmysqlclient.so.15 variant.

- Control HTTP: 20/20, early request state mask 608; candidate: 20/20, mask 0.
- Selected PHPT 349: control 344 PASS / 1 FAIL / 4 SKIP;
  candidate 336 PASS / 9 FAIL / 4 SKIP. The eight changed statuses are the
  intentionally disabled session upload-progress tests. The original
  vendor-removed `php_egg_logo_guid` failure remains. Ordinary sessions pass.
- Synthetic GD PNG output, mcrypt encrypt/decrypt, PDO SQLite, MySQL-client ABI
  and UTF-8 mbstring outputs match between control and candidate.

See `results`, `selected-tests.txt` and `results/artifact-manifest.json`.
Run the fixtures like the [PHP 5.3 lab](../../php53/tests/README.md), omitting
`--php53`. Compile `ko_lab.c` only against the matching candidate/control
headers. It is deliberately capable of causing OOM and must not be deployed.

For PHPT, use a clean TMPDIR, no scanned INI, UTC timezone and mbstring; point
TEST_PHP_EXECUTABLE / TEST_PHP_CGI_EXECUTABLE at the corresponding runtime.
The vendor SPEC does not run `%check` here; these are separate explicit tests.

## Recovery constraint on EL5

If exact old RPMs are unavailable, retain the complete original owned-file
archive, configurations, three renamed originals and SHA-256 manifest before
updating. EL5 `rpm --repackage` payload installation can fail for locally
modified config MD5s; neither ordinary reinstall nor `--nomd5` is accepted.
An isolated synthetic update/recovery test passed with original file archive
restoration and repackaged original RPMs used **only for database metadata**:
`rpm -Uvh --oldpackage --justdb --noscripts --notriggers ...`.
Keep dependency checking enabled. This requires all original headers and verified
payload/configuration archives; renamed binaries alone are insufficient.
Do not apply this to another host without its own complete recovery packet.

Optional SPEC outputs, ZTS, other distributions, all EOL vulnerabilities,
independent security review, sanitizers and complete application UAT are outside
this acceptance scope.
