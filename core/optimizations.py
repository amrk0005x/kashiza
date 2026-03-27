import hashlib
import json
import time
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from collections import OrderedDict
import functools

@dataclass
class CacheEntry:
    key: str
    value: Any
    timestamp: float
    ttl: int
    access_count: int = 0

class SmartCache:
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
    
    def _generate_key(self, *args, **kwargs) -> str:
        key_data = json.dumps({'args': args, 'kwargs': kwargs}, sort_keys=True, default=str)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            entry = self.cache[key]
            
            # Check TTL
            if time.time() - entry.timestamp > entry.ttl:
                del self.cache[key]
                return None
            
            # Update access
            entry.access_count += 1
            self.cache.move_to_end(key)
            self.stats['hits'] += 1
            
            return entry.value
        
        self.stats['misses'] += 1
        return None
    
    def set(self, key: str, value: Any, ttl: int = None):
        ttl = ttl or self.default_ttl
        
        # Evict if necessary (LRU)
        while len(self.cache) >= self.max_size:
            oldest = next(iter(self.cache))
            del self.cache[oldest]
            self.stats['evictions'] += 1
        
        self.cache[key] = CacheEntry(
            key=key,
            value=value,
            timestamp=time.time(),
            ttl=ttl
        )
    
    def invalidate(self, key: str):
        if key in self.cache:
            del self.cache[key]
    
    def invalidate_pattern(self, pattern: str):
        keys_to_remove = [k for k in self.cache.keys() if pattern in k]
        for k in keys_to_remove:
            del self.cache[k]
    
    def clear(self):
        self.cache.clear()
    
    def get_stats(self) -> Dict:
        total = self.stats['hits'] + self.stats['misses']
        hit_rate = self.stats['hits'] / total if total > 0 else 0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'hit_rate': hit_rate,
            'evictions': self.stats['evictions']
        }

class ToolResultCache(SmartCache):
    def __init__(self, max_size: int = 500):
        super().__init__(max_size, default_ttl=1800)  # 30 min default for tools
    
    def cache_tool_result(self, tool_name: str, args: Dict, result: Any, ttl: int = None):
        key = self._generate_tool_key(tool_name, args)
        self.set(key, result, ttl)
    
    def get_tool_result(self, tool_name: str, args: Dict) -> Optional[Any]:
        key = self._generate_tool_key(tool_name, args)
        return self.get(key)
    
    def _generate_tool_key(self, tool_name: str, args: Dict) -> str:
        return hashlib.md5(f"{tool_name}:{json.dumps(args, sort_keys=True)}".encode()).hexdigest()

class PromptCache(SmartCache):
    def __init__(self, max_size: int = 200):
        super().__init__(max_size, default_ttl=7200)  # 2 hours for prompts
    
    def cache_response(self, prompt: str, model: str, response: str):
        key = self._generate_key(prompt, model)
        self.set(key, response)
    
    def get_cached_response(self, prompt: str, model: str) -> Optional[str]:
        key = self._generate_key(prompt, model)
        return self.get(key)

class ContextCompressor:
    COMPRESSION_THRESHOLD = 3000  # tokens
    
    def __init__(self):
        self.compression_stats = {
            'compressed': 0,
            'bytes_saved': 0
        }
    
    def should_compress(self, context: str) -> bool:
        # Rough token estimate
        estimated_tokens = len(context.split()) * 1.3
        return estimated_tokens > self.COMPRESSION_THRESHOLD
    
    def compress(self, context: str, strategy: str = "summarize") -> str:
        if not self.should_compress(context):
            return context
        
        if strategy == "summarize":
            return self._summarize_context(context)
        elif strategy == "truncate":
            return self._truncate_context(context)
        elif strategy == "selective":
            return self._selective_keep(context)
        
        return context
    
    def _summarize_context(self, context: str) -> str:
        # Simple summarization: keep first and last parts, summarize middle
        lines = context.split('\n')
        
        if len(lines) < 20:
            return context
        
        # Keep first 10 and last 5 lines, summarize the rest
        first_part = '\n'.join(lines[:10])
        last_part = '\n'.join(lines[-5:])
        
        middle_count = len(lines) - 15
        
        self.compression_stats['compressed'] += 1
        self.compression_stats['bytes_saved'] += len(context) - len(first_part) - len(last_part) - 50
        
        return f"{first_part}\n\n[... {middle_count} lines summarized ...]\n\n{last_part}"
    
    def _truncate_context(self, context: str) -> str:
        # Keep most recent/important parts
        lines = context.split('\n')
        
        if len(lines) > 50:
            # Keep last 50 lines
            kept = '\n'.join(lines[-50:])
            self.compression_stats['bytes_saved'] += len(context) - len(kept)
            return f"[Context truncated]\n{kept}"
        
        return context
    
    def _selective_keep(self, context: str) -> str:
        # Keep important sections based on markers
        lines = context.split('\n')
        important = []
        
        skip_patterns = [
            r'^\s*#.*File.*extracted',  # File headers
            r'^\s*```\w*\s*$',  # Code block markers
            r'^\s*\d+\s*\|',  # Line numbers
        ]
        
        for line in lines:
            should_keep = True
            for pattern in skip_patterns:
                import re
                if re.match(pattern, line):
                    should_keep = False
                    break
            
            if should_keep:
                important.append(line)
        
        return '\n'.join(important)
    
    def get_stats(self) -> Dict:
        return self.compression_stats

