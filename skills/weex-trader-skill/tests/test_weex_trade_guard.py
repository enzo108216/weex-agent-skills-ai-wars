#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import weex_trade_guard as trade_guard


class ContractOnlyTradeGuardTests(unittest.TestCase):
    def test_parser_only_accepts_futures_and_live_confirmation(self) -> None:
        parser = trade_guard.build_parser()

        args = parser.parse_args(
            [
                "preview-order",
                "--profile",
                "main",
                "--market",
                "futures",
                "--trading-mode",
                "live",
                "--order-json",
                '{"symbol":"BTCUSDT","side":"BUY","position_side":"LONG","type":"MARKET","quantity":"0.001"}',
            ]
        )

        self.assertEqual(args.market, "futures")
        self.assertEqual(args.trading_mode, "live")
        args = parser.parse_args(
            [
                "preview-order",
                "--profile",
                "main",
                "--market",
                "futures",
                "--trading-mode",
                "live",
                "--order-json",
                '{"symbol":"BTCUSDT","side":"BUY","position_side":"LONG","type":"MARKET","quantity":"0.001"}',
                "--ai-log",
                "@/tmp/ai-log.json",
            ]
        )
        self.assertEqual(args.ai_log, "@/tmp/ai-log.json")
        args = parser.parse_args(
            [
                "confirm-order",
                "--intent-id",
                "intent-1",
                "--risk-signature",
                "sig-1",
                "--confirm-live",
                "--ai-log",
                "@/tmp/ai-log.json",
            ]
        )
        self.assertEqual(args.ai_log, "@/tmp/ai-log.json")
        with self.assertRaises(SystemExit):
            parser.parse_args(
                [
                    "preview-order",
                    "--profile",
                    "main",
                    "--market",
                    "spot",
                    "--order-json",
                    "{}",
                ]
            )
        with self.assertRaises(SystemExit):
            parser.parse_args(
                [
                    "confirm-order",
                    "--intent-id",
                    "intent-1",
                    "--risk-signature",
                    "sig-1",
                    "--trading-mode",
                    "demo",
                ]
            )
        with self.assertRaises(SystemExit):
            parser.parse_args(
                [
                    "confirm-order",
                    "--intent-id",
                    "intent-1",
                    "--risk-signature",
                    "sig-1",
                    "--confirm-demo",
                ]
            )

    def test_parser_accepts_ai_log_for_tp_sl_preview_and_confirmation(self) -> None:
        parser = trade_guard.build_parser()

        args = parser.parse_args(
            [
                "preview-tp-sl",
                "--profile",
                "main",
                "--tp-sl-json",
                '{"symbol":"BTCUSDT","clientAlgoId":"algo-1","planType":"STOP_LOSS","triggerPrice":"65000","quantity":"0.001","positionSide":"LONG"}',
                "--ai-log",
                "@/tmp/tp-sl-ai-log.json",
            ]
        )
        self.assertEqual(args.ai_log, "@/tmp/tp-sl-ai-log.json")

        args = parser.parse_args(
            [
                "confirm-tp-sl",
                "--intent-id",
                "intent-1",
                "--risk-signature",
                "sig-1",
                "--confirm-live",
                "--ai-log",
                "@/tmp/tp-sl-ai-log.json",
            ]
        )
        self.assertEqual(args.ai_log, "@/tmp/tp-sl-ai-log.json")

    def test_live_environment_labels_are_contract_only(self) -> None:
        environment = trade_guard._environment_for_mode("live", "futures")

        self.assertEqual(environment["trading_mode"], "live")
        self.assertTrue(environment["uses_real_funds"])
        self.assertEqual(
            trade_guard._user_facing_trading_mode_label(environment, language="zh"),
            "真实盘",
        )
        self.assertEqual(
            trade_guard._user_facing_trading_mode_label(environment, language="en"),
            "real trading",
        )

    def test_submit_order_rejects_non_futures_market_before_client_build(self) -> None:
        with mock.patch.object(trade_guard, "_build_contract_client") as contract_mock:
            with self.assertRaises(trade_guard.AggregationInputError) as exc_info:
                trade_guard._submit_live_order(
                    market="spot",
                    profile_name="main",
                    raw_order={
                        "symbol": "BTCUSDT",
                        "side": "BUY",
                        "type": "MARKET",
                        "quantity": "0.001",
                    },
                )

        self.assertIn("futures", str(exc_info.exception))
        contract_mock.assert_not_called()

    def test_submit_order_uses_contract_execute_endpoint_with_ai_log_context(self) -> None:
        fake_contract_api = mock.Mock()
        fake_contract_api.find_endpoint_key_by_doc_suffix.return_value = "transaction.place_order"
        fake_contract_api.ENDPOINTS = {"transaction.place_order": object()}
        fake_contract_api.normalize_contract_trade_symbol.side_effect = lambda symbol: symbol.upper()
        fake_contract_api.generate_client_oid.return_value = "generated-client-id"
        fake_contract_api.execute_endpoint_payload.return_value = (
            0,
            {
                "endpoint": "transaction.place_order",
                "businessOk": True,
                "exitCode": 0,
                "result": {"orderId": "1001"},
            },
        )

        fake_client = mock.Mock()
        ai_log_context = {"stage": "Strategy Generation", "model": "gpt-5", "input": {"prompt": "buy"}, "output": {}, "explanation": "test"}

        with mock.patch.object(trade_guard, "_build_contract_client", return_value=(fake_contract_api, fake_client)):
            result = trade_guard._submit_live_order(
                market="futures",
                profile_name="main",
                raw_order={
                    "symbol": "btcusdt",
                    "side": "BUY",
                    "position_side": "LONG",
                    "type": "MARKET",
                    "quantity": "0.001",
                },
                ai_log_context=ai_log_context,
            )

        self.assertEqual(result["exitCode"], 0)
        self.assertEqual(result["result"], {"orderId": "1001"})
        fake_contract_api.find_endpoint_key_by_doc_suffix.assert_called_once_with("PlaceOrder")
        fake_contract_api.execute_endpoint_payload.assert_called_once()
        execute_kwargs = fake_contract_api.execute_endpoint_payload.call_args.kwargs
        self.assertIs(execute_kwargs["client"], fake_client)
        self.assertEqual(execute_kwargs["endpoint_key"], "transaction.place_order")
        self.assertEqual(execute_kwargs["body"]["symbol"], "BTCUSDT")
        self.assertEqual(execute_kwargs["body"]["newClientOrderId"], "generated-client-id")
        self.assertFalse(execute_kwargs["dry_run"])
        self.assertTrue(execute_kwargs["confirm_live"])
        self.assertIs(execute_kwargs["ai_log_context"], ai_log_context)
        fake_client.prepare_request.assert_not_called()
        fake_client.send.assert_not_called()

    def test_submit_tp_sl_order_uses_contract_execute_endpoint_with_ai_log_context(self) -> None:
        fake_contract_api = mock.Mock()
        fake_contract_api.find_endpoint_key_by_doc_suffix.return_value = "transaction.place_tp_sl_order"
        fake_contract_api.ENDPOINTS = {"transaction.place_tp_sl_order": object()}
        fake_contract_api.normalize_contract_trade_symbol.side_effect = lambda symbol: symbol.upper()
        fake_contract_api.execute_endpoint_payload.return_value = (
            0,
            {
                "endpoint": "transaction.place_tp_sl_order",
                "businessOk": True,
                "exitCode": 0,
                "result": [{"orderId": "tp-1"}],
            },
        )
        fake_client = mock.Mock()
        ai_log_context = {"stage": "Strategy Generation", "model": "gpt-5", "input": {"prompt": "sl"}, "output": {}, "explanation": "test"}

        with mock.patch.object(trade_guard, "_build_contract_client", return_value=(fake_contract_api, fake_client)):
            result = trade_guard._submit_live_tp_sl_order(
                profile_name="main",
                raw_order={
                    "symbol": "btcusdt",
                    "clientAlgoId": "algo-1",
                    "planType": "STOP_LOSS",
                    "triggerPrice": "65000",
                    "quantity": "0.001",
                    "positionSide": "LONG",
                },
                ai_log_context=ai_log_context,
            )

        self.assertEqual(result["exitCode"], 0)
        fake_contract_api.find_endpoint_key_by_doc_suffix.assert_called_once_with("PlaceTpSlOrder")
        fake_contract_api.execute_endpoint_payload.assert_called_once()
        execute_kwargs = fake_contract_api.execute_endpoint_payload.call_args.kwargs
        self.assertEqual(execute_kwargs["endpoint_key"], "transaction.place_tp_sl_order")
        self.assertEqual(execute_kwargs["body"]["symbol"], "BTCUSDT")
        self.assertEqual(execute_kwargs["body"]["planType"], "STOP_LOSS")
        self.assertIs(execute_kwargs["ai_log_context"], ai_log_context)
        fake_client.prepare_request.assert_not_called()
        fake_client.send.assert_not_called()

    def test_confirm_order_passes_saved_ai_log_context_to_live_submission(self) -> None:
        ai_log_context = {"stage": "Strategy Generation", "model": "gpt-5", "input": {"prompt": "buy"}, "output": {}, "explanation": "test"}
        intent = {
            "intent_id": "intent-1",
            "intent_type": "order",
            "profile_name": "main",
            "market": "futures",
            "trading_mode": "live",
            "expires_at": 2000,
            "risk_signature": "sig-1",
            "raw_order": {
                "symbol": "BTCUSDT",
                "side": "BUY",
                "positionSide": "LONG",
                "type": "MARKET",
                "quantity": "0.001",
            },
            "environment": {"trading_mode": "live", "uses_real_funds": True, "market": "futures"},
            "ai_log_context": ai_log_context,
        }
        args = mock.Mock(
            intent_id="intent-1",
            risk_signature="sig-1",
            trading_mode="live",
            confirm_live=True,
            confirm_demo=False,
            language=None,
            pretty=False,
            ai_log=None,
        )
        captured = {}

        with mock.patch.object(trade_guard, "load_intent", return_value=intent), mock.patch.object(
            trade_guard,
            "intent_is_expired",
            return_value=False,
        ), mock.patch.object(trade_guard, "clear_intent") as clear_mock, mock.patch.object(
            trade_guard,
            "_submit_live_order",
            return_value={"businessOk": True, "exitCode": 0, "result": {"orderId": "1001"}},
        ) as submit_mock, mock.patch.object(
            trade_guard,
            "_output_json",
            side_effect=lambda payload, pretty: captured.setdefault("payload", payload),
        ):
            exit_code = trade_guard.cmd_confirm_order(args, now_ms=1000)

        self.assertEqual(exit_code, 0)
        clear_mock.assert_called_once()
        submit_mock.assert_called_once()
        self.assertIs(submit_mock.call_args.kwargs["ai_log_context"], ai_log_context)
        self.assertEqual(captured["payload"]["aiLogContextSource"], "preview")

    def test_confirm_tp_sl_passes_saved_ai_log_context_to_live_submission(self) -> None:
        ai_log_context = {"stage": "Strategy Generation", "model": "gpt-5", "input": {"prompt": "sl"}, "output": {}, "explanation": "test"}
        tp_sl_order = {
            "symbol": "BTCUSDT",
            "clientAlgoId": "algo-1",
            "planType": "STOP_LOSS",
            "triggerPrice": "65000",
            "quantity": "0.001",
            "positionSide": "LONG",
        }
        intent = {
            "intent_id": "intent-1",
            "intent_type": "tp_sl_order",
            "profile_name": "main",
            "market": "futures",
            "trading_mode": "live",
            "expires_at": 2000,
            "risk_signature": "sig-1",
            "tp_sl_order": tp_sl_order,
            "environment": {"trading_mode": "live", "uses_real_funds": True, "market": "futures"},
            "ai_log_context": ai_log_context,
        }
        args = mock.Mock(
            intent_id="intent-1",
            risk_signature="sig-1",
            trading_mode="live",
            confirm_live=True,
            confirm_demo=False,
            pretty=False,
            ai_log=None,
        )
        captured = {}

        with mock.patch.object(trade_guard, "load_intent", return_value=intent), mock.patch.object(
            trade_guard,
            "intent_is_expired",
            return_value=False,
        ), mock.patch.object(trade_guard, "clear_intent") as clear_mock, mock.patch.object(
            trade_guard,
            "_submit_live_tp_sl_order",
            return_value={"businessOk": True, "exitCode": 0, "result": [{"orderId": "tp-1"}]},
        ) as submit_mock, mock.patch.object(
            trade_guard,
            "_output_json",
            side_effect=lambda payload, pretty: captured.setdefault("payload", payload),
        ):
            exit_code = trade_guard.cmd_confirm_tp_sl(args, now_ms=1000)

        self.assertEqual(exit_code, 0)
        clear_mock.assert_called_once()
        submit_mock.assert_called_once()
        self.assertIs(submit_mock.call_args.kwargs["ai_log_context"], ai_log_context)
        self.assertEqual(captured["payload"]["aiLogContextSource"], "preview")

    def test_confirm_flag_matching_requires_live_flag_only(self) -> None:
        args = mock.Mock(confirm_live=True, confirm_demo=False)
        self.assertTrue(trade_guard._confirm_flags_match_mode(args, "live"))

        args = mock.Mock(confirm_live=False, confirm_demo=False)
        self.assertFalse(trade_guard._confirm_flags_match_mode(args, "live"))


if __name__ == "__main__":
    unittest.main()
