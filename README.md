# Job Tracker

[![CI](https://github.com/cogitoVinci/job-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/cogitoVinci/job-tracker/actions/workflows/ci.yml)

就活の管理をExcelでしていた時、締切を見逃しそうになったので作りました。  
企業名・職種・選考状況・応募日・締切日をまとめて管理できるWebアプリです。

## 公開アプリ

https://job-tracker-kuqvenpdwjb9hnv4fkqzht.streamlit.app/

※公開版は、アプリが再起動されるとデータが消えることがあります。ローカルで使う場合は消えません。

## できること

一覧表示、編集、削除のほか、締切が近い応募を一目で確認できるようにしています。  
選考状況ごとの件数や内定率も確認できるので、就活の進み具合が分かりやすくなります。

- 企業・職種・選考状況の登録、編集、削除
- 7日以内の締切の表示
- 企業名・職種での検索
- ステータスによる絞り込み
- 応募件数・内定率の集計
- 選考状況と月別応募件数のグラフ表示
- CSVファイルのダウンロード
- SQLiteによるデータ保存

## 選考状況のステータス

`検討中` → `ES` → `適性検査` → `面接` → `内定` / `不合格` / `辞退`

`検討中`はまだ応募していない会社なので、応募件数には含めていません。

## 使用例

例えば、応募した企業の選考状況と締切を管理する時は、次のように使います。

1. 左側のフォームに企業名、職種、選考状況、応募日、締切日を入力します。
2. 必要な場合はメモを書き、「追加する」を押します。
3. 登録した情報は「応募一覧」に表示されます。
4. 企業名や職種で検索したり、ステータスで絞り込んだりできます。
5. 登録後も、選考状況や締切日を編集できます。
6. 7日以内の締切は、画面上部の「直近の締切」に表示されます。
7. 「統計・分析」タブでは、選考状況ごとの件数や月別応募件数を確認できます。

次の画像は、企業情報を登録した後の画面です。  
応募件数、内定率、近い締切、応募一覧を一つの画面で確認できます。

![Job Trackerの使用例](docs/job-tracker-screenshot.png)

## 必要なもの

- Python 3.13
- uv

## インストール方法

```bash
git clone https://github.com/cogitoVinci/job-tracker.git
cd job-tracker
uv sync
```

## 開発環境の準備

開発用のパッケージも含めてインストールします。

```bash
uv sync --dev
```

テストを実行します。

```bash
uv run pytest
```

## 起動方法

```bash
uv run streamlit run main.py
```

起動した後、ブラウザで次のURLを開きます。

```text
http://localhost:8501
```

## テスト

```bash
uv run pytest
```

テストでは、主にデータベースの処理と集計の処理を確認しています。

GitHubにpushすると、GitHub Actionsでも自動でテストが実行されます。

## 使用した技術

- Python
- Streamlit
- SQLite
- pandas
- pytest
- GitHub Actions
- uv

## ライセンス

MIT Licenseを使っています。  
詳しくは[LICENSE](LICENSE)を確認してください。
