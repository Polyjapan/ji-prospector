from django import forms
from django.db.models import Value, CharField

from django_fresh_models.library import fresh_modelform_meta
from django_fresh_models.fields import FreshModelMultipleChoiceField

from .models import Contact, Deal, TaskType, Task, BoothSpace, LogisticalNeedSet
from .fields import PrefixedDataListTextInput


# Really ?
class FanzineForm(forms.Form):
    pass


class FanzineVoteForm(forms.Form):
    """One day I'll do it"""

    pass


class HardDeleteForm(forms.Form):
    magic_words_field = forms.CharField(
        max_length=128, required=False, label="Mots magiques"
    )

    def clean_magic_words_field(self):
        data = self.cleaned_data["magic_words_field"]
        if data.lower() != self.magic_words.lower():
            raise forms.ValidationError("Les mots magiques ne sont pas corrects.")
        return data

    def __init__(self, *args, magic_words, **kwargs):
        super().__init__(*args, **kwargs)
        self.magic_words = magic_words


class ContactForm(forms.ModelForm):
    @fresh_modelform_meta
    class Meta:
        model = Contact
        fields = "__all__"


class DealForm(forms.ModelForm):
    @fresh_modelform_meta
    class Meta:
        model = Deal
        exclude = ["tasks"]


class TaskTypeForm(forms.ModelForm):
    @fresh_modelform_meta
    class Meta:
        model = TaskType
        fields = "__all__"


class BoothSpaceForm(forms.ModelForm):
    @fresh_modelform_meta
    class Meta:
        model = BoothSpace
        fields = "__all__"


class LogisticalNeedSetForm(forms.ModelForm):
    @fresh_modelform_meta
    class Meta:
        model = LogisticalNeedSet
        fields = "__all__"


class TaskCommentForm(forms.Form):
    text = forms.CharField(
        max_length=128,
        label="",
        widget=forms.Textarea(
            attrs={
                "class": "form-input",
                "placeholder": "Ton commentaire ici",
                "rows": "3",
            }
        ),
    )


class QuickStartForm(forms.Form):
    what = forms.CharField(max_length=128, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        qs1 = (
            TaskType.objects.annotate(pouet=Value("tasktype", CharField()))
            .values_list("name", "pouet")
            .order_by()
        )
        qs2 = (
            Deal.objects.annotate(pouet=Value("deal", CharField()))
            .values_list("booth_name", "pouet")
            .order_by()
        )

        self.fields["what"].widget = PrefixedDataListTextInput(
            prefix="Je veux m'occuper de",
            prefix_attrs={"class": "text-large"},
            tuplelist=qs1.union(qs2),
            name="quickstart-list1",
            attrs={
                "class": "form-input input-lg d-inline",
                "autocomplete": "off",
                "placeholder": "plusieurs tâches en vrac",
            },
        )


class QuickTaskForm(forms.Form):
    name = forms.CharField(max_length=128)
    deadline = forms.DateTimeField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-select select-sm", "type": "date"}
        ),
    )
    state = forms.ChoiceField(
        choices=Task.TODO_STATES,
        widget=forms.Select(attrs={"class": "form-select select-sm"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["name"].widget = PrefixedDataListTextInput(
            prefix="Il faut",
            tuplelist=TaskType.objects.values_list("name", "id"),
            name="quicktask-list",
            attrs={"class": "form-input input-sm d-inline", "autocomplete": "off"},
        )


class ImportTaskTypesForm(forms.Form):
    json_list = forms.CharField(
        label="Liste JSON",
        help_text="Copier-coller ce que l'export a produit",
        widget=forms.Textarea(),
    )


class ExportTaskTypesForm(forms.Form):
    which_tasktypes = FreshModelMultipleChoiceField(
        label="Quels types?",
        queryset=TaskType.objects.all()
    )

# Generic ones
# class ContactForm(forms.ModelForm):
#     class Meta:
#         model = Contact
#         fields = ['__all__']
#
# class PublicContactForm(forms.ModelForm):
#     class Meta:
#         model = Contact
#         exclude = ['private_description']
#
#
# class DealForm(forms.ModelForm):
#     class Meta:
#         model = Deal
#         fields = ['__all__']
