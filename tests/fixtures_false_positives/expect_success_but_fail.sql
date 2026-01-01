{{ assess(lambda r: r.success, name="expect success but fails") }}
SELECT * FROM does_not_exist;
