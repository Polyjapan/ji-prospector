from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic.detail import SingleObjectMixin
from django.db import transaction
from django.db.models import Sum, Min, Max, Count, FilteredRelation, Q, F, Subquery, OuterRef
from django.db.models.fields import DateTimeField, Field
from django.utils.timezone import make_aware
from django.contrib import messages
from django.http import HttpResponse, HttpResponseBadRequest, Http404
from django.utils.html import format_html
from django.contrib.auth.decorators import login_required

from django_fresh_models.library import FreshFilterLibrary as ff
import safedelete

from .models import *
from .forms import *

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
                    display_value += ff.filter(related, 'a')
                display_name = f.verbose_name or f.related_model._meta.verbose_name_plural.capitalize()
                value = set
            else:
                related = getattr(instance, f.name)
                if related:
                    display_value = ff.filter(related, 'a')
                display_name = f.verbose_name or f.related_model._meta.verbose_name.capitalize()
                value = related
        else:
            display_value = getattr(instance, 'get_' + f.name + '_display', getattr(instance, f.name))
            display_name = f.verbose_name
            value = getattr(instance, f.name)

        ret[f.name] = {'display_name': display_name, 'value': value, 'display_value': display_value}

    return ret


@login_required
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
                    messages.error(request, format_html('Il n\'y a ni type de tâche, ni deal nommé <i>{}</i>.', form.cleaned_data['what']))
                    return redirect(reverse('prospector:index'))

    return redirect(reverse('prospector:tasks.list'))

@login_required
def index(request):
    """Gives overview :
    * Budget
    * Open booth spaces
    * Tasks to do and their status and their deadline
    """

    free_booths = BoothSpace.objects.filter(dealboothspace__isnull=True)

    # Yeah I know. The ORM would not let me group by one thing only. Fuck the ORM (and/or me)
    # Maybe I should just do it in <number_of_task> queries... get the tasks first, and then for each one, get the related data. but dammit... performance !!
    to_do = TaskType.objects.raw(
        '''
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
    '''
    )

    # There exists this query too, which was submitted by a dude on SO.
    # It works, although it is disgustingly inefficient.
    # I chose not to use it.

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

    # Fake models so we can use the model filters
    model_to_do = []
    for row in to_do:
        t = Task.from_db(Task.objects.all().db, ['todo_state', 'deadline', 'deal_id', 'tasktype_id'], [row.worst_todo, row.deadline, row.deal_id, row.id],)
        # Attribute specific to that query
        t.deal_count = row.deal_count
        model_to_do.append(t)

    quickstartform = QuickStartForm()

    return render(request, 'prospector/index.html', {'free_booths': free_booths, 'to_do': model_to_do, 'quickstartform': quickstartform})


@login_required
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

def list_view(model_class, templates_folder, *, archive=False):
    @login_required
    def the_view(request):
        if archive:
            qs = model_class.objects.deleted_only().order_by('deleted')
            return render(request, 'prospector/{}/archive.html'.format(templates_folder), {'qs': qs})

        qs = model_class.objects.all()
        return render(request, 'prospector/{}/list.html'.format(templates_folder), {'qs': qs})

    return the_view

def delete_view(model_class, view_prefix):
    @login_required
    def the_view(request, pk):
        obj = get_object_or_404(model_class, pk=pk)

        if request.method == 'POST':
            obj.delete()
            messages.success(request, 'Archivage effectué.')
            return redirect(reverse('prospector:{}.list'.format(view_prefix)))

        return HttpResponse()

    return the_view

def undelete_view(model_class, view_prefix):
    @login_required
    def the_view(request, pk):
        try:
            obj = model_class.objects.deleted_only().get(pk=pk)
        except Contact.DoesNotExist:
            return Http404()

        if request.method == 'POST':
            obj.save()
            messages.success(request, 'Restauration effectuée.')
            return redirect(reverse('prospector:{}.show'.format(view_prefix), args=(pk,)))

        return HttpResponse()

    return the_view


