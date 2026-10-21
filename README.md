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

## Attribution

This product includes PHP software, freely available from
<http://www.php.net/software/>.

This product includes the Zend Engine, freely available at
<http://www.zend.com>. The Zend Engine is freely available at
<http://www.zend.com>.

元ソース由来のコードには [PHP License 3.01](LICENSES/PHP-3.01.txt) と
[Zend Engine License 2.00](LICENSES/Zend-2.00.txt) が適用されます。
このリポジトリは元プロジェクトによる推奨・承認を表すものではありません。
