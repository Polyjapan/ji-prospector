from django.contrib import admin

from .models import Event, BoothSpace, Contact, Deal, TaskType, Task, TaskLog, TaskComment, LogisticalNeedSet

# Register your models here.
admin.site.register(Event)
admin.site.register(BoothSpace)
admin.site.register(Contact)
admin.site.register(Deal)
admin.site.register(TaskType)
admin.site.register(TaskLog)
admin.site.register(TaskComment)
admin.site.register(Task)
admin.site.register(LogisticalNeedSet)
