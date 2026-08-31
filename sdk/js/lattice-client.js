/**
 * Lattice Protocol JavaScript SDK
 * Client for interacting with Lattice Agent Mesh
 * @version 2.0.0
 */

class LatticeClient {
  constructor(baseURL = 'http://localhost:8080') {
    this.baseURL = baseURL;
    this.version = '2.0.0';
  }

  /**
   * Execute any Lattice action
   * @param {string} action - Action name
   * @param {object} payload - Action payload
   * @returns {Promise<object>} Response data
   */
  async execute(action, payload = {}) {
    const request = {
      request_id: `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      action,
      payload,
      timestamp: Math.floor(Date.now() / 1000)
    };

    const response = await fetch(`${this.baseURL}/lattice/v1/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${await response.text()}`);
    }

    return response.json();
  }

  // Health check
  async health() {
    const response = await fetch(`${this.baseURL}/lattice/v1/health`);
    return response.json();
  }

  // Server status
  async status() {
    const response = await fetch(`${this.baseURL}/lattice/v1/status`);
    return response.json();
  }

  // ========== ECOSYSTEM METHODS ==========

  /**
   * Register a new agent in the Lattice ecosystem
   * @param {Array} capabilities - Agent capabilities
   * @param {number} stake - Stake amount
   * @returns {Promise<object>} Registration result
   */
  async registerAgent(capabilities = [], stake = 0) {
    return this.execute('register_agent', { capabilities, stake });
  }

  /**
   * Discover agents by capability
   * @param {string} capability - Capability name
   * @param {number} minTrust - Minimum trust score
   * @returns {Promise<object>} Discovered agents
   */
  async discoverAgents(capability, minTrust = 50) {
    return this.execute('discover_agents', { capability, min_trust: minTrust });
  }

  /**
   * Get agent trust report
   * @param {string} agentId - Agent ID
   * @returns {Promise<object>} Trust report
   */
  async getAgentTrust(agentId) {
    return this.execute('get_agent_trust', { agent_id: agentId });
  }

  /**
   * Get ecosystem statistics
   * @returns {Promise<object>} Ecosystem stats
   */
  async getEcosystemStats() {
    return this.execute('get_ecosystem_stats', {});
  }

  // ========== BLOCKCHAIN METHODS ==========

  /**
   * Get Ethereum balance
   * @param {string} address - ETH address
   * @returns {Promise<object>} Balance info
   */
  async getBalance(address) {
    return this.execute('get_balance', { address });
  }

  /**
   * Get multi-chain balance
   * @param {string} chain - Chain name
   * @param {string} address - Wallet address
   * @returns {Promise<object>} Balance info
   */
  async getMultichainBalance(chain, address) {
    return this.execute('multichain_balance', { chain, address });
  }

  // ========== GAMING METHODS ==========

  /**
   * Submit game score with HMAC signature
   * @param {string} player - Player name
   * @param {number} score - Score value
   * @param {string} secret - Gaming secret for HMAC
   * @returns {Promise<object>} Verification result
   */
  async submitGameScore(player, score, secret) {
    const crypto = require('crypto');
    const signature = crypto
      .createHmac('sha256', secret)
      .update(`${player}:${score}`)
      .digest('hex');

    return this.execute('submit_game_score', {
      player,
      score,
      signature
    });
  }

  // ========== WEBSOCKET ==========

  /**
   * Connect to Lattice WebSocket
   * @returns {WebSocket} WebSocket connection
   */
  connectWebSocket() {
    const ws = new WebSocket(`ws://${this.baseURL.replace('http://', '')}/lattice/v1/ws`);

    ws.onopen = () => {
      console.log('🔌 Lattice WebSocket connected');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('📨 Message:', data);
    };

    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
    };

    return ws;
  }
}

// Export for Node.js and browsers
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { LatticeClient };
}

if (typeof window !== 'undefined') {
  window.LatticeClient = LatticeClient;
}
