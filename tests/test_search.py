from bluelog.extensions import db
from bluelog.models import Admin, Essay, Link, Post, Category

from tests.base import BaseTestCase


class SearchViewTestCase(BaseTestCase):
    def test_search_can_find_post_essay_link_and_admin_info(self):
        admin = Admin.query.first()
        admin.about = '这里记录 Flask 搜索与个人介绍。'
        admin.blog_sub_title = '一个支持全文搜索的测试博客'

        category = Category.query.first()
        category.name = 'Flask 分类'
        db.session.add(Post(title='Flask 搜索实践', body='文章正文包含统一检索能力', category=category))

        essay = Essay(body='今天补了 Flask 全文搜索入口')
        essay.images = ['/uploads/a.jpg', '/uploads/b.jpg']
        db.session.add(essay)
        db.session.add(Link(name='Flask 官方文档', url='https://flask.palletsprojects.com/'))
        db.session.commit()

        response = self.client.get('/search?q=Flask')
        text = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('搜索结果', text)
        self.assertIn('Flask 搜索实践', text)
        self.assertIn('今天补了 Flask 全文搜索入口', text)
        self.assertIn('Flask 分类', text)
        self.assertIn('Flask 官方文档', text)
        self.assertIn('这里记录 Flask 搜索与个人介绍。', text)

    def test_search_form_submit_accepts_keyword(self):
        response = self.client.get('/search?q=关键字')

        self.assertEqual(response.status_code, 200)
        self.assertIn('关键词“关键字”', response.get_data(as_text=True))

    def test_search_without_query_shows_prompt(self):
        response = self.client.get('/search')

        self.assertEqual(response.status_code, 200)
        self.assertIn('请输入关键词进行全文搜索。', response.get_data(as_text=True))
