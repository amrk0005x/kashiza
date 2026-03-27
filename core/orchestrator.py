import asyncio
import json
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import time
from collections import defaultdict

class ExecutionMode(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    COLLABORATIVE = "collaborative"
    HIERARCHICAL = "hierarchical"
    AUTO = "auto"

@dataclass
class AgentProfile:
    id: str
    name: str
    description: str
    skills: List[str]
    specialty: str
    model: str = "claude-3-opus-20240229"
    cost_per_1k_tokens: float = 0.015
    success_rate: float = 0.95
    avg_response_time: float = 2.0
    metadata: Dict = field(default_factory=dict)

@dataclass
class TaskResult:
    agent_id: str
    task_id: str
    success: bool
    output: str
    execution_time: float
    tokens_used: int
    cost: float
    quality_score: float
    feedback: Dict = field(default_factory=dict)

class AgentRegistry:
    def __init__(self):
        self.agents: Dict[str, AgentProfile] = {}
        self._provider_manager = None
        self._load_default_agents()
    
    def _get_provider_manager(self):
        if self._provider_manager is None:
            try:
                from core.providers import get_provider_manager
                self._provider_manager = get_provider_manager()
            except ImportError:
                pass
        return self._provider_manager
    
    def _get_model_info(self, model_id: str):
        """Get model info from provider manager"""
        pm = self._get_provider_manager()
        if pm:
            return pm.get_model(model_id)
        return None
    
    def _get_model_cost(self, model_id: str) -> float:
        """Get cost per 1k tokens for a model"""
        model = self._get_model_info(model_id)
        if model:
            return model.input_price
        # Fallback costs
        fallback = {
            "claude-3-opus-20240229": 0.015,
            "claude-3-sonnet-20240229": 0.003,
            "claude-3-haiku-20240307": 0.00025,
            "claude-3-5-sonnet-20241022": 0.003,
            "gpt-4o": 0.005,
            "gpt-4o-mini": 0.00015,
            "gemini-1.5-pro": 0.0035,
            "gemini-1.5-flash": 0.00035,
        }
        return fallback.get(model_id, 0.01)
    
    def _load_default_agents(self):
        """Load default agents with dynamic model selection"""
        pm = self._get_provider_manager()
        
        # Select best available models
        def select_model(preferences):
            if pm:
                for pref in preferences:
                    if pm.is_model_available(pref):
                        return pref
            return preferences[-1]  # Fallback to last option
        
        defaults = [
            AgentProfile(
                id="coder",
                name="Senior Developer",
                description="Expert en développement logiciel, architecture et code review",
                skills=["python", "javascript", "rust", "architecture", "review"],
                specialty="coding",
                model=select_model(["claude-3-opus-20240229", "gpt-4o", "deepseek-coder", "kimi-k2-5"]),
                cost_per_1k_tokens=self._get_model_cost(select_model(["claude-3-opus-20240229", "gpt-4o", "deepseek-coder", "kimi-k2-5"]))
            ),
            AgentProfile(
                id="architect",
                name="System Architect",
                description="Conception d'architecture système, patterns et scalabilité",
                skills=["architecture", "system_design", "patterns", "scalability"],
                specialty="architecture",
                model=select_model(["claude-3-opus-20240229", "claude-3-5-sonnet-20241022", "gpt-4o", "kimi-k2-5"]),
                cost_per_1k_tokens=self._get_model_cost(select_model(["claude-3-opus-20240229", "claude-3-5-sonnet-20241022", "gpt-4o", "kimi-k2-5"]))
            ),
            AgentProfile(
                id="reviewer",
                name="Code Reviewer",
                description="Revue de code, sécurité et best practices",
                skills=["security", "review", "testing", "best_practices"],
                specialty="review",
                model=select_model(["claude-3-sonnet-20240229", "gpt-4o-mini", "gemini-1.5-flash", "deepseek-coder"]),
                cost_per_1k_tokens=self._get_model_cost(select_model(["claude-3-sonnet-20240229", "gpt-4o-mini", "gemini-1.5-flash", "deepseek-coder"]))
            ),
            AgentProfile(
                id="devops",
                name="DevOps Engineer",
                description="CI/CD, Docker, Kubernetes, infrastructure",
                skills=["docker", "kubernetes", "cicd", "terraform", "aws"],
                specialty="devops",
                model=select_model(["claude-3-sonnet-20240229", "gpt-4o-mini", "gemini-1.5-flash", "deepseek-chat"]),
                cost_per_1k_tokens=self._get_model_cost(select_model(["claude-3-sonnet-20240229", "gpt-4o-mini", "gemini-1.5-flash", "deepseek-chat"]))
            ),
            AgentProfile(
                id="data_scientist",
                name="Data Scientist",
                description="ML, data analysis, visualisation",
                skills=["python", "ml", "pandas", "visualization", "statistics"],
                specialty="data_science",
                model=select_model(["claude-3-opus-20240229", "gpt-4o", "kimi-k2-5", "deepseek-chat"]),
                cost_per_1k_tokens=self._get_model_cost(select_model(["claude-3-opus-20240229", "gpt-4o", "kimi-k2-5", "deepseek-chat"]))
            ),
            AgentProfile(
                id="security",
                name="Security Expert",
                description="Sécurité, audit, vulnérabilités",
                skills=["security", "audit", "penetration_testing", "compliance"],
                specialty="security",
                model=select_model(["claude-3-opus-20240229", "gpt-4o", "kimi-k2-5", "deepseek-reasoner"]),
                cost_per_1k_tokens=self._get_model_cost(select_model(["claude-3-opus-20240229", "gpt-4o", "kimi-k2-5", "deepseek-reasoner"]))
            ),
            AgentProfile(
                id="ux",
                name="UX Designer",
                description="UI/UX, design systems, accessibility",
                skills=["ui", "ux", "design_systems", "accessibility", "figma"],
                specialty="design",
                model=select_model(["claude-3-sonnet-20240229", "gpt-4o", "gemini-1.5-pro"]),
                cost_per_1k_tokens=self._get_model_cost(select_model(["claude-3-sonnet-20240229", "gpt-4o", "gemini-1.5-pro"]))
            ),
            AgentProfile(
                id="product",
                name="Product Manager",
                description="Product strategy, roadmap, user stories",
                skills=["product", "strategy", "roadmap", "agile", "analytics"],
                specialty="product",
                model=select_model(["claude-3-sonnet-20240229", "gpt-4o-mini", "gemini-1.5-flash"]),
                cost_per_1k_tokens=self._get_model_cost(select_model(["claude-3-sonnet-20240229", "gpt-4o-mini", "gemini-1.5-flash"]))
            ),
            AgentProfile(
                id="fast_coder",
                name="Fast Coder",
                description="Développement rapide, tâches simples",
                skills=["python", "javascript", "quick_fixes"],
                specialty="quick_tasks",
                model=select_model(["claude-3-haiku-20240307", "gpt-4o-mini", "gemini-1.5-flash", "deepseek-chat", "llama3.2"]),
                cost_per_1k_tokens=self._get_model_cost(select_model(["claude-3-haiku-20240307", "gpt-4o-mini", "gemini-1.5-flash", "deepseek-chat", "llama3.2"]))
            ),
            AgentProfile(
                id="debugger",
                name="Debug Specialist",
                description="Débogage, troubleshooting, logs analysis",
                skills=["debugging", "logs", "profiling", "monitoring"],
                specialty="debugging",
                model=select_model(["claude-3-opus-20240229", "claude-3-5-sonnet-20241022", "kimi-k2-5", "deepseek-reasoner"]),
                cost_per_1k_tokens=self._get_model_cost(select_model(["claude-3-opus-20240229", "claude-3-5-sonnet-20241022", "kimi-k2-5", "deepseek-reasoner"]))
            ),
            # New specialized agents for new providers
            AgentProfile(
                id="local_expert",
                name="Local Model Expert",
                description="Expert using local Ollama models for privacy-sensitive tasks",
                skills=["privacy", "local", "offline", "security"],
                specialty="privacy",
                model=select_model(["llama3.2", "qwen2.5-coder", "mistral", "phi4"]),
                cost_per_1k_tokens=0.0
            ),
            AgentProfile(
                id="kimi_specialist",
                name="Kimi Specialist",
                description="Specialized in Kimi models for complex reasoning",
                skills=["reasoning", "analysis", "complex_tasks"],
                specialty="reasoning",
                model=select_model(["kimi-k2-5", "kimi-k1-6"]),
                cost_per_1k_tokens=self._get_model_cost(select_model(["kimi-k2-5", "kimi-k1-6"]))
            ),
            AgentProfile(
                id="deepseek_specialist",
                name="DeepSeek Specialist",
                description="Optimized for coding with DeepSeek models",
                skills=["coding", "optimization", "algorithms"],
                specialty="coding",
                model=select_model(["deepseek-coder", "deepseek-reasoner", "deepseek-chat"]),
                cost_per_1k_tokens=self._get_model_cost(select_model(["deepseek-coder", "deepseek-reasoner", "deepseek-chat"]))
            ),
        ]
        for agent in defaults:
            self.agents[agent.id] = agent
    
    def register(self, agent: AgentProfile):
        self.agents[agent.id] = agent
    
    def get(self, agent_id: str) -> Optional[AgentProfile]:
        return self.agents.get(agent_id)
    
    def list_all(self) -> List[AgentProfile]:
        return list(self.agents.values())
    
    def find_by_specialty(self, specialty: str) -> List[AgentProfile]:
        return [a for a in self.agents.values() if a.specialty == specialty]

class PromptAnalyzer:
    KEYWORD_MAPPING = {
        "coding": ["code", "develop", "implement", "function", "class", "api", "backend", "frontend", "bug", "fix"],
        "architecture": ["architecture", "design", "structure", "pattern", "scalability", "microservice", "monolith"],
        "review": ["review", "audit", "check", "analyze code", "improve"],
        "devops": ["docker", "kubernetes", "deploy", "ci/cd", "pipeline", "infrastructure", "terraform"],
        "data_science": ["ml", "machine learning", "data", "analysis", "model", "train", "pandas", "visualization"],
        "security": ["security", "vulnerability", "auth", "encryption", "penetration", "audit"],
        "design": ["ui", "ux", "design", "interface", "user experience", "mockup", "figma"],
        "product": ["product", "feature", "roadmap", "user story", "requirement", "strategy"],
        "debugging": ["debug", "error", "exception", "crash", "log", "traceback", "profiling"],
        "quick_tasks": ["quick", "simple", "fast", "small", "minor", "rename", "refactor small"]
    }
    
    COMPLEXITY_INDICATORS = {
        "high": ["complex", "architecture", "system", "scalable", "distributed", "microservice"],
        "medium": ["feature", "implement", "develop", "api", "integration"],
        "low": ["fix", "bug", "quick", "simple", "rename", "small"]
    }
    
    def analyze(self, prompt: str) -> Dict[str, Any]:
        prompt_lower = prompt.lower()
        scores = defaultdict(float)
        
        for specialty, keywords in self.KEYWORD_MAPPING.items():
            for keyword in keywords:
                if keyword in prompt_lower:
                    scores[specialty] += 1.0
        
        complexity = self._detect_complexity(prompt_lower)
        urgency = self._detect_urgency(prompt_lower)
        
        best_specialties = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "specialties": best_specialties,
            "complexity": complexity,
            "urgency": urgency,
            "estimated_tokens": self._estimate_tokens(prompt),
            "requires_multiple_agents": complexity == "high" or len(best_specialties) > 1
        }
    
    def _detect_complexity(self, prompt: str) -> str:
        high_score = sum(1 for w in self.COMPLEXITY_INDICATORS["high"] if w in prompt)
        medium_score = sum(1 for w in self.COMPLEXITY_INDICATORS["medium"] if w in prompt)
        low_score = sum(1 for w in self.COMPLEXITY_INDICATORS["low"] if w in prompt)
        
        if high_score > 0:
            return "high"
        elif low_score > 0:
            return "low"
        return "medium"
    
    def _detect_urgency(self, prompt: str) -> str:
        urgent = ["urgent", "asap", "quick", "fast", "immediate", "critical"]
        if any(w in prompt for w in urgent):
            return "high"
        return "normal"
    
    def _estimate_tokens(self, prompt: str) -> int:
        return len(prompt.split()) * 1.3

