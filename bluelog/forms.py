# -*- coding: utf-8 -*-
"""
    :author: Ang Li
    :url: http://liangliang.world
    :copyright: © 2026 Ang Li <liangliangaichirou@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, TextAreaField, ValidationError, HiddenField, \
    BooleanField, PasswordField
from wtforms.validators import DataRequired, Email, Length, Optional, URL
import json

from bluelog.models import Category


class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[
        DataRequired(message='请输入用户名。'),
        Length(1, 20, message='用户名长度需在 1 到 20 个字符之间。')
    ])
    password = PasswordField('密码', validators=[
        DataRequired(message='请输入密码。'),
        Length(1, 128, message='密码长度需在 1 到 128 个字符之间。')
    ])
    remember = BooleanField('记住我')
    submit = SubmitField('登录')


class SettingForm(FlaskForm):
    name = StringField('站长名称', validators=[
        DataRequired(message='请输入站长名称。'),
        Length(1, 30, message='站长名称长度需在 1 到 30 个字符之间。')
    ])
    blog_title = StringField('站点标题', validators=[
        DataRequired(message='请输入站点标题。'),
        Length(1, 60, message='站点标题长度需在 1 到 60 个字符之间。')
    ])
    blog_sub_title = StringField('站点副标题', validators=[
        DataRequired(message='请输入站点副标题。'),
        Length(1, 100, message='站点副标题长度需在 1 到 100 个字符之间。')
    ])
    about = TextAreaField('关于页面', validators=[DataRequired(message='请输入关于页面内容。')], render_kw={
        'rows': 18,
        'data-markdown-editor': 'true',
        'data-markdown-help': 'Markdown'
    })
    submit = SubmitField('保存设置')


class PostForm(FlaskForm):
    title = StringField('标题', validators=[
        DataRequired(message='请输入文章标题。'),
        Length(1, 60, message='文章标题长度需在 1 到 60 个字符之间。')
    ])
    category = SelectField('分类', coerce=int, default=1)
    body = TextAreaField('正文', validators=[DataRequired(message='请输入文章正文。')], render_kw={
        'rows': 20,
        'data-markdown-editor': 'true',
        'data-markdown-help': 'Markdown'
    })
    submit = SubmitField('保存文章')

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.category.choices = [(category.id, category.name)
                                 for category in Category.query.order_by(Category.name).all()]


class EssayForm(FlaskForm):
    body = TextAreaField('内容', validators=[Optional(), Length(max=2000, message='随笔内容不能超过 2000 个字符。')], render_kw={
        'rows': 8,
        'placeholder': '记录这一刻的想法、日常或图片说明'
    })
    images = HiddenField('图片')
    submit = SubmitField('发布随笔')

    def validate_images(self, field):
        raw = field.data or '[]'
        try:
            images = json.loads(raw)
        except (TypeError, ValueError):
            raise ValidationError('图片数据格式无效。')

        if not isinstance(images, list):
            raise ValidationError('图片数据格式无效。')
        if len(images) > 9:
            raise ValidationError('随笔最多只能上传 9 张图片。')
        if any(not isinstance(item, str) or not item.strip() for item in images):
            raise ValidationError('图片地址不能为空。')

    def validate(self):
        if not super(EssayForm, self).validate():
            return False

        body = (self.body.data or '').strip()
        images = json.loads(self.images.data or '[]')
        if not body and not images:
            self.body.errors.append('内容和图片至少填写一项。')
            return False
        return True


class CategoryForm(FlaskForm):
    name = StringField('名称', validators=[
        DataRequired(message='请输入分类名称。'),
        Length(1, 30, message='分类名称长度需在 1 到 30 个字符之间。')
    ])
    submit = SubmitField('保存分类')

    def validate_name(self, field):
        if Category.query.filter_by(name=field.data).first():
            raise ValidationError('分类名称已存在。')


class CommentForm(FlaskForm):
    author = StringField('昵称', validators=[
        DataRequired(message='请输入昵称。'),
        Length(1, 30, message='昵称长度需在 1 到 30 个字符之间。')
    ])
    email = StringField('邮箱', validators=[
        DataRequired(message='请输入邮箱。'),
        Email(message='请输入有效的邮箱地址。'),
        Length(1, 254, message='邮箱长度需在 1 到 254 个字符之间。')
    ])
    site = StringField('网站', validators=[
        Optional(),
        URL(message='请输入有效的网址。'),
        Length(0, 255, message='网站地址长度不能超过 255 个字符。')
    ])
    body = TextAreaField('评论内容', validators=[DataRequired(message='请输入评论内容。')])
    submit = SubmitField('提交评论')


class AdminCommentForm(CommentForm):
    author = HiddenField()
    email = HiddenField()
    site = HiddenField()


class LinkForm(FlaskForm):
    name = StringField('名称', validators=[
        DataRequired(message='请输入链接名称。'),
        Length(1, 30, message='链接名称长度需在 1 到 30 个字符之间。')
    ])
    url = StringField('链接地址', validators=[
        DataRequired(message='请输入链接地址。'),
        URL(message='请输入有效的网址。'),
        Length(1, 255, message='链接地址长度需在 1 到 255 个字符之间。')
    ])
    submit = SubmitField('保存链接')
