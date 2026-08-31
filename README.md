
# 🔷 Lattice Protocol v2.0

**The Secure, Stateless Protocol for AI, Data, Blockchain, and Gaming.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-009688.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)



## 📊 Architecture Comparison: Lattice vs MCP

![Lattice vs MCP](Lattice_vs_MCP.png)g

## 📊 Architecture Comparison: Lattice vs MCP

## 🚀 Why Lattice?

| Feature             | MCP      | **Lattice**                  |
| ------------------- | -------- | ---------------------------------- |
| 🔒 Security         | API Keys | **Ed25519 Signing**          |
| ⛓️ Blockchain     | ❌       | **Ethereum + Solana**        |
| 🎮 Gaming           | ❌       | **Anti-Cheat HMAC**          |
| 📊 Data Engineering | ❌       | **ETL Pipelines**            |
| 🤖 AI Agent Swarms  | ❌       | **Multi-Agent Coordination** |
| 🧠 Vector DB        | ❌       | **pgvector Support**         |
| ⚡ Stateless        | ❌       | **✅ Built-in**              |



## 🔷 Lattice Ecosystem (Differnt From MCP)

| Feature        | MCP       | **Lattice**                  |
| -------------- | --------- | ---------------------------------- |
| Agent Identity | ❌ None   | **✅ Ed25519 Cryptographic** |
| Trust Scoring  | ❌ None   | **✅ Decentralized (0-100)** |
| Agent Registry | ❌ None   | **✅ Global Directory**      |
| Discovery      | ❌ Static | **✅ Dynamic Gossip**        |
| Economic Model | ❌ None   | **✅ Stake + Fees**          |

### 🆕 Ecosystem Actions

```bash
# Registering Agent
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

# Discovering Agent
curl -X POST http://localhost:8080/lattice/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "disc_001",
    "action": "discover_agents",
    "payload": {"capability": "eth_balance"},
    "timestamp": '$(date +%s)'
  }'
```



## 📦 Installation

```bash
pip install -r requirements.txt
```
