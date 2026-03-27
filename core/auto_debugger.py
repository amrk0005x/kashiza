import re
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
from collections import defaultdict

class ErrorType(Enum):
    SYNTAX = "syntax_error"
    RUNTIME = "runtime_error"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    CONTEXT_LENGTH = "context_length"
    API_ERROR = "api_error"
    TOOL_ERROR = "tool_error"
    UNKNOWN = "unknown"

class FixStrategy(Enum):
    RETRY = "retry"
    SIMPLIFY_PROMPT = "simplify_prompt"
    COMPRESS_CONTEXT = "compress_context"
    SWITCH_MODEL = "switch_model"
    REDUCE_MAX_TOKENS = "reduce_max_tokens"
    SPLIT_TASK = "split_task"
    ADD_EXAMPLES = "add_examples"
    FALLBACK = "fallback"

@dataclass
class ErrorRecord:
    error_type: ErrorType
    message: str
    timestamp: float
    context: Dict
    attempts: int = 0
    strategies_tried: List[FixStrategy] = None
    
    def __post_init__(self):
        if self.strategies_tried is None:
            self.strategies_tried = []

@dataclass
class FixResult:
    success: bool
    output: str
    strategy_used: FixStrategy
    attempts: int
    execution_time: float

class SmartDebugger:
    MAX_RETRIES = 3
    CIRCUIT_BREAKER_THRESHOLD = 5
    CIRCUIT_BREAKER_TIMEOUT = 300
    
    def __init__(self):
        self.error_history: List[ErrorRecord] = []
        self.strategy_success_rates: Dict[FixStrategy, Dict] = defaultdict(lambda: {"success": 0, "total": 0})
        self.circuit_breakers: Dict[str, Dict] = {}
        self.retry_delays = [1, 2, 4, 8, 16]
        self._load_patterns()
    
    def _load_patterns(self):
        self.error_patterns = {
            ErrorType.SYNTAX: [
                r"syntax error",
                r"unexpected token",
                r"invalid syntax",
                r"parse error",
                r"indentation error"
            ],
            ErrorType.RUNTIME: [
                r"runtime error",
                r"exception",
                r"traceback",
                r"undefined",
                r"null pointer",
                r"index out of range"
            ],
            ErrorType.TIMEOUT: [
                r"timeout",
                r"time limit exceeded",
                r"deadline exceeded",
                r"took too long"
            ],
            ErrorType.RATE_LIMIT: [
                r"rate limit",
                r"too many requests",
                r"429",
                r"throttled"
            ],
            ErrorType.CONTEXT_LENGTH: [
                r"context length exceeded",
                r"maximum context length",
                r"too many tokens",
                r"token limit"
            ],
            ErrorType.API_ERROR: [
                r"api error",
                r"internal server error",
                r"500",
                r"502",
                r"503"
            ],
            ErrorType.TOOL_ERROR: [
                r"tool error",
                r"tool failed",
                r"tool timeout",
                r"tool not found"
            ]
        }
    
    def classify_error(self, error_message: str) -> ErrorType:
        error_lower = error_message.lower()
        
        for error_type, patterns in self.error_patterns.items():
            for pattern in patterns:
                if re.search(pattern, error_lower):
                    return error_type
        
        return ErrorType.UNKNOWN
    
    def check_circuit_breaker(self, agent_id: str) -> bool:
        if agent_id not in self.circuit_breakers:
            return True
        
        cb = self.circuit_breakers[agent_id]
        if cb["failures"] >= self.CIRCUIT_BREAKER_THRESHOLD:
            if time.time() - cb["last_failure"] < self.CIRCUIT_BREAKER_TIMEOUT:
                return False
            else:
                cb["failures"] = 0
        
        return True
    
    def record_failure(self, agent_id: str):
        if agent_id not in self.circuit_breakers:
            self.circuit_breakers[agent_id] = {"failures": 0, "last_failure": 0}
        
        self.circuit_breakers[agent_id]["failures"] += 1
        self.circuit_breakers[agent_id]["last_failure"] = time.time()
    
    def record_success(self, agent_id: str):
        if agent_id in self.circuit_breakers:
            self.circuit_breakers[agent_id]["failures"] = max(0, self.circuit_breakers[agent_id]["failures"] - 1)
    
    async def attempt_fix(self, prompt: str, agent, error_message: str, 
                         context: Dict = None) -> FixResult:
        start_time = time.time()
        error_type = self.classify_error(error_message)
        
        record = ErrorRecord(
            error_type=error_type,
            message=error_message,
            timestamp=time.time(),
            context=context or {}
        )
        self.error_history.append(record)
        
        strategies = self._select_strategies(error_type, agent.id)
        
        for attempt, strategy in enumerate(strategies[:self.MAX_RETRIES]):
            record.attempts = attempt + 1
            record.strategies_tried.append(strategy)
            
            try:
                fixed_prompt = self._apply_strategy(prompt, strategy, error_message)
                
                output = await self._execute_with_retry(fixed_prompt, agent, strategy)
                
                if output and not output.startswith("Error"):
                    self._record_strategy_success(strategy, True)
                    self.record_success(agent.id)
                    
                    return FixResult(
                        success=True,
                        output=output,
                        strategy_used=strategy,
                        attempts=attempt + 1,
                        execution_time=time.time() - start_time
                    )
                
            except Exception as e:
                self._record_strategy_success(strategy, False)
                continue
        
        self.record_failure(agent.id)
        
        return FixResult(
            success=False,
            output=f"Failed after {self.MAX_RETRIES} attempts. Last error: {error_message}",
            strategy_used=FixStrategy.FALLBACK,
            attempts=self.MAX_RETRIES,
            execution_time=time.time() - start_time
        )
    
    def _select_strategies(self, error_type: ErrorType, agent_id: str) -> List[FixStrategy]:
        strategies = []
        
        strategy_map = {
            ErrorType.SYNTAX: [FixStrategy.ADD_EXAMPLES, FixStrategy.SIMPLIFY_PROMPT, FixStrategy.RETRY],
            ErrorType.RUNTIME: [FixStrategy.SIMPLIFY_PROMPT, FixStrategy.SPLIT_TASK, FixStrategy.RETRY],
            ErrorType.TIMEOUT: [FixStrategy.REDUCE_MAX_TOKENS, FixStrategy.SPLIT_TASK, FixStrategy.SWITCH_MODEL],
            ErrorType.RATE_LIMIT: [FixStrategy.RETRY, FixStrategy.SWITCH_MODEL, FixStrategy.FALLBACK],
            ErrorType.CONTEXT_LENGTH: [FixStrategy.COMPRESS_CONTEXT, FixStrategy.SPLIT_TASK, FixStrategy.SIMPLIFY_PROMPT],
            ErrorType.API_ERROR: [FixStrategy.RETRY, FixStrategy.SWITCH_MODEL, FixStrategy.FALLBACK],
            ErrorType.TOOL_ERROR: [FixStrategy.SIMPLIFY_PROMPT, FixStrategy.RETRY, FixStrategy.FALLBACK],
            ErrorType.UNKNOWN: [FixStrategy.RETRY, FixStrategy.SIMPLIFY_PROMPT, FixStrategy.SWITCH_MODEL]
        }
        
        strategies = strategy_map.get(error_type, [FixStrategy.RETRY, FixStrategy.FALLBACK])
        
        # Sort by success rate
        strategies.sort(key=lambda s: 
            self.strategy_success_rates[s]["success"] / max(self.strategy_success_rates[s]["total"], 1),
            reverse=True
        )
        
        return strategies
    
    def _apply_strategy(self, prompt: str, strategy: FixStrategy, error_message: str) -> str:
        if strategy == FixStrategy.SIMPLIFY_PROMPT:
            return self._simplify_prompt(prompt)
        
        elif strategy == FixStrategy.COMPRESS_CONTEXT:
            return self._compress_context(prompt)
        
        elif strategy == FixStrategy.SPLIT_TASK:
            return self._add_split_instructions(prompt)
        
        elif strategy == FixStrategy.ADD_EXAMPLES:
            return self._add_examples(prompt)
        
        elif strategy == FixStrategy.REDUCE_MAX_TOKENS:
            return f"{prompt}\n\n[SYSTEM: Please provide a concise response, maximum 500 tokens.]"
        
        elif strategy == FixStrategy.SWITCH_MODEL:
            return prompt
        
        return prompt
    
    def _simplify_prompt(self, prompt: str) -> str:
        lines = prompt.split('\n')
        
        # Remove verbose descriptions
        simplified = []
        for line in lines:
            if any(w in line.lower() for w in ["please", "would you", "could you", "i would like"]):
                line = line.replace("Please ", "").replace("Could you ", "").replace("Would you ", "")
            simplified.append(line)
        
        # Keep only essential context
        if len(simplified) > 50:
            simplified = simplified[:20] + ["..."] + simplified[-10:]
        
        return '\n'.join(simplified)
    
    def _compress_context(self, prompt: str) -> str:
        # Remove redundant whitespace
        prompt = re.sub(r'\n\s*\n', '\n\n', prompt)
        
        # Summarize long sections
        if len(prompt) > 4000:
            sections = prompt.split('\n\n')
            compressed = []
            for section in sections:
                if len(section) > 500:
                    lines = section.split('\n')
                    compressed.append(f"[Summary: {len(lines)} lines of context]")
                else:
                    compressed.append(section)
            prompt = '\n\n'.join(compressed)
        
        return prompt
    
    def _add_split_instructions(self, prompt: str) -> str:
        return f"""{prompt}

[SYSTEM INSTRUCTION: Break this task into smaller subtasks. Complete each one step at a time and indicate when you've finished each step.]"""
    
    def _add_examples(self, prompt: str) -> str:
        return f"""{prompt}

[EXAMPLE FORMAT:
Input: [example input]
Output: [example output]
]

Please follow this format for your response."""
    
    async def _execute_with_retry(self, prompt: str, agent, strategy: FixStrategy) -> str:
        from kashiza import AIAgent
        
        model = agent.model
        if strategy == FixStrategy.SWITCH_MODEL:
            # Switch to more reliable model
            model = "claude-3-sonnet-20240229"
        
        for delay in self.retry_delays:
            try:
                kashiza_agent = AIAgent(
                    model=model,
                    enabled_toolsets=agent.skills,
                    quiet_mode=True
                )
                
                response = kashiza_agent.chat(prompt)
                return response
                
            except Exception as e:
                if "rate limit" in str(e).lower():
                    await asyncio.sleep(delay)
                    continue
                raise
        
        raise Exception("Max retries exceeded")
    
    def _record_strategy_success(self, strategy: FixStrategy, success: bool):
        self.strategy_success_rates[strategy]["total"] += 1
        if success:
            self.strategy_success_rates[strategy]["success"] += 1
    
    def get_error_stats(self) -> Dict:
        by_type = defaultdict(int)
        for record in self.error_history:
            by_type[record.error_type.value] += 1
        
        strategy_stats = {}
        for strategy, stats in self.strategy_success_rates.items():
            strategy_stats[strategy.value] = {
                "success_rate": stats["success"] / max(stats["total"], 1),
                "total_attempts": stats["total"]
            }
        
        return {
            "total_errors": len(self.error_history),
            "by_type": dict(by_type),
            "strategy_effectiveness": strategy_stats,
            "circuit_breaker_states": {k: v["failures"] for k, v in self.circuit_breakers.items()}
        }
    
    def generate_self_healing_config(self) -> Dict:
        # Analyze patterns and suggest config improvements
        if len(self.error_history) < 10:
            return {"status": "insufficient_data"}
        
        recent = self.error_history[-50:]
        
        config = {
            "auto_retry": True,
            "max_retries": 3,
            "circuit_breaker": {
                "enabled": True,
                "threshold": 5,
                "timeout": 300
            }
        }
        
        # Context length issues
        context_errors = [r for r in recent if r.error_type == ErrorType.CONTEXT_LENGTH]
        if len(context_errors) > len(recent) * 0.3:
            config["auto_compress_context"] = True
            config["context_compression_threshold"] = 3000
        
        # Timeout issues
        timeout_errors = [r for r in recent if r.error_type == ErrorType.TIMEOUT]
        if len(timeout_errors) > len(recent) * 0.2:
            config["default_timeout"] = 60
            config["auto_split_long_tasks"] = True
        
        # Rate limit issues
        rate_errors = [r for r in recent if r.error_type == ErrorType.RATE_LIMIT]
        if len(rate_errors) > 5:
            config["request_throttling"] = True
            config["min_request_interval"] = 1.0
        
        return config

_debugger = None

def get_debugger() -> SmartDebugger:
    global _debugger
    if _debugger is None:
        _debugger = SmartDebugger()
    return _debugger
