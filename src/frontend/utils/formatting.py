"""
Formatting and utility functions for Data Insights frontend.
"""

def format_value(value, is_currency=False):
    """
    Format large numbers with K, M, B suffixes for better readability.

    Args:
        value: Number to format
        is_currency: Whether to add a dollar sign
    Returns:
        Formatted string
    """
    if abs(value) >= 1_000_000_000:
        formatted = f"{value/1_000_000_000:.2f}B"
    elif abs(value) >= 1_000_000:
        formatted = f"{value/1_000_000:.2f}M"
    elif abs(value) >= 1_000:
        formatted = f"{value/1_000:.1f}K"
    else:
        formatted = f"{value:.2f}"
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
    return f"${formatted}" if is_currency else formatted
