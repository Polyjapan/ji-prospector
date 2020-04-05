from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic.detail import SingleObjectMixin
from django.db import transaction
from django.db.models import Sum, Min, Max, Count, FilteredRelation, Q, F, Subquery, OuterRef
from django.db.models.fields import DateTimeField, Field
from django.utils.timezone import is_aware, make_aware
from django.contrib import messages
from django.http import HttpResponse
from django.utils.safestring import mark_safe


from .models import Contact, Deal, Task, BoothSpace, TaskType, Event
from .forms import QuickTaskForm, QuickStartForm

from collections import namedtuple

def show_model_data(cls, instance, exclude=[]):
    fs = cls._meta.get_fields(include_hidden=False)
    ret = dict()

    for f in fs:
        if not isinstance(f, Field) or f.name == 'id' or f.name in exclude:
            continue

        display_name = ''
        value = None
        display_value = ''
        if f.is_relation:
            if f.many_to_many or f.one_to_many:
                set = getattr(instance, f.name)
                for related in set.all():
                    display_value += mark_safe('<a href="{}">{}</a>, '.format(related.get_absolute_url(), related))
                display_name = f.verbose_name or f.related_model._meta.verbose_name_plural.capitalize()
                value = set
            else:
                related = getattr(instance, f.name)
                if related:
                    display_value = mark_safe('<a href="{}">{}</a>'.format(related.get_absolute_url(), related))
                display_name = f.verbose_name or f.related_model._meta.verbose_name.capitalize()
                value = related
        else:
            display_value = getattr(instance, 'get_'+f.name+'_display', getattr(instance, f.name))
            display_name = f.verbose_name
            value = getattr(instance, f.name)

        ret[f.name] = {
            'display_name': display_name,
            'value': value,
            'display_value': display_value
        }

    return ret


def quickstart(request):
    if request.method == "GET":
        form = QuickStartForm(request.GET)
        if form.is_valid():
            if form.cleaned_data['what']:
                try:
                    obj = TaskType.objects.get(name=form.cleaned_data['what'])
                    return redirect(reverse('prospector:tasktypes.show', args=(obj.pk,)))
                except TaskType.DoesNotExist:
                    pass

                try:
                    obj = Deal.objects.get(booth_name=form.cleaned_data['what'])
                    return redirect(reverse('prospector:deals.show', args=(obj.pk,)))
                except Deal.DoesNotExist:
                    messages.error(request, mark_safe('Il n\'y a ni type de tâche, ni deal nommé <i>{}</i>.'.format(form.cleaned_data['what'])))
                    return redirect(reverse('prospector:index'))

    return redirect(reverse('prospector:tasks.list'))


def index(request):
    """Gives overview :
    * Budget
    * Open booth spaces
    * Tasks to do and their status and their deadline
    """

    free_booths = BoothSpace.objects.filter(deal__isnull=True)

    # Yeah I know. The ORM would not let me group by one thing only. Fuck the ORM (and/or me)
    # Maybe I should just do it in <number_of_task> queries... get the tasks first, and then for each one, get the related data. but dammit... performance !!
    to_do = TaskType.objects.raw('''
SELECT
	tt.id,
	tt.name,
	d.booth_name,
	t.deadline,
    t2.deal_count,
    t2.worst_todo,
    d.id AS deal_id
FROM
	prospector_task t
	JOIN prospector_tasktype tt
	ON t.tasktype_id = tt.id
	JOIN prospector_deal d
	ON t.deal_id = d.id
	JOIN (
		SELECT MIN(deadline) as min_deadline, tasktype_id, COUNT(*) AS deal_count, MAX(todo_state) AS worst_todo
		FROM prospector_task
		WHERE todo_state <> '0_done'
		GROUP BY tasktype_id
	) t2
	ON t.tasktype_id = t2.tasktype_id
WHERE t.deadline = t2.min_deadline OR t.deadline IS NULL
ORDER BY t.deadline
    ''')

    # to_do_rows2 = TaskType.objects.annotate(
    #     booth_name=Subquery(
    #         Task.objects.exclude(todo_state='0_done').filter(tasktype_id=OuterRef('id')).order_by('deadline').values('deal__booth_name')[:1]
    #     ),
    #     deal_id=Subquery(
    #         Task.objects.exclude(todo_state='0_done').filter(tasktype_id=OuterRef('id')).order_by('deadline').values('deal_id')[:1]
    #     ),
    #     deadline=Subquery(
    #         Task.objects.exclude(todo_state='0_done').filter(tasktype_id=OuterRef('id')).order_by('deadline').values('deadline')[:1]
    #     ),
    #     deal_count=Count('task__deal'),
    #     worst_todo=Max('task__todo_state'),
    # )
    #
    # print(to_do_rows2.query)
    # print(to_do_rows2.values())

    # RawSQL-to-Model glue here :(
    for row in to_do:
        # Parse datetime just as a real model would. Throws the same exceptions, too.
        if row.deadline:
            row.deadline = DateTimeField().to_python(row.deadline)
            if not is_aware(row.deadline):
                row.deadline = make_aware(row.deadline)
        # Add in display helper for todo-state
        row.get_worst_todo_display = lambda *, row=row : dict(Task.TODO_STATES).get(row.worst_todo)

    final_budget = Deal.objects.filter(price_final=True).aggregate(Sum('price'))['price__sum'] or 0
    unsure_budget = Deal.objects.filter(price_final=False).aggregate(Sum('price'))['price__sum'] or 0

    quickstartform = QuickStartForm()

    return render(request, 'prospector/index.html', {'free_booths': free_booths, 'to_do': to_do, 'final_budget': final_budget, 'unsure_budget': unsure_budget, 'quickstartform': quickstartform})


