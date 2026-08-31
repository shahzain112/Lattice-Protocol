from pydantic import BaseModel, Field, ValidationError
from typing import Optional, Dict, Any
import json

class LatticeRequest(BaseModel):
    request_id: str = Field(min_length=10, max_length=64)
    action: str = Field(pattern=r'^[a-zA-Z0-9_\.]+$')
    payload: Dict[str, Any]
    timestamp: int

class LatticeResponse(BaseModel):
    request_id: str
    status: str = Field(pattern=r'^(success|error|pending)$')
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

def parse_secure_request(raw_bytes: bytes) -> LatticeRequest:
    try:
        data = json.loads(raw_bytes.decode())
        return LatticeRequest(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        raise ValueError(f"Malicious request blocked: {e}")