# GitHub Secrets 配置指南

为了在 GitHub Actions 中正确使用 `.env` 中的敏感信息，需要在仓库中配置 GitHub Secrets。

## 步骤

1. **进入仓库设置**
   - 访问 https://github.com/markqiu/red_blud_eyes/settings/secrets/actions
   - 或在仓库中点击 **Settings** → **Secrets and variables** → **Actions**

2. **添加以下 Secrets**

   点击 **New repository secret** 并添加：

   | Secret Name | Value | 来自本地 .env |
   |---|---|---|
   | `SILICONFLOW_API_KEY` | `sk-jgzqejjjhdftokijdcldttebtfcrngycrsrtnisuprgbtipg` | ✓ |
   | `SILICONFLOW_MODEL` | `deepseek-ai/DeepSeek-V3.2` | ✓ |
   | `SILICONFLOW_BASE_URL` | `https://api.siliconflow.cn/` | ✓ |
   | `OPENAI_CERTAINTY_THRESHOLD` | `0.95` | ✓ |
   | `RENDER_API_KEY` | `rnd_bZ1SIFGrmh7yGYuhOX8SWnKKNkpY` | ✓ |
   | `RENDER_DEPLOY_HOOK` | （Render 部署 webhook URL） | 可选 |

3. **验证配置**
   - 提交代码后，GitHub Actions 会自动使用这些 Secrets 生成 `.env`
   - 在 workflow 日志中，Secrets 的值会被屏蔽显示为 `***`

## 工作流程

1. **测试阶段** (`test`)
   - 从 Secrets 生成 `.env` 文件
   - 安装依赖
   - 运行测试

2. **构建阶段** (`build`)
   - 从 Secrets 生成 `.env` 文件
   - 构建依赖

3. **部署阶段** (`deploy`)
   - 如果配置了 `RENDER_DEPLOY_HOOK`，自动部署到 Render
   - 否则跳过部署

## 安全性

- `.env` 文件包含敏感信息，**不应该提交到版本控制**
- `.env` 已添加到 `.gitignore`，不会被提交
- 每次 workflow 运行时，都会从 GitHub Secrets 重新生成 `.env`
- 本地开发使用本地 `.env`，CI/CD 使用 GitHub Secrets

## 本地开发

在本地开发时，使用本地的 `.env` 文件：
- 该文件已在 `.gitignore` 中，不会被提交
- 可以安全地存储本地凭证
