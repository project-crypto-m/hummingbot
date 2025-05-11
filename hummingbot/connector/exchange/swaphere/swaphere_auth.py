import json
import secrets
import time
from typing import Any, Dict

from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3

from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.data_types import RESTRequest, WSRequest


class SwaphereAuth(AuthBase):
    """
    Auth class for Swaphere exchange using private key authentication
    """

    def __init__(self, private_key: str):
        if private_key is None:
            # For non-trading uses, create a dummy key
            private_key = "0x" + secrets.token_hex(32)

        if private_key.startswith("0x"):
            private_key = private_key[2:]

        self.private_key = private_key
        self.account = Account.from_key(private_key)
        self.address = self.account.address
        self.web3 = Web3()

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        """
        Adds the auth headers for REST request
        For Swaphere, we'll send the signed intent in the payload
        """
        # No authentication needed for public endpoints
        return request

    async def ws_authenticate(self, request: WSRequest) -> WSRequest:
        """
        Adds auth info to the websocket connection request
        """
        # Build auth message for websocket
        timestamp = str(int(time.time()))

        auth_params = {"op": "login", "args": [{"address": self.address, "timestamp": timestamp}]}

        # Add auth params to the payload
        request.payload = auth_params

        return request

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
        Simplified implementation using web3 and eth-account
        """
        # If solver not provided, use own wallet address
        if solver is None:
            solver = self.address

        sender = self.address
        nonce = 0
        timestamp = int(time.time()) + expiration_minutes * 60

        max_out_amount = int(round(out_amount * (10 ** out_token["decimal"])))
        max_in_amount = int(round(in_amount * (10 ** in_token["decimal"])))

        # Create a structured message that simulates the EIP-712 message
        # In a full implementation, this would use proper EIP-712 typing
        message = {
            "isFullOrder": is_full_order,
            "nonce": nonce,
            "timestamp": timestamp,
            "solver": solver,
            "outToken": out_token["address"],
            "outAmount": str(max_out_amount),
            "inToken": in_token["address"],
            "inAmount": str(max_in_amount),
        }

        # Convert message to a signable format
        message_json = json.dumps(message, sort_keys=True)
        message_hash = self.web3.keccak(text=message_json)

        # Sign the message
        signable_message = encode_defunct(primitive=message_hash)
        signed_message = self.account.sign_message(signable_message)
        signature = signed_message.signature.hex()

        # For a simplified implementation, just return the signature and message in a format
        # that can be decoded by the server
        intent = {
            "message": message,
            "signature": signature,
            "sender": sender,
        }

        return json.dumps(intent)

    def _get_domain(self, blockchain_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get EIP-712 domain data"""
        return {
            "name": blockchain_context.get("name", "Swaphere"),
            "version": blockchain_context.get("version", "1"),
            "chainId": blockchain_context.get("chainId", 1),
            "verifyingContract": blockchain_context.get("verifyingContract", ""),
        }
