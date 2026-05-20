# Part 2: データクレンジングと BigQuery へのロード

GCS の日次 CSV を Cloud Run Functions で読み込み、クレンジングして BigQuery にロードします。

## 前提条件

- Part 1 が完了していること（GCS に `raw/transactions/*.csv` が存在する）
- `gcloud` CLI がインストール済みで認証済み
- 以下の API が有効化済み

```bash
gcloud services enable \
  cloudfunctions.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com
```

- デプロイユーザーに `roles/iam.serviceAccountUser` が付与済み

```bash
# Compute Engine デフォルトサービスアカウントに対して付与
gcloud iam service-accounts add-iam-policy-binding \
  $(gcloud projects describe $GOOGLE_CLOUD_PROJECT --format="value(projectNumber)")-compute@developer.gserviceaccount.com \
  --member="user:YOUR_EMAIL" \
  --role="roles/iam.serviceAccountUser"
```

## BigQuery テーブルの作成

```bash
# データセット作成
bq mk --dataset --location=us-central1 ${PROJECT_ID}:de_handson

# テーブル作成（schema.sql 内の ${PROJECT_ID} を sed で置換してから実行）
bq query --use_legacy_sql=false \
  "$(sed "s/\${PROJECT_ID}/${PROJECT_ID}/g" 02_cleaning/sql/schema.sql)"
```

テーブルスキーマ（`sql/schema.sql` 参照）:

| カラム       | 型        | 備考                                   |
|--------------|-----------|----------------------------------------|
| InvoiceNo    | STRING    | キャンセルは除外済み（C 始まりを除外） |
| StockCode    | STRING    |                                        |
| Description  | STRING    | nullable                               |
| Quantity     | INT64     |                                        |
| InvoiceDate  | TIMESTAMP | パーティションキー                     |
| UnitPrice    | FLOAT64   |                                        |
| CustomerID   | STRING    | nullable（ゲスト購入）                 |
| Country      | STRING    |                                        |
| sales_amount | FLOAT64   | Quantity × UnitPrice                   |

## Cloud Run Functions のデプロイ

```bash
gcloud functions deploy clean-and-load \
  --gen2 --runtime=python312 --region=asia-northeast1 \
  --source=02_cleaning/cloud_run_function --entry-point=main \
  --trigger-http --allow-unauthenticated --memory=512M \
  --set-env-vars PROJECT_ID=${GOOGLE_CLOUD_PROJECT},BUCKET_NAME=YOUR_BUCKET_NAME,DATASET_ID=de_handson
```

> **注意**: `--allow-unauthenticated` を指定すると関数が公開状態になります。  
> 本番環境では削除し、IAM 認証（`roles/cloudfunctions.invoker`）を使用してください。

メモリを 512MB に設定しているのは、pyarrow + pandas + BigQuery クライアントを同時にロードすると デフォルトの 256MB を超えるためです。

## 動作確認（単日）

```bash
# 関数 URL を取得
FUNCTION_URL=$(gcloud functions describe clean-and-load \
  --region=asia-northeast1 --format="value(serviceConfig.uri)")

# 1日分を手動実行
curl -X POST "${FUNCTION_URL}" \
  -H "Content-Type: application/json" \
  -d '{"date": "2010-12-01"}'
```

正常時のレスポンス例:

```text
2010-12-01: 888 行をロードしました（クレンジング前: 941 行）
```

## 全日付の一括ロード

```bash
# 重複ロードを防ぐため実行前に既存データを削除
bq query --use_legacy_sql=false \
  "TRUNCATE TABLE \`${GOOGLE_CLOUD_PROJECT}.de_handson.transactions\`"

export PROJECT_ID="${GOOGLE_CLOUD_PROJECT}"
bash 02_cleaning/scripts/batch_clean_and_load.sh
```

## クレンジング処理の内容

`cloud_run_function/main.py` の `clean_transactions()` が行う処理:

1. **キャンセル取引の除外** — `InvoiceNo` が `C` 始まりの行を削除
2. **数値型への強制変換** — `Quantity`・`UnitPrice` を `pd.to_numeric(errors="coerce")`
3. **日時型への変換** — `InvoiceDate` を `pd.to_datetime(errors="coerce")`
4. **売上金額の計算** — `sales_amount = Quantity × UnitPrice` を追加
5. **CustomerID の型変換** — CSV 読み込み時に float64（`12345.0`）になるため `str`（`"12345"`）に変換
6. **欠損行の除外** — `Quantity`・`UnitPrice`・`InvoiceDate` のいずれかが NaN の行を削除

## ローカルでのテスト

```bash
# 環境変数を先に設定してから起動すること（モジュールロード時に読み込まれるため）
export BUCKET_NAME="YOUR_BUCKET_NAME"
export PROJECT_ID="YOUR_PROJECT_ID"
export DATASET_ID="de_handson"

uv run functions-framework --target=main --port=8080
```

別ターミナルで:

```bash
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{"date": "2010-12-01"}'
```

## requirements.txt の更新

`pyproject.toml` の依存パッケージを変更した場合は再生成します。

```bash
uv export --no-hashes --no-dev > 02_cleaning/cloud_run_function/requirements.txt
```
