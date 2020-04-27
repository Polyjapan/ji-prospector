from django import template
from django.apps import apps as django_apps
from django.utils.safestring import mark_safe
from django.utils.timezone import now

from prospector.templatetags.model_filters import mf as prospector_mf_library

from datetime import timedelta, datetime

register = template.Library()

@register.filter(name='model')
def model(instance, argument=None):
    return prospector_mf_library.filter(instance, argument)

# This is just here because calling get_X_display is so ugly and shitty, that it kills me.
@register.filter(name='model_display')
def model_display(instance, fieldname):
    return getattr(instance, 'get_{}_display'.format(fieldname.lower()))()

# This is the same, but it accepts a string and lets you specify which mapping of which model you want.
@register.filter(name='display')
def display(db_text, argument):
    app_name, model_class_name, field_name = argument.split(',')
    klass = django_apps.get_app_config(app_name).get_model(model_class_name)
    return getattr(klass, 'get_{}_display'.format(field_name.lower()))()

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
