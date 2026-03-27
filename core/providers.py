"""
AI Providers Configuration for Kashiza
Supports: Anthropic, OpenAI, Google, Groq, Kimi, DeepSeek, Ollama, OpenRouter
"""
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

class ProviderType(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    GROQ = "groq"
    KIMI = "kimi"
    DEEPSEEK = "deepseek"
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"

@dataclass
class ModelInfo:
    id: str
    provider: ProviderType
    name: str
    context_window: int
    input_price: float
    output_price: float
    quality_score: int
    speed_score: int
    supports_vision: bool = False
    supports_tools: bool = True
    supports_json: bool = True

@dataclass
class ProviderConfig:
    type: ProviderType
    name: str
    api_key_env: str
    base_url: Optional[str] = None
    requires_key: bool = True
    is_local: bool = False
    models: List[ModelInfo] = field(default_factory=list)

class ProviderManager:
    MODELS = {
        # Anthropic Models
        "claude-3-opus-20240229": ModelInfo(
            id="claude-3-opus-20240229",
            provider=ProviderType.ANTHROPIC,
            name="Claude 3 Opus",
            context_window=200000,
            input_price=0.015,
            output_price=0.075,
            quality_score=10,
            speed_score=6,
            supports_vision=True
        ),
        "claude-3-sonnet-20240229": ModelInfo(
            id="claude-3-sonnet-20240229",
            provider=ProviderType.ANTHROPIC,
            name="Claude 3 Sonnet",
            context_window=200000,
            input_price=0.003,
            output_price=0.015,
            quality_score=8,
            speed_score=8,
            supports_vision=True
        ),
        "claude-3-haiku-20240307": ModelInfo(
            id="claude-3-haiku-20240307",
            provider=ProviderType.ANTHROPIC,
            name="Claude 3 Haiku",
            context_window=200000,
            input_price=0.00025,
            output_price=0.00125,
            quality_score=6,
            speed_score=10,
            supports_vision=True
        ),
        "claude-3-5-sonnet-20241022": ModelInfo(
            id="claude-3-5-sonnet-20241022",
            provider=ProviderType.ANTHROPIC,
            name="Claude 3.5 Sonnet",
            context_window=200000,
            input_price=0.003,
            output_price=0.015,
            quality_score=9,
            speed_score=9,
            supports_vision=True
        ),
        
        # OpenAI Models
        "gpt-4o": ModelInfo(
            id="gpt-4o",
            provider=ProviderType.OPENAI,
            name="GPT-4o",
            context_window=128000,
            input_price=0.005,
            output_price=0.015,
            quality_score=9,
            speed_score=8,
            supports_vision=True
        ),
        "gpt-4o-mini": ModelInfo(
            id="gpt-4o-mini",
            provider=ProviderType.OPENAI,
            name="GPT-4o Mini",
            context_window=128000,
            input_price=0.00015,
            output_price=0.0006,
            quality_score=7,
            speed_score=10,
            supports_vision=True
        ),
        "gpt-4-turbo": ModelInfo(
            id="gpt-4-turbo",
            provider=ProviderType.OPENAI,
            name="GPT-4 Turbo",
            context_window=128000,
            input_price=0.01,
            output_price=0.03,
            quality_score=9,
            speed_score=7,
            supports_vision=True
        ),
        "o1-preview": ModelInfo(
            id="o1-preview",
            provider=ProviderType.OPENAI,
            name="o1 Preview",
            context_window=128000,
            input_price=0.015,
            output_price=0.06,
            quality_score=10,
            speed_score=5,
            supports_vision=False
        ),
        "o1-mini": ModelInfo(
            id="o1-mini",
            provider=ProviderType.OPENAI,
            name="o1 Mini",
            context_window=128000,
            input_price=0.003,
            output_price=0.012,
            quality_score=8,
            speed_score=7,
            supports_vision=False
        ),
        
        # Google Models
        "gemini-1.5-pro": ModelInfo(
            id="gemini-1.5-pro",
            provider=ProviderType.GOOGLE,
            name="Gemini 1.5 Pro",
            context_window=2000000,
            input_price=0.0035,
            output_price=0.0105,
            quality_score=8,
            speed_score=7,
            supports_vision=True
        ),
        "gemini-1.5-flash": ModelInfo(
            id="gemini-1.5-flash",
            provider=ProviderType.GOOGLE,
            name="Gemini 1.5 Flash",
            context_window=1000000,
            input_price=0.00035,
            output_price=0.00105,
            quality_score=7,
            speed_score=9,
            supports_vision=True
        ),
        "gemini-2.0-flash-exp": ModelInfo(
            id="gemini-2.0-flash-exp",
            provider=ProviderType.GOOGLE,
            name="Gemini 2.0 Flash Exp",
            context_window=1000000,
            input_price=0.00035,
            output_price=0.00105,
            quality_score=8,
            speed_score=10,
            supports_vision=True
        ),
        
        # Groq Models
        "llama-3.1-70b-versatile": ModelInfo(
            id="llama-3.1-70b-versatile",
            provider=ProviderType.GROQ,
            name="Llama 3.1 70B",
            context_window=128000,
            input_price=0.00059,
            output_price=0.00079,
            quality_score=8,
            speed_score=10,
            supports_vision=False
        ),
        "llama-3.1-8b-instant": ModelInfo(
            id="llama-3.1-8b-instant",
            provider=ProviderType.GROQ,
            name="Llama 3.1 8B",
            context_window=128000,
            input_price=0.00005,
            output_price=0.00008,
            quality_score=6,
            speed_score=10,
            supports_vision=False
        ),
        "mixtral-8x7b-32768": ModelInfo(
            id="mixtral-8x7b-32768",
            provider=ProviderType.GROQ,
            name="Mixtral 8x7B",
            context_window=32768,
            input_price=0.00024,
            output_price=0.00024,
            quality_score=7,
            speed_score=10,
            supports_vision=False
        ),
        "gemma2-9b-it": ModelInfo(
            id="gemma2-9b-it",
            provider=ProviderType.GROQ,
            name="Gemma 2 9B",
            context_window=8192,
            input_price=0.00020,
            output_price=0.00020,
            quality_score=6,
            speed_score=10,
            supports_vision=False
        ),
        
        # Kimi (Moonshot AI) Models
        "kimi-k2-5": ModelInfo(
            id="kimi-k2-5",
            provider=ProviderType.KIMI,
            name="Kimi K2.5",
            context_window=256000,
            input_price=0.00125,
            output_price=0.00125,
            quality_score=9,
            speed_score=8,
            supports_vision=True
        ),
        "kimi-k1-6": ModelInfo(
            id="kimi-k1-6",
            provider=ProviderType.KIMI,
            name="Kimi K1.6",
            context_window=200000,
            input_price=0.002,
            output_price=0.006,
            quality_score=8,
            speed_score=8,
            supports_vision=True
        ),
        "kimi-k1-6-thinking": ModelInfo(
            id="kimi-k1-6-thinking",
            provider=ProviderType.KIMI,
            name="Kimi K1.6 Thinking",
            context_window=200000,
            input_price=0.002,
            output_price=0.006,
            quality_score=9,
            speed_score=7,
            supports_vision=True
        ),
        
        # DeepSeek Models
        "deepseek-chat": ModelInfo(
            id="deepseek-chat",
            provider=ProviderType.DEEPSEEK,
            name="DeepSeek V3",
            context_window=64000,
            input_price=0.00014,
            output_price=0.00028,
            quality_score=8,
            speed_score=9,
            supports_vision=False
        ),
        "deepseek-coder": ModelInfo(
            id="deepseek-coder",
            provider=ProviderType.DEEPSEEK,
            name="DeepSeek Coder",
            context_window=64000,
            input_price=0.00014,
            output_price=0.00028,
            quality_score=9,
            speed_score=9,
            supports_vision=False
        ),
        "deepseek-reasoner": ModelInfo(
            id="deepseek-reasoner",
            provider=ProviderType.DEEPSEEK,
            name="DeepSeek R1",
            context_window=64000,
            input_price=0.00055,
            output_price=0.00219,
            quality_score=9,
            speed_score=7,
            supports_vision=False
        ),
        
        # Ollama (Local) Models
        "llama3.2": ModelInfo(
            id="llama3.2",
            provider=ProviderType.OLLAMA,
            name="Llama 3.2",
            context_window=128000,
            input_price=0.0,
            output_price=0.0,
            quality_score=7,
            speed_score=8,
            supports_vision=False
        ),
        "llama3.2-vision": ModelInfo(
            id="llama3.2-vision",
            provider=ProviderType.OLLAMA,
            name="Llama 3.2 Vision",
            context_window=128000,
            input_price=0.0,
            output_price=0.0,
            quality_score=7,
            speed_score=7,
            supports_vision=True
        ),
        "qwen2.5": ModelInfo(
            id="qwen2.5",
            provider=ProviderType.OLLAMA,
            name="Qwen 2.5",
            context_window=128000,
            input_price=0.0,
            output_price=0.0,
            quality_score=8,
            speed_score=8,
            supports_vision=False
        ),
        "qwen2.5-coder": ModelInfo(
            id="qwen2.5-coder",
            provider=ProviderType.OLLAMA,
            name="Qwen 2.5 Coder",
            context_window=128000,
            input_price=0.0,
            output_price=0.0,
            quality_score=8,
            speed_score=8,
            supports_vision=False
        ),
        "mistral": ModelInfo(
            id="mistral",
            provider=ProviderType.OLLAMA,
            name="Mistral",
            context_window=32000,
            input_price=0.0,
            output_price=0.0,
            quality_score=7,
            speed_score=9,
            supports_vision=False
        ),
        "codellama": ModelInfo(
            id="codellama",
            provider=ProviderType.OLLAMA,
            name="CodeLlama",
            context_window=16000,
            input_price=0.0,
            output_price=0.0,
            quality_score=7,
            speed_score=8,
            supports_vision=False
        ),
        "phi4": ModelInfo(
            id="phi4",
            provider=ProviderType.OLLAMA,
            name="Phi-4",
            context_window=16000,
            input_price=0.0,
            output_price=0.0,
            quality_score=8,
            speed_score=8,
            supports_vision=False
        ),
        
        # OpenRouter Models
        "openrouter/claude-3.5-sonnet": ModelInfo(
            id="openrouter/claude-3.5-sonnet",
            provider=ProviderType.OPENROUTER,
            name="Claude 3.5 Sonnet (OR)",
            context_window=200000,
            input_price=0.003,
            output_price=0.015,
            quality_score=9,
            speed_score=8,
            supports_vision=True
        ),
        "openrouter/gpt-4o": ModelInfo(
            id="openrouter/gpt-4o",
            provider=ProviderType.OPENROUTER,
            name="GPT-4o (OR)",
            context_window=128000,
            input_price=0.005,
            output_price=0.015,
            quality_score=9,
            speed_score=8,
            supports_vision=True
        ),
        "openrouter/deepseek-v3": ModelInfo(
            id="openrouter/deepseek-v3",
            provider=ProviderType.OPENROUTER,
            name="DeepSeek V3 (OR)",
            context_window=64000,
            input_price=0.00014,
            output_price=0.00028,
            quality_score=8,
            speed_score=9,
            supports_vision=False
        ),
        "openrouter/llama-3.1-405b": ModelInfo(
            id="openrouter/llama-3.1-405b",
            provider=ProviderType.OPENROUTER,
            name="Llama 3.1 405B (OR)",
            context_window=128000,
            input_price=0.002,
            output_price=0.002,
            quality_score=9,
            speed_score=7,
            supports_vision=False
        ),
        "openrouter/nous-hermes-2-mixtral": ModelInfo(
            id="openrouter/nous-hermes-2-mixtral",
            provider=ProviderType.OPENROUTER,
            name="Nous Hermes 2 Mixtral",
            context_window=32000,
            input_price=0.00027,
            output_price=0.00027,
            quality_score=7,
            speed_score=9,
            supports_vision=False
        ),
    }
    
    PROVIDERS = {
        ProviderType.ANTHROPIC: ProviderConfig(
            type=ProviderType.ANTHROPIC,
            name="Anthropic",
            api_key_env="ANTHROPIC_API_KEY",
            base_url="https://api.anthropic.com/v1",
            models=[]
        ),
        ProviderType.OPENAI: ProviderConfig(
            type=ProviderType.OPENAI,
            name="OpenAI",
            api_key_env="OPENAI_API_KEY",
            base_url="https://api.openai.com/v1",
            models=[]
        ),
        ProviderType.GOOGLE: ProviderConfig(
            type=ProviderType.GOOGLE,
            name="Google",
            api_key_env="GOOGLE_API_KEY",
            base_url="https://generativelanguage.googleapis.com",
            models=[]
        ),
        ProviderType.GROQ: ProviderConfig(
            type=ProviderType.GROQ,
            name="Groq",
            api_key_env="GROQ_API_KEY",
            base_url="https://api.groq.com/openai/v1",
            models=[]
        ),
        ProviderType.KIMI: ProviderConfig(
            type=ProviderType.KIMI,
            name="Kimi (Moonshot)",
            api_key_env="KIMI_API_KEY",
            base_url="https://api.moonshot.cn/v1",
            models=[]
        ),
        ProviderType.DEEPSEEK: ProviderConfig(
            type=ProviderType.DEEPSEEK,
            name="DeepSeek",
            api_key_env="DEEPSEEK_API_KEY",
            base_url="https://api.deepseek.com/v1",
            models=[]
        ),
        ProviderType.OLLAMA: ProviderConfig(
            type=ProviderType.OLLAMA,
            name="Ollama (Local)",
            api_key_env="OLLAMA_HOST",
            base_url="http://localhost:11434",
            requires_key=False,
            is_local=True,
            models=[]
        ),
        ProviderType.OPENROUTER: ProviderConfig(
            type=ProviderType.OPENROUTER,
            name="OpenRouter",
            api_key_env="OPENROUTER_API_KEY",
            base_url="https://openrouter.ai/api/v1",
            models=[]
        ),
    }
    
    def __init__(self):
        self._init_provider_models()
    
    def _init_provider_models(self):
        """Associate models with their providers"""
        for model in self.MODELS.values():
            if model.provider in self.PROVIDERS:
                self.PROVIDERS[model.provider].models.append(model)
    
    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """Get model info by ID"""
        return self.MODELS.get(model_id)
    
    def get_provider(self, provider_type: ProviderType) -> Optional[ProviderConfig]:
        """Get provider config"""
        return self.PROVIDERS.get(provider_type)
    
    def get_provider_for_model(self, model_id: str) -> Optional[ProviderConfig]:
        """Get provider config for a model"""
        model = self.MODELS.get(model_id)
        if model:
            return self.PROVIDERS.get(model.provider)
        return None
    
    def is_provider_available(self, provider_type: ProviderType) -> bool:
        """Check if provider is configured and available"""
        provider = self.PROVIDERS.get(provider_type)
        if not provider:
            return False
        
        if provider.is_local:
            # For Ollama, check if host is set or default localhost
            host = os.getenv(provider.api_key_env, "http://localhost:11434")
            return host is not None
        
        return bool(os.getenv(provider.api_key_env))
    
    def is_model_available(self, model_id: str) -> bool:
        """Check if model's provider is available"""
        model = self.MODELS.get(model_id)
        if not model:
            return False
        return self.is_provider_available(model.provider)
    
    def list_available_providers(self) -> List[ProviderConfig]:
        """List all available (configured) providers"""
        return [p for p in self.PROVIDERS.values() if self.is_provider_available(p.type)]
    
    def list_available_models(self) -> List[ModelInfo]:
        """List all available models"""
        return [m for m in self.MODELS.values() if self.is_model_available(m.id)]
    
    def list_models_by_provider(self, provider_type: ProviderType) -> List[ModelInfo]:
        """List models for a specific provider"""
        provider = self.PROVIDERS.get(provider_type)
        if provider:
            return provider.models
        return []
    
    def get_api_key(self, provider_type: ProviderType) -> Optional[str]:
        """Get API key for provider"""
        provider = self.PROVIDERS.get(provider_type)
        if provider:
            if provider.is_local:
                return os.getenv(provider.api_key_env, provider.base_url)
            return os.getenv(provider.api_key_env)
        return None
    
    def get_base_url(self, provider_type: ProviderType) -> Optional[str]:
        """Get base URL for provider"""
        provider = self.PROVIDERS.get(provider_type)
        if provider:
            if provider.is_local:
                return os.getenv(provider.api_key_env, provider.base_url)
            return provider.base_url
        return None
    
    def recommend_model(self, task_complexity: str = "medium", 
                       priority: str = "balanced") -> str:
        """Recommend a model based on task and priority"""
        available = self.list_available_models()
        
        if not available:
            return "gpt-4o-mini"  # Fallback
        
        # Filter by complexity
        if task_complexity == "high":
            candidates = [m for m in available if m.quality_score >= 8]
        elif task_complexity == "low":
            candidates = [m for m in available if m.speed_score >= 8]
        else:
            candidates = available
        
        if not candidates:
            candidates = available
        
        # Sort by priority
        if priority == "quality":
            candidates.sort(key=lambda m: (m.quality_score * -1, m.input_price))
        elif priority == "speed":
            candidates.sort(key=lambda m: (m.speed_score * -1, m.input_price))
        elif priority == "cost":
            candidates.sort(key=lambda m: (m.input_price + m.output_price))
        else:  # balanced
            candidates.sort(key=lambda m: (
                (m.quality_score + m.speed_score) * -1,
                m.input_price + m.output_price
            ))
        
        return candidates[0].id if candidates else available[0].id
    
    def calculate_cost(self, model_id: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for a model usage"""
        model = self.MODELS.get(model_id)
        if not model:
            return 0.0
        
        input_cost = (input_tokens / 1000) * model.input_price
        output_cost = (output_tokens / 1000) * model.output_price
        return input_cost + output_cost
    
    def get_model_comparison(self) -> List[Dict]:
        """Get comparison table of all models"""
        comparison = []
        for model in self.MODELS.values():
            comparison.append({
                "id": model.id,
                "name": model.name,
                "provider": model.provider.value,
                "available": self.is_model_available(model.id),
                "input_price": model.input_price,
                "output_price": model.output_price,
                "context": model.context_window,
                "quality": model.quality_score,
                "speed": model.speed_score,
                "vision": model.supports_vision,
            })
        return comparison
    
    def format_price(self, price: float) -> str:
        """Format price for display"""
        if price == 0:
            return "FREE"
        return f"${price:.6f}"

# Global instance
_provider_manager = None

def get_provider_manager() -> ProviderManager:
    """Get singleton provider manager"""
    global _provider_manager
    if _provider_manager is None:
        _provider_manager = ProviderManager()
    return _provider_manager
