from django import template
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.utils.timesince import timesince, timeuntil

from datetime import timedelta, datetime

from prospector.models import Task

register = template.Library()

@register.filter(name='price')
def price(text):
    little_chf = '<small>CHF</small>'
    return mark_safe('{}{}'.format(little_chf, text))

@register.filter(name='todostatecolor')
def todostatecolor(todostate):
    colors = {
        '5_contact_waits_pro': 'error',
        '4_pro_waits_treasury': 'warning',
        '3_pro_waits_presidence': 'warning',
        '2_pro_waits_contact': 'default',
        '1_doing': 'success',
        '0_done': 'success',
    }

    return colors.get(todostate)

@register.filter(name='todostate')
def todostate(str):
    for mapping in Task.TODO_STATES:
        if str == mapping[0]:
            return mapping[1]
    return ''

@register.filter(name='tasktodostate', is_safe=True)
def tasktodostate(task):
    if not task:
        return ''
    span = '<span class="label label-{color}">{{text}}</span>'.format(color=todostatecolor(task.todo_state))
    return mark_safe(span.format(text='{}'.format(task.get_todo_state_display())))


@register.filter(name='deadlinecolor')
def deadlinecolor(deadline):
    if not deadline:
        return 'gray'

    delta = deadline - now()
    if delta > timedelta(weeks=2):
        return 'default'
    elif delta > timedelta(weeks=1):
        return 'gray-dark'#TODO: doesn't work
    elif delta > timedelta(seconds=1):
        return 'warning'
    else:
        return 'error'

@register.filter(name='deadline', is_safe=True)
def deadline(then):
    if not then:
        return ''

    span = '<span class="label label-{color}">{{text}}</span>'.format(color=deadlinecolor(then))

    if now() < then:
        return mark_safe(span.format(text='dans {}'.format(timeuntil(then))))
    else:
        return mark_safe(span.format(text='il y a {} !'.format(timesince(then))))

@register.filter(name='sincecolor')
def sincecolor(date):
    if not date:
        return 'gray'

    delta = now() - date
    if delta < timedelta(weeks=1):
        return 'default'
    elif delta < timedelta(weeks=2):
        return 'gray-dark' #TODO: doesn't work
    elif delta < timedelta(weeks=3):
        return 'warning'
    else:
        return 'error'

@register.filter(name='since', is_safe=True)
def since(then):
    if not then:
        return ''

    span = '<span class="label label-{color}">{{text}}</span>'.format(color=sincecolor(then))
    return mark_safe(span.format(text='depuis {}'.format(timesince(then))))
