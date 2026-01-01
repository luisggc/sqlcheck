{{ assess(lambda r: r.stdout == "ok" and "warn" in r.stderr) }}

SELECT 1;
