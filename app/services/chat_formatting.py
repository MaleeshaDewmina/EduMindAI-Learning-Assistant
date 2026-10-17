"""Render AI Markdown as constrained, sanitised HTML.

AI text and uploaded documents are untrusted. Keep raw HTML disabled in the
Markdown parser and apply an allowlist sanitizer as a second layer.
"""

import bleach
from markdown_it import MarkdownIt
from markupsafe import Markup

# Use a full CommonMark parser instead of replacing markup with regex.
# The table rule is built into markdown-it-py; breaks keeps short answers readable.
MARKDOWN = MarkdownIt(
    "commonmark", {"html": False, "linkify": False, "breaks": True}
).enable("table")

ALLOWED_TAGS = {
    "a", "p", "br", "strong", "em", "s", "del", "blockquote",
    "ul", "ol", "li", "h1", "h2", "h3", "h4", "hr",
    "pre", "code", "table", "thead", "tbody", "tr", "th", "td",
}
ALLOWED_ATTRIBUTES = {"a": ["href", "title"]}
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def format_ai_reply(value):
    """Render Markdown tables/lists/code safely for use in Jinja templates.

    No raw HTML, inline styles, scripts, event handlers, embedded images,
    JavaScript/data links, or arbitrary HTML attributes can survive sanitisation.
    This does not certify that links suggested by an LLM are trustworthy.
    """
    markdown = str(value or "")
    rendered = MARKDOWN.render(markdown)
    cleaned = bleach.clean(
        rendered,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
        strip_comments=True,
    )
    return Markup(cleaned)
