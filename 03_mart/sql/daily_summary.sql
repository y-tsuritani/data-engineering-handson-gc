CREATE OR REPLACE VIEW `${PROJECT_ID}.de_handson.v_daily_summary` AS
SELECT
  DATE(InvoiceDate)              AS invoice_date,
  Country,
  SUM(sales_amount)              AS total_sales_amount,
  SUM(Quantity)                  AS total_quantity,
  COUNT(DISTINCT InvoiceNo)      AS transaction_count,
  COUNT(DISTINCT CustomerID)     AS unique_customers  -- NULL（ゲスト購入）は除外される
FROM
  `${PROJECT_ID}.de_handson.transactions`
WHERE
  sales_amount > 0  -- UnitPrice=0 行（無償提供品）を除外
GROUP BY
  invoice_date,
  Country
ORDER BY
  invoice_date,
  total_sales_amount DESC;
