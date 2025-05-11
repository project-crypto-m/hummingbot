import asyncio
import hashlib
import time
from typing import Any, Dict

from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3

# Constants from swaphere_constants.py
DEFAULT_BLOCKCHAIN_CONTEXT = {
    "partialTokenSwapStandard": "0x1234567890123456789012345678901234567890",
    "name": "Swaphere",
    "version": "1",
    "chainId": 1,
    "verifyingContract": "0x0987654321098765432109876543210987654321"
}

# Mock token information
ETH_TOKEN = {
    "address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "decimal": 18
}

USDC_TOKEN = {
    "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "decimal": 6
}


# Simplified SwaphereAuth class
class SwaphereAuth:
    """Simplified Auth class for Swaphere exchange using private key authentication"""
    def __init__(self, private_key: str):
        if private_key.startswith("0x"):
            private_key = private_key[2:]
        self.private_key = private_key
        self.account = Account.from_key(private_key)
        self.address = self.account.address
        self.web3 = Web3()
        print(f"Initialized account with address: {self.address}")

    async def build_intent(
        self,
        is_full_order: bool,
        out_token: Dict[str, Any],
        out_amount: float,
        in_token: Dict[str, Any],
        in_amount: float,
        expiration_minutes: int,
        solver: str = None,
    ) -> str:
        """
        Builds an order intent using private key for authentication
        Implementation of the buildIntent function from Swaphere
        """
        # If solver not provided, use own wallet address
        if solver is None:
            solver = self.address

        sender = self.address
        blockchain_context = DEFAULT_BLOCKCHAIN_CONTEXT
        standard = blockchain_context.get("partialTokenSwapStandard", "")
        header_length = 32
        instruction_length = 72 if is_full_order else 88
        signature_length = 65 if solver == self.address else 130
        nonce = 0
        timestamp = int(time.time()) + expiration_minutes * 60

        # Use smaller values for better compatibility
        max_out_amount = int(round(out_amount * (10 ** out_token["decimal"])))
        max_in_amount = int(round(in_amount * (10 ** in_token["decimal"])))

        print(f"Building intent with:")
        print(f"is_full_order: {is_full_order}")
        print(f"nonce: {nonce}")
        print(f"timestamp: {timestamp}")
        print(f"solver: {solver}")
        print(f"out_token: {out_token['address']}")
        print(f"out_amount: {max_out_amount}")
        print(f"in_token: {in_token['address']}")
        print(f"in_amount: {max_in_amount}")

        # Create a message for signing (using a simplified approach for testing)
        message = f"{1 if is_full_order else 0},{nonce},{timestamp},{solver},{out_token['address']},{max_out_amount},{in_token['address']},{max_in_amount}"
        message_hash = hashlib.sha256(message.encode()).hexdigest()

        print(f"Message to sign: {message}")
        print(f"Message hash: {message_hash}")

        # Sign the message (using the correct method)
        message_to_sign = encode_defunct(text=message)
        signed_message = self.account.sign_message(message_to_sign)
        signature = signed_message.signature.hex()
        print(f"Generated signature: {signature[:20]}...")

        # Header and instructions (simplified for testing)
        header_and_instructions = message_hash

        # Construct the final intent based on order type (simplified for testing)
        if is_full_order:
            print("Creating full order intent")
            intent = f"0x{sender}{standard}{header_and_instructions}{signature}"
        else:
            print("Creating partial order intent")
            intent = f"0x{sender}{standard}{header_and_instructions}0{signature}"

        print(f"Final intent (truncated): {intent[:50]}...")
        return intent

    def _get_domain(self, blockchain_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get EIP-712 domain data"""
        return {
            "name": blockchain_context.get("name", "Swaphere"),
            "version": blockchain_context.get("version", "1"),
            "chainId": blockchain_context.get("chainId", 1),
            "verifyingContract": blockchain_context.get("verifyingContract", "")
        }


# Test the auth implementation
async def test_swaphere_auth():
    # Test private key (this is a sample key, not a real one)
    private_key = "0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"

    print("\n=== Testing Swaphere Auth ===\n")

    try:
        # Create the auth instance
        auth = SwaphereAuth(private_key)

        # Test building a full order intent
        full_intent = await auth.build_intent(
            is_full_order=True,  # Full order (limit order)
            out_token=ETH_TOKEN,
            out_amount=0.01,  # Small amount for testing
            in_token=USDC_TOKEN,
            in_amount=20.0,  # Small amount for testing
            expiration_minutes=60,
            solver=None  # Use own address
        )

        print("\nFull order intent generated successfully")

        # Test building a partial order intent
        partial_intent = await auth.build_intent(
            is_full_order=False,  # Partial order (market order)
            out_token=ETH_TOKEN,
            out_amount=0.005,  # Small amount for testing
            in_token=USDC_TOKEN,
            in_amount=10.0,  # Small amount for testing
            expiration_minutes=30,
            solver=None  # Use own address
        )

        print("\nPartial order intent generated successfully")

        return True
    except Exception as e:
        print(f"Error testing Swaphere auth: {e}")
        import traceback
        traceback.print_exc()
        return False


# Main function
if __name__ == "__main__":
    asyncio.run(test_swaphere_auth())
