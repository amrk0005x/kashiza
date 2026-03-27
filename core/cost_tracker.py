import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import asyncio

@dataclass
class CostEntry:
    timestamp: float
    agent_id: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    task_type: str
    
@dataclass
class BudgetAlert:
    level: str
    threshold_percent: float
    current_spend: float
    budget: float
    message: str
    timestamp: float

class SmartCostTracker:
    def __init__(self, config_path: str = "config/cost_config.json"):
        self.config_path = config_path
        self.daily_budget: float = 10.0
        self.monthly_budget: float = 100.0
        self.alert_thresholds: List[float] = [0.5, 0.8, 1.0]
        self.auto_switch_cheaper: bool = True
        
        self.daily_spend: float = 0.0
        self.monthly_spend: float = 0.0
        self.cost_history: List[CostEntry] = []
        self.alerts_triggered: List[BudgetAlert] = []
        self.model_usage: Dict[str, Dict] = defaultdict(lambda: {"calls": 0, "cost": 0.0})
        
        self._callbacks: List[callable] = []
        self._last_reset_day: int = 0
        self._last_reset_month: int = 0
        
        self._load_config()
        self._check_reset()
    
    def _load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                self.daily_budget = config.get('daily_budget', 10.0)
                self.monthly_budget = config.get('monthly_budget', 100.0)
                self.alert_thresholds = config.get('alert_thresholds', [0.5, 0.8, 1.0])
                self.auto_switch_cheaper = config.get('auto_switch_cheaper', True)
        except:
            self._save_config()
    
    def _save_config(self):
        import os
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump({
                'daily_budget': self.daily_budget,
                'monthly_budget': self.monthly_budget,
                'alert_thresholds': self.alert_thresholds,
                'auto_switch_cheaper': self.auto_switch_cheaper
            }, f, indent=2)
    
    def _check_reset(self):
        now = time.localtime()
        if now.tm_mday != self._last_reset_day:
            self.daily_spend = 0.0
            self._last_reset_day = now.tm_mday
        if now.tm_mon != self._last_reset_month:
            self.monthly_spend = 0.0
            self._last_reset_month = now.tm_mon
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost using provider manager pricing"""
        try:
            from core.providers import get_provider_manager
            pm = get_provider_manager()
            return pm.calculate_cost(model, input_tokens, output_tokens)
        except ImportError:
            # Fallback pricing for backward compatibility
            pricing = self._get_fallback_pricing(model)
            input_cost = (input_tokens / 1000) * pricing["input"]
            output_cost = (output_tokens / 1000) * pricing["output"]
            return input_cost + output_cost
    
    def _get_fallback_pricing(self, model: str) -> Dict:
        """Fallback pricing if provider manager not available"""
        pricing = {
            # Anthropic
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
            "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
            # OpenAI
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            # Google
            "gemini-1.5-pro": {"input": 0.0035, "output": 0.0105},
            "gemini-1.5-flash": {"input": 0.00035, "output": 0.00105},
            # Groq
            "llama-3.1-70b-versatile": {"input": 0.00059, "output": 0.00079},
            "llama-3.1-8b-instant": {"input": 0.00005, "output": 0.00008},
            # Kimi
            "kimi-k2-5": {"input": 0.00125, "output": 0.00125},
            "kimi-k1-6": {"input": 0.002, "output": 0.006},
            # DeepSeek
            "deepseek-chat": {"input": 0.00014, "output": 0.00028},
            "deepseek-coder": {"input": 0.00014, "output": 0.00028},
            "deepseek-reasoner": {"input": 0.00055, "output": 0.00219},
            # Ollama (free)
            "llama3.2": {"input": 0, "output": 0},
            "qwen2.5": {"input": 0, "output": 0},
            "mistral": {"input": 0, "output": 0},
        }
        return pricing.get(model, {"input": 0.01, "output": 0.03})
    
    def add_cost(self, cost: float, agent_id: str = "unknown", model: str = "unknown",
                 input_tokens: int = 0, output_tokens: int = 0, task_type: str = "general"):
        self._check_reset()
        
        entry = CostEntry(
            timestamp=time.time(),
            agent_id=agent_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            task_type=task_type
        )
        
        self.cost_history.append(entry)
        self.daily_spend += cost
        self.monthly_spend += cost
        
        self.model_usage[model]["calls"] += 1
        self.model_usage[model]["cost"] += cost
        
        self._check_alerts()
    
    def _check_alerts(self):
        for threshold in self.alert_thresholds:
            daily_pct = self.daily_spend / self.daily_budget
            monthly_pct = self.monthly_spend / self.monthly_budget
            
            if daily_pct >= threshold or monthly_pct >= threshold:
                alert = BudgetAlert(
                    level="warning" if threshold < 1.0 else "critical",
                    threshold_percent=threshold * 100,
                    current_spend=max(self.daily_spend, self.monthly_spend),
                    budget=self.daily_budget if daily_pct >= threshold else self.monthly_budget,
                    message=f"Budget alert: {threshold*100}% reached",
                    timestamp=time.time()
                )
                self.alerts_triggered.append(alert)
                
                for callback in self._callbacks:
                    callback(alert)
    
    def on_budget_alert(self, callback: callable):
        self._callbacks.append(callback)
    
    def get_remaining_budget(self) -> float:
        self._check_reset()
        return min(
            self.daily_budget - self.daily_spend,
            self.monthly_budget - self.monthly_spend
        )
    
    def get_budget_status(self) -> Dict:
        self._check_reset()
        return {
            "daily": {
                "budget": self.daily_budget,
                "spent": self.daily_spend,
                "remaining": self.daily_budget - self.daily_spend,
                "percent_used": (self.daily_spend / self.daily_budget) * 100
            },
            "monthly": {
                "budget": self.monthly_budget,
                "spent": self.monthly_spend,
                "remaining": self.monthly_budget - self.monthly_spend,
                "percent_used": (self.monthly_spend / self.monthly_budget) * 100
            }
        }
    
    def get_cheaper_alternative(self, model: str, task_complexity: str = "medium") -> Optional[str]:
        """Find a cheaper alternative using provider manager"""
        try:
            from core.providers import get_provider_manager
            pm = get_provider_manager()
            
            current_model = pm.get_model(model)
            if not current_model:
                return None
            
            available = pm.list_available_models()
            alternatives = []
            
            for m in available:
                if m.input_price < current_model.input_price:
                    score = self._score_alternative(m, task_complexity)
                    alternatives.append((m.id, m.input_price, score))
            
            if not alternatives:
                return None
            
            # Sort by score (higher is better) then by price
            alternatives.sort(key=lambda x: (x[2] * -1, x[1]))
            return alternatives[0][0]
            
        except ImportError:
            return self._fallback_cheaper_alternative(model, task_complexity)
    
    def _score_alternative(self, model, task_complexity: str) -> int:
        """Score an alternative model for a task"""
        scores = {
            "low": {"quality": 0.3, "speed": 0.7},
            "medium": {"quality": 0.5, "speed": 0.5},
            "high": {"quality": 0.8, "speed": 0.2}
        }
        weights = scores.get(task_complexity, scores["medium"])
        return int(model.quality_score * weights["quality"] + 
                   model.speed_score * weights["speed"])
    
    def _fallback_cheaper_alternative(self, model: str, task_complexity: str = "medium") -> Optional[str]:
        """Fallback method if provider manager not available"""
        pricing = self._get_fallback_pricing(model)
        current_price = pricing["input"]
        
        alternatives = []
        for m, p in self._get_fallback_pricing.items():
            if isinstance(p, dict) and p["input"] < current_price:
                alternatives.append((m, p["input"]))
        
        alternatives.sort(key=lambda x: x[1])
        
        quality_ok = {
            "low": ["claude-3-haiku-20240307", "gpt-4o-mini", "gemini-1.5-flash", 
                    "llama-3.1-8b-instant", "deepseek-chat"],
            "medium": ["claude-3-sonnet-20240229", "gpt-4o", "gemini-1.5-pro",
                       "llama-3.1-70b-versatile", "kimi-k2-5"],
            "high": ["claude-3-opus-20240229", "gpt-4o", "claude-3-5-sonnet-20241022"]
        }
        
        acceptable = quality_ok.get(task_complexity, quality_ok["medium"])
        
        for alt, price in alternatives:
            if alt in acceptable:
                return alt
        
        return alternatives[0][0] if alternatives else None
    
    def should_use_cheaper_model(self, estimated_cost: float) -> bool:
        remaining = self.get_remaining_budget()
        return estimated_cost > remaining * 0.5
    
    def get_model_recommendation(self, task_description: str) -> Dict:
        """Get model recommendation using provider manager"""
        try:
            from core.providers import get_provider_manager
            pm = get_provider_manager()
            
            complexity = self._estimate_complexity(task_description)
            priority = "cost" if self.should_use_cheaper_model(0.01) else "balanced"
            
            recommended = pm.recommend_model(complexity, priority)
            available = pm.list_available_models()
            
            estimated_tokens = len(task_description.split()) * 2
            
            recommendations = []
            for model in available[:10]:  # Top 10
                cost = pm.calculate_cost(model.id, estimated_tokens, 
                                        int(estimated_tokens * 0.5))
                recommendations.append({
                    "model": model.id,
                    "name": model.name,
                    "provider": model.provider.value,
                    "estimated_cost": cost,
                    "suitable_for": complexity,
                    "quality_score": model.quality_score,
                    "speed_score": model.speed_score,
                    "recommended": model.id == recommended
                })
            
            # Sort by recommended first, then quality, then cost
            recommendations.sort(key=lambda x: (
                not x["recommended"],
                x["quality_score"] * -1,
                x["estimated_cost"]
            ))
            
            return {
                "task_complexity": complexity,
                "estimated_tokens": estimated_tokens,
                "recommendations": recommendations[:5]
            }
            
        except ImportError:
            return self._fallback_recommendation(task_description)
    
    def _fallback_recommendation(self, task_description: str) -> Dict:
        """Fallback recommendation without provider manager"""
        complexity = self._estimate_complexity(task_description)
        estimated_tokens = len(task_description.split()) * 2
        
        fallback_models = [
            ("claude-3-haiku-20240307", 0.00025, 0.00125),
            ("gpt-4o-mini", 0.00015, 0.0006),
            ("gemini-1.5-flash", 0.00035, 0.00105),
        ]
        
        recommendations = []
        for model, inp, out in fallback_models:
            est_input = estimated_tokens
            est_output = int(estimated_tokens * 0.5)
            cost = (est_input / 1000) * inp + (est_output / 1000) * out
            recommendations.append({
                "model": model,
                "estimated_cost": cost,
                "suitable_for": complexity,
                "quality_score": 7,
                "recommended": model == "gpt-4o-mini"
            })
        
        return {
            "task_complexity": complexity,
            "estimated_tokens": estimated_tokens,
            "recommendations": recommendations
        }
    
    def _estimate_complexity(self, task: str) -> str:
        task_lower = task.lower()
        
        high_complexity = ["architecture", "complex", "system design", "algorithm", 
                          "optimize", "refactor", "rewrite"]
        low_complexity = ["simple", "quick", "fix", "rename", "format", "typo"]
        
        if any(w in task_lower for w in high_complexity):
            return "high"
        if any(w in task_lower for w in low_complexity):
            return "low"
        return "medium"
    
    def get_cost_report(self, days: int = 7) -> Dict:
        cutoff = time.time() - (days * 24 * 3600)
        recent = [e for e in self.cost_history if e.timestamp > cutoff]
        
        by_agent = defaultdict(lambda: {"cost": 0.0, "calls": 0})
        by_model = defaultdict(lambda: {"cost": 0.0, "calls": 0})
        by_day = defaultdict(float)
        by_provider = defaultdict(lambda: {"cost": 0.0, "calls": 0})
        
        for entry in recent:
            by_agent[entry.agent_id]["cost"] += entry.cost
            by_agent[entry.agent_id]["calls"] += 1
            by_model[entry.model]["cost"] += entry.cost
            by_model[entry.model]["calls"] += 1
            
            # Try to get provider from model
            try:
                from core.providers import get_provider_manager
                pm = get_provider_manager()
                model_info = pm.get_model(entry.model)
                if model_info:
                    provider = model_info.provider.value
                    by_provider[provider]["cost"] += entry.cost
                    by_provider[provider]["calls"] += 1
            except:
                pass
            
            day = time.strftime("%Y-%m-%d", time.localtime(entry.timestamp))
            by_day[day] += entry.cost
        
        return {
            "total_cost": sum(e.cost for e in recent),
            "total_calls": len(recent),
            "avg_cost_per_call": sum(e.cost for e in recent) / len(recent) if recent else 0,
            "by_agent": dict(by_agent),
            "by_model": dict(by_model),
            "by_provider": dict(by_provider),
            "daily_breakdown": dict(by_day),
            "projected_monthly": (sum(e.cost for e in recent) / len(recent)) * 30 if recent else 0
        }
    
    def export_to_csv(self, path: str):
        import csv
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'agent_id', 'model', 'input_tokens', 
                           'output_tokens', 'cost', 'task_type'])
            for entry in self.cost_history:
                writer.writerow([
                    time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(entry.timestamp)),
                    entry.agent_id,
                    entry.model,
                    entry.input_tokens,
                    entry.output_tokens,
                    entry.cost,
                    entry.task_type
                ])

_cost_tracker = None

def get_cost_tracker() -> SmartCostTracker:
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = SmartCostTracker()
    return _cost_tracker
