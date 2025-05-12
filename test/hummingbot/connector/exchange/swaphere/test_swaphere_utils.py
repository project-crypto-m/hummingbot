import re
import time
from datetime import datetime
from typing import Tuple

# === Swaphere Utils Functions ===


def split_trading_pair(trading_pair: str) -> Tuple[str, str]:
    """
    Splits a trading pair into base and quote assets
    Example: ETH-USDC or ETH/USDC -> (ETH, USDC)
    """
    if "-" in trading_pair:
        base, quote = trading_pair.split("-")
        return base, quote
    elif "/" in trading_pair:
        base, quote = trading_pair.split("/")
        return base, quote
    else:
        # Try regex pattern (this is a simplified version)
        pattern = re.compile(r"^(\w+)[-/](\w+)$")
        m = pattern.match(trading_pair)
        if m is None:
            raise ValueError(f"Could not parse trading pair {trading_pair}")
        return m.group(1), m.group(2)


def convert_from_exchange_trading_pair(exchange_trading_pair: str) -> str:
    """
    Convert from exchange format to client format
    Swaphere uses format like "ETH-USDC" so we'll keep it
    """
    return exchange_trading_pair


def convert_to_exchange_trading_pair(hb_trading_pair: str) -> str:
    """
    Convert from client format to exchange format
    Ensure consistent format with dash separator
    """
    if "/" in hb_trading_pair:
        base, quote = hb_trading_pair.split("/")
        return f"{base}-{quote}"
    return hb_trading_pair


def get_new_client_order_id(is_buy: bool, trading_pair: str) -> str:
    """
    Creates a client order id for a new order
    Format: B/S-{trading_pair}-{timestamp}-{nonce}
    """
    side = "B" if is_buy else "S"
    ts = int(datetime.now().timestamp() * 1000)
    import random

    nonce = random.randint(1000, 9999)  # Use random nonce for uniqueness
    return f"{side}-{trading_pair}-{ts}-{nonce}"


# === Web Utils Functions ===


def public_rest_url(path_url: str, domain: str = None) -> str:
    """
    Creates a full URL for public REST endpoints
    :param path_url: the specific endpoint path
    :param domain: the domain to connect to
    :return: the full URL for public endpoint
    """
    base_url = domain or "http://127.0.0.1:8088"  # Default server URL
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


# === Test Functions ===


def test_split_trading_pair():
    """Test the split_trading_pair function"""
    test_cases = [
        ("ETH-USDC", ("ETH", "USDC")),
        ("ETH/USDC", ("ETH", "USDC")),
        ("BTC-USDT", ("BTC", "USDT")),
    ]

    for input_pair, expected_output in test_cases:
        result = split_trading_pair(input_pair)
        assert result == expected_output, f"Failed for {input_pair}: expected {expected_output}, got {result}"
        print(f"✅ split_trading_pair({input_pair}) => {result}")


def test_convert_trading_pairs():
    """Test the convert_from/to_exchange_trading_pair functions"""
    # Test convert to exchange format
    test_cases = [
        ("ETH/USDC", "ETH-USDC"),
        ("ETH-USDC", "ETH-USDC"),
        ("BTC/USDT", "BTC-USDT"),
    ]

    for input_pair, expected_output in test_cases:
        result = convert_to_exchange_trading_pair(input_pair)
        assert result == expected_output, f"Failed for {input_pair}: expected {expected_output}, got {result}"
        print(f"✅ convert_to_exchange_trading_pair({input_pair}) => {result}")

    # Test convert from exchange format
    test_cases = [
        ("ETH-USDC", "ETH-USDC"),
        ("BTC-USDT", "BTC-USDT"),
    ]

    for input_pair, expected_output in test_cases:
        result = convert_from_exchange_trading_pair(input_pair)
        assert result == expected_output, f"Failed for {input_pair}: expected {expected_output}, got {result}"
        print(f"✅ convert_from_exchange_trading_pair({input_pair}) => {result}")


def test_get_new_client_order_id():
    """Test the get_new_client_order_id function"""
    # Just check format and uniqueness
    buy_id = get_new_client_order_id(True, "ETH-USDC")
    time.sleep(0.001)  # Small sleep to ensure different timestamps
    sell_id = get_new_client_order_id(False, "ETH-USDC")

    assert buy_id.startswith("B-ETH-USDC-"), f"Buy ID has wrong format: {buy_id}"
    assert sell_id.startswith("S-ETH-USDC-"), f"Sell ID has wrong format: {sell_id}"
    assert buy_id != sell_id, "Generated IDs should be unique"

    time.sleep(0.001)  # Small sleep to ensure different timestamps
    buy_id2 = get_new_client_order_id(True, "ETH-USDC")
    assert buy_id != buy_id2, "Generated IDs should be unique even for same side"

    print(f"✅ get_new_client_order_id(True, 'ETH-USDC') => {buy_id}")
    print(f"✅ get_new_client_order_id(False, 'ETH-USDC') => {sell_id}")


def test_rest_urls():
    """Test the URL building functions"""
    path = "/api/products"
    default_domain = "http://127.0.0.1:8088"
    custom_domain = "https://api.swaphere.com"

    # Test with default domain
    public_url = public_rest_url(path)
    assert public_url == f"{default_domain}{path}", f"Wrong public URL: {public_url}"
    print(f"✅ public_rest_url('{path}') => {public_url}")

    private_url = private_rest_url(path)
    assert private_url == f"{default_domain}{path}", f"Wrong private URL: {private_url}"
    print(f"✅ private_rest_url('{path}') => {private_url}")

    # Test with custom domain
    public_url = public_rest_url(path, custom_domain)
    assert public_url == f"{custom_domain}{path}", f"Wrong public URL with custom domain: {public_url}"
    print(f"✅ public_rest_url('{path}', '{custom_domain}') => {public_url}")

    private_url = private_rest_url(path, custom_domain)
    assert private_url == f"{custom_domain}{path}", f"Wrong private URL with custom domain: {private_url}"
    print(f"✅ private_rest_url('{path}', '{custom_domain}') => {private_url}")


def test_format_trading_pair():
    """Test the format_trading_pair function"""
    test_cases = [
        ("ETH/USDC", "ETH-USDC"),
        ("ETH-USDC", "ETH-USDC"),
        ("BTC/USDT", "BTC-USDT"),
    ]

    for input_pair, expected_output in test_cases:
        result = format_trading_pair(input_pair)
        assert result == expected_output, f"Failed for {input_pair}: expected {expected_output}, got {result}"
        print(f"✅ format_trading_pair({input_pair}) => {result}")


# === Main Function ===


def main():
    print("\n=== Testing Swaphere Utils ===\n")

    print("\n--- Testing split_trading_pair() ---")
    test_split_trading_pair()

    print("\n--- Testing convert_trading_pairs() ---")
    test_convert_trading_pairs()

    print("\n--- Testing get_new_client_order_id() ---")
    test_get_new_client_order_id()

    print("\n--- Testing rest_urls() ---")
    test_rest_urls()

    print("\n--- Testing format_trading_pair() ---")
    test_format_trading_pair()

    print("\n✨ All tests passed! ✨\n")


if __name__ == "__main__":
    main()