class SmartOrchestrator:
    def __init__(self, kashiza_path: str = ""):
        self.registry = AgentRegistry()
        self.analyzer = PromptAnalyzer()
        self.kashiza_path = kashiza_path
        self.execution_history: List[TaskResult] = []
        self.feedback_db: Dict[str, List[Dict]] = defaultdict(list)
        self.cost_tracker = None
        self.debugger = None
    
    def set_cost_tracker(self, tracker):
        self.cost_tracker = tracker
    
    def set_debugger(self, debugger):
        self.debugger = debugger
    
    def select_agents(self, prompt: str, mode: ExecutionMode = ExecutionMode.AUTO) -> List[AgentProfile]:
        analysis = self.analyzer.analyze(prompt)
        
        if mode == ExecutionMode.AUTO:
            mode = self._determine_mode(analysis)
        
        selected = []
        
        if mode == ExecutionMode.HIERARCHICAL:
            selected = self._select_hierarchical(analysis)
        elif mode == ExecutionMode.COLLABORATIVE:
            selected = self._select_collaborative(analysis)
        elif mode == ExecutionMode.PARALLEL:
            selected = self._select_parallel(analysis)
        else:
            selected = self._select_sequential(analysis)
        
        # Budget optimization
        if self.cost_tracker:
            remaining_budget = self.cost_tracker.get_remaining_budget()
            estimated_cost = sum(a.cost_per_1k_tokens * analysis["estimated_tokens"] / 1000 
                               for a in selected)
            
            if estimated_cost > remaining_budget * 0.5:
                selected = self._optimize_for_budget(selected, analysis, remaining_budget)
        
        return selected
    
    def _determine_mode(self, analysis: Dict) -> ExecutionMode:
        if analysis["requires_multiple_agents"]:
            if analysis["complexity"] == "high":
                return ExecutionMode.HIERARCHICAL
            return ExecutionMode.COLLABORATIVE
        elif analysis["complexity"] == "low":
            return ExecutionMode.SEQUENTIAL
        return ExecutionMode.PARALLEL
    
    def _select_hierarchical(self, analysis: Dict) -> List[AgentProfile]:
        agents = []
        if analysis["specialties"]:
            primary = self.registry.find_by_specialty(analysis["specialties"][0][0])
            if primary:
                agents.append(primary[0])
        
        if "architecture" not in [s[0] for s in analysis["specialties"]]:
            arch = self.registry.get("architect")
            if arch:
                agents.insert(0, arch)
        
        reviewer = self.registry.get("reviewer")
        if reviewer:
            agents.append(reviewer)
        
        return agents[:3]
    
    def _select_collaborative(self, analysis: Dict) -> List[AgentProfile]:
        agents = []
        for specialty, score in analysis["specialties"][:3]:
            matches = self.registry.find_by_specialty(specialty)
            if matches:
                agents.append(matches[0])
        
        if len(agents) < 2:
            coder = self.registry.get("coder")
            if coder and coder not in agents:
                agents.append(coder)
        
        return agents[:3]
    
    def _select_parallel(self, analysis: Dict) -> List[AgentProfile]:
        agents = []
        for specialty, score in analysis["specialties"][:2]:
            matches = self.registry.find_by_specialty(specialty)
            if matches:
                agents.append(matches[0])
        
        if not agents:
            agents = [self.registry.get("coder")]
        
        return agents
    
    def _select_sequential(self, analysis: Dict) -> List[AgentProfile]:
        if analysis["urgency"] == "high" and analysis["complexity"] == "low":
            fast = self.registry.get("fast_coder")
            if fast:
                return [fast]
        
        if analysis["specialties"]:
            specialty = analysis["specialties"][0][0]
            matches = self.registry.find_by_specialty(specialty)
            if matches:
                return [matches[0]]
        
        return [self.registry.get("coder")]
    
    def _optimize_for_budget(self, agents: List[AgentProfile], analysis: Dict, budget: float) -> List[AgentProfile]:
        if analysis["complexity"] == "low":
            fast = self.registry.get("fast_coder")
            if fast:
                return [fast]
        
        cheaper = []
        for agent in agents:
            if agent.cost_per_1k_tokens < 0.005:
                cheaper.append(agent)
        
        if not cheaper:
            sonnet = self.registry.get("reviewer")
            if sonnet:
                return [sonnet]
        
        return cheaper if cheaper else agents[:1]
    
    async def execute_task(self, prompt: str, agents: List[AgentProfile] = None, 
                          mode: ExecutionMode = ExecutionMode.AUTO,
                          context: Dict = None) -> List[TaskResult]:
        if agents is None:
            agents = self.select_agents(prompt, mode)
        
        context = context or {}
        task_id = hashlib.md5(f"{prompt}{time.time()}".encode()).hexdigest()[:8]
        
        results = []
        
        if mode in [ExecutionMode.SEQUENTIAL, ExecutionMode.AUTO]:
            results = await self._execute_sequential(prompt, agents, task_id, context)
        elif mode == ExecutionMode.PARALLEL:
            results = await self._execute_parallel(prompt, agents, task_id, context)
        elif mode == ExecutionMode.COLLABORATIVE:
            results = await self._execute_collaborative(prompt, agents, task_id, context)
        elif mode == ExecutionMode.HIERARCHICAL:
            results = await self._execute_hierarchical(prompt, agents, task_id, context)
        
        self.execution_history.extend(results)
        
        if self.cost_tracker:
            for r in results:
                self.cost_tracker.add_cost(r.cost)
        
        return results
    
    async def _execute_sequential(self, prompt: str, agents: List[AgentProfile], 
                                   task_id: str, context: Dict) -> List[TaskResult]:
        results = []
        current_prompt = prompt
        
        for i, agent in enumerate(agents):
            start = time.time()
            
            enriched_prompt = self._enrich_prompt(current_prompt, agent, context, results)
            
            output = await self._call_kashiza(enriched_prompt, agent)
            
            exec_time = time.time() - start
            tokens = len(output.split()) * 1.5
            cost = (tokens / 1000) * agent.cost_per_1k_tokens
            
            result = TaskResult(
                agent_id=agent.id,
                task_id=f"{task_id}_{i}",
                success=True,
                output=output,
                execution_time=exec_time,
                tokens_used=int(tokens),
                cost=cost,
                quality_score=0.0
            )
            
            results.append(result)
            current_prompt = f"{prompt}\n\nPrevious output:\n{output}"
        
        return results
    
    async def _execute_parallel(self, prompt: str, agents: List[AgentProfile],
                                 task_id: str, context: Dict) -> List[TaskResult]:
        tasks = []
        for i, agent in enumerate(agents):
            enriched = self._enrich_prompt(prompt, agent, context, [])
            tasks.append(self._execute_single_agent(enriched, agent, f"{task_id}_{i}"))
        
        return await asyncio.gather(*tasks)
    
    async def _execute_collaborative(self, prompt: str, agents: List[AgentProfile],
                                      task_id: str, context: Dict) -> List[TaskResult]:
        combined_prompt = f"""COLLABORATIVE TASK - Multiple agents working together

Task: {prompt}

You are part of a team. Focus on your specialty while considering other perspectives.
Your role: {{ROLE}}

Provide your contribution and note any areas where other specialists should contribute."""
        
        results = []
        for i, agent in enumerate(agents):
            agent_prompt = combined_prompt.replace("{{ROLE}}", agent.description)
            result = await self._execute_single_agent(agent_prompt, agent, f"{task_id}_{i}")
            results.append(result)
        
        return results
    
    async def _execute_hierarchical(self, prompt: str, agents: List[AgentProfile],
                                     task_id: str, context: Dict) -> List[TaskResult]:
        if not agents:
            return []
        
        # Lead agent (architect/lead) creates plan
        lead = agents[0]
        plan_prompt = f"""As the lead, create a detailed plan for this task:

{prompt}

Break down into subtasks with clear deliverables."""
        
        plan_result = await self._execute_single_agent(plan_prompt, lead, f"{task_id}_plan")
        
        # Workers execute
        worker_results = []
        for i, agent in enumerate(agents[1:-1] if len(agents) > 2 else agents[1:]):
            worker_prompt = f"""Execute this part of the plan:

Plan: {plan_result.output}

Your subtask: [Subtask {i+1}]

Focus only on your assigned portion."""
            
            result = await self._execute_single_agent(worker_prompt, agent, f"{task_id}_worker_{i}")
            worker_results.append(result)
        
        # Reviewer consolidates
        if len(agents) > 1:
            reviewer = agents[-1]
            review_prompt = f"""Review and consolidate all outputs:

Plan: {plan_result.output}

Worker outputs:
"""
            for wr in worker_results:
                review_prompt += f"\n---\n{wr.output}\n---\n"
            
            final_result = await self._execute_single_agent(review_prompt, reviewer, f"{task_id}_final")
            return [plan_result] + worker_results + [final_result]
        
        return [plan_result] + worker_results
    
    async def _execute_single_agent(self, prompt: str, agent: AgentProfile, task_id: str) -> TaskResult:
        start = time.time()
        
        output = await self._call_kashiza(prompt, agent)
        
        exec_time = time.time() - start
        tokens = len(output.split()) * 1.5
        cost = (tokens / 1000) * agent.cost_per_1k_tokens
        
        return TaskResult(
            agent_id=agent.id,
            task_id=task_id,
            success=True,
            output=output,
            execution_time=exec_time,
            tokens_used=int(tokens),
            cost=cost,
            quality_score=0.0
        )
    
    async def _call_kashiza(self, prompt: str, agent: AgentProfile) -> str:
        # Integration avec Hermes
        try:
            from kashiza import AIAgent
            
            kashiza_agent = AIAgent(
                model=agent.model,
                enabled_toolsets=agent.skills,
                quiet_mode=True
            )
            
            response = kashiza_agent.chat(prompt)
            return response
        except Exception as e:
            if self.debugger:
                return await self.debugger.attempt_fix(prompt, agent, str(e))
            return f"Error: {str(e)}"
    
    def _enrich_prompt(self, prompt: str, agent: AgentProfile, context: Dict, 
                       previous_results: List[TaskResult]) -> str:
        enriched = f"""You are {agent.name}.
Specialty: {agent.description}
Skills: {', '.join(agent.skills)}

Task: {prompt}"""
        
        if context:
            enriched += f"\n\nContext: {json.dumps(context, indent=2)}"
        
        if previous_results:
            enriched += "\n\nPrevious work:"
            for r in previous_results:
                enriched += f"\n\n[{r.agent_id}]:\n{r.output[:1000]}"
        
        return enriched
    
    def record_feedback(self, task_id: str, rating: int, comment: str = ""):
        self.feedback_db[task_id].append({
            "rating": rating,
            "comment": comment,
            "timestamp": time.time()
        })
    
    def get_agent_performance(self, agent_id: str) -> Dict:
        agent_results = [r for r in self.execution_history if r.agent_id == agent_id]
        
        if not agent_results:
            return {"tasks_completed": 0}
        
        feedback = []
        for r in agent_results:
            if r.task_id in self.feedback_db:
                feedback.extend(self.feedback_db[r.task_id])
        
        avg_rating = sum(f["rating"] for f in feedback) / len(feedback) if feedback else 0
        
        return {
            "tasks_completed": len(agent_results),
            "avg_execution_time": sum(r.execution_time for r in agent_results) / len(agent_results),
            "total_cost": sum(r.cost for r in agent_results),
            "avg_quality_score": sum(r.quality_score for r in agent_results) / len(agent_results),
            "avg_user_rating": avg_rating,
            "feedback_count": len(feedback)
        }

# Singleton instance
_orchestrator = None

def get_orchestrator(kashiza_path: str = "") -> SmartOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SmartOrchestrator(kashiza_path)
    return _orchestrator
