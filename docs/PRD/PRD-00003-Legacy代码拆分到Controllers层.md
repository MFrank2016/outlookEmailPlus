# PRD-00003｜Legacy 代码拆分到 Controllers 层

**文档编号：** PRD-00003
**创建日期：** 2026-02-24
**优先级：** P0（架构重构）
**状态：** 待评审

---

## 1. 需求背景

### 1.1 当前问题

- `outlook_web/legacy.py` 文件达到 **5757 行**，包含所有路由处理逻辑
- 职责混乱：路由处理 + 数据访问 + 业务逻辑 + 工具函数混在一起
- 难以维护、测试和扩展
- 虽然已有 services/ 和 repositories/ 层，但仍需通过 legacy.py 过渡

### 1.2 业务价值

- 提升代码可维护性，降低后续开发成本
- 清晰的分层架构，便于团队协作
- 提高代码复用性和测试覆盖率
- 为后续功能扩展打下良好基础

---

## 2. 目标架构

### 2.1 当前架构

```
routes/ (Blueprint) → legacy.py (5757行) → services/ → repositories/
```

### 2.2 目标架构

```
routes/       → 路由注册（URL 映射）
    ↓
controllers/  → 请求处理（参数解析、鉴权、响应封装）
    ↓
services/     → 业务逻辑（已有）
    ↓
repositories/ → 数据访问（已有）
```

### 2.3 各层职责

| 层级 | 职责 | 示例 |
|------|------|------|
| **routes/** | URL 到函数的映射 | `/api/groups` → `groups_controller.api_get_groups` |
| **controllers/** | 请求处理、参数验证、鉴权、响应封装 | 解析 request，调用 service，返回 jsonify |
| **services/** | 业务逻辑、多后端回退 | Graph API 失败回退到 IMAP |
| **repositories/** | 数据库操作、SQL 查询 | 查询账号、插入日志 |

---

## 3. 功能模块划分

### 3.1 模块清单

Legacy.py 包含 11 个功能模块，共 54 个 API 路由：

| 模块 | 路由数量 | 主要功能 |
|------|---------|---------|
| **accounts** | 20 | 账号管理、刷新、导出 |
| **emails** | 4 | 邮件查看、删除、验证码提取 |
| **groups** | 6 | 分组管理、导出 |
| **tags** | 4 | 标签管理 |
| **temp_emails** | 3 | 临时邮箱管理 |
| **oauth** | 2 | OAuth 授权 |
| **settings** | 3 | 系统设置 |
| **scheduler** | 1 | 定时任务状态 |
| **system** | 3 | 健康检查、诊断 |
| **audit** | 1 | 审计日志 |
| **pages** | 3 | 登录、首页 |

### 3.2 迁移优先级

按照**复杂度从低到高、依赖从少到多**的原则分 3 个阶段：

**阶段 1：基础模块（低复杂度，无依赖）**
- groups, tags, settings, system, audit, pages
- 特点：逻辑简单，适合建立迁移模板

**阶段 2：独立功能模块**
- temp_emails, oauth, scheduler
- 特点：功能独立，依赖较少

**阶段 3：核心复杂模块**
- emails, accounts
- 特点：逻辑复杂，依赖多，最后处理

---

## 4. 核心需求

### 4.1 功能需求

**FR-1：创建 Controllers 层**
- 在 `outlook_web/` 下创建 `controllers/` 目录
- 为每个模块创建对应的 controller 文件
- 从 legacy.py 提取路由处理函数到 controllers/

**FR-2：更新 Routes 层**
- 移除 routes/ 中的 `impl` 参数
- 直接导入 controllers 模块
- 保持 URL 和响应格式不变

**FR-3：清理 Legacy.py**
- 所有路由处理函数迁移完成后删除 legacy.py
- 工具函数迁移到 `utils/`
- 中间件迁移到 `middleware/` 或保留在原位置

### 4.2 非功能需求

**NFR-1：兼容性**
- 所有 API 的 URL、请求参数、响应格式保持不变
- 错误处理和 trace_id 机制保持不变
- 前端无需任何修改

**NFR-2：测试覆盖**
- 所有迁移的模块必须通过现有测试
- 不降低测试覆盖率

**NFR-3：性能**
- 响应时间不超过迁移前的 110%
- 无明显性能下降

---

## 5. 实施计划

### 5.1 分阶段交付

| 阶段 | 模块 | 交付物 | 验收标准 |
|------|------|--------|---------|
| **阶段 1** | groups, tags, settings, system, audit, pages | 6 个 controller 文件 | 所有测试通过，手动验证功能正常 |
| **阶段 2** | temp_emails, oauth, scheduler | 3 个 controller 文件 | 所有测试通过，手动验证功能正常 |
| **阶段 3** | emails, accounts | 2 个 controller 文件 | 所有测试通过，手动验证功能正常 |
| **阶段 4** | 清理 legacy.py | 删除 legacy.py，更新文档 | 应用正常运行，文档更新完成 |

### 5.2 时间估算

- 阶段 1：2-3 天
- 阶段 2：1-2 天
- 阶段 3：3-4 天
- 阶段 4：1 天
- **总计：7-10 天**

---

## 6. 验收标准

### 6.1 功能验收

- [ ] 所有 54 个 API 路由都已迁移到 controllers/
- [ ] legacy.py 已删除
- [ ] 所有功能手动测试通过
- [ ] 前端功能正常，无需修改

### 6.2 质量验收

- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 代码审查通过
- [ ] 性能测试通过（响应时间 < 迁移前 110%）

### 6.3 文档验收

- [ ] CLAUDE.md 已更新
- [ ] 开发者指南已更新
- [ ] 迁移文档已归档

---

## 7. 风险和依赖

### 7.1 风险

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| 路由映射错误 | 高 | 充分测试 + 分阶段迁移 |
| 参数解析错误 | 高 | 单元测试覆盖 |
| 依赖关系错误 | 中 | 先迁移无依赖模块 |
| 性能下降 | 中 | 性能测试 + 监控 |

### 7.2 依赖

- 依赖现有的 services/ 和 repositories/ 层
- 依赖现有的测试用例
- 无外部依赖

---

## 8. 成功指标

- 代码行数：legacy.py 从 5757 行降至 0 行
- 模块化：11 个独立的 controller 文件
- 测试覆盖率：保持或提升
- 响应时间：< 迁移前 110%
- Bug 数量：迁移后 1 周内无 P0/P1 Bug

---

## 9. 附录

### 9.1 Controller 示例

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
```

### 9.2 Routes 更新示例

```python
# outlook_web/routes/groups.py
from flask import Blueprint
from outlook_web.controllers import groups as groups_controller

def create_blueprint() -> Blueprint:
    bp = Blueprint("groups", __name__)
    bp.add_url_rule("/api/groups", view_func=groups_controller.api_get_groups, methods=["GET"])
    return bp
```

---

**文档版本：** v1.0
**最后更新：** 2026-02-24
**负责人：** 开发团队
