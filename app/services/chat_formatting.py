"""Render only minimal formatting from untrusted AI text, without enabling HTML."""
import re
from markupsafe import Markup, escape

BOLD = re.compile(r"\*\*(.+?)\*\*")


def format_ai_reply(value):
    """Escape all raw HTML, then permit bold emphasis and visible line breaks."""
    escaped = str(escape(value or ""))
    highlighted = BOLD.sub(r"<strong>\1</strong>", escaped)
    return Markup(highlighted.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>\n"))
