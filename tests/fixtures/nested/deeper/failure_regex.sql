{{ assess(lambda r: (not r.success) and "syntax" in r.stderr.lower()) }}

SELECT FROM;
