from django import forms
from django.forms.widgets import SelectDateWidget
from django.db.models import Value, CharField
from django.utils.timezone import now

from .models import Contact, Deal, Task, TaskType
from .fields import PrefixedDataListTextInput

# Really ?
class FanzineForm(forms.Form):
    pass


class FanzineVoteForm(forms.Form):
    """One day I'll do it"""
    pass


class TaskCommentForm(forms.Form):
    text = forms.CharField(max_length=128, label='', widget=forms.Textarea(attrs={'class': 'form-input', 'placeholder': 'Ton commentaire ici', 'rows':'3'}))

class QuickStartForm(forms.Form):
    what = forms.CharField(max_length=128, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        qs1 = TaskType.objects.all().annotate(pouet=Value('tasktype', CharField())).values_list('name', 'pouet')
        qs2 = Deal.objects.all().annotate(pouet=Value('deal', CharField())).values_list('booth_name', 'pouet')

        self.fields['what'].widget = PrefixedDataListTextInput(
            prefix='Je veux m\'occuper de',
            prefix_attrs={'class': 'text-large'},
            tuplelist=qs1.union(qs2),
            name='quickstart-list1',
            attrs={'class': 'form-input input-lg d-inline', 'autocomplete': 'off', 'placeholder': 'plusieurs tâches en vrac'}
        )


class QuickTaskForm(forms.Form):
    name = forms.CharField(max_length=128)
    deadline = forms.DateTimeField(required=False, widget=forms.TextInput(attrs={'class': 'form-select select-sm', 'type': 'date'}))
    state = forms.ChoiceField(choices=Task.TODO_STATES, widget=forms.Select(attrs={'class': 'form-select select-sm'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['name'].widget = PrefixedDataListTextInput(
            prefix='Il faut',
            tuplelist=TaskType.objects.values_list('name', 'id'),
            name='quicktask-list',
            attrs={'class': 'form-input input-sm d-inline', 'autocomplete': 'off'}
        )

### Generic ones
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
