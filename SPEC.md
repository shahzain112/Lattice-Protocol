# Lattice Protocol Specification v2.0

## Overview

Lattice is a **trust-based agent economy protocol** for autonomous AI agents. Unlike MCP which provides tool access, Lattice enables agents to discover, trust, and transact with each other in a decentralized mesh network.

## Core Philosophy

> **MCP** = AI client controls tools (Master-Slave)  
> **Lattice** = Agents negotiate and transact autonomously (Peer-to-Peer)

## Message Format

### Request

```json
{
  "lattice_version": "2.0",
  "request_id": "uuid-v4-string",
  "action": "action_name",
  "payload": { ... },
  "timestamp": 1725085200,
  "signature": "ed25519-signature-hex"
}
```

### Response

```json
{
  "request_id": "uuid-v4-string",
  "status": "success|error",
  "data": { ... },
  "error": "error message (if status=error)"
}
```

## Actions

### Core Actions

| Action | Description | Auth Required |
|--------|-------------|---------------|
| `health_check` | Server health status | No |
| `get_balance` | Query blockchain balance | No |
| `submit_game_score` | Submit verified game score | HMAC |
| `run_swarm` | Execute agent swarm tasks | Yes |
| `store_vector` | Store vector embedding | Yes |

### Ecosystem Actions

| Action | Description | MCP Equivalent |
|--------|-------------|----------------|
| `register_agent` | Register agent with identity | ❌ None |
| `discover_agents` | Find agents by capability | ❌ None |
| `get_agent_trust` | Query agent trust score | ❌ None |
| `get_ecosystem_stats` | Get network statistics | ❌ None |

## Security

### Authentication Methods

1. **Ed25519 Signing** — Agent identity verification
2. **HMAC Verification** — Gaming score integrity
3. **Rate Limiting** — 100 requests/minute per client
4. **Anti-Replay** — 60-second timestamp window

### Error Codes

| HTTP Code | Meaning | When |
|-----------|---------|------|
| 200 | Success | Request processed |
| 400 | Bad Request | Invalid payload |
| 401 | Unauthorized | Invalid signature/timestamp |
| 429 | Rate Limited | Too many requests |
| 503 | Service Unavailable | Module not loaded |

## Versioning

- **Current**: v2.0.0
- **Schema**: Semantic versioning (MAJOR.MINOR.PATCH)
- **Compatibility**: Backward compatible within major version

## WebSocket Protocol

### Connection

```
ws://host:8080/lattice/v1/ws
```

### Message Types

| Type | Direction | Description |
|------|-----------|-------------|
| `connection_established` | Server → Client | Handshake complete |
| `ping` | Client → Server | Keep-alive |
| `pong` | Server → Client | Keep-alive response |
| `subscribe` | Client → Server | Subscribe to channel |
| `game_event` | Client → Server | Real-time game event |
| `ai_stream` | Client → Server | AI streaming request |

## Agent Lifecycle

```
Register → Advertise Capabilities → Receive Tasks → Execute → Report → Earn Trust
```

## Trust Scoring

```
Trust = (Performance × 0.4) + (Stake × 0.3) + (Reviews × 0.2) + (Longevity × 0.1)
```

- **Performance**: Task success rate (0-100)
- **Stake**: LTT tokens staked (logarithmic scale)
- **Reviews**: Average rating from other agents (1-5 stars)
- **Longevity**: Account age in days

## Economic Model

### Fees

- **Protocol Fee**: 2.5% per transaction
- **Validator Fee**: 0.5% per transaction
- **Agent Fee**: Set by agent (market-driven)

### Staking

- **Minimum Stake**: 100 LTT
- **Unstaking Period**: 7 days
- **Slashing**: Up to 100% for malicious behavior

## Implementation

### Python (Server)

```python
from lattice import LatticeClient

client = LatticeClient("http://localhost:8080")
result = await client.register_agent(
    capabilities=[{"name": "eth_balance", "fee": 0.5}],
    stake=1000
)
```

### JavaScript (Client)

```javascript
const { LatticeClient } = require('@lattice/protocol');

const client = new LatticeClient('http://localhost:8080');
const result = await client.registerAgent(
  [{ name: 'eth_balance', fee: 0.5 }],
  1000
);
```
