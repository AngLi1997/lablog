from bluelog.models import Category, Essay, Post

from tests.base import BaseTestCase


class ApiCrudTestCase(BaseTestCase):
    def test_api_requires_login(self):
        response = self.client.get('/api/posts')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login', response.location)

    def test_post_category_and_essay_crud(self):
        self.login()

        category_response = self.client.post('/api/categories', json={'name': '技术'})
        self.assertEqual(category_response.status_code, 201)
        category_id = self.decode_json(category_response)['item']['id']

        post_response = self.create_post(title='接口文章', body='接口正文', category_id=category_id)
        self.assertEqual(post_response.status_code, 201)
        post_id = self.decode_json(post_response)['item']['id']

        update_post_response = self.client.patch('/api/posts/%s' % post_id, json={
            'title': '接口文章已更新',
            'body': '新的正文',
            'can_comment': False
        })
        self.assertEqual(update_post_response.status_code, 200)
        self.assertEqual(Post.query.get(post_id).title, '接口文章已更新')
        self.assertFalse(Post.query.get(post_id).can_comment)

        essay_response = self.create_essay(body='接口随笔', images=['/uploads/a.jpg'] * 4)
        self.assertEqual(essay_response.status_code, 201)
        essay_id = self.decode_json(essay_response)['item']['id']

        update_essay_response = self.client.patch('/api/essays/%s' % essay_id, json={
            'body': '新的随笔',
            'images': ['/uploads/b.jpg']
        })
        self.assertEqual(update_essay_response.status_code, 200)
        self.assertEqual(Essay.query.get(essay_id).images, ['/uploads/b.jpg'])

        delete_essay_response = self.client.delete('/api/essays/%s' % essay_id)
        self.assertEqual(delete_essay_response.status_code, 200)
        self.assertIsNone(Essay.query.get(essay_id))

        delete_post_response = self.client.delete('/api/posts/%s' % post_id)
        self.assertEqual(delete_post_response.status_code, 200)
        self.assertIsNone(Post.query.get(post_id))

        update_category_response = self.client.patch('/api/categories/%s' % category_id, json={'name': '开发'})
        self.assertEqual(update_category_response.status_code, 200)
        self.assertEqual(Category.query.get(category_id).name, '开发')

        delete_category_response = self.client.delete('/api/categories/%s' % category_id)
        self.assertEqual(delete_category_response.status_code, 200)
        self.assertIsNone(Category.query.get(category_id))

    def test_essay_api_validates_image_limit(self):
        self.login()
        response = self.client.post('/api/essays', json={
            'body': '太多图片',
            'images': ['/uploads/%s.jpg' % index for index in range(10)]
        })

        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.decode_json(response)['message'], '图片数量必须在 0 到 9 张之间。')
