{% macro ltl_rate_lookup(class_expr) %}
    case {{ class_expr }}
        {% for class_key, rate in var('ltl_rate_per_cwt').items() %}
        when {{ class_key }} then {{ rate }}
        {% endfor %}
    end
{% endmacro %}

{% macro parcel_rate_lookup(weight_expr) %}
    case {{ weight_expr }}
        {% for weight_key, rate in var('parcel_rate_per_lb').items() %}
        when {{ weight_key }} then {{ rate }}
        {% endfor %}
        else {{ var('parcel_rate_fallback') }}
    end
{% endmacro %}
