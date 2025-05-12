#!/usr/bin/env python
import unittest
from unittest.mock import patch


class SwaphereImportTest(unittest.TestCase):
    def test_import_connector(self):
        """
        Test that the connector can be imported without circular dependency issues
        """
        try:
            # Try importing from different places to ensure no circular imports
            from hummingbot.client.settings import AllConnectorSettings

            self.assertTrue("swaphere" in AllConnectorSettings.get_connector_settings())

            # Test direct import of exchange class from __init__.py (proxy class)
            from hummingbot.connector.exchange.swaphere import SwaphereExchange

            # Verify this is the proxy class (not the actual implementation)
            self.assertTrue(hasattr(SwaphereExchange, "get_implementation"))

            # Test that the real implementation can be imported
            import hummingbot.connector.exchange.swaphere.swaphere_exchange  # noqa: F401

            # Verify the proxy class can get the implementation
            with patch("hummingbot.connector.exchange.swaphere.swaphere_exchange.SwaphereExchange") as mocked_impl:
                # Set up the mock to return itself when instantiated
                mocked_impl.return_value = "mocked_instance"
                # Call the get_implementation method
                result = SwaphereExchange.get_implementation(test_arg="test_val")
                # Verify the implementation was called with the correct arguments
                mocked_impl.assert_called_once_with(test_arg="test_val")
                self.assertEqual(result, "mocked_instance")

            # Test utils import
            from hummingbot.connector.exchange.swaphere.swaphere_utils import (
                CENTRALIZED,
                DEFAULT_FEES,
                EXAMPLE_PAIR,
                USE_ETHEREUM_WALLET,
            )

            self.assertEqual(CENTRALIZED, False)
            self.assertEqual(EXAMPLE_PAIR, "ETH-USDC")
            self.assertEqual(DEFAULT_FEES, [0.1, 0.1])
            self.assertEqual(USE_ETHEREUM_WALLET, False)

            # Test connect command validator
            from hummingbot.client.config.config_validators import validate_connector

            result = validate_connector("swaphere")
            self.assertIsNone(result)  # None means valid

            # Check if it's in the connect options
            from hummingbot.client.command.connect_command import OPTIONS

            self.assertTrue("swaphere" in OPTIONS)

            print("All imports successful - no circular import issues!")

        except Exception as e:
            self.fail(f"Failed to import SwapHere connector: {str(e)}")


if __name__ == "__main__":
    unittest.main()
