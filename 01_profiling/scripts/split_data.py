from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent.parent.parent / "data"  # プロジェクトルートの data/
RAW_XLSX = DATA_DIR / "Online_Retail.xlsx"
TRANSACTIONS_DIR = DATA_DIR / "transactions"
PRODUCTS_PATH = DATA_DIR / "products.csv"
COUNTRIES_PATH = DATA_DIR / "countries.csv"

TARGET_YEAR = 2010
TARGET_MONTH = 12


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


def filter_by_month(df: pd.DataFrame, year: int, month: int) -> pd.DataFrame:
    """指定年月のデータのみ抽出して返す。

    Args:
        df: 対象 DataFrame。InvoiceDate 列が datetime 型であること。
        year: 抽出する年。
        month: 抽出する月。

    Returns:
        指定年月のデータのみを含む DataFrame のコピー。
    """
    mask = (df["InvoiceDate"].dt.year == year) & (df["InvoiceDate"].dt.month == month)
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

    df_month = filter_by_month(df, TARGET_YEAR, TARGET_MONTH)
    print(f"Rows in {TARGET_YEAR}-{TARGET_MONTH:02d}: {len(df_month):,}")

    n_files = split_by_date(df_month, TRANSACTIONS_DIR)
    extract_products(df_month, PRODUCTS_PATH)
    extract_countries(df_month, COUNTRIES_PATH)

    date_min = df_month["InvoiceDate"].min().date()
    date_max = df_month["InvoiceDate"].max().date()
    n_products = len(df_month[["StockCode", "Description"]].drop_duplicates())
    n_countries = df_month["Country"].nunique()

    print("\n=== 分割結果 ===")
    print(f"期間: {date_min} 〜 {date_max}")
    print(f"生成ファイル数: {n_files} 件")
    print(f"総行数: {len(df_month):,} 行")
    print(f"出力先: {TRANSACTIONS_DIR}/")
    print(f"商品マスタ: {PRODUCTS_PATH} ({n_products} 件)")
    print(f"国マスタ: {COUNTRIES_PATH} ({n_countries} 件)")


if __name__ == "__main__":
    main()
