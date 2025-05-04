import asyncio
import logging
from typing import List, Optional

from hummingbot.connector.exchange.swaphere import swaphere_constants as CONSTANTS
from hummingbot.connector.exchange.swaphere.swaphere_auth import SwaphereAuth
from hummingbot.core.data_type.user_stream_tracker_data_source import UserStreamTrackerDataSource
from hummingbot.core.web_assistant.connections.data_types import WSJSONRequest
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory
from hummingbot.core.web_assistant.ws_assistant import WSAssistant
from hummingbot.logger import HummingbotLogger


class SwaphereAPIUserStreamDataSource(UserStreamTrackerDataSource):
    _logger: Optional[HummingbotLogger] = None
    
    def __init__(
        self,
        auth: SwaphereAuth,
        trading_pairs: List[str] = None,
        web_assistants_factory: Optional[WebAssistantsFactory] = None,
    ):
        super().__init__()
        self._auth = auth
        self._trading_pairs = trading_pairs or []
        self._web_assistants_factory = web_assistants_factory or WebAssistantsFactory(auth=self._auth)
        self._ws_assistant: Optional[WSAssistant] = None
        
    @classmethod
    def logger(cls) -> HummingbotLogger:
        if cls._logger is None:
            cls._logger = logging.getLogger(__name__)
        return cls._logger
        
    async def _connected_websocket_assistant(self) -> WSAssistant:
        """
        Creates a websocket assistant and connects it to the exchange
        :return: a websocket assistant
        """
        if self._ws_assistant is None:
            self._ws_assistant = await self._web_assistants_factory.get_ws_assistant()
            await self._ws_assistant.connect(
                ws_url=CONSTANTS.SWAPHERE_WS_URI,
                ping_timeout=30,
            )
            
            # Authenticate the websocket connection
            auth_request = await self._auth.ws_authenticate(WSJSONRequest(payload={}))
            await self._ws_assistant.send(auth_request)
            
            # Wait for the authentication response
            response = await self._ws_assistant.receive()
            if not self._is_valid_auth_response(response.data):
                self.logger().error("Failed to authenticate websocket connection")
                await self._ws_assistant.disconnect()
                self._ws_assistant = None
                raise ValueError("Websocket authentication failed")
                
            self.logger().info("Websocket authenticated successfully")
            
        return self._ws_assistant
        
    def _is_valid_auth_response(self, response_data: dict) -> bool:
        """
        Check if the authentication response is valid
        :param response_data: the response data
        :return: True if valid, False otherwise
        """
        # Implement based on the actual response structure from Swaphere
        return response_data.get("success", False) or not response_data.get("error")
        
    async def listen_for_user_stream(self, output: asyncio.Queue):
        """
        Subscribe to user account events and listen for updates
        :param output: a queue to put user stream messages into
        """
        ws = None
        try:
            ws = await self._connected_websocket_assistant()
            
            # Subscribe to orders channel
            orders_subscription = {
                "op": "subscribe",
                "channel": CONSTANTS.SWAPHERE_WS_ORDERS_CHANNEL,
                "address": self._auth.address
            }
            
            orders_request = WSJSONRequest(payload=orders_subscription)
            await ws.send(orders_request)
            
            self.logger().info(f"Subscribed to private orders channel for address {self._auth.address}")
            
            # Listen for messages
            async for ws_response in ws.iter_messages():
                data = ws_response.data
                
                # Check for subscription confirmation
                if data.get("type") == "subscribed" and data.get("channel") == CONSTANTS.SWAPHERE_WS_ORDERS_CHANNEL:
                    self.logger().info("Successfully subscribed to orders channel")
                    continue
                    
                # Order updates
                if data.get("channel") == CONSTANTS.SWAPHERE_WS_ORDERS_CHANNEL:
                    # Process order updates - wrap in a dictionary to maintain compatibility
                    output.put_nowait({"order": data})
                    
        except asyncio.CancelledError:
            raise
        except Exception:
            self.logger().exception("Unexpected error while listening to user stream. Retrying after 5 seconds...")
            await asyncio.sleep(5)
        finally:
            # Close the websocket if needed
            if ws is not None:
                await ws.disconnect()
                self._ws_assistant = None
                
    async def _create_listening_session(self) -> str:
        """
        Create a listening session - not required for Swaphere
        """
        return "swaphere_session" 