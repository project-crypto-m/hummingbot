import asyncio
import json
import time
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from hummingbot.connector.exchange.swaphere.swaphere_constants import (
    SWAPHERE_BASE_URL,
    SWAPHERE_PRODUCTS_PATH,
    SWAPHERE_PRODUCT_BOOK_PATH,
    SWAPHERE_PLACE_ORDER_PATH,
    SWAPHERE_ORDERS_PATH,
    SWAPHERE_ORDER_CANCEL_PATH,
    SWAPHERE_ORDERBOOK_PATH,
    ORDER_STATE,
    ORDER_TYPE_MAP,
    CLIENT_ID_PREFIX,
    DEFAULT_BLOCKCHAIN_CONTEXT
)
from hummingbot.connector.exchange.swaphere.swaphere_auth import SwaphereAuth
from hummingbot.connector.exchange_base import ExchangeBase
from hummingbot.connector.trading_rule import TradingRule
from hummingbot.core.data_type.cancellation_result import CancellationResult
from hummingbot.core.data_type.common import OrderType, TradeType
from hummingbot.core.data_type.in_flight_order import InFlightOrder, OrderState, OrderUpdate, TradeUpdate
from hummingbot.core.data_type.trade_fee import TokenAmount, TradeFeeBase, AddedToCostTradeFee
from hummingbot.core.utils.async_utils import safe_gather, safe_ensure_future
from hummingbot.core.web_assistant.connections.data_types import RESTMethod
from hummingbot.core.web_assistant.rest_assistant import RESTAssistant
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory
from hummingbot.connector.exchange.swaphere.swaphere_utils import get_new_client_order_id
from hummingbot.core.data_type.order_book import OrderBook


