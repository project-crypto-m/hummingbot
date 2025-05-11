#!/usr/bin/env python3

import argparse
import asyncio
import logging
import sys

from mock_server import SwaphereMockServer
from test_local_server import run_all_tests as test_local_server
from test_swaphere_basic import main as test_basic
from test_swaphere_connector import main as test_connector
from test_swaphere_utils import main as test_utils

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_all_tests(use_mock=False):
    """Run all test modules for the Swaphere connector"""
    mock_server = None

    # Start mock server if requested
    if use_mock:
        logger.info("Starting mock Swaphere server...")
        mock_server = SwaphereMockServer()
        await mock_server.start()

    try:
        logger.info("=== Running Swaphere connector tests ===")

        logger.info("\n=== Basic Component Tests ===")
        basic_result = await test_basic()

        logger.info("\n=== Utility Tests ===")
        utils_result = await asyncio.create_task(test_utils())

        logger.info("\n=== Connector Tests ===")
        connector_result = await asyncio.create_task(test_connector())

        logger.info("\n=== Local Server Tests ===")
        server_result = await asyncio.create_task(test_local_server())

        # Print final results
        logger.info("\n=== Test Results Summary ===")
        logger.info(f"Basic tests: {'PASSED' if basic_result else 'FAILED'}")
        logger.info(f"Utility tests: {'PASSED' if utils_result else 'FAILED'}")
        logger.info(f"Connector tests: {'PASSED' if connector_result else 'FAILED'}")
        logger.info(f"Local server tests: {'PASSED' if server_result else 'FAILED'}")

        # Return overall status
        all_passed = all([basic_result, utils_result, connector_result, server_result])
        logger.info(f"\nOverall test result: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")

        return all_passed
    finally:
        # Stop the mock server if it was started
        if use_mock and mock_server is not None:
            logger.info("Stopping mock Swaphere server...")
            await mock_server.stop()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Run Swaphere connector tests')
    parser.add_argument('--mock', action='store_true', help='Use mock server instead of a real local server')
    args = parser.parse_args()

    if args.mock:
        logger.info("Using mock server for tests")
    else:
        logger.info("Using real local server for tests")

    result = asyncio.run(run_all_tests(use_mock=args.mock))
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
