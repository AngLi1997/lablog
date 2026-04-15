(function () {
    function escapeHtml(text) {
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function renderInlineMarkdown(text) {
        var html = escapeHtml(text);
        html = html.replace(/`([^`\n]+)`/g, '<code>$1</code>');
        html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img alt="$1" src="$2">');
        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/(^|[^*])\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '$1<em>$2</em>');
        return html;
    }

    function renderMarkdown(text) {
        var placeholders = [];

        text = text.replace(/\r\n/g, '\n').trim();
        text = text.replace(/```([\w+-]*)\n([\s\S]*?)```/g, function (_, language, code) {
            var placeholder = '@@CODE_BLOCK_' + placeholders.length + '@@';
            var classAttr = language ? ' class="language-' + language + '"' : '';
            placeholders.push('<pre><code' + classAttr + '>' + escapeHtml(code.replace(/^\n+|\n+$/g, '')) + '</code></pre>');
            return placeholder;
        });

        var blocks = [];
        var paragraphLines = [];
        var listLines = [];

        function flushParagraph() {
            if (paragraphLines.length) {
                blocks.push('<p>' + renderInlineMarkdown(paragraphLines.join(' ')) + '</p>');
                paragraphLines = [];
            }
        }

        function flushList() {
            if (listLines.length) {
                blocks.push('<ul>' + listLines.map(function (item) {
                    return '<li>' + renderInlineMarkdown(item) + '</li>';
                }).join('') + '</ul>');
                listLines = [];
            }
        }

        text.split('\n').forEach(function (rawLine) {
            var stripped = rawLine.trim();
            var headingMatch;
            var quoteMatch;
            var listMatch;

            if (!stripped) {
                flushParagraph();
                flushList();
                return;
            }

            if (/^@@CODE_BLOCK_\d+@@$/.test(stripped)) {
                flushParagraph();
                flushList();
                blocks.push(stripped);
                return;
            }

            headingMatch = stripped.match(/^(#{1,6})\s+(.*)$/);
            if (headingMatch) {
                flushParagraph();
                flushList();
                blocks.push('<h' + headingMatch[1].length + '>' + renderInlineMarkdown(headingMatch[2]) + '</h' + headingMatch[1].length + '>');
                return;
            }

            quoteMatch = stripped.match(/^>\s?(.*)$/);
            if (quoteMatch) {
                flushParagraph();
                flushList();
                blocks.push('<blockquote><p>' + renderInlineMarkdown(quoteMatch[1]) + '</p></blockquote>');
                return;
            }

            if (stripped === '---') {
                flushParagraph();
                flushList();
                blocks.push('<hr>');
                return;
            }

            listMatch = stripped.match(/^[-*]\s+(.*)$/);
            if (listMatch) {
                flushParagraph();
                listLines.push(listMatch[1]);
                return;
            }

            flushList();
            paragraphLines.push(stripped);
        });

        flushParagraph();
        flushList();

        return blocks.join('\n').replace(/@@CODE_BLOCK_(\d+)@@/g, function (_, index) {
            return placeholders[Number(index)];
        });
    }

    function enhanceCodeBlocks(container) {
        container.querySelectorAll('pre').forEach(function (pre) {
            var wrapper;
            var copyButton;
            var code;

            if (!(pre.parentNode && pre.parentNode.classList.contains('markdown-code-block'))) {
                wrapper = document.createElement('div');
                wrapper.className = 'markdown-code-block';

                copyButton = document.createElement('button');
                copyButton.type = 'button';
                copyButton.className = 'markdown-copy-btn';
                copyButton.setAttribute('aria-label', '复制代码');
                copyButton.setAttribute('title', '复制代码');
                copyButton.textContent = '复制';

                pre.parentNode.insertBefore(wrapper, pre);
                wrapper.appendChild(copyButton);
                wrapper.appendChild(pre);
            }

            code = pre.querySelector('code');
            if (code && window.hljs) {
                window.hljs.highlightElement(code);
            }
        });
    }

    function copyCodeFromButton(button) {
        var wrapper = button.closest('.markdown-code-block');
        var code = wrapper ? wrapper.querySelector('code') : null;
        var text = code ? code.textContent : '';

        if (!text) {
            return;
        }

        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(function () {
                button.textContent = '已复制';
                window.setTimeout(function () {
                    button.textContent = '复制';
                }, 1500);
            });
        }
    }

    function insertText(textarea, text) {
        var start = textarea.selectionStart;
        var end = textarea.selectionEnd;
        var value = textarea.value;
        textarea.value = value.slice(0, start) + text + value.slice(end);
        textarea.focus();
        textarea.selectionStart = start + text.length;
        textarea.selectionEnd = start + text.length;
    }

    function getCsrfToken() {
        var input = document.querySelector('input[name="csrf_token"]');
        return input ? input.value : '';
    }

    function uploadPastedImage(file) {
        var formData = new FormData();
        formData.append('image', file, file.name || 'clipboard-image.png');
        return fetch('/admin/upload-image', {
            method: 'POST',
            body: formData,
            credentials: 'same-origin',
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        }).then(function (response) {
            return response.json().then(function (payload) {
                if (!response.ok) {
                    throw new Error(payload.message || 'Upload failed.');
                }
                return payload;
            });
        });
    }

    function bindPasteUpload(textarea, help) {
        textarea.addEventListener('paste', function (event) {
            var items = event.clipboardData && event.clipboardData.items;
            var imageItem;
            var file;

            if (!items) {
                return;
            }

            imageItem = Array.prototype.find.call(items, function (item) {
                return item.kind === 'file' && item.type.indexOf('image/') === 0;
            });

            if (!imageItem) {
                return;
            }

            file = imageItem.getAsFile();
            if (!file) {
                return;
            }

            event.preventDefault();
            textarea.disabled = true;
            help.textContent = '正在上传粘贴的图片...';

            uploadPastedImage(file).then(function (payload) {
                insertText(textarea, '![](' + payload.url + ')');
                help.textContent = '图片已上传，已插入 Markdown。';
            }).catch(function (error) {
                help.textContent = error.message || '图片上传失败。';
            }).finally(function () {
                textarea.disabled = false;
                textarea.focus();
            });
        });
    }

    function wrapSelection(textarea, prefix, suffix, placeholder) {
        var start = textarea.selectionStart;
        var end = textarea.selectionEnd;
        var value = textarea.value;
        var selected = value.slice(start, end) || placeholder || '';
        var replacement = prefix + selected + suffix;
        textarea.value = value.slice(0, start) + replacement + value.slice(end);
        textarea.focus();
        textarea.selectionStart = start + prefix.length;
        textarea.selectionEnd = start + prefix.length + selected.length;
    }

    function insertBlock(textarea, before, after, placeholder) {
        var start = textarea.selectionStart;
        var end = textarea.selectionEnd;
        var value = textarea.value;
        var selected = value.slice(start, end) || placeholder || '';
        var replacement = before + selected + after;
        textarea.value = value.slice(0, start) + replacement + value.slice(end);
        textarea.focus();
        textarea.selectionStart = start + before.length;
        textarea.selectionEnd = start + before.length + selected.length;
    }

    function handleAction(textarea, action) {
        if (action === 'bold') {
            wrapSelection(textarea, '**', '**', 'bold text');
        } else if (action === 'italic') {
            wrapSelection(textarea, '*', '*', 'italic text');
        } else if (action === 'link') {
            wrapSelection(textarea, '[', '](https://example.com)', 'link text');
        } else if (action === 'image') {
            wrapSelection(textarea, '![', '](https://example.com/image.jpg)', 'alt text');
        } else if (action === 'code') {
            insertBlock(textarea, '\n```text\n', '\n```\n', 'code');
        } else if (action === 'quote') {
            insertBlock(textarea, '\n> ', '\n', 'quoted text');
        } else if (action === 'ul') {
            insertBlock(textarea, '\n- ', '\n', 'list item');
        } else if (action === 'h2') {
            insertBlock(textarea, '\n## ', '\n', 'Heading');
        }
    }

    function handleTabKey(textarea) {
        textarea.addEventListener('keydown', function (event) {
            var start;
            var end;
            var value;

            if (event.key !== 'Tab') {
                return;
            }

            event.preventDefault();
            start = textarea.selectionStart;
            end = textarea.selectionEnd;
            value = textarea.value;
            textarea.value = value.slice(0, start) + '\t' + value.slice(end);
            textarea.selectionStart = start + 1;
            textarea.selectionEnd = start + 1;
        });
    }

    function buildToolbar(textarea) {
        var container = document.createElement('div');
        container.className = 'markdown-editor';

        var toolbar = document.createElement('div');
        toolbar.className = 'markdown-toolbar';

        var previewButton = document.createElement('button');
        previewButton.type = 'button';
        previewButton.className = 'btn btn-sm btn-outline-secondary markdown-toolbar-btn markdown-preview-toggle';
        previewButton.textContent = 'Preview';
        previewButton.dataset.mode = 'edit';
        toolbar.appendChild(previewButton);

        [
            ['bold', 'Bold'],
            ['italic', 'Italic'],
            ['h2', 'H2'],
            ['link', 'Link'],
            ['image', 'Image'],
            ['quote', 'Quote'],
            ['ul', 'List'],
            ['code', 'Code']
        ].forEach(function (item) {
            var button = document.createElement('button');
            button.type = 'button';
            button.className = 'btn btn-sm btn-outline-secondary markdown-toolbar-btn';
            button.dataset.action = item[0];
            button.textContent = item[1];
            toolbar.appendChild(button);
        });

        var preview = document.createElement('div');
        preview.className = 'markdown-preview markdown-body';
        preview.hidden = true;

        var help = document.createElement('small');
        help.className = 'form-text text-muted markdown-help';
        help.textContent = '支持 Markdown，可直接粘贴截图上传图片。';

        textarea.classList.add('markdown-textarea');
        handleTabKey(textarea);
        bindPasteUpload(textarea, help);
        textarea.parentNode.insertBefore(container, textarea);
        container.appendChild(toolbar);
        container.appendChild(textarea);
        container.appendChild(preview);
        container.appendChild(help);

        toolbar.addEventListener('click', function (event) {
            var button = event.target.closest('button');
            if (!button) {
                return;
            }
            if (button === previewButton) {
                if (previewButton.dataset.mode === 'edit') {
                    preview.innerHTML = renderMarkdown(textarea.value);
                    enhanceCodeBlocks(preview);
                    preview.hidden = false;
                    textarea.hidden = true;
                    textarea.readOnly = true;
                    previewButton.dataset.mode = 'preview';
                    previewButton.textContent = 'Edit';
                } else {
                    preview.hidden = true;
                    textarea.hidden = false;
                    textarea.readOnly = false;
                    previewButton.dataset.mode = 'edit';
                    previewButton.textContent = 'Preview';
                    textarea.focus();
                }
                return;
            }
            if (!button.dataset.action) {
                return;
            }
            handleAction(textarea, button.dataset.action);
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('textarea[data-markdown-editor="true"]').forEach(buildToolbar);
        document.querySelectorAll('.markdown-body').forEach(enhanceCodeBlocks);
        document.addEventListener('click', function (event) {
            var button = event.target.closest('.markdown-copy-btn');
            if (!button) {
                return;
            }
            copyCodeFromButton(button);
        });
    });
})();
