import json
import unittest

from bluelog import create_app
from bluelog.extensions import db
from bluelog.models import Admin, Category


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.config.update(
            BLUELOG_EMAIL='admin@example.com',
            SERVER_NAME='localhost.localdomain'
        )
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        admin = Admin(
            username='admin',
            blog_title='测试博客',
            blog_sub_title='测试副标题',
            name='测试站长',
            about='关于我'
        )
        admin.set_password('password')
        db.session.add(admin)
        db.session.add(Category(name='默认分类'))
        db.session.commit()

        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self):
        return self.client.post('/auth/login', data={
            'username': 'admin',
            'password': 'password'
        }, follow_redirects=True)

    def create_post(self, title='测试文章', body='文章内容', category_id=1):
        return self.client.post('/api/posts', json={
            'title': title,
            'body': body,
            'category_id': category_id
        })

    def create_essay(self, body='随笔内容', images=None):
        return self.client.post('/api/essays', json={
            'body': body,
            'images': images or []
        })

    @staticmethod
    def decode_json(response):
        return json.loads(response.data.decode('utf-8'))
