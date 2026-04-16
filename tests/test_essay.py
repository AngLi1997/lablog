from io import BytesIO

from bluelog.models import Essay

from tests.base import BaseTestCase


class EssayViewTestCase(BaseTestCase):
    def test_essay_table_is_available(self):
        response = self.client.get('/essays')
        self.assertEqual(response.status_code, 200)

    def test_guest_can_view_essay_timeline(self):
        essay = Essay(body='今天的随笔')
        essay.images = ['/uploads/a.jpg']
        from bluelog.extensions import db
        db.session.add(essay)
        db.session.commit()

        response = self.client.get('/essays')

        self.assertEqual(response.status_code, 200)
        self.assertIn('随笔时间轴', response.get_data(as_text=True))
        self.assertIn('\\u4eca\\u5929\\u7684\\u968f\\u7b14', response.get_data(as_text=True))
        self.assertIn('/uploads/a.jpg', response.get_data(as_text=True))

    def test_admin_can_create_essay_from_form(self):
        self.login()

        response = self.client.post('/admin/essay/new', data={
            'body': '表单随笔',
            'images': '["/uploads/1.jpg","/uploads/2.jpg"]'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('随笔已发布。', response.get_data(as_text=True))
        essay = Essay.query.first()
        self.assertIsNotNone(essay)
        self.assertEqual(essay.images, ['/uploads/1.jpg', '/uploads/2.jpg'])

    def test_essay_form_rejects_more_than_nine_images(self):
        self.login()
        images = ['/%s.jpg' % index for index in range(10)]

        response = self.client.post('/admin/essay/new', data={
            'body': '图片过多',
            'images': str(images).replace("'", '"')
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn('随笔最多只能上传 9 张图片。', response.get_data(as_text=True))

    def test_upload_image_accepts_file_without_extension(self):
        self.login()

        response = self.client.post('/admin/upload-image', data={
            'image': (BytesIO(
                b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
                b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
                b'\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02'
                b'\xfeA\xed\xd4\xb3\x00\x00\x00\x00IEND\xaeB`\x82'
            ), 'blob')
        })

        self.assertEqual(response.status_code, 201)
        payload = self.decode_json(response)
        self.assertTrue(payload['filename'].endswith('.png'))
        self.assertIn('/uploads/', payload['url'])

    def test_upload_image_rejects_non_image_file(self):
        self.login()

        response = self.client.post('/admin/upload-image', data={
            'image': (BytesIO(b'not-an-image'), 'blob')
        })

        self.assertEqual(response.status_code, 400)
        payload = self.decode_json(response)
        self.assertEqual(payload['message'], '图片格式不支持。')
