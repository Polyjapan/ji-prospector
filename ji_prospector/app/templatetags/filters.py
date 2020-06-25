from django import template
from django.apps import apps as django_apps
from django.utils.safestring import mark_safe
from django.utils.timezone import now

from datetime import timedelta, datetime

register = template.Library()

@register.filter(name='or_edit', is_safe=True)
def or_edit(value, url):
    if value:
        return value
    else:
        return mark_safe('<span><a href="{}" class="icon icon-edit"></a></span>'.format(url))

@register.filter(name='past')
def past(date):
    return now() > date if date else False

@register.filter(name='or_cross', is_safe=True)
def or_cross(value):
    if value:
        return value
    else:
        return mark_safe('<span><i class="icon icon-cross"></i></span>')

@register.filter(name='or_check', is_safe=True)
def or_check(value):
    if value:
        return value
    else:
        return mark_safe('<span><i class="icon icon-check"></i></span>')

@register.filter(name='check_or_cross', is_safe=True)
def check_or_cross(value):
    if type(value) != bool:
        return value
    if value:
        return mark_safe('<span><i class="icon icon-check"></i></span>')
    else:
        return mark_safe('<span><i class="icon icon-cross"></i></span>')

@register.filter(name='then_check', is_safe=True)
def then_check(value):
    if value:
        return mark_safe('<span><i class="icon icon-check"></i></span>')
    else:
        return ''

@register.filter(name='then_cross', is_safe=True)
def then_cross(value):
    if value:
        return mark_safe('<span><i class="icon icon-cross"></i></span>')
    else:
        return ''
