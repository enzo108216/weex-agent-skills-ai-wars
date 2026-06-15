# WEEX AI Wars Agent Repo Guidance

- Treat `skills/` as the only source-of-truth layer.
- Use `skills/weex-trader-skill` for WEEX AI Wars real contract REST access, profile management, vault operations, risk previews, AI log upload, and any live order action.
- Use `skills/weex-analysis-skill` for read-only analysis of normalized WEEX real contract snapshots, fills, replay data, profiles, order-risk payloads, and account-risk payloads.
- Use `skills/weex-monitor-skill` for automated monitor orchestration around real contract position PnL tasks; it delegates account reads and execution to `skills/weex-trader-skill`.
- Never send mutating requests without explicit user confirmation and the `--confirm-live` flag required by the trader skill.
- AI-driven real contract mutating requests must validate the matching `--ai-log @file.json` before execution when using the automatic upload path.
- Do not route requests to removed skills or unsupported markets/environments.
- Prefer non-argv secret transport when the trader skill offers a safer option.
