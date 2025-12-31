{{ success(name="cte with filtering") }}

CREATE TABLE metrics (id INT, value INT);
INSERT INTO metrics VALUES (1, 10), (2, 20), (3, 5), (4, 30);

WITH ranked AS (
  SELECT id, value, RANK() OVER (ORDER BY value DESC) AS rnk
  FROM metrics
)
SELECT id, value
FROM ranked
WHERE rnk <= 2
ORDER BY value DESC;
