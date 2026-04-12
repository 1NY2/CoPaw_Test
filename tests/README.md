# CoPaw 测试套件说明

## 📋 概述

本目录包含 CoPaw 项目的完整测试套件，从 v1.0.1 版本导入。测试分为两大类：

- **单元测试** (`tests/unit/`): 针对单个模块、类和函数的测试
- **集成测试** (`tests/integrated/`): 测试多个组件的交互

## 📁 测试结构

```
tests/
├── __init__.py
├── integrated/              # 集成测试
│   ├── test_app_startup.py  # 应用启动测试
│   └── test_version.py      # 版本验证测试
└── unit/                    # 单元测试
    ├── agents/              # Agent 相关测试
    │   └── tools/
    │       └── test_file_search.py
    ├── app/                 # 应用层测试
    │   ├── test_agents_ordering.py
    │   ├── test_agents_workspace_initialization.py
    │   └── test_chat_updates.py
    ├── channels/            # 渠道测试
    │   ├── test_onebot_channel.py
    │   └── test_qq_channel.py
    ├── cli/                 # CLI 命令测试
    │   ├── test_cli_shutdown.py
    │   ├── test_cli_update.py
    │   └── test_cli_version.py
    ├── local_models/        # 本地模型测试
    │   ├── test_download_manager.py
    │   ├── test_llamacpp_backend.py
    │   ├── test_local_model_manager.py
    │   └── test_model_manager.py
    ├── providers/           # 模型提供商测试
    │   ├── test_anthropic_provider.py
    │   ├── test_gemini_provider.py
    │   ├── test_kimi_provider.py
    │   ├── test_ollama_provider.py
    │   ├── test_openai_provider.py
    │   ├── test_openai_stream_toolcall_compat.py
    │   └── test_provider_manager.py
    ├── routers/             # API 路由测试
    │   └── test_settings.py
    ├── utils/               # 工具函数测试
    │   └── test_command_runner.py
    └── workspace/           # 工作区测试
        ├── test_agent_creation.py
        ├── test_agent_id.py
        ├── test_agent_model.py
        ├── test_cli_agent_id.py
        ├── test_prompt.py
        └── test_workspace.py
```

## 🚀 运行测试

### 前置条件

安装测试依赖：

```bash
pip install -e ".[dev]"
```

这将安装：
- pytest >= 8.3.5
- pytest-asyncio >= 0.23.0
- pytest-cov >= 6.2.1
- pre-commit >= 4.2.0

### 运行所有测试

```bash
pytest
```

### 运行特定测试目录

```bash
# 只运行单元测试
pytest tests/unit/

# 只运行集成测试
pytest tests/integrated/

# 运行特定模块的测试
pytest tests/unit/providers/
```

### 运行单个测试文件

```bash
pytest tests/unit/workspace/test_workspace.py -v
```

### 运行特定测试函数

```bash
pytest tests/unit/workspace/test_workspace.py::test_workspace_creation -v
```

### 带覆盖率报告的测试

```bash
pytest --cov=src/copaw --cov-report=html
```

覆盖率报告将生成在 `htmlcov/` 目录中。

### 跳过慢速测试

```bash
pytest -m "not slow"
```

### 详细输出模式

```bash
pytest -v          # 详细输出
pytest -vv         # 更详细的输出
pytest -s          # 显示 print 输出
```

## 📊 测试统计

- **总测试文件数**: 35 个
- **总代码行数**: ~9,410 行
- **覆盖模块**:
  - Agents (Agent 核心逻辑)
  - App (应用层)
  - Channels (消息渠道)
  - CLI (命令行接口)
  - Local Models (本地模型)
  - Providers (模型提供商)
  - Routers (API 路由)
  - Utils (工具函数)
  - Workspace (工作区管理)

## 🔧 测试配置

测试配置位于 `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
]
```

## 📝 编写新测试

### 测试命名规范

- 文件名: `test_<模块名>.py`
- 测试函数: `test_<功能>_<场景>`
- 使用描述性的测试名称

### 示例

```python
import pytest
from copaw.agents.memory.memory_manager import MemoryManager

@pytest.mark.asyncio
async def test_add_memory():
    """测试添加记忆功能"""
    manager = MemoryManager()
    result = await manager.add({"content": "test"})
    assert result.success is True
```

### 使用 Fixtures

在测试文件中定义或使用现有的 fixtures：

```python
@pytest.fixture
def temp_dir():
    """创建临时目录"""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)

def test_file_operation(temp_dir):
    """使用临时目录进行测试"""
    test_file = temp_dir / "test.txt"
    test_file.write_text("hello")
    assert test_file.exists()
```

## ⚠️ 注意事项

1. **异步测试**: 大多数测试是异步的，需要使用 `@pytest.mark.asyncio` 装饰器
2. **Mock 外部依赖**: 对于网络请求、文件系统等外部依赖，应使用 mock
3. **独立性**: 每个测试应该独立运行，不依赖其他测试的状态
4. **清理资源**: 使用 fixtures 确保测试后清理临时文件和资源

## 🐛 调试测试

### 使用 pdb 调试

```python
def test_something():
    import pdb; pdb.set_trace()  # 断点
    # ... 测试代码
```

或使用 pytest 内置调试：

```bash
pytest --pdb tests/unit/workspace/test_workspace.py::test_workspace_creation
```

### 查看测试日志

```bash
pytest -v --log-cli-level=DEBUG
```

## 🔄 CI/CD 集成

测试已配置为在 GitHub Actions 中自动运行。配置文件位于 `.github/workflows/`。

## 📚 相关资源

- [pytest 官方文档](https://docs.pytest.org/)
- [pytest-asyncio 文档](https://pytest-asyncio.readthedocs.io/)
- [CoPaw 贡献指南](../CONTRIBUTING.md)

## 🤝 贡献

欢迎提交新的测试用例和改进现有测试！请遵循以下步骤：

1. 确保测试通过: `pytest`
2. 检查代码风格: `pre-commit run --all-files`
3. 提交 PR 并描述测试覆盖的功能

---

**最后更新**: 2026-04-06  
**测试来源**: CoPaw v1.0.1
