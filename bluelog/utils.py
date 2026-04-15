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
import os
import re
import uuid
from html import escape

from flask import request, redirect, url_for, current_app
from markupsafe import Markup
from werkzeug.utils import secure_filename


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


def _render_inline_markdown(text):
    text = escape(text)
    text = INLINE_CODE_RE.sub(r'<code>\1</code>', text)
    text = IMAGE_RE.sub(r'<img alt="\1" src="\2">', text)
    text = LINK_RE.sub(r'<a href="\2">\1</a>', text)
    text = BOLD_RE.sub(r'<strong>\1</strong>', text)
    text = ITALIC_RE.sub(r'<em>\1</em>', text)
    return text


def render_markdown(text):
    if not text:
        return Markup('')

    placeholders = {}

    def replace_code_block(match):
        language = escape(match.group(1))
        raw_code = match.group(2).strip('\n')
        placeholder = '@@CODE_BLOCK_%d@@' % len(placeholders)
        class_attr = ' class="language-%s"' % language if language else ''
        placeholders[placeholder] = (
            '<div class="markdown-code-block">'
            '<button type="button" class="markdown-copy-btn" aria-label="复制代码" title="复制代码">'
            '<span class="markdown-copy-icon" aria-hidden="true"></span>'
            '</button>'
            '<pre><code%s>%s</code></pre>'
            '</div>'
        ) % (class_attr, escape(raw_code))
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


def allowed_image_file(filename):
    if '.' not in filename:
        return False
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in current_app.config['BLUELOG_UPLOAD_EXTENSIONS']


def save_image_file(storage):
    filename = secure_filename(storage.filename or '')
    if not filename or not allowed_image_file(filename):
        raise ValueError('Invalid image file.')

    upload_path = current_app.config['BLUELOG_UPLOAD_PATH']
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)

    extension = filename.rsplit('.', 1)[1].lower()
    generated_name = '%s.%s' % (uuid.uuid4().hex, extension)
    final_path = os.path.join(upload_path, generated_name)
    storage.save(final_path)
    return generated_name
