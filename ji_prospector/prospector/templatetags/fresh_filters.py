from django.utils.html import format_html
from django.utils.timezone import now, make_aware, is_aware
from django.utils.timesince import timesince, timeuntil
from django.urls import reverse
from django import template

from django_fresh_models.library import FreshFilterLibrary

from prospector.models import Contact, Deal, Task, TaskLog, BoothSpace, TaskType, Event
import prospector.templatetags.filters as normal_filters

ff = FreshFilterLibrary()

@ff.filter(type(None))
def none(inst, argument):
    return ''

@ff.filter(Contact)
def contact(inst, argument):
    url = reverse('prospector:contacts.show', args=[inst.pk])
    string = inst.person_name

    if argument == 'url':
        return url
    elif argument == 'a':
        return format_html('<a href="{}">{}</a>', url, string)
    else:
        return string

@ff.filter(Event)
def events(inst, argument):
    url = reverse('prospector:events.show', args=[inst.pk])
    string = inst.name

    if argument == 'url':
        return url
    elif argument == 'a':
        return format_html('<a href="{}">{}</a>', url, string)
    else:
        return string

@ff.filter(TaskType)
def tasktype(inst, argument):
    url = reverse('prospector:tasktypes.show', args=[inst.pk])
    string = inst.name

    if argument == 'url':
        return url
    elif argument == 'a':
        return format_html('<a href="{}">{}</a>', url, string)
    else:
        return string

@ff.filter(BoothSpace)
def boothspace(inst, argument):
    url = 'plan.polyjapon.ch/du/cul'
    string = '{} ({})'.format(inst.name, inst.building)

    if argument == 'url':
        return url
    elif argument == 'a':
        return format_html('<a href="{}">{}</a>', url, string)
    else:
        return string

@ff.filter(Deal)
def deal(inst, argument):
    url = reverse('prospector:deals.show', args=[inst.pk])
    string = inst.booth_name

    if argument == 'url':
        return url
    elif argument == 'a':
        return format_html('<a href="{}">{}</a>', url, string)
    elif argument == 'price':
        t = normal_filters.price(inst.price)
        if inst.additional_price_exists:
            return format_html('{}(+{})', t, inst.additional_price_sum if inst.additional_price_sum else inst.additional_price_modalities)
        return t
    elif argument == 'boothspaces_price':
        t = ''
        if inst.dealboothspace_set.exists():
            t = normal_filters.price('pleasefixfilter')
        return t
    else:
        return string

@ff.filter(Task)
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
    elif argument == 'todo_state':
        t = format_html('<span class="label label-{}">{}</span>',
            normal_filters.todo_state_color(inst.todo_state),
            inst.get_todo_state_display()
        )
        return t
    elif argument == 'deadline':
        if not inst.deadline or inst.todo_state == '0_done':
            return ''

        if now() < inst.deadline:
            return 'dans {}'.format(timeuntil(inst.deadline).split(',')[0])
        else:
            return 'il y a {}'.format(timesince(inst.deadline).split(',')[0])
    else:
        return string

@ff.filter(TaskLog)
def tasklog(inst, argument):
    if argument == 'old_todo_state':
        t = format_html('<span class="label label-{}">{}</span>',
            ff.do_filter(inst, 'old_todo_state_color'),
            inst.get_old_todo_state_display()
        )
        return t
    elif argument == 'new_todo_state':
        t = format_html('<span class="label label-{}">{}</span>',
            ff.do_filter(inst, 'new_todo_state_color'),
            inst.get_new_todo_state_display()
        )
        return t
    elif argument == 'old_todo_state_color' or argument == 'new_todo_state_color':
        colors = {
            '5_contact_waits_pro': 'error',
            '4_pro_waits_treasury': 'warning',
            '3_pro_waits_presidence': 'warning',
            '2_pro_waits_contact': 'default',
            '1_doing': 'success',
            '0_done': 'success',
        }
        if argument == 'old_todo_state_color':
            return colors.get(inst.old_todo_state)
        else:
            return colors.get(inst.new_todo_state)
    else:
        return ''