def plan(request):
    """Helps with modifiying booth spaces and such
    * Asks to confirm that the mutex has been taken
    * Get the plan's svg somehow (make a separate function for that, as it may change)
    * Load the pro layer, link the polygons to the BoothSpaces with a svg id fioupfioup
    * Allow to do the following with booths:
        * Move (intelligently move tables as well)
        * Rename (keep links intact !)
        * Add (propose to link to a deal)
        * Remove (with correct warning if it is linked)
        * Undo/Redo
    * Saves constantly to django
    * When user is done, push back plan (another separate function), and ask user to release mutex.
    """

    return render(request, 'prospector/index.html')

def contacts_list(request):
    qs = Contact.objects.order_by('person_name')
    return render(request, 'prospector/contacts/list.html', {'qs': qs})

def contacts_show(request, pk):
    obj = Contact.objects.get(pk=pk)
    # Get all fields of this object, and their values, in a dictionary
    show_data = show_model_data(Contact, obj)
    # Get all deals related to this object
    qs = Deal.objects.filter(contact__pk=obj.pk).order_by('-event__date')
    return render(request, 'prospector/contacts/show.html', {'show_data': show_data, 'obj': obj, 'qs': qs})

def deals_list(request):
    qs = Deal.objects.order_by('booth_name')
    return render(request, 'prospector/deals/list.html', {'qs': qs})

def deals_show(request, pk):
    obj = Deal.objects.get(pk=pk)

    if request.method == "POST":
        taskform = QuickTaskForm(request.POST)
        if taskform.is_valid():
            tasktype, created = TaskType.objects.get_or_create(
                name=taskform.cleaned_data['name']
            )
            task = Task.objects.create(
                todo_state=taskform.cleaned_data['state'],
                deadline=taskform.cleaned_data['deadline'],
                deal=obj,
                tasktype=tasktype,
                comment=taskform.cleaned_data['comment'],
            )
            messages.success(request, mark_safe('Il faut maintenant <i>{}</i> pour <i>{}</i>.'.format(tasktype.name.lower(), obj.booth_name)))
            if created:
                messages.info(
                    request,
                    mark_safe('Le type de tâche <i>{}</i> a été créé car il n\'existait pas.<br><a href="{}">Voir ici</a>.'.format(
                        tasktype.name,
                        reverse('prospector:tasktypes.show', args=(tasktype.pk,))
                    ))
                )
    else:
        taskform = QuickTaskForm(initial={'state': '5_contact_waits_pro'})

    show_data = show_model_data(Deal, obj, exclude=['tasks'])
    return render(request, 'prospector/deals/show.html', {'show_data': show_data, 'obj': obj, 'taskform': taskform})

def tasktypes_list(request):
    qs = TaskType.objects.annotate(Count('task__deal')).annotate(Min('task__deadline')).order_by('task__deadline__min'), pk
    return render(request, 'prospector/tasktypes/list.html', {'qs': qs})

def tasks_list(request):
    return render(request, 'prospector/tasks/list.html')

def tasks_list_embed(request, fixed_tasktype=None, fixed_deal=None):
    qs = Task.objects.all()
    if fixed_tasktype:
        qs = qs.filter(tasktype__pk=fixed_tasktype)
    if fixed_deal:
        qs = qs.filter(deal__pk=fixed_deal)

    return render(request, 'prospector/tasks/list_embed.html', {'qs': qs, 'fixed_deal': fixed_deal, 'fixed_tasktype': fixed_tasktype})

#TODO : use good POST and form or vue or something idk
# but for now, this works.
def tasks_set_todostate(request, pk, state):
    obj = Task.objects.get(pk=pk)
    obj.todo_state = state
    obj.save()
    return HttpResponse()

def tasktypes_show(request, pk):
    obj = TaskType.objects.get(pk=pk)
    show_data = show_model_data(TaskType, obj)
    qs = Task.objects.filter(tasktype__pk=obj.pk)
    return render(request, 'prospector/tasktypes/show.html', {'show_data': show_data, 'obj': obj, 'qs': qs})

def events_list(request):
    qs = Event.objects.order_by('-date')
    return render(request, 'prospector/events/list.html', {'qs': qs})

def events_show(request, pk):
    if request.method == 'POST':
        if request.POST['what'] == 'please_make_this_current':
            old_current = Event.objects.select_for_update().filter(current=True)
            new_current = Event.objects.select_for_update().filter(pk=pk)
            with transaction.atomic():
                old_current.update(current=False)
                new_current.update(current=True)
            messages.success(request, 'L\'événement {} est maintenant actuel !'.format(new_current.get().name))

    obj = Event.objects.get(pk=pk)
    show_data = show_model_data(Event, obj)
    return render(request, 'prospector/events/show.html', {'show_data': show_data, 'obj': obj})

# TODO: Find a way to select the fanzines



# Create your views here.
