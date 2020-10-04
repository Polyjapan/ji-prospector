from django.db import transaction

from .models import Event


def current_event(request):
    try:
        with transaction.atomic():
            e = Event.objects.select_for_update().get(current=True)
    except Event.DoesNotExist:
        e = None
    return {"current_event": e}
