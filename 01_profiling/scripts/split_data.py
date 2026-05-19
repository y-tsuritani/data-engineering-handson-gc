from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent.parent.parent / "data"  # プロジェクトルートの data/
RAW_XLSX = DATA_DIR / "Online_Retail.xlsx"
TRANSACTIONS_DIR = DATA_DIR / "transactions"
PRODUCTS_PATH = DATA_DIR / "products.csv"
COUNTRIES_PATH = DATA_DIR / "countries.csv"

PERIOD_START = pd.Timestamp("2010-12-01")
PERIOD_END = pd.Timestamp("2011-02-28")


def load_raw_data(filepath: Path) -> pd.DataFrame:
    """xlsx ファイルを読み込んで InvoiceDate を datetime にパースして返す。

    Args:
        filepath: 読み込む xlsx ファイルのパス。

    Returns:
        InvoiceDate が有効な行のみの DataFrame。
    """
    df = pd.read_excel(filepath, engine="openpyxl")
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    return df.dropna(subset=["InvoiceDate"])


def filter_by_period(
    df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp
) -> pd.DataFrame:
    """指定期間のデータのみ抽出して返す。

    Args:
        df: 対象 DataFrame。InvoiceDate 列が datetime 型であること。
        start: 抽出開始日時（この日付を含む）。
        end: 抽出終了日時（この日付を含む）。

    Returns:
        指定期間のデータのみを含む DataFrame のコピー。
    """
    mask = (df["InvoiceDate"] >= start) & (df["InvoiceDate"] <= end)
    return df[mask].copy()


def split_by_date(df: pd.DataFrame, output_dir: Path) -> int:
    """日付ごとに CSV を書き出し、生成ファイル数を返す。

    Args:
        df: 対象 DataFrame。InvoiceDate 列が datetime 型であること。
        output_dir: CSV の出力先ディレクトリ。存在しない場合は自動作成する。

    Returns:
        生成した日次 CSV ファイルの数。
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    for date, group in df.groupby(df["InvoiceDate"].dt.date):
        filename = output_dir / f"transactions_{date}.csv"
        group.to_csv(filename, index=False)
    return df["InvoiceDate"].dt.date.nunique()


def extract_products(df: pd.DataFrame, output_path: Path) -> None:
    """StockCode・Description の重複なし一覧を CSV 出力する。

    Args:
        df: 対象 DataFrame。StockCode・Description 列を含むこと。
        output_path: 出力先 CSV ファイルのパス。
    """
    products = (
        df[["StockCode", "Description"]]
        .assign(StockCode=df["StockCode"].astype(str))  # 整数・文字列混在のため文字列に統一
        .drop_duplicates()
        .sort_values("StockCode")
    )
    products.to_csv(output_path, index=False)


def extract_countries(df: pd.DataFrame, output_path: Path) -> None:
    """Country の重複なし一覧を CSV 出力する。

    Args:
        df: 対象 DataFrame。Country 列を含むこと。
        output_path: 出力先 CSV ファイルのパス。
    """
    countries = df[["Country"]].drop_duplicates().sort_values("Country")
    countries.to_csv(output_path, index=False)


def main() -> None:
    """エントリポイント。"""
    print(f"Loading: {RAW_XLSX}")
    df = load_raw_data(RAW_XLSX)
    print(f"Total rows loaded: {len(df):,}")

    df_period = filter_by_period(df, PERIOD_START, PERIOD_END)
    print(f"Rows in {PERIOD_START.date()} - {PERIOD_END.date()}: {len(df_period):,}")

    n_files = split_by_date(df_period, TRANSACTIONS_DIR)
    extract_products(df_period, PRODUCTS_PATH)
    extract_countries(df_period, COUNTRIES_PATH)

    date_min = df_period["InvoiceDate"].min().date()
    date_max = df_period["InvoiceDate"].max().date()
    n_products = len(df_period[["StockCode", "Description"]].drop_duplicates())
    n_countries = df_period["Country"].nunique()

    print("\n=== 分割結果 ===")
    print(f"期間: {date_min} 〜 {date_max}")
    print(f"生成ファイル数: {n_files} 件")
    print(f"総行数: {len(df_period):,} 行")
    print(f"出力先: {TRANSACTIONS_DIR}/")
    print(f"商品マスタ: {PRODUCTS_PATH} ({n_products} 件)")
    print(f"国マスタ: {COUNTRIES_PATH} ({n_countries} 件)")


if __name__ == "__main__":
    main()