@login_required
def contacts_edit(request, pk=None, create=False):
    if create:
        obj = Contact()
    else:
        obj = get_object_or_404(Contact, pk=pk)

    if request.method == 'POST':
        form = ContactForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Modifications sauvegardées.')
            return redirect(reverse('prospector:contacts.show', args=(form.instance.pk,)))
    else:
        form = ContactForm(instance=obj)

    return render(request, 'prospector/contacts/edit.html', {'obj': obj, 'form': form, 'create': create})


@login_required
def contacts_show(request, pk):
    obj = get_object_or_404(Contact, pk=pk)
    # Get all deals related to this object
    qs = Deal.objects.filter(contact__pk=obj.pk).order_by('-event__date')
    return render(request, 'prospector/contacts/show.html', {'obj': obj, 'qs': qs})


@login_required
def events_edit(request, pk=None, create=False):
    if create:
        obj = Event()
    else:
        obj = get_object_or_404(Event, pk=pk)
        
    if request.method == 'POST':
        form = EventForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Modifications sauvegardées.')
            return redirect(reverse('prospector:events.show', args=(form.instance.pk,)))
    else:
        form = EventForm(instance=obj)
        
    return render(request, 'prospector/events/edit.html', {'obj': obj, 'form': form, 'create': create})


@login_required
def deals_edit(request, pk=None, create=False):
    if create:
        contact = get_object_or_404(Contact, pk=request.GET['from_contact']) if 'from_contact' in request.GET else None
        obj = Deal(contact=contact)
    else:
        obj = get_object_or_404(Deal, pk=pk)

    if request.method == 'POST':
        form = DealForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Modifications sauvegardées.')
            return redirect(reverse('prospector:deals.show', args=(form.instance.pk,)))
    else:
        form = DealForm(instance=obj)

    return render(request, 'prospector/deals/edit.html', {'obj': obj, 'form': form, 'create': create})


@login_required
def deals_show(request, pk):
    obj = get_object_or_404(Deal, pk=pk)

    if request.method == 'POST':
        taskform = QuickTaskForm(request.POST)
        if taskform.is_valid():
            tasktype, created = TaskType.objects.get_or_create(name=taskform.cleaned_data['name'])
            task = Task.objects.create(todo_state=taskform.cleaned_data['state'], deadline=taskform.cleaned_data['deadline'], deal=obj, tasktype=tasktype)
            messages.success(request, format_html('Il faut maintenant <i>{}</i> pour <i>{}</i>.', tasktype.name.lower(), obj.booth_name))
            if created:
                messages.info(
                    request,
                    format_html(
                        'Le type de tâche <i>{}</i> a été créé car il n\'existait pas.<br><a href="{}">Voir ici</a>.', tasktype.name, reverse('prospector:tasktypes.show', args=(tasktype.pk,))
                    ),
                )
    else:
        taskform = QuickTaskForm(initial={'state': '5_contact_waits_pro'})

    return render(request, 'prospector/deals/show.html', {'obj': obj, 'taskform': taskform})


@login_required
def deals_explaintags(request, pk):
    obj = get_object_or_404(Deal, pk=pk)
    tasks = {
        'price': obj.any_tasks_with_tag('price'),
        'boothspace': obj.any_tasks_with_tag('boothspace'),
        'contract': obj.any_tasks_with_tag('contract'),
    }
    return render(request, 'prospector/deals/explaintags.html', {'obj': obj, 'tasks': tasks})

@login_required
def deals_defaulttasks(request, pk):
    obj = get_object_or_404(Deal, pk=pk)
    if request.method == 'POST':
        types = TaskType.objects.filter(default_task_type=True)
        for type in types:
            task = Task(deal=obj, tasktype=type, todo_state='5_contact_waits_pro')
            task.save()
        return redirect(reverse('prospector:deals.show', args=(pk,)))

    return HttpResponse()


@login_required
def tasktypes_list(request):
    qs = TaskType.objects.annotate(Count('task__deal')).annotate(Min('task__deadline')).order_by('task__deadline__min')
    return render(request, 'prospector/tasktypes/list.html', {'qs': qs})


@login_required
def tasktypes_edit(request, pk=None, create=False):
    if create:
        obj = TaskType()
    else:
        obj = get_object_or_404(TaskType, pk=pk)

    if request.method == 'POST':
        form = TaskTypeForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Modifications sauvegardées.')
            return redirect(reverse('prospector:tasktypes.show', args=(form.instance.pk,)))
    else:
        form = TaskTypeForm(instance=obj)

    return render(request, 'prospector/tasktypes/edit.html', {'obj': obj, 'form': form, 'create': create})


