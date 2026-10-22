# PHP security maintenance

PHP のバージョン系列ごとに、セキュリティ修正・再ビルド手順・検証結果を管理します。

| ディレクトリ | 対象ソース | 修正 | 状態 |
|---|---|---|---|
| [php54/](php54/) | CentOS 7 `php-5.4.16-48.el7.src.rpm` | CVE-2026-109618 / CVE-2026-109619 | 手動バックポート、RPM ビルド・隔離 Apache 比較済み |
| [php53/](php53/) | CentOS 6 `php-5.3.3-50.el6_10.src.rpm` | CVE-2026-109618 / CVE-2026-109619 | 手動移植、最終 RPM の Apache 試験 20/20 |
| [php54-el5/](php54-el5/) | Atomic `php-5.4.45-56.art.src.rpm` / CentOS 5 | 同上 | 5.4.36 から同系列更新＋手動移植、Apache 試験 20/20 |
| [php83/](php83/) | Rocky 10 SPEC＋公式 PHP 8.3.36 | 公式修正版への更新 | 最終 RPM の FPM 試験 17/17、選択 PHPT 0 FAIL |

各ディレクトリに適用元・パッチ・ビルド方法・検証範囲を記録します。
`php54/` と `php54-el5/` は異なるベンダーソースと ABI を対象にするため分けています。

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

今回追加した `php53` / `php54-el5` / `php83` はネイティブ環境での手動ビルド・比較結果を記録しています。
現行の `build` 自動比較ジョブは `php54` のみです。新系列のビルド補助は、依存関係を準備済みの隔離環境内で実行します。

CI の再ビルドはリリースバイナリーの再現ではありません（ビルド時刻などで RPM ハッシュは変わります）。
配布物の同一性は `release-verify` が確認します。

新しい系列 `phpXX/`（必要なら `phpXX-elN/`）は次の規約に従うと自動で CI 対象になります（`ci/series.py`）。

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
