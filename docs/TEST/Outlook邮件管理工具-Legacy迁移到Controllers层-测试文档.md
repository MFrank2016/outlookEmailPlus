# Outlook 邮件管理工具｜Legacy 迁移到 Controllers 层 测试文档

- 文档状态：草案
- 版本：V1.0
- 日期：2026-02-24
- 对齐 PRD：`docs/PRD/PRD-00003-Legacy代码拆分到Controllers层.md`
- 对齐 FD：`docs/FD/Outlook邮件管理工具-Legacy迁移到Controllers层FD.md`
- 对齐 TDD：`docs/TDD/Outlook邮件管理工具-Legacy迁移到Controllers层TDD.md`
- 对齐 TODO：`docs/TODO/Outlook邮件管理工具-Legacy迁移到Controllers层TODO.md`

---

## 1. 测试概述

### 1.1 测试目标

本测试文档旨在验证 Legacy 迁移到 Controllers 层的正确性、完整性和性能，确保：

1. **功能完整性**：
   - 所有 54 个 API 路由功能正常
   - 所有业务逻辑保持不变
   - 所有数据处理正确

2. **API 契约不变**：
   - URL 路径不变
   - HTTP 方法不变
   - 请求参数不变
   - 响应格式不变
   - 错误格式不变

3. **性能不下降**：
   - 响应时间 < 迁移前 110%
   - 内存使用无明显增加
   - 并发处理能力不下降

4. **代码质量提升**：
   - 代码结构清晰
   - 职责分离明确
   - 易于测试和维护

### 1.2 测试范围

**包含：**
- 单元测试（Controllers 层）
- 集成测试（完整请求-响应流程）
- 回归测试（所有现有功能）
- 契约测试（API 契约验证）
- 性能测试（响应时间、内存使用）
- 错误处理测试
- 边界情况测试

**不包含：**
- 安全渗透测试（不在本次迁移范围）
- 压力测试（不在本次迁移范围）
- 前端功能测试（前端无需修改）

### 1.3 测试环境

**后端环境：**
- Python 3.8+
- Flask 3.0+
- SQLite 3
- 测试框架：unittest
- Mock 工具：unittest.mock
- 覆盖率工具：coverage

**测试数据：**
- 测试数据库：`data/test_outlook_accounts.db`
- 测试账号：10 个
- 测试分组：3 个
- 测试标签：5 个
- 测试邮件：20 封

**测试工具：**
- unittest - Python 标准测试框架
- unittest.mock - Mock 工具
- Flask test client - 集成测试
- coverage - 测试覆盖率
- time - 性能测试
- tracemalloc - 内存测试

---

## 2. 测试策略

### 2.1 测试金字塔

```
        /\
       /  \      E2E 测试（少量）
      /    \     - 关键业务流程
     /------\
    /        \   集成测试（适量）
   /          \  - API 接口测试
  /------------\
 /              \ 单元测试（大量）
/________________\- Controllers 测试
                  - Services 测试
                  - Repositories 测试
```

**测试比例：**
- 单元测试：70%
- 集成测试：20%
- E2E 测试：10%

### 2.2 测试优先级

**P0（必须通过）：**
- 所有现有测试通过（回归测试）
- 所有 API 契约测试通过
- 核心功能集成测试通过

**P1（重要）：**
- Controllers 单元测试通过
- 性能测试通过
- 错误处理测试通过

**P2（可选）：**
- 测试覆盖率 > 80%
- 边界情况测试通过

### 2.3 测试方法

#### 2.3.1 单元测试

**目标：** 测试 Controllers 层的每个函数

**方法：**
- 使用 unittest.mock.patch Mock 依赖
- 测试正常场景
- 测试异常场景
- 测试边界场景

**示例：**
```python
@patch('outlook_web.controllers.groups.groups_repo')
@patch('outlook_web.controllers.groups.session')
def test_api_get_groups_success(self, mock_session, mock_repo):
    # Mock 登录状态
    mock_session.get.return_value = True

    # Mock repository 返回
    mock_repo.get_all_groups.return_value = [
        {'id': 1, 'name': '分组1'},
        {'id': 2, 'name': '分组2'}
    ]

    # 调用 controller
    response = groups_controller.api_get_groups()

    # 验证
    self.assertEqual(response.status_code, 200)
```

#### 2.3.2 集成测试

**目标：** 测试完整的请求-响应流程

**方法：**
- 使用 Flask test client
- 测试真实的数据库操作
- 测试完整的业务流程

**示例：**
```python
def test_groups_crud_integration(self):
    # 1. 创建分组
    response = self.client.post('/api/groups', json={'name': '测试分组'})
    self.assertEqual(response.status_code, 200)
    group_id = response.get_json()['id']

    # 2. 获取分组
    response = self.client.get(f'/api/groups/{group_id}')
    self.assertEqual(response.status_code, 200)

    # 3. 删除分组
    response = self.client.delete(f'/api/groups/{group_id}')
    self.assertEqual(response.status_code, 200)
```

#### 2.3.3 回归测试

