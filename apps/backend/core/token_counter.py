"""
Token counting and cost calculation utilities.
More accurate than simple word splitting.
"""

from typing import Optional
import os


class TokenCounter:
    """Count tokens accurately using tiktoken (like OpenAI)."""
    
    def __init__(self):
        """Initialize token counter."""
        self.tiktoken_available = False
        try:
            import tiktoken
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
            self.tiktoken_available = True
        except ImportError:
            print("⚠️  tiktoken not available. Using fallback token counting.")
            self.tokenizer = None
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text accurately.
        
        Args:
            text: Text to count
            
        Returns:
            Number of tokens
        """
        if not text:
            return 0
        
        if self.tiktoken_available and self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception as e:
                print(f"⚠️  Token counting error: {e}. Using fallback.")
        
        # Fallback: estimate tokens as ~0.33 words
        # More accurate than character-based for English
        word_count = len(text.split())
        return max(1, int(word_count * 0.33))
    
    def count_messages_tokens(self, messages: list) -> int:
        """
        Count tokens in a list of messages.
        Includes message format overhead.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            
        Returns:
            Total token count
        """
        total = 0
        for msg in messages:
            if isinstance(msg, dict):
                # Count content
                content = msg.get('content', '')
                total += self.count_tokens(content)
                # Add overhead per message (role, formatting, etc.)
                total += 4  # 4 tokens per message overhead
            else:
                # Handle LangChain BaseMessage objects
                if hasattr(msg, 'content'):
                    total += self.count_tokens(msg.content)
                    total += 4
        
        return total


class CostCalculator:
    """Calculate costs based on actual Vertex AI pricing."""
    
    # Vertex AI pricing as of Dec 2024
    # Source: https://cloud.google.com/vertex-ai/generative-ai/pricing
    PRICING = {
        "gemini-2.5-flash": {
            "input_cost_per_1m": 0.075,      # $0.075 per 1M input tokens
            "output_cost_per_1m": 0.3,       # $0.3 per 1M output tokens
            "name": "Gemini 2.5 Flash (Latest)"
        },
        "gemini-1.5-pro": {
            "input_cost_per_1m": 2.5,        # $2.5 per 1M input tokens
            "output_cost_per_1m": 10,        # $10 per 1M output tokens
            "name": "Gemini 1.5 Pro"
        },
        "gemini-1.5-flash": {
            "input_cost_per_1m": 0.075,
            "output_cost_per_1m": 0.3,
            "name": "Gemini 1.5 Flash"
        },
        "claude-3-opus": {
            "input_cost_per_1m": 15,         # $15 per 1M input tokens (if integrated)
            "output_cost_per_1m": 75,        # $75 per 1M output tokens
            "name": "Claude 3 Opus (for future)"
        },
        "gpt-4-turbo": {
            "input_cost_per_1m": 10,         # $10 per 1M input tokens (if integrated)
            "output_cost_per_1m": 30,        # $30 per 1M output tokens
            "name": "GPT-4 Turbo (for future)"
        }
    }
    
    @classmethod
    def calculate_cost(
        cls,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Calculate cost in USD.
        
        Args:
            model: Model name (e.g., "gemini-2.5-flash")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Cost in USD (6 decimal places)
        """
        pricing = cls.PRICING.get(model, cls.PRICING["gemini-2.0-flash"])
        
        input_cost = (input_tokens / 1_000_000) * pricing["input_cost_per_1m"]
        output_cost = (output_tokens / 1_000_000) * pricing["output_cost_per_1m"]
        
        total_cost = input_cost + output_cost
        return round(total_cost, 6)
    
    @classmethod
    def estimate_monthly_cost(
        cls,
        model: str,
        daily_requests: int,
        avg_input_tokens: int = 100,
        avg_output_tokens: int = 200
    ) -> float:
        """
        Estimate monthly cost based on usage pattern.
        
        Args:
            model: Model name
            daily_requests: Average requests per day
            avg_input_tokens: Average input tokens per request
            avg_output_tokens: Average output tokens per request
            
        Returns:
            Estimated monthly cost in USD
        """
        monthly_requests = daily_requests * 30
        total_input = monthly_requests * avg_input_tokens
        total_output = monthly_requests * avg_output_tokens
        
        return cls.calculate_cost(model, total_input, total_output)
    
    @classmethod
    def get_pricing_info(cls, model: str) -> dict:
        """
        Get pricing information for a model.
        
        Args:
            model: Model name
            
        Returns:
            Pricing dict with rates and name
        """
        return cls.PRICING.get(model, cls.PRICING["gemini-2.5-flash"])


