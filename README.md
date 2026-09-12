# 🔷 Lattice Protocol v2.1

**The Secure, Stateless Protocol for AI, Data, Blockchain, and Gaming.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/) [![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-009688.svg)](https://fastapi.tiangolo.com) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📋 Table of Contents

- [What&#39;s New in v2.1](#-whats-new-in-v21-economic-security--control-center)
- [Architecture Comparison](#-architecture-comparison-lattice-vs-mcp)
- [Features](#-features)
- [Why Lattice?](#-why-lattice)
- [MCP Bridge Module](#-mcp-bridge-module-lattice-mcp-gateway)
- [Lattice Ecosystem](#-lattice-ecosystem-different-from-mcp)
- [Client SDK](#-lattice-client-sdk-for-developers)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Join the Ecosystem](#-join-the-lattice-ecosystem)

---

## 🆕 What's New in v2.1? (Economic Security & Control Center)

Lattice is no longer just a protocol — it's a full-fledged **Agent Economy Control Center**. This release introduces Financial Slashing, Audit Trails, and an Interactive Web Dashboard.

### 🖥️ Interactive Web Dashboard

No need to use `curl` for everything! Lattice now comes with a built-in Web Control Center.

* **Visual Registry** — View all registered agents, their trust scores, and locked stakes.
* **One-Click Actions** — Select specific agents from a dropdown to execute tasks or slash them instantly.
* **Live Audit Logs** — Monitor recent activities, task successes, and slashing events in real-time.
* **Access it at:** `http://localhost:8080/` after starting the server.

### 🔥 Financial Slashing (Stake Burn)

Trust scores are no longer the only penalty. If an agent provides malicious data or fails a task, Lattice enforces Economic Slashing:

* The agent's Trust Score drops to `0.0`.
* The agent's locked Stake is burned to `0.0`.
* The agent's status is permanently updated to `slashed`, preventing future task execution.

### 📜 Audit Trail & Task History

Enterprise-grade accountability. Every action is logged immutably into the SQLite database.

* When an agent executes a task, a log is recorded with the `Task Name`, `Status` (Success/Failed), and `Timestamp`.
* Slashing events are recorded with the specific reason.

### 🛠️ Developer Experience (Zero-Config DB)

Tired of manually initializing databases or deleting files when schemas update? Lattice v2.1 features an **Auto-Migrating Database**. Simply run `python server.py`, and Lattice automatically checks for missing columns and updates the SQLite schema on the fly. No `del` commands, no headaches.

### 💸 Agent Payments (Micropayments)

Agents can now be compensated for their work. The `pay_agent` action allows clients to send rewards to active agents, which are recorded in the database. Slashed agents cannot receive payments.

---

## 📊 Architecture Comparison: Lattice vs MCP

![Lattice vs MCP](Lattice_vs_MCP.png)

---

## 🚀 Features

* **Ed25519 Cryptographic Identity** — Every agent signs requests. No more IP-based tracking.
* **Trust Scoring Engine** — Agents build reputation by successfully completing tasks.
* **Slashing Mechanism** — Malicious agents are penalized, and their trust score is dropped to zero.
* **Financial Slashing** — Malicious/failing agents also have their locked stake burned to `0.0` and are permanently marked `slashed`. *(New in v2.1)*
* **Persistent Registry** — SQLite-backed agent registry (survives server restarts).
* **Auto-Migrating Database** — Schema updates apply automatically on startup, no manual migrations needed. *(New in v2.1)*
* **Audit Trail** — Immutable logging of task history and slashing events. *(New in v2.1)*
* **Agent Payments** — Micropayment rewards to active (non-slashed) agents via `pay_agent`. *(New in v2.1)*
* **Interactive Web Dashboard** — Visual registry, one-click actions, and live audit logs. *(New in v2.1)*
* **MCP Bridge Ready** — Designed to sit on top of MCP, adding economic and trust layers.

---

## 🚀 Why Lattice?

| Feature              | MCP      | **Lattice**                     |
| -------------------- | -------- | ------------------------------------- |
| 🔒 Security          | API Keys | **Ed25519 Signing**             |
| ⛓️ Blockchain      | ❌       | **Ethereum + Solana**           |
| 🎮 Gaming            | ❌       | **Anti-Cheat HMAC**             |
| 📊 Data Engineering  | ❌       | **ETL Pipelines**               |
| 🤖 AI Agent Swarms   | ❌       | **Multi-Agent Coordination**    |
| 🧠 Vector DB         | ❌       | **pgvector Support**            |
| ⚡ Stateless         | ❌       | **✅ Built-in**                 |
| 🌉 MCP Compatibility | ❌       | **✅ MCP Bridge Gateway**       |
| 💰 Economic Slashing | ❌       | **✅ Stake Burn + Audit Trail** |
| 🖥️ Dashboard       | ❌       | **✅ Interactive Web UI**       |

---

## 🌉 MCP Bridge Module (Lattice-MCP Gateway)

**Lattice eliminates the need to rebuild MCP tools!** You can simply "rent" existing MCP tools on the Lattice network. An agent sends a `bridge_mcp_tool` request, the Lattice server calls the MCP tool locally, retrieves the result, and returns it to the agent.

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

---

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

# Pay Agent (New in v2.1)
curl -X POST http://localhost:8080/lattice/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "pay_001",
    "action": "pay_agent",
    "payload": {
      "agent_id": "AGENT_ID_HERE",
      "amount": 10
    },
    "timestamp": '$(date +%s)'
  }'
```

---

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

---

## 📦 Installation

```bash
pip install -r requirements.txt
```

---

## 🚀 Quick Start

```bash
# Start server
python server.py

# Access the Interactive Web Dashboard
# → http://localhost:8080/

# Run tests
python test_lattice.py

# Docker
docker build -t lattice-protocol .
docker run -p 8080:8080 lattice-protocol
```

---

## 🤝 Join the Lattice Ecosystem

Let's build the future of autonomous AI agents. MCP connects AI to Tools. Lattice connects AI to AI Economy.

**[GitHub](https://github.com/shahzain112/Lattice-Protocol)** | **[Documentation](https://github.com/shahzain112/Lattice-Protocol/wiki)**
