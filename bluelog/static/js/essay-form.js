(function () {
    function getCsrfToken(form) {
        var csrfInput = form.querySelector('input[name="csrf_token"]');
        return csrfInput ? csrfInput.value : '';
    }

    function parseJsonSafely(response) {
        return response.text().then(function (text) {
            if (!text) {
                return {};
            }

            try {
                return JSON.parse(text);
            } catch (error) {
                throw new Error('服务器返回了非 JSON 响应，请检查登录状态或 CSRF 配置。');
            }
        });
    }

    function parseImages(input) {
        try {
            var data = JSON.parse(input.value || '[]');
            return Array.isArray(data) ? data : [];
        } catch (error) {
            return [];
        }
    }

    function syncImages(input, images) {
        input.value = JSON.stringify(images);
    }

    function renderImages(container, input) {
        var images = parseImages(input);
        container.innerHTML = '';

        if (!images.length) {
            return;
        }

        images.forEach(function (url, index) {
            var item = document.createElement('div');
            item.className = 'essay-image-list__item';

            var image = document.createElement('img');
            image.src = url;
            image.alt = '已上传图片 ' + (index + 1);

            var removeButton = document.createElement('button');
            removeButton.type = 'button';
            removeButton.className = 'essay-image-list__remove';
            removeButton.textContent = '删除';
            removeButton.addEventListener('click', function () {
                var nextImages = parseImages(input).filter(function (_, currentIndex) {
                    return currentIndex !== index;
                });
                syncImages(input, nextImages);
                renderImages(container, input);
            });

            item.appendChild(image);
            item.appendChild(removeButton);
            container.appendChild(item);
        });
    }

    function setFeedback(feedback, message, isError) {
        feedback.textContent = message;
        feedback.classList.toggle('text-danger', Boolean(isError));
        feedback.classList.toggle('text-muted', !isError);
    }

    function uploadFiles(files, uploadUrl, input, preview, feedback, csrfToken) {
        var queue = Array.from(files || []);
        if (!queue.length) {
            return;
        }

        if (parseImages(input).length + queue.length > 9) {
            setFeedback(feedback, '最多只能保留 9 张图片。', true);
            return;
        }

        setFeedback(feedback, '图片上传中，请稍候...', false);

        Promise.all(queue.map(function (file) {
            var formData = new FormData();
            formData.append('image', file);
            formData.append('csrf_token', csrfToken);
            return fetch(uploadUrl, {
                method: 'POST',
                body: formData,
                credentials: 'same-origin',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            }).then(function (response) {
                return parseJsonSafely(response).then(function (payload) {
                    if (!response.ok) {
                        throw new Error(payload.message || '上传失败。');
                    }
                    return payload;
                });
            }).then(function (payload) {
                return payload.url;
            });
        })).then(function (urls) {
            var nextImages = parseImages(input).concat(urls);
            syncImages(input, nextImages);
            renderImages(preview, input);
            setFeedback(feedback, '图片上传完成。', false);
        }).catch(function (error) {
            setFeedback(feedback, error.message || '上传失败。', true);
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        var form = document.querySelector('.essay-form');
        if (!form) {
            return;
        }

        var input = form.querySelector('#essay-images-input');
        var uploader = form.querySelector('#essay-image-uploader');
        var preview = form.querySelector('.essay-image-list');
        var feedback = form.querySelector('.essay-upload-feedback');
        var uploadUrl = form.dataset.uploadUrl;
        var csrfToken = getCsrfToken(form);

        renderImages(preview, input);

        uploader.addEventListener('change', function () {
            uploadFiles(uploader.files, uploadUrl, input, preview, feedback, csrfToken);
            uploader.value = '';
        });
    });
})();
