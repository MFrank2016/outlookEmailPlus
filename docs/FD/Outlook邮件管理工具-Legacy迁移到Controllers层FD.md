# Outlook 邮件管理工具｜Legacy 迁移到 Controllers 层 FD（功能实现清单，仅说明做什么）

- 文档状态：草案
- 版本：V1.0
- 日期：2026-02-24
- 对齐 PRD：`docs/PRD/PRD-00003-Legacy代码拆分到Controllers层.md`
- 对齐开发指南：`docs/DEV/00002-前后端拆分-开发者指南.md`

---

## 1. 文档目的

本 FD 用于把"Legacy 迁移到 Controllers 层 PRD"拆解为**可执行的功能清单**，用于开发/测试/验收对齐。
仅描述**要实现/保证的功能与行为**，不讨论具体实现方式与技术细节。

---

## 2. 总交付清单（必须完成）

### 2.1 创建 Controllers 层目录结构

- 在 `outlook_web/` 下创建 `controllers/` 目录
- 创建 11 个 controller 模块文件：
  - `controllers/accounts.py` - 账号管理（20 个路由）
  - `controllers/emails.py` - 邮件操作（4 个路由）
  - `controllers/groups.py` - 分组管理（6 个路由）
  - `controllers/tags.py` - 标签管理（4 个路由）
  - `controllers/temp_emails.py` - 临时邮箱（3 个路由）
  - `controllers/oauth.py` - OAuth 授权（2 个路由）
  - `controllers/settings.py` - 系统设置（3 个路由）
  - `controllers/scheduler.py` - 定时任务（1 个路由）
  - `controllers/system.py` - 系统信息（3 个路由）
  - `controllers/audit.py` - 审计日志（1 个路由）
  - `controllers/pages.py` - 页面路由（3 个路由）
- 创建 `controllers/__init__.py` 用于模块导出

### 2.2 迁移所有路由处理函数

- 从 `legacy.py` 提取 54 个 API 路由处理函数到对应的 controller 文件
- 保持函数签名和行为完全一致
- 保持装饰器（@login_required）不变
- 保持错误处理和 trace_id 机制不变
- 保持响应格式（jsonify）不变

### 2.3 更新 Routes 层

- 更新 11 个 routes 文件，移除 `impl` 参数
- 直接导入对应的 controller 模块
- 保持 URL 映射和 HTTP 方法不变
- 保持路由注册顺序不变

### 2.4 更新应用工厂

- 更新 `outlook_web/app.py` 中的 Blueprint 注册
- 移除所有 `impl=legacy` 参数
- 保持 Blueprint 注册顺序不变
- 保持中间件和错误处理器注册不变

### 2.5 清理 Legacy.py

- 删除已迁移的 54 个路由处理函数
- 保留工具函数和中间件（暂时）
- 保留初始化函数（init_app, init_db 等）
- 最终目标：完全删除 legacy.py

### 2.6 工具函数迁移（可选，后续阶段）

- 创建 `outlook_web/utils/` 目录
- 迁移工具函数到对应的 utils 模块：
  - `utils/sanitize.py` - sanitize_input, decode_header_value
  - `utils/email_parser.py` - get_email_body, parse_account_string
  - `utils/datetime.py` - utcnow
  - `utils/proxy.py` - build_proxies

### 2.7 中间件迁移（可选，后续阶段）

- 创建 `outlook_web/middleware/` 目录
- 迁移中间件函数：
  - `middleware/trace.py` - ensure_trace_id, attach_trace_id_and_normalize_errors
  - `middleware/error_handler.py` - handle_http_exception, handle_exception

---

## 3. 分阶段交付清单

### 3.1 阶段 1：基础模块（低复杂度，无依赖）

**目标模块：** groups, tags, settings, system, audit, pages

**交付物：**
- 创建 6 个 controller 文件
- 迁移 19 个路由处理函数
- 更新 6 个 routes 文件
- 更新 app.py 中的 6 个 Blueprint 注册

**功能清单：**

#### 3.1.1 Groups Controller
- `api_get_groups()` - 获取所有分组
- `api_get_group(group_id)` - 获取单个分组
- `api_add_group()` - 添加分组
- `api_update_group(group_id)` - 更新分组
- `api_delete_group(group_id)` - 删除分组
- `api_export_group(group_id)` - 导出分组账号

