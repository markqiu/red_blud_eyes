# 部署指南

本文档说明如何将项目部署到云平台。

## 快速选择

| 平台 | 难度 | 成本 | 推荐 |
|-----|-----|------|------|
| **Render** | ⭐ 简单 | 免费/付费 | ✅ 推荐 |
| **Railway** | ⭐⭐ 中等 | 免费/付费 | ✅ 不错 |
| **Heroku** | ⭐⭐ 中等 | 仅付费 | ⚠️ 老旧 |
| **AWS** | ⭐⭐⭐ 复杂 | 按量付费 | 企业级 |
| **自建** | ⭐⭐⭐⭐ 复杂 | 自行负担 | 完全控制 |

## 1. 使用 Render 部署（推荐）

### 步骤

1. **准备 GitHub 仓库**
   ```bash
   git push origin main
   ```

2. **登录 Render**
   - 访问 https://render.com
   - 使用 GitHub 账户登录

3. **创建 Web Service**
   - 点击 "New +" → "Web Service"
   - 连接你的 GitHub 仓库
   - 选择此项目

4. **配置环境变量**
   - Build Command: `uv sync`
   - Start Command: `uv run python -m src.web_server`
   - 添加环境变量：
     ```
     APP_PASSWORD=your_secret_password
     OPENAI_API_KEY=sk-xxx (可选)
     OPENAI_MODEL=gpt-4 (可选)
     ```

5. **部署**
   - 点击 "Create Web Service"
   - 等待部署完成（通常 3-5 分钟）

### 成本

- **免费计划**：部署 15 分钟后自动休眠
- **付费计划**：$7/月起，无休眠

## 2. 使用 Railway 部署

### 步骤

1. **安装 Railway CLI**
   ```bash
   npm i -g @railway/cli
   ```

2. **登录并初始化项目**
   ```bash
   railway login
   railway init
   ```

3. **配置 railway.json**
   ```json
   {
     "name": "red-blue-eyes",
     "buildCommand": "uv sync",
     "startCommand": "uv run python -m src.web_server",
     "env": {
       "APP_PASSWORD": "your_secret_password",
       "OPENAI_API_KEY": "",
       "OPENAI_MODEL": "gpt-4"
     }
   }
   ```

4. **部署**
   ```bash
   railway deploy
   ```

### 成本

- **免费计划**：$5/月免费额度，超出按量计费
- **支持多个服务**：数据库、缓存等

## 3. 使用 Heroku 部署

### 步骤

1. **安装 Heroku CLI**
   ```bash
   brew tap heroku/brew && brew install heroku
   ```

2. **登录**
   ```bash
   heroku login
   ```

3. **创建应用**
   ```bash
   heroku create your-app-name
   ```

4. **设置环境变量**
   ```bash
   heroku config:set APP_PASSWORD=your_secret_password
   heroku config:set OPENAI_API_KEY=sk-xxx
   ```

5. **部署**
   ```bash
   git push heroku main
   ```

### 注意

- Heroku 已停止免费计划（2022 年起）
- 最低成本 $5/月
- 需要信用卡认证

## 4. GitHub Actions 自动部署

本项目配置了 GitHub Actions 工作流，每次推送到 `main` 分支时自动：

1. 运行测试
2. 构建项目
3. 部署到配置的平台

### 启用自动部署

1. **添加仓库 Secrets**
   - 进入 GitHub 仓库 → Settings → Secrets and variables → Actions
   - 添加以下 secrets：
     - `RENDER_DEPLOY_HOOK`：Render 部署 webhook
     - `RAILWAY_TOKEN`：Railway 认证令牌
     - `APP_PASSWORD`：应用密码
     - `OPENAI_API_KEY`：OpenAI API 密钥（可选）

2. **获取 Render 部署 Hook**
   - Render 控制面板 → Service 设置 → Deploy Hook
   - 复制完整的 webhook URL

3. **设置自动部署**
   ```bash
   git add .
   git commit -m "Enable CI/CD"
   git push origin main
   ```

## 5. 环境变量配置

所有平台都需要设置以下环境变量：

| 变量 | 说明 | 示例值 |
|------|------|--------|
| `APP_PASSWORD` | 访问密码 | `redblue` |
| `OPENAI_API_KEY` | OpenAI API 密钥（可选） | `sk-...` |
| `OPENAI_MODEL` | OpenAI 模型名称 | `gpt-4` |
| `SILICONFLOW_API_KEY` | 硅基流动密钥（可选） | `sk-...` |
| `SILICONFLOW_MODEL` | 硅基流动模型 | `deepseek-v3` |
| `PORT` | 服务监听端口 | `8000` |

## 6. 自定义域名

### Render

1. Settings → Custom Domain
2. 输入你的域名（如 puzzle.example.com）
3. 添加 CNAME 记录到你的 DNS 提供商

### Railway

1. 项目设置 → Custom Domain
2. 关联 GitHub 域名或自定义域

### Heroku

1. Settings → Domains
2. 添加你的自定义域名

## 7. 监控和日志

### 实时日志

```bash
# Render
render logs --service red-blue-eyes

# Railway
railway logs

# Heroku
heroku logs --tail
```

### 性能监控

- **Render**：Dashboard → Metrics
- **Railway**：Project → Monitoring
- **Heroku**：Metrics → Dyno

## 8. 故障排查

### 服务无法启动

1. 检查日志中的错误信息
2. 确认环境变量正确设置
3. 验证 Python 版本（需要 3.8+）

### 依赖问题

如果 `uv` 安装失败，平台需要：

```bash
# 使用 pip 代替 (备选方案)
pip install -r requirements.txt
python -m src.web_server
```

### 端口配置

确保应用监听正确的端口：

```python
# src/web_server.py
PORT = int(os.getenv('PORT', '8000'))
```

## 9. 安全建议

1. ✅ 使用强密码：`APP_PASSWORD` 应为 16+ 字符
2. ✅ 保护 API 密钥：使用仓库 Secrets，不要提交到代码
3. ✅ 定期更新依赖：监控安全公告
4. ✅ 启用 HTTPS：所有云平台默认支持
5. ✅ 添加速率限制：考虑使用 Cloudflare 等 CDN

## 10. 成本估算

| 平台 | 免费额度 | 常规月成本 |
|------|---------|----------|
| Render | 15min/月 | $7-20 |
| Railway | $5 免费额度 | $0-20（超额按量） |
| Heroku | 无 | $5-50+ |
| AWS | 有限 | $5-50+ |

## 帮助和支持

- 📚 Render 文档：https://render.com/docs
- 📚 Railway 文档：https://docs.railway.app
- 💬 GitHub Issues：提交问题和建议
- 📧 邮件支持：各平台提供官方支持

---

**快速部署**：选择 Render，按照第 1 部分操作，5 分钟内上线！
