# PHP 5.4 — CVE-2026-109618 / CVE-2026-109619

## 適用対象

| 項目 | 値 |
|---|---|
| 元 SRPM | `php-5.4.16-48.el7.src.rpm` |
| ソース | [CentOS 7.9.2009 archive](https://vault.centos.org/7.9.2009/os/Source/SPackages/php-5.4.16-48.el7.src.rpm) |
| SRPM SHA-256 | `84cfffd22e99e87e1f25f5e69f74108d762bab94759ef62079092382c89c06f1` |
| ベンダーパッチ | 元 spec の 95 パッチを維持 |
| 出力 release | `5.4.16-48.el7.kucsec1` |
| 検証対象 | Linux x86_64、NTS、Apache prefork/mod_php |

[パッチ](patches/php-5.4.16-cve-2026-109618-109619.patch) は、上記 SRPM の
ベンダーパッチを適用したツリーに追加します。素の PHP 5.4.16 や 5.4.45、
他ディストリビューションへの適用・同等性は検証していません。

## 上流との対応

PHP の公式 7.4 緊急バックポート
[`712e60f9edfd03f0960fc4fc3c2c375f42b90aa2`](https://github.com/php/php-src/commit/712e60f9edfd03f0960fc4fc3c2c375f42b90aa2)
を PHP 5.4 のエンジン構造に手動で移植しています。

- [OOM corruption advisory](https://github.com/php/php-src/security/advisories/GHSA-w8hw-w9fx-j79w)
- [Stale global state advisory](https://github.com/php/php-src/security/advisories/GHSA-6wmf-4rv5-p3rp)
- [変更ごとの対応表](docs/semantic-mapping.md)

主な変更は、OOM/割当オーバーフロー時の `_exit(1)`、リクエスト終了時の状態消去、
早期 session upload-progress 処理の無効化、multipart ヘッダーと総パート数の制限です。

## ビルド

Docker と Python 3 を用意し、専用の使い捨て Docker context を指定します。
スクリプトは依存取得後のコンテナをネットワークなしで実行し、`builder` ユーザーで
元 spec に基づく RPM を生成します。ホストディレクトリや SSH agent はマウントしません。

```sh
export PHP_BACKPORT_DOCKER_CONTEXT=your-isolated-lab
sh php54/build/build-rpms.sh
```

出力先は `php54/out/`。変更する場合は `PHP_BACKPORT_OUTPUT_DIR` を指定します。
既存出力の上書きは拒否します。生成 RPM は署名されていません。
正確な入力・出力ハッシュは [manifest](tests/results/artifact-manifest.json) を参照してください。
ビルド時刻などが入るため、再ビルドで同じ RPM ハッシュになるという保証はありません。

元 spec の全 self-test は `runselftest 0` で無効化しています。
ビルド成功をテスト成功と読み替えないでください。

## 検証結果

- 修正前/修正後の実 Apache 比較: それぞれ **19/19**。
- 1,999 MiB（2,096,103,424 bytes）のアップロード: SHA-256 一致、PHP peak heap 524,288 bytes。
- 次リクエスト初期化前の状態検出値: **608 → 0**。
- 起動時/実行時/ストレージ失敗/整数オーバーフロー: 修正後はワーカー交代、親は継続。
- 四つの旧 RPM への回復: 設定保持、元モジュールハッシュ復元、**18/18**。
- 公式 PHPT 349 件: 元版 338 PASS / 1 FAIL / 5 SKIP / 5 XFAIL、
  修正版 330 PASS / 9 FAIL / 5 SKIP / 5 XFAIL。
  追加の 8 FAIL は upload-progress 無効化による意図した差分。未変更 341 件。
  元からの FAIL は vendor Patch41 で削除された `php_egg_logo_guid` の試験です。

生結果と比較用コードは [tests/](tests/) にあります。実行環境は CentOS 7 x86_64 を
QEMU 10.2.3 で動かした隔離環境です。別途、ネイティブ x86_64 ホストで CLI、
修正版 Apache モジュールの構成チェック、起動・通常 HTTP 応答を確認しています。
独立セキュリティレビュー、sanitizer 実行、実アプリ全体の UAT は未完了です。

## 運用上の変更

- OOM では PHP shutdown callback / destructor / バッファー後処理が実行されません。
  処理途中の非原子的なファイル書き込みは、別途整合性対策が必要です。
- PHP の upload-progress データは INI が On でも生成されません。通常セッションは維持します。
- 総 multipart part 数の既定値は `max_input_vars + max_file_uploads`。
  空ファイルコントロールも数えます。不要/重複 MIME ヘッダーは保持しません。
- mod_php の適用時には全 Apache ワーカーの置き換えが必要です。
  通常の graceful reload だけでは古いワーカーを残す場合があります。
- `ko_lab.so` と PHP fixture は故障注入専用です。本番への配置・ロードは禁止です。
