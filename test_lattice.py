import requests
import json
import time
import os
import sys
import hmac
import hashlib

# Configuration (can be overridden via environment)
BASE_URL = os.environ.get("LATTICE_URL", "http://localhost:8080")
API_ENDPOINT = f"{BASE_URL}/lattice/v1/execute"

# Test tracking
_tests_passed = 0
_tests_failed = 0

def _assert_response(response, expected_status="success"):
    """Assert and validate response."""
    global _tests_passed, _tests_failed
    try:
        data = response.json()
        assert data.get("status") == expected_status, f"Expected {expected_status}, got {data.get('status')}"
        assert "request_id" in data, "Missing request_id in response"
        _tests_passed += 1
        return data
    except (AssertionError, Exception) as e:
        _tests_failed += 1
        print(f"❌ ASSERTION FAILED: {e}")
        print(f"   Response: {response.text}")
        return None

def _make_request(payload):
    """Helper to make requests with error handling."""
    try:
        response = requests.post(API_ENDPOINT, json=payload, timeout=10)
        return response
    except requests.exceptions.ConnectionError:
        print(f"❌ CONNECTION ERROR: Server not running at {BASE_URL}")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT: Request took too long")
        return None

# 1. Test Health Check
def test_health():
    print("\n🧪 Testing: health_check")
    payload = {
        "request_id": "test_health_001",
        "action": "health_check",
        "payload": {},
        "timestamp": int(time.time())
    }
    response = _make_request(payload)
    if response:
        data = _assert_response(response, "success")
        if data:
            assert data["data"]["message"] == "Lattice is alive"
            print("✅ Health Check: PASSED")
        else:
            print("❌ Health Check: FAILED")

