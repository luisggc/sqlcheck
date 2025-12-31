{{ 
    fail(
        name="basic failure",
        error_contains="Catalog Error: Type with name notexistanttype does not exist"
    )
}}

CREATE TABLE t (id notexistanttype);
INSERT INTO t VALUES (1);
SELECT * FROM t;
