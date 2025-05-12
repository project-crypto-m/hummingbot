import asyncio
import logging
from decimal import Decimal

# Import Swaphere connector
from hummingbot.connector.exchange.swaphere.swaphere_exchange import SwaphereExchange

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test function


async def test_swaphere_connector():
    # Test private key (replace with a real one for actual testing)
    test_private_key = "0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"  # noqa: mock

    # Create the exchange instance
    logger.info("Initializing Swaphere exchange...")
    exchange = SwaphereExchange(private_key=test_private_key, trading_pairs=["ETH-USDC"], trading_required=True)

    try:
        # Initialize the exchange
        logger.info("Starting network...")
        await exchange.start_network()

        # Check network connectivity
        logger.info("Checking network connection...")
        network_status = await exchange.check_network()
        logger.info(f"Network status: {network_status}")

        # Get trading rules
        logger.info("Getting trading rules...")
        trading_rules = await exchange.get_trading_rules()
        logger.info(f"Trading rules: {trading_rules}")

        # Get order book for a trading pair
        logger.info("Getting order book for ETH-USDC...")
        order_book = await exchange.get_order_book("ETH-USDC")
        logger.info(f"Order book: {order_book}")

        # Get last traded price
        logger.info("Getting last traded price for ETH-USDC...")
        last_price = await exchange.get_last_traded_price("ETH-USDC")
        logger.info(f"Last traded price: {last_price}")

        # Check trading fee calculation
        logger.info("Calculating trading fee...")
        fee = exchange.get_fee(
            base_currency="ETH",
            quote_currency="USDC",
            order_type=exchange.MARKET,
            order_side=exchange.BUY,
            amount=Decimal("1.0"),
            price=Decimal("2000.0"),
        )
        logger.info(f"Trading fee: {fee}")

    except Exception as e:
        logger.error(f"Error testing Swaphere connector: {e}", exc_info=True)
    finally:
        # Stop the exchange
        logger.info("Stopping network...")
        await exchange.stop_network()


# Main function
if __name__ == "__main__":
    asyncio.run(test_swaphere_connector())
