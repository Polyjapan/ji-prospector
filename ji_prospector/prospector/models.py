from django.db import models
from django.contrib.auth import get_user_model


# from gmail_link.models import EmailAddress
from django_fresh_models.library import fresh_model

import safedelete.models
import json


User = get_user_model()

# Create your models here.
#
# class EmailAddressContact(models.Model):
#     emailaddress = models.ForeignKey('EmailAddress', on_delete=models.CASCADE)
#     contact = models.ForeignKey('Contact', on_delete=models.CASCADE)


@fresh_model
class Event(models.Model):
    name = models.CharField(max_length=128, verbose_name="Nom")
    date = models.DateField(verbose_name="Date")
    current = models.BooleanField(default=False, verbose_name="Événement actuel ?")
    budget = models.FloatField(verbose_name="Budget stands")
    agepoly_president = models.CharField(
        max_length=128, verbose_name="Président AGEPoly"
    )
    polyjapan_president = models.CharField(
        max_length=128, verbose_name="Président PolyJapan"
    )


@fresh_model
class Contact(safedelete.models.SafeDeleteModel):
    class Meta:
        ordering = ["person_name"]

    _safedelete_policy = safedelete.models.HARD_DELETE_NOCASCADE

    person_name = models.CharField(
        max_length=128, blank=True, verbose_name="Nom de la personne"
    )
    phone_number = models.CharField(max_length=16, blank=True, verbose_name="Téléphone")

    address_street = models.CharField(
        max_length=128, blank=True, verbose_name="Adresse"
    )
    address_city = models.CharField(max_length=128, blank=True, verbose_name="Ville")
    address_country = models.CharField(
        max_length=2, blank=True, verbose_name="Pays", help_text="Code à deux lettres"
    )

    private_description = models.TextField(
        blank=True, verbose_name="Description privée"
    )
    pr_description = models.TextField(blank=True, verbose_name="Description comm")


@fresh_model
class TaskType(safedelete.models.SafeDeleteModel):
    """e.g. 'Send the contract' or 'Set booth location'..."""

    _safedelete_policy = safedelete.models.HARD_DELETE_NOCASCADE

    name = models.CharField(max_length=128, verbose_name="Nom")
    description = models.TextField(blank=True, verbose_name="Description")
    wiki_page = models.URLField(max_length=256, blank=True, verbose_name="Lien wiki")
    default_task_type = models.BooleanField(
        default=False, verbose_name="Ce type de tâche est par défaut"
    )

    typical_prev_task = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="typical_next_tasks",
        verbose_name="Type de tâche précédent typique",
    )
    tags = models.TextField(
        blank=True,
        verbose_name="Tags magiques",
        help_text="Line-separated list of tags",
    )  # Search with regex field lookup
    useful_views = models.TextField(
        blank=True,
        verbose_name="Liens utiles",
        help_text="JSON object. Key=Name of button, Value=django URL name",
    )  # A list of url names that point to views accepting an argument named pk, which is a --Task's--

    @property
    def depth(self):
        if self.typical_prev_task:
            return self.typical_prev_task.depth + 1
        else:
            return 0

    @property
    def useful_views_dict(self):
        return json.loads(self.useful_views) if self.useful_views else {}

    @property
    def tags_list(self):
        return [x.strip() for x in self.tags.split("\n")] if self.tags else []


@fresh_model
class Task(safedelete.models.SafeDeleteModel):
    TODO_STATES = [
        ("0_done", "Terminé"),
        ("1_doing", "En cours"),
        ("2_pro_waits_contact", "Attente contact"),
        ("3_pro_waits_presidence", "Attente prés."),
        ("4_pro_waits_treasury", "Attente tréso."),
        ("5_contact_waits_pro", "À faire"),
    ]

    _safedelete_policy = safedelete.models.HARD_DELETE_NOCASCADE

    todo_state = models.CharField(max_length=32, choices=TODO_STATES)
    todo_state_logged = models.BooleanField(default=False)
    start_date = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField(blank=True, null=True)
    deal = models.ForeignKey("Deal", on_delete=models.CASCADE)
    tasktype = models.ForeignKey("TaskType", on_delete=models.CASCADE)

    def usual_next_states(self):
        pro_waits = [
            "2_pro_waits_contact",
            "3_pro_waits_presidence",
            "4_pro_waits_treasury",
        ]

        if self.todo_state in pro_waits:
            ret = pro_waits + ["1_doing"]
            ret.remove(self.todo_state)
            return ret
        if self.todo_state == "5_contact_waits_pro":
            return ["1_doing"]
        if self.todo_state == "1_doing":
            return pro_waits + ["0_done"]
        if self.todo_state == "0_done":
            return []
        return ["5_contact_waits_pro"]

    def usual_prev_states(self):
        if self.todo_state == "0_done":
            return ["1_doing"]
        if self.todo_state == "1_doing":
            return ["5_contact_waits_pro"]
        if self.todo_state == "5_contact_waits_pro":
            return ["2_pro_waits_contact"]
        return ["5_contact_waits_pro"]


