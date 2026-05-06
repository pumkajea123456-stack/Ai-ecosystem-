"""
Provider Factory - Unified interface for all AI providers
Routes requests to the appropriate provider based on strategy
"""

from typing import Dict, Optional
from openai_adapter import OpenAIAdapter
from claude_adapter import ClaudeAdapter

class ProviderFactory:
    def __init__(self):
        self.providers = {
            "openai": OpenAIAdapter(),
            "claude": ClaudeAdapter(),
        }
        self._cache_models = None

    def get_provider(self, provider_name: str):
        """Get specific provider"""
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not found. Available: {list(self.providers.keys())}")
        return self.providers[provider_name]

    async def query(
        self,
        prompt: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        strategy: str = "auto"
    ) -> Dict:
        """
        Query AI with automatic routing
        
        Args:
            prompt: User prompt
            provider: Specific provider (openai, claude, etc.)
            model: Specific model
            strategy: auto | cheap | fast | quality
            
        Returns:
            Query result with response, tokens, cost, latency
        """
        
        # If specific provider given, use it
        if provider and model:
            return await self.providers[provider].query(prompt, model)

        # Otherwise, select based on strategy
        selected = self._select_by_strategy(strategy)
        return await selected["adapter"].query(prompt, selected["model"])

    def _select_by_strategy(self, strategy: str = "auto") -> Dict:
        """
        Select provider and model based on strategy
        
        Returns:
            {"provider": str, "model": str, "adapter": object, "specs": dict}
        """
        all_models = self._get_all_models()

        if strategy == "cheap":
            # Lowest cost
            selected = min(all_models, key=lambda x: x["specs"]["price_per_1k_tokens"])

        elif strategy == "fast":
            # Lowest latency
            selected = min(all_models, key=lambda x: x["specs"]["latency_ms"])

        elif strategy == "quality":
            # Highest quality score
            selected = max(all_models, key=lambda x: x["specs"]["quality_score"])

        else:  # auto - balanced scoring
            def score(m):
                specs = m["specs"]
                # Lower is better: prioritize cost, then speed, but reward quality
                return (
                    specs["price_per_1k_tokens"] +
                    specs["latency_ms"] / 1000 -
                    specs["quality_score"] / 100
                )
            selected = min(all_models, key=score)

        return selected

    def _get_all_models(self) -> list:
        """Get all available models from all providers"""
        all_models = []

        for provider_name, adapter in self.providers.items():
            models = adapter.get_available_models()
            for model_name, specs in models.items():
                all_models.append({
                    "provider": provider_name,
                    "model": model_name,
                    "adapter": adapter,
                    "specs": specs
                })

        return all_models

    def get_all_models(self) -> Dict:
        """Get all available models organized by provider"""
        result = {}
        for provider_name, adapter in self.providers.items():
            result[provider_name] = adapter.get_available_models()
        return result

    async def health_check(self) -> Dict[str, bool]:
        """Check health of all providers"""
        health = {}
        for provider_name, adapter in self.providers.items():
            try:
                health[provider_name] = await adapter.health_check()
            except Exception:
                health[provider_name] = False
        return health
