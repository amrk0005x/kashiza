"""
Plugin: Cost Monitor
Surveillance en temps réel des coûts et alertes
"""
import sys
sys.path.append('..')
from core.plugin import Plugin, hook

class CostMonitorPlugin(Plugin):
    name = "cost-monitor"
    version = "1.0.0"
    author = "Hermes"
    description = "Real-time cost monitoring and alerts"
    dependencies = []
    
    def __init__(self, config=None):
        super().__init__(config)
        self.daily_cost = 0.0
        self.alert_threshold = config.get("alert_threshold", 5.0) if config else 5.0
    
    @hook("pre_tool_call")
    def log_tool_cost(self, tool_name, args):
        """Log avant chaque appel d'outil"""
        print(f"[CostMonitor] Tool call: {tool_name}")
        return args
    
    @hook("post_response")
    def track_response_cost(self, response):
        """Track le coût après chaque réponse"""
        # Estimation simple basée sur la longueur
        estimated_tokens = len(response) / 4
        estimated_cost = estimated_tokens * 0.00001  # ~$0.01 par 1K tokens
        
        self.daily_cost += estimated_cost
        
        if self.daily_cost > self.alert_threshold:
            print(f"[CostMonitor] ⚠️  Daily cost: ${self.daily_cost:.4f}")
        
        return response
    
    @hook("on_error")
    def log_error_cost(self, error):
        """Log les erreurs qui ont un coût"""
        print(f"[CostMonitor] Error occurred (cost wasted): {type(error).__name__}")
        return {"error": str(error), "monitored": True}
    
    def get_daily_cost(self):
        return self.daily_cost
    
    def reset_daily(self):
        self.daily_cost = 0.0
