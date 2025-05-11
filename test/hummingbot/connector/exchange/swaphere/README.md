# Swaphere Connector Testing Guide

This directory contains tests for the Swaphere connector. The tests are designed to verify the functionality of the connector with a local Swaphere server.

## Prerequisites

1. A running Swaphere server at `localhost:8088`
2. Python 3.8+
3. Hummingbot environment set up

## Test Structure

The tests are organized into several files:

- **test_swaphere_basic.py**: Tests basic components like auth, web utils, and utility functions
- **test_swaphere_connector.py**: Tests the SwaphereExchange connector class
- **test_swaphere_utils.py**: Tests utility functions specific to the Swaphere connector
- **test_local_server.py**: Tests connectivity with a local Swaphere server
- **run_tests.py**: Script to run all tests

## Running Tests

### 1. Start the Swaphere server

Make sure the Swaphere server is running at `localhost:8088` before running the tests.

### 2. Run Individual Tests

You can run individual test files using Python:

```bash
# Run basic component tests
python test_swaphere_basic.py

# Run connector tests
python test_swaphere_connector.py

# Run utility tests
python test_swaphere_utils.py

# Run local server tests
python test_local_server.py
```

### 3. Run All Tests

To run all tests at once, use the `run_tests.py` script:

```bash
python run_tests.py
```

## Test Configuration

The tests use a test private key and ETH-USDC as the default trading pair. These can be modified in the test files if needed.

### Test Private Key

```
0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
```

**Important**: This private key is for testing only. Do not use it in a production environment.

### Trading Pair

The tests use `ETH-USDC` as the default trading pair. Ensure your Swaphere server has this pair available.

## Troubleshooting

### Connection Issues

If tests fail due to connection issues:

1. Verify the Swaphere server is running at `localhost:8088`
2. Check the server logs for errors
3. Ensure the correct ports are open (8088 for HTTP, WS)

### Order Test Issues

If order tests fail:

1. Check if the server supports the test trading pair (ETH-USDC)
2. Verify the server has order book data for the test trading pair
3. Ensure the test private key has sufficient balance for placing orders

## Extending Tests

To add more tests:

1. Create a new test file in this directory
2. Import the necessary modules
3. Add test functions
4. Update `run_tests.py` to include your new tests

## Server Mocking

For CI/CD environments where running a real server might not be possible, this directory includes a mock server implementation in `mock_server.py`.

### Starting the Mock Server

To use the mock server instead of a real Swaphere server:

```bash
# Start the mock server
python mock_server.py
```

The mock server runs on port 8088 by default and provides:

- REST API endpoints that simulate the Swaphere API
- WebSocket server for order book and trade updates
- Mock order placement and cancellation

### Mock Server Features

The mock server includes:

- Mock order books for ETH-USDC and BTC-USDC trading pairs
- Simulated order book updates via WebSocket
- Simulated trade data
- Order tracking for placed and canceled orders
- API endpoints matching the real Swaphere server

### Simulated Data

The mock server generates random order book data that changes over time to simulate a real market. It supports:

- Order book retrieval with bids and asks
- Trade history with simulated trade data
- Order placement and tracking
- Order cancellation

This allows for comprehensive testing of the connector without needing access to a real Swaphere server. 