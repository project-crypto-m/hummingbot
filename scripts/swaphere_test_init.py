#!/usr/bin/env python

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dummy private key for testing
PRIVATE_KEY = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"  # noqa: mock


def main():
    """Test SwapHereAuth initialization"""
    try:
        logger.info("Testing SwapHere auth initialization...")
        from hummingbot.connector.exchange.swaphere.swaphere_auth import SwaphereAuth

        auth = SwaphereAuth(PRIVATE_KEY)
        logger.info(f"Successfully created SwaphereAuth with wallet address: {auth.address}")

        return True
    except Exception as e:
        logger.error(f"Error initializing SwaphereAuth: {e}")
        return False


if __name__ == "__main__":
    success = main()
    if success:
        logger.info("Test completed successfully")
    else:
        logger.error("Test failed")
