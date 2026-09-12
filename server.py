import json
import time
import asyncio
from typing import Dict
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from main import handle_request
import uvicorn
import bcrypt
import database
# Server start hone par DB auto-initialize hogi!
database.init_db()

app = FastAPI(
    title="Lattice Protocol",
    description="Secure AI/Data/Blockchain Gateway",
    version="2.0.0"
)

# CORS Configuration (Updated: allow_methods=["*"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Changed from True to False
    allow_methods=["*"],      # Changed from ["POST", "GET"] to ["*"]
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
    """Execute a Lattice protocol action with signature verification."""
    try:
        content_length = request.headers.get('content-length')
        if content_length and int(content_length) > MAX_REQUEST_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Request too large. Max size: {MAX_REQUEST_SIZE} bytes"
            )

        raw_body = await request.body()
        payload = json.loads(raw_body)

        # --- NAYA CODE: Identity Verification ---
        # Pehle IP use ho raha tha, ab public key use karein
        client_public_key = payload.get("sender_id")
        signature = payload.get("signature")

        if not client_public_key or not signature:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing sender_id or signature"
            )

        # Crypto Auth Import (from crypto_auth.py)
        from crypto_auth import verify_lattice_signature

        if not verify_lattice_signature(payload):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature or expired timestamp"
            )

        # Agar signature verified ho gaya, tabhi process karein
        # client_id ab public key hai (IP nahi)
        response_json = handle_request(raw_body, client_id=client_public_key)
        response_data = json.loads(response_json)

        # Always return JSONResponse with proper status code
        # but preserve the original Lattice response format
        if response_data.get("status") == "error":
            error_msg = response_data.get("error", "")
            if "expired" in error_msg.lower():
                http_code = status.HTTP_401_UNAUTHORIZED
            elif "rate limit" in error_msg.lower():
                http_code = status.HTTP_429_TOO_MANY_REQUESTS
            elif "not available" in error_msg.lower():
                http_code = status.HTTP_503_SERVICE_UNAVAILABLE
            elif "unknown" in error_msg.lower():
                http_code = status.HTTP_400_BAD_REQUEST
            else:
                http_code = status.HTTP_400_BAD_REQUEST
            
            # Return the ORIGINAL Lattice response format
            return JSONResponse(status_code=http_code, content=response_data)

        return JSONResponse(status_code=status.HTTP_200_OK, content=response_data)

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
        print(f"WebSocket disconnected: {client_id}")
    except Exception as e:
        print(f"WebSocket error for {client_id}: {e}")
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

# ==========================================
# DASHBOARD & UI ENDPOINTS (Secured)
# ==========================================

from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import Depends, HTTPException, status, Request, Form
import bcrypt
import time
import sqlite3
import database

# Brute Force Protection Tracker
_login_attempts = {}

def verify_admin(request: Request):
    """Secure verification with Brute Force protection"""
    client_ip = request.client.host if request.client else "unknown"
    if client_ip in _login_attempts and _login_attempts[client_ip]["count"] >= 3:
        block_time = time.time() - _login_attempts[client_ip]["last_attempt"]
        if block_time < 300:
            raise HTTPException(status_code=429, detail="Too many attempts. Blocked for 5 min.")
    
    session_token = request.cookies.get("lattice_session")
    if session_token and session_token == "valid_admin_session":
        return True
    raise HTTPException(status_code=401, detail="Not authenticated", headers={"Location": "/login"})

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return """
    <html>
        <head><title>Lattice Admin Login</title>
        <style>
            body { font-family: Arial; background: #f4f4f9; display: flex; justify-content: center; align-items: center; height: 100vh; }
            .login-box { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
            input { display: block; width: 100%; padding: 10px; margin: 10px 0; box-sizing: border-box; }
            button { width: 100%; padding: 10px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        </style>
        </head>
        <body>
            <div class="login-box">
                <h2>🛡️ Lattice Admin Access</h2>
                <form action="/authenticate" method="POST">
                    <input type="text" name="username" placeholder="Username" required>
                    <input type="password" name="password" placeholder="Password" required>
                    <button type="submit">Login Securely</button>
                </form>
            </div>
        </body>
    </html>
    """

