# Part 3: 集計マート構築と Looker Studio 可視化

BigQuery の `transactions` テーブルからビューを作成し、Looker Studio でダッシュボードを構築します。

## 前提条件

- Part 2 が完了していること（`de_handson.transactions` に 41,753 行が存在する）
- Looker Studio アカウント（Google アカウントで即時利用可）

## 作成するビュー

| ビュー名 | 用途 |
|----------|------|
| `v_daily_summary` | 日別×国別の売上・取引数集計（グラフ1・3の入力） |
| `v_weekday_pattern` | 曜日別の売上・取引数集計（グラフ2の入力） |

## ビューの作成

```bash
# v_daily_summary
bq query --use_legacy_sql=false \
  "$(sed "s/\${PROJECT_ID}/${GOOGLE_CLOUD_PROJECT}/g" 03_mart/sql/daily_summary.sql)"

# v_weekday_pattern
bq query --use_legacy_sql=false \
  "$(sed "s/\${PROJECT_ID}/${GOOGLE_CLOUD_PROJECT}/g" 03_mart/sql/weekday_pattern.sql)"
```

または BigQuery コンソールのクエリエディタで `${PROJECT_ID}` を実際のプロジェクト ID に置換して実行。

## 動作確認

ビュー作成後に以下のクエリで結果を確認します。

**日別集計（20行返れば正常）**

```sql
SELECT
  invoice_date,
  COUNT(*)                          AS country_count,
  ROUND(SUM(total_sales_amount), 2) AS daily_total
FROM `YOUR_PROJECT_ID.de_handson.v_daily_summary`
GROUP BY invoice_date
ORDER BY invoice_date;
```

期待値: 20行（2010-12-01〜12-23、土曜3日を除く）

**国別合計（上位10カ国）**

```sql
SELECT
  Country,
  ROUND(SUM(total_sales_amount), 2) AS country_total,
  SUM(transaction_count)            AS transactions
FROM `YOUR_PROJECT_ID.de_handson.v_daily_summary`
GROUP BY Country
ORDER BY country_total DESC
LIMIT 10;
```

期待値: United Kingdom が圧倒的1位

**曜日別パターン（6行返れば正常）**

```sql
SELECT
  day_of_week,
  day_num,
  ROUND(total_sales_amount, 2) AS sales,
  transaction_count
FROM `YOUR_PROJECT_ID.de_handson.v_weekday_pattern`
ORDER BY day_num;
```

期待値: 6行（土曜日は取引ゼロのため GROUP BY に現れない）

## Looker Studio ダッシュボード

### BigQuery への接続

1. [Looker Studio](https://lookerstudio.google.com/) を開き「作成」→「レポート」を選択
2. データソースに「BigQuery」を選択
3. プロジェクト `YOUR_PROJECT_ID` → データセット `de_handson` → `v_daily_summary` を選択して接続

### グラフ構成

| # | グラフ種類 | データソース | ディメンション | 指標 |
|---|-----------|-------------|----------------|------|
| 1 | 折れ線グラフ | `v_daily_summary` | `invoice_date` | `total_sales_amount` |
| 2 | 棒グラフ | `v_weekday_pattern` | `day_of_week`（`day_num` 昇順ソート） | `total_sales_amount` |
| 3 | 横棒グラフ | `v_daily_summary` | `Country`（上位10件） | `total_sales_amount` |

### 注意事項

- グラフ2（曜日別）は土曜日の行が `v_weekday_pattern` に存在しないため、棒グラフに土曜の棒が表示されません
- グラフ2の `day_of_week` をアルファベット順ではなく曜日順に並べるには、並び替えに `day_num` を指定してください
- `unique_customers` は `CustomerID` が NULL のゲスト購入を除外してカウントしています
