{{ assess(check="statement_count == 2 && statements[0].contains('SELECT 3') && statements[1].contains('SELECT 2')") }}

SELECT 3;
SELECT 2;
