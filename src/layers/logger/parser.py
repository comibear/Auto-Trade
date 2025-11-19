# parser.py
from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Any, Dict, List, Optional

_MS = 1000

def _ts(ms: int) -> str:
    # 로컬 타임스탬프(YYYY-MM-DD HH:MM:SS)
    return dt.datetime.fromtimestamp(ms / _MS).strftime("%Y-%m-%d %H:%M:%S")

def _d(x: Any) -> Decimal:
    # Binance는 숫자를 문자열로 주는 경우가 많음
    try:
        return Decimal(str(x))
    except Exception:
        return Decimal(0)

def _fmt_usd(x: Any) -> str:
    q = _d(x)
    # 큰 금액/작은 금액 가독성
    if abs(q) >= 1000:
        return f"${q:,.2f}"
    if abs(q) >= Decimal("0.01"):
        return f"${q:.2f}"
    return f"${q:.6f}"

def _fmt_num(x: Any) -> str:
    q = _d(x)
    if abs(q) >= 1:
        return f"{q:,.4f}"
    return f"{q:.8f}"

def _side_emoji(side: str) -> str:
    return "🟢" if side.upper() == "BUY" else "🔴"

def _pos_side_emoji(ps: str) -> str:
    # BOTH (단일), LONG, SHORT
    m = {"BOTH": "↔️", "LONG": "⬆️", "SHORT": "⬇️"}
    return m.get(ps.upper(), "↔️")

def _order_status_emoji(s: str) -> str:
    m = {
        "NEW": "🆕", "PARTIALLY_FILLED": "🧩", "FILLED": "✅",
        "CANCELED": "🚫", "EXPIRED": "⏳", "REJECTED": "❌"
    }
    return m.get(s.upper(), "ℹ️")

def _reason_emoji(m: str) -> str:
    # ACCOUNT_UPDATE reason
    m = (m or "").upper()
    if m == "ORDER":
        return "🧾"
    if m == "FUNDING_FEE":
        return "💸"
    if m == "WITHDRAW" or m == "DEPOSIT" or m == "TRANSFER":
        return "💼"
    if m == "ADL":
        return "⚠️"
    return "🛠️"

