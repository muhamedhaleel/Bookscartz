from django import template

register = template.Library()

@register.filter
def subtract(value, arg):
    """Subtract the arg from the value"""
    try:
        return value - arg
    except (ValueError, TypeError):
        return value

@register.filter
def multiply(value, arg):
    return float(value) * float(arg) 