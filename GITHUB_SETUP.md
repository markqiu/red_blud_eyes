# GitHub 仓库设置指南

## 📋 前置条件

- GitHub 账户
- Git 已安装
- 项目已本地初始化（git init）

## 🚀 创建 GitHub 仓库

### 方式 1：使用 GitHub CLI（推荐）

```bash
# 安装 GitHub CLI
brew install gh

# 登录
gh auth login

# 在当前目录创建仓库
gh repo create red-blue-eyes --source=. --remote=origin --push

# 自动关联并推送代码
```

### 方式 2：使用 GitHub Web 界面

1. 访问 https://github.com/new
2. 填写仓库信息：
   - **Repository name**: `red-blue-eyes` 或自定义
   - **Description**: "Red/Blue Eyes Puzzle Verification System"
   - **Public/Private**: 选择（默认 Public）
   - **不** 初始化 README（我们已有）

3. 创建后，按照提示关联本地仓库：
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/red-blue-eyes.git
   git branch -M main
   git push -u origin main
   ```

## 🔐 配置 GitHub Secrets

用于 CI/CD 自动部署，在 Settings → Secrets and variables → Actions 中添加：

### 必需 Secrets

| Secret 名称 | 说明 | 获取方式 |
|-----------|------|---------|
| `APP_PASSWORD` | 应用访问密码 | 自定义强密码 |

### 可选 Secrets（云部署用）

```
RENDER_DEPLOY_HOOK    # Render 部署 webhook
RAILWAY_TOKEN         # Railway 个人访问令牌
RAILWAY_PROJECT_ID    # Railway 项目 ID
OPENAI_API_KEY        # OpenAI API 密钥
OPENAI_MODEL          # OpenAI 模型名称
SILICONFLOW_API_KEY   # 硅基流动 API 密钥
SILICONFLOW_MODEL     # 硅基流动模型名称
```

## 📤 首次推送

```bash
# 验证远程配置
git remote -v

# 推送所有分支
git push -u origin main

# 推送指定分支
git push origin main
```

## ✅ 验证仓库

1. 访问 GitHub 仓库主页
2. 检查文件是否完整：
   - ✅ src/ 源代码
   - ✅ web/ 前端资源
   - ✅ tests/ 测试代码
   - ✅ README.md
   - ✅ .github/workflows/deploy.yml

3. 检查 CI/CD 状态：
   - 点击 "Actions" 选项卡
   - 查看工作流运行状态

## 🔄 启用 CI/CD 工作流

### GitHub Actions 自动触发

工作流在以下情况自动运行：

- ✅ Push 到 `main` 或 `master` 分支
- ✅ Pull Request 创建时
- ⏱️ 可选：定时运行

### 手动触发

```bash
# 本地推送触发
git push origin main

# 在 GitHub Actions 页面手动触发
# Actions → Deploy to Cloud → Run workflow
```

## 🚀 部署平台集成

### Render 集成步骤

1. **获取 Deploy Hook**
   - Render 仪表板 → Service 设置
   - 找到 "Deploy Hook" 部分
   - 复制完整的 webhook URL

2. **添加到 GitHub Secrets**
   - Settings → Secrets → New repository secret
   - Name: `RENDER_DEPLOY_HOOK`
   - Value: 粘贴 webhook URL

3. **自动部署**
   ```bash
   git push origin main  # 自动触发 GitHub Actions
   # → Actions 运行测试
   # → Render 自动部署
   ```

### Railway 集成步骤

1. **获取 Personal Access Token**
   - Railway → Account → Tokens
   - 创建新 token

2. **保存到 GitHub Secrets**
   - `RAILWAY_TOKEN`: token 值
   - `RAILWAY_PROJECT_ID`: 项目 ID（Railway Dashboard 可找到）

3. **推送触发部署**
   ```bash
   git push origin main
   ```

## 📋 .gitignore 检查清单

确保以下文件被忽略：

```
✅ .env              # 环境变量和密钥
✅ __pycache__/      # Python 缓存
✅ .pytest_cache/    # 测试缓存
✅ .venv/            # 虚拟环境
✅ *.pyc             # 编译的 Python 文件
✅ .DS_Store         # macOS 文件
```

验证：
```bash
git check-ignore .env __pycache__/
# 若返回文件名，说明正确忽略
```

## 🔒 安全最佳实践

### DO ✅
- ✅ 使用强密码（16+ 字符）
- ✅ API 密钥存储在 Secrets，不提交
- ✅ 定期更新依赖
- ✅ 启用分支保护（main 分支）
- ✅ 要求 PR review

### DON'T ❌
- ❌ 提交 .env 或密钥文件
- ❌ 使用弱密码
- ❌ 在提交信息中包含敏感信息
- ❌ 禁用所有安全检查

## 📝 分支管理

### 推荐工作流

```
main (生产) ← pull request ← develop (开发)
                            ↑
                    feature/xxx (特性分支)