@fresh_model
class TaskLog(models.Model):
    class Meta:
        get_latest_by = "date"

    old_todo_state = models.CharField(
        max_length=32, choices=Task.TODO_STATES, blank=True, null=True
    )
    new_todo_state = models.CharField(max_length=32, choices=Task.TODO_STATES)
    task = models.ForeignKey("Task", on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)


@fresh_model
class TaskComment(models.Model):
    task = models.ForeignKey("Task", on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    date = models.DateTimeField(auto_now_add=True)


@fresh_model
class Deal(safedelete.models.SafeDeleteModel):
    class Meta:
        ordering = ["booth_name"]

    DEAL_TYPES = [
        ("pro", "Stand pro"),
        ("fanzine", "Stand fanzine/jeune créateur"),
        ("sponsor", "Stand sponsor"),
        ("service_provider", "Stand prestataire"),
        ("association", "Stand association"),
        ("food", "Stand nourriture"),
    ]

    _safedelete_policy = safedelete.models.HARD_DELETE_NOCASCADE

    type = models.CharField(max_length=32, choices=DEAL_TYPES, verbose_name="Type")
    contact = models.ForeignKey(
        "Contact", on_delete=models.CASCADE, verbose_name="Contact"
    )
    event = models.ForeignKey(
        "Event", on_delete=models.CASCADE, verbose_name="Événement"
    )

    booth_name = models.CharField(
        max_length=128, blank=True, verbose_name="Nom du stand"
    )

    price = models.FloatField(verbose_name="Prix")
    additional_price_exists = models.BooleanField(
        default=False, verbose_name="Supplément ?"
    )
    additional_price_modalities = models.TextField(
        blank=True, verbose_name="Modalités du supplément"
    )  # e.g. "10% CA"
    additional_price_sum = models.FloatField(
        blank=True, null=True, verbose_name="Montant du supplément"
    )  # to be filled when known

    tasks = models.ManyToManyField("TaskType", through="Task", verbose_name="Tâches")
    attend_to_mail_alert = models.BooleanField(default=False)
    logistical_needs = models.ForeignKey(
        "LogisticalNeedSet",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Besoins logistiques prévisionnels",
        related_name="previsional_deals",
    )
    # actual_logistical_needs = models.ForeignKey('LogisticalNeedSet', on_delete=models.CASCADE, blank=True, verbose_name='Besoins logistiques finaux', related_name='final_deals')

    def unfinished_tasks_with_tag(self, tag):
        return self.task_set.filter(
            tasktype__tags__regex=r"(^|\n)\s*{}\s*($|\n)".format(tag)
        ).exclude(todo_state="0_done")

    def any_tasks_with_tag(self, tag):
        return self.task_set.filter(
            tasktype__tags__regex=r"(^|\n)\s*{}\s*($|\n)".format(tag)
        )

    @property
    def price_decided(self):
        if self.any_tasks_with_tag("price"):
            return not self.unfinished_tasks_with_tag("price").exists()
        return False

    @property
    def boothspace_decided(self):
        if self.any_tasks_with_tag("boothspace"):
            return not self.unfinished_tasks_with_tag("boothspace").exists()
        return False

    @property
    def contract_decided(self):
        if self.any_tasks_with_tag("contract"):
            return not self.unfinished_tasks_with_tag("contract").exists()
        return False

    # @property
    # def is_floating(self):
    #     if not self.price_final:
    #         return True
    #     for bs in self.boothspace_set.all():
    #         if not bs.final:
    #             return True
    #     return False
    #
    # @property
    # def is_finalized(self):
    #     additional_price_ok = self.additional_price_sum if self.additional_price_modalities else True
    #     return not additional_price_ok and self.actual_logistical_needs
    #
    # @property
    # def main_boothspace(self):
    #     if self.boothspace_set.exists():
    #         return self.boothspace_set.order_by('-usual_price')[0]
    #     return None
    #
    # @property
    # def boothspaces_usual_price_sum(self):
    #     if self.boothspace_set.exists():
    #         return self.boothspace_set.aggregate(Sum('usual_price'))[0]
    #     return None


class DealBoothSpace(models.Model):
    deal = models.ForeignKey("Deal", on_delete=models.CASCADE)
    boothspace = models.ForeignKey("BoothSpace", on_delete=models.CASCADE)


class BoothSpace(models.Model):
    name = models.CharField(max_length=32)
    building = models.CharField(max_length=32)
    usual_price = models.FloatField()
    identifier = models.CharField(
        max_length=256
    )  # To identify the booth with whatever indirection of the plans we have
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
