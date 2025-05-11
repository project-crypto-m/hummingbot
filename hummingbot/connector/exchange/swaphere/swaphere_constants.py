import sys

from hummingbot.core.api_throttler.data_types import RateLimit
from hummingbot.core.data_type.common import OrderType
from hummingbot.core.data_type.in_flight_order import OrderState

CLIENT_ID_PREFIX = "hb_swaphere_"
MAX_ID_LEN = 32
SECONDS_TO_WAIT_TO_RECEIVE_MESSAGE = 30 * 0.8

DEFAULT_DOMAIN = ""

# URLs
SWAPHERE_BASE_URL = "http://127.0.0.1:8088"  # Default local server URL, should be configurable

# API Endpoints
SWAPHERE_PRODUCTS_PATH = '/api/products'
SWAPHERE_PRODUCT_BOOK_PATH = '/api/products/{}/book'
SWAPHERE_PRODUCT_TRADES_PATH = '/api/products/{}/trades'
SWAPHERE_PRODUCT_CANDLES_PATH = '/api/products/{}/candles'

# Auth required
SWAPHERE_PLACE_ORDER_PATH = "/api/v2/orders"
SWAPHERE_ORDERS_PATH = '/api/orders'
SWAPHERE_MARKET_ORDERS_PATH = '/api/market'
SWAPHERE_ORDER_CANCEL_PATH = '/api/orders/{}'
SWAPHERE_ORDER_RESERVE_PATH = '/api/v2/orders/{}/reserve'
SWAPHERE_ORDERBOOK_PATH = '/api/orderbook'

# WS
SWAPHERE_WS_URI = "ws://127.0.0.1:8088/ws"  # WebSocket URL for local server

SWAPHERE_WS_ORDERBOOK_CHANNEL = "orderbook"
SWAPHERE_WS_TRADES_CHANNEL = "trades"
SWAPHERE_WS_ORDERS_CHANNEL = "orders"

SWAPHERE_WS_CHANNELS = {
    SWAPHERE_WS_ORDERBOOK_CHANNEL,
    SWAPHERE_WS_TRADES_CHANNEL,
    SWAPHERE_WS_ORDERS_CHANNEL
}

WS_CONNECTION_LIMIT_ID = "WSConnection"
WS_REQUEST_LIMIT_ID = "WSRequest"
WS_SUBSCRIPTION_LIMIT_ID = "WSSubscription"
WS_LOGIN_LIMIT_ID = "WSLogin"

ORDER_STATE = {
    "live": OrderState.OPEN,
    "filled": OrderState.FILLED,
    "partially_filled": OrderState.PARTIALLY_FILLED,
    "canceled": OrderState.CANCELED,
}

ORDER_TYPE_MAP = {
    OrderType.LIMIT: "LIMIT",
    OrderType.MARKET: "MARKET",
    OrderType.LIMIT_MAKER: "LIMIT",  # Using LIMIT for LIMIT_MAKER since there's no specific type
}

# Blockchain context information for EIP-712 signing
DEFAULT_BLOCKCHAIN_CONTEXT = {
    "partialTokenSwapStandard": "0x1234567890123456789012345678901234567890",
    "name": "Swaphere",
    "version": "1",
    "chainId": 1,
    "verifyingContract": "0x0987654321098765432109876543210987654321"
}

# Used for ethers.js typed data signing
TYPES = {
    "Swap": [
        {"name": "isFullOrder", "type": "bool"},
        {"name": "nonce", "type": "uint24"},
        {"name": "timestamp", "type": "uint64"},
        {"name": "solver", "type": "address"},
        {"name": "outToken", "type": "address"},
        {"name": "outAmount", "type": "uint128"},
        {"name": "inToken", "type": "address"},
        {"name": "inAmount", "type": "uint128"}
    ]
}

NO_LIMIT = sys.maxsize

RATE_LIMITS = [
    RateLimit(WS_CONNECTION_LIMIT_ID, limit=3, time_interval=1),
    RateLimit(WS_REQUEST_LIMIT_ID, limit=100, time_interval=10),
    RateLimit(WS_SUBSCRIPTION_LIMIT_ID, limit=240, time_interval=60 * 60),
    RateLimit(WS_LOGIN_LIMIT_ID, limit=1, time_interval=15),
    RateLimit(limit_id=SWAPHERE_PRODUCTS_PATH, limit=10, time_interval=2),
    RateLimit(limit_id=SWAPHERE_PRODUCT_BOOK_PATH, limit=20, time_interval=2),
    RateLimit(limit_id=SWAPHERE_PRODUCT_TRADES_PATH, limit=20, time_interval=2),
    RateLimit(limit_id=SWAPHERE_PRODUCT_CANDLES_PATH, limit=20, time_interval=2),
    RateLimit(limit_id=SWAPHERE_PLACE_ORDER_PATH, limit=20, time_interval=2),
    RateLimit(limit_id=SWAPHERE_ORDERS_PATH, limit=20, time_interval=2),
    RateLimit(limit_id=SWAPHERE_ORDER_CANCEL_PATH, limit=20, time_interval=2),
    RateLimit(limit_id=SWAPHERE_ORDER_RESERVE_PATH, limit=20, time_interval=2),
    RateLimit(limit_id=SWAPHERE_ORDERBOOK_PATH, limit=10, time_interval=2),
    RateLimit(limit_id=SWAPHERE_MARKET_ORDERS_PATH, limit=10, time_interval=2),
]
