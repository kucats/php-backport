# PHP 5.4.45 — CVE-2026-109618 / CVE-2026-109619

対象入力は [php-5.4.45-56.art.src.rpm](https://updates.atomicorp.com/channels/source/php/php-5.4.45-56.art.src.rpm)、SHA-256 は
`616c8247bc99f1b8127861a750fdf51ef05cfd76c98b975cd1acac5e39f59107` です。出力候補は `5.4.45-56.el5.art.kucsec1`、Linux x86_64 向けです。
最終 RPM の Apache 試験 **20/20**（1,999 MiB アップロードを含む）を確認しました。
同一ベンダー 5.4.45 の未修正 build-tree ランタイムとの比較では、PHPT 349 件中の変更は
意図した upload-progress 無効化による 8 件のみです。元からの `php_egg_logo_guid` 失敗は残ります。
[検証・再現手順](tests/README.md) と [検証済み RPM ハッシュ](tests/results/artifact-manifest.json) を参照してください。

[入力 manifest](docs/input-manifest.json)、[SPEC](packaging/php.spec) と
[元 SPEC からの差分](packaging/spec.patch) を記録しています。

このパッチは元 SRPM の 20 個の適用対象ベンダーパッチの**後**に追加します。
素の PHP 5.4.45 や別 OS 向けパッケージへの流用は未検証です。
公式 PHP 7.4 緊急修正
[`712e60f9edfd03f0960fc4fc3c2c375f42b90aa2`](https://github.com/php/php-src/commit/712e60f9edfd03f0960fc4fc3c2c375f42b90aa2)
に基づく手動移植です。割当失敗・整数オーバーフロー時にプロセスを終了し、
次のリクエストへ残る状態を消去し、multipart の不要・重複ヘッダーと総部品数を制限します。

早期 session upload-progress を無効化します。通常セッションは維持します。
SPEC は `rhel=5`、`dist=.el5` として評価します。Atomic 5.4.36 の完全な元ソースではなく、同系列最終版 5.4.45 を基礎にします。

公開インタープリターと合成試験のみを管理します。本番アプリ・認証情報・本番設定・
利用者データは含めません。生成 RPM はローカルビルドの未署名パッケージです。
ベンダー公式更新や EOL 系列の全面的な脆弱性解消を意味しません。
