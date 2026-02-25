# Outlook 邮件管理工具｜Legacy 迁移到 Controllers 层 TDD（技术设计细节）

- 文档状态：草案
- 版本：V1.0
- 日期：2026-02-24
- 对齐 PRD：`docs/PRD/PRD-00003-Legacy代码拆分到Controllers层.md`
- 对齐 FD：`docs/FD/Outlook邮件管理工具-Legacy迁移到Controllers层FD.md`
- 对齐开发指南：`docs/DEV/00002-前后端拆分-开发者指南.md`

---

## 1. 文档目的

本 TDD 用于描述"为满足 PRD/FD，Legacy 迁移到 Controllers 层需要采用的技术设计细节"。

重点回答：

- 如何设计 Controllers 层的标准模式和职责边界
- 如何从 `impl=legacy` 模式迁移到直接导入 controller 模式
- 如何保证 **URL/响应契约/错误结构/trace_id** 不回归
- 如何实现分阶段迁移（每阶段可回滚、可验证、可测试）
- 如何避免循环依赖和全局状态问题
- 如何设计测试策略（单元测试、集成测试）

---

## 2. 设计原则与硬约束（必须满足）

### 2.1 行为兼容性（对用户无感）

- 保持现有 API 路径/方法/参数语义/响应结构不变
- 保持统一错误结构、`trace_id` 透传、默认脱敏策略不变
- 保持登录/会话/CSRF 行为不变
- 保持中间件和错误处理器行为不变

### 2.2 渐进式迁移（可回滚、可验证）

- 任何阶段都必须可运行且可回归：至少通过 `python -m unittest discover -s tests -v` 与关键接口抽样验收
- 每个阶段完成后提交 Git，便于回滚
- 保留 legacy.py 直到所有模块迁移完成

### 2.3 不引入新复杂度

- 不引入新的框架或库
- 不改变现有的技术栈（Flask + SQLite）
- 不引入复杂的依赖注入框架
- 保持代码简单、直接、易于理解

### 2.4 性能要求

- 响应时间不超过迁移前的 110%
- 内存使用无明显增加
- 启动时间无明显增加

---

## 3. 总体架构设计

### 3.1 四层架构

采用清晰的分层架构，职责分离：

```
┌─────────────────────────────────────────────────────────┐
│  Routes 层（路由注册）                                    │
│  - URL 到函数的映射                                       │
│  - Blueprint 创建和注册                                   │
│  - 不包含业务逻辑                                         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────┐
│  Controllers 层（请求处理）【新增】                       │
│  - 参数解析和验证                                         │
│  - 鉴权检查（@login_required）                           │
│  - 调用 Services/Repositories                           │
│  - 响应封装（jsonify）                                    │
│  - 错误处理（try-except）                                │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Services 层（业务逻辑）【已有】                          │
│  - 业务流程编排                                           │
│  - 多后端回退（Graph API → IMAP）                        │
│  - 不依赖 Flask request/response                         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Repositories 层（数据访问）【已有】                      │
│  - SQL 查询和数据映射                                     │
│  - 不包含业务逻辑                                         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Database（SQLite）                                      │
└─────────────────────────────────────────────────────────┘
```

### 3.2 依赖方向约束（必须遵守）

```
routes → controllers → services → repositories → db
```

**禁止反向依赖：**
- repositories 不能依赖 services
- services 不能依赖 controllers
- controllers 不能依赖 routes

**横切关注点（可被任何层依赖）：**
- `config` - 配置管理
- `errors` - 错误模型
- `security` - 安全模块
- `audit` - 审计日志
- `db` - 数据库连接

### 3.3 当前架构 vs 目标架构

**当前架构（迁移前）：**
```
routes/ (Blueprint) → legacy.py (5757行) → services/ → repositories/
                          ↓
                    包含所有路由处理逻辑
```

**目标架构（迁移后）：**
```
routes/ (Blueprint) → controllers/ → services/ → repositories/
                          ↓
                    职责清晰的请求处理层
```

---

## 4. Controllers 层技术设计

