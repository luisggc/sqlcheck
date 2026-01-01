{{ fail(match="'does_not_exist' in error_message") }}

SELECT * FROM does_not_exist;
