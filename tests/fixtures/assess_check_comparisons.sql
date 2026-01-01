{{ assess(check="returncode == 0 && duration_s > 0 && rows[0][0] >= 5") }}

SELECT 5;