### 4.1 目录结构

```
outlook_web/
├── controllers/
│   ├── __init__.py          # 模块导出
│   ├── accounts.py          # 账号管理 Controller（20 个路由）
│   ├── emails.py            # 邮件操作 Controller（4 个路由）
│   ├── groups.py            # 分组管理 Controller（6 个路由）
│   ├── tags.py              # 标签管理 Controller（4 个路由）
│   ├── temp_emails.py       # 临时邮箱 Controller（3 个路由）
│   ├── oauth.py             # OAuth 授权 Controller（2 个路由）
│   ├── settings.py          # 系统设置 Controller（3 个路由）
│   ├── scheduler.py         # 定时任务 Controller（1 个路由）
│   ├── system.py            # 系统信息 Controller（3 个路由）
│   ├── audit.py             # 审计日志 Controller（1 个路由）
│   └── pages.py             # 页面路由 Controller（3 个路由）
```

### 4.2 Controller 职责边界

**必须做的事情：**
- ✅ 参数解析（从 request 中提取参数）
- ✅ 参数验证（基本验证，如非空检查）
- ✅ 鉴权检查（使用 @login_required 装饰器）
- ✅ 调用 services 或 repositories
- ✅ 响应封装（使用 jsonify）
- ✅ 错误处理（try-except，返回标准错误格式）

**不应该做的事情：**
- ❌ 直接操作数据库（应调用 repositories）
- ❌ 复杂的业务逻辑（应调用 services）
- ❌ 直接调用第三方 API（应通过 services）
- ❌ 数据加密/解密（应使用 security 模块）
- ❌ 依赖 Flask 全局对象传递到下层（request, g, session 只在 controller 中使用）

### 4.3 Controller 标准模式

#### 4.3.1 简单 CRUD Controller

```python
# outlook_web/controllers/groups.py
from flask import request, jsonify
from outlook_web.security.auth import login_required
from outlook_web.repositories import groups as groups_repo
from outlook_web.errors import build_error_payload

@login_required
def api_get_groups():
    """获取所有分组"""
    try:
        # 1. 调用 repository
        groups = groups_repo.get_all_groups()

        # 2. 返回响应
        return jsonify(groups)
    except Exception as e:
        # 3. 错误处理
        return jsonify(build_error_payload(str(e))), 500

@login_required
def api_add_group():
    """添加分组"""
    try:
        # 1. 参数解析
        data = request.get_json()
        name = data.get('name', '').strip()

        # 2. 参数验证
        if not name:
            return jsonify(build_error_payload('分组名称不能为空')), 400

        # 3. 调用 repository
        group_id = groups_repo.create_group(name)

        # 4. 返回响应
        return jsonify({'id': group_id, 'name': name})
    except Exception as e:
        # 5. 错误处理
        return jsonify(build_error_payload(str(e))), 500
```

#### 4.3.2 复杂业务逻辑 Controller

```python
# outlook_web/controllers/emails.py
from flask import request, jsonify
from outlook_web.security.auth import login_required
from outlook_web.services import graph as graph_service
from outlook_web.services import imap as imap_service
from outlook_web.repositories import accounts as accounts_repo
from outlook_web.errors import build_error_payload

@login_required
def api_get_emails(email_addr: str):
    """获取邮件列表（支持 Graph API 和 IMAP 回退）"""
    try:
        # 1. 获取账号信息
        account = accounts_repo.get_account_by_email(email_addr)
        if not account:
            return jsonify(build_error_payload('账号不存在')), 404

        # 2. 参数解析
        folder = request.args.get('folder', 'inbox')
        skip = request.args.get('skip', 0, type=int)
        top = request.args.get('top', 20, type=int)

        # 3. 调用 service（业务逻辑在 service 中）
        result = graph_service.get_emails(
            client_id=account['client_id'],
            refresh_token=account['refresh_token'],
            folder=folder,
            skip=skip,
            top=top,
            proxy_url=account.get('proxy_url')
        )

        # 4. 如果 Graph API 失败，回退到 IMAP（回退逻辑在 service 中）
        if not result.get('success'):
            result = imap_service.get_emails(
                account=email_addr,
                client_id=account['client_id'],
                refresh_token=account['refresh_token'],
                folder=folder,
                skip=skip,
                top=top
            )

        # 5. 返回响应
        return jsonify(result)
    except Exception as e:
        # 6. 错误处理
        return jsonify(build_error_payload(str(e))), 500
```

