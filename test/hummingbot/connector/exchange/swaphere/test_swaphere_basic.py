import asyncio
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test private key
PRIVATE_KEY = "0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"

# Mock token information
ETH_TOKEN = {
    "address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "decimal": 18
}

USDC_TOKEN = {
    "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "decimal": 6
}

# Test functions


async def test_auth_signing():
    try:
        # Import directly from the module to avoid full Hummingbot dependency
        from hummingbot.connector.exchange.swaphere.swaphere_auth import SwaphereAuth

        # Create the auth instance
        logger.info("Creating SwaphereAuth instance...")
        auth = SwaphereAuth(PRIVATE_KEY)
        logger.info(f"Wallet address: {auth.address}")

        # Test building an order intent
        logger.info("Testing order intent building...")
        intent = await auth.build_intent(
            is_full_order=True,  # Full order (limit order)
            out_token=ETH_TOKEN,
            out_amount=1.0,
            in_token=USDC_TOKEN,
            in_amount=2000.0,
            expiration_minutes=60,
            solver=None  # Use own address
        )

        logger.info(f"Generated intent (hex): {intent[:50]}...")
        logger.info("Order intent generation successful")

        return True
    except Exception as e:
        logger.error(f"Error testing Swaphere auth: {e}", exc_info=True)
        return False


async def test_web_utils():
    try:
        from hummingbot.connector.exchange.swaphere.swaphere_web_utils import (
            format_trading_pair,
            private_rest_url,
            public_rest_url,
        )

        # Test URL building
        base_url = "http://127.0.0.1:8088"
        path = "/api/products"

        public_url = public_rest_url(path, base_url)
        private_url = private_rest_url(path, base_url)

        logger.info(f"Public URL: {public_url}")
        logger.info(f"Private URL: {private_url}")

        # Test trading pair formatting
        pair1 = "ETH/USDC"
        pair2 = "ETH-USDC"

        formatted1 = format_trading_pair(pair1)
        formatted2 = format_trading_pair(pair2)

        logger.info(f"Formatted pair1: {formatted1}")
        logger.info(f"Formatted pair2: {formatted2}")

        return True
    except Exception as e:
        logger.error(f"Error testing web utils: {e}", exc_info=True)
        return False


async def test_utils():
    try:
        from hummingbot.connector.exchange.swaphere.swaphere_utils import (
            convert_to_exchange_trading_pair,
            get_new_client_order_id,
            split_trading_pair,
        )

        # Test splitting trading pair
        pair = "ETH-USDC"
        base, quote = split_trading_pair(pair)
        logger.info(f"Split pair {pair}: Base={base}, Quote={quote}")

        # Test trading pair conversion
        hb_pair = "ETH/USDC"
        exchange_pair = convert_to_exchange_trading_pair(hb_pair)
        logger.info(f"Converted to exchange format: {exchange_pair}")

        # Test client order ID generation
        buy_order_id = get_new_client_order_id(True, "ETH-USDC")
        sell_order_id = get_new_client_order_id(False, "ETH-USDC")
        logger.info(f"Buy order ID: {buy_order_id}")
        logger.info(f"Sell order ID: {sell_order_id}")

        return True
    except Exception as e:
        logger.error(f"Error testing utils: {e}", exc_info=True)
        return False

# Main function


async def main():
    logger.info("=== Testing Swaphere Basic Components ===")

    auth_result = await test_auth_signing()
    logger.info(f"Auth testing {'passed' if auth_result else 'failed'}")

    web_utils_result = await test_web_utils()
    logger.info(f"Web utils testing {'passed' if web_utils_result else 'failed'}")

    utils_result = await test_utils()
    logger.info(f"Utils testing {'passed' if utils_result else 'failed'}")

    if auth_result and web_utils_result and utils_result:
        logger.info("All basic tests passed!")
    else:
        logger.error("Some tests failed!")

if __name__ == "__main__":
    asyncio.run(main())
