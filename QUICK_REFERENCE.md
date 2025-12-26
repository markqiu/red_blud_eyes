# 快速参考手册

## 🎯 本地开发

### 初次设置
```bash
git clone <repo-url> && cd red_blud_eyes
uv sync
echo "APP_PASSWORD=your_password" > .env
uv run python -m src.web_server
# 打开 http://localhost:8000
```

### 日常命令

| 操作 | 命令 |
|-----|-----|
| 启动服务 | `uv run python -m src.web_server` |
| 运行测试 | `uv run pytest -v` |
| 快速测试 | `uv run pytest -q` |
| 安装新包 | `uv add package_name` |
| 清理缓存 | `rm -rf .pytest_cache __pycache__` |

## 🔐 密码管理

### 设置密码
```bash
# 在 .env 中
APP_PASSWORD=your_secure_password

# 或环境变量
export APP_PASSWORD=your_secure_password
```

### 默认密码
- **默认**：`redblue`
- **更改**：编辑 `.env` 或设置环境变量

## 📝 API 快速调用

### 验证密码
```bash
curl -X POST http://localhost:8000/api/verify_password \
  -H "Content-Type: application/json" \
  -d '{"password":"redblue"}'
```

### 初始化村庄
```bash
curl -X POST http://localhost:8000/api/init \
  -H "Content-Type: application/json" \
  -d '{"numRed":2,"numBlue":2,"villagerMode":"mixed_ends"}'
```

### 获取状态
```bash
curl http://localhost:8000/api/state
```

## 🧪 测试命令速查

```bash
# 所有测试 + 详细输出
uv run pytest -v

# 仅运行特定测试
uv run pytest tests/test_reasoning.py::test_perfect_induction_decide_no_log -v

# 显示打印输出
uv run pytest -s

# 快速汇总
uv run pytest -q

# 覆盖率分析（需要 pytest-cov）
uv run pytest --cov=src
```

## 🌐 部署速查

### Render（推荐 5 分钟上线）
1. 推送到 GitHub
2. 访问 render.com
3. New Web Service
4. 连接仓库并设置环境变量
5. Deploy ✅

### Railway
```bash
railway login
railway init
railway deploy
```

### Heroku
```bash
heroku create app-name
heroku config:set APP_PASSWORD=xxx
git push heroku main
```

## 🔧 常用配置

### pyproject.toml 位置
```python
# 项目配置
[project]
name = "red-blue-eyes"
version = "1.0.0"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### 环境变量清单
```env
# 必需
APP_PASSWORD=your_password

# OpenAI（可选）
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# 硅基流动（可选）
SILICONFLOW_API_KEY=sk-...
SILICONFLOW_MODEL=deepseek-v3

# 服务器
PORT=8000
```

## 📊 查看日志

### 实时日志（开发）
```bash
uv run python -m src.web_server 2>&1 | tail -f
```

### 云平台日志

```bash
# Render
render logs --service red-blue-eyes --tail

# Railway
railway logs --tail

# Heroku
heroku logs --tail
```

## 🐛 常见错误解决

| 错误 | 原因 | 解决方案 |
|------|------|---------|
| `Address already in use` | 端口 8000 被占用 | `lsof -i :8000` + `kill -9 <PID>` |
| `ModuleNotFoundError` | 依赖未安装 | `uv sync` |
| `Password invalid` | 密码错误 | 检查 `.env` 文件 |
| `OpenAI 超时` | API 慢或网络差 | 查看日志，自动 fallback 处理 |
| `测试失败` | Python 版本不对 | 检查 `python --version`，需 3.8+ |

## 📦 依赖管理

### 查看已安装包
```bash
uv pip list
```

### 升级所有依赖
```bash
uv sync --upgrade
```

### 生成 requirements.txt
```bash
uv pip compile -o requirements.txt pyproject.toml
```

## 🚀 性能优化

### 启用缓存
```python
# 在 web_server.py 中已实现
# 使用 ThreadingHTTPServer + threading.Lock
```

### 监控响应时间
```bash
# API 请求日志包含耗时信息
[API] end /api/next (0.123s)
```

## 📱 前端调试

### 浏览器控制台
```javascript
// 检查认证状态
sessionStorage.getItem('authenticated')

// 手动清除认证（重新输入密码）
sessionStorage.removeItem('authenticated')

// 查看当前状态
window.state
```

### 网络监控（F12 → Network）
- 检查 API 响应时间
- 查看 websocket 连接（暂无，可扩展）
- 监控资源加载

## 🔄 版本管理

### 提交规范
```bash
git add .
git commit -m "type(scope): description"
# 示例：git commit -m "feat(api): add password verification"
```

### 语义版本
- `v1.0.0-alpha`：初期开发
- `v1.0.0-beta`：测试阶段
- `v1.0.0`：稳定发布

## 📚 文档链接

| 文档 | 链接 |
|-----|-----|
| 项目说明 | [README.md](README.md) |
| 部署指南 | [DEPLOYMENT.md](DEPLOYMENT.md) |
| 项目总结 | [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) |
| 此文件 | QUICK_REFERENCE.md |

## 💾 备份和恢复

### 备份本地开发环境
```bash
# 导出依赖
uv pip freeze > backup.txt

# 导出环境变量（不包括密钥）
env | grep -E "^(APP|OPENAI|SILICONFLOW)" > env.backup
```

### 恢复
```bash
# 重新安装依赖
uv sync

# 恢复环境变量
source env.backup
```

---

**版本**：1.0  
**最后更新**：2025-12-26

💡 **提示**：保存此文件为书签，方便快速查阅！