class FuturesEventParser:
    """
    handle(payload: dict) -> str
    Binance USDⓈ-M 사용자 데이터 스트림 이벤트를 읽기 쉬운 요약 메시지로 변환.

    지원 이벤트:
      - ORDER_TRADE_UPDATE (주문/체결 업데이트)
      - TRADE_LITE (경량 체결 스트림)
      - ACCOUNT_UPDATE (잔고/포지션/마진 타입 변경)
      - MARGIN_CALL (마진 콜 경고)
      - ACCOUNT_CONFIG_UPDATE (레버리지/모드 변경)
    문서:
      - User Data Streams: https://developers.binance.com/docs/derivatives/usds-margined-futures/user-data-streams
      - ORDER_TRADE_UPDATE: https://developers.binance.com/docs/derivatives/usds-margined-futures/user-data-streams/Event-Order-Update
      - ACCOUNT_UPDATE: https://developers.binance.com/docs/derivatives/usds-margined-futures/user-data-streams/Event-Balance-and-Position-Update
      - TRADE_LITE: https://developers.binance.com/docs/derivatives/usds-margined-futures/user-data-streams/Event-Trade-Lite
      - ACCOUNT_CONFIG_UPDATE (레버리지): https://developers.binance.com/docs/derivatives/portfolio-margin/user-data-streams/Event-Futures-Account-Configuration-Update
    """

    def handle(self, payload: Dict[str, Any]) -> Optional[str]:
        if not isinstance(payload, dict):
            return None

        etype = payload.get("e") or payload.get("event", {}).get("e")
        if not etype:
            # 불명 이벤트 (무시)
            return None

        etype = str(etype)

        try:
            if etype == "ORDER_TRADE_UPDATE":
                return self._order_trade_update(payload)
            if etype == "TRADE_LITE":
                return self._trade_lite(payload)
            if etype == "ACCOUNT_UPDATE":
                return self._account_update(payload)
            if etype == "MARGIN_CALL":
                return self._margin_call(payload)
            if etype == "ACCOUNT_CONFIG_UPDATE":
                return self._account_config_update(payload)
            if etype == "eventStreamTerminated":
                e = payload.get("E") or payload.get("event", {}).get("E")
                return f"🔌 Stream terminated | at={_ts(int(e)) if e else 'N/A'}"
            # 기타 이벤트: 원문 축약 표시
            return f"ℹ️ {etype} | {self._short(payload)}"
        except Exception as e:
            # 파싱 에러 시 원문 일부와 함께 반환
            raw = self._short(payload)
            return f"⚠️ parser error: {e} | raw={raw}"

    # ---------- EVENT HANDLERS ----------

    def _order_trade_update(self, p: Dict[str, Any]) -> str:
        """
        구조(요지):
        {
          "e":"ORDER_TRADE_UPDATE","E":..., "T":..., 
          "o":{
             "s":"BTCUSDT","S":"BUY/SELL","ps":"BOTH/LONG/SHORT",
             "X":"NEW/FILLED/... (orderStatus)", "x":"TRADE/NEW/... (executionType)",
             "q":"origQty","z":"cumQty","Z":"cumQuote",
             "p":"price","ap":"avgPrice","L":"lastPrice",
             "l":"lastQty","N":"commissionAsset","n":"commission",
             "rp":"realizedPnL","ot":"orderType","t":"tradeId", "i":"orderId", ...
          }
        }
        """
        E = p.get("E")
        o = p.get("o", {})
        sym = o.get("s")
        side = (o.get("S") or "").upper()
        ps = (o.get("ps") or "BOTH").upper()
        x = (o.get("x") or "").upper()          # executionType
        X = (o.get("X") or "").upper()          # orderStatus
        typ = (o.get("ot") or "").upper()

        # 수량/가격
        lqty = o.get("l")   # last filled qty
        lpx  = o.get("L")   # last price
        avg  = o.get("ap")  # average fill price
        oq   = o.get("q")   # original qty
        z    = o.get("z")   # cumulative filled
        rp   = o.get("rp")  # realized PnL (execution 기준)
        fee_a = o.get("N")  # commission asset
        fee   = o.get("n")  # commission amount

        head = f"{_side_emoji(side)} [ORDER] {sym} | {side} {typ} | st={_order_status_emoji(X)} {X} / ex={x} · pos={_pos_side_emoji(ps)} {ps}"
        lines = [head, f"🕒 {_ts(int(E)) if E else 'N/A'}"]

        # 체결이 있었을 때 핵심
        if x == "TRADE" or _d(lqty) > 0:
            trade_line = f"• last={_fmt_num(lqty)} @ {_fmt_num(lpx)}"
            if _d(avg) > 0:
                trade_line += f" | avg={_fmt_num(avg)}"
            trade_line += f" | cum={_fmt_num(z)}/{_fmt_num(oq)}"
            lines.append(trade_line)

            # 수수료 / 실현손익
            tail = []
            if fee and _d(fee) != 0:
                tail.append(f"fee={_fmt_num(fee)} {fee_a or ''}".strip())
            if rp and _d(rp) != 0:
                # realized PnL는 통화가 quote(USDT) 기준
                pnl_emoji = "📈" if _d(rp) > 0 else "📉"
                tail.append(f"rp={pnl_emoji} {_fmt_usd(rp)}")
            if tail:
                lines.append("• " + " | ".join(tail))
        else:
            # 체결 없는 상태 변경 NEW/EXPIRED/CANCELED 등
            qty_part = f"qty={_fmt_num(oq)}"
            if _d(z) > 0:
                qty_part += f" (filled={_fmt_num(z)})"
            px = o.get("p")
            if _d(px) > 0:
                qty_part += f" @ {_fmt_num(px)}"
            lines.append("• " + qty_part)

        # 유용한 플래그들 (감지되면 붙임)
        flags = []
        if str(o.get("wt", "")).upper() == "CONTRACT_PRICE":
            flags.append("trigger=Mark")
        if str(o.get("wt", "")).upper() == "LAST_PRICE":
            flags.append("trigger=Last")
        if str(o.get("wt", "")).upper() == "INDEX_PRICE":
            flags.append("trigger=Index")
        if o.get("AP"):
            flags.append(f"trailingAP={_fmt_num(o['AP'])}")
        if o.get("cr"):
            flags.append(f"trailingCR={_fmt_num(o['cr'])}")
        if o.get("cp") == True:
            flags.append("close-all")
        if flags:
            lines.append("• " + ", ".join(flags))

        return "\n".join(lines)

    def _trade_lite(self, p: Dict[str, Any]) -> str:
        """
        TRADE_LITE는 TRADE execution만 푸시, 필드 축소.
        예: {"e":"TRADE_LITE","E":...,"o":{"s":"BTCUSDT","S":"BUY","ps":"BOTH","L":"price","l":"qty","ap":"avg","z":"cum"}}
        """
        E = p.get("E")
        o = p.get("o", {})
        sym = o.get("s")
        side = (o.get("S") or "").upper()
        ps = (o.get("ps") or "BOTH").upper()
        lqty = o.get("l")
        lpx = o.get("L")
        avg = o.get("ap")
        z = o.get("z")

        lines = [
            f"{_side_emoji(side)} [TRADE] {sym} · pos={_pos_side_emoji(ps)} {ps}",
            f"🕒 {_ts(int(E)) if E else 'N/A'}",
            f"• last={_fmt_num(lqty)} @ {_fmt_num(lpx)} | cum={_fmt_num(z)}"
            + (f" | avg={_fmt_num(avg)}" if _d(avg) > 0 else "")
        ]
        return "\n".join(lines)

    def _account_update(self, p: Dict[str, Any]) -> str:
        """
        ACCOUNT_UPDATE: 잔고/포지션/마진타입 변경.
        구조(요지):
        {
          "e":"ACCOUNT_UPDATE","E":...,
          "a": {
             "m":"ORDER/FUNDING_FEE/..(reason)",
             "B":[{"a":"USDT","wb":"walletBalance","cw":"crossWallet"}...],
             "P":[{"s":"BTCUSDT","pa":"positionAmt","ep":"entryPrice","up":"unrealizedPnL",
                   "ps":"BOTH/LONG/SHORT","mt":"CROSSED/ISOLATED","iw":"isolatedWallet"}...]
          }
        }
        """
        E = p.get("E")
        a = p.get("a", {})
        reason = a.get("m", "")
        head = f"{_reason_emoji(reason)} [ACCOUNT] reason={reason or 'N/A'}"
        lines = [head, f"🕒 {_ts(int(E)) if E else 'N/A'}"]

        # 잔고 변화 요약(주요 코인만 표시: USDT/BNB)
        bs = a.get("B", [])
        if bs:
            # 변화량 유추가 불가하므로 스냅샷 형태 요약
            focus = []
            for b in bs:
                asset = b.get("a")
                if asset in ("USDT", "BNB"):
                    focus.append(f"{asset}: wallet={_fmt_num(b.get('wb'))}, cross={_fmt_num(b.get('cw'))}")
            if focus:
                lines.append("• balances | " + " | ".join(focus))

        # 포지션 변화: 심볼별 핵심
        ps = a.get("P", [])
        for pos in ps:
            sym = pos.get("s")
            amt = _d(pos.get("pa"))
            if amt == 0 and _d(pos.get("up")) == 0 and _d(pos.get("iw")) == 0:
                # 완전 청산/미보유 상태는 간략 표기
                lines.append(f"• {sym}: flat")
                continue

            ep = pos.get("ep")
            up = pos.get("up")
            psd = pos.get("ps", "BOTH")
            mt = pos.get("mt")  # CROSSED/ISOLATED
            iw = pos.get("iw")  # isolated wallet
            part = [
                f"{sym} {_pos_side_emoji(psd)}",
                f"size={_fmt_num(amt)} @ {_fmt_num(ep)}",
                f"uPnL={_fmt_usd(up)}",
                f"margin={mt or '-'}",
            ]
            if _d(iw) != 0:
                part.append(f"iw={_fmt_usd(iw)}")
            lines.append("• " + " | ".join(part))

        # FUNDING_FEE 간략 강조
        if (reason or "").upper() == "FUNDING_FEE":
            lines.append("• funding fee applied 💸")

        return "\n".join(lines)

    def _margin_call(self, p: Dict[str, Any]) -> str:
        """
        MARGIN_CALL: 유지증거금 부족 위험 경보
        구조(요지):
        {"e":"MARGIN_CALL","E":...,"cw":"crossWalletBalance","p":[
           {"s":"BTCUSDT","ps":"BOTH/LONG/SHORT","pa":"positionAmt","mt":"CROSSED/ISOLATED","iw":"isolatedWallet","mp":"markPrice","up":"unrealizedPnL","mm":"maintMargin"}...
        ]}
        """
        E = p.get("E")
        cw = p.get("cw")
        positions = p.get("p", [])

        lines = [f"🚨 [MARGIN CALL] crossWallet={_fmt_usd(cw)}", f"🕒 {_ts(int(E)) if E else 'N/A'}"]
        for pos in positions:
            sym = pos.get("s")
            psd = pos.get("ps", "BOTH")
            amt = pos.get("pa")
            mp = pos.get("mp")
            up = pos.get("up")
            mm = pos.get("mm")
            mt = pos.get("mt")
            iw = pos.get("iw")
            lines.append(
                "• "
                + f"{sym} {_pos_side_emoji(psd)} size={_fmt_num(amt)} | mark={_fmt_num(mp)} | uPnL={_fmt_usd(up)} | mm={_fmt_usd(mm)} | {mt}"
                + (f" | iw={_fmt_usd(iw)}" if _d(iw) != 0 else "")
            )
        lines.append("• Action: reduce risk / add margin / close exposure")
        return "\n".join(lines)

    def _account_config_update(self, p: Dict[str, Any]) -> str:
        """
        ACCOUNT_CONFIG_UPDATE: 레버리지/모드 변경
        구조(요지):
        {
          "e":"ACCOUNT_CONFIG_UPDATE","E":...,
          "ac":{"s":"BTCUSDT","l":25},         # 심볼별 레버리지 변경
          "ai":{"j":"true/false","l":"BOTH"}   # dual position 등 계정 설정
        }
        """
        E = p.get("E")
        ac = p.get("ac")
        ai = p.get("ai")

        lines = [f"🛠️ [CONFIG]", f"🕒 {_ts(int(E)) if E else 'N/A'}"]
        if ac:
            sym = ac.get("s")
            lev = ac.get("l")
            lines.append(f"• leverage: {sym} -> x{lev}")
        if ai:
            dual = ai.get("j")
            mode = ai.get("l")
            if dual is not None:
                lines.append(f"• dualPositionMode: {dual}")
            if mode:
                lines.append(f"• mode: {mode}")
        return "\n".join(lines)

    # ---------- UTILS ----------

    def _short(self, p: Dict[str, Any], limit: int = 280) -> str:
        """
        원문 dict를 한 줄 요약(로그 보호용)
        """
        try:
            import json
            s = json.dumps(p, separators=(",", ":"), ensure_ascii=False)
        except Exception:
            s = str(p)
        if len(s) > limit:
            s = s[:limit] + "…"
        return s
