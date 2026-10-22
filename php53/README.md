# PHP 5.3.3 — CVE-2026-109618 / CVE-2026-109619

対象入力は [php-5.3.3-50.el6_10.src.rpm](https://archive.kernel.org/centos-vault/6.10/updates/Source/SPackages/php-5.3.3-50.el6_10.src.rpm)、SHA-256 は
`ddd0f179582dda7b9f0ef2936948e62455509a7ee651ecc24e33468a20b9b10a` です。出力候補は `5.3.3-50.el6_10.kucsec1`、Linux x86_64 向けです。
最終 8 RPM を隔離環境へインストールして Apache 試験 **20/20**
（1,999 MiB アップロードを含む）と、署名済み元 RPM への復旧・再更新を確認しました。
PHPT 271 件の比較は build-tree CLI/CGI を用い、元版と全件同じ結果です。
[検証・再現手順](tests/README.md) と [検証済み RPM ハッシュ](tests/results/artifact-manifest.json) を参照してください。

[入力 manifest](docs/input-manifest.json)、[SPEC](packaging/php.spec) と
[元 SPEC からの差分](packaging/spec.patch) を記録しています。

このパッチは元 SRPM の 114 個の適用対象ベンダーパッチの**後**に追加します。
素の PHP 5.3.3 や別 OS 向けパッケージへの流用は未検証です。
公式 PHP 7.4 緊急修正
[`712e60f9edfd03f0960fc4fc3c2c375f42b90aa2`](https://github.com/php/php-src/commit/712e60f9edfd03f0960fc4fc3c2c375f42b90aa2)
に基づく手動移植です。割当失敗・整数オーバーフロー時にプロセスを終了し、
次のリクエストへ残る状態を消去し、multipart の不要・重複ヘッダーと総部品数を制限します。

PHP 5.3 には session upload-progress 実装がないため、その無効化パッチは含めません。

公開インタープリターと合成試験のみを管理します。本番アプリ・認証情報・本番設定・
利用者データは含めません。生成 RPM はローカルビルドの未署名パッケージです。
ベンダー公式更新や EOL 系列の全面的な脆弱性解消を意味しません。

[比較結果](tests/results/php53-phpt-comparison.json): 261 PASS / 9 FAIL / 1 SKIP、
変更された判定は0件です。元からの9 FAILはそのまま記録しています。

`tests/fixtures/ko_lab.c` は故障注入専用です。本番へ配置・ロードしないでください。
[ビルド補助](build/build-rpms.sh) は、署名を検証できる一致OSの隔離コンテナ内で、
非rootユーザーにより実行します。実行前に署名済み依存パッケージを用意し、
ビルド前にネットワークを切断してください。ホストマウント、SSH agent、公開ポートは不要です。
