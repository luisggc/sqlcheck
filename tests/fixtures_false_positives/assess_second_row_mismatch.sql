{{ assess(name="assess second row mismatch", match="rows[1][0] == 5") }}
SELECT 10
UNION ALL
SELECT 11;
