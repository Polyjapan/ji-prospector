from django.shortcuts import render
from django.views import View
from django.views.generic.detail import SingleObjectMixin
from django.db.models import Sum, Min, Max, Count, FilteredRelation, Q, F
from django.db.models.fields import DateTimeField
from django.utils.timezone import is_aware, make_aware

from .models import Contact, Deal, DealTask, BoothSpace, Task

from collections import namedtuple

def get_table_data(model_class, model_instance):
    Key = namedtuple('Key', ['verbose_name', 'name'])
    kv = {
        Key(f.verbose_name, f.name) :
        getattr(model_instance, 'get_{}_display'.format(f.name), getattr(model_instance, f.name))
        for f in model_class._meta.local_fields if f.name != 'id'
    }
    return kv

def index(request):
    """Gives overview :
    * Budget
    * Open booth spaces
    * Tasks to do and their status and their deadline
    * Floating deals
    """
    floating_deals = {
        'rows': Deal.objects.exclude(floating=''),
        'cols': ['Stand', 'Personne', 'Email', 'Explication'],
    }

    free_booths = {
        'rows': BoothSpace.objects.filter(deal__isnull=True),
        'cols': ['Emplacement', 'Bâtiment', 'Prix usuel'],
    }

    # Yeah I know. The ORM would not let me group by one thing only. Fuck the ORM (and/or me)
    # Maybe I should just do it in <number_of_task> queries... get the tasks first, and then for each one, get the related data. but dammit... performance !!
    to_do_rows = Task.objects.raw('''
SELECT
	t.id,
	t.name,
	c.booth_name,
	dt.deadline,
    dt2.deal_count,
    dt2.worst_todo,
    d.id AS deal_id
FROM
	prospector_dealtask dt
	JOIN prospector_task t
	ON dt.task_id = t.id
	JOIN prospector_deal d
	ON dt.deal_id = d.id
	JOIN prospector_contact c
	ON d.contact_id = c.id
	JOIN (
		SELECT MIN(deadline) as min_deadline, task_id, COUNT(*) AS deal_count, MAX(todo_state) AS worst_todo
		FROM prospector_dealtask
		WHERE todo_state <> '0_done'
		GROUP BY task_id
	) dt2
	ON dt.task_id = dt2.task_id
WHERE dt.deadline = dt2.min_deadline
ORDER BY dt.deadline
    ''')

    # RawSQL-to-Model glue here :(
    for row in to_do_rows:
        # Parse datetime just as a real model would. Throws the same exceptions, too.
        row.deadline = DateTimeField().to_python(row.deadline)
        if not is_aware(row.deadline):
            row.deadline = make_aware(row.deadline)
        # Add in display helper for todo-state
        row.get_worst_todo_display = lambda *, row=row : dict(DealTask.TODO_STATES).get(row.worst_todo)

    to_do = {
        'rows': to_do_rows,
        'cols': ['Tâche', '# de Deals liés', 'État le plus grave', 'Échéance la plus proche']
    }

    final_budget = Deal.objects.filter(price_final=True).aggregate(Sum('price'))['price__sum'] or 0
    unsure_budget = Deal.objects.filter(price_final=False).aggregate(Sum('price'))['price__sum'] or 0

    return render(request, 'prospector/index.html', {'floating_deals': floating_deals, 'free_booths': free_booths, 'to_do': to_do, 'final_budget': final_budget, 'unsure_budget': unsure_budget})


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
    qs = {
        'rows': Contact.objects.order_by('booth_name'),
        'cols': ['Stand', 'Personne', 'Email', 'Description'],
    }
    return render(request, 'prospector/contacts/list.html', {'qs': qs})

def contacts_show(request, pk):
    obj = Contact.objects.get(pk=pk)
    # Get all fields of this object, and their values, in a dictionary
    kv = get_table_data(Contact, obj)
    # Get all deals related to this object
    deals = Deal.objects.filter(contact__pk=obj.pk).order_by('-event__date')
    return render(request, 'prospector/contacts/show.html', {'kv': kv, 'obj': obj, 'deals': deals})

def deals_list(request):
    qs = {
        'rows': Deal.objects.order_by('contact__booth_name'),
        'cols': ['Contact', 'Événement', 'Type', 'Prix', 'Emplacement', 'Flottant', 'Finalisé']
    }
    return render(request, 'prospector/deals/list.html', {'qs': qs})

def deals_show(request, pk):
    obj = Deal.objects.get(pk=pk)
    # Get all fields of this object, and their values, in a dictionary
    kv = get_table_data(Deal, obj)
    # Get all dealtasks related to this object
    dealtasks = DealTask.objects.filter(deal__pk=obj.pk).order_by('-deadline')
    return render(request, 'prospector/deals/show.html', {'kv': kv, 'obj': obj, 'dealtasks': dealtasks})

def tasks_list(request):
    qs = {
        'rows': Task.objects.annotate(Count('dealtask__deal')).annotate(Min('dealtask__deadline')).order_by('dealtask__deadline__min'),
        'cols': ['Nom', '# de Deals liés', 'Échéance la plus proche', 'Description'],
    }
    return render(request, 'prospector/tasks/list.html', {'qs': qs})

def dealtasks_list(request):
    qs = {
        'rows': DealTask.objects.all(),
        'cols': ['Nom', 'Échéance', 'État'],
    }
    return render(request, 'prospector/dealtasks/list.html', {'qs': qs})

def tasks_show(request, pk):
    obj = Deal.objects.get(pk=pk)
    # Get all fields of this object, and their values, in a dictionary
    kv = get_table_data(Deal, obj)
    # Get all dealtasks related to this object
    dealtasks = DealTask.objects.filter(deal__pk=obj.pk).order_by('-deadline')
    return render(request, 'prospector/deals/show.html', {'kv': kv, 'obj': obj, 'dealtasks': dealtasks})

# TODO: Find a way to select the fanzines



# Create your views here.
