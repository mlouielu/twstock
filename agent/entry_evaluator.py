import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from datetime import datetime
from tech_indicators import calculate_rsi, calculate_kd, calculate_atr
from macd import get_macd_signal, calculate_macd
from twstock.analytics import BestFourPoint

class EntryEvaluator:
    """
    量化進場裁決引擎 (Entry Evaluator)
    整合：趨勢均線(40分)、動能型態(30分)、風報比安全空間(30分)
    並設置一票否決 (Red Flag) 機制，確保給出明確、果斷、不自相矛盾的「是否可以進場」決策。
    """
    def __init__(self, stock):
        self.stock = stock
        self.prices = stock.price
        self.highs = stock.high
        self.lows = stock.low
        self.volumes = stock.capacity
        self.n = len(self.prices)
        
    def evaluate(self):
        """
        執行進場評估，回傳決策字典：
        {
            "can_enter": bool,
            "verdict": str, # "🟢 強烈可進場", "🟢 可偏多進場", "🟡 暫緩進場 (觀望)", "🔴 不宜進場 (減碼)", "🔴 嚴禁進場 (避開)"
            "verdict_badge": str, # 短版燈號供表格使用
            "score": int, # 0 ~ 100
            "trend_score": int,
            "momentum_score": int,
            "risk_reward_score": int,
            "rrr": float, # 風報比
            "upside_target": float,
            "upside_pct": float,
            "downside_risk": float,
            "downside_pct": float,
            "stop_loss": float,
            "suggested_entry": str,
            "red_flags": list, # 一票否決或嚴重警示原因
            "reasons": list, # 正向支持理由
            "signals": list # 原有的技術訊號字串清單
        }
        """
        if self.n < 20:
            return self._fallback_result("資料不足(少於20日)")
            
        current_price = self.prices[-1]
        
        # 1. 均線計算
        ma5 = sum(self.prices[-5:]) / 5 if self.n >= 5 else current_price
        ma20 = sum(self.prices[-20:]) / 20
        ma60 = sum(self.prices[-60:]) / 60 if self.n >= 60 else ma20
        
        # 均線斜率 (前 5 天的 MA20)
        ma20_prev = sum(self.prices[-25:-5]) / 20 if self.n >= 25 else ma20
        ma20_slope_up = ma20 >= ma20_prev
        
        # ── 趨勢維度評分 (最高 40 分) ────────────────────────
        trend_score = 0
        reasons = []
        red_flags = []
        
        if current_price >= ma20:
            trend_score += 15
            reasons.append("站穩月線 (MA20)")
        else:
            red_flags.append("跌破月線 (MA20)")
            
        if current_price >= ma60:
            trend_score += 15
            reasons.append("站上季線 (MA60)")
        else:
            if self.n >= 60:
                red_flags.append("處於季線 (MA60) 之下，長期空頭")
                
        if ma5 >= ma20:
            trend_score += 5
            reasons.append("短均多頭排列 (MA5 > MA20)")
            
        if ma20_slope_up:
            trend_score += 5
            reasons.append("月線趨勢向上")
            
        # ── 動能與型態維度 (最高 30 分) ──────────────────────
        momentum_score = 15 # 基礎中性分
        signals = []
        
        # 2.1 四大買賣點
        bfp_buy = False
        bfp_sell = False
        try:
            bfp = BestFourPoint(self.stock)
            bfp_res = bfp.best_four_point()
            if bfp_res:
                is_buy, bfp_reason = bfp_res
                if is_buy:
                    bfp_buy = True
                    momentum_score += 10
                    signals.append(f"[🟢 買進] 四大買賣點: {bfp_reason}")
                    reasons.append(f"四大買點: {bfp_reason}")
                else:
                    bfp_sell = True
                    momentum_score -= 15
                    signals.append(f"[🔴 賣出] 四大買賣點: {bfp_reason}")
                    red_flags.append(f"四大賣點: {bfp_reason}")
        except Exception:
            pass
            
        # 2.2 MACD 指標
        macd_res = calculate_macd(self.prices)
        if macd_res and macd_res["osc"] and len(macd_res["osc"]) >= 2:
            osc_now = macd_res["osc"][-1]
            osc_prev = macd_res["osc"][-2]
            if osc_now is not None and osc_prev is not None:
                if osc_prev <= 0 and osc_now > 0:
                    momentum_score += 10
                    signals.append("🟢 MACD 黃金交叉 (柱狀圖由負轉正)")
                    reasons.append("MACD 黃金交叉")
                elif osc_now > 0 and osc_now > osc_prev:
                    momentum_score += 5
                    reasons.append("MACD 紅柱擴散增強")
                elif osc_prev >= 0 and osc_now < 0:
                    momentum_score -= 10
                    signals.append("🔴 MACD 死亡交叉 (柱狀圖由正轉負)")
                    red_flags.append("MACD 死亡交叉")
                elif osc_now < 0:
                    momentum_score -= 5
                    
        # 2.3 KD 指標
        k, d, prev_k, prev_d = calculate_kd(self.highs, self.lows, self.prices)
        if k is not None and d is not None:
            if prev_k is not None and prev_d is not None and prev_k < prev_d and k > d:
                if k < 35:
                    momentum_score += 15
                    signals.append(f"[🟢 買進] KD 低檔黃金交叉 (K={k:.1f})")
                    reasons.append("KD 低檔黃金交叉")
                else:
                    momentum_score += 8
                    signals.append(f"[🟢 買進] KD 黃金交叉 (K={k:.1f})")
                    reasons.append("KD 交叉向上")
            elif prev_k is not None and prev_d is not None and prev_k > prev_d and k < d:
                if k > 70:
                    momentum_score -= 15
                    signals.append(f"[🔴 賣出] KD 高檔死亡交叉 (K={k:.1f})")
                    red_flags.append(f"KD 高檔死亡交叉(K={k:.1f})")
                else:
                    momentum_score -= 8
                    signals.append(f"[🔴 賣出] KD 死亡交叉 (K={k:.1f})")
                    
        # 2.4 RSI 指標
        rsi = calculate_rsi(self.prices)
        if rsi is not None:
            if rsi > 75:
                momentum_score -= 15
                signals.append(f"[🔴 賣出] RSI 嚴重超買 ({rsi:.1f})")
                red_flags.append(f"RSI 嚴重超買過熱({rsi:.1f})")
            elif rsi < 30:
                signals.append(f"[🟢 買進] RSI 超賣區 ({rsi:.1f})")
                if current_price >= ma5: # 超賣且短線止跌
                    momentum_score += 10
                    reasons.append(f"RSI 超賣反彈 ({rsi:.1f})")
            elif 48 <= rsi <= 68:
                momentum_score += 5
                
        momentum_score = max(0, min(30, momentum_score))
        
        # ── 風報比與安全空間 (最高 30 分) ────────────────────
        risk_reward_score = 0
        atr = calculate_atr(self.prices, self.highs, self.lows, period=14)
        if not atr or atr <= 0:
            atr = current_price * 0.03
            
        # 支撐與壓力以近20日低點與高點計算
        recent_low = min(self.lows[-20:]) if self.lows else min(self.prices[-20:])
        recent_high = max(self.highs[-20:]) if self.highs else max(self.prices[-20:])
        
        # 距離 20 日結構支撐的乖離下行風險
        chart_downside_pct = (current_price - recent_low) / current_price if current_price > recent_low else 0.02
        
        # 動態操作防守價：兼顧 ATR 短線波動與結構支撐
        atr_stop = current_price - 1.5 * atr
        stop_loss = max(recent_low, atr_stop)
        downside_risk_amount = current_price - stop_loss
        if downside_risk_amount <= 0:
            downside_risk_amount = current_price * 0.02
        downside_pct = downside_risk_amount / current_price
        
        # 上行目標價：
        # 若目前已在或逼近20日最高價(突破型態)，則上行目標為等幅測量滿足點或 2.5*ATR
        if current_price >= recent_high * 0.995:
            box_height = recent_high - recent_low
            upside_target = current_price + max(box_height, 2.5 * atr)
            is_breakout = True
        else:
            upside_target = recent_high
            is_breakout = False
            
        upside_gain_amount = upside_target - current_price
        if upside_gain_amount <= 0:
            upside_gain_amount = current_price * 0.02
        upside_pct = upside_gain_amount / current_price
        
        # 風報比 (Risk-Reward Ratio)
        rrr = upside_gain_amount / downside_risk_amount if downside_risk_amount > 0 else 1.0
        
        # 風報比情境說明加入 signals
        scenario_msg = (f"📊 [情境分析] 上行目標: {upside_target:.2f} (+{upside_pct*100:.1f}%), "
                        f"下行防守: {stop_loss:.2f} (-{downside_pct*100:.1f}%), "
                        f"風報比: {rrr:.2f}")
        if rrr >= 2.0 and chart_downside_pct < 0.10:
            scenario_msg += " ➡️ **風報比優良**"
        elif chart_downside_pct >= 0.10:
            scenario_msg += " ➡️ **⚠️ 下行風險過大 (>10%)**"
        signals.append(scenario_msg)
        
        # 風報比評分
        if rrr >= 2.5:
            risk_reward_score += 30
            reasons.append(f"風報比極佳 ({rrr:.2f})")
        elif rrr >= 2.0:
            risk_reward_score += 24
            reasons.append(f"風報比良好 ({rrr:.2f})")
        elif rrr >= 1.5:
            risk_reward_score += 16
            reasons.append(f"風報比及格 ({rrr:.2f})")
        elif rrr >= 1.0:
            risk_reward_score += 8
        else:
            red_flags.append(f"風報比過低 ({rrr:.2f} < 1.0)，空間受限")
            
        # 結構下行風險扣分
        if chart_downside_pct >= 0.10:
            risk_reward_score = max(0, risk_reward_score - 15)
            red_flags.append(f"下行風險過大 (距20日支撐 {chart_downside_pct*100:.1f}% > 10%)")
        elif chart_downside_pct > 0.07:
            risk_reward_score = max(0, risk_reward_score - 8)
            
        # ── 綜合總分計算 (0 ~ 100) ───────────────────────────
        raw_score = trend_score + momentum_score + risk_reward_score
        
        # ── 一票否決 (Red Flag) 規則 ─────────────────────────
        has_fatal_veto = False
        veto_reasons = []
        
        # 否決 1: 結構下行風險過大且風報比不足 1.8
        if chart_downside_pct >= 0.10 and rrr < 1.8:
            has_fatal_veto = True
            veto_reasons.append("距離結構支撐過遠(>10%)，追高風險大")
            
        # 否決 2: RSI 嚴重超買 (>= 78) 且 KD 高檔死叉
        if rsi is not None and rsi >= 78:
            has_fatal_veto = True
            veto_reasons.append("短線嚴重超買過熱，面臨回檔壓力")
            
        # 否決 3: 價格在月線與季線之下 (長期空頭格局，不作多)
        if current_price < ma20 and current_price < ma60:
            has_fatal_veto = True
            veto_reasons.append("處於月線與季線下方空頭格局")
            
        # 否決 4: 出現明確四大賣點或 MACD 死亡交叉，且風報比不足 2.0
        if bfp_sell and rrr < 2.0:
            has_fatal_veto = True
            veto_reasons.append("觸發技術面實質賣訊")
            
        final_score = raw_score
        if has_fatal_veto and final_score >= 65:
            final_score = 58 if current_price >= ma20 else 40
            
        # ── 產生最終進場裁決 (Verdict) ──────────────────────
        if final_score >= 80 and not has_fatal_veto:
            verdict = "🟢 強烈可進場"
            verdict_badge = "🟢 強烈可進場"
            can_enter = True
        elif final_score >= 65 and not has_fatal_veto:
            verdict = "🟢 可分批進場"
            verdict_badge = "🟢 可分批進場"
            can_enter = True
        elif final_score >= 45:
            verdict = "🟡 暫緩進場 (觀望)"
            verdict_badge = "🟡 建議觀望"
            can_enter = False
        elif final_score >= 30:
            verdict = "🔴 不宜進場 (減碼)"
            verdict_badge = "🔴 不宜進場"
            can_enter = False
        else:
            verdict = "🔴 嚴禁進場 (避開)"
            verdict_badge = "🔴 嚴禁進場"
            can_enter = False
            
        # 建議進場策略
        if can_enter:
            if is_breakout:
                suggested_entry = f"突破確認 ({current_price:.2f} 附近，或小幅回測 5MA)"
            else:
                suggested_entry = f"現價 ({current_price:.2f}) 或回測 MA5 ({ma5:.2f}) 附近分批承接"
        else:
            if final_score >= 45:
                suggested_entry = f"暫緩進場，待突破 {recent_high:.2f} 或回測守穩 {ma20:.2f} 再評估"
            else:
                suggested_entry = "嚴禁追高，持股者逢反彈減碼或嚴守停損"
                
        return {
            "can_enter": can_enter,
            "verdict": verdict,
            "verdict_badge": verdict_badge,
            "score": final_score,
            "trend_score": trend_score,
            "momentum_score": momentum_score,
            "risk_reward_score": risk_reward_score,
            "rrr": rrr,
            "upside_target": upside_target,
            "upside_pct": upside_pct,
            "downside_risk": stop_loss,
            "downside_pct": downside_pct,
            "stop_loss": stop_loss,
            "suggested_entry": suggested_entry,
            "red_flags": red_flags + veto_reasons,
            "reasons": reasons,
            "signals": signals
        }
        
    def _fallback_result(self, reason):
        return {
            "can_enter": False,
            "verdict": "🟡 暫緩進場 (資料不足)",
            "verdict_badge": "🟡 資料不足",
            "score": 50,
            "trend_score": 0,
            "momentum_score": 0,
            "risk_reward_score": 0,
            "rrr": 1.0,
            "upside_target": 0.0,
            "upside_pct": 0.0,
            "downside_risk": 0.0,
            "downside_pct": 0.0,
            "stop_loss": 0.0,
            "suggested_entry": "無足夠數據，維持觀望",
            "red_flags": [reason],
            "reasons": [],
            "signals": []
        }