```

### 创建特性分支

```bash
# 创建并切换到特性分支
git checkout -b feature/password-protection

# 进行开发...

# 推送特性分支
git push -u origin feature/password-protection

# 在 GitHub 创建 Pull Request
# 等待审查和自动测试
# 合并到 develop，最后合并到 main
```

## 🔍 代码审查设置

### 启用分支保护

1. Settings → Branches
2. 添加规则：Branch name pattern = `main`
3. 启用：
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass
   - ✅ Include administrators

### PR 模板

创建 `.github/pull_request_template.md`：

```markdown
## 描述
简述此 PR 的目的和改动

## 类型
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Performance improvement

## 变更清单
- [ ] 更新了测试
- [ ] 更新了文档
- [ ] 本地测试通过

## 相关 Issues
Closes #123
```

## 📊 仓库统计

### 查看项目统计

- **Insights** 选项卡：代码频率、贡献者
- **Pulse** 选项卡：周活动概览
- **Network** 选项卡：分支和提交历史

## 🤝 协作设置

### 邀请协作者

1. Settings → Collaborators
2. 搜索用户名
3. 选择权限级别：
   - **Maintain**: 管理设置，非破坏性操作
   - **Write**: 推送、创建分支、合并 PR
   - **Read**: 仅查看（免费仓库默认）

### 团队管理

对于组织仓库，创建 Teams：

```bash
# 组织设置中创建团队
# 将成员添加到团队
# 给团队分配仓库权限
```

## 🎯 常用命令速查

```bash
# 查看远程配置
git remote -v

# 更改远程 URL（若 SSH vs HTTPS）
git remote set-url origin https://github.com/USER/REPO.git

# 检查分支
git branch -a

# 切换分支
git checkout develop

# 拉取最新
git pull origin main

# 查看提交历史
git log --oneline --graph --all

# 撤销最后提交（未推送）
git reset --soft HEAD~1
```

## ⚠️ 常见问题

### Q: 如何更改仓库名称？
A: Settings → Repository name → 更改并保存

### Q: 不小心推送了密钥怎么办？
A: 
```bash
# 1. 重生成密钥
# 2. 从历史记录中删除：
git filter-branch --force --index-filter "git rm -rf --cached .env" -- --all
git push --force-with-lease
# 3. 通知平台重新扫描
```

### Q: GitHub Actions 为什么没有运行？
A: 
- 检查 `.github/workflows/deploy.yml` 是否存在
- 确认是否有写入权限
- 查看 Actions 选项卡的日志

### Q: 如何删除仓库？
A: Settings → Danger Zone → Delete this repository → 按提示操作

## 📚 更多资源

- [GitHub 官方文档](https://docs.github.com)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Git 官方文档](https://git-scm.com/doc)
- [本项目部署指南](DEPLOYMENT.md)

## ✨ 下一步

1. ✅ 创建 GitHub 仓库
2. ✅ 推送代码
3. ✅ 配置 Secrets（密码、部署 hooks）
4. ✅ 验证 CI/CD 工作流
5. ✅ 部署到云平台（Render/Railway）

---

**完成设置后，每次 `git push` 都会自动运行测试和部署！**

