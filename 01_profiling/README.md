# Part 1: GCS へのデータ取り込みとプロファイリング

UCI Online Retail Dataset を GCS にアップロードし、データ品質を確認します。

## 前提条件

- Python 3.12 / uv がインストール済み
- `gcloud` CLI がインストール済みで認証済み（`gcloud auth login`）
- GCS バケットが作成済み

```bash
# バケット作成（未作成の場合）
# us-central1 を指定するのは GCS 無料枠が US リージョン限定のため
gcloud storage buckets create gs://YOUR_BUCKET_NAME --location=us-central1
```

## セットアップ

```bash
# リポジトリルートで依存パッケージをインストール
uv sync
```

## データ準備

1. `data/README.md` の手順に従い `data/Online_Retail.xlsx` を配置する

2. xlsx を日次 CSV とマスタファイルに分割する

```bash
uv run python 01_profiling/scripts/split_data.py
```

実行後に生成されるファイル:

```text
data/
├── transactions/
│   ├── transactions_2010-12-01.csv
│   ├── transactions_2010-12-02.csv
│   └── ...（20ファイル）
├── products.csv
└── countries.csv
```

## GCS へのアップロード

```bash
export BUCKET_NAME="YOUR_BUCKET_NAME"
uv run python 01_profiling/scripts/upload_to_gcs.py
```

アップロード先:

```text
gs://YOUR_BUCKET_NAME/
└── raw/
    ├── transactions/transactions_YYYY-MM-DD.csv  （20ファイル）
    ├── products.csv
    └── countries.csv
```

## プロファイリング

Jupyter Notebook でデータ品質を確認します。

```bash
uv run jupyter notebook 01_profiling/notebooks/profiling.ipynb
```

確認内容:
- 欠損値の分布（`CustomerID` は約37%欠損）
- 異常値（マイナス `Quantity`、`UnitPrice = 0` など）
- 日付ごとの取引件数の分布

## データ品質メモ

| 項目               | 値                        | 備考                                        |
|--------------------|---------------------------|---------------------------------------------|
| 総行数             | 103,598 行                | 2010-12〜2011-02 の3ヶ月分                  |
| 期間               | 2010-12-01 〜 2011-02-27  | 土曜日はデータなし                          |
| 月別行数           | 42,481 / 35,147 / 25,970  | 12月 / 1月 / 2月                            |
| 日次CSVファイル数  | 67 ファイル               |                                             |
| `CustomerID` 欠損  | 約34%                     | ゲスト購入として保持                        |
| キャンセル取引     | 1,903 行                  | `InvoiceNo` が C 始まり                     |
| `Quantity` < 0     | 2,114 行                  | キャンセル行と一部重複                      |
| `UnitPrice` = 0    | 484 行                    | Part 2 でビジネスルールを決定               |
| タイムゾーン       | UTC+0（GMT）              | 英国の12〜2月はサマータイム外（GMT = UTC+0）|
