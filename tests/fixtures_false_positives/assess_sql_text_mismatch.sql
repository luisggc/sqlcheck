{{ assess(name="assess sql text mismatch", match="sql.contains('FROM does_not_exist')") }}
SELECT 10;
