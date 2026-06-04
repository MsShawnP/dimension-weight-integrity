{% macro billable_weight_lb(actual_weight_lb, dim_weight_lb) %}
    ceil(greatest({{ actual_weight_lb }}, {{ dim_weight_lb }}))
{% endmacro %}