class MarketRegimeEvaluator:
    """
    市場大盤進場環境評估器 (Market Regime Evaluator)
    綜合統計觀察名單與權值核心標的之多空廣度，回答：
    「今日整體台股環境是否適合進場？建議總曝險/持倉水位是多少？」
    """
    def __init__(self, evaluations):
        """
        evaluations: list of dict, 每個元素包含:
          {
            "code": str,
            "name": str,
            "price": float,
            "eval": dict (from EntryEvaluator.evaluate())
          }
        """
        self.evaluations = evaluations
        
    def evaluate_market(self):
        total = len(self.evaluations)
        if total == 0:
            return {
                "market_verdict": "🟡 觀望等待",
                "can_enter_market": False,
                "suggested_exposure": "0% ~ 20%",
                "bull_ratio_ma20": 0.0,
                "bull_ratio_ma60": 0.0,
                "buy_count": 0,
                "wait_count": 0,
                "sell_count": 0,
                "summary": "無足夠市場資料評估。"
            }
            
        above_ma20_cnt = 0
        above_ma60_cnt = 0
        buy_cnt = 0
        wait_cnt = 0
        sell_cnt = 0
        avg_score = 0.0
        
        top_picks = []
        avoid_picks = []
        
        for item in self.evaluations:
            e = item.get("eval", {})
            score = e.get("score", 50)
            avg_score += score
            
            if e.get("can_enter"):
                buy_cnt += 1
                top_picks.append(item)
            elif "不宜" in e.get("verdict", "") or "嚴禁" in e.get("verdict", ""):
                sell_cnt += 1
                avoid_picks.append(item)
            else:
                wait_cnt += 1
                
            # 統計趨勢
            trend_s = e.get("trend_score", 0)
            if trend_s >= 15: # 至少站上 MA20
                above_ma20_cnt += 1
            if trend_s >= 30: # 站上 MA20 且 MA60
                above_ma60_cnt += 1
                
        avg_score /= total
        bull_ratio_ma20 = (above_ma20_cnt / total) * 100
        bull_ratio_ma60 = (above_ma60_cnt / total) * 100
        buy_ratio = (buy_cnt / total) * 100
        
        # 依分數排序 top_picks (最高分者優先)
        top_picks.sort(key=lambda x: x["eval"].get("score", 0), reverse=True)
        avoid_picks.sort(key=lambda x: x["eval"].get("score", 0))
        
        # 綜合評定大盤環境與建議資金水位
        if bull_ratio_ma20 >= 65 and avg_score >= 65:
            market_verdict = "🟢 適合進場 (全面多頭動能)"
            can_enter_market = True
            suggested_exposure = "70% ~ 85%"
            summary = (f"大盤多頭結構完整，{bull_ratio_ma20:.0f}% 標的維持在月線之上，"
                       f"市場具備良好賺錢效應，適合積極挑選具風報比優勢標的進場。")
        elif bull_ratio_ma20 >= 50 or (buy_cnt >= 2 and avg_score >= 55):
            market_verdict = "🟢 謹慎選股進場 (震盪偏多)"
            can_enter_market = True
            suggested_exposure = "40% ~ 60%"
            summary = (f"大盤呈現高檔震盪或類股輪動，{bull_ratio_ma20:.0f}% 標的位於月線上。"
                       f"可精選符合進場標準的強勢股逢低分批佈局，切忌盲目追高。")
        elif bull_ratio_ma20 >= 35:
            market_verdict = "🟡 暫緩進場 (多空拉鋸觀望)"
            can_enter_market = False
            suggested_exposure = "20% ~ 35%"
            summary = (f"市場多空分歧加劇，僅 {bull_ratio_ma20:.0f}% 標的站上月線，"
                       f"技術指標普遍呈現矛盾或高檔鈍化，建議保留現金，以觀望為主。")
        else:
            market_verdict = "🔴 嚴禁進場 (空頭修正防禦)"
            can_enter_market = False
            suggested_exposure = "0% ~ 15%"
            summary = (f"盤勢轉弱，多數個股跌破關鍵支撐，下行風險擴大。"
                       f"嚴禁進場追價，現有持股應嚴設停損或逢高減碼保全資本。")
            
        return {
            "market_verdict": market_verdict,
            "can_enter_market": can_enter_market,
            "suggested_exposure": suggested_exposure,
            "bull_ratio_ma20": bull_ratio_ma20,
            "bull_ratio_ma60": bull_ratio_ma60,
            "avg_score": avg_score,
            "buy_count": buy_cnt,
            "wait_count": wait_cnt,
            "sell_count": sell_cnt,
            "total_count": total,
            "top_picks": top_picks,
            "avoid_picks": avoid_picks,
            "summary": summary
        }
