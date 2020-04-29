from django.db import models
from django.utils.timezone import now
from django.db.models import Sum
from django.utils.safestring import mark_safe
from django.urls import reverse
#
#
# from gmail_link.models import EmailAddress


from datetime import timedelta
import json

# Create your models here.
#
# class EmailAddressContact(models.Model):
#     emailaddress = models.ForeignKey('EmailAddress', on_delete=models.CASCADE)
#     contact = models.ForeignKey('Contact', on_delete=models.CASCADE)

class Event(models.Model):
    name = models.CharField(max_length=128, verbose_name='Nom')
    date = models.DateField(verbose_name='Date')
    current = models.BooleanField(default=False, verbose_name='Événement actuel ?')
    budget = models.FloatField(verbose_name='Budget stands')

class Contact(models.Model):
    person_name = models.CharField(max_length=128, blank=True, verbose_name='Nom de la personne')
    phone_number = models.CharField(max_length=16, blank=True, verbose_name='Téléphone')

    address_street = models.CharField(max_length=128, blank=True, verbose_name='Adresse')
    address_city = models.CharField(max_length=128, blank=True, verbose_name='Ville')
    address_country = models.CharField(max_length=2, blank=True, verbose_name='Pays')

    private_description = models.TextField(blank=True, verbose_name='Description privée')
    pr_description = models.TextField(blank=True, verbose_name='Description comm')

class TaskType(models.Model):
    """e.g. 'Send the contract' or 'Set booth location'..."""
    name = models.CharField(max_length=128, verbose_name='Nom')
    description = models.TextField(blank=True, verbose_name='Description')
    typical_next_task = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, verbose_name='Tâche suivante typique')
    useful_views = models.TextField(blank=True, verbose_name='Liens utiles', help_text='JSON object. Key=Name of button, Value=django URL name') # A list of url names that point to views accepting an argument named pk, which is a --Task's--

    @property
    def useful_views_dict(self):
        return json.loads(self.useful_views) if self.useful_views else {}

class Task(models.Model):
    """Each time the todo-state changes, create a new Task object. That way, you can keep a history => No. Use another model, and show it with Spectre Timelines."""
    TODO_STATES = [
        ('0_done', 'Tâche terminée'),
        ('1_doing', 'Tâche en cours'),
        ('2_pro_waits_contact', 'Pro attend sur contact'),
        ('3_pro_waits_presidence', 'Pro attend sur présidence'),
        ('4_pro_waits_treasury', 'Pro attend sur trésorerie'),
        ('5_contact_waits_pro', 'Contact attend sur pro'),
    ]

    todo_state = models.CharField(max_length=32, choices=TODO_STATES)
    todo_state_logged = models.BooleanField(default=False)
    start_date = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    deal = models.ForeignKey('Deal', on_delete=models.CASCADE)
    tasktype = models.ForeignKey('TaskType', on_delete=models.CASCADE)

    def usual_next_states(self):
        pro_waits = ['2_pro_waits_contact', '3_pro_waits_presidence', '4_pro_waits_treasury']

        if self.todo_state in pro_waits:
            ret = pro_waits + ['1_doing']
            ret.remove(self.todo_state)
            return ret
        if self.todo_state == '5_contact_waits_pro':
            return ['1_doing']
        if self.todo_state == '1_doing':
            return ['0_done']
        if self.todo_state == '0_done':
            return []
        return ['5_contact_waits_pro']

    def usual_prev_states(self):
        pro_waits = ['2_pro_waits_contact', '3_pro_waits_presidence', '4_pro_waits_treasury']

        if self.todo_state == '0_done':
            return ['1_doing']
        if self.todo_state == '1_doing':
            return ['5_contact_waits_pro']
        if self.todo_state == '5_contact_waits_pro':
            return ['2_pro_waits_contact']
        return ['5_contact_waits_pro']

