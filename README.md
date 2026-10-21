# EOL interpreter security backports

PHP のバージョン系列ごとに、セキュリティ修正・再ビルド手順・検証結果を管理します。

| ディレクトリ | 対象ソース | 修正 | 状態 |
|---|---|---|---|
| [php54/](php54/) | CentOS 7 `php-5.4.16-48.el7.src.rpm` | CVE-2026-109618 / CVE-2026-109619 | 手動バックポート、RPM ビルド・隔離 Apache 比較済み |

現在の対象は PHP 5.4 のみです。追加系列では `php55/`、`php56/`、`php74/`
のように分け、各ディレクトリに適用元・パッチ・ビルド方法・検証範囲を記録します。

これはコミュニティーの緊急バックポート候補です。PHP プロジェクトや CentOS の
公式更新ではありません。対象ソースと検証範囲を確認して利用してください。
EOL ランタイムに存在する他の脆弱性まで解消したという保証はありません。

このリポジトリには公開インタープリター由来の差分と合成試験のみを置きます。
本番アプリケーション、認証情報、秘密鍵、実利用者データ、環境固有の運用ログは含めません。

## CI

| ワークフロー | 内容 |
|---|---|
| `ci` | 全系列のシェル/Python 構文、保存済み結果 JSON、パッチと manifest の SHA-256、PHPT 比較の再現 |
| `build` | 変更のあった系列を公開ソースパッケージから再ビルドし、ネットワークなしのコンテナで修正前/修正後を比較 |
| `release-verify` | 公開 Release の全アセットを `SHA256SUMS`・`release-manifest.json`・GitHub の digest・`source_commit` 時点のパッチ・検証済み manifest と照合（Release 公開時と毎週） |

CI の再ビルドはリリースバイナリーの再現ではありません（ビルド時刻などで RPM ハッシュは変わります）。
配布物の同一性は `release-verify` が確認します。

新しい系列 `phpXX/` は次の規約に従うと自動で CI 対象になります（`ci/series.py`）。

- 上の表に `[phpXX/](phpXX/)` として掲載し、`phpXX/README.md` を置く。
- パッチは `phpXX/patches/*.patch`、試験結果は `phpXX/tests/results/*.json`。
  `passed`/`total`/`tests` を持つ結果は全件 PASS であること。
  `artifact-manifest.json` の `patch_sha256` は `patches/` 内のパッチと一致すること。
- `phpXX/build/build-rpms.sh` と `phpXX/tests/run-comparison.sh` があれば `build` の対象。
  環境変数は php54 と同じ（`PHP_BACKPORT_DOCKER_CONTEXT`、`PHP_BACKPORT_OUTPUT_DIR`、
  `PHP_BACKPORT_KEEP_IMAGE`、`PHP_BACKPORT_IMAGE`、`PHP_BACKPORT_RPM_DIR`、`PHP_BACKPORT_RESULT_DIR`）。
- Release タグは `phpXX-<version-release>`。アセットに `SHA256SUMS` と、
  `series`・`version_release`・`source_commit`・`files`（`sha256`/`bytes`/`kind`）を持つ
  `release-manifest.json` を添付する。

## Attribution

This product includes PHP software, freely available from
<http://www.php.net/software/>.

This product includes the Zend Engine, freely available at
<http://www.zend.com>. The Zend Engine is freely available at
<http://www.zend.com>.

元ソース由来のコードには [PHP License 3.01](LICENSES/PHP-3.01.txt) と
[Zend Engine License 2.00](LICENSES/Zend-2.00.txt) が適用されます。
このリポジトリは元プロジェクトによる推奨・承認を表すものではありません。
