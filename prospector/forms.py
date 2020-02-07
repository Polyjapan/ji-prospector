from django import forms

from .models import Contact, Deal

# Really ?
class FanzineForm(forms.Form):
    pass


class FanzineVoteForm(forms.Form):
    """One day I'll do it"""
    pass


### Generic ones
class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact


class PublicContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        exclude = ['private_description']


class DealForm(forms.ModelForm):
    class Meta:
        model = Deal
