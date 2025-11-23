from typing import Dict, Optional
from dataclasses import dataclass

# Pricing per 1M tokens (Input, Output)
# Updated with values found for Gemini 2.5/3.0 (User Timeline: Nov 2025)
PRICING = {
    "gemini-2.5-pro": {"input": 1.25, "output": 10.00},   # Base rate (<= 200k context)
    "gemini-2.5-flash": {"input": 0.10, "output": 0.40},  # High throughput model
    "gemini-3.0-pro": {"input": 2.00, "output": 12.00},   # Base rate (<= 200k context)
}

@dataclass
class CostStats:
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0

class CostTracker:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CostTracker, cls).__new__(cls)
            cls._instance.stats = CostStats()
        return cls._instance

    def add_usage(self, input_tokens: int, output_tokens: int, model: str):
        """Add usage stats and update total cost."""
        cost = estimate_cost(input_tokens, output_tokens, model)
        
        self.stats.total_input_tokens += input_tokens
        self.stats.total_output_tokens += output_tokens
        self.stats.total_cost_usd += cost
        
    def get_stats(self) -> CostStats:
        return self.stats
        
    def reset(self):
        self.stats = CostStats()

def count_tokens(text: str, model: str = "gemini-2.5-flash") -> int:
    """
    Estimate token count for a given text.
    For Gemini, we use a rough approximation if exact counting isn't available via API.
    Rule of thumb: 1 token ≈ 4 characters.
    """
    if not text:
        return 0
    # Simple character-based approximation
    return len(text) // 4

def estimate_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    """
    Estimate cost in USD for a given usage.
    """
    if model not in PRICING:
        # Fallback to highest price or 0 if unknown? Let's warn and return 0 for safety
        return 0.0
        
    rates = PRICING[model]
    input_cost = (input_tokens / 1_000_000) * rates["input"]
    output_cost = (output_tokens / 1_000_000) * rates["output"]
    
    return input_cost + output_cost

# Global tracker instance
tracker = CostTracker()