class TaskLog(models.Model):
    class Meta:
        get_latest_by = 'date'

    old_todo_state = models.CharField(max_length=32, choices=Task.TODO_STATES, blank=True, null=True)
    new_todo_state = models.CharField(max_length=32, choices=Task.TODO_STATES)
    task = models.ForeignKey('Task', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now=True)

class Deal(models.Model):
    DEAL_TYPES = [
        ('pro', 'Stand pro'),
        ('fanzine', 'Stand fanzine/jeune créateur'),
        ('sponsor', 'Stand sponsor'),
        ('service_provider', 'Stand prestataire'),
        ('association', 'Stand association'),
        ('food', 'Stand nourriture'),
    ]
    type = models.CharField(max_length=32, choices=DEAL_TYPES, verbose_name='Type')
    contact = models.ForeignKey('Contact', on_delete=models.CASCADE, verbose_name='Contact')
    event = models.ForeignKey('Event', on_delete=models.CASCADE, verbose_name='Événement')

    booth_name = models.CharField(max_length=128, blank=True, verbose_name='Nom du stand')

    price = models.FloatField(verbose_name='Prix')
    price_final = models.BooleanField(default=False, verbose_name='Prix certain ?')
    additional_price_modalities = models.TextField(blank=True, verbose_name='Supplément ?') # e.g. "10% CA"
    additional_price_sum = models.FloatField(blank=True, null=True, verbose_name='Montant supplément') # to be filled when known

    tasks = models.ManyToManyField('TaskType', through='Task', verbose_name='Tâches')
    attend_to_mail_alert = models.BooleanField(default=False)
    logistical_needs = models.ForeignKey('LogisticalNeedSet', on_delete=models.CASCADE, blank=True, null=True, verbose_name='Besoins logistiques prévisionnels', related_name='previsional_deals')
    #actual_logistical_needs = models.ForeignKey('LogisticalNeedSet', on_delete=models.CASCADE, blank=True, verbose_name='Besoins logistiques finaux', related_name='final_deals')

    @property
    def is_floating(self):
        return not self.price_final or not self.boothspace.final

    @property
    def is_finalized(self):
        additional_price_ok = self.additional_price_sum if self.additional_price_modalities else True
        return not additional_price_ok and self.actual_logistical_needs

    @property
    def main_boothspace(self):
        if self.boothspace_set.exists():
            return self.boothspace_set.order_by('-usual_price')[0]
        return None

    @property
    def boothspaces_usual_price_sum(self):
        if self.boothspace_set.exists():
            return self.boothspace_set.aggregate(Sum('usual_price'))[0]
        return None

class BoothSpace(models.Model):
    name = models.CharField(max_length=32)
    building = models.CharField(max_length=32)
    usual_price = models.FloatField()
    identifier = models.CharField(max_length=256) # To identify the booth with whatever indirection of the plans we have
    deal = models.ForeignKey('Deal', blank=True, null=True, on_delete=models.CASCADE)
    final = models.BooleanField(default=False) # For every deal, at most 1 linked booth space must be final !
    # TODO : ^this shouldn't be here !!! it should be linked to event at least.
    # or have the entire model be linked to event ? after all, numerotation changes every year...
    # but in that case, allow easy copypaste from year to year.

class LogisticalNeedSet(models.Model):
    name = models.CharField(max_length=128)

    # Heavy
    tables = models.IntegerField(default=0)
    chairs = models.IntegerField(default=0)
    panels = models.IntegerField(default=0)
    electrical = models.TextField(blank=True)

    # Cutlery
    small_plates = models.IntegerField(default=0)
    medium_plates = models.IntegerField(default=0)
    bowls = models.IntegerField(default=0)
    utensils = models.IntegerField(default=0)
    cutlery_comment = models.TextField(blank=True)

    # Staffs
    staffs = models.IntegerField(default=0)
    staffs_comment = models.TextField(blank=True)

    # Other
    other_material = models.TextField(blank=True)
