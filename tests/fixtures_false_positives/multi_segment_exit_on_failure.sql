{{ assess(match="rows[0][0] == 2", exit_on_failure=False) }}
SELECT 1;
{{ assess(match="rows[0][0] == 1") }}
SELECT 1;
