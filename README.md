
# 🔷 Lattice Protocol v2.0

**Trust-Based Agent Economy for Autonomous AI Agents**

[https://www.python.org/downloads/](https://www.python.org/downloads/)
[https://fastapi.tiangolo.com](https://fastapi.tiangolo.com/)
[https://opensource.org/licenses/MIT](https://opensource.org/licenses/MIT)
[https://github.com/shahzain112/Lattice-Protocol/actions](https://github.com/shahzain112/Lattice-Protocol/actions)

## 🎯 What is Lattice?

Lattice is a  **complementary protocol to MCP** . While MCP connects AI clients to tools, Lattice enables AI agents to:

* 🔐 Establish cryptographic identity (Ed25519)
* 🤝 Discover and trust each other dynamically
* 💰 Stake tokens and earn fees for services
* 🌐 Form a peer-to-peer mesh network

> **MCP** = "AI, use these tools" (Client-Server)
> **Lattice** = "Agents, find trusted partners and transact" (Peer-to-Peer)

## 📊 Architecture Comparison

## 🚀 Why Lattice?

| Feature        | MCP              | **Lattice**                          |
| -------------- | ---------------- | ------------------------------------------ |
| Architecture   | Client-Server    | **Peer-to-Peer Mesh**                |
| Agent Identity | ❌ None          | **✅ Ed25519 Cryptographic**         |
| Trust Layer    | ❌ None          | **✅ Decentralized Scoring (0-100)** |
| Discovery      | Static tool list | **Dynamic capability matching**      |
| Economics      | ❌ None          | **✅ Stake + Fee market**            |
| Blockchain     | ❌ None          | **✅ Multi-chain native**            |


## 📦 Installation

# Clone repo

git clone https://github.com/shahzain112/Lattice-Protocol.git
cd Lattice-Protocol

# Install dependencies

pip install -r requirements.txt

# Or install as package

pip install -e .


## 🚀 Quick Start

# Start server

python server.py

# Run tests

python test_lattice.py

# Docker

docker build -t lattice-protocol .
docker run -p 8080:8080 lattice-protocol


## 📖 Documentation

### Protocol Specification

See [SPEC.md](https://www.kimi.ai/chat/SPEC.md) for complete protocol documentation:

* Message format (JSON + Ed25519 signing)
* Action types and error codes
* WebSocket protocol
* Trust scoring algorithm
* Economic model

### API Reference

#### Core Actions

| Action                | Description       | Example                                                                                           |
| --------------------- | ----------------- | ------------------------------------------------------------------------------------------------- |
| `health_check`      | Server health     | `{"action": "health_check"}`                                                                    |
| `get_balance`       | ETH balance       | `{"action": "get_balance", "payload": {"address": "0x..."}}`                                    |
| `submit_game_score` | HMAC score verify | `{"action": "submit_game_score", "payload": {"player": "x", "score": 100, "signature": "..."}}` |



#### Ecosystem Actions (MCP doesn't have these!)



| Action                  | Description            | Example                                                                             |
| ----------------------- | ---------------------- | ----------------------------------------------------------------------------------- |
| `register_agent`      | Register with identity | `{"action": "register_agent", "payload": {"capabilities": [...], "stake": 1000}}` |
| `discover_agents`     | Find by capability     | `{"action": "discover_agents", "payload": {"capability": "eth_balance"}}`         |
| `get_agent_trust`     | Trust report           | `{"action": "get_agent_trust", "payload": {"agent_id": "..."}}`                   |
| `get_ecosystem_stats` | Network stats          | `{"action": "get_ecosystem_stats"}`                                               |


### Deployment Guide

#### Local Development

python server.py

# Server runs on http://localhost:8080


**Docker**

docker build -t lattice-protocol .
docker run -d -p 8080:8080 --name lattice lattice-protocol

#### Production (Gunicorn)

pip install gunicorn
gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080


## 📦 JavaScript SDK

npm install @lattice/protocol

const { LatticeClient } = require('@lattice/protocol');
const client = new LatticeClient('http://localhost:8080');

// Register agent
await client.registerAgent(
  [{ name: 'eth_balance', fee: 0.5 }],
  1000  // stake
);

// Discover agents
const agents = await client.discoverAgents('eth_balance');
console.log(agents);


## 🛡️ Security

* ✅ Private keys never committed to repo (see `.gitignore`)
* ✅ Ed25519 signing for all agent messages
* ✅ HMAC verification for gaming scores
* ✅ Rate limiting: 100 req/min per client
* ✅ Anti-replay protection: 60s timestamp window

## 📄 License

MIT — See [LICENSE](https://www.kimi.ai/chat/LICENSE) for details.
