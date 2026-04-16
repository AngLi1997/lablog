$(function () {
    var searchState = {
        controller: null,
        activeUrl: null
    };

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
        });
    }

    function getViewerPlugins() {
        if (!window.toastui || !window.toastui.Editor || !window.toastui.Editor.plugin) {
            return [];
        }

        if (!window.toastui.Editor.plugin.codeSyntaxHighlight) {
            return [];
        }

        return [window.toastui.Editor.plugin.codeSyntaxHighlight];
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
                initialValue: initialValue,
                plugins: getViewerPlugins()
            });
            element.dataset.viewerReady = 'true';
            enhanceCodeBlocks(element);
        });
    }

    function escapeHtml(value) {
        return String(value || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function truncateText(value, maxLength) {
        if (!value) {
            return '';
        }
        if (value.length <= maxLength) {
            return value;
        }
        return value.slice(0, maxLength) + '...';
    }

    function closeSearchPanel() {
        document.querySelectorAll('[data-search-panel]').forEach(function (panel) {
            panel.classList.add('d-none');
        });
    }

    function focusSearchResult(items, nextIndex) {
        items.forEach(function (item, index) {
            if (index === nextIndex) {
                item.classList.add('is-active');
                item.focus();
            } else {
                item.classList.remove('is-active');
            }
        });
    }

    function renderSearchItems(panel, items) {
        var results = panel.querySelector('[data-search-results]');
        var empty = panel.querySelector('[data-search-empty]');

        results.innerHTML = '';
        if (!items.length) {
            empty.classList.remove('d-none');
            panel.classList.remove('d-none');
            return;
        }

        empty.classList.add('d-none');
        items.forEach(function (item) {
            var link = document.createElement('a');
            link.className = 'navbar-search__result';
            link.href = item.url;
            if (/^https?:\/\//.test(item.url)) {
                link.target = '_blank';
                link.rel = 'noopener noreferrer';
            }
            link.innerHTML =
                '<span class="navbar-search__type">' + escapeHtml(item.type) + '</span>' +
                '<strong class="navbar-search__title">' + escapeHtml(item.title) + '</strong>' +
                '<span class="navbar-search__summary">' + escapeHtml(truncateText(item.summary, 70)) + '</span>';
            results.appendChild(link);
        });
        panel.classList.remove('d-none');
    }

    function bindSearchAutocomplete() {
        var input = document.querySelector('[data-search-input]');
        var panel = document.querySelector('[data-search-panel]');
        var searchBox = document.querySelector('.navbar-search');
        var debounceTimer;

        if (!input || !panel || !searchBox || !window.fetch) {
            return;
        }

        input.addEventListener('input', function () {
            var query = input.value.trim();
            var url;

            window.clearTimeout(debounceTimer);
            if (!query) {
                if (searchState.controller) {
                    searchState.controller.abort();
                }
                closeSearchPanel();
                return;
            }

            debounceTimer = window.setTimeout(function () {
                if (searchState.controller) {
                    searchState.controller.abort();
                }

                searchState.controller = new AbortController();
                url = input.dataset.searchUrl + '?q=' + encodeURIComponent(query);
                searchState.activeUrl = url;

                window.fetch(url, {
                    signal: searchState.controller.signal,
                    headers: {'X-Requested-With': 'XMLHttpRequest'}
                })
                    .then(function (response) {
                        return response.ok ? response.json() : {items: []};
                    })
                    .then(function (payload) {
                        if (searchState.activeUrl !== url) {
                            return;
                        }
                        renderSearchItems(panel, payload.items || []);
                    })
                    .catch(function (error) {
                        if (error.name !== 'AbortError') {
                            closeSearchPanel();
                        }
                    });
            }, 180);
        });

        input.addEventListener('focus', function () {
            if (input.value.trim()) {
                panel.classList.remove('d-none');
            }
        });

        input.addEventListener('keydown', function (event) {
            var items = Array.prototype.slice.call(panel.querySelectorAll('.navbar-search__result'));
            var currentIndex = items.findIndex(function (item) {
                return item.classList.contains('is-active') || item === document.activeElement;
            });

            if (event.key === 'ArrowDown' && items.length) {
                event.preventDefault();
                focusSearchResult(items, currentIndex >= items.length - 1 ? 0 : currentIndex + 1);
                return;
            }

            if (event.key === 'ArrowUp' && items.length) {
                event.preventDefault();
                if (currentIndex <= 0) {
                    items.forEach(function (item) {
                        item.classList.remove('is-active');
                    });
                    input.focus();
                    return;
                }
                focusSearchResult(items, currentIndex - 1);
                return;
            }

            if (event.key === 'Escape') {
                closeSearchPanel();
                return;
            }

            if (event.key === 'Enter') {
                if (document.activeElement && document.activeElement.classList.contains('navbar-search__result')) {
                    document.activeElement.click();
                }
            }
        });

        document.addEventListener('click', function (event) {
            if (!event.target.closest('.navbar-search')) {
                closeSearchPanel();
            }
        });

        searchBox.addEventListener('submit', function (event) {
            var query = input.value.trim();
            if (!query) {
                event.preventDefault();
                closeSearchPanel();
            }
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
    bindSearchAutocomplete();
    document.addEventListener('click', function (event) {
        var button = event.target.closest('.markdown-copy-btn');
        if (!button) {
            return;
        }
        copyCodeFromButton(button);
    });
});
