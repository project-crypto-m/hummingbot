# Strategy parameters
from decimal import Decimal

TRADING_PAIR = "ETH-USDC"  # The trading pair
BASE_ASSET = TRADING_PAIR.split("-")[0]  # Base asset (e.g., ETH)
QUOTE_ASSET = TRADING_PAIR.split("-")[1]  # Quote asset (e.g., USDC)
BID_SPREAD = Decimal("0.005")  # 0.5% bid spread
ASK_SPREAD = Decimal("0.005")  # 0.5% ask spread
ORDER_AMOUNT = Decimal("0.01")  # Order size in base asset
ORDER_REFRESH_TIME = 60.0  # Time in seconds between order updates
PRIVATE_KEY = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"  # Dummy private key for testing  # noqa: mock