### 4.4 是否需要 Controller 基类？

**决策：不需要**

**理由：**
1. Flask 本身不需要基类，使用装饰器和工具函数更简单
2. Python 的鸭子类型不需要强制继承
3. 统一的错误处理可以通过全局错误处理器实现
4. 统一的响应格式可以通过工具函数实现
5. 避免增加不必要的复杂度

**替代方案：**
- 使用装饰器（@login_required）
- 使用工具函数（build_error_payload, jsonify）
- 使用全局错误处理器（app.register_error_handler）

---

## 5. Routes 层技术设计

### 5.1 Blueprint 创建模式

#### 5.1.1 迁移前（使用 impl 参数）

```python
# outlook_web/routes/groups.py
from flask import Blueprint

def create_blueprint(*, impl) -> Blueprint:
    """
    创建 groups Blueprint

    Args:
        impl: 实现模块（legacy.py）
    """
    bp = Blueprint("groups", __name__)

    # 路由注册（使用 impl 的函数）
    bp.add_url_rule("/api/groups", view_func=impl.api_get_groups, methods=["GET"])
    bp.add_url_rule("/api/groups", view_func=impl.api_add_group, methods=["POST"])
    bp.add_url_rule("/api/groups/<int:group_id>", view_func=impl.api_update_group, methods=["PUT"])
    bp.add_url_rule("/api/groups/<int:group_id>", view_func=impl.api_delete_group, methods=["DELETE"])

    return bp
```

#### 5.1.2 迁移后（直接导入 controller）

```python
# outlook_web/routes/groups.py
from flask import Blueprint
from outlook_web.controllers import groups as groups_controller

def create_blueprint() -> Blueprint:
    """创建 groups Blueprint"""
    bp = Blueprint("groups", __name__)

    # 路由注册（直接使用 controller 的函数）
    bp.add_url_rule("/api/groups", view_func=groups_controller.api_get_groups, methods=["GET"])
    bp.add_url_rule("/api/groups", view_func=groups_controller.api_add_group, methods=["POST"])
    bp.add_url_rule("/api/groups/<int:group_id>", view_func=groups_controller.api_update_group, methods=["PUT"])
    bp.add_url_rule("/api/groups/<int:group_id>", view_func=groups_controller.api_delete_group, methods=["DELETE"])

    return bp
```

### 5.2 必须保持不变

- ✅ URL 路径不变
- ✅ HTTP 方法不变
- ✅ 路由注册顺序不变
- ✅ Blueprint 名称不变
- ✅ URL 参数（如 `<int:group_id>`）不变

---

（文档未完，待续...）
## 6. App.py 应用工厂设计

### 6.1 Blueprint 注册模式

#### 6.1.1 迁移前

```python
# outlook_web/app.py
from outlook_web import legacy
from outlook_web.routes import groups, tags, accounts, emails

def create_app():
    app = Flask(__name__)
    
    # ... 其他初始化代码 ...
    
    # Blueprint 注册（使用 impl=legacy）
    app.register_blueprint(groups.create_blueprint(impl=legacy))
    app.register_blueprint(tags.create_blueprint(impl=legacy))
    app.register_blueprint(accounts.create_blueprint(impl=legacy))
    app.register_blueprint(emails.create_blueprint(impl=legacy))
    
    return app
```

#### 6.1.2 迁移后

```python
# outlook_web/app.py
from outlook_web.routes import groups, tags, accounts, emails

def create_app():
    app = Flask(__name__)
    
    # ... 其他初始化代码 ...
    
    # Blueprint 注册（不再需要 impl 参数）
    app.register_blueprint(groups.create_blueprint())
    app.register_blueprint(tags.create_blueprint())
    app.register_blueprint(accounts.create_blueprint())
    app.register_blueprint(emails.create_blueprint())
    
    return app
```

