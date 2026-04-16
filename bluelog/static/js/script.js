$(function () {
    function render_time() {
        return moment($(this).data('timestamp')).format('lll')
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

    function enhanceCodeBlocks(container) {
        var root = container || document;

        root.querySelectorAll('.markdown-body pre, .toastui-editor-contents pre').forEach(function (pre) {
            var wrapper;
            var copyButton;
            var code = pre.querySelector('code');

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

            if (code && window.hljs && code.dataset.highlighted !== 'yes') {
                window.hljs.highlightElement(code);
            }
        });
    }

    function initToastuiViewers() {
        if (!window.toastui || !window.toastui.Editor || !window.toastui.Editor.factory) {
            return;
        }

        document.querySelectorAll('.toastui-viewer').forEach(function (element) {
            var initialValue;

            if (element.dataset.viewerReady === 'true') {
                return;
            }

            initialValue = '';
            if (element.dataset.markdownContent) {
                try {
                    initialValue = JSON.parse(element.dataset.markdownContent);
                } catch (error) {
                    initialValue = element.dataset.markdownContent;
                }
            }

            element.innerHTML = '';
            window.toastui.Editor.factory({
                el: element,
                viewer: true,
                initialValue: initialValue
            });
            element.dataset.viewerReady = 'true';
            enhanceCodeBlocks(element);
        });
    }

    window.BluelogMarkdown = {
        enhanceCodeBlocks: enhanceCodeBlocks,
        initToastuiViewers: initToastuiViewers
    };

    $('[data-toggle="tooltip"]').tooltip(
        {title: render_time}
    );
    initToastuiViewers();
    enhanceCodeBlocks();
    document.addEventListener('click', function (event) {
        var button = event.target.closest('.markdown-copy-btn');
        if (!button) {
            return;
        }
        copyCodeFromButton(button);
    });
});
