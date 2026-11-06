"""Shared JSON message protocol for the TCP and UDP demonstrations."""
from __future__ import annotations

import json
from typing import Any

MAX_MESSAGE_BYTES = 4096


def encode_message(message: dict[str, Any]) -> bytes:
    """Encode one JSON object as UTF-8; TCP callers append the newline delimiter."""
    if not isinstance(message, dict):
        raise ValueError("message must be a JSON object")
    try:
        payload = json.dumps(message, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"message is not JSON serializable: {exc}") from exc
    if len(payload) > MAX_MESSAGE_BYTES:
        raise ValueError(f"message exceeds {MAX_MESSAGE_BYTES} bytes")
    return payload


def decode_message(payload: bytes) -> dict[str, Any]:
    """Decode a complete JSON object from bytes, rejecting oversized or invalid data."""
    if not isinstance(payload, bytes):
        raise ValueError("payload must be bytes")
    if len(payload) > MAX_MESSAGE_BYTES:
        raise ValueError(f"message exceeds {MAX_MESSAGE_BYTES} bytes")
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON message: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("message must be a JSON object")
    return value


def make_request(message: str, request_id: str = "1") -> dict[str, Any]:
    """Create a validated echo request shared by both transports."""
    if not isinstance(message, str) or not message.strip():
        raise ValueError("message must be a non-empty string")
    return {"id": str(request_id), "type": "echo", "message": message}


def make_response(request: dict[str, Any]) -> dict[str, Any]:
    """Build an echo response, or a structured error for unsupported requests."""
    request_id = str(request.get("id", ""))
    if request.get("type") != "echo":
        return {"id": request_id, "status": "error", "error": "unsupported request type"}
    message = request.get("message")
    if not isinstance(message, str) or not message.strip():
        return {"id": request_id, "status": "error", "error": "message must be a non-empty string"}
    return {"id": request_id, "status": "ok", "message": message}
