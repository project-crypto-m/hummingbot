import asyncio
import logging
from decimal import Decimal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test private key - this is a test key, don't use in production
PRIVATE_KEY = "0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"  # noqa: mock

# Trading pair to tes
TEST_TRADING_PAIR = "ETH-USDC"

# Test order parameters
TEST_AMOUNT = Decimal("0.1")
TEST_PRICE = Decimal("2000.0")


async def test_connector_initialization():
    """Test basic connector initialization"""
    try:
        from hummingbot.connector.exchange.swaphere.swaphere_exchange import SwaphereExchange

        # Initialize the connector
        connector = SwaphereExchange(
            private_key=PRIVATE_KEY,
            trading_pairs=[TEST_TRADING_PAIR],
            trading_required=True,
        )

        logger.info(f"Connector initialized: {connector.name}")

        # Test network connection
        await connector.start_network()
        logger.info("Network started")

        # Check if network is connected
        network_status = await connector.check_network()
        logger.info(f"Network status: {'Connected' if network_status else 'Disconnected'}")

        # Stop network
        await connector.stop_network()
        logger.info("Network stopped")

        return network_status
    except Exception as e:
        logger.error(f"Error initializing connector: {e}", exc_info=True)
        return False


async def test_order_book():
    """Test fetching order book data"""
    try:
        from hummingbot.connector.exchange.swaphere.swaphere_exchange import SwaphereExchange

        # Initialize the connector
        connector = SwaphereExchange(
            private_key=PRIVATE_KEY,
            trading_pairs=[TEST_TRADING_PAIR],
            trading_required=False,
        )

        await connector.start_network()

        # Get order book
        order_book = await connector.get_order_book(TEST_TRADING_PAIR)

        # Print order book summary
        if order_book:
            logger.info(f"Order book for {TEST_TRADING_PAIR} fetched successfully")
            if "bids" in order_book:
                logger.info(f"Bids: {len(order_book['bids'])} entries")
            if "asks" in order_book:
                logger.info(f"Asks: {len(order_book['asks'])} entries")
        else:
            logger.warning("No order book data received")

        await connector.stop_network()
        return order_book is not None
    except Exception as e:
        logger.error(f"Error fetching order book: {e}", exc_info=True)
        return False


async def test_trading_rules():
    """Test fetching trading rules"""
    try:
        from hummingbot.connector.exchange.swaphere.swaphere_exchange import SwaphereExchange

        # Initialize the connector
        connector = SwaphereExchange(
            private_key=PRIVATE_KEY,
            trading_pairs=[TEST_TRADING_PAIR],
            trading_required=False,
        )

        await connector.start_network()

        # Update and get trading rules
        await connector._update_trading_rules()
        trading_rules = await connector.get_trading_rules()

        # Print trading rules
        if trading_rules and TEST_TRADING_PAIR in trading_rules:
            rule = trading_rules[TEST_TRADING_PAIR]
            logger.info(f"Trading rule for {TEST_TRADING_PAIR}:")
            logger.info(f"  Min order size: {rule.min_order_size}")
            logger.info(f"  Max order size: {rule.max_order_size}")
            logger.info(f"  Min price increment: {rule.min_price_increment}")
            logger.info(f"  Min base amount increment: {rule.min_base_amount_increment}")
        else:
            logger.warning(f"No trading rule found for {TEST_TRADING_PAIR}")

        await connector.stop_network()
        return trading_rules is not None and TEST_TRADING_PAIR in trading_rules
    except Exception as e:
        logger.error(f"Error fetching trading rules: {e}", exc_info=True)
        return False


async def test_place_order(is_buy=True):
    """Test placing an order"""
    try:
        from hummingbot.connector.exchange.swaphere.swaphere_exchange import SwaphereExchange
        from hummingbot.core.data_type.common import OrderType

        # Initialize the connector
        connector = SwaphereExchange(
            private_key=PRIVATE_KEY,
            trading_pairs=[TEST_TRADING_PAIR],
            trading_required=True,
        )

        await connector.start_network()

        # Place order
        if is_buy:
            order_id = await connector.execute_buy(
                order_id=None,  # Let the connector generate the ID
                trading_pair=TEST_TRADING_PAIR,
                amount=TEST_AMOUNT,
                order_type=OrderType.LIMIT,
                price=TEST_PRICE,
            )
            logger.info(f"Buy order placed with ID: {order_id}")
        else:
            order_id = await connector.execute_sell(
                order_id=None,  # Let the connector generate the ID
                trading_pair=TEST_TRADING_PAIR,
                amount=TEST_AMOUNT,
                order_type=OrderType.LIMIT,
                price=TEST_PRICE,
            )
            logger.info(f"Sell order placed with ID: {order_id}")

        # Wait a bit for the order to be processed
        await asyncio.sleep(2)

        # Check if the order is tracked
        if order_id in connector._in_flight_orders:
            order = connector._in_flight_orders[order_id]
            logger.info(f"Order status: {order}")
        else:
            logger.warning(f"Order with ID {order_id} not found in tracking")

        # Cancel the order
        cancellation_result = await connector.cancel_order(order_id)
        logger.info(f"Order cancellation result: {cancellation_result}")

        await connector.stop_network()
        return order_id is not None
    except Exception as e:
        logger.error(f"Error placing order: {e}", exc_info=True)
        return False


