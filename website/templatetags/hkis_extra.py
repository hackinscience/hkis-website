from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

import bleach
import markdown

register = template.Library()


@register.filter(is_safe=True)
def md_to_bootstrap(value):
    """This replaces some markdown css classes to bootstrap classes.
    """
    return (
        value.replace('class="admonition warning"', 'class="alert alert-warning"')
        .replace('class="admonition note"', 'class="alert alert-info"')
        .replace("admonition-title", "alert-heading")
    )


@register.filter(is_safe=True)
def i18n_doc_links(value, language):
    """This filter rewrites https://docs.python.org link to
    include language tag.
    """
    if language == "fr":
        return value.replace("https://docs.python.org/", "https://docs.python.org/fr/")
    return value


@register.filter(name="markdown", is_safe=True)
def markdown_filter(value):
    """Processes the given value as Markdown.
    Syntax::
        {{ value|markdown }}
    """
    return mark_safe(
        markdown.markdown(value, extensions=["fenced_code", "codehilite", "admonition"])
    )


@register.filter(name="safe_markdown", is_safe=True)
def safe_markdown_filter(value):
    """Processes the given value as Markdown and pass it to bleach.clean.
    Syntax::
        {{ value|safe_markdown }}
    """
    return mark_safe(
        bleach.clean(
            markdown.markdown(
                value, extensions=["fenced_code", "codehilite", "admonition"]
            ),
            tags=settings.ALLOWED_TAGS,
            attributes=settings.ALLOWED_ATTRIBUTES,
            styles=settings.ALLOWED_STYLES,
        )
    )


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
