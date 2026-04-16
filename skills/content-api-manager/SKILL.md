---
name: content-api-manager
description: 当需要通过本项目的 HTTP 接口管理文章、分类或随笔时使用。适用于登录站点、调用 /api 下的文章/分类/随笔增删查改接口、校验返回结果，并在必要时先创建依赖分类。
---

# Content API Manager

该技能用于通过项目内置管理接口操作内容数据，范围包括：文章、分类、随笔。

## 触发场景

- 用户要求“通过接口”创建、读取、更新、删除文章、分类或随笔。
- 需要把管理操作整理成可重复执行的 API 调用步骤。
- 需要验证 `/api/posts`、`/api/categories`、`/api/essays` 的请求与响应。

## 前置条件

- 服务已启动。
- 使用管理员账号登录。
- 如果运行在非 `testing` 配置，接口依赖 session 登录态；优先使用同一会话保持 cookie。

## 工作流程

1. 先确认服务地址，默认使用 `http://127.0.0.1:5000`。
2. 先访问 `/auth/login` 或直接提交登录表单建立会话。
3. 后续所有 `/api/*` 请求复用同一个 session cookie。
4. 需要创建文章时，先确认目标分类存在；不存在则先调分类创建接口。
5. 创建或更新随笔时，`images` 字段必须是数组，最多 9 个字符串 URL。
6. 删除分类前，确认不是 ID 为 `1` 的默认分类。
7. 返回结果后，提炼关键字段给用户：ID、标题/名称、时间、图片数量、是否成功。

## 接口约定

### 文章

- `GET /api/posts`：列出文章。
- `POST /api/posts`：创建文章。
  - 必填 JSON：`title`、`body`、`category_id`
- `GET /api/posts/<post_id>`：读取文章。
- `PATCH /api/posts/<post_id>`：更新文章。
  - 可选 JSON：`title`、`body`、`category_id`、`can_comment`
- `DELETE /api/posts/<post_id>`：删除文章。

### 分类

- `GET /api/categories`：列出分类。
- `POST /api/categories`：创建分类。
  - 必填 JSON：`name`
- `GET /api/categories/<category_id>`：读取分类。
- `PATCH /api/categories/<category_id>`：更新分类。
  - 必填 JSON：`name`
- `DELETE /api/categories/<category_id>`：删除分类。

### 随笔

- `GET /api/essays`：列出随笔。
- `POST /api/essays`：创建随笔。
  - JSON：`body` 可为空，但 `body` 和 `images` 至少一个有值。
  - `images` 为图片 URL 数组，最多 9 个。
- `GET /api/essays/<essay_id>`：读取随笔。
- `PATCH /api/essays/<essay_id>`：更新随笔。
  - 可选 JSON：`body`、`images`
- `DELETE /api/essays/<essay_id>`：删除随笔。

## 执行原则

- 优先用 JSON 请求体。
- 遇到 400 响应时，直接使用接口返回的中文错误信息，不自行改写语义。
- 涉及批量操作时，逐个确认返回结果，避免把失败对象混入成功列表。
- 如果用户只要查看，不要做写操作。
- 如果用户要求通过脚本自动化，优先给出 `curl` 示例，必要时再写脚本。

## 最小示例

```bash
curl -X POST http://127.0.0.1:5000/api/categories \
  -H 'Content-Type: application/json' \
  -b cookies.txt -c cookies.txt \
  -d '{"name":"生活"}'
```

```bash
curl -X POST http://127.0.0.1:5000/api/essays \
  -H 'Content-Type: application/json' \
  -b cookies.txt -c cookies.txt \
  -d '{"body":"今天去爬山。","images":["/uploads/a.jpg","/uploads/b.jpg"]}'
```
