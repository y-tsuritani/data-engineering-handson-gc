import io
import os

import flask
import functions_framework
import pandas as pd
from google.cloud import bigquery, storage

BUCKET_NAME = os.environ.get("BUCKET_NAME", "")
PROJECT_ID = os.environ.get("PROJECT_ID", "")
DATASET_ID = os.environ.get("DATASET_ID", "de_handson")
TABLE_ID = "transactions"


def read_csv_from_gcs(bucket_name: str, date_str: str) -> pd.DataFrame:
    """GCS から日次 CSV を読み込んで DataFrame を返す。

    Args:
        bucket_name: GCS バケット名。
        date_str: 対象日付（例: "2010-12-01"）。

    Returns:
        読み込んだ DataFrame。

    Raises:
        google.cloud.exceptions.NotFound: 対象 CSV が GCS に存在しない場合。
    """
    client = storage.Client()
    blob = client.bucket(bucket_name).blob(f"raw/transactions/transactions_{date_str}.csv")
    content = blob.download_as_bytes()
    return pd.read_csv(io.BytesIO(content))


def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """クレンジング処理を適用した DataFrame を返す。

    処理内容:
    - キャンセル取引（InvoiceNo が C 始まり）を除外
    - Quantity・UnitPrice を数値型に強制変換
    - InvoiceDate を TIMESTAMP 型に変換
    - sales_amount（Quantity × UnitPrice）を追加
    - CustomerID 欠損は NULL のまま保持

    Args:
        df: クレンジング前の DataFrame。

    Returns:
        クレンジング済みの DataFrame。
    """
    df = df[~df["InvoiceNo"].astype(str).str.startswith("C")].copy()
    # C始まりを除外後、全行が数値になるとpandasがint64に推論するためSTRINGに明示変換
    df["InvoiceNo"] = df["InvoiceNo"].astype(str)

    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")

    df["sales_amount"] = df["Quantity"] * df["UnitPrice"]

    # CSV 読み込み時に float64 になるため str に変換（例: 12345.0 → "12345"）
    df["CustomerID"] = df["CustomerID"].apply(
        lambda x: str(int(x)) if pd.notna(x) else None
    )

    return df.dropna(subset=["Quantity", "UnitPrice", "InvoiceDate"])


def load_to_bigquery(df: pd.DataFrame, project_id: str, dataset_id: str) -> int:
    """BigQuery の transactions テーブルに append してロード件数を返す。

    Args:
        df: ロードする DataFrame。
        project_id: GCP プロジェクト ID。
        dataset_id: BigQuery データセット ID。

    Returns:
        ロードした行数。
    """
    client = bigquery.Client(project=project_id)
    table_ref = f"{project_id}.{dataset_id}.{TABLE_ID}"

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        time_partitioning=bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="InvoiceDate",
        ),
    )

    job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
    job.result()  # 完了まで待機

    return len(df)


@functions_framework.http
def main(request: flask.Request) -> tuple[str, int]:
    """Cloud Run Functions エントリポイント。

    Args:
        request: HTTP リクエスト。ボディに JSON で `date`（例: "2010-12-01"）を渡す。

    Returns:
        (レスポンスメッセージ, HTTP ステータスコード) のタプル。
    """
    request_json = request.get_json(silent=True)
    if not request_json or "date" not in request_json:
        return "リクエストボディに 'date' パラメータが必要です（例: {'date': '2010-12-01'}）", 400

    date_str = request_json["date"]

    if not BUCKET_NAME or not PROJECT_ID:
        return "環境変数 BUCKET_NAME・PROJECT_ID が設定されていません", 500

    df_raw = read_csv_from_gcs(BUCKET_NAME, date_str)
    df_clean = clean_transactions(df_raw)
    n_loaded = load_to_bigquery(df_clean, PROJECT_ID, DATASET_ID)

    message = f"{date_str}: {n_loaded} 行をロードしました（クレンジング前: {len(df_raw)} 行）"
    print(message)
    return message, 200
