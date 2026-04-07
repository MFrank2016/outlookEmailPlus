# 一键更新功能实施任务 — AI 执行提示词

## 项目背景

你正在为 **Outlook Email Plus**（一个基于 Flask 的 Outlook 邮箱管理 Web 应用）实施一键更新功能的改进。该项目使用 Docker 部署，当前已具备基础的版本检测和 Watchtower 热更新功能。

**项目路径**: `E:\hushaokang\Data-code\EnsoAi\outlookEmail\dev`
**分支**: `dev`
**技术栈**: Python 3.11 + Flask + Gunicorn + SQLite + Docker + Watchtower
**当前版本**: v1.12.0

---

## 当前代码架构

### 后端结构
```
outlook_web/
├── __init__.py              # APP_VERSION = "1.12.0"
├── app.py                   # Flask create_app()
├── controllers/
│   ├── system.py            # api_version_check(), api_trigger_update(), api_test_watchtower()
│   └── settings.py          # api_get_settings(), api_update_settings(), api_test_telegram_proxy()
├── routes/
│   ├── system.py            # /api/system/version-check, /api/system/trigger-update, /api/system/test-watchtower
│   └── settings.py          # /api/settings, /api/settings/test-telegram-proxy
├── services/
│   └── telegram_push.py     # Telegram 推送（支持代理）
├── repositories/
│   └── settings.py          # settings_repo.get_setting(), set_setting()
├── security/
│   └── crypto.py            # encrypt_data(), decrypt_data(), is_encrypted()
└── db.py                    # SQLite 数据库
```

### 前端结构
```
templates/index.html         # 单页应用，设置页有 Tab（基础/临时邮箱/API安全/自动化）
static/js/main.js            # 所有前端逻辑
```

### Docker 配置
```
Dockerfile                   # Python 3.11-slim + Gunicorn
docker-compose.yml           # app + watchtower 两个服务
```

---

## 已完成的工作

1. **版本检测 API**: `GET /api/system/version-check` — 对比 GitHub latest release，10 分钟缓存
2. **一键更新 API**: `POST /api/system/trigger-update` — 调用 Watchtower HTTP API
3. **Watchtower 测试 API**: `POST /api/system/test-watchtower` — 测试连通性
4. **设置页面 Watchtower 配置**: URL + Token（加密存储），支持测试连通性
5. **GitHub 仓库地址修复**: `hshaokang/outlookemail-plus` → `ZeroPointSix/outlookEmailPlus`
6. **热更新验证通过**: v1.12.0 → v1.12.1 成功更新

---

## 待实施任务

请按照优先级顺序实施以下改进：

### Phase 1: BUG 修复（P1 优先级）

#### 任务 1: 修复 Watchtower Token 为空时启动失败的问题

**问题**: `WATCHTOWER_HTTP_API_TOKEN` 未设置时，Watchtower 容器启动后立即 fatal 退出。

**实施方案**:
1. `.env.example` 中添加 `WATCHTOWER_HTTP_API_TOKEN=your-secret-token-here` 模板
2. `docker-compose.yml` 中为 `WATCHTOWER_HTTP_API_TOKEN` 提供默认生成值
3. 设置页面 Watchtower 配置区域增加首次配置引导文案
4. （可选）应用启动时检测 Watchtower 是否在线，不可达时在 UI 上显示配置提示

**参考代码**:
- `docker-compose.yml` 第 64 行: `WATCHTOWER_HTTP_API_TOKEN=${WATCHTOWER_HTTP_API_TOKEN}`
- `templates/index.html` Watchtower 配置区域

#### 任务 2: 修复浏览器缓存旧 JS 文件的问题

**问题**: 容器更新后，浏览器使用缓存的旧 JS 文件。

**实施方案**:
1. `templates/index.html` 中静态文件引用添加版本号参数:
   ```html
   <script src="/static/js/main.js?v={{ version }}"></script>
   ```
2. `outlook_web/app.py` 中为静态文件设置 Cache-Control 头部
3. 使用 `outlook_web.__version__` 作为版本号

### Phase 2: UI 提示优化（P2 优先级）

#### 任务 3: 镜像标签/构建模式检测与提示

**问题**: 使用固定版本标签或本地构建时一键更新失效，用户不了解原因。

**实施方案**:
1. 后端新增 API 返回当前容器的部署信息:
   ```python
   # GET /api/system/deployment-info
   {
     "image": "guangshanshui/outlook-email-plus:latest",
     "is_local_build": false,
     "uses_fixed_tag": false,
     "update_method": "watchtower",
     "watchtower_reachable": true
   }
   ```
