{{ assess(check="status == 'fail' && stderr.contains('does_not_exist')") }}

SELECT * FROM does_not_exist;
