# BSHL Alpha Skill 快速开始

---

## 三种使用方式

### 方式 1：直接对话

```
用 BSHL Alpha Skill 分析 NVDA
```

### 方式 2：指定工作流

```
BSHL Alpha Skill，启动每日雷达
BSHL Alpha Skill，检查 COIN 的交易准备状态
BSHL Alpha Skill，复盘这笔交易
```

### 方式 3：生成完整卡片

```
用 BSHL Alpha Skill 为 MSTR 生成完整分析卡
```

---

## 核心工作流

| 工作流 | 输入示例 | 输出 |
|--------|----------|------|
| 每日雷达 | 扫描 AI、Crypto 方向的机会 | 主题、标的、状态表格 |
| 深度分析 | 分析 NVDA | 完整分析卡 |
| 主题映射 | AI 电力主题里哪些股票值得研究 | 产业链拆解、公司映射 |
| 交易准备 | COIN 涨了 40% 还能追吗 | 交易准备状态、建议 |
| 风控检查 | 检查 MSTR 风控状态 | 风控决策 |
| 复盘 | 复盘之前的 COIN 交易 | 复盘卡、规则更新 |

---

## 输出状态

| 状态 | 含义 | 后续动作 |
|------|------|----------|
| Research Only | 值得研究，暂不交易 | 深入研究 |
| Watchlist | 进入观察池 | 定期检查 |
| Trade Ready | 具备交易准备 | 可进入执行准备 |
| Wait Pullback | 等回踩 | 等待回踩确认 |
| Avoid | 回避 | 不关注 |
| Veto | 风控否决 | 禁止交易 |

---

## 核心原则

1. **证据弱，不下判断** - 弱证据只能提出假设
2. **结构差，不进交易准备** - K线结构不好不交易
3. **风控否决，任何逻辑无效** - Risk Governor 最高权限
4. **没有复盘，系统不会进化** - 每次判断留下日志

---

## 安全声明

**本系统不做三件事**:
1. 不做人格模仿
2. 不直接给无条件买卖指令
3. 不默认自动下单

**所有交易决策需用户人工确认。**

---

## 目录结构

```
BSHL_Alpha_Skill/
├── SKILL.md              # 技能入口
├── README.md             # 完整架构
├── QUICKSTART.md         # 本文件
├── VERSION_ROADMAP.md     # 版本路线
├── constitution/         # 核心原则
├── workflows/            # 工作流
├── references/           # 参考规则
├── schemas/             # 数据定义
├── prompts/             # 提示词
├── examples/            # 示例
└── evals/              # 测试
```

---

*BSHL Alpha Skill v0.5*
*证据驱动 · 结构确认 · 风险优先 · 复盘进化*
