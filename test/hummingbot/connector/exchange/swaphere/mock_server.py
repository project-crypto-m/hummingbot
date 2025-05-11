#!/usr/bin/env python3

import asyncio
import json
import logging
import random
import time
from typing import Dict

import aiohttp
from aiohttp import web

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SwaphereMockServer:
    """
    A mock server that simulates the Swaphere API for testing purposes.
    """
    def __init__(self, host="0.0.0.0", port=8088):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.runner = None
        self.site = None
        self.orders = {}
        self.next_order_id = 1000
        self._setup_routes()
        self.ws_connections = set()
        self.order_books = self._create_mock_order_books()

    def _setup_routes(self):
        """Set up the routes for the mock server"""
        # Public endpoints
        self.app.router.add_get('/api/products', self.handle_products)
        self.app.router.add_get('/api/products/{trading_pair}/book', self.handle_order_book)
        self.app.router.add_get('/api/products/{trading_pair}/trades', self.handle_trades)

        # Private endpoints
        self.app.router.add_post('/api/v2/orders', self.handle_place_order)
        self.app.router.add_get('/api/orders', self.handle_orders)
        self.app.router.add_delete('/api/orders/{order_id}', self.handle_cancel_order)

        # WebSocket
        self.app.router.add_get('/ws', self.handle_websocket)

    def _create_mock_order_books(self) -> Dict[str, Dict]:
        """Create mock order books for testing"""
        order_books = {
            'ETH-USDC': {
                'bids': [[str(2000 - i * 10), str(1.0 / (i + 1))] for i in range(10)],
                'asks': [[str(2000 + i * 10), str(1.0 / (i + 1))] for i in range(10)]
            },
            'BTC-USDC': {
                'bids': [[str(30000 - i * 100), str(0.1 / (i + 1))] for i in range(10)],
                'asks': [[str(30000 + i * 100), str(0.1 / (i + 1))] for i in range(10)]
            }
        }
        return order_books

    async def start(self):
        """Start the mock server"""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        logger.info(f"Mock Swaphere server running at http://{self.host}:{self.port}")

        # Start the WebSocket broadcaster
        asyncio.create_task(self._websocket_broadcaster())

    async def stop(self):
        """Stop the mock server"""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("Mock Swaphere server stopped")

    async def handle_products(self, request):
        """Handle GET /api/products request"""
        products = [
            {
                "id": "ETH-USDC",
                "baseCurrency": "ETH",
                "quoteCurrency": "USDC",
                "baseMinSize": "0.001",
                "baseMaxSize": "1000.0",
                "quoteIncrement": "0.01",
                "baseScale": 18,
                "quoteScale": 6,
                "status": "online"
            },
            {
                "id": "BTC-USDC",
                "baseCurrency": "BTC",
                "quoteCurrency": "USDC",
                "baseMinSize": "0.0001",
                "baseMaxSize": "100.0",
                "quoteIncrement": "0.01",
                "baseScale": 8,
                "quoteScale": 6,
                "status": "online"
            }
        ]
        return web.json_response(products)

    async def handle_order_book(self, request):
        """Handle GET /api/products/{trading_pair}/book request"""
        trading_pair = request.match_info['trading_pair']
        # We don't actually use the level parameter, but we get it from the request
        # to match the API's behavior
        _ = int(request.query.get('level', 2))

        if trading_pair not in self.order_books:
            return web.json_response({"error": "Trading pair not found"}, status=404)

        order_book = self.order_books[trading_pair]
        return web.json_response(order_book)

    async def handle_trades(self, request):
        """Handle GET /api/products/{trading_pair}/trades request"""
        trading_pair = request.match_info['trading_pair']
        limit = int(request.query.get('limit', 10))

        if trading_pair not in self.order_books:
            return web.json_response({"error": "Trading pair not found"}, status=404)

        # Generate mock trades
        current_time = int(time.time() * 1000)
        trades = []

        for i in range(limit):
            price = float(self.order_books[trading_pair]['bids'][0][0])
            size = float(self.order_books[trading_pair]['bids'][0][1])
            side = "buy" if random.random() > 0.5 else "sell"

            trades.append({
                "time": current_time - i * 1000,
                "sequence": 1000 + i,
                "price": str(price + (random.random() - 0.5) * 10),
                "size": str(size * random.random()),
                "side": side
            })

        return web.json_response(trades)

    async def handle_place_order(self, request):
        """Handle POST /api/v2/orders request"""
        try:
            data = await request.json()
            intent = data.get("intent", "")
            order_type = data.get("type", "LIMIT")

            order_id = str(self.next_order_id)
            self.next_order_id += 1

            # Create a mock order
            order = {
                "id": order_id,
                "status": "live",
                "type": order_type,
                "intent": intent[:30] + "...",  # Truncate for brevity
                "created_at": int(time.time() * 1000),
                "updated_at": int(time.time() * 1000)
            }

            self.orders[order_id] = order

            return web.json_response(order)
        except Exception as e:
            logger.error(f"Error handling place order: {e}")
            return web.json_response({"error": str(e)}, status=400)

    async def handle_orders(self, request):
        """Handle GET /api/orders request"""
        return web.json_response(list(self.orders.values()))

    async def handle_cancel_order(self, request):
        """Handle DELETE /api/orders/{order_id} request"""
        order_id = request.match_info['order_id']

        if order_id not in self.orders:
            return web.json_response({"error": "Order not found"}, status=404)

        self.orders[order_id]["status"] = "canceled"
        return web.json_response({"success": True, "order_id": order_id})

    async def handle_websocket(self, request):
        """Handle WebSocket connections"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        self.ws_connections.add(ws)

        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)

                    # Handle subscription requests
                    if data.get("op") == "subscribe":
                        channel = data.get("channel")
                        product_id = data.get("product_id")

                        response = {
                            "type": "subscribed",
                            "channel": channel,
                            "product_id": product_id
                        }
                        await ws.send_json(response)

                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket connection closed with exception {ws.exception()}")
        finally:
            self.ws_connections.remove(ws)

        return ws

    async def _websocket_broadcaster(self):
        """Periodically broadcast updates to WebSocket clients"""
        while True:
            try:
                # Skip if no connections
                if not self.ws_connections:
                    await asyncio.sleep(1)
                    continue

                # Broadcast order book updates
                for trading_pair, order_book in self.order_books.items():
                    # Randomly modify order book to simulate changes
                    new_order_book = self._slightly_modify_order_book(order_book)
                    self.order_books[trading_pair] = new_order_book

                    message = {
                        "channel": "orderbook",
                        "product_id": trading_pair,
                        "bids": new_order_book["bids"][:5],  # Send only top 5 entries
                        "asks": new_order_book["asks"][:5]   # Send only top 5 entries
                    }

                    # Send to all connected clients
                    for ws in self.ws_connections:
                        try:
                            await ws.send_json(message)
                        except Exception as e:
                            logger.error(f"Error sending WebSocket message: {e}")

                # Broadcast trade updates
                for trading_pair in self.order_books.keys():
                    price = float(self.order_books[trading_pair]['bids'][0][0])
                    size = float(self.order_books[trading_pair]['bids'][0][1])
                    side = "buy" if random.random() > 0.5 else "sell"

                    trade = {
                        "time": int(time.time() * 1000),
                        "sequence": self.next_order_id,
                        "price": str(price + (random.random() - 0.5) * 5),
                        "size": str(size * random.random()),
                        "side": side
                    }
                    self.next_order_id += 1

                    message = {
                        "channel": "trades",
                        "product_id": trading_pair,
                        "data": trade
                    }

                    for ws in self.ws_connections:
                        try:
                            await ws.send_json(message)
                        except Exception as e:
                            logger.error(f"Error sending WebSocket message: {e}")

                await asyncio.sleep(1)  # Update every second
            except Exception as e:
                logger.error(f"Error in WebSocket broadcaster: {e}")
                await asyncio.sleep(1)

    def _slightly_modify_order_book(self, order_book):
        """Make small random changes to an order book"""
        new_order_book = {"bids": [], "asks": []}

        # Modify bids
        for bid in order_book["bids"]:
            price = float(bid[0])
            size = float(bid[1])

            # Make small random adjustments
            price_change = price * (1 + (random.random() - 0.5) * 0.001)
            size_change = size * (1 + (random.random() - 0.5) * 0.01)

            new_order_book["bids"].append([str(price_change), str(size_change)])

        # Modify asks
        for ask in order_book["asks"]:
            price = float(ask[0])
            size = float(ask[1])

            # Make small random adjustments
            price_change = price * (1 + (random.random() - 0.5) * 0.001)
            size_change = size * (1 + (random.random() - 0.5) * 0.01)

            new_order_book["asks"].append([str(price_change), str(size_change)])

        # Sort bids (descending) and asks (ascending)
        new_order_book["bids"].sort(key=lambda x: float(x[0]), reverse=True)
        new_order_book["asks"].sort(key=lambda x: float(x[0]))

        return new_order_book


async def main():
    """Start the mock server and keep it running"""
    server = SwaphereMockServer()
    await server.start()

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
