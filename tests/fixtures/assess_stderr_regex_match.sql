{{ assess(check="status == 'fail' && stderr.matches('.*does_not_exist.*')") }}

SELECT * FROM does_not_exist;
