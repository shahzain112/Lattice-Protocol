import json
import time
import asyncio
from typing import Dict
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from main import handle_request
import uvicorn

app = FastAPI(
    title="Lattice Protocol",
    description="Secure AI/Data/Blockchain Gateway",
    version="2.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# Request size limit (10MB max)
MAX_REQUEST_SIZE = 10 * 1024 * 1024

# WebSocket Connection Tracking
_active_connections: Dict[str, WebSocket] = {}
_max_ws_connections = 100

# ==========================================
# HTTP ENDPOINTS
# ==========================================

@app.post("/lattice/v1/execute")
async def execute(request: Request):
    """Execute a Lattice protocol action."""
    try:
        content_length = request.headers.get('content-length')
        if content_length and int(content_length) > MAX_REQUEST_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Request too large. Max size: {MAX_REQUEST_SIZE} bytes"
            )

        raw_body = await request.body()
        client_ip = request.client.host if request.client else "unknown"

        response_json = handle_request(raw_body, client_id=client_ip)
        response_data = json.loads(response_json)

        if response_data.get("status") == "error":
            error_msg = response_data.get("error", "")
            if "expired" in error_msg.lower():
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error_msg)
            elif "rate limit" in error_msg.lower():
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=error_msg)
            elif "not available" in error_msg.lower():
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=error_msg)
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

        return response_data

    except HTTPException:
        raise
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON in request body"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/lattice/v1/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "Lattice is alive and secure!",
        "version": "2.0.0",
        "timestamp": int(time.time()),
        "active_ws_connections": len(_active_connections)
    }

# ✅ FIXED: 'status' → 'get_server_status' (taake fastapi.status override na ho)
@app.get("/lattice/v1/status")
async def get_server_status():
    """Detailed status endpoint."""
    return {
        "status": "operational",
        "version": "2.0.0",
        "features": [
            "health_check", "process_data", "get_balance",
            "check_multisig", "submit_game_score", "migrate_database",
            "enable_extension", "run_swarm", "store_vector", "multichain_balance"
        ],
        "websocket": {
            "enabled": True,
            "max_connections": _max_ws_connections,
            "active": len(_active_connections)
        },
        "timestamp": int(time.time())
    }

# ==========================================
# WEBSOCKET ENDPOINT
# ==========================================

@app.websocket("/lattice/v1/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication."""
    client_id = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "unknown"

    # Connection Limit Check
    if len(_active_connections) >= _max_ws_connections:
        await websocket.close(code=1008, reason="Server at max capacity")
        return

    await websocket.accept()
    _active_connections[client_id] = websocket

    try:
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "client_id": client_id,
            "message": "Lattice WebSocket connected"
        }))

        # Message Loop with Validation
        message_count = 0
        max_messages_per_minute = 60
        last_minute_start = time.time()

        while True:
            # Rate limit check
            current_time = time.time()
            if current_time - last_minute_start >= 60:
                message_count = 0
                last_minute_start = current_time

            if message_count >= max_messages_per_minute:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "error": "Rate limit exceeded: 60 messages/minute"
                }))
                await asyncio.sleep(1)
                continue

            # Receive with timeout
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({
                    "type": "ping",
                    "message": "Connection alive"
                }))
                continue

            # Validate message size
            if len(data) > 65536:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "error": "Message too large (max 64KB)"
                }))
                continue

            # Validate JSON
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "error": "Invalid JSON format"
                }))
                continue

            # Validate required fields
            if not isinstance(message, dict) or "action" not in message:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "error": "Message must contain 'action' field"
                }))
                continue

            # Process message
            message_count += 1
            action = message.get("action")

            if action == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": int(time.time())
                }))

            elif action == "subscribe":
                channel = message.get("channel", "default")
                await websocket.send_text(json.dumps({
                    "type": "subscribed",
                    "channel": channel
                }))

            elif action == "game_event":
                await websocket.send_text(json.dumps({
                    "type": "game_event_ack",
                    "data": message.get("data", {})
                }))

            elif action == "ai_stream":
                prompt = message.get("prompt", "")
                await websocket.send_text(json.dumps({
                    "type": "ai_stream_start",
                    "prompt_length": len(prompt)
                }))
                await websocket.send_text(json.dumps({
                    "type": "ai_stream_end",
                    "message": "Stream complete"
                }))

            else:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "error": f"Unknown action: {action}"
                }))

    except WebSocketDisconnect:
        print(f"🔌 WebSocket disconnected: {client_id}")
    except Exception as e:
        print(f"❌ WebSocket error for {client_id}: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "error": f"Server error: {str(e)}"
            }))
        except:
            pass
    finally:
        if client_id in _active_connections:
            del _active_connections[client_id]
        try:
            await websocket.close()
        except:
            pass

# ==========================================
# RATE LIMITED SECURE ENDPOINT
# ==========================================

@app.get("/lattice/v1/secure")
async def secure_endpoint(request: Request):
    """Secure endpoint with rate limiting."""
    client_ip = request.client.host if request.client else "unknown"

    from main import _check_rate_limit

    if not _check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded: 100 requests/minute"
        )

    return {
        "status": "success",
        "client": client_ip,
        "timestamp": int(time.time())
    }

if __name__ == "__main__":
    print("🌐 Lattice HTTP + WebSocket Server v2.0")
    print("🔗 HTTP:    http://localhost:8080/lattice/v1/execute")
    print("⚡ WebSocket: ws://localhost:8080/lattice/v1/ws")
    print("🛡️  Security: CORS, Rate limiting, WS validation")

    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")