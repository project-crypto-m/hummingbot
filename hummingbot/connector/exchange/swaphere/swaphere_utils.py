import re
from datetime import datetime
from typing import Optional, Tuple

from hummingbot.client.config.config_var import ConfigVar
from hummingbot.client.config.config_methods import using_exchange
from hummingbot.core.utils.tracking_nonce import get_tracking_nonce

# Updated pattern to handle different types of trading pair formats
TRADING_PAIR_SPLITTER = re.compile(r"^(\w+)[-/](\w+)$")


def split_trading_pair(trading_pair: str) -> Tuple[str, str]:
    """
    Splits a trading pair into base and quote assets
    Example: ETH-USDC or ETH/USDC -> (ETH, USDC)
    """
    if "-" in trading_pair:
        base, quote = trading_pair.split("-")
        return base, quote
    elif "/" in trading_pair:
        base, quote = trading_pair.split("/")
        return base, quote
    else:
        # Try regex pattern
        m = TRADING_PAIR_SPLITTER.match(trading_pair)
        if m is None:
            raise ValueError(f"Could not parse trading pair {trading_pair}")
        return m.group(1), m.group(2)


def convert_from_exchange_trading_pair(exchange_trading_pair: str) -> str:
    """
    Convert from exchange format to client format
    Swaphere uses format like "ETH-USDC" so we'll keep it
    """
    return exchange_trading_pair


def convert_to_exchange_trading_pair(hb_trading_pair: str) -> str:
    """
    Convert from client format to exchange format
    Ensure consistent format with dash separator
    """
    if "/" in hb_trading_pair:
        base, quote = hb_trading_pair.split("/")
        return f"{base}-{quote}"
    return hb_trading_pair


def get_new_client_order_id(is_buy: bool, trading_pair: str) -> str:
    """
    Creates a client order id for a new order
    Format: B/S-{trading_pair}-{timestamp}-{nonce}
    """
    side = "B" if is_buy else "S"
    ts = int(datetime.now().timestamp() * 1000)
    return f"{side}-{trading_pair}-{ts}-{get_tracking_nonce()}"


KEYS = {
    "swaphere_private_key": ConfigVar(
        key="swaphere_private_key",
        prompt="Enter your Ethereum private key for Swaphere >>> ",
        required_if=using_exchange("swaphere"),
        is_secure=True,
        is_connect_key=True,
    ),
}

# Constants related to the exchange
CENTRALIZED = False  # Swaphere is not a centralized exchange since it's based on blockchain
EXAMPLE_PAIR = "ETH-USDC"
DEFAULT_FEES = [0.1, 0.1]  # Maker and taker fees in percentage 