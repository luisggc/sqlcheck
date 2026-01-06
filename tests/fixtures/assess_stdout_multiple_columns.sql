{{ assess(check="stdout.contains('ID') && stdout.contains('NAME') && stdout.contains('42') && stdout.contains('Alice')") }}

SELECT 42 AS ID, 'Alice' AS NAME;
