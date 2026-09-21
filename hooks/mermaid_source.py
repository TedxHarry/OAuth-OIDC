"""MkDocs build hook: preserve each Mermaid diagram's source in the HTML.

Material for MkDocs converts ``<pre class="mermaid"><code>...</code></pre>`` into
an (in this project, empty) rendered container and blanks the source before any
client script can read it. To render reliably we wrap every diagram in a
``<div class="diagram-wrap" data-diagram-source="...">`` whose attribute keeps
the raw Mermaid definition. Material never touches the wrapper, so
``diagrams-v5.js`` can always recover the source and render it once.
"""

from __future__ import annotations

import html
import re

_MERMAID_BLOCK = re.compile(
    r'<pre class="mermaid"><code>(?P<body>.*?)</code></pre>',
    re.DOTALL,
)


def _wrap(match: "re.Match[str]") -> str:
    escaped_body = match.group("body")
    raw_source = html.unescape(escaped_body)
    attr_value = html.escape(raw_source, quote=True)
    return (
        f'<div class="diagram-wrap" data-diagram-source="{attr_value}">'
        f"{match.group(0)}"
        "</div>"
    )


def on_page_content(html_content: str, page=None, config=None, files=None) -> str:
    return _MERMAID_BLOCK.sub(_wrap, html_content)
