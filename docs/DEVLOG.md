# DEVLOG（发布记录）

## v1.1.1（2026-02-28）

### 新增功能
- GitHub Actions Docker 构建工作流支持推送到 Docker Hub（`guangshanshui/outlook-email-plus`），并在未配置凭据时自动跳过，避免 fork/缺失 secrets 场景构建失败。

### 修复
- README 同步更新镜像地址与仓库链接，避免用户拉取/访问到旧地址（GHCR/旧仓库）。

### 重要变更
- 容器镜像发布从 GitHub Container Registry（GHCR）切换为 Docker Hub；需要在仓库 Secrets 中配置 `DOCKERHUB_USERNAME` 与 `DOCKERHUB_TOKEN` 才会执行推送。

### 测试/验证
- `npm test`：布局系统 Jest 用例回归。
- `python -m unittest discover -s tests -v`：全量 Python 单测回归。
- `docker build .`：本地镜像构建通过（用于验证 Dockerfile 未回归）。

## v1.1.0（2026-02-27）

### 新增功能
- 新增“可调整布局系统”：支持面板拖拽调整宽度、折叠/展开指示器、布局状态持久化与版本迁移。
- 新增“恢复默认布局”入口与确认对话框，便于一键回到默认四栏布局。
- UI 导航栏展示应用版本号，便于排查问题与对齐发布版本。
- 新增布局系统测试工程（Jest）：覆盖拖拽/键盘调整、折叠/展开、状态保存/加载、窗口自适配等场景。

### 修复
- 修复窄屏下自动/手动折叠后指示器不可见、导致无法再展开的问题。
- 修复折叠后页面出现滚动条、指示器高度观感异常的问题。
- 修复“隐藏邮件列表”仅改 display 导致 Grid 仍占位的空白列问题（与布局系统联动）。

### 重要变更
- 前端布局从历史侧栏方案调整为 Grid + CSS 变量驱动的四栏式布局；折叠时通过 layout-width 变量将列宽置 0（保存宽度不丢失）。
- 新增 `layout-system-enabled` 标记类，用于与旧的窄屏侧栏样式隔离，避免样式冲突与交互回归。

### 测试/验证
- `npm test`：布局系统 Jest 覆盖单元/集成用例。
- `python -m unittest discover -s tests -v`：全量 Python 单测回归。
- 手工验证：宽屏/窄屏折叠与指示器可见性、折叠后无滚动条、重置布局可恢复默认状态。
