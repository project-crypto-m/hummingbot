import time
from typing import Dict, Any, Optional
import json

from ethers import Wallet
from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.data_types import RESTRequest, WSRequest
from hummingbot.connector.exchange.swaphere.swaphere_constants import DEFAULT_BLOCKCHAIN_CONTEXT, TYPES


class SwaphereAuth(AuthBase):
    """
    Auth class for Swaphere exchange using private key authentication
    """
    def __init__(self, private_key: str):
        self.private_key = private_key
        self.wallet = Wallet(private_key)
        self.address = self.wallet.address

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
        
        auth_params = {
            "op": "login",
            "args": [{
                "address": self.address,
                "timestamp": timestamp
            }]
        }
        
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
        
        max_out_amount = int(round(out_amount * (10 ** out_token["decimal"])))
        max_in_amount = int(round(in_amount * (10 ** in_token["decimal"])))
        
        # Create packed header and instructions using ethers.js solidityPacked
        header_and_instructions = self.wallet.provider._encode_packed(
            ["uint8", "uint24", "uint64", "address", "address", "uint128", "address", "uint128"],
            [
                1 if is_full_order else 0, 
                nonce, 
                timestamp, 
                solver, 
                out_token["address"], 
                str(max_out_amount), 
                in_token["address"], 
                str(max_in_amount)
            ]
        )
        
        # Get domain for signing
        domain = self._get_domain(blockchain_context)
        
        # Get values for signing
        value = {
            "isFullOrder": is_full_order,
            "nonce": nonce,
            "timestamp": timestamp,
            "solver": solver,
            "outToken": out_token["address"],
            "outAmount": str(max_out_amount),
            "inToken": in_token["address"],
            "inAmount": str(max_in_amount)
        }
        
        # Sign the typed data using EIP-712
        signature = await self.wallet.signTypedData(domain, TYPES, value)
        
        # Construct the final intent based on order type
        if is_full_order:
            return self.wallet.provider._encode_packed(
                ["address", "address", "uint16", "uint16", "uint16", "bytes", "bytes"],
                [sender, standard, header_length, instruction_length, signature_length, header_and_instructions, signature]
            )
        else:
            return self.wallet.provider._encode_packed(
                ["address", "address", "uint16", "uint16", "uint16", "bytes", "uint128", "bytes"],
                [sender, standard, header_length, instruction_length, signature_length, header_and_instructions, 0, signature]
            )
    
    def _get_domain(self, blockchain_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get EIP-712 domain data"""
        return {
            "name": blockchain_context.get("name", "Swaphere"),
            "version": blockchain_context.get("version", "1"),
            "chainId": blockchain_context.get("chainId", 1),
            "verifyingContract": blockchain_context.get("verifyingContract", "")
        } 