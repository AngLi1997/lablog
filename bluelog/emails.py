# -*- coding: utf-8 -*-
"""
    :author: Ang Li
    :url: http://liangliang.world
    :copyright: © 2026 Ang Li <liangliangaichirou@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
from threading import Thread

from flask import url_for, current_app
from flask_mail import Message

from bluelog.extensions import mail


def _send_async_mail(app, message):
    with app.app_context():
        mail.send(message)


def send_mail(subject, to, html):
    app = current_app._get_current_object()
    message = Message(subject, recipients=[to], html=html)
    thr = Thread(target=_send_async_mail, args=[app, message])
    thr.start()
    return thr


def send_new_comment_email(post):
    post_url = url_for('blog.show_post', post_id=post.id, _external=True) + '#comments'
    send_mail(subject='Bluelog 有新评论', to=current_app.config['BLUELOG_EMAIL'],
              html='<p>文章 <i>%s</i> 收到一条新评论，请点击下面的链接查看：</p>'
                   '<p><a href="%s">%s</a></P>'
                   '<p><small style="color: #868e96">这是一封系统邮件，请勿直接回复。</small></p>'
                   % (post.title, post_url, post_url))


def send_new_reply_email(comment):
    post_url = url_for('blog.show_post', post_id=comment.post_id, _external=True) + '#comments'
    send_mail(subject='Bluelog 有新回复', to=comment.email,
              html='<p>你在文章 <i>%s</i> 下的评论收到了新回复，请点击下面的链接查看：</p>'
                   '<p><a href="%s">%s</a></p>'
                   '<p><small style="color: #868e96">这是一封系统邮件，请勿直接回复。</small></p>'
                   % (comment.post.title, post_url, post_url))
