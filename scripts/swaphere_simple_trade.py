#!/usr/bin/env python

import asyncio
import logging
from decimal import Decimal

# Import library modules
from hummingbot.client.config.config_helpers import ClientConfigAdapter
from hummingbot.connector.exchange.swaphere import SwaphereExchange

print("Starting SwapHere simple trade script...")
print("Imports loaded successfully.")

# Configuration parameters
TRADING_PAIR = "ETH-USDC"  # The trading pair to trade
PRIVATE_KEY = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"  # Dummy private key for testing  # noqa: mock
AMOUNT = Decimal("0.01")  # Amount to trade (in base currency)
BUY_PRICE = None  # If None, will use market price minus 5%
SELL_PRICE = None  # If None, will use market price plus 5%


async def run_simple_trade():
    """Run a simple buy and sell trade using the SwapHere connector"""
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("Initializing SwapHere connector...")

    # Create client config with proper structure
    client_config_map = {"anonymized_metrics_mode": {"get_collector": lambda: None}}
    client_config = ClientConfigAdapter(client_config_map)

    # Initialize the connector
    connector = SwaphereExchange.get_implementation(
        client_config_map=client_config,
        swaphere_private_key=PRIVATE_KEY,
        trading_pairs=[TRADING_PAIR],
        trading_required=True,
    )

    try:
        # Start the connector
        logger.info("Starting network connection...")
        await connector.start_network()

        # Wait for connector to initialize
        await asyncio.sleep(5)

        # Check if market is available
        is_online = await connector.check_network()
        if not is_online:
            logger.error("SwapHere exchange is not available. Please check your connection.")
            return

        logger.info("Successfully connected to SwapHere!")

        # Fetch order book to get current market price
        logger.info(f"Fetching order book for {TRADING_PAIR}...")
        order_book = await connector.get_order_book(TRADING_PAIR)
        if not order_book or not order_book.get("bids") or not order_book.get("asks"):
            logger.error(f"Unable to fetch order book for {TRADING_PAIR}")
            return

        # Get best bid and ask prices
        best_bid_price = Decimal(str(order_book["bids"][0][0]))
        best_ask_price = Decimal(str(order_book["asks"][0][0]))
        mid_price = (best_bid_price + best_ask_price) / Decimal("2")

        logger.info(f"Current market - Bid: {best_bid_price}, Ask: {best_ask_price}, Mid: {mid_price}")

        # Get balances
        logger.info("Fetching balances...")
        # Note: Balances are updated when starting network
        base_currency, quote_currency = TRADING_PAIR.split("-")
        base_balance = connector._account_balances.get(base_currency, Decimal("0"))
        quote_balance = connector._account_balances.get(quote_currency, Decimal("0"))

        logger.info(f"Current balances - {base_currency}: {base_balance}, {quote_currency}: {quote_balance}")

        # Calculate buy and sell prices if not provided
        buy_price = BUY_PRICE if BUY_PRICE is not None else mid_price * Decimal("0.95")  # 5% below mid price
        sell_price = SELL_PRICE if SELL_PRICE is not None else mid_price * Decimal("1.05")  # 5% above mid price

        # Execute buy order
        logger.info(f"Placing buy order: {AMOUNT} {base_currency} at {buy_price} {quote_currency}")
        buy_order_id = await connector.execute_buy(
            order_id=None,  # Let the connector generate an order ID
            trading_pair=TRADING_PAIR,
            amount=AMOUNT,
            order_type=connector.OrderType.LIMIT,
            price=buy_price,
        )

        logger.info(f"Buy order placed with ID: {buy_order_id}")

        # Wait a bit for the order to potentially fill
        logger.info("Waiting for buy order to fill...")
        await asyncio.sleep(30)

        # Check buy order status
        in_flight_orders = connector.limit_orders
        buy_order = next((o for o in in_flight_orders if o.client_order_id == buy_order_id), None)

        if buy_order:
            logger.info("Buy order is still active. Cancelling...")
            await connector.cancel_order(buy_order_id)
            logger.info("Buy order cancelled")
        else:
            logger.info("Buy order has been filled or cancelled")

        # Execute sell order
        logger.info(f"Placing sell order: {AMOUNT} {base_currency} at {sell_price} {quote_currency}")
        sell_order_id = await connector.execute_sell(
            order_id=None,  # Let the connector generate an order ID
            trading_pair=TRADING_PAIR,
            amount=AMOUNT,
            order_type=connector.OrderType.LIMIT,
            price=sell_price,
        )

        logger.info(f"Sell order placed with ID: {sell_order_id}")

        # Wait a bit for the order to potentially fill
        logger.info("Waiting for sell order to fill...")
        await asyncio.sleep(30)

        # Check sell order status
        in_flight_orders = connector.limit_orders
        sell_order = next((o for o in in_flight_orders if o.client_order_id == sell_order_id), None)

        if sell_order:
            logger.info("Sell order is still active. Cancelling...")
            await connector.cancel_order(sell_order_id)
            logger.info("Sell order cancelled")
        else:
            logger.info("Sell order has been filled or cancelled")

        # Get updated balances
        logger.info("Fetching updated balances...")
        await connector._update_balances()

        base_balance = connector._account_balances.get(base_currency, Decimal("0"))
        quote_balance = connector._account_balances.get(quote_currency, Decimal("0"))
        logger.info(f"Updated balances - {base_currency}: {base_balance}, {quote_currency}: {quote_balance}")

    except Exception as e:
        logger.error(f"Error during trading: {str(e)}", exc_info=True)
    finally:
        # Clean up
        logger.info("Stopping network connection...")
        await connector.stop_network()
        logger.info("Done")


if __name__ == "__main__":
    print("About to run the simple trade example...")
    # Run the simple trade example
    asyncio.run(run_simple_trade())
    print("Simple trade execution completed.")