async def test_order_book_data_source():
    """Test the order book data source"""
    try:
        from hummingbot.connector.exchange.swaphere.swaphere_api_order_book_data_source import (
            SwaphereAPIOrderBookDataSource,
        )
        from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory

        # Initialize the data source
        data_source = SwaphereAPIOrderBookDataSource(
            trading_pairs=[TEST_TRADING_PAIR],
            web_assistants_factory=WebAssistantsFactory(),
        )

        # Get snapsho
        snapshot = await data_source.get_snapshot(TEST_TRADING_PAIR)

        if snapshot:
            logger.info(f"Order book snapshot for {TEST_TRADING_PAIR} fetched successfully")
            if "bids" in snapshot:
                logger.info(f"Bids: {len(snapshot['bids'])} entries")
            if "asks" in snapshot:
                logger.info(f"Asks: {len(snapshot['asks'])} entries")
        else:
            logger.warning("No snapshot data received")

        # Create order book
        order_book = await data_source.get_new_order_book(TEST_TRADING_PAIR)
        logger.info(f"Order book created successfully: {type(order_book)}")

        return snapshot is not None and order_book is not None
    except Exception as e:
        logger.error(f"Error testing order book data source: {e}", exc_info=True)
        return False


async def test_websocket_connection():
    """Test the WebSocket connection"""
    try:
        from hummingbot.connector.exchange.swaphere.swaphere_api_order_book_data_source import (
            SwaphereAPIOrderBookDataSource,
        )
        from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory

        # Create a queue to receive messages
        message_queue = asyncio.Queue()

        # Initialize the data source
        data_source = SwaphereAPIOrderBookDataSource(
            trading_pairs=[TEST_TRADING_PAIR],
            web_assistants_factory=WebAssistantsFactory(),
        )

        # Start listening for messages in the background
        listen_task = asyncio.create_task(
            data_source.listen_for_order_book_diffs(asyncio.get_event_loop(), message_queue)
        )

        # Wait a bit to allow connection and subscription
        logger.info("Waiting for WebSocket messages...")
        await asyncio.sleep(10)

        # Check if any messages were received
        received_messages = []
        while not message_queue.empty():
            msg = await message_queue.get()
            received_messages.append(msg)

        # Cancel the listening task
        listen_task.cancel()

        logger.info(f"Received {len(received_messages)} order book messages")
        for msg in received_messages[:3]:  # Just print the first few
            logger.info(f"Message: {msg}")

        return True
    except Exception as e:
        logger.error(f"Error testing WebSocket connection: {e}", exc_info=True)
        return False


async def run_all_tests():
    """Run all tests in sequence"""
    logger.info("=== Testing Swaphere Connector with Local Server ===")

    # Basic initialization
    logger.info("\n=== Test 1: Connector Initialization ===")
    init_result = await test_connector_initialization()
    logger.info(f"Initialization test {'passed' if init_result else 'failed'}")

    # Order book
    logger.info("\n=== Test 2: Order Book Fetching ===")
    order_book_result = await test_order_book()
    logger.info(f"Order book test {'passed' if order_book_result else 'failed'}")

    # Trading rules
    logger.info("\n=== Test 3: Trading Rules ===")
    rules_result = await test_trading_rules()
    logger.info(f"Trading rules test {'passed' if rules_result else 'failed'}")

    # Order book data source
    logger.info("\n=== Test 4: Order Book Data Source ===")
    data_source_result = await test_order_book_data_source()
    logger.info(f"Order book data source test {'passed' if data_source_result else 'failed'}")

    # WebSocket connection
    logger.info("\n=== Test 5: WebSocket Connection ===")
    websocket_result = await test_websocket_connection()
    logger.info(f"WebSocket test {'passed' if websocket_result else 'failed'}")

    # Place buy order
    logger.info("\n=== Test 6: Place Buy Order ===")
    buy_result = await test_place_order(is_buy=True)
    logger.info(f"Buy order test {'passed' if buy_result else 'failed'}")

    # Place sell order
    logger.info("\n=== Test 7: Place Sell Order ===")
    sell_result = await test_place_order(is_buy=False)
    logger.info(f"Sell order test {'passed' if sell_result else 'failed'}")

    # Summary
    all_passed = all([
        init_result,
        order_book_result,
        rules_result,
        data_source_result,
        websocket_result,
        buy_result,
        sell_result
    ])

    logger.info("\n=== Test Summary ===")
    logger.info(f"All tests {'passed' if all_passed else 'failed'}")

    return all_passed


if __name__ == "__main__":
    asyncio.run(run_all_tests())
