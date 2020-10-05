# This class aims at removing render logic from Model definitions, where it almost certainly does not belong.
# It also handles type-based dispatching.

# To use, instantiate the class as mf, and decorate functions with @mf.filter(MyModelClassHere)
# Do not hesitate to call mf.do_filter(...) recursively if you need it. e.g. for related models.

from .fields import FreshModelChoiceField


class FreshFilterLibrary:
    filters = {}

    def filter(self, model_class):
        def decorator(function):
            FreshFilterLibrary.filters[model_class] = function
            return function
        return decorator

    def do_filter(self, model_inst, argument=None):
        return FreshFilterLibrary.filters[type(model_inst)](model_inst, argument)


# Model decorator
def fresh_model(model_class):
    def freshly_filtered(self):
        mf = FreshFilterLibrary()
        return mf.do_filter(self, argument=None)
    setattr(model_class, 'freshly_filtered', freshly_filtered)
    return model_class


def fresh_modelform_meta(modelform_metaclass):
    """A ModelForm decorator that automatically sets the fields of fresh-model FK's to a FreshModelChoiceField"""

    if not hasattr(modelform_metaclass, "field_classes"):
        setattr(modelform_metaclass, "field_classes", {})

    fresh_model_fk_field_names = [
        x.name
        for x in modelform_metaclass.model._meta.get_fields()
        if x.is_relation
        and (x.many_to_one or x.one_to_one)
        and hasattr(x.related_model, "freshly_filtered")
    ]

    for name in fresh_model_fk_field_names:
        included = (
            (modelform_metaclass.fields == "__all__" or name in modelform_metaclass.fields)
            if hasattr(modelform_metaclass, "fields")
            else True
        )
        not_excluded = (
            (name not in modelform_metaclass.exclude)
            if hasattr(modelform_metaclass, "exclude")
            else True
        )

        if included and not_excluded:
            modelform_metaclass.field_classes[name] = FreshModelChoiceField

    return modelform_metaclass
