from django import forms


class PrefixedDataListTextInput(forms.TextInput):
    def __init__(self, prefix, tuplelist, name, prefix_attrs=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._prefix = prefix
        self._prefix_attrs = prefix_attrs or dict()
        self._name = name
        self._list = tuplelist
        self.attrs.update({"list": "list__{}".format(self._name)})

    def render(self, name, value, attrs=None, renderer=None):
        text_html = super().render(name, value, attrs=attrs)

        prefix_attrs_html = ""
        for name, value in self._prefix_attrs.items():
            prefix_attrs_html += '{}="{}" '.format(name, value)

        prefix = "<span {}>{}</span>".format(prefix_attrs_html, self._prefix)
        datalist = '<datalist id="list__{}">'.format(self._name)
        for t in self._list:
            datalist += '<option value="{}"><data value="{}"></option>'.format(
                t[0], t[1:]
            )
        datalist += "</datalist>"

        return """
            <div class="columns col-gapless flex-centered">
                <div class="column col-auto mr-2">
                    {}
                </div>
                <div class="column col">
                    {}
                </div>
            </div>
        {}""".format(
            prefix, text_html, datalist
        )
