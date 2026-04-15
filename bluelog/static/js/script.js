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

    $('[data-toggle="tooltip"]').tooltip(
        {title: render_time}
    );
    enhanceCodeBlocks();
});
