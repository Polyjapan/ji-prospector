from django import forms
from django.forms.widgets import SelectDateWidget
from django.utils.timezone import now

from .models import Contact, Deal, Task, TaskType
from .fields import PrefixedDataListTextInput

# Really ?
class FanzineForm(forms.Form):
    pass


class FanzineVoteForm(forms.Form):
    """One day I'll do it"""
    pass


class QuickTaskForm(forms.Form):
    name = forms.CharField(max_length=128)
    deadline = forms.DateTimeField(required=False, widget=forms.TextInput(attrs={'class': 'form-select select-sm', 'type': 'date'}))
    state = forms.ChoiceField(choices=Task.TODO_STATES, widget=forms.Select(attrs={'class': 'form-select select-sm'}))
    comment = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-input input-sm'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['name'].widget = PrefixedDataListTextInput(
            prefix='Il faut',
            datalist=TaskType.objects.values_list('name', flat=True),
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
