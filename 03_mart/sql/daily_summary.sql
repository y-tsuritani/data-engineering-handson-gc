-- 日別×国別 集計ビュー
-- sales_amount > 0 で UnitPrice=0 行（無償提供品）を除外
CREATE OR REPLACE VIEW `${PROJECT_ID}.de_handson.v_daily_summary` AS
SELECT
  DATE(InvoiceDate)              AS invoice_date,
  Country,
  SUM(sales_amount)              AS total_sales_amount,
  SUM(Quantity)                  AS total_quantity,
  COUNT(DISTINCT InvoiceNo)      AS transaction_count,
  -- NULL（ゲスト購入）は COUNT(DISTINCT) から除外される
  COUNT(DISTINCT CustomerID)     AS unique_customers
FROM
  `${PROJECT_ID}.de_handson.transactions`
WHERE
  sales_amount > 0
GROUP BY
  invoice_date,
  Country
ORDER BY
  invoice_date,
  total_sales_amount DESC;
