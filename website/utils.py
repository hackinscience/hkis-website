from functools import partial, lru_cache
from urllib.parse import urlparse

import bleach
from django.conf import settings
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension


def _set_target(attrs, new=False):
    if new:
        return None  # Don't create new links.
    try:
        p = urlparse(attrs[(None, "href")])
    except KeyError:
        return attrs
    if p.netloc not in settings.INTERNAL_DOMAINS:
        attrs[(None, "target")] = "_blank"
    else:
        attrs.pop((None, "target"), None)
    return attrs


@lru_cache(maxsize=8192)
def markdown_to_bootstrap(text):
    """This convert markdown text to html, with two things:
    - Uses bleach.clean to remove unsafe things.
    - Use custom replacements to adapt classes to bootstrap 4
     """

    return (
        bleach.sanitizer.Cleaner(
            tags=settings.ALLOWED_TAGS,
            attributes=settings.ALLOWED_ATTRIBUTES,
            styles=settings.ALLOWED_STYLES,
            filters=[
                partial(
                    bleach.linkifier.LinkifyFilter,
                    callbacks=[_set_target],
                    skip_tags=["pre"],
                    parse_email=False,
                ),
            ],
        )
        .clean(
            markdown.markdown(
                text,
                extensions=[
                    "fenced_code",
                    CodeHiliteExtension(guess_lang=False),
                    "admonition",
                ],
            ),
        )
        .replace('class="admonition warning"', 'class="alert alert-warning"')
        .replace('class="admonition note"', 'class="alert alert-info"')
        .replace("admonition-title", "alert-heading")
    )
