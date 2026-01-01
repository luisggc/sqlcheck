{{ assess(lambda r: (not r.success) and "boom" in r.stderr) }}

SELECT 1;
