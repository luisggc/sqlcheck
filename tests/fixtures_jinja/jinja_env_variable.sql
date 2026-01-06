-- Test using env variable in multiple contexts
{{ success(name="test on " ~ env ~ " environment") }}
{{ assess(match="rows[0][0] == 1") }}

CREATE TABLE {{ env }}_test_data (id INT);
INSERT INTO {{ env }}_test_data VALUES (1);
SELECT * FROM {{ env }}_test_data;