class SwaphereExchange(ExchangeBase):
    def __init__(
        self,
        private_key: str,
        trading_pairs: List[str] = None,
        trading_required: bool = True,
        client_config_map = None
    ):
        super().__init__(client_config_map)
        self._private_key = private_key
        self._trading_pairs = trading_pairs or []
        self._trading_required = trading_required
        
        self._auth = SwaphereAuth(private_key)
        self._web_assistants_factory = WebAssistantsFactory(auth=self._auth)
        self._rest_assistant = None
        
        # In-flight order management
        self._in_flight_orders = {}
        self._trading_rules = {}
        
        # Token information (to be fetched from API or set manually)
        self._tokens = {}
        
        # Blockchain context for signing orders
        self._blockchain_context = DEFAULT_BLOCKCHAIN_CONTEXT
        
        # Order book management
        self._order_books = {}
        self._order_book_tracker = None  # Would be implemented with a proper OrderBookTracker
        
        # Account balances
        self._account_balances = {}
        self._account_available_balances = {}
        
    @property
    def name(self) -> str:
        return "swaphere"
        
    @property
    def order_books(self) -> Dict[str, OrderBook]:
        return self._order_books
        
    @property
    def limit_orders(self) -> List[Any]:
        return [o for o in self._in_flight_orders.values() if o.is_open]
        
    async def start_network(self):
        """Start network and initialize connections."""
        self._rest_assistant = await self._web_assistants_factory.get_rest_assistant()
        await self._update_trading_rules()
        # Initialize token information if trading is required
        if self._trading_required:
            await self._fetch_tokens()
            await self._update_balances()
        
    async def stop_network(self):
        """Stop network and close connections."""
        # Perform any cleanup operations here
        pass
        
    async def check_network(self) -> bool:
        """Check if the exchange is online and working properly."""
        try:
            # Use products endpoint to check network
            await self._api_request(RESTMethod.GET, SWAPHERE_PRODUCTS_PATH)
            return True
        except Exception:
            return False
            
    async def get_order_book(self, trading_pair: str) -> Dict[str, Any]:
        """Get order book for a specific trading pair."""
        path = SWAPHERE_PRODUCT_BOOK_PATH.format(trading_pair)
        params = {"level": 2}  # Default depth level
        response = await self._api_request(RESTMethod.GET, path, params=params)
        return response
        
    async def get_trading_rules(self) -> Dict[str, TradingRule]:
        """Get trading rules for all trading pairs."""
        return self._trading_rules
        
    async def _update_trading_rules(self):
        """Update trading rules from the exchange."""
        products_info = await self._api_request(RESTMethod.GET, SWAPHERE_PRODUCTS_PATH)
        trading_rules = {}
        
        for product in products_info:
            try:
                trading_pair = product["id"]
                base_min_size = Decimal(product.get("baseMinSize", "0"))
                base_max_size = Decimal(product.get("baseMaxSize", "9999999"))
                quote_increment = Decimal(product.get("quoteIncrement", "0.00000001"))
                base_scale = product.get("baseScale", 8)
                quote_scale = product.get("quoteScale", 8)
                
                # Calculate min notional and other constraints from the scales
                min_price_increment = Decimal(10) ** -quote_scale
                min_base_amount_increment = Decimal(10) ** -base_scale
                
                trading_rules[trading_pair] = TradingRule(
                    trading_pair=trading_pair,
                    min_order_size=base_min_size,
                    max_order_size=base_max_size,
                    min_price_increment=min_price_increment,
                    min_base_amount_increment=min_base_amount_increment,
                )
            except Exception as e:
                self.logger().error(f"Error parsing trading pair rule {product}. Error: {e}")
                
        self._trading_rules = trading_rules
        
    async def _fetch_tokens(self):
        """Fetch token information from the exchange"""
        # Get products to derive token information
        products = await self._api_request(RESTMethod.GET, SWAPHERE_PRODUCTS_PATH)
        
        for product in products:
            base_currency = product["baseCurrency"]
            quote_currency = product["quoteCurrency"]
            base_scale = product.get("baseScale", 18)
            quote_scale = product.get("quoteScale", 18)
            
            # Store token information for both base and quote (simplified for demo)
            # In real implementation, you'd want to fetch actual token contracts
            if base_currency not in self._tokens:
                self._tokens[base_currency] = {
                    "address": f"0x{base_currency}000000000000000000000000000000000000",  # Placeholder
                    "decimal": base_scale
                }
            
            if quote_currency not in self._tokens:
                self._tokens[quote_currency] = {
                    "address": f"0x{quote_currency}00000000000000000000000000000000000",  # Placeholder
                    "decimal": quote_scale
                }
                
    async def place_order(
        self,
        order_id: str,
        trading_pair: str,
        amount: Decimal,
        order_type: OrderType,
        is_buy: bool,
        price: Optional[Decimal] = None,
    ) -> Dict[str, Any]:
        """Place an order on the exchange using signed intent."""
        # Parse the trading pair
        if "-" in trading_pair:
            base_token, quote_token = trading_pair.split("-")
        else:
            # Assume format like ETH/USDC
            base_token, quote_token = trading_pair.split("/")
        
        # Get token information for signature
        base_token_info = self._tokens.get(base_token, {"address": f"0x{base_token}000000000000000000000000000000000000", "decimal": 18})
        quote_token_info = self._tokens.get(quote_token, {"address": f"0x{quote_token}00000000000000000000000000000000000", "decimal": 18})
        
        # Set up tokens for the order based on direction
        if is_buy:
            # Buying base with quote
            out_token = quote_token_info 
            in_token = base_token_info
            out_amount = float(price * amount) if price else float(amount) 
            in_amount = float(amount)
        else:
            # Selling base for quote
            out_token = base_token_info
            in_token = quote_token_info
            out_amount = float(amount)
            in_amount = float(price * amount) if price else float(amount)
        
        # Default solver is our own address
        solver = self._auth.address
        
        # Sign the order intent
        intent = await self._auth.build_intent(
            is_full_order=(order_type == OrderType.LIMIT),  # Full order for limit orders
            out_token=out_token,
            out_amount=out_amount,
            in_token=in_token,
            in_amount=in_amount,
            expiration_minutes=60,  # 1 hour expiration
            solver=solver
        )
        
        # Construct request payload
        data = {
            "intent": intent,
            "type": ORDER_TYPE_MAP.get(order_type)
        }
            
        response = await self._api_request(RESTMethod.POST, SWAPHERE_PLACE_ORDER_PATH, data=data)
        return response
        
    async def execute_buy(
        self,
        order_id: str,
        trading_pair: str,
        amount: Decimal,
        order_type: OrderType,
        price: Optional[Decimal] = None,
    ) -> str:
        """
        Execute a buy order
        :return: the client order id
        """
        client_order_id = order_id or get_new_client_order_id(True, trading_pair)
        try:
            order_result = await self.place_order(
                order_id=client_order_id,
                trading_pair=trading_pair,
                amount=amount,
                order_type=order_type,
                is_buy=True,
                price=price
            )
            
            exchange_order_id = order_result.get("id")
            self.start_tracking_order(
                order_id=client_order_id,
                exchange_order_id=exchange_order_id,
                trading_pair=trading_pair,
                order_type=order_type,
                trade_type=TradeType.BUY,
                price=price,
                amount=amount,
            )
            
            self.logger().info(f"Buy order {client_order_id} created for {amount} {trading_pair}")
            return client_order_id
            
        except Exception as e:
            self.logger().error(f"Error creating buy order: {str(e)}", exc_info=True)
            raise
            
    async def execute_sell(
        self,
        order_id: str,
        trading_pair: str,
        amount: Decimal,
        order_type: OrderType,
        price: Optional[Decimal] = None,
    ) -> str:
        """
        Execute a sell order
        :return: the client order id
        """
        client_order_id = order_id or get_new_client_order_id(False, trading_pair)
        try:
            order_result = await self.place_order(
                order_id=client_order_id,
                trading_pair=trading_pair,
                amount=amount,
                order_type=order_type,
                is_buy=False,
                price=price
            )
            
            exchange_order_id = order_result.get("id")
            self.start_tracking_order(
                order_id=client_order_id,
                exchange_order_id=exchange_order_id,
                trading_pair=trading_pair,
                order_type=order_type,
                trade_type=TradeType.SELL,
                price=price,
                amount=amount,
            )
            
            self.logger().info(f"Sell order {client_order_id} created for {amount} {trading_pair}")
            return client_order_id
            
        except Exception as e:
            self.logger().error(f"Error creating sell order: {str(e)}", exc_info=True)
            raise
            
    def start_tracking_order(
        self,
        order_id: str,
        exchange_order_id: str,
        trading_pair: str,
        order_type: OrderType,
        trade_type: TradeType,
        price: Optional[Decimal],
        amount: Decimal,
    ):
        """
        Starts tracking an order by adding it to the _in_flight_orders dictionary
        """
        self._in_flight_orders[order_id] = InFlightOrder(
            client_order_id=order_id,
            exchange_order_id=exchange_order_id,
            trading_pair=trading_pair,
            order_type=order_type,
            trade_type=trade_type,
            price=price,
            amount=amount,
            creation_timestamp=self.current_timestamp
        )
        
    def stop_tracking_order(self, order_id: str):
        """
        Stops tracking an order by removing it from _in_flight_orders dictionary
        """
        if order_id in self._in_flight_orders:
            del self._in_flight_orders[order_id]
            
    async def _api_request(
        self,
        method: RESTMethod,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Sends an API request to Swaphere
        """
        full_url = f"{SWAPHERE_BASE_URL.rstrip('/')}{path}"
        
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)
            
        resp = await self._rest_assistant.call(
            method=method,
            url=full_url,
            params=params,
            data=json.dumps(data) if data else None,
            headers=request_headers
        )
        
        response_json = await resp.json()
        return response_json
        
    async def cancel_order(self, client_order_id: str) -> Dict[str, Any]:
        """
        Cancel an existing order
        """
        order = self._in_flight_orders.get(client_order_id)
        if not order:
            self.logger().error(f"Failed to cancel order - {client_order_id}: Order not found in tracking.")
            return {"success": False, "error": "Order not found"}
            
        exchange_order_id = order.exchange_order_id
        
        path = SWAPHERE_ORDER_CANCEL_PATH.format(exchange_order_id)
        response = await self._api_request(
            method=RESTMethod.DELETE,
            path=path
        )
        
        # Assume successful cancellation unless there's an error in the response
        if not isinstance(response, dict) or response.get("error"):
            return {"success": False, "error": "Failed to cancel order"}
        
        self.logger().info(f"Successfully canceled order {client_order_id}")
        self.stop_tracking_order(client_order_id)
            
        return {"success": True}
        
    async def cancel_all(self, timeout_seconds: float) -> List[CancellationResult]:
        """
        Cancel all in-flight orders
        """
        incomplete_orders = [o for o in self._in_flight_orders.values() if not o.is_done]
        tasks = [self.cancel_order(o.client_order_id) for o in incomplete_orders]
        cancellation_results = []
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for order, result in zip(incomplete_orders, results):
                success = not isinstance(result, Exception) and result.get("success", False)
                cancellation_results.append(CancellationResult(order.client_order_id, success))
        except Exception as e:
            self.logger().error(f"Failed to cancel all orders: {str(e)}", exc_info=True)
            
        return cancellation_results
        
    def get_fee(self,
                base_currency: str,
                quote_currency: str,
                order_type: OrderType,
                order_side: TradeType,
                amount: Decimal,
                price: Decimal = None,
                is_maker: bool = None) -> TradeFeeBase:
        """
        Calculate the trading fee for the exchange
        """
        # Assume a default fee of 0.1% for both maker and taker
        fee_percent = Decimal('0.001')
        if is_maker:
            fee_percent = Decimal('0.0008')  # Lower fee for makers
            
        return AddedToCostTradeFee(percent=fee_percent)
        
    async def _update_balances(self):
        """
        Update account balances from user's blockchain balances
        For Swaphere, we'll need to get the balances from the blockchain or wallet
        """
        # In a real implementation, we'd query the blockchain or the Swaphere API
        # for the wallet's token balances
        # For this example implementation, we'll simulate some balances
        
        # Get list of tokens from our tracked tokens
        for token_symbol, token_info in self._tokens.items():
            # Simulate balance data - in real implementation, query from blockchain
            self._account_balances[token_symbol] = Decimal('100.0')  # Example balance
            self._account_available_balances[token_symbol] = Decimal('100.0')  # Example available
            
    async def get_last_traded_price(self, trading_pair: str) -> float:
        """
        Get the last traded price for a trading pair
        """
        path = SWAPHERE_PRODUCT_TRADES_PATH.format(trading_pair)
        params = {"limit": 1}  # Just get the latest trade
        
        response = await self._api_request(RESTMethod.GET, path, params=params)
        
        if not response or len(response) == 0:
            return 0.0
            
        # Extract the last price from the response
        last_trade = response[0]
        last_price = float(last_trade.get("price", 0))
        return last_price 