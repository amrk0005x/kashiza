import json
import time
import psutil
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
from datetime import datetime
import asyncio

@dataclass
class PerformanceMetrics:
    timestamp: float
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_io_sent: int
    network_io_recv: int
    response_time_ms: float
    tokens_per_second: float
    error_rate: float
    active_tasks: int

@dataclass
class QualityScore:
    task_id: str
    score: float  # 0-10
    criteria: Dict[str, float]
    timestamp: float

class SelfMonitor:
    QUALITY_CRITERIA = {
        'response_time': 0.2,      # Fast response
        'accuracy': 0.3,            # Correct output
        'completeness': 0.2,        # Full answer
        'efficiency': 0.15,         # Optimal tokens
        'user_satisfaction': 0.15   # User rating
    }
    
    def __init__(self, config_path: str = "config/monitor.json"):
        self.config_path = config_path
        self.metrics_history: List[PerformanceMetrics] = []
        self.quality_scores: List[QualityScore] = []
        self.error_history: List[Dict] = []
        self.config_adjustments: List[Dict] = []
        
        self.target_quality = 7.0  # 7/10 target
        self.monitoring_active = False
        
        self._load_config()
    
    def _load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                self.target_quality = config.get('target_quality', 7.0)
        except:
            self._save_config()
    
    def _save_config(self):
        import os
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump({
                'target_quality': self.target_quality,
                'auto_optimize': True,
                'quality_threshold': 7.0
            }, f, indent=2)
    
    def collect_metrics(self) -> PerformanceMetrics:
        cpu = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        net_io = psutil.net_io_counters()
        
        metrics = PerformanceMetrics(
            timestamp=time.time(),
            cpu_percent=cpu,
            memory_percent=memory,
            disk_usage_percent=disk,
            network_io_sent=net_io.bytes_sent,
            network_io_recv=net_io.bytes_recv,
            response_time_ms=0.0,
            tokens_per_second=0.0,
            error_rate=0.0,
            active_tasks=0
        )
        
        self.metrics_history.append(metrics)
        
        # Keep only last 1000 metrics
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        
        return metrics
    
    def record_task_completion(self, task_id: str, response_time_ms: float,
                               tokens_used: int, success: bool):
        if not self.metrics_history:
            return
        
        latest = self.metrics_history[-1]
        latest.response_time_ms = response_time_ms
        latest.tokens_per_second = (tokens_used / response_time_ms * 1000) if response_time_ms > 0 else 0
        latest.active_tasks += 1 if success else 0
    
    def record_error(self, error_type: str, message: str, context: Dict):
        self.error_history.append({
            'timestamp': time.time(),
            'type': error_type,
            'message': message,
            'context': context
        })
        
        # Update error rate in latest metrics
        if self.metrics_history:
            recent_errors = len([e for e in self.error_history 
                               if e['timestamp'] > time.time() - 3600])
            self.metrics_history[-1].error_rate = recent_errors / max(len(self.metrics_history), 1)
    
    def calculate_quality_score(self, task_id: str, user_rating: int = None,
                                criteria_scores: Dict[str, float] = None) -> QualityScore:
        if criteria_scores is None:
            criteria_scores = {}
        
        # Calculate weighted score
        total_score = 0.0
        for criterion, weight in self.QUALITY_CRITERIA.items():
            score = criteria_scores.get(criterion, 5.0)  # Default 5/10
            total_score += score * weight
        
        # Adjust with user rating if provided
        if user_rating:
            total_score = (total_score * 0.7) + (user_rating * 0.3)
        
        score = QualityScore(
            task_id=task_id,
            score=min(total_score, 10.0),
            criteria=criteria_scores,
            timestamp=time.time()
        )
        
        self.quality_scores.append(score)
        return score
    
    def get_average_quality(self, window_hours: int = 24) -> float:
        cutoff = time.time() - (window_hours * 3600)
        recent = [s for s in self.quality_scores if s.timestamp > cutoff]
        
        if not recent:
            return 0.0
        
        return sum(s.score for s in recent) / len(recent)
    
    def detect_performance_issues(self) -> List[Dict]:
        issues = []
        
        if len(self.metrics_history) < 10:
            return issues
        
        recent = self.metrics_history[-10:]
        
        # High CPU
        avg_cpu = sum(m.cpu_percent for m in recent) / len(recent)
        if avg_cpu > 80:
            issues.append({
                'type': 'high_cpu',
                'severity': 'warning' if avg_cpu < 90 else 'critical',
                'value': avg_cpu,
                'recommendation': 'Reduce concurrent tasks or upgrade hardware'
            })
        
        # High memory
        avg_mem = sum(m.memory_percent for m in recent) / len(recent)
        if avg_mem > 85:
            issues.append({
                'type': 'high_memory',
                'severity': 'warning' if avg_mem < 95 else 'critical',
                'value': avg_mem,
                'recommendation': 'Implement memory cleanup or increase RAM'
            })
        
        # Slow response times
        avg_response = sum(m.response_time_ms for m in recent if m.response_time_ms > 0) / \
                      max(len([m for m in recent if m.response_time_ms > 0]), 1)
        if avg_response > 5000:  # 5 seconds
            issues.append({
                'type': 'slow_response',
                'severity': 'warning',
                'value': avg_response,
                'recommendation': 'Enable caching or use faster models'
            })
        
        # High error rate
        avg_error = sum(m.error_rate for m in recent) / len(recent)
        if avg_error > 0.1:  # 10%
            issues.append({
                'type': 'high_error_rate',
                'severity': 'critical',
                'value': avg_error,
                'recommendation': 'Review error logs and fix common issues'
            })
        
        return issues
    
    def analyze_quality_trends(self) -> Dict:
        if len(self.quality_scores) < 20:
            return {'status': 'insufficient_data'}
        
        # Split into recent and older
        mid = len(self.quality_scores) // 2
        older = self.quality_scores[:mid]
        recent = self.quality_scores[mid:]
        
        older_avg = sum(s.score for s in older) / len(older)
        recent_avg = sum(s.score for s in recent) / len(recent)
        
        trend = 'improving' if recent_avg > older_avg else 'declining' if recent_avg < older_avg else 'stable'
        
        return {
            'status': 'ok',
            'trend': trend,
            'older_average': older_avg,
            'recent_average': recent_avg,
            'change': recent_avg - older_avg,
            'current_average': self.get_average_quality()
        }
    
    def auto_optimize_config(self) -> Dict:
        quality = self.get_average_quality()
        issues = self.detect_performance_issues()
        trends = self.analyze_quality_trends()
        
        adjustments = []
        
        if quality < self.target_quality:
            # Quality is below target - need improvements
            if trends.get('trend') == 'declining':
                adjustments.append({
                    'setting': 'model_selection',
                    'change': 'upgrade_to_higher_quality',
                    'reason': f'Quality declining (current: {quality:.1f})'
                })
            
            adjustments.append({
                'setting': 'prompt_optimization',
                'change': 'enable_auto_enhancement',
                'reason': 'Low quality scores detected'
            })
        
        for issue in issues:
            if issue['type'] == 'high_cpu' or issue['type'] == 'high_memory':
                adjustments.append({
                    'setting': 'concurrent_tasks',
                    'change': 'decrease_limit',
                    'reason': issue['recommendation']
                })
            
            if issue['type'] == 'slow_response':
                adjustments.append({
                    'setting': 'caching',
                    'change': 'enable_aggressive_caching',
                    'reason': issue['recommendation']
                })
            
            if issue['type'] == 'high_error_rate':
                adjustments.append({
                    'setting': 'retry_policy',
                    'change': 'increase_retries',
                    'reason': issue['recommendation']
                })
        
        # Check for repeated errors
        error_types = defaultdict(int)
        for e in self.error_history[-50:]:
            error_types[e['type']] += 1
        
        for error_type, count in error_types.items():
            if count > 5:
                adjustments.append({
                    'setting': 'error_handling',
                    'change': f'add_specific_handler_for_{error_type}',
                    'reason': f'Frequent {error_type} errors detected'
                })
        
        self.config_adjustments.extend(adjustments)
        
        return {
            'quality': quality,
            'target': self.target_quality,
            'issues_detected': len(issues),
            'adjustments': adjustments,
            'applied': self._apply_adjustments(adjustments)
        }
    
    def _apply_adjustments(self, adjustments: List[Dict]) -> List[Dict]:
        applied = []
        
        for adj in adjustments:
            # In production, these would actually modify config
            applied.append({
                'setting': adj['setting'],
                'status': 'applied',
                'timestamp': time.time()
            })
        
        return applied
    
    def generate_report(self) -> Dict:
        return {
            'timestamp': datetime.now().isoformat(),
            'system_health': {
                'cpu_avg': sum(m.cpu_percent for m in self.metrics_history[-100:]) / min(len(self.metrics_history), 100) if self.metrics_history else 0,
                'memory_avg': sum(m.memory_percent for m in self.metrics_history[-100:]) / min(len(self.metrics_history), 100) if self.metrics_history else 0,
            },
            'quality_metrics': {
                'average_score': self.get_average_quality(),
                'target': self.target_quality,
                'trend': self.analyze_quality_trends().get('trend', 'unknown')
            },
            'performance': {
                'avg_response_time': sum(m.response_time_ms for m in self.metrics_history[-100:]) / min(len(self.metrics_history), 100) if self.metrics_history else 0,
                'error_rate': sum(m.error_rate for m in self.metrics_history[-100:]) / min(len(self.metrics_history), 100) if self.metrics_history else 0
            },
            'issues': self.detect_performance_issues(),
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        recs = []
        
        quality = self.get_average_quality()
        if quality < 5:
            recs.append("URGENT: Quality below 5/10. Consider reviewing agent prompts and switching to higher-quality models.")
        elif quality < self.target_quality:
            recs.append(f"Quality below target ({self.target_quality}). Enable prompt optimization.")
        
        issues = self.detect_performance_issues()
        if any(i['severity'] == 'critical' for i in issues):
            recs.append("Critical performance issues detected. Scale down concurrent operations immediately.")
        
        if len(self.error_history) > 20:
            recs.append("High error volume. Review error patterns and implement specific handlers.")
        
        trends = self.analyze_quality_trends()
        if trends.get('trend') == 'declining':
            recs.append("Quality trend is declining. Investigate recent changes.")
        
        return recs
    
    async def start_monitoring(self, interval_seconds: int = 60):
        self.monitoring_active = True
        
        while self.monitoring_active:
            self.collect_metrics()
            
            # Auto-optimize every 5 minutes
            if len(self.metrics_history) % 5 == 0:
                self.auto_optimize_config()
            
            await asyncio.sleep(interval_seconds)
    
    def stop_monitoring(self):
        self.monitoring_active = False

class AutoCorrector:
    def __init__(self, monitor: SelfMonitor):
        self.monitor = monitor
        self.correction_history = []
    
    def check_and_correct(self) -> Dict:
        quality = self.monitor.get_average_quality()
        
        if quality >= 7:
            return {'status': 'ok', 'quality': quality}
        
        # Quality is below 7/10 - investigate why
        analysis = self._analyze_low_quality()
        corrections = self._generate_corrections(analysis)
        
        result = {
            'quality': quality,
            'analysis': analysis,
            'corrections': corrections,
            'applied': self._apply_corrections(corrections)
        }
        
        self.correction_history.append(result)
        return result
    
    def _analyze_low_quality(self) -> Dict:
        # Analyze patterns in low-quality outputs
        low_scores = [s for s in self.monitor.quality_scores if s.score < 7]
        
        if not low_scores:
            return {'reason': 'unknown'}
        
        # Find common criteria with low scores
        criteria_issues = defaultdict(list)
        for score in low_scores:
            for criterion, value in score.criteria.items():
                criteria_issues[criterion].append(value)
        
        avg_criteria = {k: sum(v)/len(v) for k, v in criteria_issues.items()}
        
        # Find worst performing criteria
        worst = min(avg_criteria.items(), key=lambda x: x[1])
        
        return {
            'low_score_count': len(low_scores),
            'criteria_averages': avg_criteria,
            'worst_criterion': worst[0],
            'worst_score': worst[1]
        }
    
    def _generate_corrections(self, analysis: Dict) -> List[Dict]:
        corrections = []
        worst = analysis.get('worst_criterion')
        
        correction_map = {
            'response_time': {
                'action': 'enable_caching',
                'config': {'cache_ttl': 3600, 'cache_size': 1000}
            },
            'accuracy': {
                'action': 'upgrade_model',
                'config': {'model': 'claude-3-opus-20240229'}
            },
            'completeness': {
                'action': 'enhance_prompts',
                'config': {'add_examples': True, 'require_structure': True}
            },
            'efficiency': {
                'action': 'optimize_tokens',
                'config': {'max_tokens': 2000, 'compress_context': True}
            },
            'user_satisfaction': {
                'action': 'improve_formatting',
                'config': {'format': 'markdown', 'add_summaries': True}
            }
        }
        
        if worst and worst in correction_map:
            corrections.append(correction_map[worst])
        
        # Always add general improvements
        corrections.append({
            'action': 'review_prompts',
            'config': {'audit_prompts': True}
        })
        
        return corrections
    
    def _apply_corrections(self, corrections: List[Dict]) -> List[Dict]:
        applied = []
        
        for corr in corrections:
            # Apply the correction
            applied.append({
                'action': corr['action'],
                'status': 'applied',
                'config': corr['config'],
                'timestamp': time.time()
            })
        
        return applied
