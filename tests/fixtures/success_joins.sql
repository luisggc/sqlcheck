{{ success(name="joins and aggregates") }}

CREATE TABLE customers (id INT, name VARCHAR);
CREATE TABLE orders (id INT, customer_id INT, amount INT);

INSERT INTO customers VALUES (1, 'Ada'), (2, 'Lin'), (3, 'Ken');
INSERT INTO orders VALUES (1, 1, 40), (2, 1, 25), (3, 2, 10), (4, 3, 100);

WITH totals AS (
  SELECT customer_id, SUM(amount) AS total
  FROM orders
  GROUP BY customer_id
)
SELECT c.name, t.total
FROM customers c
JOIN totals t ON c.id = t.customer_id
WHERE t.total >= 50
ORDER BY t.total DESC;