### 6.2 必须保持不变

- ✅ Blueprint 注册顺序不变
- ✅ 中间件注册不变（before_request, after_request）
- ✅ 错误处理器注册不变（register_error_handler）
- ✅ 应用配置不变（secret_key, session 配置等）

---

## 7. 数据流设计

### 7.1 请求处理流程

```
HTTP Request
    ↓
Flask WSGI
    ↓
Middleware: ensure_trace_id()
    ↓
Routes: Blueprint 路由匹配
    ↓
Controller: 
    - 参数解析（request.args, request.get_json()）
    - 参数验证（非空检查、类型检查）
    - 鉴权检查（@login_required）
    ↓
Service/Repository:
    - 业务逻辑处理
    - 数据库操作
    ↓
Controller:
    - 响应封装（jsonify）
    - 错误处理（try-except）
    ↓
Middleware: attach_trace_id_and_normalize_errors()
    ↓
Flask WSGI
    ↓
HTTP Response
```

### 7.2 错误处理流程

```
Exception (任何层抛出)
    ↓
Controller: try-except 捕获
    ↓
build_error_payload(error_message)
    ↓
jsonify(error_payload) + HTTP 状态码
    ↓
Middleware: attach_trace_id_and_normalize_errors()
    ↓
统一错误响应格式:
{
    "success": false,
    "error": "错误信息",
    "trace_id": "xxx-xxx-xxx"
}
```

### 7.3 数据流示例：获取分组列表

```
1. HTTP GET /api/groups
2. Flask 路由匹配 → groups_controller.api_get_groups
3. Controller:
   - @login_required 检查登录状态
   - 调用 groups_repo.get_all_groups()
4. Repository:
   - 执行 SQL: SELECT * FROM groups
   - 返回 List[Dict]
5. Controller:
   - jsonify(groups)
   - 返回 HTTP 200
6. Middleware:
   - 添加 trace_id 到响应头
7. HTTP Response:
   [
       {"id": 1, "name": "分组1"},
       {"id": 2, "name": "分组2"}
   ]
```

---

## 8. 迁移策略技术设计

### 8.1 分阶段迁移技术方案

#### 8.1.1 阶段 1：基础模块（groups, tags, settings, system, audit, pages）

**技术步骤：**

1. **创建 Controller 文件**
   ```bash
   touch outlook_web/controllers/groups.py
   ```

2. **从 legacy.py 提取函数**
   - 找到 legacy.py 中的 `api_get_groups`, `api_add_group` 等函数
   - 复制到 `controllers/groups.py`

3. **调整导入语句**
   ```python
   # 迁移前（在 legacy.py 中）
   from outlook_web.repositories import groups as _groups_repo
   
   # 迁移后（在 controllers/groups.py 中）
   from outlook_web.repositories import groups as groups_repo
   ```

4. **更新 routes/groups.py**
   ```python
   # 迁移前
   def create_blueprint(*, impl) -> Blueprint:
       bp.add_url_rule("/api/groups", view_func=impl.api_get_groups, methods=["GET"])
   
   # 迁移后
   from outlook_web.controllers import groups as groups_controller
   
   def create_blueprint() -> Blueprint:
       bp.add_url_rule("/api/groups", view_func=groups_controller.api_get_groups, methods=["GET"])
   ```

5. **更新 app.py**
   ```python
   # 迁移前
   app.register_blueprint(groups.create_blueprint(impl=legacy))
   
   # 迁移后
   app.register_blueprint(groups.create_blueprint())
   ```

6. **运行测试**
   ```bash
   python -m unittest discover -s tests -v
   ```

7. **手动验证**
   ```bash
   curl -X GET http://localhost:5000/api/groups
   ```