class TokenMetrics:
    """Track token metrics for requests."""
    
    def __init__(self):
        """Initialize metrics."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_requests = 0
        self.total_cost = 0.0
        self.min_input_tokens = float('inf')
        self.max_input_tokens = 0
        self.min_output_tokens = float('inf')
        self.max_output_tokens = 0
    
    def record(
        self,
        input_tokens: int,
        output_tokens: int,
        cost: float
    ):
        """
        Record metrics from a request.
        
        Args:
            input_tokens: Input token count
            output_tokens: Output token count
            cost: Request cost in USD
        """
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += cost
        self.total_requests += 1
        
        self.min_input_tokens = min(self.min_input_tokens, input_tokens)
        self.max_input_tokens = max(self.max_input_tokens, input_tokens)
        self.min_output_tokens = min(self.min_output_tokens, output_tokens)
        self.max_output_tokens = max(self.max_output_tokens, output_tokens)
    
    @property
    def avg_input_tokens(self) -> float:
        """Average input tokens per request."""
        return self.total_input_tokens / max(self.total_requests, 1)
    
    @property
    def avg_output_tokens(self) -> float:
        """Average output tokens per request."""
        return self.total_output_tokens / max(self.total_requests, 1)
    
    @property
    def avg_cost(self) -> float:
        """Average cost per request."""
        return self.total_cost / max(self.total_requests, 1)
    
    def to_dict(self) -> dict:
        """Export metrics as dict."""
        return {
            "total_requests": self.total_requests,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": round(self.total_cost, 6),
            "avg_input_tokens": round(self.avg_input_tokens, 2),
            "avg_output_tokens": round(self.avg_output_tokens, 2),
            "avg_cost_usd": round(self.avg_cost, 6),
            "min_input_tokens": self.min_input_tokens if self.min_input_tokens != float('inf') else 0,
            "max_input_tokens": self.max_input_tokens,
            "min_output_tokens": self.min_output_tokens if self.min_output_tokens != float('inf') else 0,
            "max_output_tokens": self.max_output_tokens,
        }


# Global instances
_token_counter: Optional[TokenCounter] = None
_cost_calculator = CostCalculator


def get_token_counter() -> TokenCounter:
    """Get or create token counter singleton."""
    global _token_counter
    if _token_counter is None:
        _token_counter = TokenCounter()
    return _token_counter


def count_tokens(text: str) -> int:
    """Convenience function to count tokens."""
    return get_token_counter().count_tokens(text)


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Convenience function to calculate cost."""
    return _cost_calculator.calculate_cost(model, input_tokens, output_tokens)


if __name__ == "__main__":
    # Test token counting
    counter = get_token_counter()
    test_text = "This is a test message to count tokens. It should be around 12-15 tokens."
    tokens = counter.count_tokens(test_text)
    print(f"Text: {test_text}")
    print(f"Tokens: {tokens}")
    
    # Test cost calculation
    cost = calculate_cost("gemini-2.0-flash", 100, 200)
    print(f"\nCost for 100 input + 200 output tokens: ${cost}")
    
    # Test monthly estimate
    monthly = CostCalculator.estimate_monthly_cost(
        "gemini-2.0-flash",
        daily_requests=100,
        avg_input_tokens=100,
        avg_output_tokens=200
    )
    print(f"Estimated monthly cost (100 daily requests): ${monthly}")
