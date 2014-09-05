# NINJAM WebChat for audience

## 概要

 ブラウザから NINJAM チャットへ参加 (音声はなし)

### 作業手順

 - 環境設定
  - 環境へのインストール (sudo apt-get install)
  - 依存ライブラリ等のインストール
 - 公開
  - ルータの設定
  - Apache との連携



```
 +---- Server Machine ---+
 |                       |     +---------------+
 | [NINJAM Server]    <======> | NINJAM Client |
 |   ^                   |     +---------------+
 |   |                   |     +---------------+
 | [bot.py client]    <======> | IRC Server    | (Optional)
 |   |                   |     +---------------+
 |   v                   |     +---------------+
 | [WebSocket Server] <======> |               |
 |                       |     | Web Browser   |
 | [Web Server]       <======> |               |
 +-----------------------+     +---------------+
```

## Setup

 - python -- version 3.4.x
  - pip
 - node.js -- version 0.10.x
  - npm
 - git

 Python と Node.js (JavaScript)


## 作業前に

これから行う作業のログを取るように環境を構築します。

```
$ cd $HOME
$ mkdir -p tmp/
$ cd tmp
$ script ninjam-chat-build-$(date +YYYYMMDD).log
$ mkdir ninjam-chat
$ cd ninjam-chat
```

以降は、この端末で


## Ubuntu 環境でのインストール

 システム環境へインストールする為、root権限が必要になるかもしれませんが、
 ユーザ権限で、sudo を使って作業します。

```
$ sudo apt-get install node-legacy
$ sudo apt-get install npm
$ sudo apt-get install python3-tk
$ sudo apt-get install python3-pip
```

 Ubuntu の Node.js は `nodejs` というパッケージですが、
 コマンドが `nodejs` になってしまい、追加で入れる 'npm' 等コマンドが、
 そのままでは起動しません。そこで `node-legacy` パッケージをインストールします。

 Ubuntu には、Pythonのバージョンが複数入ってるので、
 3.x 系のバージョンを使います。

 `python3-tk` はオプションです。後述の設定ファイルで off に出来ます。
 ここでは、どちらでも構いません。(GUI画面にチャットのログが出るだけです)

 依存パッケージで tk という、軽量なGUIのツールキットが入ります。
 これが、Linux では幅広く使われてるライブラリで、
 もし、別のバージョンが既に入ってて更新が難しい状況であれば、


```
$ sudo pip3 autobahn
```

 Python での WebSocket ライブラリ

```
$ sudo npm install -g gulp bower forever
```

 `gulp` `bower` `forever` の 3 つのコマンドを、
 環境にインストールします。`-g` は global を意味するオプション。


### インストール後の確認作業

 インストール後にまず行う作業を

 - 正常にインストールされたかどうか
 - 何処にインストールされたか
 - アンインストール方法はどうするのか
 - アンインストール後にクリーンな環境に戻ってるかどうかの確認方法

 `script` コマンドでログを取ってると、追加でメモを取る必要はありません。

```
$ python3 --version
$ pip3 --version
$ node --version
$ npm --version
```

 ２つ目以降のコマンドは、
- 矢印の ↑ キーを押して、シェルの履歴から直前のコマンドを持ってくる
- Ctrl-A でカーソルを行頭に移動
- Alt-D でカーソル位置の単語を削除

```
$ which python3
$ which pip3
$ which node
$ which npm
```

 ２つ目以降のコマンドは、
- 矢印の ↑ キーを押して、シェルの履歴から直前のコマンドを持ってくる
- Alt-B でカーソルを前の単語の頭に移動
- Alt-D でカーソル位置の単語を削除


## プロジェクト環境の構築

次にインストールされるライブラリは、
作業ディレクトリの下にインストールされるので、

```
$ npm install
$ bower install
```

 前述の `gulp` `bower` `forever` 等のコマンドも
 ローカル環境へインストールする事も可能でしたが、
 このプロジェクト外でも利用することが出来るように、グローバルへ

 ローカル環境へインストールした場合、コマンドのPATH等が通ってないため、
 `$ node ./node_modules/gulp/bin/gulp.js` のように起動する必要が出てきます。

 ここで install されるモジュール群は、直接コマンドから呼び出す類のものではないので
 PATH が長くなる心配はありません。


```
$ gulp build
```

### 設定ファイル

#### ./src/ninjam-bot/bot.cfg



### サーバ起動

```
$ npm run chat-server
```

```
$ npm run ninjam-bot
```

 コマンドは、npm を経由しなくても実行可能です。
 package.json 内の scripts セクションに記述されたコマンドが呼び出されます。


