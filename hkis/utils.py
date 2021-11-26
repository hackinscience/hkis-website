from functools import partial, lru_cache
from urllib.parse import urlparse
from typing import List
import bleach
from django.conf import settings
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension


ALLOWED_TAGS = [
    # Bleach Defaults
    "a",
    "abbr",
    "acronym",
    "b",
    "blockquote",
    "code",
    "em",
    "i",
    "li",
    "ol",
    "strong",
    "ul",
    # Custom Additions
    "br",
    "caption",
    "cite",
    "col",
    "colgroup",
    "dd",
    "del",
    "details",
    "div",
    "dl",
    "dt",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "img",
    "p",
    "pre",
    "span",
    "sub",
    "summary",
    "sup",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "tt",
    "kbd",
    "var",
]

ALLOWED_ATTRIBUTES = {
    # Bleach Defaults
    "a": ["href", "title"],
    "abbr": ["title"],
    "acronym": ["title"],
    # Custom Additions
    "*": ["id"],
    "hr": ["class"],
    "img": ["src", "width", "height", "alt", "align", "class"],
    "span": ["class"],
    "div": ["class"],
    "th": ["align"],
    "td": ["align"],
    "code": ["class"],
    "p": ["align", "class"],
}

ALLOWED_STYLES: List[str] = []


def _set_target(attrs, new=False):
    if new:
        return None  # Don't create new links.
    try:
        url = urlparse(attrs[(None, "href")])
    except KeyError:
        return attrs
    if url.netloc not in settings.ALLOWED_HOSTS:
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
            tags=getattr(settings, "ALLOWED_TAGS", ALLOWED_TAGS),
            attributes=getattr(settings, "ALLOWED_ATTRIBUTES", ALLOWED_ATTRIBUTES),
            styles=getattr(settings, "ALLOWED_STYLES", ALLOWED_STYLES),
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
