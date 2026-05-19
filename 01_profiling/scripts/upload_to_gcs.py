import os
from pathlib import Path

from google.cloud import storage

DATA_DIR = Path(__file__).parent.parent.parent / "data"  # プロジェクトルートの data/
MASTER_FILES: tuple[str, ...] = ("products.csv", "countries.csv")


def get_bucket(bucket_name: str) -> storage.Bucket:
    """GCS バケットオブジェクトを返す。

    Args:
        bucket_name: バケット名。

    Returns:
        指定バケットの Bucket オブジェクト。
    """
    client = storage.Client()
    return client.bucket(bucket_name)


def upload_file(bucket: storage.Bucket, local_path: Path, gcs_path: str) -> None:
    """1 ファイルを GCS にアップロードしてログ出力する。

    Args:
        bucket: アップロード先のバケット。
        local_path: アップロードするローカルファイルのパス。
        gcs_path: GCS 上のオブジェクトパス（バケット名を含まない）。
    """
    blob = bucket.blob(gcs_path)
    blob.upload_from_filename(str(local_path))  # GCS API は str パスを要求するため
    size_kb = local_path.stat().st_size / 1024
    print(f"Uploaded ({size_kb:.1f} KB): gs://{bucket.name}/{gcs_path}")


def upload_daily_transactions(bucket: storage.Bucket, data_dir: Path) -> int:
    """transactions/ 配下の全 CSV を GCS にアップロードしてファイル数を返す。

    Args:
        bucket: アップロード先のバケット。
        data_dir: ローカルのデータルートディレクトリ。transactions/ サブディレクトリを含むこと。

    Returns:
        アップロードした CSV ファイルの数。
    """
    csv_files = sorted((data_dir / "transactions").glob("*.csv"))
    for f in csv_files:
        upload_file(bucket, f, f"raw/transactions/{f.name}")
    return len(csv_files)


def upload_master_files(bucket: storage.Bucket, data_dir: Path) -> None:
    """products.csv・countries.csv を GCS にアップロードする。

    Args:
        bucket: アップロード先のバケット。
        data_dir: ローカルのデータルートディレクトリ。

    Raises:
        FileNotFoundError: マスタファイルが存在しない場合。先に split_data.py を実行すること。
    """
    for filename in MASTER_FILES:
        local_path = data_dir / filename
        if not local_path.exists():
            raise FileNotFoundError(
                f"{local_path} が見つかりません。"
                " 先に split_data.py を実行してください。"
            )
        upload_file(bucket, local_path, f"raw/{filename}")


def main() -> None:
    """エントリポイント。"""
    bucket_name = os.environ.get("BUCKET_NAME")
    if not bucket_name:
        raise ValueError(
            "環境変数 BUCKET_NAME が設定されていません。\n"
            "export BUCKET_NAME=YOUR_BUCKET_NAME"
        )

    print(f"Bucket: {bucket_name}")
    bucket = get_bucket(bucket_name)

    n_files = upload_daily_transactions(bucket, DATA_DIR)
    upload_master_files(bucket, DATA_DIR)

    print("\n=== アップロード完了 ===")
    print(f"日次 CSV ファイル数: {n_files} 件")
    print(f"マスタファイル数: {len(MASTER_FILES)} 件 ({', '.join(MASTER_FILES)})")
    print(f"格納先プレフィックス: gs://{bucket_name}/raw/")


if __name__ == "__main__":
    main()
