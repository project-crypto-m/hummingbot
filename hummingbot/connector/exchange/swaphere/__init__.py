# Define SwaphereExchange here to avoid circular imports but still expose the class
# This allows the `connect swaphere` command to work properly
class SwaphereExchange:
    @classmethod
    def get_implementation(cls, *args, **kwargs):
        # Import real implementation only when needed
        from hummingbot.connector.exchange.swaphere.swaphere_exchange import SwaphereExchange as SwaphereExchangeImpl

        return SwaphereExchangeImpl(*args, **kwargs)


# Expose the connector class for proper registration
__all__ = ["SwaphereExchange"]
