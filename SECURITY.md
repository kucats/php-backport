# Security policy

## 報告方法

このリポジトリのパッチ・ビルド手順・配布 RPM に関する脆弱性は、公開 Issue ではなく
GitHub の [Private vulnerability reporting](https://github.com/kucats/php-backport/security/advisories/new)
から非公開で報告してください。

報告には次を含めてください。

- 対象の系列（`php54/` など）と Release タグ
- 再現手順、影響、可能なら修正案

## 対象範囲

- 対象：このリポジトリのバックポートパッチ、spec 変更、ビルド・検証スクリプト、Release 資産
- 対象外：PHP 本体や各ディストリビューションの脆弱性そのもの。
  PHP 本体は [PHP プロジェクト](https://github.com/php/php-src/security)、
  各ディストリビューションはそれぞれの窓口へ報告してください。

## サポート

[README](README.md) の表に掲載した系列が対象です。これらはコミュニティーの緊急
バックポート候補で、EOL ランタイムの全脆弱性の解消や対応期限は保証しません。
