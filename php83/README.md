# PHP 8.3.36 — CVE-2026-109618 / CVE-2026-109619

対象入力は [php-8.3.33-1.el10_2.src.rpm](https://dl.rockylinux.org/pub/rocky/10.2/AppStream/source/tree/Packages/p/php-8.3.33-1.el10_2.src.rpm)、SHA-256 は
`d4350267bdedbe046d2f3cafe054be9b0ddc7077136f0be76a3910da95ea8e34` です。出力候補は `8.3.36-1.el10_2.kucsec1`、Linux x86_64 向けです。
最終 8 RPM を隔離環境へインストールし、Nginx/FPM 試験 **17/17**
（1,999 MiB アップロードを含む）と、署名済み元 RPM への復旧・再更新を確認しました。
選択した公式 PHPT 483 件は **452 PASS / 30 SKIP / 1 XFAIL / 0 FAIL / 0 WARN** です。
[検証・再現手順](tests/README.md)、[ビルド補助](build/build-rpms.sh)、
[検証済み RPM ハッシュ](tests/results/artifact-manifest.json) を参照してください。

[入力 manifest](docs/input-manifest.json)、[SPEC](packaging/php.spec) と
[元 SPEC からの差分](packaging/spec.patch) を記録しています。

手動の EOL エンジンパッチではなく、[公式 PHP 8.3.36](https://www.php.net/releases/8_3_36.php)
の署名済みソースに Rocky 既存 SPEC とベンダーパッチを適用する再ビルドです。
元 SRPM の `SOURCES/php-keyring.gpg` を使い、8.3.36 の detached signature も確認します。
署名確認後、ソース tar と署名を SOURCES へ追加し、SPEC の版と release のみ変更します。

公開インタープリターと合成試験のみを管理します。本番アプリ・認証情報・本番設定・
利用者データは含めません。生成 RPM はローカルビルドの未署名パッケージです。
ベンダー公式更新や EOL 系列の全面的な脆弱性解消を意味しません。