8. **提交 Git**
   ```bash
   git add outlook_web/controllers/groups.py outlook_web/routes/groups.py outlook_web/app.py
   git commit -m "feat: 迁移 groups 模块到 controllers 层"
   ```

#### 8.1.2 阶段 2 和 3：重复相同步骤

对于 temp_emails, oauth, scheduler, emails, accounts 模块，重复上述步骤。

**注意事项：**
- emails 和 accounts 模块更复杂，需要更仔细的测试
- 确保回退机制（Graph API → IMAP）仍然正常工作
- 确保数据脱敏仍然正常工作

### 8.2 兼容性保证机制

#### 8.2.1 函数签名保持不变

```python
# 迁移前（legacy.py）
@login_required
def api_get_groups():
    """获取所有分组"""
    # ...

# 迁移后（controllers/groups.py）
@login_required
def api_get_groups():
    """获取所有分组"""
    # ... 完全相同的签名
```

#### 8.2.2 装饰器保持不变

```python
# 迁移前后都使用相同的装饰器
@login_required
def api_xxx():
    pass
```

#### 8.2.3 错误处理保持不变

```python
# 迁移前后都使用相同的错误处理
try:
    # ...
except Exception as e:
    return jsonify(build_error_payload(str(e))), 500
```

#### 8.2.4 响应格式保持不变

```python
# 迁移前后都使用相同的响应格式
return jsonify(data)  # 成功响应
return jsonify(build_error_payload(msg)), 400  # 错误响应
```

### 8.3 回滚机制

#### 8.3.1 Git 回滚

```bash
# 查看提交历史
git log --oneline

# 回滚到指定提交
git revert <commit-hash>

# 或者硬回滚（慎用）
git reset --hard <commit-hash>
```

#### 8.3.2 临时回滚（保留 legacy.py）

如果迁移后发现问题，可以临时恢复 `impl=legacy`：

```python
# 临时回滚到 legacy
from outlook_web import legacy
app.register_blueprint(groups.create_blueprint(impl=legacy))
```

**注意：** 这要求 routes/groups.py 仍然支持 `impl` 参数，所以在迁移完成前不要删除这个参数。

#### 8.3.3 分支策略

```bash
# 在独立分支进行迁移
git checkout -b feature/migrate-groups-to-controllers

# 迁移完成后合并
git checkout main
git merge feature/migrate-groups-to-controllers

# 如果出现问题，可以快速切换回 main 分支
git checkout main
```

---

## 9. 依赖管理设计

### 9.1 避免循环依赖

#### 9.1.1 依赖方向规则

```
routes → controllers → services → repositories → db
```

**禁止的依赖：**
- ❌ repositories → services
- ❌ services → controllers
- ❌ controllers → routes

#### 9.1.2 循环依赖检测

如果出现循环依赖，Python 会在导入时报错：

```python
ImportError: cannot import name 'xxx' from partially initialized module 'yyy'
```

**解决方案：**
1. 检查导入语句，确保依赖方向正确
2. 如果必须反向引用，使用延迟导入（在函数内部导入）

### 9.2 全局状态管理

#### 9.2.1 Flask 全局对象

Flask 提供的全局对象：
- `request` - 当前请求对象
- `g` - 请求级别的全局变量
- `session` - 会话对象
- `current_app` - 当前应用对象

**使用规则：**
- ✅ 在 controllers 中使用
- ❌ 不要传递到 services 或 repositories
- ❌ services 和 repositories 应该是纯函数，不依赖 Flask 全局对象

---

## 10. 测试策略设计

### 10.1 单元测试设计

使用 unittest.mock.patch Mock 依赖。

### 10.2 集成测试设计

测试完整的请求-响应流程。

### 10.3 回归测试设计

确保所有现有测试通过。

---

## 11. 性能优化设计

### 11.1 层级调用开销分析

**问题：** 增加 controllers 层会增加一层函数调用，是否会影响性能？

**分析：**
- Python 函数调用开销：约 0.1-0.5 微秒
- 数据库查询开销：约 1-10 毫秒
- HTTP 请求开销：约 10-100 毫秒

