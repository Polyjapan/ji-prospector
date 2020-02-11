from django import template
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.utils.timesince import timesince, timeuntil

from datetime import timedelta, datetime

register = template.Library()

@register.filter(name='todostatecolor')
def todostatecolor(todostate):
    colors = {
        '5_contact_waits_pro': 'error',
        '4_pro_waits_treasury': 'warning',
        '3_pro_waits_presidence': 'warning',
        '2_pro_waits_contact': 'default',
        '1_doing': 'secondary',
        '0_done': 'success',
    }

    return colors.get(todostate)

@register.filter(name='deadlinecolor')
def deadlinecolor(deadline):
    if not deadline:
        return 'gray'

    delta = deadline - now()
    if delta > timedelta(weeks=2):
        return 'default'
    elif delta > timedelta(weeks=1):
        return 'gray-dark'
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
        return mark_safe(span.format(text='in {}'.format(timeuntil(then))))
    else:
        return mark_safe(span.format(text='{} ago !'.format(timesince(then))))


@register.filter(name='orcross', is_safe=True)
def orcross(value):
    if value:
        return value
    else:
        return mark_safe('<div class="text-center"><i class="icon icon-cross"></i></div>')

@register.filter(name='checkorcross', is_safe=True)
def checkorcross(value):
    if value:
        return mark_safe('<div class="text-center"><i class="icon icon-check"></i></div>')
    else:
        return mark_safe('<div class="text-center"><i class="icon icon-cross"></i></div>')
