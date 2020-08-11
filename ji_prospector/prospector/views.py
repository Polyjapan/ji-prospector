from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic.detail import SingleObjectMixin
from django.db import transaction
from django.db.models import Sum, Min, Max, Count, FilteredRelation, Q, F, Subquery, OuterRef, Avg
from django.db.models.fields import DateTimeField, Field
from django.utils.timezone import make_aware
from django.contrib import messages
from django.http import HttpResponse, HttpResponseBadRequest, Http404
from django.utils.html import format_html
from django.contrib.auth.decorators import login_required

from django_fresh_models.library import FreshFilterLibrary as ff
import safedelete
import csv, io

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

# TODO: Put it in separate file?
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
    qs = Fanzine.objects.order_by('-total_score')
    return render(request, 'prospector/fanzines/list.html', {'qs': qs})

@login_required
def fanzines_show(request, pk):
    obj = Fanzine.objects.get(pk=pk)
    show_data = show_model_data(Fanzine, obj, exclude=['total_score'])
    # Show rating
    ratings = FanzineRating.objects.filter(fanzine=pk)
    avg_score = ratings.aggregate(Avg('score'))
    show_data['score'] = {'display_name': 'Average score', 'value': avg_score, 'display_value': avg_score['score__avg']}
    return render(request, 'prospector/fanzines/show.html', {'show_data': show_data, 'obj': obj, 'qs': ratings})
    
@login_required
def fanzines_delete(request):
    Fanzine.objects.all().delete()
    return redirect(reverse('prospector:fanzines.list'))
    
@login_required
def fanzines_add(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            try:
                decoded = file.read().decode()
            except:
                messages.error(request, 'Le format du fichier n\'est pas valide')
                return redirect(reverse('prospector:fanzines.add'))
            with io.StringIO(decoded) as f:
                reader = csv.reader(f)
                next(reader) # skip header
                for row in reader:
                    if (len(row) != 27):
                        messages.error(request, 'Le contenu du fichier n\'est pas valide')
                        return redirect(reverse('prospector:fanzines.add'))
                    _, created = Fanzine.objects.get_or_create(
                        name = row[2],
                        address_street = row[3],
                        address_city = row[4],
                        age = row[5],
                        email = row[6],
                        phone_number = row[7],
                        stand_name = row[8],
                        prev_editions = row[9],
                        tables = row[10],
                        num_people = row[11],
                        stand_content = row[12],
                        logistic_needs = row[13],
                        electric_needs = row[14],
                        activities = row[15],
                        stand_description = row[16],
                        image_url = row[17],
                        second_chance = (row[18] == 'Oui'),
                        deadline = row[19],
                        deviant_url = row[20],
                        facebook_url = row[21],
                        blog_url = row[22],
                        deco = (row[23] == 'Oui'),
                        remarks = row[24]
                        )
                    assert created
                messages.success(request, 'Fanzines importées avec succès')
                return redirect(reverse('prospector:fanzines.list'))
    else:
        form = UploadFileForm()
    return render(request, 'prospector/fanzines/add.html', {'form': form})

@login_required
def fanzines_vote_start(request):
    all_fanzines = list(Fanzine.objects.all()) # We assume that the number of fanzines is not too big, which seems a reasonable assumption
    username = request.user.get_full_name()
    user_ratings = FanzineRating.objects.all().filter(user=username)
    remaining = {fz.pk for fz in all_fanzines} - {rt.fanzine.pk for rt in user_ratings}
    empty = {rt.fanzine.pk for rt in user_ratings if rt.score == 0}
    remaining = list(remaining.union(empty))
    from_start = True
    if len(remaining) != 0 and len(remaining) != len(all_fanzines):
        remaining.sort()
        next = remaining[0]
        from_start = False
    else:
        next = all_fanzines[0].pk
    return render(request, 'prospector/fanzines/vote_start.html', {'start_from': next, 'total': len(all_fanzines), 'start': from_start}) 
  
@login_required
def fanzines_vote(request, pk):
    obj = get_object_or_404(Fanzine, pk=pk)
    all_fanzines = list(Fanzine.objects.all())
    current_index = all_fanzines.index(obj) # Seems awfully inefficient but I couldn't see any other way...
    username = request.user.get_full_name()
    try:
        obj_rating = FanzineRating.objects.filter(fanzine=obj).get(user=username)
    except FanzineRating.DoesNotExist:
        obj_rating = None
    
    # Get previous element (for returning back)
    prev = None
    if current_index != 0:
        prev = all_fanzines[current_index-1].pk
    
    # Handle user input
    if request.method == 'POST':
        form = FanzineVoteForm(request.POST)
        if form.is_valid():
            score = form.cleaned_data['rating']
            comment = form.cleaned_data['comment']
            #if comment == '': comment = None
            
            if obj_rating == None:
                # Update fanzine (only if new)
                obj.total_score += score
                obj.save()
                
                # Create rating
                obj_rating = FanzineRating(fanzine=obj, user=username, score=score, comment=comment)
            else:
                # Update rating
                obj_rating.score = score
                obj_rating.comment = comment
            
            obj_rating.save()

            next_index = current_index+1
            if next_index >= len(all_fanzines): # Arrived at the end
                return render(request, 'prospector/fanzines/vote_end.html')
            else:
                next_pk = all_fanzines[next_index].pk
                # TODO can we remove this indirection ?
                return redirect(reverse('prospector:fanzines.vote', args=(next_pk,)))

    # Display form
    if obj_rating != None:
        form = FanzineVoteForm(initial={'rating': obj_rating.score, 'comment': obj_rating.comment})
    else:
        form = FanzineVoteForm()

    return render(request, 'prospector/fanzines/vote.html', {'obj': obj, 'form': form, 'prev': prev, 'index': current_index+1, 'total':len(all_fanzines)})       
            
            
            
            
