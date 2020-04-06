from django import template
from django.utils.safestring import mark_safe
from django.utils.timezone import now

from prospector.templatetags.model_filters import mf as prospector_mf_library

from datetime import timedelta, datetime

register = template.Library()

@register.filter(name='model')
def model(instance, argument=None):
    return prospector_mf_library.filter(instance, argument)

# This is just here because calling get_X_display is so ugly and shitty, that it kills me.
@register.filter(name='display')
def display(instance, fieldname):
    return getattr(instance, 'get_{}_display'.format(fieldname.lower()))()

@register.filter(name='past')
def past(date):
    return now() > date if date else False

@register.filter(name='orcross', is_safe=True)
def orcross(value):
    if value:
        return value
    else:
        return mark_safe('<span><i class="icon icon-cross"></i></span>')

@register.filter(name='orcheck', is_safe=True)
def orcheck(value):
    if value:
        return value
    else:
        return mark_safe('<span><i class="icon icon-check"></i></span>')

@register.filter(name='oredit', is_safe=True)
def oredit(value, url):
    if value:
        return value
    else:
        return mark_safe('<span><a href="{}" class="icon icon-edit"></a></span>'.format(url))

@register.filter(name='checkorcross', is_safe=True)
def checkorcross(value):
    if value:
        return mark_safe('<span><i class="icon icon-check"></i></span>')
    else:
        return mark_safe('<span><i class="icon icon-cross"></i></span>')

@register.filter(name='checkorempty', is_safe=True)
def checkorempty(value):
    if value:
        return mark_safe('<span><i class="icon icon-check"></i></span>')
    else:
        return mark_safe('')
