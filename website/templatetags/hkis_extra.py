from django import template
from django.utils.safestring import mark_safe
from website.utils import markdown_to_bootstrap

import markdown

register = template.Library()


@register.filter("markdown_to_bootstrap", is_safe=True)
def _markdown_to_bootstrap(value):
    return mark_safe(markdown_to_bootstrap(value))


@register.filter(is_safe=True)
def i18n_doc_links(value, language):
    """This filter rewrites https://docs.python.org link to
    include language tag.
    """
    if language == "fr":
        return value.replace("https://docs.python.org/", "https://docs.python.org/fr/")
    return value


@register.tag(name="md")
def do_markdownize(parser, token):
    nodelist = parser.parse(("endmd",))
    parser.delete_first_token()
    return MarkdownNode(nodelist)


class MarkdownNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        output = self.nodelist.render(context)
        return markdown.markdown(
            output, extensions=["fenced_code", "codehilite", "admonition"]
        )
