{{ success() }}

CREATE OR REPLACE TABLE test_n1 (id INT);
INSERT INTO test_n1 VALUES (1), (2);
SELECT * FROM test_n1 ORDER BY id;