#### 3.1.2 Tags Controller
- `api_get_tags()` - 获取所有标签
- `api_add_tag()` - 添加标签
- `api_delete_tag(tag_id)` - 删除标签
- `api_batch_manage_tags()` - 批量管理标签

#### 3.1.3 Settings Controller
- `api_get_settings()` - 获取系统设置
- `api_update_settings()` - 更新系统设置
- `api_validate_cron()` - 验证 Cron 表达式

#### 3.1.4 System Controller
- `api_health_check()` - 健康检查
- `api_get_diagnostics()` - 获取诊断信息
- `api_get_upgrade_status()` - 获取升级状态

#### 3.1.5 Audit Controller
- `api_get_audit_logs()` - 获取审计日志

#### 3.1.6 Pages Controller
- `login()` - 登录页面
- `logout()` - 登出
- `index()` - 首页

**验收标准：**
- 所有 19 个路由功能正常
- 所有测试通过
- 手动验证功能无异常

### 3.2 阶段 2：独立功能模块

**目标模块：** temp_emails, oauth, scheduler

**交付物：**
- 创建 3 个 controller 文件
- 迁移 6 个路由处理函数
- 更新 3 个 routes 文件
- 更新 app.py 中的 3 个 Blueprint 注册

**功能清单：**

#### 3.2.1 Temp Emails Controller
- `api_get_temp_emails()` - 获取临时邮箱列表
- `api_generate_temp_email()` - 生成临时邮箱
- `api_get_temp_email_messages(email_id)` - 获取临时邮箱消息

#### 3.2.2 OAuth Controller
- `api_get_oauth_auth_url()` - 获取 OAuth 授权 URL
- `api_exchange_oauth_token()` - 交换 OAuth Token

#### 3.2.3 Scheduler Controller
- `api_get_scheduler_status()` - 获取调度器状态

**验收标准：**
- 所有 6 个路由功能正常
- OAuth 授权流程正常
- 临时邮箱功能正常
- 调度器状态查询正常

### 3.3 阶段 3：核心复杂模块

**目标模块：** emails, accounts

**交付物：**
- 创建 2 个 controller 文件
- 迁移 24 个路由处理函数
- 更新 2 个 routes 文件
- 更新 app.py 中的 2 个 Blueprint 注册

**功能清单：**

#### 3.3.1 Emails Controller
- `api_get_emails(email_addr)` - 获取邮件列表
- `api_get_email_detail(email_addr, message_id)` - 获取邮件详情
- `api_delete_emails()` - 删除邮件
- `api_extract_verification(email_addr)` - 提取验证码

**关键行为：**
- 支持 Graph API 和 IMAP 回退机制
- 支持代理配置
- 支持多文件夹（inbox, junk）
- 支持分页（skip, top）

#### 3.3.2 Accounts Controller
- `api_get_accounts()` - 获取账号列表
- `api_get_account(account_id)` - 获取单个账号
- `api_add_account()` - 添加账号
- `api_update_account(account_id)` - 更新账号
- `api_update_account_status(account_id, status)` - 更新账号状态
- `api_delete_account(account_id)` - 删除账号
- `api_delete_account_by_email(email_addr)` - 按邮箱删除账号
- `api_batch_delete_accounts()` - 批量删除账号
- `api_batch_update_account_group()` - 批量更新分组
- `api_search_accounts()` - 搜索账号
- `api_export_all_accounts()` - 导出所有账号
- `api_export_selected_accounts()` - 导出选中账号
- `api_generate_export_verify_token()` - 生成导出验证 Token
- `api_refresh_account(account_id)` - 刷新单个账号
- `api_refresh_all_accounts()` - 刷新所有账号
- `api_retry_refresh_account(account_id)` - 重试刷新账号
- `api_refresh_failed_accounts()` - 刷新失败账号
- `api_trigger_scheduled_refresh()` - 触发定时刷新
- `api_get_refresh_logs()` - 获取刷新日志
- `api_get_account_refresh_logs(account_id)` - 获取账号刷新日志
- `api_get_failed_refresh_logs()` - 获取失败刷新日志
- `api_get_refresh_stats()` - 获取刷新统计

**关键行为：**
- 支持分组过滤
- 支持标签管理
- 支持批量操作
- 支持导出验证（二次确认）
- 支持 Token 刷新和重试
- 支持刷新日志查询
- 数据脱敏（client_id, refresh_token）

**验收标准：**
- 所有 24 个路由功能正常
- 邮件读取和删除功能正常
- 账号 CRUD 功能正常
- Token 刷新功能正常
- 批量操作功能正常
- 导出功能正常