## ルータの設定

 外部に公開する必要があるのは、WebSocket サーバの port: 6789 のみ。
 ポート番号は自由に変更可能です。(但し、ソース内も追従して変更する必要あり)

 後述のリバースプロキシを設定すれば、ルータのポート転送設定は不要です。

 or

 Apache でリバースプロキシを設定

## Apache との連携

 ./app 以下と ./bower_components を正しく配置します。

 2通りの方法

 - ディレクトリをコピーもしくは移動する。
  - ./src 編集後に毎回作業が必要になるので、タスクを `Makefile` に纏める。
 - Apache 側 _.htaccess_ 等で、エイリアスやLocation設定する。


 gulp コマンドで起動する開発用サーバは、アドレスがローカルホストでバインドされるので、
 外部からはアクセスできません。

 192.168.0.x でサーバを起動すると、ローカルネットワーク内から参照可能、
 0.0.0.0 とすることで、外部公開可能になりますが、  
 Apache 等の http サーバ経由でアクセスするように構成して下さい。

 個人規模のサイトでは、組み込みの http サーバでも、
 パフォーマンス等が問題になることはありませんが、
 Apache 側でアクセスログを一元管理、不要なポートを開かない、
 等の理由により、


## Debug use


```
$ gulp
```

## Development

### 開発言語

 - Python (NINJAM Bot)
 - Markdown (ドキュメント記述)
 - コンテンツ記述
  - Jade (HTML へ変換)
  - Less (CSS へ変換)
  - LiveScript (JavaScript へ変換)


> HTML/CSS/JavaScript は、直接

### 開発ツール

 - git
  - リビジョン管理。
    `npm` `bower` 内でもリポジトリからのソース所得に利用されます。
 - pip
  - Python のパッケージ管理
 - npm
  - サーバ側JavaScript のパッケージ管理
 - bower
  - ブラウザ側JavaScript のパッケージ管理
 - gulp
  - ビルドシステム
 - forever
  - サーバ・プロセス管理

 _pip_/_npm_/_bower_ はそれぞれ _apt_ みたいなもの
 _gulp_ は、 _make_ みたいなものです。
 _bower_ は、`npm init` すると、  
 _package.json_ に書かれた依存ライブラリが ./node_modules 以下にインストールされます。


```
$ gulp build
```

 開発中は、簡易HTTPサーバ, LiveReload, ファイル監視ビルド が起動

```
$ gulp
```

 ./src 以下の監視対象ファイルに更新があった時、  
 jade/less/ls ファイルは、html/css/js へ自動でコンパイルされ、
 自動でブラウザがリロードされます。

 自動リロードは、ブラウザ側に LiveReload のプラグインのインストールが必要です。


### 開発環境

 プログラミングのサポートのあるエディタを

 - atom (https://atom.io/)
  - Python は標準でサポート
  - Jade/Less/LiveScript はプラグインでサポート
  - Markdown 編集は Markdown Preview で、Preview を確認しながら編集。
 - 編集設定
  - .py ファイルは、インデント幅4 ソフトスペース (インデントの Tab は 幅4 のスペースに展開)
  - .jade, .less, .ls ファイルは、インデント幅 2 ソフトスペース
  - 改行文字は LF で統一。

## 運用

### Console

 - タブの利用
  - `byobu`
 - `script` コマンドで作業ログを取る

### forever コマンドでサーバを起動 / 再起動 / 終了

 サーバの起動スクリプトで PID をファイルに出力し、  
 終了スクリプトでは、`kill` コマンドで 起動時に記録した PID のプロセスに終了のシグナルを送る。

> XXX: version issue `forever` require node 0.8

 NINJAMサーバの起動・停止も `forever` で管理すると便利です。


### Git でリビジョン管理 / ブランチ作成 / マージ手順

 設定等をカスタマイズした




## TODO

 - 名前入力欄を解り易く
 - オーディオ視聴 (別途配信が必要。bot.py で shoutcast 対応、等)
  - vorbis decode / mp3 encode
 - 参加者/視聴者数の表示
 - サーバの起動・停止タスクの提供
 - コネクション切断時の再接続処理
 - 発言履歴の件数制限 (発言が溜まってきた時の、ブラウザのリソース消費を抑える)
 - bot.py 各サービスのプラグイン化
 - AngularJS/Test
 - Python/Wheel

## Resources

 - https://www.python.org/
 - http://nodejs.org/
 - http://jade-lang.com/
 - http://lesscss.org/
 - http://livescript.net/
 - http://gulpjs.com/
