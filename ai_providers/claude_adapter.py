"""
Claude (Anthropic) Provider Adapter
Support for Claude 3 models (Opus, Sonnet, Haiku)
"""

import anthropic
import time
from typing import Dict, Optional
import os

class ClaudeAdapter:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.models = {
            "claude-3-opus-20240229": {
                "price_per_1k_tokens": 0.015,
                "latency_ms": 2000,
                "quality_score": 98,
                "max_tokens": 200000,
                "display_name": "Claude 3 Opus (Best)"
            },
            "claude-3-sonnet-20240229": {
                "price_per_1k_tokens": 0.003,
                "latency_ms": 1200,
                "quality_score": 85,
                "max_tokens": 200000,
                "display_name": "Claude 3 Sonnet (Balanced)"
            },
            "claude-3-haiku-20240307": {
                "price_per_1k_tokens": 0.00025,
                "latency_ms": 600,
                "quality_score": 75,
                "max_tokens": 200000,
                "display_name": "Claude 3 Haiku (Fast)"
            },
        }

    async def query(self, prompt: str, model: str = "claude-3-sonnet-20240229", max_tokens: int = None) -> Dict:
        """
        Query Claude model
        
        Args:
            prompt: User prompt
            model: Model name (claude-3-opus, claude-3-sonnet, claude-3-haiku)
            max_tokens: Max response tokens
            
        Returns:
            {
                "response": str,
                "tokens": int,
                "cost": float,
                "latency_ms": int,
                "model": str
            }
        """
        if model not in self.models:
            raise ValueError(f"Model {model} not supported. Available: {list(self.models.keys())}")

        try:
            start_time = time.time()
            
            model_config = self.models[model]
            if max_tokens is None:
                max_tokens = min(2048, model_config["max_tokens"])

            # Call Claude API
            message = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system="You are a helpful, harmless, and honest assistant.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            latency_ms = int((time.time() - start_time) * 1000)

            # Extract response
            response_text = message.content[0].text

            # Get token usage
            input_tokens = message.usage.input_tokens
            output_tokens = message.usage.output_tokens
            total_tokens = input_tokens + output_tokens

            # Claude pricing (input/output separate)
            if model == "claude-3-opus-20240229":
                # $15 per 1M input tokens, $75 per 1M output tokens
                cost = (input_tokens * 0.000015 + output_tokens * 0.000075)
            elif model == "claude-3-sonnet-20240229":
                # $3 per 1M input tokens, $15 per 1M output tokens
                cost = (input_tokens * 0.000003 + output_tokens * 0.000015)
            else:  # claude-3-haiku-20240307
                # $0.25 per 1M input tokens, $1.25 per 1M output tokens
                cost = (input_tokens * 0.00000025 + output_tokens * 0.00000125)

            return {
                "response": response_text,
                "tokens": total_tokens,
                "cost": cost,
                "latency_ms": latency_ms,
                "model": model,
                "provider": "claude",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            }

        except anthropic.APIError as e:
            raise Exception(f"Claude API Error: {str(e)}")
        except anthropic.APIConnectionError as e:
            raise Exception(f"Claude Connection Error: {str(e)}")
        except Exception as e:
            raise Exception(f"Claude Error: {str(e)}")

    def get_available_models(self) -> Dict:
        """Get list of available models with specs"""
        return self.models

    async def health_check(self) -> bool:
        """Check if Claude API is accessible"""
        try:
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[
                    {
                        "role": "user",
                        "content": "ping"
                    }
                ]
            )
            return True
        except Exception:
            return False
