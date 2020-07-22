import bleach
from django.conf import settings
import markdown


def markdown_to_bootstrap(text):
    """This convert markdown text to html, with two things:
    - Uses bleach.clean to remove unsafe things.
    - Use custom replacements to adapt classes to bootstrap 4
     """

    return (
        bleach.clean(
            markdown.markdown(
                text, extensions=["fenced_code", "codehilite", "admonition"],
            ),
            tags=settings.ALLOWED_TAGS,
            attributes=settings.ALLOWED_ATTRIBUTES,
            styles=settings.ALLOWED_STYLES,
        )
        .replace('class="admonition warning"', 'class="alert alert-warning"')
        .replace('class="admonition note"', 'class="alert alert-info"')
        .replace("admonition-title", "alert-heading")
    )
