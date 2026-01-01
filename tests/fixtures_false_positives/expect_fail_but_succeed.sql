{{ assess(lambda r: not r.success, name="expect fail but succeeds") }}
SELECT 1;
