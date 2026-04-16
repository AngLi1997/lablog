# -*- coding: utf-8 -*-
"""
    :author: Ang Li
    :url: http://liangliang.world
    :copyright: © 2026 Ang Li <liangliangaichirou@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
from flask import render_template, flash, redirect, url_for, request, current_app, Blueprint, abort, make_response, send_from_directory, jsonify
from flask_login import current_user
from sqlalchemy import or_

from bluelog.emails import send_new_comment_email, send_new_reply_email
from bluelog.extensions import db
from bluelog.forms import CommentForm, AdminCommentForm
from bluelog.models import Post, Essay, Category, Comment, Admin, Link
from bluelog.utils import redirect_back

blog_bp = Blueprint('blog', __name__)


def build_search_summary(text, fallback=''):
    content = (text or fallback or '').strip()
    if not content:
        return ''
    return ' '.join(content.split())


@blog_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['BLUELOG_POST_PER_PAGE']
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page, per_page=per_page)
    posts = pagination.items
    return render_template('blog/index.html', pagination=pagination, posts=posts)


@blog_bp.route('/essays')
def show_essays():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['BLUELOG_POST_PER_PAGE']
    pagination = Essay.query.order_by(Essay.timestamp.desc()).paginate(page, per_page=per_page)
    essays = pagination.items
    return render_template('blog/essays.html', pagination=pagination, essays=essays)


@blog_bp.route('/about')
def about():
    return render_template('blog/about.html')


@blog_bp.route('/search')
def search():
    query = request.args.get('q', '', type=str).strip()

    posts = []
    essays = []
    categories = []
    links = []
    admin = Admin.query.first()
    admin_match = False

    if query:
        like_pattern = '%%%s%%' % query
        posts = Post.query.filter(
            or_(Post.title.ilike(like_pattern), Post.body.ilike(like_pattern))
        ).order_by(Post.timestamp.desc()).all()
        essays = Essay.query.filter(Essay.body.ilike(like_pattern)).order_by(Essay.timestamp.desc()).all()
        categories = Category.query.filter(Category.name.ilike(like_pattern)).order_by(Category.name.asc()).all()
        links = Link.query.filter(
            or_(Link.name.ilike(like_pattern), Link.url.ilike(like_pattern))
        ).order_by(Link.name.asc()).all()
        if admin is not None:
            admin_match = any(
                query.lower() in (value or '').lower()
                for value in [admin.blog_title, admin.blog_sub_title, admin.name, admin.about]
            )

    total = len(posts) + len(essays) + len(categories) + len(links) + (1 if admin_match else 0)
    return render_template(
        'blog/search.html',
        query=query,
        posts=posts,
        essays=essays,
        categories=categories,
        links=links,
        admin_result=admin if admin_match else None,
        total=total
    )


@blog_bp.route('/api/search')
def search_suggestions():
    query = request.args.get('q', '', type=str).strip()
    items = []

    if not query:
        return jsonify(items=items)

    like_pattern = '%%%s%%' % query
    posts = Post.query.filter(
        or_(Post.title.ilike(like_pattern), Post.body.ilike(like_pattern))
    ).order_by(Post.timestamp.desc()).limit(5).all()
    essays = Essay.query.filter(Essay.body.ilike(like_pattern)).order_by(Essay.timestamp.desc()).limit(5).all()
    categories = Category.query.filter(Category.name.ilike(like_pattern)).order_by(Category.name.asc()).limit(5).all()
    links = Link.query.filter(
        or_(Link.name.ilike(like_pattern), Link.url.ilike(like_pattern))
    ).order_by(Link.name.asc()).limit(5).all()

    admin = Admin.query.first()
    if admin is not None and any(
        query.lower() in (value or '').lower()
        for value in [admin.blog_title, admin.blog_sub_title, admin.name, admin.about]
    ):
        items.append({
            'type': '网站信息',
            'title': admin.blog_title or '关于',
            'summary': build_search_summary(admin.about, admin.blog_sub_title),
            'url': url_for('blog.about')
        })

    for post in posts:
        items.append({
            'type': '文章',
            'title': post.title,
            'summary': build_search_summary(post.body),
            'url': url_for('blog.show_post', post_id=post.id)
        })

    for essay in essays:
        items.append({
            'type': '随笔',
            'title': '随笔 %s' % essay.timestamp.strftime('%Y-%m-%d %H:%M'),
            'summary': build_search_summary(essay.body),
            'url': '%s#essay-%s' % (url_for('blog.show_essays'), essay.id)
        })

    for category in categories:
        items.append({
            'type': '分类',
            'title': category.name,
            'summary': '共 %s 篇文章' % len(category.posts),
            'url': url_for('blog.show_category', category_id=category.id)
        })

    for link in links:
        items.append({
            'type': '网站信息',
            'title': link.name,
            'summary': build_search_summary(link.url),
            'url': link.url
        })

    return jsonify(items=items[:8])


@blog_bp.route('/category/<int:category_id>')
def show_category(category_id):
    category = Category.query.get_or_404(category_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['BLUELOG_POST_PER_PAGE']
    pagination = Post.query.with_parent(category).order_by(Post.timestamp.desc()).paginate(page, per_page)
    posts = pagination.items
    return render_template('blog/category.html', category=category, pagination=pagination, posts=posts)


@blog_bp.route('/post/<int:post_id>', methods=['GET', 'POST'])
def show_post(post_id):
    post = Post.query.get_or_404(post_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['BLUELOG_COMMENT_PER_PAGE']
    pagination = Comment.query.with_parent(post).filter_by(reviewed=True).order_by(Comment.timestamp.asc()).paginate(
        page, per_page)
    comments = pagination.items

    if current_user.is_authenticated:
        form = AdminCommentForm()
        form.author.data = current_user.name
        form.email.data = current_app.config['BLUELOG_EMAIL']
        form.site.data = url_for('.index')
        form.submit.label.text = '发布评论'
        from_admin = True
        reviewed = True
    else:
        form = CommentForm()
        from_admin = False
        reviewed = False

    if form.validate_on_submit():
        author = form.author.data
        email = form.email.data
        site = form.site.data
        body = form.body.data
        comment = Comment(
            author=author, email=email, site=site, body=body,
            from_admin=from_admin, post=post, reviewed=reviewed)
        replied_id = request.args.get('reply')
        if replied_id:
            replied_comment = Comment.query.get_or_404(replied_id)
            comment.replied = replied_comment
            send_new_reply_email(replied_comment)
        db.session.add(comment)
        db.session.commit()
        if current_user.is_authenticated:
            flash('评论已发布。', 'success')
        else:
            flash('评论已提交，审核后展示。', 'info')
            send_new_comment_email(post)
        return redirect(url_for('.show_post', post_id=post_id))
    return render_template('blog/post.html', post=post, pagination=pagination, form=form, comments=comments)


@blog_bp.route('/reply/comment/<int:comment_id>')
def reply_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if not comment.post.can_comment:
        flash('评论功能已关闭。', 'warning')
        return redirect(url_for('.show_post', post_id=comment.post.id))
    return redirect(
        url_for('.show_post', post_id=comment.post_id, reply=comment_id, author=comment.author) + '#comment-form')


@blog_bp.route('/change-theme/<theme_name>')
def change_theme(theme_name):
    if theme_name not in current_app.config['BLUELOG_THEMES'].keys():
        abort(404)

    response = make_response(redirect_back())
    response.set_cookie('theme', theme_name, max_age=30 * 24 * 60 * 60)
    return response


@blog_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['BLUELOG_UPLOAD_PATH'], filename)
