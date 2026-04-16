# -*- coding: utf-8 -*-
"""
    :author: Ang Li
    :url: http://liangliang.world
    :copyright: © 2026 Ang Li <liangliangaichirou@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
import logging
import os
from logging.handlers import SMTPHandler, RotatingFileHandler

import click
import sqlalchemy as sa
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from flask_login import current_user
from flask_sqlalchemy import get_debug_queries
from flask_wtf.csrf import CSRFError

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


def load_runtime_env():
    config_name = os.getenv('FLASK_CONFIG', 'development')
    env_file = {
        'development': '.env.example',
        'production': '.env'
    }.get(config_name)

    if env_file is None:
        return

    dotenv_path = os.path.join(basedir, env_file)
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path, override=False)


load_runtime_env()

from bluelog.blueprints.admin import admin_bp
from bluelog.blueprints.api import api_bp
from bluelog.blueprints.auth import auth_bp
from bluelog.blueprints.blog import blog_bp
from bluelog.extensions import bootstrap, db, login_manager, csrf, mail, moment, toolbar, migrate
from bluelog.models import Admin, Post, Category, Comment, Link, Essay
from bluelog.settings import config
from bluelog.utils import render_markdown, markdown_to_plain_text


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'development')

    app = Flask('bluelog')
    app.config.from_object(config[config_name])

    register_logging(app)
    register_extensions(app)
    register_blueprints(app)
    register_commands(app)
    register_errors(app)
    register_shell_context(app)
    register_template_context(app)
    register_template_filters(app)
    register_compatibility_hooks(app)
    register_request_handlers(app)
    return app


def register_logging(app):
    class RequestFormatter(logging.Formatter):

        def format(self, record):
            record.url = request.url
            record.remote_addr = request.remote_addr
            return super(RequestFormatter, self).format(record)

    request_formatter = RequestFormatter(
        '[%(asctime)s] %(remote_addr)s requested %(url)s\n'
        '%(levelname)s in %(module)s: %(message)s'
    )

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    file_handler = RotatingFileHandler(os.path.join(basedir, 'logs/bluelog.log'),
                                       maxBytes=10 * 1024 * 1024, backupCount=10)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    mail_handler = SMTPHandler(
        mailhost=app.config['MAIL_SERVER'],
        fromaddr=app.config['MAIL_USERNAME'],
        toaddrs=['ADMIN_EMAIL'],
        subject='Bluelog Application Error',
        credentials=(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD']))
    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(request_formatter)

    if not app.debug:
        app.logger.addHandler(mail_handler)
        app.logger.addHandler(file_handler)


def register_extensions(app):
    bootstrap.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    toolbar.init_app(app)
    migrate.init_app(app, db)


def register_blueprints(app):
    app.register_blueprint(blog_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')


def register_shell_context(app):
    @app.shell_context_processor
    def make_shell_context():
        return dict(db=db, Admin=Admin, Post=Post, Category=Category, Comment=Comment, Essay=Essay)


def register_template_context(app):
    @app.context_processor
    def make_template_context():
        admin = Admin.query.first()
        categories = Category.query.order_by(Category.name).all()
        links = Link.query.order_by(Link.name).all()
        if current_user.is_authenticated:
            unread_comments = Comment.query.filter_by(reviewed=False).count()
        else:
            unread_comments = None
        return dict(
            admin=admin, categories=categories,
            links=links, unread_comments=unread_comments)


def register_template_filters(app):
    @app.template_filter()
    def markdown(value):
        return render_markdown(value)

    @app.template_filter()
    def markdown_plain(value):
        return markdown_to_plain_text(value)


def register_compatibility_hooks(app):
    @app.before_first_request
    def ensure_runtime_tables():
        inspector = sa.inspect(db.engine)
        if 'essay' not in inspector.get_table_names():
            Essay.__table__.create(db.engine)


def register_errors(app):
    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html'), 400

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(message='上传请求校验失败：%s' % e.description), 400
        return render_template('errors/400.html', description=e.description), 400


def register_commands(app):
    def bootstrap_admin(username=None, password=None):
        username = username or os.getenv('BLUELOG_ADMIN_USERNAME')
        password = password or os.getenv('BLUELOG_ADMIN_PASSWORD')

        if username is None or password is None:
            return False

        admin = Admin.query.first()
        if admin is not None:
            click.echo('The administrator already exists, updating...')
            click.echo('管理员已存在，正在更新信息...')
            admin.username = username
            admin.set_password(password)
        else:
            click.echo('正在创建管理员账号...')
            admin = Admin(
                username=username,
                blog_title='Bluelog',
                blog_sub_title='分享记录与灵感。',
                name='站长',
                about='这里是关于页面。'
            )
            admin.set_password(password)
            db.session.add(admin)

        category = Category.query.first()
        if category is None:
            click.echo('正在创建默认分类...')
            category = Category(name='默认分类')
            db.session.add(category)

        db.session.commit()
        return True

    @app.cli.command()
    @click.option('--drop', is_flag=True, help='删除现有数据表后再创建。')
    def initdb(drop):
        """初始化数据库。"""
        if drop:
            click.confirm('此操作会删除现有数据库，是否继续？', abort=True)
            db.drop_all()
            click.echo('已删除数据表。')
        db.create_all()
        bootstrap_admin()
        click.echo('数据库初始化完成。')

    @app.cli.command()
    @click.option('--username', help='管理员登录用户名。')
    @click.option('--password', help='管理员登录密码。')
    def init(username, password):
        """初始化站点。"""
        username = username or os.getenv('BLUELOG_ADMIN_USERNAME')
        password = password or os.getenv('BLUELOG_ADMIN_PASSWORD')

        if username is None:
            username = click.prompt('请输入管理员用户名')
        if password is None:
            password = click.prompt('请输入管理员密码', hide_input=True, confirmation_prompt=True)

        click.echo('正在初始化数据库...')
        db.create_all()
        bootstrap_admin(username, password)
        click.echo('初始化完成。')

    @app.cli.command()
    @click.option('--category', default=10, help='分类数量，默认为 10。')
    @click.option('--post', default=50, help='文章数量，默认为 50。')
    @click.option('--comment', default=500, help='评论数量，默认为 500。')
    def forge(category, post, comment):
        """生成演示数据。"""
        from bluelog.fakes import fake_admin, fake_categories, fake_posts, fake_comments, fake_links

        db.drop_all()
        db.create_all()

        click.echo('正在生成管理员...')
        fake_admin()

        click.echo('正在生成 %d 个分类...' % category)
        fake_categories(category)

        click.echo('正在生成 %d 篇文章...' % post)
        fake_posts(post)

        click.echo('正在生成 %d 条评论...' % comment)
        fake_comments(comment)

        click.echo('正在生成友情链接...')
        fake_links()

        click.echo('完成。')


def register_request_handlers(app):
    @app.after_request
    def query_profiler(response):
        for q in get_debug_queries():
            if q.duration >= app.config['BLUELOG_SLOW_QUERY_THRESHOLD']:
                app.logger.warning(
                    'Slow query: Duration: %fs\n Context: %s\nQuery: %s\n '
                    % (q.duration, q.context, q.statement)
                )
        return response
