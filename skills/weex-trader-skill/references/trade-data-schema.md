# Trade Data Schema

The AI Wars trader aggregation layer emits normalized JSON for real contract replay, profile, order-risk, and account-risk payloads.

## Shared Fields

- `schema`: local payload schema identifier.
- `profile`: saved profile name used for collection.
- `market`: always `futures`.
- `trading_mode`: always `live`.
- `environment`: user-facing trading metadata; display this instead of inferring context from profile names or base URLs.
- `symbol`: optional uppercase contract symbol.
- `partial`: whether the aggregation layer could not prove the dataset is complete.
- `constraints`: explicit collection limits.
- `degraded_reasons`: machine-readable collection gaps.

## Environment

```json
{
  "trading_mode": "live",
  "label": "live",
  "market": "futures",
  "uses_real_funds": true,
  "notice": "This operation targets real WEEX futures trading."
}
```

Chinese user-facing summaries should begin with `当前交易环境：真实盘` when the prefix is returned. English summaries should begin with `Current trading mode: real trading`.

## Replay Payload

```json
{
  "schema": "weex.ai_wars.contract_payload.v1",
  "profile": "main",
  "market": "futures",
  "trading_mode": "live",
  "environment": {
    "trading_mode": "live",
    "label": "live",
    "market": "futures",
    "uses_real_funds": true,
    "notice": "This operation targets real WEEX futures trading."
  },
  "period": "30d",
  "symbol": "BTCUSDT",
  "orders": [],
  "partial": false,
  "constraints": [],
  "degraded_reasons": []
}
```

`collect-replay` accepts `7d`, `30d`, `90d`, `180d`, and `360d`. The payload is intended for local review and audit trails around contract activity.

## Profile Payload

`collect-profile` reuses the replay payload shape and records a longer collection period. It does not create a separate strategy profile or scoring model.

## Order-Risk Payload

```json
{
  "schema": "weex.ai_wars.contract_payload.v1",
  "profile": "main",
  "market": "futures",
  "trading_mode": "live",
  "environment": {
    "trading_mode": "live",
    "label": "live",
    "market": "futures",
    "uses_real_funds": true,
    "notice": "This operation targets real WEEX futures trading."
  },
  "order_preview": {
    "symbol": "BTCUSDT",
    "side": "BUY",
    "position_side": "LONG",
    "type": "MARKET",
    "quantity": "0.001"
  },
  "balances": [],
  "positions": [],
  "orders": [],
  "fills": [],
  "bills": [],
  "partial": false,
  "constraints": [],
  "degraded_reasons": []
}
```

The pending order intent and risk signature bind `trading_mode`, `environment`, profile, market, order preview, and alerts before a real order can be confirmed.

## Account-Risk Payload

```json
{
  "schema": "weex.ai_wars.contract_payload.v1",
  "profile": "main",
  "market": "futures",
  "trading_mode": "live",
  "environment": {
    "trading_mode": "live",
    "label": "live",
    "market": "futures",
    "uses_real_funds": true,
    "notice": "This operation targets real WEEX futures trading."
  },
  "symbol": "BTCUSDT",
  "balances": [],
  "positions": [],
  "orders": [],
  "fills": [],
  "bills": [],
  "partial": false,
  "constraints": [],
  "degraded_reasons": []
}
```

Account-risk scans are read-only, but they still carry the same environment block because they inspect private account state.