**结论：** 函数调用开销可以忽略不计（< 0.1%）

### 11.2 导入开销分析

**问题：** 每个 controller 都要导入 services 和 repositories，是否会影响启动时间？

**分析：**
- Python 的导入是缓存的，只在第一次导入时有开销
- 模块导入开销：约 1-10 毫秒
- 应用启动时间：约 1-2 秒

**结论：** 导入开销可以忽略不计（< 1%）

### 11.3 内存开销分析

**问题：** 增加模块会增加内存使用吗？

**分析：**
- 每个模块的内存开销：约 10-100 KB
- 应用总内存使用：约 50-100 MB

**结论：** 内存开销可以忽略不计（< 0.1%）

### 11.4 性能优化建议

**不需要特殊优化：**
- 层级调用开销极小
- 导入开销极小
- 内存开销极小

**如果确实需要优化：**
- 使用数据库连接池（已有）
- 使用缓存（如果需要）
- 优化 SQL 查询（已有索引）

---

## 12. 错误处理设计

### 12.1 统一错误格式

所有 API 错误响应使用统一格式：

```json
{
    "success": false,
    "error": "错误信息",
    "trace_id": "xxx-xxx-xxx"
}
```

### 12.2 错误处理流程

```python
@login_required
def api_xxx():
    try:
        # 业务逻辑
        result = service.do_something()
        return jsonify(result)
    except Exception as e:
        # 统一错误处理
        return jsonify(build_error_payload(str(e))), 500
```

### 12.3 全局错误处理器

保持现有的全局错误处理器：

```python
# outlook_web/app.py
app.register_error_handler(HTTPException, legacy.handle_http_exception)
app.register_error_handler(Exception, legacy.handle_exception)
```

---

## 13. 兼容性保证设计

### 13.1 API 契约不变

- ✅ URL 路径不变
- ✅ HTTP 方法不变
- ✅ 请求参数不变
- ✅ 响应格式不变
- ✅ 错误格式不变
- ✅ HTTP 状态码不变

### 13.2 功能行为不变

- ✅ 鉴权机制不变（@login_required）
- ✅ 数据脱敏不变（client_id, refresh_token）
- ✅ 审计日志不变
- ✅ CSRF 防护不变
- ✅ 回退机制不变（Graph API → IMAP）
- ✅ trace_id 机制不变

### 13.3 部署方式不变

- ✅ Docker 启动命令不变
- ✅ Gunicorn 启动命令不变
- ✅ 环境变量配置不变
- ✅ 数据库结构不变

---

## 14. 代码示例汇总

### 14.1 完整的 Controller 示例

```python
# outlook_web/controllers/groups.py
from flask import request, jsonify
from outlook_web.security.auth import login_required
from outlook_web.repositories import groups as groups_repo
from outlook_web.errors import build_error_payload

@login_required
def api_get_groups():
    """获取所有分组"""
    try:
        groups = groups_repo.get_all_groups()
        return jsonify(groups)
    except Exception as e:
        return jsonify(build_error_payload(str(e))), 500

@login_required
def api_get_group(group_t):
    """获取单个分组"""
    try:
        group = groups_repo.get_group_by_id(group_id)
        if not group:
            return jsonify(build_error_payload('分组不存在')), 404
        return jsonify(group)
    except Exception as e:
        return jsonify(build_error_payload(str(e))), 500

@login_required
def api_add_group():
    """添加分组"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify(build_error_payload('分组名称不能为空')), 400
        
        group_id = groups_repo.create_group(name)
        return jsonify({'id': group_id, 'name': name})
    except Exception as e:
        return jsonify(build_error_payload(str(e))), 500

@login_required
def api_update_group(group_id: int):
    """更新分组"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify(build_error_payload('分组名称不能为空')), 400
        
        success = groups_repo.update_group(group_id, name)
        if not success:
      urn jsonify(build_error_payload('分组不存在')), 404
        
        return jsonify({'id': group_id, 'name': name})
    except Exception as e:
        return jsonify(build_error_payload(str(e))), 500

@login_required
def api_delete_group(group_id: int):
    """删除分组"""
    try:
        success = groups_repo.delete_group(group_id)
        if not success:
            return jsonify(build_error_payload('分组不存在')), 404
        
        return jsonify({'message': '删除成功'})
    except Exception as e:
        return jsonify(build_error_payload(str(e))), 500
```

