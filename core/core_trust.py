"""
Lattice Trust Engine
Decentralized reputation and trust scoring system.
This is what makes Lattice autonomous — no central authority needed.
"""

import time
import math
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class TrustEvent:
    """A single trust event (task completion, review, slashing)."""
    agent_id: str
    event_type: str  # "task_complete", "task_fail", "review", "slash", "stake"
    delta: float
    reason: str
    timestamp: float = field(default_factory=time.time)
    verifier_id: Optional[str] = None  # Who verified this event


class TrustEngine:
    """
    Decentralized Trust Engine

    Unlike MCP which has no trust layer, Lattice:
    - Calculates trust from multiple signals
    - Uses stake-weighted consensus
    - Implements slashing for bad behavior
    - Has review/rating system
    """

    def __init__(self):
        self._events: Dict[str, List[TrustEvent]] = defaultdict(list)
        self._reviews: Dict[str, List[dict]] = defaultdict(list)
        self._stakes: Dict[str, float] = {}

        # Trust calculation weights
        self.WEIGHTS = {
            "performance": 0.4,
            "stake": 0.3,
            "reviews": 0.2,
            "longevity": 0.1
        }

    def record_event(self, event: TrustEvent):
        """Record a trust event."""
        self._events[event.agent_id].append(event)

    def add_review(self, agent_id: str, reviewer_id: str, rating: float, comment: str = ""):
        """Add a review for an agent (1-5 stars)."""
        self._reviews[agent_id].append({
            "reviewer": reviewer_id,
            "rating": rating,
            "comment": comment,
            "timestamp": time.time()
        })

    def update_stake(self, agent_id: str, amount: float):
        """Update staked amount."""
        self._stakes[agent_id] = amount

    def calculate_trust(self, agent_id: str) -> float:
        """
        Calculate composite trust score (0-100).

        Formula:
        trust = (performance * 0.4) + (stake * 0.3) + (reviews * 0.2) + (longevity * 0.1)
        """
        events = self._events.get(agent_id, [])

        # Performance score (0-100)
        if not events:
            performance = 50.0
        else:
            task_events = [e for e in events if e.event_type in ("task_complete", "task_fail")]
            if not task_events:
                performance = 50.0
            else:
                successes = sum(1 for e in task_events if e.event_type == "task_complete")
                performance = (successes / len(task_events)) * 100

        # Stake score (0-100) - logarithmic scale
        stake = self._stakes.get(agent_id, 0)
        stake_score = min(100, math.log10(stake + 1) * 20) if stake > 0 else 0

        # Review score (0-100)
        reviews = self._reviews.get(agent_id, [])
        if not reviews:
            review_score = 50.0
        else:
            avg_rating = sum(r["rating"] for r in reviews) / len(reviews)
            review_score = (avg_rating / 5.0) * 100

        # Longevity score (0-100) - based on first event
        if events:
            age_days = (time.time() - min(e.timestamp for e in events)) / 86400
            longevity = min(100, age_days * 2)  # 50 days = 100
        else:
            longevity = 0.0

        # Composite score
        trust = (
            performance * self.WEIGHTS["performance"] +
            stake_score * self.WEIGHTS["stake"] +
            review_score * self.WEIGHTS["reviews"] +
            longevity * self.WEIGHTS["longevity"]
        )

        return round(trust, 2)

    def slash(self, agent_id: str, amount: float, reason: str, verifier_id: str):
        """
        Slash an agent's trust for bad behavior.
        This is the economic security mechanism.
        """
        event = TrustEvent(
            agent_id=agent_id,
            event_type="slash",
            delta=-amount,
            reason=reason,
            verifier_id=verifier_id
        )
        self.record_event(event)

        # Also reduce stake
        current_stake = self._stakes.get(agent_id, 0)
        self._stakes[agent_id] = max(0, current_stake - amount)

    def get_trust_report(self, agent_id: str) -> dict:
        """Get detailed trust report."""
        return {
            "agent_id": agent_id,
            "trust_score": self.calculate_trust(agent_id),
            "total_events": len(self._events.get(agent_id, [])),
            "total_reviews": len(self._reviews.get(agent_id, [])),
            "stake_amount": self._stakes.get(agent_id, 0),
            "recent_events": [
                {
                    "type": e.event_type,
                    "delta": e.delta,
                    "reason": e.reason,
                    "time": e.timestamp
                }
                for e in self._events.get(agent_id, [])[-5:]
            ]
        }