# 2. Test Blockchain (Ethereum Balance)
def test_blockchain():
    print("\n🧪 Testing: get_balance")
    payload = {
        "request_id": "test_eth_001",
        "action": "get_balance",
        "payload": {
            "address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        },
        "timestamp": int(time.time())
    }
    response = _make_request(payload)
    if response:
        data = _assert_response(response)
        if data:
            print(f"✅ Blockchain Balance: PASSED (response received)")
        else:
            print("⚠️ Blockchain Balance: Response received but validation failed (may be expected if module missing)")

# 3. Test Gaming (Score Submission)
def test_gaming():
    print("\n🧪 Testing: submit_game_score")
    player = "Usman"
    score = 9999
    secret_key = os.environ.get("LATTICE_GAMING_SECRET", "Lattice_Gaming_Secret_2024").encode()

    # Generate correct signature
    signature = hmac.new(secret_key, f"{player}:{score}".encode(), hashlib.sha256).hexdigest()

    payload = {
        "request_id": "test_game_001",
        "action": "submit_game_score",
        "payload": {
            "player": player,
            "score": score,
            "signature": signature
        },
        "timestamp": int(time.time())
    }
    response = _make_request(payload)
    if response:
        data = _assert_response(response, "success")
        if data:
            assert "verified" in data["data"]["message"].lower()
            print("✅ Gaming Score: PASSED")
        else:
            print("❌ Gaming Score: FAILED")

# 4. Test Gaming (Invalid Signature - Negative Test)
def test_gaming_cheat():
    print("\n🧪 Testing: submit_game_score (cheating detection)")
    payload = {
        "request_id": "test_game_cheat_001",
        "action": "submit_game_score",
        "payload": {
            "player": "Hacker",
            "score": 99999,
            "signature": "invalid_signature"
        },
        "timestamp": int(time.time())
    }
    response = _make_request(payload)
    if response:
        data = _assert_response(response, "error")
        if data:
            assert "cheating" in data.get("error", "").lower() or "invalid" in data.get("error", "").lower()
            print("✅ Gaming Anti-Cheat: PASSED")
        else:
            print("❌ Gaming Anti-Cheat: FAILED")

# 5. Test Multi-Sig
def test_multisig():
    print("\n🧪 Testing: check_multisig")
    payload = {
        "request_id": "test_multisig_001",
        "action": "check_multisig",
        "payload": {
            "address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        },
        "timestamp": int(time.time())
    }
    response = _make_request(payload)
    if response:
        data = _assert_response(response)
        if data:
            print("✅ Multi-Sig Check: PASSED (response received)")
        else:
            print("⚠️ Multi-Sig Check: Module may not be available")

# 6. Test AI Agent Swarm
def test_swarm():
    print("\n🧪 Testing: run_swarm")
    payload = {
        "request_id": "test_swarm_001",
        "action": "run_swarm",
        "payload": {
            "tasks": [
                {"name": "task1", "data": {"key": "value1"}},
                {"name": "task2", "data": {"key": "value2"}}
            ]
        },
        "timestamp": int(time.time())
    }
    response = _make_request(payload)
    if response:
        data = _assert_response(response)
        if data:
            print("✅ Agent Swarm: PASSED (response received)")
        else:
            print("⚠️ Agent Swarm: Module may not be available")

# 7. Test Vector DB Store
def test_vector_store():
    print("\n🧪 Testing: store_vector")
    payload = {
        "request_id": "test_vector_001",
        "action": "store_vector",
        "payload": {
            "db_uri": "postgresql://user:pass@localhost:5432/testdb",
            "table": "embeddings",
            "embedding": [0.1, 0.2, 0.3, 0.4],
            "metadata": {"source": "test"}
        },
        "timestamp": int(time.time())
    }
    response = _make_request(payload)
    if response:
        data = _assert_response(response)
        if data:
            print("✅ Vector Store: PASSED (response received)")
        else:
            print("⚠️ Vector Store: Module may not be available")

# 8. Test Multi-Chain Balance
def test_multichain():
    print("\n🧪 Testing: multichain_balance")
    payload = {
        "request_id": "test_multichain_001",
        "action": "multichain_balance",
        "payload": {
            "chain": "ethereum",
            "address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        },
        "timestamp": int(time.time())
    }
    response = _make_request(payload)
    if response:
        data = _assert_response(response)
        if data:
            print("✅ Multi-Chain Balance: PASSED (response received)")
        else:
            print("⚠️ Multi-Chain Balance: Module may not be available")

# 9. Test Invalid Action (Negative Test)
def test_invalid_action():
    print("\n🧪 Testing: invalid_action (negative test)")
    payload = {
        "request_id": "test_invalid_001",
        "action": "nonexistent_action",
        "payload": {},
        "timestamp": int(time.time())
    }
    response = _make_request(payload)
    if response:
        data = _assert_response(response, "error")
        if data:
            assert "unknown" in data.get("error", "").lower()
            print("✅ Invalid Action: PASSED")
        else:
            print("❌ Invalid Action: FAILED")

# 10. Test Expired Request (Negative Test)
def test_expired_request():
    print("\n🧪 Testing: expired_request (negative test)")
    payload = {
        "request_id": "test_expired_001",
        "action": "health_check",
        "payload": {},
        "timestamp": int(time.time()) - 120  # 2 minutes old
    }
    response = _make_request(payload)
    if response:
        data = _assert_response(response, "error")
        if data:
            assert "expired" in data.get("error", "").lower()
            print("✅ Expired Request: PASSED")
        else:
            print("❌ Expired Request: FAILED")

if __name__ == "__main__":
    print("🚀 Lattice Protocol Test Suite v2.0")
    print(f"🔗 Target: {BASE_URL}")
    print("=" * 50)

    test_health()
    test_blockchain()
    test_gaming()
    test_gaming_cheat()
    test_multisig()
    test_swarm()
    test_vector_store()
    test_multichain()
    test_invalid_action()
    test_expired_request()

    print("\n" + "=" * 50)
    print(f"📊 Results: {_tests_passed} passed, {_tests_failed} failed")
    if _tests_failed == 0:
        print("🎉 ALL TESTS PASSED!")
    else:
        print(f"⚠️  {_tests_failed} test(s) failed. Check output above.")
    print("=" * 50)