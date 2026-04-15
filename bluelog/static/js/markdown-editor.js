(function () {
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

    function buildToolbar(textarea) {
        var container = document.createElement('div');
        container.className = 'markdown-editor';

        var toolbar = document.createElement('div');
        toolbar.className = 'markdown-toolbar';

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

        var help = document.createElement('small');
        help.className = 'form-text text-muted markdown-help';
        help.textContent = '使用 Markdown 编写内容，旧 HTML 内容也会兼容显示。';

        textarea.classList.add('markdown-textarea');
        textarea.parentNode.insertBefore(container, textarea);
        container.appendChild(toolbar);
        container.appendChild(textarea);
        container.appendChild(help);

        toolbar.addEventListener('click', function (event) {
            var button = event.target.closest('[data-action]');
            if (!button) {
                return;
            }
            handleAction(textarea, button.dataset.action);
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('textarea[data-markdown-editor="true"]').forEach(buildToolbar);
    });
})();
