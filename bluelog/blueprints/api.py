# -*- coding: utf-8 -*-
"""项目内部管理 API。"""
from flask import Blueprint, jsonify, request
from flask_login import login_required

from bluelog.extensions import db
from bluelog.models import Category, Essay, Post

api_bp = Blueprint('api', __name__)


def _essay_to_dict(essay):
    return {
        'id': essay.id,
        'body': essay.body,
        'images': essay.images,
        'timestamp': essay.timestamp.isoformat() + 'Z'
    }


def _post_to_dict(post):
    return {
        'id': post.id,
        'title': post.title,
        'body': post.body,
        'category_id': post.category_id,
        'category_name': post.category.name if post.category else None,
        'can_comment': post.can_comment,
        'timestamp': post.timestamp.isoformat() + 'Z'
    }


def _category_to_dict(category):
    return {
        'id': category.id,
        'name': category.name,
        'post_count': len(category.posts)
    }


@api_bp.route('/posts', methods=['GET'])
@login_required
def list_posts():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return jsonify(items=[_post_to_dict(post) for post in posts])


@api_bp.route('/posts', methods=['POST'])
@login_required
def create_post():
    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    body = (data.get('body') or '').strip()
    category_id = data.get('category_id', 1)
    if not title or not body:
        return jsonify(message='标题和正文不能为空。'), 400

    category = Category.query.get_or_404(category_id)
    post = Post(title=title, body=body, category=category)
    db.session.add(post)
    db.session.commit()
    return jsonify(item=_post_to_dict(post)), 201


@api_bp.route('/posts/<int:post_id>', methods=['GET'])
@login_required
def get_post(post_id):
    post = Post.query.get_or_404(post_id)
    return jsonify(item=_post_to_dict(post))


@api_bp.route('/posts/<int:post_id>', methods=['PUT', 'PATCH'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    data = request.get_json() or {}

    if 'title' in data:
        post.title = (data.get('title') or '').strip()
    if 'body' in data:
        post.body = (data.get('body') or '').strip()
    if 'category_id' in data:
        post.category = Category.query.get_or_404(data['category_id'])
    if 'can_comment' in data:
        post.can_comment = bool(data['can_comment'])

    if not post.title or not post.body:
        return jsonify(message='标题和正文不能为空。'), 400

    db.session.commit()
    return jsonify(item=_post_to_dict(post))


@api_bp.route('/posts/<int:post_id>', methods=['DELETE'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return jsonify(message='文章已删除。')


@api_bp.route('/categories', methods=['GET'])
@login_required
def list_categories():
    categories = Category.query.order_by(Category.name).all()
    return jsonify(items=[_category_to_dict(category) for category in categories])


@api_bp.route('/categories', methods=['POST'])
@login_required
def create_category():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify(message='分类名称不能为空。'), 400
    if Category.query.filter_by(name=name).first():
        return jsonify(message='分类名称已存在。'), 400

    category = Category(name=name)
    db.session.add(category)
    db.session.commit()
    return jsonify(item=_category_to_dict(category)), 201


@api_bp.route('/categories/<int:category_id>', methods=['GET'])
@login_required
def get_category(category_id):
    category = Category.query.get_or_404(category_id)
    return jsonify(item=_category_to_dict(category))


@api_bp.route('/categories/<int:category_id>', methods=['PUT', 'PATCH'])
@login_required
def update_category(category_id):
    category = Category.query.get_or_404(category_id)
    if category.id == 1:
        return jsonify(message='默认分类不允许修改。'), 400

    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify(message='分类名称不能为空。'), 400
    existing = Category.query.filter_by(name=name).first()
    if existing and existing.id != category.id:
        return jsonify(message='分类名称已存在。'), 400

    category.name = name
    db.session.commit()
    return jsonify(item=_category_to_dict(category))


@api_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@login_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    if category.id == 1:
        return jsonify(message='默认分类不允许删除。'), 400
    category.delete()
    return jsonify(message='分类已删除。')


@api_bp.route('/essays', methods=['GET'])
@login_required
def list_essays():
    essays = Essay.query.order_by(Essay.timestamp.desc()).all()
    return jsonify(items=[_essay_to_dict(essay) for essay in essays])


@api_bp.route('/essays', methods=['POST'])
@login_required
def create_essay():
    data = request.get_json() or {}
    body = (data.get('body') or '').strip()
    images = data.get('images') or []
    if not body and not images:
        return jsonify(message='内容和图片至少填写一项。'), 400
    if not isinstance(images, list) or len(images) > 9:
        return jsonify(message='图片数量必须在 0 到 9 张之间。'), 400

    essay = Essay(body=body)
    essay.images = images
    db.session.add(essay)
    db.session.commit()
    return jsonify(item=_essay_to_dict(essay)), 201


@api_bp.route('/essays/<int:essay_id>', methods=['GET'])
@login_required
def get_essay(essay_id):
    essay = Essay.query.get_or_404(essay_id)
    return jsonify(item=_essay_to_dict(essay))


@api_bp.route('/essays/<int:essay_id>', methods=['PUT', 'PATCH'])
@login_required
def update_essay(essay_id):
    essay = Essay.query.get_or_404(essay_id)
    data = request.get_json() or {}

    if 'body' in data:
        essay.body = (data.get('body') or '').strip()
    if 'images' in data:
        images = data.get('images') or []
        if not isinstance(images, list) or len(images) > 9:
            return jsonify(message='图片数量必须在 0 到 9 张之间。'), 400
        essay.images = images

    if not (essay.body or essay.images):
        return jsonify(message='内容和图片至少填写一项。'), 400

    db.session.commit()
    return jsonify(item=_essay_to_dict(essay))


@api_bp.route('/essays/<int:essay_id>', methods=['DELETE'])
@login_required
def delete_essay(essay_id):
    essay = Essay.query.get_or_404(essay_id)
    db.session.delete(essay)
    db.session.commit()
    return jsonify(message='随笔已删除。')