**目标：** 确保所有现有功能正常

**方法：**
- 运行所有现有测试
- 手动测试关键功能
- 对比迁移前后的行为

**现有测试文件：**
- `tests/test_smoke_contract.py` - 烟雾测试和契约测试
- `tests/test_core_features.py` - 核心功能测试
- `tests/test_error_and_trace.py` - 错误处理测试
- `tests/test_distributed_lock.py` - 分布式锁测试
- `tests/test_masking_audit_and_import.py` - 数据脱敏测试

#### 2.3.4 契约测试

**目标：** 确保 API 契约不变

**方法：**
- 验证 URL 路径
- 验证 HTTP 方法
- 验证请求参数
- 验证响应格式
- 验证错误格式

**示例：**
```python
def test_api_contract_groups(self):
    # 验证响应格式
    response = self.client.get('/api/groups')
    data = response.get_json()

    self.assertIsInstance(data, list)
    if len(data) > 0:
        group = data[0]
        self.assertIn('id', group)
        self.assertIn('name', group)
```

#### 2.3.5 性能测试

**目标：** 确保性能不下降

**方法：**
- 测量响应时间
- 测量内存使用
- 对比迁移前后的性能

**示例：**
```python
def test_performance_groups(self):
    start = time.time()
    response = self.client.get('/api/groups')
    end = time.time()

    response_time = (end - start) * 1000  # 毫秒
    self.assertLess(response_time, 100)  # < 100ms
```

---

## 3. 测试用例

### 3.1 阶段 1：基础模块测试

#### 3.1.1 Groups 模块测试

**测试文件：** `tests/test_controllers_groups.py`

##### TC-G-001：获取所有分组（正常场景）

**测试目标：** 验证获取所有分组功能正常

**前置条件：**
- 用户已登录
- 数据库中有 2 个分组

**测试步骤：**
1. 发送 GET 请求到 `/api/groups`
2. 验证响应状态码为 200
3. 验证响应数据为列表
4. 验证列表包含 2 个分组
5. 验证每个分组包含 id 和 name 字段

**预期结果：**
```json
[
    {"id": 1, "name": "分组1"},
    {"id": 2, "name": "分组2"}
]
```

##### TC-G-002：获取所有分组（未登录）

**测试目标：** 验证未登录时无法访问

**前置条件：**
- 用户未登录

**测试步骤：**
1. 发送 GET 请求到 `/api/groups`
2. 验证响应状态码为 302（重定向到登录页）

**预期结果：**
- 重定向到 `/login`

##### TC-G-003：添加分组（正常场景）

**测试目标：** 验证添加分组功能正常

**前置条件：**
- 用户已登录

**测试步骤：**
1. 发送 POST 请求到 `/api/groups`
2. 请求体：`{"name": "新分组"}`
3. 验证响应状态码为 200
4. 验证响应包含 id 和 name
5. 验证数据库中已创建该分组

**预期结果：**
```json
{"id": 3, "name": "新分组"}
```

##### TC-G-004：添加分组（名称为空）

**测试目标：** 验证参数验证正常

**前置条件：**
- 用户已登录

**测试步骤：**
1. 发送 POST 请求到 `/api/groups`
2. 请求体：`{"name": ""}`
3. 验证响应状态码为 400
4. 验证错误信息为"分组名称不能为空"

**预期结果：**
```json
{
    "success": false,
    "error": "分组名称不能为空",
    "trace_id": "xxx-xxx-xxx"
}
```

##### TC-G-005：更新分组（正常场景）

**测试目标：** 验证更新分组功能正常

**前置条件：**
- 用户已登录
- 数据库中有 id 为 1 的分组

**测试步骤：**
1. 发送 PUT 请求到 `/api/groups/1`
2. 请求体：`{"name": "更新后的分组"}`
3. 验证响应状态码为 200
4. 验证响应包含更新后的数据
5. 验证数据库中已更新

**预期结果：**
```json
{"id": 1, "name": "更新后的分组"}
```

##### TC-G-006：删除分组（正常场景）

**测试目标：** 验证删除分组功能正常

**前置条件：**
- 用户已登录
- 数据库中有 id 为 1 的分组

**测试步骤：**
1. 发送 DELETE 请求到 `/api/groups/1`
2. 验证响应状态码为 200
3. 验证响应包含成功消息
4. 验证数据库中已删除

**预期结果：**
```json
{"message": "删除成功"}
```

##### TC-G-007：删除分组（分组不存在）

**测试目标：** 验证错误处理正常

**前置条件：**
- 用户已登录
- 数据库中没有 id 为 999 的分组

**测试步骤：**
1. 发送 DELETE 请求到 `/api/groups/999`
2. 验证响应状态码为 404
3. 验证错误信息为"分组不存在"

**预期结果：**
```json
{
    "success": false,
    "error": "分组不存在",
    "trace_id": "xxx-xxx-xxx"
}
```

#### 3.1.2 Tags 模块测试

**测试文件：** `tests/test_controllers_tags.py`

