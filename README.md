# Bluelog

一个基于 Flask 的个人博客示例项目，包含公开博客页、后台管理、分类管理、评论审核、友情链接和图片上传能力。

## 项目概览

- 应用入口：`bluelog/__init__.py`
- 配置文件：`bluelog/settings.py`
- 数据模型：`bluelog/models.py`
- 蓝图模块：`bluelog/blueprints/`
- 模板目录：`bluelog/templates/`
- 静态资源：`bluelog/static/`
- 数据迁移：`migrations/`
- 容器启动脚本：`docker/start.sh`
- 运行期目录：`data/`、`logs/`、`uploads/`

## 功能特性

- 文章发布、编辑、删除
- 分类管理，删除分类时将文章回退到默认分类
- 评论发布、审核、删除、管理员回复
- 后台站点设置
- 友情链接管理
- CKEditor 富文本编辑
- 本地图片上传，上传目录为 `uploads/`
- 基于 Flask-Migrate 的数据库迁移支持
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

4. 生成演示数据：

```bash
flask forge
```

5. 启动开发服务器：

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

## CLI 命令

- `flask initdb`：创建数据库表，并在环境变量存在时初始化管理员和默认分类
- `flask initdb --drop`：先删表再重建
- `flask init`：交互式初始化数据库和管理员账号
- `flask forge`：重建数据库并生成假数据
- `flask forge --category 5 --post 20 --comment 100`：指定伪造数据规模

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

如果镜像需要上传到仓库并在 `linux/amd64` 服务器上运行，推荐使用 `buildx` 显式构建目标平台，而不是直接使用本机默认架构构建。

单架构发布：

```bash
docker buildx build --platform linux/amd64 -t <registry>/<namespace>/bluelog:latest --push .
```

多架构发布：

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t <registry>/<namespace>/bluelog:latest --push .
```

服务器拉取并启动：

```bash
docker pull <registry>/<namespace>/bluelog:latest
```

使用 `docker run` 时，推荐通过 `.env` 注入配置：

```bash
docker run -d \
  --name bluelog \
  --restart unless-stopped \
  -p 80:5000 \
  --env-file .env \
  -v $(pwd)/data:/data \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/logs:/app/logs \
  crpi-lozquo71tyi4s87k.cn-chengdu.personal.cr.aliyuncs.com/liang1997/bluelog
```

容器行为说明：

- 暴露端口 `5000`
- 挂载 `./data` 到容器内 `/data`
- 挂载 `./uploads` 到容器内 `/app/uploads`
- 挂载 `./logs` 到容器内 `/app/logs`
- 镜像内默认设置 `FLASK_APP=wsgi.py`
- 镜像内默认设置 `FLASK_CONFIG=production`
- `DATABASE_URL` 由 `.env` 或外部环境变量提供，不再要求在启动命令里显式指定

跨平台说明：

- 在 Apple Silicon 设备上直接执行 `docker compose build`，默认可能产出 `linux/arm64` 镜像
- 如果该镜像被上传后运行在 `linux/amd64` 服务器，可能出现 `no matching manifest for linux/amd64 in the manifest list entries`
- 对外发布镜像时应优先使用 `docker buildx build --platform ... --push`

## 项目结构

```text
.
├── bluelog/                 Flask 应用包
│   ├── blueprints/          博客、认证、后台蓝图
│   ├── static/              CSS、JS、CKEditor、图片等静态资源
│   ├── templates/           前台、后台、错误页模板
│   ├── __init__.py          应用工厂、命令注册、日志配置
│   ├── extensions.py        Flask 扩展初始化
│   ├── forms.py             WTForms 表单
│   ├── models.py            SQLAlchemy 模型
│   ├── settings.py          开发/测试/生产配置
│   └── utils.py             辅助函数
├── data/                    Docker 持久化数据库目录
├── docker/                  容器启动脚本
├── logs/                    应用日志目录
├── migrations/              Alembic 迁移文件
├── uploads/                 上传文件目录
├── docker-compose.yml       Docker Compose 配置
├── Dockerfile               镜像定义
├── requirements.txt         Python 依赖
└── wsgi.py                  生产入口
```

## 部署说明

- `Procfile` 使用 `gunicorn wsgi:app --log-file -`
- `Procfile.windows` 使用 `flask run`
- 生产环境需要自行提供 `.env`
- 不要提交 `.env`、数据库文件、日志文件和上传文件
- 生产环境推荐通过 `.env` 或 `docker run --env-file .env` 传入配置
- 如果部署目标是 Linux x86_64 服务器，发布镜像时优先构建 `linux/amd64` 或多架构 manifest
