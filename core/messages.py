"""
Lattice Message Protocol
Core message types for the Lattice ecosystem.
"""

import json
import time
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class LatticeRequest(BaseModel):
    """Standard request format for Lattice protocol."""
    request_id: str
    action: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[int] = None
    signature: Optional[str] = None

    model_config = {"extra": "allow"}


class LatticeResponse(BaseModel):
    """Standard response format for Lattice protocol."""
    request_id: str
    status: str  # "success" or "error"
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    model_config = {"extra": "allow"}


def parse_secure_request(raw_input: bytes) -> LatticeRequest:
    """
    Parse and validate incoming request.

    Args:
        raw_input: Raw JSON bytes

    Returns:
        LatticeRequest object

    Raises:
        ValueError: If request is invalid
        json.JSONDecodeError: If JSON is malformed
    """
    try:
        data = json.loads(raw_input.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise json.JSONDecodeError("Invalid JSON format", str(e), 0)

    # Validate required fields
    if not isinstance(data, dict):
        raise ValueError("Request must be a JSON object")

    if "request_id" not in data:
        raise ValueError("Missing required field: request_id")

    if "action" not in data:
        raise ValueError("Missing required field: action")

    if not isinstance(data.get("request_id"), str):
        raise ValueError("request_id must be a string")

    if not isinstance(data.get("action"), str):
        raise ValueError("action must be a string")

    # Set default timestamp if not provided
    if "timestamp" not in data:
        data["timestamp"] = int(time.time())

    return LatticeRequest(**data)