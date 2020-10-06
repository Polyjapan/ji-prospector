from django import template
from django.utils.html import format_html
from django.utils.timezone import now
from django.utils.timesince import timesince, timeuntil

from datetime import timedelta

register = template.Library()


@register.filter(name="price")
def price(text):
    return format_html("{}<small>CHF</small>", text)


@register.filter(name="plus")
def plus(number):
    return '+{}'.format(number) if number > 0 else number


@register.filter(name="todo_state_color")
def todo_state_color(str):
    colors = {
        "5_contact_waits_pro": "error",
        "4_pro_waits_treasury": "warning",
        "3_pro_waits_presidence": "warning",
        "2_pro_waits_contact": "gray",
        "1_doing": "success",
        "0_done": "success",
    }
    return colors.get(str)


@register.filter(name="todo_state_short")
def todo_state_short(str):
    translation = [
        ("0_done", "Terminé"),
        ("1_doing", "En cours"),
        ("2_pro_waits_contact", "Attente C"),
        ("3_pro_waits_presidence", "Attente P"),
        ("4_pro_waits_treasury", "Attente T"),
        ("5_contact_waits_pro", "À faire"),
    ]

    for mapping in translation:
        if str == mapping[0]:
            return mapping[1]
    return ""


@register.filter(name="deadline_color")
def deadline_color(deadline):
    if not deadline:
        return "gray"

    delta = deadline - now()
    if delta > timedelta(weeks=2):
        return "default"
    elif delta > timedelta(weeks=1):
        return "gray"  # TODO: doesn't work
    elif delta > timedelta(seconds=1):
        return "warning"
    else:
        return "error"


@register.filter(name="deadline", is_safe=True)
def deadline(then):
    if not then:
        return ""

    if now() < then:
        return format_html(
            '<span class="label label-{}">{}</span>',
            deadline_color(then),
            "dans {}".format(timeuntil(then)).split(",")[0],
        )
    else:
        return format_html(
            '<span class="label label-{}">{}</span>',
            deadline_color(then),
            "il y a {} !".format(timesince(then)).split(",")[0],
        )


@register.filter(name="sincecolor")
def sincecolor(date):
    if not date:
        return "gray"

    delta = now() - date
    if delta < timedelta(weeks=2):
        return "default"
    elif delta < timedelta(weeks=3):
        return "warning"
    else:
        return "error"


@register.filter(name="since", is_safe=True)
def since(then):
    if not then:
        return ""

    return format_html(
        '<span class="label label-{color}">{text}</span>',
        color=sincecolor(then),
        text="depuis {}".format(timesince(then)).split(",")[0],
    )