### 3.4 阶段 4：清理和优化

**交付物：**
- 删除 legacy.py 中已迁移的路由处理函数
- 迁移工具函数到 utils/（可选）
- 迁移中间件到 middleware/（可选）
- 最终删除 legacy.py（如果所有代码都已迁移）
- 更新文档

**验收标准：**
- legacy.py 已删除或仅保留必要的初始化代码
- 所有功能正常
- 所有测试通过
- 文档已更新

---

## 4. Controllers 层职责规范

### 4.1 必须做的事情

- ✅ 参数解析和验证（从 request 中提取参数）
- ✅ 鉴权检查（使用 @login_required 装饰器）
- ✅ 调用 services 层或 repositories 层
- ✅ 响应封装（使用 jsonify）
- ✅ 错误处理（try-except，返回标准错误格式）
- ✅ 保持 trace_id 透传

### 4.2 不应该做的事情

- ❌ 直接操作数据库（应调用 repositories）
- ❌ 复杂的业务逻辑（应调用 services）
- ❌ 直接调用第三方 API（应通过 services）
- ❌ 数据加密/解密（应使用 security 模块）

### 4.```python
@login_required
def api_xxx():
    """函数说明"""
    try:
        # 1. 参数解析
        param1 = request.args.get('param1')
        param2 = request.get_json().get('param2')

        # 2. 参数验证
        if not param1:
            return jsonify(build_error_payload('参数错误')), 400

        # 3. 调用 service/repository
        result = service.do_something(param1, param2)

        # 4. 返回响应
        return jsonify(result)
    except Exception as e:
        # 5. 错误处理
        return jsonify(build_error_payload(str(e))), 500
```

---

## 5. 层更新规范

### 5.1 更新前（使用 impl 参数）

```python
# outlook_web/routes/groups.py
def create_blueprint(*, impl) -> Blueprint:
    bp = Blueprint("groups", __name__)
    bp.add_url_rule("/api/groups", view_func=impl.api_get_groups, methods=["GET"])
    return bp
```

### 5.2 更新后（直接导入 controller）

```python
# outlook_web/routes/groups.py
from flask import Blueprint
from outlook_web.controllers import groups as groups_controller

def create_blueprint() -> Blueprint:
    bp = Blueprint("groups", __name__)
    bp.add_url_rule("/api/groups", view_func=groups_controller.api_get_groups, methods=["GET"])
    return bp
```

### 5.3 必须保持不变

- ✅ URL 路径不变
- ✅ HTTP 方法不变
- ✅ 路由注册顺序不变
- ✅ Blueprint 名称不变

---

## 6. App.py 更新规范

### 6.1 更新前

```python
from outlook_web import legacy
from outlook_web.routes import groups

app.register_blueprint(groups.create_blueprint(impl=legacy))
```

### 6.2 更新后

```python
from outlook_web.routes import groups

