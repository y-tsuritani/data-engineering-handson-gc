CREATE OR REPLACE VIEW `${PROJECT_ID}.de_handson.v_weekday_pattern` AS
SELECT
  FORMAT_DATE('%A', DATE(InvoiceDate))  AS day_of_week,
  EXTRACT(DAYOFWEEK FROM InvoiceDate)   AS day_num,  -- 日=1, 月=2 ... 土=7
  SUM(sales_amount)                     AS total_sales_amount,
  COUNT(DISTINCT InvoiceNo)             AS transaction_count
FROM
  `${PROJECT_ID}.de_handson.transactions`
WHERE
  sales_amount > 0
GROUP BY
  day_of_week,
  day_num
ORDER BY
  day_num;
