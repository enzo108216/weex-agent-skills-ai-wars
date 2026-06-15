# WEEX Agent Skills AI Wars

[English](README.md)

本仓库是 WEEX agent skills 的 AI Wars 分发版本，包含三套面向合约的 skill：`$weex-trader-skill`、`$weex-analysis-skill` 和 `$weex-monitor-skill`。

这套分发仅面向 WEEX 真实合约交易，保留 saved profile、vault 本地密钥管理、运行前检查、WEEX host 白名单、订单风险预览、合约账户和合约订单访问、只读分析、PnL 监控、真实交易确认等正式版底座，并加入 AI Wars 日志上传能力。AI 发起的真实合约交易成功后，可自动上传对应的 AI 决策记录。

## 从这里开始

1. 推荐让 AI 工具安装 AI Wars skills：

```text
请从 https://github.com/weex-labs/weex-agent-skills-ai-wars 安装 WEEX AI Wars skills。
```

如果你想手动安装，运行：

```bash
npx skills add https://github.com/weex-labs/weex-agent-skills-ai-wars --all
```

2. 安装完成后，在 AI 工具里点名 skill：

```text
使用 $weex-trader-skill 查询 BTCUSDT 最新合约价格。
```

3. 如果要查看私有账户或执行交易相关操作，skill 会引导你设置已保存的 WEEX API profile。优先使用本地 profile manager 或其他本地密钥输入方式，不要把密钥直接粘贴到聊天里。

4. AI 驱动的真实合约下单需要通过 `--ai-log @file.json` 提供 AI 决策文件。skill 会先校验文件，再执行交易，并且只在主合约请求成功后上传日志。

## 三套 Skill

当 AI 工具需要 WEEX AI Wars 合约访问时，使用 [`weex-trader-skill`](skills/weex-trader-skill/README.md)。

适合：

- 查询公开合约行情
- 查看私有合约余额、仓位、订单和订单状态
- 设置并使用已保存的 API profile
- 采集合约交易历史，供后续复盘
- 在真实交易前预览订单风险
- 在明确确认后提交、平仓或撤销真实合约订单
- 为成功的 AI 驱动合约交易上传 AI Wars 决策日志

当 AI 工具需要分析已采集的 WEEX 合约 JSON 数据时，使用 [`weex-analysis-skill`](skills/weex-analysis-skill/README.md)。

适合：

- 复核合约敞口、集中度、杠杆和可用保证金
- 汇总合约成交、手续费和已实现盈亏
- 复盘合约订单与成交行为
- 基于标准化历史数据生成合约交易画像
- 分析 `weex-trader-skill` 采集到的订单风险或账户风险 JSON

当 AI 工具需要创建、确认、运行、查看或取消本地合约 PnL 监控任务时，使用 [`weex-monitor-skill`](skills/weex-monitor-skill/SKILL.md)。

这套 skill 只负责本地监控编排，账户读取和真实平仓执行都委托给 `weex-trader-skill`。价格条件平仓应通过 `weex-trader-skill` 使用 WEEX 官方条件单。

示例提示词：

| 场景 | 提示词 |
|---|---|
| 查询价格 | `使用 $weex-trader-skill 查询 BTCUSDT 最新合约价格。` |
| 查看账户 | `使用 $weex-trader-skill 查看我的 BTCUSDT 合约仓位和可用余额。` |
| 预览风险 | `使用 $weex-trader-skill 在开 BTCUSDT 多单前预览风险。` |
| 准备订单 | `使用 $weex-trader-skill 预览一笔 BTCUSDT 合约订单，并说明执行前需要的 AI 日志文件。` |
| 分析历史 | `使用 $weex-analysis-skill 分析这份合约 replay JSON，找出主要交易行为问题。` |
| 创建监控 | `使用 $weex-monitor-skill 创建 BTCUSDT 多仓 PnL 监控，触发后通过真实合约确认流程平仓。` |

## 从本地目录安装

如果你已经下载或 clone 了本仓库，并想从这个本地目录安装，运行：

```bash
python3 tools/install_local_skills.py --all --agent codex
```

Claude Code 请使用 `--agent claude-code`。本地安装工具会校验 `gh skill install` 当前支持的 agent；如果你的宿主不在支持列表里，请用 `--dir` 安装到该宿主期望的 skills 目录。

`weex-monitor-skill` 依赖 `weex-trader-skill` 完成账户读取和执行委托。仅安装 `weex-monitor-skill` 时，本地安装工具会自动包含 `weex-trader-skill`。

## 使用前请注意

- 真实下单、撤单或修改账户状态的操作会影响真实资产。确认前请核对账户、交易对、方向、数量、价格、订单类型、AI 决策文件和风险预览。
- 不要把 API key、API secret、passphrase、vault password 或临时密钥文件粘贴到聊天窗口、issue、公开日志或截图里。
- 优先使用 saved profile、本地 profile manager、`--prompt-secrets`、环境变量或 `--secrets-stdin-json` 等本地密钥输入方式。
- 为这个工作流使用最小权限 API key。如果凭证可能已经暴露，请立即撤销或轮换。
- `weex-analysis-skill` 的输出只用于复核和风险参考，不构成投资或交易建议。
- 不确定时，先让 AI 工具预览或解释，再要求它执行任何操作。

## 更多文档

- [`weex-trader-skill` README](skills/weex-trader-skill/README.md)：WEEX 合约访问、API profile、订单预览、AI Wars 日志上传和故障排查。
- [`weex-trader-skill` script operations](skills/weex-trader-skill/references/script-operations.md)：面向进阶用户的直接脚本用法。
- [`weex-analysis-skill` README](skills/weex-analysis-skill/README.md)：合约输入数据、分析示例、复盘审查和安全说明。
- [`weex-monitor-skill` SKILL.md](skills/weex-monitor-skill/SKILL.md)：PnL 监控 DSL、确认流程、dry-run runner 和真实执行边界。
