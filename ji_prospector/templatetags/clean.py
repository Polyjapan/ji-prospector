from django import template

import re

register = template.Library()

@register.filter(name='clean')
def clean(s):
    # Remove illegal characters
    s = re.sub('[^0-9A-Za-zÀ-ÖØ-öø-ÿ_]', '', s)

    # Make it start with _ or alphanumeric
    s = re.sub('^[^a-zA-Za-zÀ-ÖØ-öø-ÿ_]+', '', s)

    return s
