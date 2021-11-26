from django import template
from django.utils.safestring import mark_safe
import markdown

from hkis.utils import markdown_to_bootstrap

register = template.Library()


@register.filter("markdown_to_bootstrap", is_safe=True)
def _markdown_to_bootstrap(value):
    return mark_safe(markdown_to_bootstrap(value))


@register.tag(name="md")
def do_markdownize(parser, token):  # pylint: disable=unused-argument
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
