# SwapHere Connector

This is a connector for the SwapHere exchange, which allows Hummingbot to interact with the SwapHere trading platform.

## Features

- Connects to SwapHere exchange using Ethereum private key authentication
- Supports order placement and cancellation
- Tracks order books and trades
- Uses EIP-712 compliant message signing for order intent

## Configuration

To use the SwapHere connector, you need to provide your Ethereum private key in the Hummingbot configuration.

Example configuration:

```
connector: swaphere
swaphere_private_key: YOUR_ETHEREUM_PRIVATE_KEY
```

## Trading Pairs

SwapHere uses the format `BASE-QUOTE` for trading pairs (e.g., `ETH-USDC`).

## Architecture

The SwapHere connector uses a special "proxy class" pattern to avoid circular imports in the Hummingbot codebase:

1. `__init__.py` - Contains a proxy class for connector registration
2. `swaphere_exchange.py` - The actual implementation using lazy imports
3. `swaphere_auth.py` - Authentication class using eth-account and Web3
4. `swaphere_utils.py` - Utility functions and connector configuration
5. `swaphere_constants.py` - Constants for API endpoints and parameters

### Proxy Class Pattern

To prevent circular imports while maintaining compatibility with Hummingbot's connector registration system, this connector uses a proxy class pattern:

- The `__init__.py` file defines a lightweight `SwaphereExchange` class
- This proxy class is registered with Hummingbot
- The proxy class's `get_implementation` method imports and returns the actual implementation
- The real implementation lives in `swaphere_exchange.py` and uses late binding imports

### Configuration Notes

Although this connector uses Ethereum private keys for authentication, it's configured with `USE_ETHEREUM_WALLET = False` in the settings to ensure it appears in Hummingbot's connect options. The private key is handled internally as if it were a regular API key.

## Dependencies

This connector requires the following dependencies:
- web3
- eth-account
- hexbytes

## Server Configuration

By default, the connector connects to `http://127.0.0.1:8088`. This can be customized in `swaphere_constants.py`.

## Testing

See the tests directory for details on testing the connector. 