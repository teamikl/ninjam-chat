# NINJAM Web Chat


##　前準備

- python3.4 / pip
- node / npm
- git

> Ubuntu環境での注意点
> `node` の aptパッケージは `nodejs-legacy` を選択してください。
> `pip` は Python3 用のものを利用します。

### 環境へのインストール

> pythoh/node を環境へインストールしている場合、
> 管理者権限が必要になるので、各コマンドの頭に `sudo` を付けて、管理者権限で実行してください。

#### Python module

```
$ pip install autobahn
```

#### Node module

```
$ npm -g install gulp
$ npm -g install bower
```

### プロジェクト環境へのインストール

ユーザのローカル環境へインストールされるため、管理者権限は不要です。

```
$ npm install
$ bower install
```

## 設定

 ./src/ninjam-bot/bot.cfg

必須項目は、NINJAM のチャットのみ。


## サーバの起動

```
$ npm run chat-server
```

```
$ npm run ninjam-bot
```


## デプロイ

TODO: ./app ./bower_components の公開
TODO: reverse proxy の設定