**测试用例：** 类似 Groups 模块，包括：
- TC-T-001：获取所有标签（正常场景）
- TC-T-002：获取所有标签（未登录）
- TC-T-003：添加标签（正常场景）
- TC-T-004：添加标签（名称为空）
- TC-T-005：删除标签（正常场景）
- TC-T-006：删除标签（标签不存在）
- TC-T-007：批量管理标签（正常场景）

#### 3.1.3 Settings 模块测试

**测试文件：** `tests/test_controllers_settings.py`

**测试用例：**
- TC-S-001：获取系统设置（正常场景）
- TC-S-002：更新系统设置（正常场景）
- TC-S-003：更新系统设置（参数验证）
- TC-S-004：验证 Cron 表达式（正常场景）
- TC-S-005：验证 Cron 表达式（格式错误）

#### 3.1.4 System 模块测试

**测试文件：** `tests/test_controllers_system.py`

**测试用例：**
- TC-SYS-001：健康检查（正常场景）
- TC-SYS-002：获取诊断信息（正常场景）
- TC-SYS-003：获取升级状态（正常场景）

#### 3.1.5 Audit 模块测试

**测试文件：** `tests/test_controllers_audit.py`

**测试用例：**
- TC-A-001：获取审计日志（正常场景）
- TC-A-002：获取审计日志（分页）
- TC-A-003：获取审计日志（过滤）

#### 3.1.6 Pages 模块测试

**测试文件：** `tests/test_controllers_pages.py`

**测试用例：**
- TC-P-001：登录页面（正常场景）
- TC-P-002：登录功能（正确密码）
- TC-P-003：登录功能（错误密码）
- TC-P-004：登出功能（正常场景）
- TC-P-005：首页（已登录）
- TC-P-006：首页（未登录，重定向）

---

### 3.2 阶段 2：独立功能模块测试

#### 3.2.1 Temp Emails 模块测试

**测试文件：** `tests/test_controllers_temp_emails.py`

**测试用例：**
- TC-TE-001：获取临时邮箱列表（正常场景）
- TC-TE-002：生成临时邮箱（正常场景）
- TC-TE-003：获取临时邮箱消息（正常场景）
- TC-TE-004：获取临时邮箱消息（邮箱不存在）

#### 3.2.2 OAuth 模块测试

**测试文件：** `tests/test_controllers_oauth.py`

**测试用例：**
- TC-O-001：获取 OAuth 授权 URL（正常场景）
- TC-O-002：交换 OAuth Token（正常场景）
- TC-O-003：交换 OAuth Token（code 无效）

#### 3.2.3 Scheduler 模块测试

**测试文件：** `tests/test_controllers_scheduler.py`

**测试用例：**
- TC-SCH-001：获取调度器状态（正常场景）
- TC-SCH-002：获取调度器状态（调度器未启动）

---

### 3.3 阶段 3：核心复杂模块测试

#### 3.3.1 Emails 模块测试

**测试文件：** `tests/test_controllers_emails.py`

**测试用例：**
- TC-E-001：获取邮件列表（Graph API 成功）
- TC-E-002：获取邮件列表（IMAP 回退）
- TC-E-003：获取邮件列表（账号不存在）
- TC-E-004：获取邮件详情（正常场景）
- TC-E-005：删除邮件（正常场景）
- TC-E-006：提取验证码（正常场景）
- TC-E-007：提取验证码（未找到验证信息）

#### 3.3.2 Accounts 模块测试

**测试文件：** `tests/test_controllers_accounts.py`

**测试用例（基础 CRUD）：**
- TC-AC-001：获取账号列表（正常场景）
- TC-AC-002：获取账号列表（按分组过滤）
- TC-AC-003：获取账号列表（数据脱敏验证）
- TC-AC-004：获取单个账号（ TC-AC-005：添加账号（正常场景）
- TC-AC-006：添加账号（参数验证）
- TC-AC-007：更新账号（正常场景）
- TC-AC-008：删除账号（正常场景）

**测试用例（批量操作）：**
- TC-AC-009：按邮箱删除账号（正常场景）
- TC-AC-010：批量删除账号（正常场景）
- TC-AC-011：批量更新分组（正常场景）
- TC-AC-012：搜索账号（正常场景）

**测试用例（导出功能）：**
- TC-AC-013：导出所有账号（正常场景）
- TC-AC-014：导出选中账号（正常场景）
- TC-AC-015：生成导出验证 Token（正常场景）
- TC-AC-016：导出验证流程（完整流程）

**测试用例（Token 刷新）：**
- TC-AC-017：刷新单个账号（正常场景）
- TC-AC-018：刷新所有账号（正常场景）
- TC-AC-019：重试刷新账号（正常场景）
- TC-AC-020：刷新失败账号（正常场景）
- TC-AC-021：触发定时刷新（正常场景）
- TC-AC-022：获取刷新日志（正常场景）
- TC-AC-023：获取账号刷新日志（正常场景）
- TC-AC-024：获取刷新统计（正常场景）

---

（文档未完，待续...）
