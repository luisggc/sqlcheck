{{ assess(lambda r: (not r.success) and "does_not_exist" in r.stderr) }}

SELECT * FROM does_not_exist;
