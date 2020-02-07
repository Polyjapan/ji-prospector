from django.contrib import admin

from .models import Event, BoothSpace, Contact, Deal, Task, DealTask, LogisticalNeedSet

# Register your models here.
admin.site.register(Event)
admin.site.register(BoothSpace)
admin.site.register(Contact)
admin.site.register(Deal)
admin.site.register(Task)
admin.site.register(DealTask)
admin.site.register(LogisticalNeedSet)