class ParallelExecutor:
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.execution_stats = {
            'total_executed': 0,
            'parallel_executed': 0,
            'avg_batch_time': 0
        }
    
    async def execute_parallel(self, tasks: List[Callable], *args, **kwargs) -> List[Any]:
        async def run_with_semaphore(task):
            async with self.semaphore:
                if asyncio.iscoroutinefunction(task):
                    return await task(*args, **kwargs)
                else:
                    return task(*args, **kwargs)
        
        start = time.time()
        results = await asyncio.gather(*[run_with_semaphore(t) for t in tasks])
        elapsed = time.time() - start
        
        self.execution_stats['total_executed'] += len(tasks)
        self.execution_stats['parallel_executed'] += len(tasks)
        
        # Update average
        total = self.execution_stats['total_executed']
        current_avg = self.execution_stats['avg_batch_time']
        self.execution_stats['avg_batch_time'] = ((current_avg * (total - len(tasks))) + elapsed) / total
        
        return results
    
    async def execute_tools_parallel(self, tool_calls: List[Dict]) -> List[Dict]:
        async def execute_single(call):
            async with self.semaphore:
                tool_name = call['name']
                args = call.get('args', {})
                
                # Simulate tool execution
                await asyncio.sleep(0.1)  # Simulated delay
                
                return {
                    'tool': tool_name,
                    'result': f"Executed {tool_name} with {args}",
                    'success': True
                }
        
        return await asyncio.gather(*[execute_single(call) for call in tool_calls])
    
    def get_stats(self) -> Dict:
        return self.execution_stats

class ModelRouter:
    MODELS = {
        'claude-3-opus-20240229': {'quality': 10, 'speed': 5, 'cost': 10},
        'claude-3-sonnet-20240229': {'quality': 8, 'speed': 8, 'cost': 5},
        'claude-3-haiku-20240307': {'quality': 6, 'speed': 10, 'cost': 1},
        'gpt-4o': {'quality': 9, 'speed': 7, 'cost': 8},
        'gpt-4o-mini': {'quality': 7, 'speed': 9, 'cost': 2},
    }
    
    def __init__(self):
        self.preferences = {
            'quality_weight': 0.4,
            'speed_weight': 0.3,
            'cost_weight': 0.3
        }
        self.usage_stats = defaultdict(lambda: {'calls': 0, 'avg_latency': 0})
    
    def select_model(self, task_description: str, priority: str = "balanced") -> str:
        # Adjust weights based on priority
        weights = dict(self.preferences)
        if priority == "quality":
            weights = {'quality_weight': 0.6, 'speed_weight': 0.2, 'cost_weight': 0.2}
        elif priority == "speed":
            weights = {'quality_weight': 0.2, 'speed_weight': 0.6, 'cost_weight': 0.2}
        elif priority == "cost":
            weights = {'quality_weight': 0.2, 'speed_weight': 0.2, 'cost_weight': 0.6}
        
        # Calculate scores
        scores = {}
        for model, stats in self.MODELS.items():
            score = (
                stats['quality'] * weights['quality_weight'] +
                stats['speed'] * weights['speed_weight'] +
                (11 - stats['cost']) * weights['cost_weight']  # Invert cost
            )
            scores[model] = score
        
        # Return best model
        return max(scores.items(), key=lambda x: x[1])[0]
    
    def record_usage(self, model: str, latency_ms: float):
        stats = self.usage_stats[model]
        stats['calls'] += 1
        # Update running average
        stats['avg_latency'] = (stats['avg_latency'] * (stats['calls'] - 1) + latency_ms) / stats['calls']
    
    def get_recommendations(self) -> Dict:
        recommendations = []
        
        for model, stats in self.usage_stats.items():
            if stats['calls'] > 10:
                expected = self.MODELS.get(model, {}).get('speed', 5) * 100
                if stats['avg_latency'] > expected * 1.5:
                    recommendations.append({
                        'model': model,
                        'issue': 'slower_than_expected',
                        'suggestion': 'Consider alternative for time-sensitive tasks'
                    })
        
        return {
            'model_stats': dict(self.usage_stats),
            'recommendations': recommendations
        }

