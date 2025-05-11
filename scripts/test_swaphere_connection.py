#!/usr/bin/env python

import asyncio
import logging
import random
import uuid
from decimal import Decimal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dummy private key for testing
PRIVATE_KEY = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"  # noqa: mock


class DummyMetricsCollector:
    @staticmethod
    def get_collector(*args, **kwargs):
        return None


class DummyAnonymizedMetricsMode:
    @staticmethod
    def get_collector(*args, **kwargs):
        return DummyMetricsCollector()


def generate_client_id() -> str:
    vals = [random.choice(range(0, 256)) for i in range(0, 20)]
    return "".join([f"{val:02x}" for val in vals])


class DummyConfig:
    def __init__(self):
        self.anonymized_metrics_mode = DummyAnonymizedMetricsMode()
        self.instance_id = str(uuid.uuid4())
        self.client_id = generate_client_id()
        self.logger_override = None
        self.tables_format = "psql"
        self.debug_console = False
        self.strategy_report_interval = 900.0
        self.reporting_aggregation_interval = 60.0
        self.reporting_metrics_enabled = False
        self.hanging_order_cancel_pct = Decimal("10")

    def __getattr__(self, name):
        # Return None for any other attributes that might be accessed
        return None


async def test_swaphere_connection():
    """Test basic connection to SwapHere exchange"""
    logger.info("Testing SwapHere connection...")

    try:
        # Import SwapHere classes directly
        from hummingbot.client.config.config_helpers import ClientConfigAdapter
        from hummingbot.connector.exchange.swaphere import SwaphereExchange
        from hummingbot.connector.exchange.swaphere.swaphere_auth import SwaphereAuth

        # Create a simple auth object to test connection
        auth = SwaphereAuth(PRIVATE_KEY)
        logger.info(f"Created auth object with address: {auth.address}")

        # Create a dummy client config map
        client_config_map = ClientConfigAdapter(DummyConfig())

        # Initialize the exchange with minimal parameters
        exchange = SwaphereExchange.get_implementation(
            client_config_map=client_config_map,
            swaphere_private_key=PRIVATE_KEY,
            trading_pairs=["ETH-USDC"],
            trading_required=False,  # No actual trading needed for this test
        )

        logger.info("Initialized SwapHere exchange")

        # Start the network
        logger.info("Starting network connection...")
        await exchange.start_network()

        # Check if the exchange is online
        is_online = await exchange.check_network()
        logger.info(f"Exchange is online: {is_online}")

        if is_online:
            # Try to get the order book
            logger.info("Fetching order book for ETH-USDC...")
            order_book = await exchange.get_order_book("ETH-USDC")

            if order_book:
                bids = order_book.get("bids", [])
                asks = order_book.get("asks", [])

                logger.info(f"Order book received. Bids: {len(bids)}, Asks: {len(asks)}")

                if bids:
                    logger.info(f"Top bid: {bids[0]}")
                if asks:
                    logger.info(f"Top ask: {asks[0]}")
            else:
                logger.warning("Order book is empty or not available")

        # Stop the network
        logger.info("Stopping network connection...")
        await exchange.stop_network()

        logger.info("Test completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error testing SwapHere connection: {str(e)}", exc_info=True)
        return False


async def main():
    """Main function to run the test"""
    result = await test_swaphere_connection()

    if result:
        logger.info("SwapHere connection test passed!")
    else:
        logger.error("SwapHere connection test failed!")


if __name__ == "__main__":
    # Run the test
    asyncio.run(main())