@app.post("/authenticate")
async def authenticate_user(username: str = Form(...), password: str = Form(...), request: Request = None):
    client_ip = request.client.host if request.client else "unknown"
    if client_ip in _login_attempts and _login_attempts[client_ip]["count"] >= 3:
        if time.time() - _login_attempts[client_ip]["last_attempt"] < 300:
            return HTMLResponse("<h3>🚫 IP Blocked. Try again after 5 minutes.</h3>")
    
    conn = sqlite3.connect('lattice_agents.db')
    c = conn.cursor()
    c.execute("SELECT password_hash FROM admins WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    
    if row and bcrypt.checkpw(password.encode('utf-8'), row[0].encode('utf-8')):
        if client_ip in _login_attempts: del _login_attempts[client_ip]
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="lattice_session", value="valid_admin_session", httponly=True, samesite="strict")
        return response
    else:
        if client_ip not in _login_attempts:
            _login_attempts[client_ip] = {"count": 0, "last_attempt": 0}
        _login_attempts[client_ip]["count"] += 1
        _login_attempts[client_ip]["last_attempt"] = time.time()
        return HTMLResponse(f"<h3>❌ Invalid Credentials. Attempts remaining: {3 - _login_attempts[client_ip]['count']}</h3>")

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("lattice_session")
    return response

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    try:
        verify_admin(request)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=303)

    conn = sqlite3.connect('lattice_agents.db')
    c = conn.cursor()
    
    # Agents Data
    c.execute('SELECT public_key, trust_score, tasks_completed, status, stake FROM agents')
    agents = c.fetchall()
    
    # Stats Calculation
    total_agents = len(agents)
    slashed_agents = len([a for a in agents if a[3] == 'slashed'])
    active_agents = total_agents - slashed_agents
    total_stake = sum(a[4] for a in agents)
    
    conn.close()
    logs = database.get_logs(5)

    html_content = f"""
    <html>
        <head>
            <title>Lattice Protocol Dashboard</title>
            <style>
                body {{ font-family: Arial; background: #f4f4f9; padding: 20px; }}
                h1, h2 {{ color: #333; }}
                .header {{ display: flex; justify-content: space-between; align-items: center; }}
                table {{ width: 100%; border-collapse: collapse; background: white; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                th, td {{ padding: 12px; border-bottom: 1px solid #ddd; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
                .btn {{ padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; margin-right: 10px; }}
                .btn-success {{ background-color: #28a745; color: white; }}
                .btn-danger {{ background-color: #dc3545; color: white; }}
                .btn-primary {{ background-color: #007bff; color: white; }}
                .btn-secondary {{ background-color: #6c757d; color: white; text-decoration: none; padding: 10px 15px; border-radius: 5px; }}
                select {{ padding: 10px; font-size: 16px; border-radius: 5px; margin-right: 10px; }}
                
                /* Stats Cards CSS */
                .stats-container {{ display: flex; gap: 20px; margin-bottom: 30px; }}
                .card {{ background: white; padding: 20px; border-radius: 10px; width: 23%; box-shadow: 0 4px 8px rgba(0,0,0,0.1); text-align: center; }}
                .card h3 {{ font-size: 40px; margin: 0; color: #007bff; }}
                .card p {{ color: #666; margin: 5px 0 0 0; font-weight: bold; }}
                .card.danger h3 {{ color: #dc3545; }}
                .card.success h3 {{ color: #28a745; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🛡️ Lattice Protocol - Control Center</h1>
                <a href='/logout' class="btn-secondary">Logout</a>
            </div>
            
            <!-- STATS CARDS -->
            <div class="stats-container">
                <div class="card">
                    <h3>{total_agents}</h3>
                    <p>Total Agents</p>
                </div>
                <div class="card success">
                    <h3>{active_agents}</h3>
                    <p>Active Agents</p>
                </div>
                <div class="card danger">
                    <h3>{slashed_agents}</h3>
                    <p>Slashed Agents</p>
                </div>
                <div class="card">
                    <h3>{total_stake}</h3>
                    <p>Total Staked Value</p>
                </div>
            </div>

            <h2>Agent Actions</h2>
            <div style="display: flex; align-items: center; margin-bottom: 20px; flex-wrap: wrap;">
                <form action="/ui/register_new" method="POST" style="display:inline;">
                    <button type="submit" class="btn btn-primary">+ Register New Agent</button>
                </form>
                
                <form action="/ui/run_task" method="POST" style="display:inline; display: flex; align-items: center; margin-top: 10px;">
                    <select name="agent_id" required>
                        <option value="" disabled selected>Select Agent for Task...</option>
                        {"".join([f"<option value='{a[0]}'>{a[0][:15]}... (Trust: {a[1]})</option>" for a in agents if a[3] == 'active'])}
                    </select>
                    <button type="submit" class="btn btn-success">Execute Task</button>
                </form>
                
                <form action="/ui/slash_agent" method="POST" style="display:inline; display: flex; align-items: center; margin-top: 10px;">
                    <select name="agent_id" required>
                        <option value="" disabled selected>Select Agent to Punish...</option>
                        {"".join([f"<option value='{a[0]}'>{a[0][:15]}... (Trust: {a[1]})</option>" for a in agents])}
                    </select>
                    <button type="submit" class="btn btn-danger">Slash & Burn Stake</button>
                </form>
                
                <form action="/ui/pay_agent" method="POST" style="display:inline; display: flex; align-items: center; margin-top: 10px;">
                    <select name="agent_id" required>
                        <option value="" disabled selected>Select Agent to Pay...</option>
                        {"".join([f"<option value='{a[0]}'>{a[0][:15]}... (Trust: {a[1]})</option>" for a in agents])}
                    </select>
                    <button type="submit" class="btn" style="background-color: #ffc107; color: black;">Pay 10 USDC</button>
                </form>
            </div>

            <h2>Agents Registry</h2>
            <table>
                <tr><th>Agent Public Key</th><th>Trust Score</th><th>Tasks</th><th>Status</th><th>Stake Locked</th></tr>
                {"".join([f"<tr><td>{a[0][:30]}...</td><td>{a[1]}</td><td>{a[2]}</td><td>{a[3]}</td><td>{a[4]}</td></tr>" for a in agents])}
            </table>

            <h2>📜 Audit Log (Recent Activity)</h2>
            <table>
                <tr><th>Agent Key</th><th>Task / Event</th><th>Status</th><th>Time</th></tr>
                {"".join([f"<tr><td>{l[0][:20]}...</td><td>{l[1]}</td><td>{l[2]}</td><td>{l[3]}</td></tr>" for l in logs])}
            </table>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/ui/run_task")
async def ui_run_task(request: Request, agent_id: str = Form(...)):
    try:
        verify_admin(request)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=303)

    conn = sqlite3.connect('lattice_agents.db')
    c = conn.cursor()
    c.execute("SELECT trust_score, tasks_completed FROM agents WHERE public_key=?", (agent_id,))
    agent = c.fetchone()
    if agent:
        new_trust = min(100.0, agent[0] + 2.0)
        new_tasks = agent[1] + 1
        c.execute("UPDATE agents SET trust_score=?, tasks_completed=? WHERE public_key=?", (new_trust, new_tasks, agent_id))
        conn.commit()
        database.log_task(agent_id, "Execute API Task", "Success")
    conn.close()
    return RedirectResponse(url="/", status_code=303)

@app.post("/ui/slash_agent")
async def ui_slash_agent(request: Request, agent_id: str = Form(...)):
    try:
        verify_admin(request)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=303)
    
    database.burn_stake(agent_id)
    database.log_task(agent_id, "Manual Slash via UI", "Stake Burned")
    return RedirectResponse(url="/", status_code=303)

@app.post("/ui/pay_agent")
async def ui_pay_agent(request: Request, agent_id: str = Form(...)):
    """Agent ko task ka payment karna"""
    try:
        verify_admin(request)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=303)
    
    # DB se agent ki current details nikalo
    agent_info = database.get_agent(agent_id)
    if not agent_info:
        return RedirectResponse(url="/", status_code=303)
        
    # Agar agent slashed hai, toh payment fail ho jaye!
    if agent_info[5] == 'slashed':
        database.log_task(agent_id, "Payment Attempted", "Failed (Slashed Agent)")
    else:
        # Payment record karo DB mein (amount = 10.0, payer = 'Dashboard')
        database.record_payment(agent_id, 10.0, "Dashboard Admin")
        database.log_task(agent_id, "Received Payment", "Success (+10 USDC)")
        
    return RedirectResponse(url="/", status_code=303)

@app.post("/ui/register_new")
async def ui_register_new(request: Request):
    try:
        verify_admin(request)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=303)
        
    import secrets as sec
    dummy_key = sec.token_hex(32)
    database.add_agent(dummy_key, [{"name": "web_scraper", "fee": 0.5}], 100.0)
    return RedirectResponse(url="/", status_code=303)


if __name__ == "__main__":
    print("Lattice HTTP + WebSocket Server v2.0")
    print("HTTP:    http://localhost:8080/lattice/v1/execute")
    print("WebSocket: ws://localhost:8080/lattice/v1/ws")
    print("Security: CORS, Rate limiting, WS validation, Signature Verification")

    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")