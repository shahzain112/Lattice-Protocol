# 🔷 Lattice Protocol v2.0

**The Secure, Stateless Protocol for AI, Data, Blockchain, and Gaming.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/) [![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-009688.svg)](https://fastapi.tiangolo.com) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📊 Architecture Comparison: Lattice vs MCP

![Lattice vs MCP](Lattice_vs_MCP.png)

## 🚀 Features

* **Ed25519 Cryptographic Identity** : Every agent signs requests. No more IP-based tracking.
* **Trust Scoring Engine** : Agents build reputation by successfully completing tasks.
* **Slashing Mechanism** : Malicious agents are penalized, and their trust score is dropped to zero.
* **Persistent Registry** : SQLite-backed agent registry (survives server restarts).
* **MCP Bridge Ready** : Designed to sit on top of MCP, adding economic and trust layers.

## 🚀 Why Lattice?

| Feature              | MCP      | **Lattice**                  |
| -------------------- | -------- | ---------------------------------- |
| 🔒 Security          | API Keys | **Ed25519 Signing**          |
| ⛓️ Blockchain      | ❌       | **Ethereum + Solana**        |
| 🎮 Gaming            | ❌       | **Anti-Cheat HMAC**          |
| 📊 Data Engineering  | ❌       | **ETL Pipelines**            |
| 🤖 AI Agent Swarms   | ❌       | **Multi-Agent Coordination** |
| 🧠 Vector DB         | ❌       | **pgvector Support**         |
| ⚡ Stateless         | ❌       | **✅ Built-in**              |
| 🌉 MCP Compatibility | ❌       | **✅ MCP Bridge Gateway**    |

## 🌉 NEW: MCP Bridge Module (Lattice-MCP Gateway)

**Lattice eliminates the need to rebuild MCP tools!** Now, you can simply "rent" existing MCP tools on the Lattice network. An agent will send a `bridge_mcp_tool` request, the Lattice server will call the MCP tool locally, retrieve the result, and return it to the agent.

### Bridge MCP Tool Example

```bash
curl -X POST http://localhost:8080/lattice/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "bridge_001",
    "action": "bridge_mcp_tool",
    "payload": {
      "tool": "example_tool"
    },
    "timestamp": '$(date +%s)'
  }'
```

## 🔷 Lattice Ecosystem (Different From MCP)

| Feature        | MCP       | **Lattice**                  |
| -------------- | --------- | ---------------------------------- |
| Agent Identity | ❌ None   | **✅ Ed25519 Cryptographic** |
| Trust Scoring  | ❌ None   | **✅ Decentralized (0-100)** |
| Agent Registry | ❌ None   | **✅ Global Directory**      |
| Discovery      | ❌ Static | **✅ Dynamic Gossip**        |
| Economic Model | ❌ None   | **✅ Stake + Fees**          |

### 🆕 Ecosystem Actions

```bash
# Register Agent
curl -X POST http://localhost:8080/lattice/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "reg_001",
    "action": "register_agent",
    "payload": {
      "capabilities": [{"name": "eth_balance", "fee": 0.5}],
      "stake": 1000
    },
    "timestamp": '$(date +%s)'
  }'

# Discover Agents
curl -X POST http://localhost:8080/lattice/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "disc_001",
    "action": "discover_agents",
    "payload": {"capability": "eth_balance"},
    "timestamp": '$(date +%s)'
  }'
```

## 🐍 Lattice Client SDK (For Developers)

We have built a simple Client SDK so you don't have to worry about Ed25519 signing or complex JSON formatting. Just initialize the client and execute actions in 2 lines!

```python
from lattice_client import LatticeClient

# Initialize client (auto-generates and saves your secure keys)
client = LatticeClient(server_url="http://localhost:8080")

# Execute any action
result = client.execute("health_check")
print(result)
```

## 📦 Installation

```bash
pip install -r requirements.txt
```

## 🚀 Quick Start

```bash
# Start server
python server.py

# Run tests
python test_lattice.py

# Docker
docker build -t lattice-protocol .
docker run -p 8080:8080 lattice-protocol
```

## 🤝 Join the Lattice Ecosystem

Let's build the future of autonomous AI agents. MCP connects AI to Tools. Lattice connects AI to AI Economy.

**[GitHub](https://github.com/shahzain112/Lattice-Protocol)** | **[Documentation](https://github.com/shahzain112/Lattice-Protocol/wiki)**
