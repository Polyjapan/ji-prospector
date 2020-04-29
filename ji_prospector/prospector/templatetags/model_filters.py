from django.utils.html import format_html
from django.utils.timezone import now, make_aware, is_aware
from django.urls import reverse
from django import template

from prospector.models import Contact, Deal, Task, BoothSpace, TaskType, Event
import prospector.templatetags.filters as normal_filters

# This class aims at removing render logic from Model definitions, where it almost certainly does not belong.
# It also handles type-based dispatching.

# app.templatetags.filters defines a 'model' filter which just calls this class's filter() function directly.

class ModelFilters:
    def __init__(self):
        self.filters = {}

    def new_filter(self, model_class):
        def decorator(function):
            self.filters[model_class] = function
            return function
        return decorator

    def filter(self, model_inst, argument=None):
        return self.filters[type(model_inst)](model_inst, argument)

# To extend, simply add a new function and decorate it with @mf.new_filter(MyModelClassHere)
# Do not hesitate to call mf.filter(...) recursively if you need it. e.g. for related models.
# Normal filters are accessible too, by virtue of being simply imported under 'normal_filters'.

# Do not rename 'mf', because it is imported from app.templatetags.filters !!
mf = ModelFilters()

@mf.new_filter(NoneType)
def none(inst, argument):
    return ''

@mf.new_filter(Contact)
def contact(inst, argument):
    url = reverse('prospector:contacts.show', args=[inst.pk])
    string = inst.person_name

    if argument == 'url':
        return url
    elif argument == 'a':
        return format_html('<a href="{}">{}</a>', url, string)
    else:
        return string

@mf.new_filter(Event)
def events(inst, argument):
    url = reverse('prospector:events.show', args=[inst.pk])
    string = inst.name

    if argument == 'url':
        return url
    elif argument == 'a':
        return format_html('<a href="{}">{}</a>', url, string)
    else:
        return string

@mf.new_filter(TaskType)
def tasktype(inst, argument):
    url = reverse('prospector:tasktypes.show', args=[inst.pk])
    string = inst.name

    if argument == 'url':
        return url
    elif argument == 'a':
        return format_html('<a href="{}">{}</a>', url, string)
    else:
        return string

@mf.new_filter(BoothSpace)
def boothspace(inst, argument):
    url = 'plan.polyjapon.ch/du/cul'
    string = '{} ({})'.format(inst.name, inst.building)

    if argument == 'url':
        return url
    elif argument == 'a':
        return format_html('<a href="{}">{}</a>', url, string)
    else:
        return string

@mf.new_filter(Deal)
def deal(inst, argument):
    url = reverse('prospector:deals.show', args=[inst.pk])
    string = inst.booth_name

    if argument == 'url':
        return url
    elif argument == 'a':
        return format_html('<a href="{}">{}</a>', url, string)
    elif argument == 'price':
        t = normal_filters.price(inst.price)
        if inst.additional_price_modalities:
            format_html('{}(+{})', t, inst.additional_price_sum if inst.additional_price_sum else inst.additional_price_modalities)
        return t
    elif argument == 'boothspaces_price':
        t = ''
        if inst.boothspace_set.exists():
            t = normal_filters.price(inst.boothspaces_usual_price_sum)
        return t
    else:
        return string

@mf.new_filter(Task)
def task(inst, argument):
    url = reverse('prospector:tasktypes.show', args=[inst.tasktype.id])
    string = inst.tasktype.name

    if argument == 'url':
        return url
    elif argument == 'a':
        return format_html('<a href="{}">{}</a>', url, string)
    elif argument == 'timed_a':
        inst.deadline = None if not inst.deadline else inst.deadline if is_aware(inst.deadline) else make_aware(inst.deadline)
        t = format_html('{} <a href="{}">{}</a>',
            'Il faut' if not inst.deadline or inst.deadline > now() else 'Il fallait',
            url,
            string.lower(),
        )
        return t
    elif argument == 'todo_state_color':
        colors = {
            '5_contact_waits_pro': 'error',
            '4_pro_waits_treasury': 'warning',
            '3_pro_waits_presidence': 'warning',
            '2_pro_waits_contact': 'default',
            '1_doing': 'success',
            '0_done': 'success',
        }
        return colors.get(inst.todo_state)
    elif argument == 'todo_state':
        t = format_html('<span class="label label-{}">{}</span>',
            mf.filter(inst, 'todo_state_color'),
            inst.get_todo_state_display()
        )
        return t
    else:
        return string
