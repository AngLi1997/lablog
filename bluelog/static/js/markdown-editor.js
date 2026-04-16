(function () {
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

    function syncEditorValue(textarea, editor) {
        textarea.value = editor.getMarkdown();
    }

    function buildEditor(textarea) {
        if (!window.toastui || !window.toastui.Editor) {
            return;
        }

        var container = document.createElement('div');
        var editorRoot = document.createElement('div');
        var help = document.createElement('small');
        var editor;
        var form = textarea.form;
        var rows = parseInt(textarea.getAttribute('rows') || '20', 10);
        var editorHeight = Math.max(rows * 24, 320) + 'px';

        container.className = 'markdown-editor';
        editorRoot.className = 'toastui-editor-host';
        help.className = 'form-text text-muted markdown-help';
        help.textContent = '使用 Toast UI Editor，可直接粘贴图片上传。';

        textarea.classList.add('markdown-textarea');
        textarea.hidden = true;
        textarea.parentNode.insertBefore(container, textarea);
        container.appendChild(editorRoot);
        container.appendChild(textarea);
        container.appendChild(help);

        editor = new window.toastui.Editor({
            el: editorRoot,
            initialValue: textarea.value || '',
            initialEditType: 'markdown',
            previewStyle: 'vertical',
            height: editorHeight,
            usageStatistics: false,
            hooks: {
                addImageBlobHook: function (blob, callback) {
                    help.textContent = '正在上传图片...';
                    uploadPastedImage(blob).then(function (payload) {
                        callback(payload.url, payload.filename || 'image');
                        help.textContent = '图片已上传并插入内容。';
                    }).catch(function (error) {
                        help.textContent = error.message || '图片上传失败。';
                    });
                }
            }
        });

        textarea._toastuiEditor = editor;
        syncEditorValue(textarea, editor);

        editor.on('change', function () {
            syncEditorValue(textarea, editor);
        });

        if (form) {
            form.addEventListener('submit', function () {
                syncEditorValue(textarea, editor);
            });
        }

        window.setTimeout(function () {
            if (window.BluelogMarkdown && window.BluelogMarkdown.enhanceCodeBlocks) {
                window.BluelogMarkdown.enhanceCodeBlocks(container);
            }
        }, 0);
    }

    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('textarea[data-markdown-editor="true"]').forEach(buildEditor);
    });
})();
