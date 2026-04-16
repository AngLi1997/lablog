# Bluelog

一个基于 Flask 的个人博客项目，包含公开博客页、随笔时间轴、后台管理、分类管理、评论审核、友情链接、图片上传和内容管理接口。

## 项目概览

- 应用入口：`bluelog/__init__.py`
- 配置文件：`bluelog/settings.py`
- 数据模型：`bluelog/models.py`
- 蓝图模块：`bluelog/blueprints/`
- 模板目录：`bluelog/templates/`
- 静态资源：`bluelog/static/`
- 数据迁移：`migrations/`
- 容器启动脚本：`docker/start.sh`
- 本地技能：`skills/content-api-manager/`
- 运行期目录：`data/`、`logs/`、`uploads/`

## 功能特性

- 文章发布、编辑、删除
- 随笔发布、编辑、删除，前台按时间轴展示
- 随笔支持图片一宫格、四宫格、九宫格展示，最多 9 张
- 分类管理，删除分类时将文章回退到默认分类
- 评论发布、审核、删除、管理员回复
- 后台站点设置
- 友情链接管理
- Markdown 编辑与代码高亮
- 本地图片上传，上传目录为 `uploads/`
- 基于 Flask-Migrate 的数据库迁移支持
- 提供 `/api/posts`、`/api/categories`、`/api/essays` 管理接口
- Docker 部署支持

## 环境要求

- Python 3.9 及以上
- 推荐使用 `uv` 管理虚拟环境和依赖

## 本地开发

1. 创建虚拟环境并安装依赖：

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

2. 准备环境变量：

开发环境会自动加载仓库根目录下的 `.env.example`。如需覆盖默认值，可以自行导出环境变量，或切换到生产配置并提供 `.env`。

默认示例配置见 `.env.example`，关键项包括：

- `FLASK_CONFIG`
- `SECRET_KEY`
- `DATABASE_URL`
- `BLUELOG_ADMIN_USERNAME`
- `BLUELOG_ADMIN_PASSWORD`
- `MAIL_SERVER`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`
- `BLUELOG_EMAIL`

3. 初始化数据库并创建管理员：

```bash
flask init
```

如果只想建表并尝试从环境变量自动创建管理员，可执行：

```bash
flask initdb
```

4. 启动开发服务器：

```bash
flask run
```

默认地址：

```text
http://127.0.0.1:5000
```

`.env.example` 默认测试账号：

- 用户名：`admin`
- 密码：`helloflask`

## 测试

执行全部测试：

```bash
python -m unittest discover
```

当前测试覆盖：

- 随笔时间轴页面渲染
- 后台随笔表单创建与图片上限校验
- `/api/posts`、`/api/categories`、`/api/essays` 增删查改

## CLI 命令

- `flask initdb`：创建数据库表，并在环境变量存在时初始化管理员和默认分类
- `flask initdb --drop`：先删表再重建
- `flask init`：交互式初始化数据库和管理员账号
- `flask forge`：重建数据库并生成假数据
- `flask forge --category 5 --post 20 --comment 100`：指定演示数据规模

## 内容管理接口

所有 `/api/*` 接口都要求管理员登录态。

- `GET /api/posts`
- `POST /api/posts`
- `GET /api/posts/<post_id>`
- `PATCH /api/posts/<post_id>`
- `DELETE /api/posts/<post_id>`
- `GET /api/categories`
- `POST /api/categories`
- `GET /api/categories/<category_id>`
- `PATCH /api/categories/<category_id>`
- `DELETE /api/categories/<category_id>`
- `GET /api/essays`
- `POST /api/essays`
- `GET /api/essays/<essay_id>`
- `PATCH /api/essays/<essay_id>`
- `DELETE /api/essays/<essay_id>`

如果希望由 Codex 通过接口管理内容，可以直接使用仓库根目录的 `skills/content-api-manager/`。

## 数据库与配置

- Docker 环境建议通过 `.env` 或 `--env-file` 提供 `DATABASE_URL`
- 如果把宿主机目录挂载到容器内 `/data`，可在 `.env` 中使用 `DATABASE_URL=sqlite:////data/data.db` 持久化 SQLite 数据

应用会按 `FLASK_CONFIG` 加载环境文件：

- `development`：加载 `.env.example`
- `production`：加载 `.env`

## Docker 运行

本地构建并运行：

```bash
docker compose build
docker compose up -d
```

查看日志：

```bash
docker compose logs -f bluelog
```

如果镜像需要上传到仓库并在 `linux/amd64` 服务器上运行，推荐使用 `buildx` 显式构建目标平台，而不是直接使用本机默认架构。

单架构发布：

```bash
docker buildx build --platform linux/amd64 -t <registry>/<namespace>/bluelog:latest --push .
```

多架构发布：

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t <registry>/<namespace>/bluelog:latest --push .
```

## 项目结构

```text
.
├── bluelog/                 Flask 应用包
│   ├── blueprints/          博客、认证、后台、API 蓝图
│   ├── static/              CSS、JS、图片等静态资源
│   ├── templates/           前台、后台、错误页模板
│   ├── __init__.py          应用工厂、命令注册、日志配置
│   ├── extensions.py        Flask 扩展初始化
│   ├── forms.py             WTForms 表单
│   ├── models.py            SQLAlchemy 模型
│   ├── settings.py          开发/测试/生产配置
│   └── utils.py             辅助函数
├── migrations/              Alembic 迁移文件
├── skills/                  本地 Codex 技能
├── tests/                   unittest 测试
├── uploads/                 上传文件目录
└── wsgi.py                  生产入口
```

## 部署说明

- `Procfile` 使用 `gunicorn wsgi:app --log-file -`
- `Procfile.windows` 使用 `flask run`
- 生产环境需要自行提供 `.env`
- 不要提交 `.env`、数据库文件、日志文件和上传文件
- 生产环境推荐通过 `.env` 或 `docker run --env-file .env` 传入配置
- 如果部署目标是 Linux x86_64 服务器，发布镜像时优先构建 `linux/amd64` 或多架构 manifest