@login_required
def tasks_list(request):
    return render(request, 'prospector/tasks/list.html')


@login_required
def tasks_history(request, pk):
    obj = get_object_or_404(Task, pk=pk)
    return render(request, 'prospector/tasks/history.html', {'obj': obj})


@login_required
def tasks_comments(request, pk):
    obj = get_object_or_404(Task, pk=pk)
    if request.method == "POST":
        form = TaskCommentForm(request.POST)
        if form.is_valid():
            TaskComment.objects.create(task=obj, author=request.user, text=form.cleaned_data['text'])
    else:
        form = TaskCommentForm()
    return render(request, 'prospector/tasks/comments.html', {'obj': obj, 'form': form})


@login_required
def tasks_delete_comment(request, pk):
    obj = get_object_or_404(TaskComment, pk=pk)
    if request.method == "POST":
        obj.delete()

    return HttpResponse()


@login_required
def tasks_list_embed(request):
    qs = Task.objects.all()
    fixed_tasktype = False
    fixed_deal = False
    if 'fixed_tasktype' in request.GET:
        fixed_tasktype = True
        qs = qs.filter(tasktype__pk=request.GET['fixed_tasktype'])
    if 'fixed_deal' in request.GET:
        fixed_deal = True
        qs = qs.filter(deal__pk=request.GET['fixed_deal'])

    return render(request, 'prospector/tasks/list_embed.html', {'qs': qs, 'fixed_deal': fixed_deal, 'fixed_tasktype': fixed_tasktype})


@login_required
def tasks_set_todostate(request, pk):
    if request.method == "POST":
        if not 'state' in request.GET:
            return HttpResponseBadRequest()
        with transaction.atomic():
            obj = Task.objects.select_for_update().get(pk=pk)
            if obj.todo_state != request.GET['state']:
                obj.todo_state_logged = False
                obj.todo_state = request.GET['state']
                obj.save()

    return HttpResponse()


@login_required
def tasks_log_todostate(request, pk):
    if request.method == "POST":
        with transaction.atomic():
            obj = Task.objects.select_for_update().get(pk=pk)
            if not obj.tasklog_set.exists():
                TaskLog.objects.create(new_todo_state=obj.todo_state, old_todo_state=None, task=obj, user=request.user)
            else:
                log = obj.tasklog_set.latest()
                if log.new_todo_state != obj.todo_state:
                    TaskLog.objects.create(new_todo_state=obj.todo_state, old_todo_state=log.new_todo_state, task=obj, user=request.user)

            obj.todo_state_logged = True
            obj.save()

    return HttpResponse()


@login_required
def tasktypes_show(request, pk):
    obj = TaskType.objects.get(pk=pk)
    show_data = show_model_data(TaskType, obj)
    qs = Task.objects.filter(tasktype__pk=obj.pk)
    return render(request, 'prospector/tasktypes/show.html', {'show_data': show_data, 'obj': obj, 'qs': qs})


@login_required
def events_list(request):
    qs = Event.objects.order_by('-date')
    return render(request, 'prospector/events/list.html', {'qs': qs})


@login_required
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
def fanzine_register(request):
    event = Event.objects.filter(current=True).get()
    obj = Fanzine()
    if request.method == 'POST':
        form = FanzineForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre inscription a été effectuée avec succès')
            return redirect('prospector:fanzines.register')
    else:
        form = FanzineForm(instance=obj)
    return render(request, 'prospector/fanzines/register.html', {'event': event, 'form': form})

@login_required
def fanzine_list(request):
    qs = Fanzine.objects.all()
    return render(request, 'prospector/fanzines/list.html', {'qs': qs})

@login_required
def fanzines_show(request, pk):
    obj = Fanzine.objects.get(pk=pk)
    show_data = show_model_data(Fanzine, obj)
    return render(request, 'prospector/fanzines/show.html', {'show_data': show_data, 'obj': obj})
    
@login_required
def fanzines_delete(request):
    Fanzine.objects.all().delete()
    return redirect(reverse('prospector:fanzines.list'))
