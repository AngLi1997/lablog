$(function () {
    function render_time() {
        return moment($(this).data('timestamp')).format('lll')
    }

    function enhanceCodeBlocks() {
        if (!window.hljs) {
            return;
        }

        document.querySelectorAll('.markdown-body pre code').forEach(function (block) {
            if (block.dataset.highlighted === 'yes') {
                return;
            }
            window.hljs.highlightElement(block);
        });
    }

    function copyCodeFromButton(button) {
        var wrapper = button.closest('.markdown-code-block');
        var code = wrapper ? wrapper.querySelector('code') : null;
        var text = code ? code.textContent : '';
        var icon = button.querySelector('.markdown-copy-icon');

        if (!text) {
            return;
        }

        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(function () {
                button.classList.add('is-copied');
                if (icon) {
                    icon.setAttribute('data-copied', 'true');
                }
                window.setTimeout(function () {
                    button.classList.remove('is-copied');
                    if (icon) {
                        icon.removeAttribute('data-copied');
                    }
                }, 1500);
            });
        }
    }

    $('[data-toggle="tooltip"]').tooltip(
        {title: render_time}
    );
    enhanceCodeBlocks();
    document.addEventListener('click', function (event) {
        var button = event.target.closest('.markdown-copy-btn');
        if (!button) {
            return;
        }
        copyCodeFromButton(button);
    });
});
