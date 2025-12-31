{{ fail(name="basic insert") }}

CREATE TABLE t (id notexistanttype);
INSERT INTO t VALUES (1);
SELECT * FROM t;
