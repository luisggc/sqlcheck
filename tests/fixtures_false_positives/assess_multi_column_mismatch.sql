{{ assess(name="assess multi column mismatch", match="rows[0][0] == 5 && rows[0][1] == 20") }}
SELECT 10, 20;