### 14.2 完整的 Routes 示例

```python
# outlook_web/routes/groups.py
from flask import Blueprint
from outlook_web.controllers import groups as groups_controller

def create_blueprint() -> Blueprint:
    """创建 groups Blueprint"""
    bp = Blueprint("groups", __name__)
    
    bp.add_url_rule("/api/groups", 
                    view_func=groups_controller.api_get_groups, 
                    methods=["GET"])
    
    bp.add_url_rule("/api/groups/<int:group_id>", 
                    view_func=groups_controller.api_get_group, 
                    methods=["GET"])
    
    bp.add_url_rule("/api/groups", 
                    view_func=groups_controller.api_add_group, 
                    methods=["POST"])
    
    bp.add_url_rule("/api/groups/<int:group_id>", 
                    view_func=groups_controller.api_update_group, 
                    methods=["PUT"])
    
    bp.add_url_rule("/api/groups/<int:group_id>", 
                    view_func=groups_controller.api_delete_group, 
                    methods=["DELETE"])
    
    return bp
```

### 14.3 完整的测试示例

```python
# tests/test_controllers_groups.py
import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from outlook_web.controllers import groups as groups_controller

class TestGroupsController(unittest.TestCase):
    
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        @self.app.route('/api/groups')
        def get_groups():
            return groups_controller.api_get_groups()
    
    @patch('outlook_web.controllers.groups.session')
    @patch('outlook_web.controllers.groups.groups_repo')
    def test_api_get_groups_success(self, mock_repo, mock_session):
        mock_session.get.return_value = True
        mock_repo.get_all_groups.return_value = [
            {'id': 1, 'name': '分组1'},
            {'id': 2, 'name': '分组2'}
        ]
        
        response = self.client.get('/api/groups')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['name'], '分组1')

if __name__ == '__main__':
    unittest.main()
```

---

## 15. 实施检查清单

### 15.1 迁移前检查

- [ ] 阅读 PRD 和 FD 文档
- [ ] 阅读本 TDD 文档
- [ ] 理解现有架构
- [ ] 运行所有测试，确保通过
- [ ] 创建 Git 分支

### 15.2 迁移中检查

- [ ] 创建 controllers 目录
- [ ] 创建 controller 文件
- [ ] 从 legacy.py 提取函数
- [ ] 调整导入语句
- [ ] 更新 routes 文件
- [ ] 更新 app.py
- [ ] 运行测试
- [ ] 手动验证
- [ ] 提交 Git

### 15.3 迁移后检查

- [ ] 所有测试通过
- [ ] 所有功能正常
- [ ] 性能无明显下降
- [ ] 文档已更新
- [ ] 代码审查通过

---

## 16. 总结

### 16.1 技术要点

1. **四层架构**：routes → controllers → services → repositories
2. **职责清晰**：每层只做一件事
3. **依赖单向**：避免循环依赖
4. **兼容性保证**：API 契约不变
5. **分阶段迁移**：可回滚、可验证
6. **测试覆盖**：单元测试 + 集成测试

### 16.2 关键决策

1. **不使用 Controller 基类**：使用装饰器和工具函数更简单
2. **不引入 DI 框架**：直接导入即可，测试时使用 mock
3. **保留 legacy.py**：直到所有模块迁移完成
4. **分阶段迁移**：从简单到复杂，降低风险

##益

1. **代码可维护性提升**：职责清晰，易于理解
2. **测试覆盖率提升**：易于编写单元测试
3. **代码复用性提升**：services 可以被多个 controllers 调用
4. **团队协作效率提升**：模块化便于并行开发

---

**文档版本：** v1.0
**最后更新：** 2026-02-24
**维护者：** 开发团队
