# 隔離した比較試験

このディレクトリは合成データのみです。`ko_lab.c` はメモリ割当失敗と整数
オーバーフローを意図的に発生させます。本番での配置・ロード・実行は禁止です。

## 実行済みの条件

- CentOS 7 x86_64 / Apache 2.4.6-99 / mod_php 5.4.16、NTS、prefork。
- 修正前 `5.4.16-48.el7`、修正後 `5.4.16-48.el7.kucsec1`。
- 専用 Docker VM、ホストマウント/SSH agent 共有なし。
- テストコンテナは `--network none --memory 512m --pids-limit 128`、ポート公開なし。
- Apache はコンテナ内 `127.0.0.1:8080` にのみ bind、再利用ワーカー 1。
- QEMU 10.2.3。旧 QEMU 7 の基本コマンド障害を含むビルド出力は使用していません。

## 比較の再現

元 RPM と修正 RPM を別々の使い捨てコンテナに用意します。ビルド用 Dockerfile は
元版と php-devel をインストールするので、修正前の比較イメージとして保存できます。
修正版では対象の php/common/cli/mbstring と、試験用の同版 php-devel を入れます。

1. `httpd.conf`、`ko_lab.c`、`run_http.py` を `/lab/` へコピーします。
2. `fixture.php` を `/lab/www/`、その `parts/`、`warn/`、`probe/` にコピーします。
3. `/lab/state` を作成します。runner が配下の一時ファイル/セッション領域を初期化します。
4. コンテナ内で次を実行します。

```sh
gcc -shared -fPIC $(php-config --includes) /lab/ko_lab.c -o /lab/ko_lab.so
echo extension=/lab/ko_lab.so > /etc/php.d/99-ko-lab.ini
python3 /lab/run_http.py --large-mib 1999 --output /lab/state/baseline.json
# 修正済みコンテナでは:
python3 /lab/run_http.py --candidate --large-mib 1999 --output /lab/state/candidate.json
```

約 2 GB の一時ディスク領域が必要です。試験は Apache を別 process group で起動し、
終了時に停止します。実サービスの URL を指定する機能はありません。

CI（`build` ワークフロー）では `build-rpms.sh` を `PHP_BACKPORT_KEEP_IMAGE` 付きで実行し、
残したビルドイメージで `run-comparison.sh` が上記 1〜4 を修正前/修正後それぞれの
`--network none` コンテナで自動実行します。既定では大容量アップロード試験は省略します。

## 保存済み結果

`results/baseline.json` と `candidate.json` は各 19/19、`recovery.json` は 18/18。
baseline の PASS は「旧挙動を検出できた」という意味です。脆弱な旧版の安全性を
示すものではありません。修正版では OOM 即時終了、進捗処理無効化、状態消去、
パート制限などについて期待値を変えています。

early-state のビット値は、error handlers (1/2)、exceptions (4)、error mode (8)、
object buckets (16)、superglobals (32)、modules activated (64)、handler stacks (128)、
SAPI strings (256)、header list (512)。修正前 608、修正後 0 です。

## 公式 PHPT

`results/selected-phpt.txt` は選定した 349 件の一覧です。元 SRPM に含まれる試験を
同じディレクトリ構造で使い、元版/修正版の CLI と CGI でそれぞれ実行しました。

```sh
NO_INTERACTION=1 REPORT_EXIT_STATUS=1 \
  TEST_PHP_EXECUTABLE=/usr/bin/php TEST_PHP_CGI_EXECUTABLE=/usr/bin/php-cgi \
  php -n run-tests.php -n -p /usr/bin/php -q -r selected-phpt.txt
```

生ログは `results/*-phpt.log`。比較は `python3 php54/tests/compare_phpt.py` で行えます。
元からの失敗 1 件、既存 XFAIL 5 件、SKIP 5 件は残っています。追加 8 FAIL は
無効化された進捗データ/早期 session 警告の期待値の差です。生の FAIL を PASS に
書き換えていません。元 spec の self-test 全体は実行していません。

これらは PHP API と合成ファイル操作の検証です。実アプリの認可、外部同期、
非原子的なメタデータ更新の整合性や、全攻撃変種への耐性を保証しません。
