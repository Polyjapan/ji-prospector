# This class aims at removing render logic from Model definitions, where it almost certainly does not belong.
# It also handles type-based dispatching.

# To use, instantiate the class as mf, and decorate functions with @mf.filter(MyModelClassHere)
# Do not hesitate to call mf.do_filter(...) recursively if you need it. e.g. for related models.

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
