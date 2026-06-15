# WEEX Agent Skills AI Wars

[中文版本](README.zh-CN.md)

This repository is the AI Wars distribution of the WEEX agent skills. It ships three installable contract-focused skills: `$weex-trader-skill`, `$weex-analysis-skill`, and `$weex-monitor-skill`.

The distribution is scoped to WEEX real contract trading. It keeps the current agent-friendly WEEX base layer, including saved profiles, vault-backed secret handling, runtime preflight, host allowlists, order risk preview, contract account/order access, read-only analysis, local PnL monitoring, and explicit live confirmation. It also adds AI Wars log upload so successful AI-driven contract trades can upload their matching AI decision record.

## Start Here

1. Ask your AI tool to install the AI Wars skills:

```text
Install the WEEX AI Wars skills from https://github.com/weex-labs/weex-agent-skills-ai-wars.
```

If you prefer to install manually, run:

```bash
npx skills add https://github.com/weex-labs/weex-agent-skills-ai-wars --all
```

2. After installation, mention the skill you want to use in chat:

```text
Use $weex-trader-skill to check the latest BTCUSDT contract price.
```

3. For private account or trading tasks, set up a saved WEEX API profile when the skill asks you to. Use the local profile manager or another local secret-entry method instead of pasting secrets into chat.

4. For AI-driven real contract order actions, provide the AI decision file through `--ai-log @file.json`. The trader skill validates the file before execution and uploads it only after the main contract request succeeds.

## The Three Skills

### `weex-trader-skill`

Use [`weex-trader-skill`](skills/weex-trader-skill/README.md) when the AI tool needs WEEX AI Wars contract access.

Good for:

- checking public contract market data
- checking private contract balances, positions, orders, and order status
- setting up and using saved API profiles
- collecting normalized contract trading history for review
- previewing order risk before a real trade
- placing, closing, or cancelling real contract orders after explicit confirmation
- uploading AI Wars decision logs for successful AI-driven contract trades

### `weex-analysis-skill`

Use [`weex-analysis-skill`](skills/weex-analysis-skill/README.md) when the AI tool needs read-only review of collected WEEX contract data.

Good for:

- reviewing exposure, concentration, leverage, and free collateral
- summarizing filled contract trades, fees, and realized profit/loss
- reviewing contract replay behavior and trading patterns
- generating a contract trading profile from normalized history
- reviewing order-risk or account-risk JSON collected by `weex-trader-skill`

### `weex-monitor-skill`

Use [`weex-monitor-skill`](skills/weex-monitor-skill/SKILL.md) when the AI tool needs to create, confirm, evaluate, run, list, or cancel local PnL monitor tasks for WEEX contract positions.

This skill delegates account reads and real close execution to `weex-trader-skill`. For price-based conditional closes, use WEEX official conditional orders through `weex-trader-skill` instead of a local monitor task.

## Which Skill Should I Use?

| If you want to... | Use |
|---|---|
| check contract prices | `weex-trader-skill` |
| check private contract account, balance, order, or position data | `weex-trader-skill` |
| set up or use a saved WEEX API profile | `weex-trader-skill` |
| preview, place, cancel, or check a real contract order | `weex-trader-skill` |
| create or review a local PnL monitor for a contract position | `weex-monitor-skill` |
| create an exchange-native price conditional close | `weex-trader-skill` |
| analyze an existing WEEX contract JSON file or pasted JSON data | `weex-analysis-skill` |
| analyze live account history | collect data with `weex-trader-skill`, then analyze it with `weex-analysis-skill` |

## Install From A Local Copy

If you downloaded or cloned this repository and want to install from that local copy, run:

```bash
python3 tools/install_local_skills.py --all --agent codex
```

Use `--agent claude-code` for Claude Code. The local installer validates the agents supported by `gh skill install`; if your host is not in that list, install to its expected skills directory with `--dir`.

`weex-monitor-skill` depends on `weex-trader-skill` for live account reads and execution delegation. Installing only `weex-monitor-skill` from the local installer automatically includes `weex-trader-skill`.

## User Safety Notes

- Real order, cancel, close, or account-changing actions can affect real assets. Check the account, symbol, side, size, price, order type, AI decision file, and risk preview before you confirm any action.
- Do not paste API keys, API secrets, passphrases, vault passwords, or temporary secret files into chat, issue trackers, public logs, or screenshots.
- Prefer saved profiles, the local profile manager, `--prompt-secrets`, environment variables, or `--secrets-stdin-json` for local secret entry.
- Use least-privilege API keys for this workflow. If credentials may have been exposed, revoke or rotate them immediately.
- `weex-analysis-skill` output is for review and risk reference only. It is not investment or trading advice.
- When in doubt, ask the AI tool to preview or explain before asking it to execute anything.

## More Documentation

- [`weex-trader-skill` README](skills/weex-trader-skill/README.md): WEEX contract access, API profiles, order preview, AI Wars log upload, and troubleshooting.
- [`weex-analysis-skill` README](skills/weex-analysis-skill/README.md): accepted contract input data, analysis examples, replay review, and safety notes.
- [`weex-monitor-skill` SKILL.md](skills/weex-monitor-skill/SKILL.md): automated PnL monitor DSL, confirmation flow, dry-run runner, and live execution boundary.
- [`weex-trader-skill` script operations](skills/weex-trader-skill/references/script-operations.md): direct script usage for advanced users.
- [`weex-analysis-skill` analysis playbook](skills/weex-analysis-skill/references/analysis-playbook.md): analysis behavior and interpretation details.
