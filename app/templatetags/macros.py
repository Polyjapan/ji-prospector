from django import template
from django.template.base import Node, FilterExpression
from django.template.loader import get_template

register = template.Library()

# Forked from https://github.com/twidi/django-templates-macros
# New feature : macro body

def _setup_macros_dict(parser):
    # Metadata of each macro are stored in a new attribute
    # of 'parser' class. That way we can access it later
    # in the template when processing 'usemacro' tags.
    try:
        # Only try to access it to eventually trigger an exception
        parser._macros
    except AttributeError:
        parser._macros = {}


class DefineMacroNode(template.Node):
    def __init__(self, name, nodelists, args):

        self.name = name
        self.nodelists = nodelists
        self.args = []
        self.kwargs = {}
        for a in args:
            if "=" not in a:
                self.args.append(a)
            else:
                name, value = a.split("=")
                self.kwargs[name] = value

    def render(self, context):
        # empty string - {% macro %} tag does no output
        return ''


@register.tag(name="macro")
def do_macro(parser, token):
    try:
        args = token.split_contents()
        tag_name, macro_name, args = args[0], args[1], args[2:]
    except IndexError:
        m = ("'{}' tag requires at least one argument (macro name)".format(token.contents.split()[0]))
        raise template.TemplateSyntaxError(m)

    nodelists = [parser.parse(('macrobody', 'endmacro', ))]
    token = parser.next_token()

    # {% macrobody %} (repeatable)
    while token.contents == 'macrobody':
        nodelists += [parser.parse(('macrobody', 'endmacro', ))]
        token = parser.next_token()

    if token.contents != 'endmacro':
        raise TemplateSyntaxError('Malformed template tag at line {}: "{}"'.format(token.lineno, token.contents))

    # Metadata of each macro are stored in a new attribute
    # of 'parser' class. That way we can access it later
    # in the template when processing 'usemacro' tags.
    _setup_macros_dict(parser)
    parser._macros[macro_name] = DefineMacroNode(macro_name, nodelists, args)
    return parser._macros[macro_name]


class LoadMacrosNode(template.Node):
    def render(self, context):
        # empty string - {% loadmacros %} tag does no output
        return ''


@register.tag(name="loadmacros")
def do_loadmacros(parser, token):
    try:
        tag_name, filename = token.split_contents()
    except IndexError:
        m = ("'{}' tag requires at least one argument (macro name)".format(token.contents.split()[0]))
        raise template.TemplateSyntaxError(m)
    if filename[0] in ('"', "'") and filename[-1] == filename[0]:
        filename = filename[1:-1]
    t = get_template(filename)
    macros = getattr(t, 'template', t).nodelist.get_nodes_by_type(DefineMacroNode)
    # Metadata of each macro are stored in a new attribute
    # of 'parser' class. That way we can access it later
    # in the template when processing 'usemacro' tags.
    _setup_macros_dict(parser)
    for macro in macros:
        parser._macros[macro.name] = macro
    return LoadMacrosNode()


class UseMacroNode(template.Node):
    def __init__(self, macro, fe_args, fe_kwargs, nodelist, context_only):
        self.macro = macro
        self.fe_args = fe_args
        self.fe_kwargs = fe_kwargs
        self.context_only = context_only
        self.nodelist = nodelist

    def render(self, context):

        for i, arg in enumerate(self.macro.args):
            try:
                fe = self.fe_args[i]
                context[arg] = fe.resolve(context)
            except IndexError:
                context[arg] = ""

        for name, default in self.macro.kwargs.items():
            if name in self.fe_kwargs:
                context[name] = self.fe_kwargs[name].resolve(context)
            else:
                context[name] = FilterExpression(default,
                                                 self.macro.parser
                                                 ).resolve(context)

        # # Place output into context variable
        # context[self.macro.name] = self.macro.nodelist.render(context)
        # return '' if self.context_only else context[self.macro.name]

        string = self.macro.nodelists[0].render(context)
        for nl in self.macro.nodelists[1:]:
            # render macro body
            string += self.nodelist.render(context)
            string += nl.render(context)

        return string


@register.tag(name="call")
def do_usemacro(parser, token):
    try:
        args = token.split_contents()
        tag_name, macro_name, values = args[0], args[1], args[2:]
    except IndexError:
        m = ("'{}' tag requires at least one argument (macro name)".format(token.contents.split()[0]))
        raise template.TemplateSyntaxError(m)

    try:
        macro = parser._macros[macro_name]
    except (AttributeError, KeyError):
        m = "Macro '%s' is not defined" % macro_name
        raise template.TemplateSyntaxError(m)

    fe_kwargs = {}
    fe_args = []

    for val in values:
        if "=" in val:
            # kwarg
            name, value = val.split("=")
            fe_kwargs[name] = FilterExpression(value, parser)
        else:  # arg
            # no validation, go for it ...
            fe_args.append(FilterExpression(val, parser))

    nodelist = parser.parse(('endcall',))
    parser.next_token()

    macro.name = macro_name
    macro.parser = parser

    return UseMacroNode(macro, fe_args, fe_kwargs, nodelist, context_only=False)
