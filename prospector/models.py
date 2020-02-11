from django.db import models
from django.utils.timezone import now


from datetime import timedelta

# Create your models here.

class Event(models.Model):
    name = models.CharField(max_length=128)
    date = models.DateField()
    budget = models.FloatField()

class Contact(models.Model):
    person_name = models.CharField(max_length=128, blank=True, verbose_name='Nom de la personne')
    phone_number = models.CharField(max_length=16, blank=True, verbose_name='Téléphone')
    email_address = models.CharField(max_length=128, blank=True, verbose_name='Email')

    address_street = models.CharField(max_length=128, blank=True, verbose_name='Adresse')
    address_city = models.CharField(max_length=128, blank=True, verbose_name='Ville')
    address_country = models.CharField(max_length=2, blank=True, verbose_name='Pays')

    private_description = models.TextField(blank=True, verbose_name='Description privée')
    pr_description = models.TextField(blank=True, verbose_name='Description comm')


class TaskType(models.Model):
    """e.g. 'Send the contract' or 'Set booth location'..."""
    name = models.CharField(max_length=128)
    description = models.TextField()
    typical_next_task = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)
    useful_views = models.TextField(blank=True) # A list of url names that point to views accepting an argument named pk, which is a --Task's--


class Task(models.Model):
    """Each time the todo-state changes, create a new Task object. That way, you can keep a history."""
    TODO_STATES = [
        ('5_contact_waits_pro', 'Contact attend sur pro'),
        ('4_pro_waits_treasury', 'Pro attend sur trésorerie'),
        ('3_pro_waits_presidence', 'Pro attend sur présidence'),
        ('2_pro_waits_contact', 'Pro attend sur contact'),
        ('1_doing', 'Tâche en cours'),
        ('0_done', 'Tâche terminée'),
    ]

    todo_state = models.CharField(max_length=32, choices=TODO_STATES)
    start_date = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField(blank=True, null=True)
    deal = models.ForeignKey('Deal', on_delete=models.CASCADE)
    tasktype = models.ForeignKey('TaskType', on_delete=models.CASCADE)


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
    logistical_needs = models.ForeignKey('LogisticalNeedSet', on_delete=models.CASCADE, blank=True, null=True, verbose_name='Besoins logistiques prévisionnels', related_name='previsional_deals')
    #actual_logistical_needs = models.ForeignKey('LogisticalNeedSet', on_delete=models.CASCADE, blank=True, verbose_name='Besoins logistiques finaux', related_name='final_deals')

    floating = models.TextField(blank=True, verbose_name='Détail flottant ?') # if there are doubts over a big change, put in here.

    @property
    def is_floating(self):
        return self.floating or not self.price_final or not self.boothspace.final

    @property
    def is_finalized(self):
        additional_price_ok = self.additional_price_sum if self.additional_price_modalities else True
        return not self.is_floating and additional_price_ok and self.actual_logistical_needs


class BoothSpace(models.Model):
    name = models.CharField(max_length=32)
    building = models.CharField(max_length=32)
    usual_price = models.FloatField()
    identifier = models.CharField(max_length=256) # To identify the booth with whatever indirection of the plans we have
    deal = models.ForeignKey('Deal', blank=True, null=True, on_delete=models.CASCADE)
    final = models.BooleanField(default=False) # For every deal, at most 1 linked booth space must be final !


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
