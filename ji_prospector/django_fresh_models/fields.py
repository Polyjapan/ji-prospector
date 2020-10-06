import django.forms


class FreshModelChoiceField(django.forms.ModelChoiceField):
    def label_from_instance(self, obj):
        if getattr(obj, 'freshly_filtered', False):
            return obj.freshly_filtered()
        return str(obj)


class FreshModelMultipleChoiceField(django.forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        if getattr(obj, 'freshly_filtered', False):
            return obj.freshly_filtered()
        return str(obj)