class SmartRetry:
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, 
                 max_delay: float = 60.0, exponential_base: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.circuit_breakers: Dict[str, Dict] = {}
    
    def calculate_delay(self, attempt: int) -> float:
        delay = self.base_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)
    
    def is_circuit_open(self, key: str) -> bool:
        if key not in self.circuit_breakers:
            return False
        
        cb = self.circuit_breakers[key]
        if cb['failures'] >= 5:
            if time.time() - cb['last_failure'] < 300:  # 5 min timeout
                return True
            else:
                cb['failures'] = 0
        
        return False
    
    def record_failure(self, key: str):
        if key not in self.circuit_breakers:
            self.circuit_breakers[key] = {'failures': 0, 'last_failure': 0}
        
        self.circuit_breakers[key]['failures'] += 1
        self.circuit_breakers[key]['last_failure'] = time.time()
    
    def record_success(self, key: str):
        if key in self.circuit_breakers:
            self.circuit_breakers[key]['failures'] = max(0, self.circuit_breakers[key]['failures'] - 1)
    
    async def execute_with_retry(self, func: Callable, key: str = None, *args, **kwargs):
        key = key or func.__name__
        
        if self.is_circuit_open(key):
            raise Exception(f"Circuit breaker open for {key}")
        
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                self.record_success(key)
                return result
                
            except Exception as e:
                last_exception = e
                self.record_failure(key)
                
                if attempt < self.max_retries - 1:
                    delay = self.calculate_delay(attempt)
                    await asyncio.sleep(delay)
        
        raise last_exception

class HealthChecker:
    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.health_status: Dict[str, Dict] = {}
    
    def register_check(self, name: str, check_func: Callable):
        self.checks[name] = check_func
    
    async def run_checks(self) -> Dict:
        results = {}
        
        for name, check in self.checks.items():
            try:
                start = time.time()
                result = await check() if asyncio.iscoroutinefunction(check) else check()
                latency = time.time() - start
                
                results[name] = {
                    'status': 'healthy' if result else 'unhealthy',
                    'latency_ms': latency * 1000,
                    'timestamp': time.time()
                }
            except Exception as e:
                results[name] = {
                    'status': 'error',
                    'error': str(e),
                    'timestamp': time.time()
                }
        
        self.health_status = results
        return results
    
    def get_overall_status(self) -> str:
        if not self.health_status:
            return "unknown"
        
        unhealthy = [k for k, v in self.health_status.items() if v['status'] != 'healthy']
        
        if len(unhealthy) == 0:
            return "healthy"
        elif len(unhealthy) < len(self.health_status) / 2:
            return "degraded"
        else:
            return "unhealthy"

# Global instances
_tool_cache = ToolResultCache()
_prompt_cache = PromptCache()
_context_compressor = ContextCompressor()
_parallel_executor = ParallelExecutor()
_model_router = ModelRouter()
_smart_retry = SmartRetry()
_health_checker = HealthChecker()

def get_tool_cache() -> ToolResultCache:
    return _tool_cache

def get_prompt_cache() -> PromptCache:
    return _prompt_cache

def get_context_compressor() -> ContextCompressor:
    return _context_compressor

def get_parallel_executor() -> ParallelExecutor:
    return _parallel_executor

def get_model_router() -> ModelRouter:
    return _model_router

def get_smart_retry() -> SmartRetry:
    return _smart_retry

def get_health_checker() -> HealthChecker:
    return _health_checker