app.register_blueprint(groups.create_blueprint())
```

### 6.3 必须保持不变

- ✅ Blueprint 注册顺序不变
- ✅ 中间件注册不变
- ✅ 错误处理器注册不变
- ✅ 应用配置不变

---

## 7. 兼容性保证（必须满足）

### 7.1 API 契约不变

- 所有 URL 路径保持不变
- 所有请求参数保持不变
- 所有响应格式保持不变
- 所有错误格式保持不变
- trace_id 机制保持不变

### 7.2 功能行为不变

- 鉴权机制保持不变（@login_required）
- 数据脱敏保持不变（client_id, refresh_token）
- 审计日志保持不变
- CSRF 防护保持不变（如果启用）
- 回退机制保持不变（Graph API → IMAP）

### 7.3 部署方式不变

- Docker 启动命令不变
- Gunicorn 启动命令不变
- 环境变量配置不变
- 数据库结构不变

---

## 8. 测试验收清单

### 8.1 单元测试

- [ ] 所有现有单元测试通过
- [ ] 新增 controller 单元测试（可选）
- [ ] 测试覆盖率不降低

### 8.2 集成测试

- [ ] 所有 API 路由可访问
- [ ] 所有功能正常工作
- [ ] 错误处理正确
- [ ] trace_id 正常透传

### 8.3 回归测试

- [ ] 登录功能正常
- [ ] 分组管理功能正常
- [ ] 账号管理功能正常
- [ ] 标签管理功能正常
- [ ] 邮件读取功能正常
- [ ] 邮件删除功能正常
- [ ] Token 刷新功能正常
- [ ] 导出功能正常
- [ ] 临时邮箱功能正常
- [ ] OAuth 授权功能正常
- [ ] 系统设置功能正常
- [ ] 审计日志功能正常

### 8.4 性能测试

- [ ] 响应时间不超过迁移前的 110%
- [ ] 内存使用无明显增加
- [ ] 并发处理能力不下降

### 8.5 手动验证

- [ ] 前端页面正常加载
- [ ] 所有按钮和操作正常
- [ ] 错误提示正常显示
- [ ] 数据正确展示

---

## 9. 风险控制清单

### 9.1 迁移风险

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| 路由映射错误 | 高 | 分阶段迁移，每阶段充分测试 |
| 参数解析错误 | 高 | 保持函数签名一致，单元测试覆盖 |
| 依赖关系错误 | 中 | 先迁移无依赖模块，后迁移复杂模块 |
| 性能下降 | 中 | 性能测试对比 |
| 功能回归 | 高 | 完整的回归测试 |

### 9.2 回滚策略

- 每个阶段完成后提交 Git
- 如果出现问题，可以快速回滚到上一个阶段
- 保留 legacy.py 直到所有模块迁移完成
- 如果需要紧急回滚，可以临时恢复 `impl=legacy`

---

## 10. 文档更新清单

### 10.1 必须更新的文档

- [ ] `CLAUDE.md` - 更新项目架构说明
- [ ] `docs/DEV/00002-前后端拆分-开发者指南.md` - 更新开发指南
- [ ] `docs/QA/回归验证清单.md` - 更新验证清单（如有需要）

### 10.2 可选更新的文档

- [ ] `README.md` - 更新项目说明（如有需要）
- [ ] API 文档 - 更新 API 说明（如有需要）

---

## 11. 验收标准（最终交付）

### 11.1 代码质量

- [ ] 所有 54 个路由处理函数已迁移到 controllers/
- [ ] legacy.py 已删除或仅保留必要代码
- [ ] 代码结构清晰，职责明确
- [ ] 无重复代码

### 11.2 功能完整性

- [ ] 所有功能正常工作
- [ ] 所有 API 契约保持不变
- [ ] 所有测试通过
- [ ] 无功能回归

### 11.3 性能指标

- [ ] 响应时间 < 迁移前 110%
- [ ] 内存使用无明显增加
- [ ] 启动时间无明显增加

### 11.4 文档完整性

- [ ] 所有文档已更新
- [ ] 开发指南清晰
- [ ] 验收清单完整

---

## 12. 附录：路由清单

### 12.1 Groups 模块（6 个路由）

| 路由 | 方法 | 函数 | 说明 |
|------|------|------|------|
| `/api/groups` | GET | api_get_groups | 获取所有分组 |
| `/api/groups/<int:group_id>` | GET | api_get_group | 获取单个分组 |
| `/api/groups` | POST | api_add_group | 添加分组 |
| `/api/groups/<int:group_id>` | PUT | api_update_group | 更新分组 |
| `/api/groups/<int:group_id>` | DELETE | api_delete_group | 删除分组 |
| `/api/groups/<int:group_id>/export` | GET | api_export_group | 导出分组账号 |

### 12.2 Tags 模块（4 个路由）

| 路由 | 方法 | 函数 | 说明 |
|------|------|------|------|
| `/api/tags` | GET | api_get_tags | 获取所有标签 |
| ` POST | api_add_tag | 添加标签 |
| `/api/tags/<int:tag_id>` | DELETE | api_delete_tag | 删除标签 |
| `/api/accounts/tags` | POST | api_batch_manage_tags | 批量管理标签 |

### 12.3 Settings 模块（3 个路由）

| 路由 | 方法 | 函数 | 说明 |
|------|------|------|------|
| `/api/settings` | GET | api_get_settings | 获取系统设置 |
| `/api/settings` | POST | api_update_settings | 更新系统设置 |
| `/api/settings/validate-cron` | POST | api_validate_cron | 验证 Cron 表达式 |

### 12.4 System 模块（3 个路由）

| 路由 | 方法 | 函数 | 说明 |
|------|------|------|------|
| `/healthz` | GET | api_health_check | 健康检查 |
| `/api/system/diagnostics` | GET | api_get_diagnostics | 获取诊断信息 |
| `/api/system/upgrade-status` | GET | api_get_upgrade_status | 获取升级状态 |

