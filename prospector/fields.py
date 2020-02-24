from django import forms

class PrefixedDataListTextInput(forms.TextInput):
    def __init__(self, prefix, datalist, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._prefix = prefix
        self._name = name
        self._list = datalist
        self.attrs.update({'list':'list__{}'.format(self._name)})

    def render(self, name, value, attrs=None, renderer=None):
        text_html = super().render(name, value, attrs=attrs)
        prefix = '<span>{}</span>'.format(self._prefix)
        datalist = '<datalist id="list__{}">'.format(self._name)
        for item in self._list:
            datalist += '<option value="{}">'.format(item)
        datalist += '</datalist>'

        return '''
            <div class="columns col-gapless">
                <div class="column col-auto mr-1">
                    {}
                </div>
                <div class="column col-9">
                    {}
                </div>
            </div>
        {}'''.format(prefix, text_html, datalist)
