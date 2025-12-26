# 红蓝眼谜题可视化验证系统

## 概述

这是一个交互式验证系统，用于演示和验证经典的"红蓝眼谜题"（Logic Puzzle）。系统实现了：

1. **核心验证引擎**：基于归纳证明的推理逻辑
2. **可视化 Web UI**：实时展示每个村民的视角、推理过程和决策日志
3. **可配置推理策略**：支持完美推理、有限推理、OpenAI 集成等多种策略
4. **密码保护**：简单的访问控制机制

## 功能特性

- 🧩 **Dummy 村民**：遵循标准归纳推理规则
- 🧠 **OpenAI 村民**：通过 API 调用 LLM 模拟真实推理（可选）
- 📊 **实时日志**：展示每日决策过程和推理链条
- 🔐 **密码保护**：通过 `.env` 配置访问密码
- 🌍 **支持多种 LLM 服务**：OpenAI 和硅基流动（SiliconFlow）
- 🧪 **完整测试覆盖**：pytest 单元测试验证核心逻辑

## 快速开始

### 环境要求

- Python 3.8+
- `uv` 包管理器（[安装指南](https://docs.astral.sh/uv/)）

### 本地运行

1. **克隆仓库并安装依赖**
   ```bash
   git clone <repository-url>
   cd red_blud_eyes
   uv sync
   ```

2. **配置密码（可选）**
   ```bash
   # 在项目根目录创建 .env 文件
   echo "APP_PASSWORD=your_secret_password" > .env
   ```
   默认密码为 `redblue`

3. **启动服务器**
   ```bash
   uv run python -m src.web_server
   ```

4. **访问 Web 界面**
   在浏览器中打开 `http://localhost:8000`，输入密码进行验证

### 配置 OpenAI（可选）

如果需要使用 OpenAI 的 LLM 功能，编辑 `.env` 文件：

```bash
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4
```

或使用硅基流动：

```bash
SILICONFLOW_API_KEY=sk-xxx
SILICONFLOW_MODEL=deepseek-v3
```

## 运行测试

```bash
# 运行所有测试
uv run pytest -v

# 仅运行推理逻辑测试
uv run pytest tests/test_reasoning.py -v
```

## 项目结构

```
src/
├── puzzle.py           # 村庄和村民的核心数据结构
├── reasoning.py        # 推理策略实现（完美推理、OpenAI 等）
├── simulation.py       # 村庄仿真引擎
├── knowledge.py        # 知识和认知模型
├── proof.py            # 归纳证明逻辑
├── induction_proof.py  # 更高级的证明工具
├── env.py              # 环境变量加载
└── web_server.py       # HTTP 服务器和 API 端点

web/
├── index.html          # Web UI 主页
└── script.js           # 前端交互逻辑

tests/
├── test_puzzle.py      # 村庄逻辑单测
└── test_reasoning.py   # 推理策略单测
```

## API 端点

| 端点 | 方法 | 功能 |
|-----|-----|-----|
| `/api/state` | GET | 获取当前村庄状态 |
| `/api/verify_password` | POST | 验证访问密码 |
| `/api/init` | POST | 初始化村庄（指定红蓝眼睛数量） |
| `/api/announce` | POST | 游客宣布"至少有一个红眼睛" |
| `/api/next` | POST | 模拟下一天 |
| `/api/run_all` | POST | 运行到谜题完成 |
| `/api/reset` | POST | 重置系统状态 |

## 部署

### 云平台部署

本项目支持多种云平台部署：

- **Vercel**：无需配置，自动部署 Python 支持
- **Heroku**：需要 Procfile 配置
- **Railway**：推荐选项，直接支持 Python
- **Render**：需要 Web Service 配置

详见 `.github/workflows/deploy.yml` 自动部署配置。

## 故障排查

### 服务器无法启动
- 检查端口 8000 是否被占用：`lsof -i :8000`
- 确保已安装 uv：`uv --version`

### 密码验证失败
- 检查 `.env` 文件中的 `APP_PASSWORD` 设置
- 浏览器缓存问题：清空 SessionStorage 后重试

### OpenAI 调用失败
- 验证 `OPENAI_API_KEY` 和 `OPENAI_MODEL` 配置
- 检查网络连接和 API 配额
- 查看服务器日志获取详细错误信息

## 许可证

MIT License

## 作者

@qiucheng
