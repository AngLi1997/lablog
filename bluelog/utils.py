# -*- coding: utf-8 -*-
"""
    :author: Ang Li
    :url: http://liangliang.world
    :copyright: © 2026 Ang Li <liangliangaichirou@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
try:
    from urlparse import urlparse, urljoin
except ImportError:
    from urllib.parse import urlparse, urljoin
import re
from html import escape

from flask import request, redirect, url_for, current_app
from markupsafe import Markup


CODE_BLOCK_RE = re.compile(r'```([\w+-]*)\n(.*?)```', re.DOTALL)
INLINE_CODE_RE = re.compile(r'`([^`\n]+)`')
IMAGE_RE = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
BOLD_RE = re.compile(r'\*\*(.+?)\*\*')
ITALIC_RE = re.compile(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)')
HEADING_RE = re.compile(r'^#{1,6}\s+', re.MULTILINE)
LIST_RE = re.compile(r'^\s*[-*+]\s+', re.MULTILINE)
QUOTE_RE = re.compile(r'^\s*>\s?', re.MULTILINE)
FENCE_RE = re.compile(r'^```[\w+-]*\n|\n```$', re.MULTILINE)
SHELL_SQL_PY_KEYWORDS = re.compile(
    r'\b(and|as|assert|async|await|break|case|class|continue|def|elif|else|esac|except|False|fi|for|from|if|'
    r'import|in|insert|into|is|join|lambda|limit|None|nonlocal|not|or|order|by|group|pass|raise|return|select|'
    r'set|then|True|try|update|delete|values|where|while|with|yield)\b',
    re.IGNORECASE
)
SYSTEM_KEYWORDS = re.compile(
    r'\b(break|case|catch|class|const|continue|default|delete|else|enum|export|extends|false|finally|fn|for|'
    r'function|if|implements|import|in|instanceof|interface|let|match|new|null|package|private|protected|public|'
    r'return|static|struct|super|switch|this|throw|trait|true|try|type|typeof|use|var|void|while)\b'
)
NUMBER_RE = re.compile(r'\b\d+(\.\d+)?\b')
STRING_RE = re.compile(r'([\'"])(?:(?=(\\?))\2.)*?\1')
COMMENT_RE = re.compile(r'(#.*$|//.*$)', re.MULTILINE)
CONSTANT_RE = re.compile(r'\b(true|false|null|undefined|None)\b')
HTML_TAG_RE = re.compile(r'(&lt;\/?)([\w:-]+)')
HTML_ATTR_RE = re.compile(r'([\w:-]+)=')
CSS_SELECTOR_RE = re.compile(r'([.#]?[\w-]+)(\s*\{)')
CSS_ATTR_RE = re.compile(r'([\w-]+)(\s*:)')


def _render_inline_markdown(text):
    text = escape(text)
    text = INLINE_CODE_RE.sub(r'<code>\1</code>', text)
    text = IMAGE_RE.sub(r'<img alt="\1" src="\2">', text)
    text = LINK_RE.sub(r'<a href="\2">\1</a>', text)
    text = BOLD_RE.sub(r'<strong>\1</strong>', text)
    text = ITALIC_RE.sub(r'<em>\1</em>', text)
    return text


def _highlight_code(code, language):
    escaped = escape(code)
    normalized_language = language.lower()

    def replace_pattern(text, pattern, class_name):
        return pattern.sub(lambda match: '<span class="%s">%s</span>' % (class_name, match.group(0)), text)

    highlighted = replace_pattern(escaped, STRING_RE, 'md-token-string')
    highlighted = replace_pattern(highlighted, COMMENT_RE, 'md-token-comment')
    highlighted = replace_pattern(highlighted, NUMBER_RE, 'md-token-number')
    highlighted = replace_pattern(highlighted, CONSTANT_RE, 'md-token-constant')

    if normalized_language in ('python', 'py', 'bash', 'sh', 'shell', 'zsh', 'yaml', 'yml', 'sql'):
        highlighted = replace_pattern(highlighted, SHELL_SQL_PY_KEYWORDS, 'md-token-keyword')
    elif normalized_language in ('javascript', 'js', 'typescript', 'ts', 'json', 'java', 'c', 'cpp', 'cxx', 'go', 'rust', 'php'):
        highlighted = replace_pattern(highlighted, SYSTEM_KEYWORDS, 'md-token-keyword')
    elif normalized_language in ('html', 'xml'):
        highlighted = HTML_TAG_RE.sub(r'\1<span class="md-token-keyword">\2</span>', highlighted)
        highlighted = HTML_ATTR_RE.sub(r'<span class="md-token-attr">\1</span>=', highlighted)
    elif normalized_language in ('css', 'scss', 'less'):
        highlighted = CSS_SELECTOR_RE.sub(r'<span class="md-token-keyword">\1</span>\2', highlighted)
        highlighted = CSS_ATTR_RE.sub(r'<span class="md-token-attr">\1</span>\2', highlighted)

    return highlighted


def render_markdown(text):
    if not text:
        return Markup('')

    placeholders = {}

    def replace_code_block(match):
        language = escape(match.group(1))
        raw_code = match.group(2).strip('\n')
        placeholder = '@@CODE_BLOCK_%d@@' % len(placeholders)
        class_attr = ' class="language-%s"' % language if language else ''
        highlighted = _highlight_code(raw_code, language)
        placeholders[placeholder] = (
            '<div class="markdown-code-block">'
            '<button type="button" class="btn btn-sm btn-light markdown-copy-btn">复制</button>'
            '<pre><code%s>%s</code></pre>'
            '</div>'
        ) % (class_attr, highlighted)
        return placeholder

    normalized = text.replace('\r\n', '\n').strip()
    normalized = CODE_BLOCK_RE.sub(replace_code_block, normalized)

    blocks = []
    paragraph_lines = []
    list_lines = []

    def flush_paragraph():
        if paragraph_lines:
            content = ' '.join(line.strip() for line in paragraph_lines)
            blocks.append('<p>%s</p>' % _render_inline_markdown(content))
            paragraph_lines[:] = []

    def flush_list():
        if list_lines:
            items = ''.join('<li>%s</li>' % _render_inline_markdown(item) for item in list_lines)
            blocks.append('<ul>%s</ul>' % items)
            list_lines[:] = []

    for raw_line in normalized.split('\n'):
        line = raw_line.rstrip()
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            flush_list()
            continue

        if stripped in placeholders:
            flush_paragraph()
            flush_list()
            blocks.append(placeholders[stripped])
            continue

        heading_match = re.match(r'^(#{1,6})\s+(.*)$', stripped)
        if heading_match:
            flush_paragraph()
            flush_list()
            level = len(heading_match.group(1))
            blocks.append('<h%d>%s</h%d>' % (
                level,
                _render_inline_markdown(heading_match.group(2).strip()),
                level
            ))
            continue

        quote_match = re.match(r'^>\s?(.*)$', stripped)
        if quote_match:
            flush_paragraph()
            flush_list()
            blocks.append('<blockquote><p>%s</p></blockquote>' % _render_inline_markdown(quote_match.group(1)))
            continue

        if stripped == '---':
            flush_paragraph()
            flush_list()
            blocks.append('<hr>')
            continue

        list_match = re.match(r'^[-*]\s+(.*)$', stripped)
        if list_match:
            flush_paragraph()
            list_lines.append(list_match.group(1).strip())
            continue

        flush_list()
        paragraph_lines.append(stripped)

    flush_paragraph()
    flush_list()

    html = '\n'.join(blocks)
    for placeholder, code_html in placeholders.items():
        html = html.replace(placeholder, code_html)
    return Markup(html)


def markdown_to_plain_text(text):
    if not text:
        return ''

    plain = text.replace('\r\n', '\n')
    plain = CODE_BLOCK_RE.sub(lambda match: '\n%s\n' % match.group(2).strip('\n'), plain)
    plain = IMAGE_RE.sub(r'\1', plain)
    plain = LINK_RE.sub(r'\1', plain)
    plain = INLINE_CODE_RE.sub(r'\1', plain)
    plain = BOLD_RE.sub(r'\1', plain)
    plain = ITALIC_RE.sub(r'\1', plain)
    plain = HEADING_RE.sub('', plain)
    plain = LIST_RE.sub('', plain)
    plain = QUOTE_RE.sub('', plain)
    plain = FENCE_RE.sub('', plain)
    plain = plain.replace('---', ' ')
    plain = re.sub(r'\n+', ' ', plain)
    plain = re.sub(r'\s+', ' ', plain)
    return plain.strip()


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def redirect_back(default='blog.index', **kwargs):
    for target in request.args.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return redirect(target)
    return redirect(url_for(default, **kwargs))
