from django import template
from django.apps import apps as django_apps
from django_fresh_models.library import FreshFilterLibrary

register = template.Library()

@register.filter(name='fresh')
def fresh(instance, argument=None):
    ff = FreshFilterLibrary()
    return ff.do_filter(instance, argument)

# This is just here because calling get_X_display is so ugly and shitty, that it kills me.
@register.filter(name='model_choice')
def model_choice(instance, fieldname):
    return getattr(instance, 'get_{}_display'.format(fieldname.lower()))()

# This is the same, but it accepts a string and lets you specify which mapping of which field of which model you want.
@register.filter(name='choice')
def choice(db_text, argument):
    app_name, model_class_name, field_name = argument.split('.')
    choices = django_apps.get_app_config(app_name).get_model(model_class_name)._meta.get_field(field_name).choices

    if not choices:
        return db_text
    for db, display in choices:
        if db_text == db:
            return display
    return db_text
