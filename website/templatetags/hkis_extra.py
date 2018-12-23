from django import template
from django.utils.safestring import mark_safe

import markdown

register = template.Library()


@register.filter(is_safe=True)
def md_to_bootstrap(value):
    """This replaces some markdown css classes to bootstrap classes.
    """
    return value.replace(
        'class="admonition warning"', 'class="alert alert-warning"'
    ).replace("admonition-title", "alert-heading")


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
