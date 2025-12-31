{{ success(name="window functions") }}

CREATE TABLE events (id INT, category VARCHAR, ts INT);
INSERT INTO events VALUES
  (1, 'alpha', 100),
  (2, 'alpha', 105),
  (3, 'beta', 101),
  (4, 'beta', 106),
  (5, 'beta', 110);

SELECT
  category,
  ts,
  ROW_NUMBER() OVER (PARTITION BY category ORDER BY ts) AS rn,
  SUM(ts) OVER (PARTITION BY category) AS category_sum
FROM events
ORDER BY category, ts;
