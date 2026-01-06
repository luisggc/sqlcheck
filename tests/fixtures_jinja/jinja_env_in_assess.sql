-- Use env inside a CEL expression via Jinja interpolation
{{ assess(match="'" ~ env ~ "' == 'dev'") }}
SELECT 1;
