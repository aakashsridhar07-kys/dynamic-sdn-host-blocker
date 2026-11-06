"""Pure validation and policy helpers for the SDN controller API."""

from __future__ import annotations

import ipaddress


def normalize_ipv4(value: str) -> str:
    """Return a canonical IPv4 address or raise ValueError."""
    if not isinstance(value, str):
        raise ValueError("IP address must be a string")
    try:
        address = ipaddress.ip_address(value.strip())
    except ValueError as exc:
        raise ValueError("A valid IPv4 address is required") from exc
    if address.version != 4:
        raise ValueError("Only IPv4 addresses are supported")
    if address.is_unspecified or address.is_multicast:
        raise ValueError("Unspecified and multicast addresses cannot be blocked")
    return str(address)


def validate_block_seconds(value: object) -> int:
    """Validate a hard-timeout duration; zero means no automatic expiry."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("block_seconds must be an integer")
    if value < 0 or value > 65535:
        raise ValueError("block_seconds must be between 0 and 65535")
    return value
