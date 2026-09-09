import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import unittest
from datetime import datetime, timedelta
from entry_evaluator import EntryEvaluator, MarketRegimeEvaluator

class MockStock:
    """Mock stock object for testing EntryEvaluator without network calls"""
    def __init__(self, prices, highs=None, lows=None, volumes=None):
        self.price = list(prices)
        self.high = list(highs) if highs is not None else [p * 1.02 for p in prices]
        self.low = list(lows) if lows is not None else [p * 0.98 for p in prices]
        self.capacity = list(volumes) if volumes is not None else [1000] * len(prices)
        today = datetime.now()
        self.date = [today - timedelta(days=len(prices)-i) for i in range(len(prices))]

class TestEntryEvaluator(unittest.TestCase):
    
    def test_insufficient_data(self):
        """少於 20 天資料應回傳資料不足觀望結果"""
        stock = MockStock([10.0] * 10)
        evaluator = EntryEvaluator(stock)
        res = evaluator.evaluate()
        self.assertFalse(res["can_enter"])
        self.assertIn("資料不足", res["verdict"])
        self.assertEqual(res["score"], 50)
        
    def test_bullish_uptrend_can_enter(self):
        """強勢多頭均線排列、良好風報比，應判定為可進場"""
        # 構造前 40 天在 100 附近橫盤打底 (RSI 處於 50 溫和區間)
        # 後 10 天溫和放量起漲至 108，前波壓力設在 125
        base_prices = [100.0 + (i % 4) * 0.4 - 0.5 for i in range(40)]
        uptrend_prices = [101.0, 100.8, 102.0, 103.2, 104.5, 105.8, 107.0]
        prices = base_prices + uptrend_prices
        highs = [p * 1.015 for p in prices]
        lows = [p * 0.985 for p in prices]
        # 在第 35 天設有前高壓力 125
        highs[35] = 125.0
        stock = MockStock(prices, highs, lows)
        
        evaluator = EntryEvaluator(stock)
        res = evaluator.evaluate()
        
        self.assertTrue(res["can_enter"], f"預期可進場，但結果為: {res['verdict']}")
        self.assertIn("🟢", res["verdict"])
        self.assertGreaterEqual(res["score"], 65)
        self.assertGreater(res["trend_score"], 25)
        self.assertIn("站穩月線", " ".join(res["reasons"]))
        
    def test_red_flag_large_downside_risk(self):
        """即使均線多頭，若股價距離20日支撐過遠(>10%)且追高，應啟動一票否決判定觀望"""
        # 前 30 天在 100 整理，隨後 15 天連續跳空拉抬至 160
        prices = [100.0] * 30 + [100.0 + i * 4.0 for i in range(15)]
        highs = [p * 1.02 for p in prices]
        lows = [p * 0.98 for p in prices]
        # 近 20 天之內包含當初 100 的起漲點支撐 (距現價 156 達 36% 乖離)
        lows[-18] = 98.0
        stock = MockStock(prices, highs, lows)
        
        evaluator = EntryEvaluator(stock)
        res = evaluator.evaluate()
        
        # 由於下行風險過大，一票否決機制應阻擋進場
        self.assertFalse(res["can_enter"], f"預期觀望，但結果為: {res['verdict']}")
        self.assertLess(res["score"], 65)
        self.assertTrue(any("下行風險" in flag for flag in res["red_flags"]))
        
    def test_bearish_downtrend_avoid(self):
        """跌破月線與季線之長期空頭股票，應明確判定為不宜進場或嚴禁進場"""
        # 構造 65 天下跌趨勢 (從 150 跌到 90)
        prices = [150.0 - i * 0.9 for i in range(65)]
        highs = [p * 1.01 for p in prices]
        lows = [p * 0.98 for p in prices]
        stock = MockStock(prices, highs, lows)
        
        evaluator = EntryEvaluator(stock)
        res = evaluator.evaluate()
        
        self.assertFalse(res["can_enter"])
        self.assertIn("🔴", res["verdict"])
        self.assertLess(res["score"], 45)
        self.assertTrue(any("空頭" in flag or "跌破" in flag for flag in res["red_flags"]))

class TestMarketRegimeEvaluator(unittest.TestCase):
    
    def test_market_regime_evaluation(self):
        """測試全市場多空廣度統計與進場環境判定"""
        # 建立 4 檔假想股票評估結果
        evaluations = [
            {
                "code": "2330",
                "name": "台積電",
                "price": 1000.0,
                "eval": {
                    "can_enter": True,
                    "verdict": "🟢 強烈可進場",
                    "verdict_badge": "🟢 強烈可進場",
                    "score": 88,
                    "trend_score": 35,
                    "rrr": 2.8,
                    "stop_loss": 970.0,
                    "upside_target": 1100.0,
                    "suggested_entry": "現價進場",
                    "reasons": ["站穩月線", "風報比極佳"]
                }
            },
            {
                "code": "2317",
                "name": "鴻海",
                "price": 200.0,
                "eval": {
                    "can_enter": True,
                    "verdict": "🟢 可分批進場",
                    "verdict_badge": "🟢 可分批進場",
                    "score": 72,
                    "trend_score": 30,
                    "rrr": 1.9,
                    "stop_loss": 192.0,
                    "upside_target": 215.0,
                    "suggested_entry": "回測MA5分批",
                    "reasons": ["站穩月線"]
                }
            },
            {
                "code": "2454",
                "name": "聯發科",
                "price": 1200.0,
                "eval": {
                    "can_enter": False,
                    "verdict": "🟡 暫緩進場 (觀望)",
                    "verdict_badge": "🟡 建議觀望",
                    "score": 55,
                    "trend_score": 20,
                    "rrr": 1.1,
                    "stop_loss": 1150.0,
                    "upside_target": 1250.0,
                    "suggested_entry": "暫緩觀望",
                    "reasons": []
                }
            },
            {
                "code": "2603",
                "name": "長榮",
                "price": 180.0,
                "eval": {
                    "can_enter": False,
                    "verdict": "🔴 不宜進場 (減碼)",
                    "verdict_badge": "🔴 不宜進場",
                    "score": 35,
                    "trend_score": 0,
                    "rrr": 0.5,
                    "stop_loss": 170.0,
                    "upside_target": 185.0,
                    "suggested_entry": "逢高減碼",
                    "reasons": []
                }
            }
        ]
        
        regime_eval = MarketRegimeEvaluator(evaluations)
        res = regime_eval.evaluate_market()
        
        self.assertEqual(res["total_count"], 4)
        self.assertEqual(res["buy_count"], 2)
        self.assertEqual(res["wait_count"], 1)
        self.assertEqual(res["sell_count"], 1)
        # 3檔站上月線 (trend_score >= 15) -> 75%
        self.assertEqual(res["bull_ratio_ma20"], 75.0)
        self.assertTrue(res["can_enter_market"])
        self.assertIn("🟢", res["market_verdict"])
        self.assertEqual(len(res["top_picks"]), 2)
        # 第一推薦應為分數最高的台積電 (88分)
        self.assertEqual(res["top_picks"][0]["code"], "2330")

if __name__ == "__main__":
    unittest.main()
