# ✅ 部署检查清单

使用此清单确保项目已准备好部署到生产环境。

## 🔍 代码质量检查

- [ ] 所有测试通过
  ```bash
  uv run pytest -q
  ```
  **预期**：37 passed

- [ ] 没有 Python 语法错误
  ```bash
  python -m py_compile src/*.py tests/*.py
  ```

- [ ] 代码符合风格规范（可选）
  ```bash
  # 如果使用 pylint/flake8
  uv run pylint src/ --disable=all --enable=E,F
  ```

- [ ] 导入语句清理
  ```bash
  # 检查未使用的导入
  grep -r "^import\|^from" src/ | wc -l
  ```

## 🔐 安全检查

- [ ] `.env` 文件已添加到 `.gitignore`
  ```bash
  cat .gitignore | grep .env
  ```

- [ ] 没有硬编码的密钥或密码
  ```bash
  grep -r "sk-\|secret\|password" src/ --ignore-case | head -5
  # 应该返回 0 行（除了明确的引用）
  ```

- [ ] 已设置 `APP_PASSWORD` 环境变量
  ```bash
  # 本地测试
  echo $APP_PASSWORD  # 应该显示密码
  
  # GitHub Secrets 已配置
  # 检查: Settings → Secrets and variables → Actions
  ```

- [ ] 没有提交敏感文件
  ```bash
  git log --oneline --all | head -10
  # 查看是否误提交了 .env、密钥等
  ```

## 📦 依赖管理

- [ ] 依赖已同步
  ```bash
  uv sync
  ```

- [ ] `uv.lock` 文件已提交
  ```bash
  git ls-files | grep uv.lock
  ```

- [ ] `pyproject.toml` 配置正确
  ```bash
  cat pyproject.toml | head -20
  ```

- [ ] 没有过期或不安全的依赖
  ```bash
  # 检查依赖列表
  uv pip list | wc -l
  ```

## 🌐 Web 应用检查

- [ ] 前端资源完整
  ```bash
  ls -la web/
  # 应该包含: index.html, script.js
  ```

- [ ] HTML 有效性
  ```bash
  # 检查语法（可选）
  # 或在浏览器中打开检查
  ```

- [ ] 密码验证功能正常
  ```bash
  # 本地测试
  curl -X POST http://localhost:8000/api/verify_password \
    -H "Content-Type: application/json" \
    -d '{"password":"redblue"}'
  # 预期返回: {"ok": true, "valid": true}
  ```

- [ ] 所有 API 端点可访问
  ```bash
  # 测试健康检查
  curl http://localhost:8000/api/health
  ```

## 📝 文档检查

- [ ] README.md 完整
  - [ ] 包含项目描述
  - [ ] 包含快速开始步骤
  - [ ] 包含故障排查
  - [ ] 包含许可证信息

- [ ] DEPLOYMENT.md 完整
  - [ ] 多个平台的部署步骤
  - [ ] 环境变量配置
  - [ ] 成本估算
  - [ ] 故障排查

- [ ] GITHUB_SETUP.md 完整
  - [ ] 仓库创建步骤
  - [ ] Secrets 配置说明
  - [ ] 安全最佳实践

- [ ] QUICK_REFERENCE.md 完整
  - [ ] 常用命令
  - [ ] API 快速调用示例

## 🔧 配置文件检查

- [ ] `.gitignore` 配置正确
  ```bash
  cat .gitignore
  # 应该包含: .env, __pycache__, .pytest_cache, .venv
  ```

- [ ] `.github/workflows/deploy.yml` 存在
  ```bash
  ls -la .github/workflows/
  ```

- [ ] `Procfile` 正确配置
  ```bash
  cat Procfile
  # 预期: web: uv run python -m src.web_server
  ```

- [ ] `runtime.txt` 指定 Python 版本
  ```bash
  cat runtime.txt
  # 预期: python-3.11.x 或更新
  ```

- [ ] `render.yaml` 存在
  ```bash
  ls -la render.yaml
  ```

## 🚀 部署前测试

### 本地完整测试

```bash
# 1. 清理环境
rm -rf .venv .pytest_cache __pycache__

# 2. 安装依赖
uv sync

# 3. 运行所有测试
uv run pytest -v

# 4. 启动服务器
uv run python -m src.web_server &

# 5. 测试 Web 访问
sleep 2
curl -s http://localhost:8000/api/health | jq .

# 6. 测试密码
curl -s -X POST http://localhost:8000/api/verify_password \
  -H "Content-Type: application/json" \
  -d '{"password":"redblue"}' | jq .

# 7. 停止服务器
pkill -f "python -m src.web_server"
```