2. 前端设置页面读取此信息，根据情况显示提示:
   - 本地构建 → "当前为本地构建模式，请使用远程镜像部署以支持一键更新"
   - 固定标签 → "建议使用 latest 标签以支持自动更新"
   - Watchtower 不可达 → "请确保 Watchtower 容器正常运行"

**涉及文件**:
- `outlook_web/controllers/system.py` — 新增 `api_deployment_info()`
- `outlook_web/routes/system.py` — 注册路由
- `static/js/main.js` — 加载并显示部署信息
- `templates/index.html` — 提示 UI

### Phase 3: 内置 Docker API 自更新（P3 优先级）

#### 任务 4: 实现内置 Docker API 自更新功能

**背景**: 当前一键更新依赖 Watchtower 外部容器。增加内置 Docker API 自更新可简化部署。

**实施方案**:

1. **新建 `outlook_web/services/docker_update.py`**:
   ```python
   def self_update():
       """通过 Docker API 拉取最新镜像并重建当前容器"""
       # 1. 检查 docker.sock 是否可用
       # 2. 获取当前容器 (os.environ['HOSTNAME'])
       # 3. 读取当前镜像名
       # 4. docker.images.pull() 拉取最新镜像
       # 5. 对比 digest，相同则返回"已是最新"
       # 6. 创建新容器（复制原配置）
       # 7. 启动新容器
       # 8. 停止旧容器
       # 9. 记录审计日志
   ```

2. **修改 `outlook_web/controllers/system.py`**:
   - 扩展 `api_trigger_update()` 支持 `method` 参数:
     - `method=watchtower` (默认): 使用 Watchtower HTTP API
     - `method=docker`: 使用 Docker API 自更新
   - 安全检查: 确认 `DOCKER_SELF_UPDATE_ALLOW=true`

3. **修改 `outlook_web/controllers/settings.py`**:
   - GET/PUT settings 新增 `update_method` 字段 (watchtower / docker_api)

4. **修改 `static/js/main.js`**:
   - `triggerUpdate()` 根据 `update_method` 设置选择触发方式
   - Docker API 模式下拉取镜像可能较慢，需要更长的超时

5. **修改 `templates/index.html`**:
   - 设置页添加"更新方式"选择:
     - Watchtower（推荐）
     - Docker API（高级，需挂载 docker.sock）
   - Docker API 选项显示安全警告

6. **修改 `docker-compose.yml`**:
   ```yaml
   services:
     app:
       volumes:
         - /var/run/docker.sock:/var/run/docker.sock  # 可选
       environment:
         DOCKER_SELF_UPDATE_ALLOW: "${DOCKER_SELF_UPDATE_ALLOW:-false}"
   ```

7. **修改 `requirements.txt`**:
   ```
   docker>=6.0
   ```

**安全要求**:
- 默认关闭，需 `DOCKER_SELF_UPDATE_ALLOW=true` 启用
- 检测 docker.sock 是否可访问
- 校验镜像名白名单（仅允许 `guangshanshui/outlook-email-plus`）
- 操作前记录审计日志
- 与 docker-compose 管理冲突时给出提示

**回滚机制**:
- 拉取新镜像前保存旧 digest
- 创建新容器但不立即删除旧容器
- 新容器 healthcheck 通过后才删除旧容器
- 失败时保留旧容器

---

## 参考文件清单

实施时需要参考/修改的文件：

| 文件 | 用途 |
|------|------|
| `outlook_web/__init__.py` | 版本号 |
| `outlook_web/controllers/system.py` | 版本检测、更新触发、Watchtower 测试 |
| `outlook_web/controllers/settings.py` | 设置读写（含 Watchtower 配置） |
| `outlook_web/routes/system.py` | 路由注册 |
| `outlook_web/services/docker_update.py` | 新建：Docker API 自更新服务 |
| `outlook_web/repositories/settings.py` | 设置数据库操作 |
| `outlook_web/security/crypto.py` | 加密/解密/脱敏 |
| `static/js/main.js` | 前端逻辑（triggerUpdate, waitForRestart, testWatchtower 等） |
| `templates/index.html` | UI（版本更新 Banner, Watchtower 配置卡片） |
| `docker-compose.yml` | Docker 编排配置 |
| `requirements.txt` | Python 依赖 |
| `Dockerfile` | 镜像构建 |
| `.env.example` | 环境变量模板 |

---

## 注意事项

1. **不要修改 `main` 分支**，只在 `dev` 分支上开发
2. **遵循现有代码风格**: 中文注释、类型注解、错误处理模式
3. **敏感信息处理**: Token 使用 `encrypt_data()` 加密存储，GET 时脱敏返回
4. **向后兼容**: 环境变量配置作为数据库配置的 fallback
5. **测试**: 每个阶段完成后提供验证方法
