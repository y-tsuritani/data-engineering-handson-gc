CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.de_handson.transactions` (
  InvoiceNo     STRING    NOT NULL,
  StockCode     STRING    NOT NULL,
  Description   STRING,
  Quantity      INT64     NOT NULL,
  InvoiceDate   TIMESTAMP NOT NULL,
  UnitPrice     FLOAT64   NOT NULL,
  CustomerID    STRING,
  Country       STRING    NOT NULL,
  sales_amount  FLOAT64   NOT NULL
)
PARTITION BY DATE(InvoiceDate)
OPTIONS (
  require_partition_filter = FALSE
);
