{% macro density_to_nmfc_class(density_lb_per_ft3) %}
{# NMFTA Docket 2025-1 (effective July 2025) — 18 density-based classes.
   Classes 50 and 55 added in 2025. Breakpoints are lower bounds (>=). #}
    case
        when {{ density_lb_per_ft3 }} >= 50.0  then 50
        when {{ density_lb_per_ft3 }} >= 35.0  then 55
        when {{ density_lb_per_ft3 }} >= 22.5  then 60
        when {{ density_lb_per_ft3 }} >= 15.0  then 65
        when {{ density_lb_per_ft3 }} >= 13.5  then 70
        when {{ density_lb_per_ft3 }} >= 12.0  then 77.5
        when {{ density_lb_per_ft3 }} >= 10.5  then 85
        when {{ density_lb_per_ft3 }} >= 9.0   then 92.5
        when {{ density_lb_per_ft3 }} >= 8.0   then 100
        when {{ density_lb_per_ft3 }} >= 7.0   then 110
        when {{ density_lb_per_ft3 }} >= 6.0   then 125
        when {{ density_lb_per_ft3 }} >= 5.0   then 150
        when {{ density_lb_per_ft3 }} >= 4.0   then 175
        when {{ density_lb_per_ft3 }} >= 3.0   then 200
        when {{ density_lb_per_ft3 }} >= 2.0   then 250
        when {{ density_lb_per_ft3 }} >= 1.0   then 300
        when {{ density_lb_per_ft3 }} >= 0.5   then 400
        else 500
    end
{% endmacro %}
