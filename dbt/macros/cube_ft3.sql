{% macro cube_ft3(length_in, width_in, height_in) %}
    ({{ length_in }} * {{ width_in }} * {{ height_in }}) / 1728.0
{% endmacro %}
