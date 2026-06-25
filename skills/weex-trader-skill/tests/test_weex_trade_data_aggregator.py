#!/usr/bin/env python3
from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import weex_trade_data_aggregator as aggregator
import weex_contract_api
import weex_trade_risk_review as risk_review


class ContractOnlyAggregatorTests(unittest.TestCase):
    def test_parser_accepts_futures_without_public_trading_mode_switch(self) -> None:
        parser = aggregator.build_parser()

        args = parser.parse_args(
            [
                "collect-account-risk",
                "--profile",
                "main",
                "--market",
                "futures",
            ]
        )

        self.assertEqual(args.market, "futures")
        with self.assertRaises(SystemExit):
            parser.parse_args(["collect-account-risk", "--profile", "main", "--market", "spot"])
        with self.assertRaises(SystemExit):
            parser.parse_args(
                [
                    "collect-account-risk",
                    "--profile",
                    "main",
                    "--market",
                    "futures",
                    "--trading-mode",
                    "live",
                ]
            )

    def test_rejects_non_futures_market_before_fetching(self) -> None:
        fetcher = mock.Mock()
        trade_aggregator = aggregator.TradeDataAggregator(fetcher=fetcher)

        with self.assertRaises(aggregator.AggregationInputError) as exc_info:
            trade_aggregator.collect_account_risk_payload(profile_name="main", market="spot")

        self.assertIn("futures", str(exc_info.exception))
        fetcher.fetch_futures_balance.assert_not_called()

    def test_rejects_non_live_trading_mode_before_fetching(self) -> None:
        fetcher = mock.Mock()
        trade_aggregator = aggregator.TradeDataAggregator(fetcher=fetcher)

        with self.assertRaises(aggregator.AggregationInputError) as exc_info:
            trade_aggregator.collect_account_risk_payload(
                profile_name="main",
                market="futures",
                trading_mode="demo",
            )

        self.assertIn("live", str(exc_info.exception))
        fetcher.fetch_futures_balance.assert_not_called()

    def test_live_environment_prefix_is_real_contract_only(self) -> None:
        environment = aggregator._environment_for_trading_mode("live", "futures")

        self.assertEqual(environment["trading_mode"], "live")
        self.assertTrue(environment["uses_real_funds"])
        self.assertEqual(aggregator._user_environment_prefix(environment, "zh"), "当前交易环境：真实盘")
        self.assertEqual(aggregator._user_environment_prefix(environment, "en"), "Current trading mode: real trading")

    def test_fetch_futures_balance_uses_live_contract_endpoint(self) -> None:
        fetcher = aggregator.WeexApiFetcher()

        with mock.patch.object(
            fetcher,
            "_send_contract_request",
            return_value={"balance": []},
        ) as send_mock:
            payload = fetcher.fetch_futures_balance(profile_name="main", trading_mode="live")

        self.assertEqual(payload, {"balance": []})
        send_mock.assert_called_once()
        self.assertEqual(send_mock.call_args.kwargs["endpoint_key"], "account.get_account_balance")

    def test_build_contract_client_uses_profile_runtime_loader(self) -> None:
        fetcher = aggregator.WeexApiFetcher()
        profile = types.SimpleNamespace(name="main", contract_base_url="")
        contract_api = types.SimpleNamespace(
            DEFAULT_BASE_URL=weex_contract_api.DEFAULT_BASE_URL,
            DEFAULT_LOCALE=weex_contract_api.DEFAULT_LOCALE,
            DEFAULT_TIMEOUT=weex_contract_api.DEFAULT_TIMEOUT,
            WeexContractClient=mock.Mock(return_value=mock.Mock()),
            ensure_private_runtime_ready=mock.Mock(),
            refresh_agent_records=mock.Mock(),
            require_private_profile=mock.Mock(),
            resolve_runtime_profile=mock.Mock(return_value=profile),
        )

        with mock.patch.object(fetcher, "_contract_module", return_value=contract_api), mock.patch.dict(
            "os.environ",
            {},
            clear=True,
        ):
            returned_contract_api, client = fetcher._build_contract_client("main")

        self.assertIs(returned_contract_api, contract_api)
        self.assertIs(client, contract_api.WeexContractClient.return_value)
        contract_api.WeexContractClient.assert_called_once()
        client_kwargs = contract_api.WeexContractClient.call_args.kwargs
        self.assertIsNone(client_kwargs["api_key"])
        self.assertIsNone(client_kwargs["api_secret"])
        self.assertIsNone(client_kwargs["api_passphrase"])
        self.assertEqual(client_kwargs["profile_name"], "main")

    def test_order_collection_uses_existing_contract_order_endpoints(self) -> None:
        fetcher = aggregator.WeexApiFetcher()

        cases = (
            (
                fetcher.fetch_futures_open_orders,
                "transaction.get_current_order_status",
            ),
            (
                fetcher.fetch_futures_pending_orders,
                "transaction.get_current_pending_orders",
            ),
        )
        for fetch_method, expected_endpoint_key in cases:
            with self.subTest(endpoint=expected_endpoint_key), mock.patch.object(
                fetcher,
                "_send_contract_request",
                return_value={"orders": []},
            ) as send_mock:
                payload = fetch_method(profile_name="main", symbol="ethusdt", trading_mode="live")

            self.assertEqual(payload, {"orders": []})
            send_mock.assert_called_once()
            call_kwargs = send_mock.call_args.kwargs
            self.assertEqual(call_kwargs["endpoint_key"], expected_endpoint_key)
            self.assertIn(call_kwargs["endpoint_key"], weex_contract_api.ENDPOINTS)
            self.assertEqual(call_kwargs["query"], {"symbol": "ETHUSDT"})
            self.assertIsNone(call_kwargs.get("body"))

    def test_order_risk_payload_exposes_analysis_context(self) -> None:
        fetcher = mock.Mock()
        fetcher.fetch_futures_balance.return_value = [
            {
                "asset": "USDT",
                "balance": "1000",
                "availableBalance": "620",
                "unrealizePnl": "12",
            }
        ]
        fetcher.fetch_futures_positions.return_value = [
            {
                "symbol": "BTCUSDT",
                "positionSide": "LONG",
                "size": "0.01",
                "openValue": "650",
                "leverage": "20",
            }
        ]
        fetcher.fetch_futures_open_orders.return_value = [
            {
                "orderId": 101,
                "symbol": "BTCUSDT",
                "side": "BUY",
                "positionSide": "LONG",
                "type": "LIMIT",
                "origQty": "0.02",
                "executedQty": "0.01",
                "price": "64000",
            }
        ]
        fetcher.fetch_futures_pending_orders.return_value = [
            {
                "algoId": 201,
                "symbol": "BTCUSDT",
                "side": "SELL",
                "positionSide": "LONG",
                "orderType": "TAKE_PROFIT_MARKET",
                "quantity": "0.01",
                "triggerPrice": "85000",
                "reduceOnly": True,
            },
            {
                "algoId": 202,
                "symbol": "BTCUSDT",
                "side": "SELL",
                "positionSide": "LONG",
                "orderType": "STOP_MARKET",
                "quantity": "0.01",
                "triggerPrice": "60000",
                "reduceOnly": True,
            },
        ]
        trade_aggregator = aggregator.TradeDataAggregator(fetcher=fetcher)

        payload = trade_aggregator.collect_order_risk_payload(
            profile_name="main",
            market="futures",
            trading_mode="live",
            raw_order={
                "symbol": "btcusdt",
                "side": "BUY",
                "positionSide": "LONG",
                "type": "MARKET",
                "quantity": "0.01",
            },
        )

        self.assertEqual(payload["account_snapshot"]["balance"], 1000.0)
        self.assertEqual(payload["account_snapshot"]["available_balance"], 620.0)
        self.assertEqual(payload["positions"][0]["notional"], 650.0)
        self.assertEqual(payload["order_preview"]["market"], "futures")
        self.assertEqual(payload["open_orders"][0]["order_id"], "101")
        self.assertEqual(payload["conditional_orders"][0]["tp_trigger_price"], 85000.0)
        self.assertEqual(payload["conditional_orders"][1]["sl_trigger_price"], 60000.0)

    def test_order_risk_payload_includes_recent_order_history_for_frequency_alert(self) -> None:
        now_ms = 1710004200000
        fetcher = mock.Mock()
        fetcher.fetch_futures_balance.return_value = [
            {
                "asset": "USDT",
                "balance": "1000",
                "availableBalance": "620",
            }
        ]
        fetcher.fetch_futures_positions.return_value = []
        fetcher.fetch_futures_open_orders.return_value = []
        fetcher.fetch_futures_pending_orders.return_value = []
        fetcher.fetch_futures_orders.return_value = [
            {
                "orderId": 100 + index,
                "symbol": "BTCUSDT",
                "side": "BUY",
                "positionSide": "LONG",
                "type": "MARKET",
                "status": "FILLED",
                "origQty": "0.001",
                "executedQty": "0.001",
                "time": now_ms - (index * 5 * 60 * 1000),
            }
            for index in range(7)
        ]
        trade_aggregator = aggregator.TradeDataAggregator(fetcher=fetcher)

        with mock.patch.object(aggregator, "_now_ms", return_value=now_ms):
            payload = trade_aggregator.collect_order_risk_payload(
                profile_name="main",
                market="futures",
                trading_mode="live",
                raw_order={
                    "symbol": "BTCUSDT",
                    "side": "BUY",
                    "positionSide": "LONG",
                    "type": "MARKET",
                    "quantity": "0.001",
                },
            )

        self.assertEqual(len(payload["recent_orders"]), 7)
        fetcher.fetch_futures_orders.assert_called_once_with(
            profile_name="main",
            start_ms=now_ms - aggregator.RECENT_ORDER_LOOKBACK_MS,
            end_ms=now_ms,
            symbol="BTCUSDT",
            trading_mode="live",
        )
        result = risk_review.analyze_order_risk(payload)
        self.assertIn("high_trade_frequency", {alert["type"] for alert in result["alerts"]})

    def test_account_risk_marks_partial_when_recent_order_history_is_unavailable(self) -> None:
        fetcher = mock.Mock()
        fetcher.fetch_futures_balance.return_value = [
            {
                "asset": "USDT",
                "balance": "1000",
                "availableBalance": "620",
            }
        ]
        fetcher.fetch_futures_positions.return_value = []
        fetcher.fetch_futures_open_orders.return_value = []
        fetcher.fetch_futures_pending_orders.return_value = []
        fetcher.fetch_futures_orders.side_effect = aggregator.AggregationInputError("order history unavailable")
        trade_aggregator = aggregator.TradeDataAggregator(fetcher=fetcher)

        payload = trade_aggregator.collect_account_risk_payload(
            profile_name="main",
            market="futures",
            trading_mode="live",
            symbol="BTCUSDT",
        )

        self.assertTrue(payload["partial"])
        self.assertIn("recent_order_history_unavailable", payload["degraded_reasons"])
        self.assertEqual(payload["recent_orders"], [])

    def test_collect_replay_payload_includes_futures_fills_bills_and_price_series(self) -> None:
        fetcher = mock.Mock()
        fetcher.fetch_futures_balance.return_value = {
            "asset": "USDT",
            "balance": "1000",
            "availableBalance": "620",
            "unrealizePnl": "30",
        }
        fetcher.fetch_futures_positions.return_value = [
            {
                "symbol": "BTCUSDT",
                "side": "LONG",
                "marginType": "CROSSED",
                "separatedMode": "COMBINED",
                "size": "0.01",
                "openValue": "650",
            }
        ]
        fetcher.fetch_futures_orders.return_value = [
            {
                "symbol": "BTCUSDT",
                "orderId": 11,
                "side": "BUY",
                "positionSide": "LONG",
                "type": "LIMIT",
                "status": "FILLED",
                "origQty": "0.01",
                "executedQty": "0.01",
                "cumQuote": "650",
                "avgPrice": "65000",
                "time": 1710000000000,
            }
        ]
        fetcher.fetch_futures_historical_pending_orders.return_value = []
        fetcher.fetch_futures_fills.return_value = [
            {
                "id": 21,
                "orderId": 11,
                "symbol": "BTCUSDT",
                "side": "BUY",
                "positionSide": "LONG",
                "price": "65000",
                "qty": "0.01",
                "quoteQty": "650",
                "realizedPnl": "12",
                "commission": "0.5",
                "time": 1710003600000,
            }
        ]
        fetcher.fetch_futures_bills.return_value = {
            "items": [
                {
                    "billId": 31,
                    "asset": "USDT",
                    "symbol": "BTCUSDT",
                    "income": "12",
                    "incomeType": "position_close_long",
                    "fillFee": "0.5",
                    "time": 1710003600000,
                }
            ]
        }
        fetcher.fetch_futures_klines.return_value = [
            [1710000000000, "64000", "66000", "63500", "65000", "100", 1710003599999, "6500000", 120, "55", "3575000"]
        ]
        trade_aggregator = aggregator.TradeDataAggregator(fetcher=fetcher)

        result = trade_aggregator.collect_replay_payload(
            profile_name="main",
            market="futures",
            trading_mode="live",
            period="7d",
            symbol="BTCUSDT",
        )

        self.assertEqual(result["market"], "futures")
        self.assertEqual(result["trading_mode"], "live")
        self.assertEqual(result["balances"][0]["account_scope"], "personal_futures")
        self.assertEqual(result["positions"][0]["symbol"], "BTCUSDT")
        self.assertEqual(result["orders"][0]["status"], "FILLED")
        self.assertEqual(result["fills"][0]["realized_pnl"], 12.0)
        self.assertEqual(result["bills"][0]["type"], "position_close_long")
        self.assertEqual(result["price_series"][0]["close"], 65000.0)
        self.assertEqual(result["closed_trade_count"], 1)
        fetcher.fetch_futures_fills.assert_called()
        fetcher.fetch_futures_bills.assert_called()
        fetcher.fetch_futures_klines.assert_called_once()

    def test_main_exits_for_rejected_market(self) -> None:
        with self.assertRaises(SystemExit) as exc_info:
            aggregator.main(["collect-account-risk", "--profile", "main", "--market", "spot"])

        self.assertEqual(exc_info.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
