# Swaphere Connector Testing Guide

This directory contains tests for the Swaphere connector. The tests are designed to verify the functionality of the connector with a local Swaphere server.

## Prerequisites

1. A running Swaphere server at `localhost:8088`
2. Python 3.8+
3. Hummingbot environment set up
4. Required Python dependencies:
   - eth-account
   - web3
   - hexbytes
   - bidict
   - aioprocessing

## Test Structure

The tests are organized into several files:

- **test_swaphere_basic.py**: Tests basic components like auth, web utils, and utility functions
- **test_swaphere_connector.py**: Tests the SwaphereExchange connector class
- **test_swaphere_utils.py**: Tests utility functions specific to the Swaphere connector
- **test_swaphere_import.py**: Tests import dependencies to ensure no circular imports
- **test_local_server.py**: Tests connectivity with a local Swaphere server
- **run_tests.py**: Script to run all tests

## Important Notes About Circular Import Issues

The connector uses a "proxy class" pattern to avoid circular dependencies in the Hummingbot codebase while still allowing the connector to be properly registered for the "connect" command:

1. **__init__.py**: Contains a proxy `SwaphereExchange` class that defers actual implementation import
2. **dummy.py**: A placeholder file for initial registration
3. **swaphere_exchange.py**: The actual implementation class that uses late binding imports
4. **swaphere_utils.py**: Minimizes deep dependencies

### Proxy Class Pattern

The key technique for avoiding circular imports while maintaining "connect" command functionality is in `__init__.py`:

```python
# Define SwaphereExchange here to avoid circular imports but still expose the class
class SwaphereExchange:
    @classmethod
    def get_implementation(cls, *args, **kwargs):
        # Import real implementation only when needed
        from hummingbot.connector.exchange.swaphere.swaphere_exchange import SwaphereExchange as SwaphereExchangeImpl
        return SwaphereExchangeImpl(*args, **kwargs)

# Expose the proxy class for proper registration
__all__ = ["SwaphereExchange"]
```

This allows:
1. The connector registry to find the class
2. The "connect swaphere" command to use the proxy class
3. Circular imports to be avoided since the real implementation is only imported when needed

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

# Run import tests (ensure no circular dependencies)
python test_swaphere_import.py

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

### Circular Import Issues

If you encounter circular import errors, make sure the proxy class pattern is maintained in the connector files:

1. Keep the proxy class in `__init__.py`
2. Do not directly import the implementation class in `__init__.py`
3. Make sure the implementation class (`swaphere_exchange.py`) continues to use late binding imports with `importlib.import_module()`

### Connect Command Issues

If the "connect swaphere" command doesn't work:

1. Ensure `__all__ = ["SwaphereExchange"]` is present in `__init__.py`
2. Verify the proxy class is properly named `SwaphereExchange`
3. Make sure the `get_implementation` method in the proxy class properly imports and returns the actual implementation class

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