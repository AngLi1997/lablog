from bluelog.extensions import db
from bluelog.models import Admin, Essay, Link, Post, Category

from tests.base import BaseTestCase


class SeoAndSearchApiTestCase(BaseTestCase):
    def test_post_page_contains_basic_seo_meta(self):
        category = Category.query.first()
        post = Post(title='SEO 标题', body='用于 SEO 描述的正文内容', category=category)
        db.session.add(post)
        db.session.commit()

        response = self.client.get('/post/%s' % post.id)
        text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('meta name="description"', text)
        self.assertIn('meta property="og:title"', text)
        self.assertIn('link rel="canonical"', text)
        self.assertIn('SEO 标题', text)

    def test_search_api_returns_suggestion_items(self):
        admin = Admin.query.first()
        admin.about = '这里有 Flask 搜索介绍'
        category = Category.query.first()
        category.name = 'Flask 分类'
        db.session.add(Post(title='Flask 文章', body='文章摘要', category=category))
        essay = Essay(body='Flask 随笔内容')
        essay.images = ['/uploads/1.jpg']
        db.session.add(essay)
        db.session.add(Link(name='Flask 官网', url='https://flask.palletsprojects.com/'))
        db.session.commit()

        response = self.client.get('/api/search?q=Flask')
        payload = self.decode_json(response)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload['items'])
        titles = [item['title'] for item in payload['items']]
        self.assertIn('Flask 文章', titles)
        self.assertIn('Flask 分类', titles)

    def test_search_api_returns_empty_for_blank_query(self):
        response = self.client.get('/api/search?q=')
        payload = self.decode_json(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload['items'], [])
