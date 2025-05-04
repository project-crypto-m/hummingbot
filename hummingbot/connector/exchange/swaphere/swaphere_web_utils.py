import json
import aiohttp
from typing import Callable, Dict, Any, Optional

from hummingbot.connector.exchange.swaphere import swaphere_constants as CONSTANTS
from hummingbot.core.web_assistant.connections.data_types import RESTMethod, RESTResponse
from hummingbot.core.web_assistant.rest_assistant import RESTAssistant
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory


def public_rest_url(path_url: str, domain: str = None) -> str:
    """
    Creates a full URL for public REST endpoints
    :param path_url: the specific endpoint path
    :param domain: the domain to connect to
    :return: the full URL for public endpoint
    """
    base_url = domain or CONSTANTS.SWAPHERE_BASE_URL
    return f"{base_url.rstrip('/')}{path_url}"


def private_rest_url(path_url: str, domain: str = None) -> str:
    """
    Creates a full URL for private REST endpoints
    :param path_url: the specific endpoint path
    :param domain: the domain to connect to
    :return: the full URL for private endpoint
    """
    # For Swaphere, public and private URLs are the same
    return public_rest_url(path_url, domain)


def build_api_error_message(status_code: int, response_body: Dict[str, Any]) -> str:
    """
    Builds a comprehensive error message from the API response
    :param status_code: the HTTP status code
    :param response_body: the response body in dict form
    :return: a comprehensive error message
    """
    error = response_body.get("error", "") or response_body.get("message", "")
    return f"Error executing request {status_code}: {error}"


async def api_request(
    path: str,
    api_factory: WebAssistantsFactory,
    rest_method: RESTMethod = RESTMethod.GET,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    is_auth_required: bool = False,
    domain: str = None,
) -> Dict[str, Any]:
    """
    Makes an API request to Swaphere
    :param path: the path for the API endpoint
    :param api_factory: the web assistant factory to create the REST assistant
    :param rest_method: the HTTP method
    :param params: additional parameters for the request
    :param data: data to include in the request body
    :param is_auth_required: whether authentication is required
    :param domain: the domain to connect to
    :return: the response from the API
    """
    rest_assistant: RESTAssistant = await api_factory.get_rest_assistant()
    
    if is_auth_required:
        url = private_rest_url(path, domain)
    else:
        url = public_rest_url(path, domain)
        
    headers = {"Content-Type": "application/json"} if data else {}
    
    response = await rest_assistant.execute_request(
        method=rest_method,
        url=url,
        params=params,
        data=json.dumps(data) if data else None,
        headers=headers,
    )
    
    if response.status != 200:
        response_json = await response.json()
        raise IOError(build_api_error_message(response.status, response_json))
    
    response_json = await response.json()
    return response_json


def format_trading_pair(trading_pair: str) -> str:
    """
    Formats the trading pair to the exchange format (if needed)
    :param trading_pair: the trading pair in hummingbot format
    :return: the trading pair in exchange format
    """
    # Ensure consistent format with dash separator
    if "/" in trading_pair:
        base, quote = trading_pair.split("/")
        return f"{base}-{quote}"
    return trading_pair 