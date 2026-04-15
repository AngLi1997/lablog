# Repository Guidelines

## 项目结构与模块组织
`bluelog/` 是 Flask 应用主目录。应用工厂、CLI 命令和日志注册位于 `bluelog/__init__.py`，配置位于 `bluelog/settings.py`，数据模型位于 `bluelog/models.py`，表单定义位于 `bluelog/forms.py`，视图按功能拆分在 `bluelog/blueprints/`。模板位于 `bluelog/templates/`，静态资源位于 `bluelog/static/`，迁移文件位于 `migrations/`，容器启动脚本位于 `docker/start.sh`，生产入口是 `wsgi.py`。运行期数据和产物写入 `data/`、`logs/`、`uploads/`。当前仓库没有 `tests/` 目录，新增测试时再创建。

## 构建、测试与开发命令
先创建虚拟环境并安装依赖：`uv venv .venv && source .venv/bin/activate && uv pip install -r requirements.txt`。

- `flask run`：基于 `.flaskenv` 启动本地开发服务器，默认读取 `FLASK_APP=bluelog` 和 `FLASK_ENV=development`。
- `flask init`：交互式初始化数据库并创建管理员账户。
- `flask initdb` 或 `flask initdb --drop`：初始化数据库结构；如果环境变量中提供管理员账号密码，会顺带创建管理员和默认分类。
- `flask forge`：重建 SQLite 数据库并生成假数据。
- `python -m unittest discover`：运行测试套件；仅在补充 `tests/` 目录后适用。
- `coverage run -m unittest discover && coverage report`：统计覆盖率；同样依赖测试目录存在。
- `flake8`：按仓库内配置执行静态检查。
- `docker compose build`：用于本地构建 Docker 镜像。
- `docker buildx build --platform linux/amd64 -t <image> --push .`：面向 Linux x86_64 服务器发布镜像。
- `docker buildx build --platform linux/amd64,linux/arm64 -t <image> --push .`：发布多架构镜像。
- `docker compose up -d`：通过 `.env` 启动容器，并将 `./data`、`./uploads`、`./logs` 挂载到容器。
- `docker run --env-file .env ...`：服务器上直接运行镜像时的推荐方式。
- `docker compose logs -f bluelog`：查看容器实时日志。

## 代码风格与命名约定
统一使用 4 空格缩进，单行长度不超过 `flake8` 配置的 119 个字符。遵循现有 Python 命名习惯：函数和变量使用 `snake_case`，类名使用 `CamelCase`，模块文件名保持小写。路由处理按功能归类到 `bluelog/blueprints/`，数据库逻辑尽量留在模型、表单或辅助函数中，不要把复杂业务逻辑塞进模板。文档修改时优先保持与当前代码、目录和运行方式一致，不要沿用历史 README 中已经过时的安装说明。

## 测试规范
当前仓库没有现成测试文件。新增测试时，推荐使用 `unittest`、Flask 测试客户端和 `create_app('testing')` 提供的内存 SQLite 数据库。测试文件命名为 `tests/test_<feature>.py`，测试方法命名为 `test_<behavior>`。如果需要公共基类或夹具，可新增 `tests/base.py` 统一封装应用上下文、CLI runner 和登录辅助方法。

## 提交与 Pull Request 规范
Git 历史使用简短、祈使句风格的提交标题，例如 `Fix missing CKEditor config for about textarea`。提交应保持单一目的，避免把重构和行为变更混在一起。PR 需要包含变更摘要、测试说明、关联 issue（如有），以及模板或样式调整的截图。

## 配置与数据说明
默认开发环境使用 SQLite `data-dev.db`，生产环境默认使用 SQLite `data.db`，测试环境使用内存数据库。应用会按 `FLASK_CONFIG` 自动加载环境文件：`development` 读取 `.env.example`，`production` 读取 `.env`。敏感配置通过环境变量注入，例如 `SECRET_KEY`、`MAIL_USERNAME`、`MAIL_PASSWORD`、`DATABASE_URL`、`BLUELOG_ADMIN_USERNAME`、`BLUELOG_ADMIN_PASSWORD` 和 `BLUELOG_EMAIL`。不要提交 `.env`、生成的数据库文件、上传内容或日志输出。Docker 镜像内默认设置 `FLASK_APP=wsgi.py` 与 `FLASK_CONFIG=production`，运行时应优先通过 `.env` 或 `--env-file` 提供 `DATABASE_URL` 等配置，而不是在 `docker run` 中逐个硬编码；如需持久化 SQLite，可将宿主机目录挂载到容器内 `/data` 并在 `.env` 中设置 `DATABASE_URL=sqlite:////data/data.db`。容器启动时会先执行 `flask initdb`。如果需要把镜像上传到仓库并运行在 `linux/amd64` 服务器，不要只依赖本机 `docker compose build` 的默认架构，应优先使用 `docker buildx build --platform ... --push` 生成目标架构或多架构镜像。
