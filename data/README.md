# データのダウンロード手順

このディレクトリにはデータファイルは含まれていません。以下の手順でデータを準備してください。

## Online_Retail.xlsx のダウンロード

1. UCI Machine Learning Repository のページを開く  
   <https://doi.org/10.24432/C5BW33>

2. ページ内の **Download** ボタンから `Online Retail.xlsx` をダウンロード

3. ダウンロードしたファイルをこのディレクトリに配置し、名前を変更する

```bash
mv ~/Downloads/Online\ Retail.xlsx data/Online_Retail.xlsx
```

## 配置後のディレクトリ構成

```
data/
└── Online_Retail.xlsx   ← ここに配置
```

`split_data.py` を実行すると、以下が自動生成されます。

```
data/
├── Online_Retail.xlsx
├── transactions/
│   ├── transactions_2010-12-01.csv
│   ├── transactions_2010-12-02.csv
│   └── ...（約20〜25ファイル）
├── products.csv
└── countries.csv
```

## データ出典

Chen, D. (2015). Online Retail [Dataset]. UCI Machine Learning Repository.  
<https://doi.org/10.24432/C5BW33>  
ライセンス: CC BY 4.0
