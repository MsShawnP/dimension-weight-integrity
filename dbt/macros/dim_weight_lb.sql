{% macro dim_weight_lb(length_in, width_in, height_in, divisor) %}
{# FedEx/UPS round each fractional dimension up to nearest whole inch
   before computing DIM weight. Source: carrier official docs, Aug 2025. #}
    (ceil({{ length_in }}) * ceil({{ width_in }}) * ceil({{ height_in }})) / {{ divisor }}::numeric
{% endmacro %}
