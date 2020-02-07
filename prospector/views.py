from django.shortcuts import render
from django.views import View
from django.views.generic.detail import SingleObjectMixin
from django.db.models import Sum

from .models import Contact, Deal, DealTask, BoothSpace

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
    floating_deals = Deal.objects.exclude(floating='')
    free_booths = BoothSpace.objects.filter(deal__isnull=True)
    to_do = DealTask.objects.filter(todo_state='contact_waits_pro').order_by('deadline', 'deal')
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
    qs = Contact.objects.order_by('booth_name')
    return render(request, 'prospector/contacts/list.html', {'qs': qs})

def contacts_show(request, pk):
    obj = Contact.objects.get(pk=pk)
    # Get all fields of this object, and their values, in a dictionary
    kv = get_table_data(Contact, obj)
    # Get all deals related to this object
    deals = Deal.objects.filter(contact__pk=obj.pk).order_by('-event__date')
    return render(request, 'prospector/contacts/show.html', {'kv': kv, 'obj': obj, 'deals': deals})

def deals_list(request):
    qs = Deal.objects.order_by('contact__booth_name')
    return render(request, 'prospector/deals/list.html', {'qs': qs})

def deals_show(request, pk):
    obj = Deal.objects.get(pk=pk)
    # Get all fields of this object, and their values, in a dictionary
    kv = get_table_data(Deal, obj)
    # Get all dealtasks related to this object
    dealtasks = DealTask.objects.filter(deal__pk=obj.pk).order_by('-deadline')
    return render(request, 'prospector/deals/show.html', {'kv': kv, 'obj': obj, 'dealtasks': dealtasks})

# TODO: Find a way to select the fanzines



# Create your views here.
