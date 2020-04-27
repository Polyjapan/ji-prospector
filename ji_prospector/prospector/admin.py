from django.contrib import admin

from .models import Event, BoothSpace, Contact, Deal, TaskType, Task, LogisticalNeedSet, EmailAddress

# Register your models here.
admin.site.register(Event)
admin.site.register(BoothSpace)
admin.site.register(Contact)
admin.site.register(Deal)
admin.site.register(TaskType)
admin.site.register(Task)
admin.site.register(LogisticalNeedSet)
admin.site.register(EmailAddress)
