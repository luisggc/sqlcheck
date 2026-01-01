{{ assess(check="statement_count == 2 && statements[0].contains('SELECT 1') && statements[1].contains('SELECT 2') && rows.size() == 1 && rows[0][0] == 3 && returncode == 0") }}

SELECT 3;
SELECT 2;
