{{
    assess(
        lambda r: (not r.success) and "type" in r.stderr,
        name="basic failure"
    )
}}

CREATE TABLE test_n2 (id notexistanttype);
INSERT INTO test_n2 VALUES (1);
SELECT * FROM test_n2;
