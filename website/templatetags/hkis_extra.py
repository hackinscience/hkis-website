from django import template

register = template.Library()


@register.filter(is_safe=True)
def trash_fix_code_in_a(value):
    """This is temporarily trash-fixing
    https://github.com/trentm/python-markdown2/issues/259
    """
    return value.replace("&lt;code&gt;", "<code>").replace("&lt;/code&gt;", "</code>")


@register.filter(is_safe=True)
def i18n_doc_links(value, language):
    """This filter rewrites https://docs.python.org link to
    include language tag.
    """
    if language == "fr":
        return value.replace("https://docs.python.org/", "https://docs.python.org/fr/")
    return value
