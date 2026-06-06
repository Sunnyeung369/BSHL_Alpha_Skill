# Contributing to BSHL Alpha Skill

感谢您对 BSHL Alpha Skill 的关注！我们欢迎各种形式的贡献。

---

## 贡献类型

### 1. Bug 报告

发现问题时，请提供：
- 问题描述
- 复现步骤
- 预期行为 vs 实际行为
- 环境信息（使用的 AI 平台、模型等）

### 2. 功能建议

我们有明确的版本路线图（见 `VERSION_ROADMAP.md`），建议优先考虑路线图中的功能。

### 3. 文档改进

- 修正错误
- 补充示例
- 翻译文档
- 改进可读性

### 4. 规则与案例

- 添加新的参考规则
- 贡献回放案例
- 分享交易复盘
- 提供评分优化建议

### 5. 代码贡献

- 评分脚本优化
- 数据接口扩展
- Schema 更新
- Bug 修复

---

## 贡献流程

### 1. 提交 Issue

在提交 PR 之前，建议先提交 Issue 讨论您的想法。

### 2. Fork 项目

```bash
# 1. Fork 本仓库到您的账号
# 2. Clone 您的 fork
git clone https://github.com/YOUR_USERNAME/BSHL_Alpha_Skill.git
cd BSHL_Alpha_Skill
```

### 3. 创建分支

```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/your-bug-fix
```

### 4. 提交更改

```bash
git add .
git commit -m "描述您的更改"
```

### 5. 推送并创建 PR

```bash
git push origin feature/your-feature-name
# 然后在 GitHub 上创建 Pull Request
```

---

## 提交规范

### Commit 消息格式

```
类型(范围): 简短描述

详细描述（可选）

关闭的 Issue（可选）
```

### 类型标签

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

### 示例

```
feat(scoring): 添加仓位风险评分脚本

- 实现 single_position_size 评分
- 实现 sector_concentration 评分
- 实现 total_exposure 评分

Closes #123
```

---

## 代码规范

### Python 代码

- 遵循 PEP 8
- 添加类型注解
- 编写文档字符串
- 保持函数简短（< 50 行）

### Markdown 文档

- 使用清晰的标题层级
- 代码块指定语言
- 表格对齐
- 链接有效

---

## 测试

### 测试要求

- 新功能需要添加测试
- Bug 修复需要添加回归测试
- 确保所有测试通过

### 运行测试

```bash
# 评分脚本测试
python -m scoring.alpha_thesis_score
python -m scoring.market_pricing_score
python -m scoring.trade_readiness_score
python -m scoring.risk_governor_score
python -m scoring.position_risk_score

# 回放系统测试
python -m replay.case_library
python -m replay.replay_engine

# 数据接口测试
python -m data.market_data
python -m data.fundamental_data
python -m data.news_data
```

---

## 文档结构

贡献文档时，请遵循现有结构：

```
BSHL_Alpha_Skill/
├── constitution/     # 核心原则
├── workflows/        # 工作流
├── references/       # 参考规则
├── prompts/          # 提示词模板
├── scoring/          # 评分脚本
├── schemas/          # JSON Schema
├── examples/         # 示例
└── replay/           # 回放系统
```

---

## 审查标准

PR 将按以下标准审查：

1. **必要性**: 是否符合项目方向
2. **质量**: 代码/文档质量是否达标
3. **一致性**: 是否与现有风格一致
4. **文档**: 是否有相应的文档更新
5. **测试**: 是否有相应的测试

---

## 行为准则

### 我们的承诺

- 尊重不同观点
- 欢迎不同经验水平的贡献者
- 建设性反馈
- 关注解决问题而非指责个人

### 不可接受的行为

- 使用性化语言
- 人身攻击或侮辱
- 公开或私下骚扰
- 未经许可发布他人隐私信息

### 举报

联系项目维护者报告不当行为。

---

## 获取帮助

- 提交 Issue 寻求帮助
- 查看 `README.md` 了解项目
- 查看 `QUICKSTART.md` 快速开始
- 查看 `examples/` 目录学习示例

---

## 许可

贡献的内容将采用与项目相同的 MIT 许可证。

---

*感谢您的贡献！*
