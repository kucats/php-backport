# PHP 5.4.16 candidate security backport

This is a manually adapted **candidate**, not an upstream or vendor release.
It applies after all 95 selected patches from the exact CentOS 7 source RPM
`php-5.4.16-48.el7.src.rpm`. Keep that patch sequence and package spec intact.
Do not apply it directly to an unrelated PHP tree or a running interpreter.

The source is derived from PHP, under the PHP/Zend licenses retained by the
original source package. Upstream reference: PHP's
[7.4 emergency commit 712e60f](https://github.com/php/php-src/commit/712e60f9edfd03f0960fc4fc3c2c375f42b90aa2),
for [OOM corruption](https://github.com/php/php-src/security/advisories/GHSA-w8hw-w9fx-j79w)
and [stale request state](https://github.com/php/php-src/security/advisories/GHSA-6wmf-4rv5-p3rp).

## Semantic mapping

| Upstream file/family | PHP 5.4 candidate handling |
|---|---|
| `Zend/zend_alloc.c`, `.h` | Allocation panic, heap memory-limit/storage failure and safe-size overflow use a common fixed-buffer error reporter followed by `_exit(1)`. Persistent malloc/realloc also use the fatal helper. `_estrndup` uses safe-size arithmetic. |
| `Zend/zend_multiply.h` | The equivalent 5.4 `safe_address` implementation is in `zend_alloc.c`; all four platform branches use the helper. There is no corresponding 5.4 header. |
| `Zend/zend_strtod.c` | Both Balloc allocation failures use the fatal helper. |
| `Zend/zend_execute_API.c` | Clear handler pointers/stacks, exceptions, error mode, object buckets and active execution pointers outside bailout-protected cleanup blocks. |
| `Zend/zend_llist.c` | Destroyed lists reset head/tail as well as count, covering SAPI header lists. |
| `main/main.c` | Reset superglobals and module activation after both ordinary and hook request shutdown; register the new per-directory/system multipart part limit. |
| `main/SAPI.c` | Clear freed authentication/content/current-user strings, plus 5.4-owned post/raw data, upload hash and callback pointers. |
| `ext/session/session.c` | Preserve the chained original RFC1867 callback return value, then unconditionally skip PHP's early session progress processing. Ordinary `session_start()` remains available. |
| `main/rfc1867.c` | Keep Content-Disposition/Content-Type only, ignore duplicate retained headers, count total parts including empty file controls, use size_t for substring lengths. Default part limit is max_input_vars + max_file_uploads with saturated addition. |
| `Zend/zend_vm_def.h`, generated `zend_vm_execute.h` | 5.4 CONCAT dispatch calls `concat_function`; ADD_STRING calls `add_string_to_string`. Overflow checks are added to these shared helpers in `Zend/zend_operators.c`, covering VM specializations without generated-code edits. |
| `Zend/zend_API.h`, `zend_hash.c`, `zend_hash.h`, `zend_types.h`, `main/php_variables.c` singleton/packed-hash changes | 5.4 has a different pointer/bucket array representation, no packed hash or modern SIMD hash-reset path. Initial bucket allocation is lazy; `pecalloc` uses safe allocation arithmetic. No modern singleton helper is copied. Nested-input/OOM behavior must be tested on this implementation. |
| `Zend/zend_hash.c` modern fatal size checks | 5.4 has no corresponding modern error sites: initialization clamps uint capacity; resize caps doubling and returns failure. Memory failures route through the adapted allocator. The x86_64 target's bucket-pointer multiplication fits size_t for uint capacity. This mapping does not validate 32-bit builds. |

The upstream emergency strategy deliberately terminates the worker on OOM.
It skips PHP shutdown callbacks, destructors and buffered cleanup. Apache
prefork replacement and parent survival require validation. An application
write interrupted before `_exit` can leave partial state; this patch does not
make legacy registry writes transactional. PHP upload-progress data is disabled
even if its INI flag says enabled.

See the [isolated lab](../tests/README.md)
for fixtures and reproduction. No production rollout is authorized by this
README. No claim is made that PHP 5.4 or CentOS 7 becomes fully supported or
free of other vulnerabilities.
