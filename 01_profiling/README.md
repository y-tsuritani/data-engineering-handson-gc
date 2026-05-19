# Part 1: GCS へのデータ取り込みとプロファイリング

UCI Online Retail Dataset を GCS にアップロードし、データ品質を確認します。

## 前提条件

- Python 3.12 / uv がインストール済み
- `gcloud` CLI がインストール済みで認証済み（`gcloud auth login`）
- GCS バケットが作成済み

```bash
# バケット作成（未作成の場合）
gcloud storage buckets create gs://YOUR_BUCKET_NAME --location=asia-northeast1
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

| 項目               | 値                        | 備考                         |
|--------------------|---------------------------|------------------------------|
| 総行数             | 42,481 行                 | 2010年12月分                 |
| 期間               | 2010-12-01 〜 2010-12-23  | 土曜日はデータなし           |
| `CustomerID` 欠損  | 約37%                     | ゲスト購入として保持         |
| キャンセル取引     | 728 行                    | `InvoiceNo` が C 始まり      |
| `Quantity` < 0     | 798 行                    | キャンセル行と一部重複       |
| `UnitPrice` = 0    | 273 行                    | Part 2 でビジネスルールを決定|
| タイムゾーン       | UTC+0（GMT）              | 英国の12月はサマータイム外   |
