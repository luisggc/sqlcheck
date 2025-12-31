{{ 
    fail(
        name="basic failure",
        error_contains="type"
    )
}}

CREATE TABLE test_n2 (id notexistanttype);
INSERT INTO test_n2 VALUES (1);
SELECT * FROM test_n2;