### 12.5 Audit 模块（1 个路由）

| 路由 | 方法 | 函数 | 说明 |
|------|------|------|------|
| `/api/audit-logs` | GET | api_get_audit_logs | 获取审计日志 |

### 12.6 Pages 模块（3 个路由）

| 路由 | 方法 | 函数 | 说明 |
|------|------|------|------|
| `/login` | GET/POST | login | 登录页面 |
| `/logout` | GET | logout | 登出 |
| `/` | GET | index | 首页 |

### 12.7 Temp Emails 模块（3 个路由）

| 路由 | 方法 | 函数 | 说明 |
|------|------|------|------|
| `/api/temp-emails` | GET | api_get_temp_emails | 获取临时邮箱列表 |
| `/api/temp-emails/generate` | POST | api_generate_temp_email | 生成临时邮箱 |
| `/api/temp-emails/<path:email_id>` | GET | api_get_temp_email_messages | 获取临时邮箱消息 |

### 12.8 OAuth 模块（2 个路由）

| 路由 | 方法 | 函数 | 说明 |
|------|------|------|------|
| `/api/oauth/auth-url` | GET | api_get_oauth_auth_url | 获取 OAuth 授权 URL |
| `/api/oauth/exchange-token` | POST | api_exchange_oauth_token | 交换 OAuth Token |

### 12.9 Scheduler 模块（1 个路由）

| 路由 | 方法 | 函数 | 说明 |
|------|------|------|------|
| `/api/scheduler/status` | GET | api_get_scheduler_status | 获取调度器状态 |

### 12.10 Emails 模块（4 个路由）

| 路由 | 方法 | 函数 | 说明 |
|------|------|------|------|
| `/api/emails/<email_addr>` | GET | api_get_emails | 获取邮件列表 |
| `/api/email/<email_addr>/<path:message_id>` | GET | api_get_email_detail | 获取邮件详情 |
| `/api/emails/delete` | POST | api_delete_emails | 删除邮件 |
| `/api/emails/<email_addr>/extract-verification` | GET | api_extract_verification | 提取验证码 |

### 12.11 Accounts 模块（20 个路由）

| 路由 | 方法 | 函数 | 说明 |
|------|------|------|------|
| `/api/accounts` | GET | api_get_accounts | 获取账号列表 |
| `/api/accounts/<int:account_id>` | GET | api_get_account | 获取单个账号 |
| `/api/accounts` | POST | api_add_account | 添加账号 |
| `/api/accounts/<int:account_id>` | PUT | api_update_account | 更新账号 |
| `/api/accounts/<int:account_id>` | DELETE | api_delete_account | 删除账号 |
| `/api/accounts/email/<email_addr>` | DELETE | api_delete_account_by_email | 按邮箱删除账号 |
| `/api/accounts/batch-delete` | POST | api_batch_delete_accounts | 批量删除账号 |
| `/api/accounts/batch-update-group` | POST | api_batch_update_account_group | 批量更新分组 |
| `/api/accounts/search` | GET | api_search_accounts | 搜索账号 |
| `/api/accounts/export` | GET | api_export_all_accounts | 导出所有账号 |
| `/api/accounts/export-selected` | POST | api_export_selected_accounts | 导出选中账号 |
| `/api/export/verify` | POST | api_generate_export_verify_token | 生成导出验证 Token |
| `/api/accounts/<int:account_id>/refresh` | POST | account | 刷新单个账号 |
| `/api/accounts/refresh-all` | GET | api_refresh_all_accounts | 刷新所有账号 |
| `/api/accounts/<int:account_id>/retry-refresh` | POST | api_retry_refresh_account | 重试刷新账号 |
| `/api/accounts/refresh-failed` | POST | api_refresh_failed_accounts | 刷新失败账号 |
| `/api/accounts/trigger-scheduled-refresh` | GET | api_trigger_scheduled_refresh | 触发定时刷新 |
| `/api/accounts/refresh-logs` | GET | api_get_refresh_logs | 获取刷新日志 |
| `/api/accounts/<int:account_id>/refresh-logs` | GET | api_get_account_refresh_logs | 获取账号刷新日志 |
| `/api/accounts/refresh-logs/failed` | GET | api_get_failed_refresh_logs | 获取失败刷新日志 |
| `/api//refresh-stats` | GET | api_get_refresh_stats | 获取刷新统计 |

---

**文档版本：** v1.0
**最后更新：** 2026-02-24
**维护者：** 开发团队
