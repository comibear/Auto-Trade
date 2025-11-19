# futures_trader.py
import asyncio
import logging
from typing import Optional, Dict, Any, List, Union

# Binance USDⓈ-M Futures SDK (modular)
from binance_sdk_derivatives_trading_usds_futures.derivatives_trading_usds_futures import (
    DerivativesTradingUsdsFutures,
)

logger = logging.getLogger("futures.trader")

class FuturesTrader:
    """
    Binance USDⓈ-M Futures REST Trade 래퍼.
    SDK 내부 네이밍(예: client.trade.new_order 등)은 모듈 버전에 따라 다릅니다.
    아래는 가장 일반적인 패턴:
      client.trade.new_order(...)
      client.trade.cancel_order(...)
      client.trade.query_order(...)
      client.account.change_leverage(...)
      client.account.change_margin_type(...)
      client.account.get_position_risk(...)
    만약 네 SDK 버전에서 속성 경로가 다르면, 동일한 메서드명을 가진
    하위 네임스페이스를 찾아 넣어주면 됩니다(예: client.http_api.trade.new_order).
    """

    def __init__(self, client: DerivativesTradingUsdsFutures, recv_window: int = 5000):
        self.client = client
        self.recv_window = recv_window

        # 추정 네임스페이스 바인딩(버전 차이 호환): 최초 1회 동적으로 보정
        self._trade = getattr(client, "trade", None) or getattr(client, "http_api", None)
        self._account = getattr(client, "account", None) or getattr(client, "http_api", None)
        if self._trade is None or self._account is None:
            raise RuntimeError("SDK 구조를 확인하세요: trade/account 네임스페이스를 찾을 수 없습니다.")

    # ---------- 계좌 세팅 ----------
    async def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """
        POST /fapi/v1/leverage
        """
        leverage = max(1, min(leverage, 125))
        try:
            resp = await self._account.change_leverage(
                symbol=symbol,
                leverage=leverage,
                recvWindow=self.recv_window,
            )
            data = resp.data().to_dict() if hasattr(resp, "data") else resp
            logger.info(f"[leverage] {symbol} -> x{data.get('leverage', leverage)}")
            return data
        except Exception as e:
            logger.exception(f"[leverage] error: {symbol}, x{leverage}: {e}")
            raise

    async def set_margin_type(self, symbol: str, margin_type: str) -> Dict[str, Any]:
        """
        POST /fapi/v1/marginType
        margin_type: 'ISOLATED' | 'CROSSED'
        """
        margin_type = margin_type.upper()
        if margin_type not in ("ISOLATED", "CROSSED"):
            raise ValueError("margin_type must be 'ISOLATED' or 'CROSSED'")
        try:
            resp = await self._account.change_margin_type(
                symbol=symbol,
                marginType=margin_type,
                recvWindow=self.recv_window,
            )
            data = resp.data().to_dict() if hasattr(resp, "data") else resp
            logger.info(f"[marginType] {symbol} -> {margin_type}")
            return data
        except Exception as e:
            logger.exception(f"[marginType] error: {symbol}, {margin_type}: {e}")
            raise

    # ---------- 주문 ----------
    async def place_order(
        self,
        symbol: str,
        side: str,
        type: str,
        quantity: Optional[Union[float, str]] = None,
        price: Optional[Union[float, str]] = None,
        time_in_force: Optional[str] = None,   # GTC/IOC/FOK
        reduce_only: Optional[bool] = None,
        position_side: Optional[str] = None,   # BOTH/LONG/SHORT (hedge 모드)
        new_client_order_id: Optional[str] = None,
        stop_price: Optional[Union[float, str]] = None,       # STOP/TAKE_PROFIT/STOP_MARKET/TAKE_PROFIT_MARKET
        close_position: Optional[bool] = None, # *MARKET + close_position=True for full close
        working_type: Optional[str] = None,    # MARK_PRICE | CONTRACT_PRICE
        price_protect: Optional[bool] = None,  # True/False
        callback_rate: Optional[float] = None, # TRAILING_STOP_MARKET
        activation_price: Optional[float] = None, # TRAILING_STOP_MARKET activation
        recv_window: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        POST /fapi/v1/order  (TRADE, SIGNED)
        문서: New Order (USDⓈ-M Futures). side: BUY/SELL, type 예시: MARKET/LIMIT/STOP/STOP_MARKET/TAKE_PROFIT/TAKE_PROFIT_MARKET/TRAILING_STOP_MARKET
        권장:
          - LIMIT엔 timeInForce 기본값 'GTC'
          - 시장가 청산은 type='MARKET', reduceOnly=True 또는 closePosition=True
        """
        params: Dict[str, Any] = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": type.upper(),
            "recvWindow": recv_window or self.recv_window,
        }
        if quantity is not None:
            params["quantity"] = quantity
        if price is not None:
            params["price"] = price
        if time_in_force:
            params["timeInForce"] = time_in_force
        if reduce_only is not None:
            params["reduceOnly"] = "true" if reduce_only else "false"
        if position_side:
            params["positionSide"] = position_side.upper()
        if new_client_order_id:
            params["newClientOrderId"] = new_client_order_id
        if stop_price is not None:
            params["stopPrice"] = stop_price
        if close_position is not None:
            params["closePosition"] = "true" if close_position else "false"
        if working_type:
            params["workingType"] = working_type
        if price_protect is not None:
            params["priceProtect"] = "true" if price_protect else "false"
        if callback_rate is not None:
            params["callbackRate"] = callback_rate
        if activation_price is not None:
            params["activationPrice"] = activation_price

        # LIMIT일 때 기본 TIF
        if params["type"] == "LIMIT" and "timeInForce" not in params:
            params["timeInForce"] = "GTC"

        try:
            resp = await self._trade.new_order(**params)
            data = resp.data().to_dict() if hasattr(resp, "data") else resp
            oid = data.get("orderId")
            status = data.get("status")
            logger.info(f"[order] {symbol} {params['side']} {params['type']} q={params.get('quantity')} p={params.get('price')} -> id={oid} status={status}")
            return data
        except Exception as e:
            logger.exception(f"[order] error: {params}: {e}")
            raise

    async def place_batch_orders(self, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        POST /fapi/v1/batchOrders
        각 원소는 New Order와 동일 파라미터. 반환 순서는 요청 순서와 동일. 동시 처리 주의. 
        """
        try:
            resp = await self._trade.batch_orders(
                batchOrders=orders,
                recvWindow=self.recv_window,
            )
            data = resp.data().to_dict() if hasattr(resp, "data") else resp
            logger.info(f"[batchOrders] n={len(orders)}")
            return data
        except Exception as e:
            logger.exception(f"[batchOrders] error: {e}")
            raise

    async def cancel_order(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        orig_client_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        DELETE /fapi/v1/order
        """
        if not order_id and not orig_client_order_id:
            raise ValueError("order_id 또는 orig_client_order_id 중 하나는 필요합니다.")
        try:
            resp = await self._trade.cancel_order(
                symbol=symbol.upper(),
                orderId=order_id,
                origClientOrderId=orig_client_order_id,
                recvWindow=self.recv_window,
            )
            data = resp.data().to_dict() if hasattr(resp, "data") else resp
            logger.info(f"[cancel] {symbol} id={order_id or orig_client_order_id} -> {data.get('status')}")
            return data
        except Exception as e:
            logger.exception(f"[cancel] error: {symbol}, {order_id or orig_client_order_id}: {e}")
            raise

    async def cancel_all_open_orders(self, symbol: str) -> Dict[str, Any]:
        """
        DELETE /fapi/v1/allOpenOrders
        """
        try:
            resp = await self._trade.cancel_all_open_orders(
                symbol=symbol.upper(),
                recvWindow=self.recv_window,
            )
            data = resp.data().to_dict() if hasattr(resp, "data") else resp
            logger.info(f"[cancelAll] {symbol} -> {data}")
            return data
        except Exception as e:
            logger.exception(f"[cancelAll] error: {symbol}: {e}")
            raise

    # ---------- 조회 ----------
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        GET /fapi/v1/openOrders
        """
        try:
            resp = await self._trade.open_orders(
                symbol=symbol.upper() if symbol else None,
                recvWindow=self.recv_window,
            )
            data = resp.data().to_dict() if hasattr(resp, "data") else resp
            return data
        except Exception as e:
            logger.exception(f"[openOrders] error: {symbol}: {e}")
            raise

    async def query_order(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        orig_client_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        GET /fapi/v1/order
        """
        try:
            resp = await self._trade.query_order(
                symbol=symbol.upper(),
                orderId=order_id,
                origClientOrderId=orig_client_order_id,
                recvWindow=self.recv_window,
            )
            data = resp.data().to_dict() if hasattr(resp, "data") else resp
            return data
        except Exception as e:
            logger.exception(f"[queryOrder] error: {symbol}, {order_id or orig_client_order_id}: {e}")
            raise

    async def get_position_info(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        GET /fapi/v2/positionRisk
        """
        try:
            resp = await getattr(self._account, "position_risk")(
                symbol=symbol.upper() if symbol else None,
                recvWindow=self.recv_window,
            )
            data = resp.data().to_dict() if hasattr(resp, "data") else resp
            return data
        except Exception as e:
            logger.exception(f"[positionRisk] error: {symbol}: {e}")
            raise

    # ---------- 편의 메서드 ----------
    async def market_buy(
        self, symbol: str, qty: Union[float, str], reduce_only: bool = False, position_side: Optional[str] = None
    ):
        return await self.place_order(
            symbol=symbol, side="BUY", type="MARKET",
            quantity=qty, reduce_only=reduce_only, position_side=position_side
        )

    async def market_sell(
        self, symbol: str, qty: Union[float, str], reduce_only: bool = False, position_side: Optional[str] = None
    ):
        return await self.place_order(
            symbol=symbol, side="SELL", type="MARKET",
            quantity=qty, reduce_only=reduce_only, position_side=position_side
        )

    async def limit(
        self, symbol: str, side: str, qty: Union[float, str], price: Union[float, str], tif: str = "GTC", reduce_only: bool = False, position_side: Optional[str] = None
    ):
        return await self.place_order(
            symbol=symbol, side=side, type="LIMIT",
            quantity=qty, price=price, time_in_force=tif,
            reduce_only=reduce_only, position_side=position_side
        )

    async def stop_market(
        self, symbol: str, side: str, stop_price: Union[float, str], close_position: bool = False,
        reduce_only: Optional[bool] = None, position_side: Optional[str] = None, working_type: str = "MARK_PRICE"
    ):
        return await self.place_order(
            symbol=symbol, side=side, type="STOP_MARKET",
            stop_price=stop_price, close_position=close_position,
            reduce_only=reduce_only, position_side=position_side, working_type=working_type
        )

    async def take_profit_market(
        self, symbol: str, side: str, stop_price: Union[float, str], close_position: bool = False,
        reduce_only: Optional[bool] = None, position_side: Optional[str] = None, working_type: str = "MARK_PRICE"
    ):
        return await self.place_order(
            symbol=symbol, side=side, type="TAKE_PROFIT_MARKET",
            stop_price=stop_price, close_position=close_position,
            reduce_only=reduce_only, position_side=position_side, working_type=working_type
        )
