import json
import time
import hashlib
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict
import random

@dataclass
class Variant:
    id: str
    name: str
    prompt_template: str
    metadata: Dict
    
@dataclass
class TestResult:
    variant_id: str
    test_id: str
    input: str
    output: str
    latency_ms: float
    token_count: int
    success: bool
    quality_score: float
    timestamp: float

class ABTester:
    def __init__(self, storage_path: str = "config/ab_tests.json"):
        self.storage_path = storage_path
        self.active_tests: Dict[str, Dict] = {}
        self.results: Dict[str, List[TestResult]] = defaultdict(list)
        self.variants: Dict[str, Variant] = {}
        self._load_data()
    
    def _load_data(self):
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                self.active_tests = data.get('tests', {})
                for vid, vdata in data.get('variants', {}).items():
                    self.variants[vid] = Variant(**vdata)
        except:
            pass
    
    def _save_data(self):
        import os
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, 'w') as f:
            json.dump({
                'tests': self.active_tests,
                'variants': {vid: asdict(v) for vid, v in self.variants.items()},
                'results': {tid: [asdict(r) for r in res] for tid, res in self.results.items()}
            }, f, indent=2)
    
    def create_variant(self, name: str, prompt_template: str, metadata: Dict = None) -> str:
        vid = hashlib.md5(f"{name}{time.time()}".encode()).hexdigest()[:8]
        self.variants[vid] = Variant(
            id=vid,
            name=name,
            prompt_template=prompt_template,
            metadata=metadata or {}
        )
        self._save_data()
        return vid
    
    def create_test(self, name: str, variant_ids: List[str], 
                    traffic_split: List[float] = None) -> str:
        if traffic_split is None:
            traffic_split = [1.0 / len(variant_ids)] * len(variant_ids)
        
        test_id = hashlib.md5(f"{name}{time.time()}".encode()).hexdigest()[:8]
        
        self.active_tests[test_id] = {
            'name': name,
            'variant_ids': variant_ids,
            'traffic_split': traffic_split,
            'created_at': time.time(),
            'status': 'running',
            'total_runs': 0
        }
        
        self._save_data()
        return test_id
    
    def get_variant_for_request(self, test_id: str) -> Optional[Variant]:
        test = self.active_tests.get(test_id)
        if not test or test['status'] != 'running':
            return None
        
        # Weighted random selection
        splits = test['traffic_split']
        variants = test['variant_ids']
        
        r = random.random()
        cumulative = 0
        for i, split in enumerate(splits):
            cumulative += split
            if r <= cumulative:
                return self.variants.get(variants[i])
        
        return self.variants.get(variants[-1])
    
    async def run_test(self, test_id: str, inputs: List[str], 
                       agent_executor: Callable) -> Dict:
        test = self.active_tests.get(test_id)
        if not test:
            return {'error': 'Test not found'}
        
        results = []
        for inp in inputs:
            variant = self.get_variant_for_request(test_id)
            if not variant:
                continue
            
            start = time.time()
            prompt = variant.prompt_template.replace("{{input}}", inp)
            
            try:
                output = await agent_executor(prompt)
                latency = (time.time() - start) * 1000
                
                result = TestResult(
                    variant_id=variant.id,
                    test_id=test_id,
                    input=inp,
                    output=output,
                    latency_ms=latency,
                    token_count=len(output.split()),
                    success=True,
                    quality_score=0.0,
                    timestamp=time.time()
                )
                
                self.results[test_id].append(result)
                results.append(result)
                
            except Exception as e:
                results.append(TestResult(
                    variant_id=variant.id,
                    test_id=test_id,
                    input=inp,
                    output=str(e),
                    latency_ms=0,
                    token_count=0,
                    success=False,
                    quality_score=0.0,
                    timestamp=time.time()
                ))
        
        test['total_runs'] += len(inputs)
        self._save_data()
        
        return {'test_id': test_id, 'runs': len(results), 'results': results}
    
    def get_test_stats(self, test_id: str) -> Dict:
        results = self.results.get(test_id, [])
        if not results:
            return {'error': 'No results for this test'}
        
        by_variant = defaultdict(lambda: {
            'runs': 0,
            'success_rate': 0,
            'avg_latency': 0,
            'avg_tokens': 0
        })
        
        for r in results:
            v = by_variant[r.variant_id]
            v['runs'] += 1
            v['success_rate'] += 1 if r.success else 0
            v['avg_latency'] += r.latency_ms
            v['avg_tokens'] += r.token_count
        
        for vid, stats in by_variant.items():
            if stats['runs'] > 0:
                stats['success_rate'] /= stats['runs']
                stats['avg_latency'] /= stats['runs']
                stats['avg_tokens'] /= stats['runs']
        
        # Statistical significance
        winner = self._determine_winner(by_variant)
        
        return {
            'test_id': test_id,
            'total_runs': len(results),
            'by_variant': dict(by_variant),
            'winner': winner,
            'confidence': self._calculate_confidence(by_variant)
        }
    
    def _determine_winner(self, by_variant: Dict) -> Optional[str]:
        if not by_variant:
            return None
        
        # Score based on success rate and latency
        scores = {}
        for vid, stats in by_variant.items():
            if stats['runs'] < 10:
                continue
            score = (stats['success_rate'] * 0.6) + (1 / (1 + stats['avg_latency']/1000) * 0.4)
            scores[vid] = score
        
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        return None
    
    def _calculate_confidence(self, by_variant: Dict) -> float:
        # Simplified confidence calculation
        runs = sum(v['runs'] for v in by_variant.values())
        if runs < 30:
            return min(runs / 30 * 100, 95)
        return 95.0
    
    def declare_winner(self, test_id: str, variant_id: str):
        test = self.active_tests.get(test_id)
        if test:
            test['status'] = 'completed'
            test['winner'] = variant_id
            test['completed_at'] = time.time()
            self._save_data()
    
    def auto_optimize(self, test_id: str, threshold: float = 0.95):
        stats = self.get_test_stats(test_id)
        if stats.get('confidence', 0) >= threshold * 100:
            winner = stats.get('winner')
            if winner:
                self.declare_winner(test_id, winner)
                return {'action': 'winner_declared', 'winner': winner}
        
        return {'action': 'continue_testing', 'confidence': stats.get('confidence', 0)}

# Built-in prompt tests
BUILT_IN_TESTS = {
    'code_generation': {
        'variants': [
            ('direct', 'Write code to: {{input}}'),
            ('with_examples', 'Write code with examples to: {{input}}\n\nExample format:\n```python\n# code here\n```'),
            ('step_by_step', 'Break down and write code for: {{input}}\n\nSteps:\n1. Understand requirements\n2. Plan solution\n3. Implement\n4. Review')
        ]
    },
    'code_review': {
        'variants': [
            ('direct', 'Review this code:\n{{input}}'),
            ('structured', 'Review this code with structure:\n{{input}}\n\nFormat:\n- Issues: \n- Suggestions: \n- Security: \n- Performance:'),
            ('gentle', 'Please review this code constructively:\n{{input}}\n\nFocus on improvements while highlighting good practices.')
        ]
    }
}