### 预期结果

- ✅ 所有 37 个测试通过
- ✅ 服务器正常启动
- ✅ API 端点响应 200
- ✅ 密码验证返回 `"valid": true`

## 📤 Git 准备

- [ ] 所有更改已提交
  ```bash
  git status
  # 应该显示: nothing to commit, working tree clean
  ```

- [ ] 分支已推送到远程
  ```bash
  git push origin main
  # 查看 GitHub 确认推送成功
  ```

- [ ] Git 历史清晰
  ```bash
  git log --oneline | head -10
  # 提交信息应该清晰描述性
  ```

- [ ] .gitignore 规则正确
  ```bash
  # 验证敏感文件未追踪
  git check-ignore .env .venv __pycache__
  ```

## ☁️ 云平台部署准备

### Render 部署

- [ ] GitHub 仓库已公开（或设置了访问权限）
- [ ] Render 账户已创建
- [ ] 部署 Hook 已获取并保存到 GitHub Secrets
  ```
  RENDER_DEPLOY_HOOK=https://api.render.com/deploy/srv-...
  ```

### Railway 部署

- [ ] Railway 账户已创建
- [ ] Personal Access Token 已生成并保存
  ```
  RAILWAY_TOKEN=...
  RAILWAY_PROJECT_ID=...
  ```

### Heroku 部署（备选）

- [ ] Heroku 账户已创建
- [ ] Heroku CLI 已安装
- [ ] API 密钥已配置

## 🔐 GitHub 配置

- [ ] Repository Secrets 已设置
  - [ ] `APP_PASSWORD`: 强密码 (16+ 字符)
  - [ ] `RENDER_DEPLOY_HOOK`: (如果使用 Render)
  - [ ] `RAILWAY_TOKEN`: (如果使用 Railway)
  - [ ] `OPENAI_API_KEY`: (可选)

- [ ] GitHub Actions 已启用
  ```bash
  # 访问: Settings → Actions → General
  # 确保 "Allow all actions and reusable workflows" 已启用
  ```

- [ ] 工作流文件有效
  ```bash
  # 检查: Actions → Deploy to Cloud
  # 应该显示一个可用的工作流
  ```

## 📊 监控和告警

- [ ] 错误日志收集已配置
  ```bash
  # 云平台应该提供日志查看
  # Render: render logs
  # Railway: railway logs
  ```

- [ ] 健康检查端点可用
  ```bash
  # GET /api/health 应该返回 200
  ```

- [ ] 性能监控已启用
  ```bash
  # 云平台仪表板应该显示性能指标
  ```

## ✨ 最终检查

- [ ] 本地测试 100% 通过
- [ ] 代码审查完成
- [ ] 文档已更新
- [ ] Secrets 已配置
- [ ] 部署脚本已验证
- [ ] 团队已通知（如适用）
- [ ] 备份计划已制定

## 🚀 部署步骤

### 快速部署（Render）

```bash
# 1. 最后确认
git status  # 应该是 clean
uv run pytest -q  # 所有测试通过

# 2. 推送到 GitHub
git push origin main

# 3. 监控 GitHub Actions
# 访问: https://github.com/YOUR_USER/red-blue-eyes/actions

# 4. 监控 Render 部署
# 访问: Render 仪表板 → Service → Deployments

# 5. 测试在线应用
# 访问: https://your-service.render.com
# 输入密码验证
```

## 📋 部署后检查

部署完成后，执行以下检查：

- [ ] 应用在云平台上正常运行
  ```bash
  # 访问应用 URL
  # 检查是否能加载页面
  ```

- [ ] 密码验证功能正常
  ```bash
  # 在浏览器中输入密码
  # 检查是否能访问应用
  ```

- [ ] API 端点可访问
  ```bash
  # 测试 /api/health
  # 测试 /api/state
  ```

- [ ] 日志记录正常
  ```bash
  # 查看云平台的日志输出
  # 应该看到请求日志
  ```

- [ ] 性能可接受
  ```bash
  # 测试初始化村庄、推进日期等操作
  # 响应时间应该 < 500ms
  ```

## 🎉 完成！

如果所有检查都通过，项目已成功部署！

### 后续维护任务

- 每周检查错误日志
- 每月更新依赖
- 监控 API 配额使用情况（OpenAI）
- 定期备份数据库（如有）
- 监控服务成本

---

**最后检查日期**：_____________  
**检查者**：_____________  
**部署日期**：_____________  
**应用 URL**：_____________
