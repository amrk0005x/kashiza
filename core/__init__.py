"""
Kashiza Core Module

Advanced multi-agent orchestration with AI-powered features.
"""

from .orchestrator import (
    SmartOrchestrator,
    AgentRegistry,
    PromptAnalyzer,
    ExecutionMode,
    get_orchestrator
)

from .cost_tracker import (
    SmartCostTracker,
    CostEntry,
    BudgetAlert,
    get_cost_tracker
)

from .auto_debugger import (
    SmartDebugger,
    ErrorType,
    FixStrategy,
    FixResult,
    get_debugger
)

from .team_collab import (
    TeamCollaboration,
    RealtimeCollaboration,
    TeamMember,
    Project,
    Task,
    Comment
)

from .self_monitor import (
    SelfMonitor,
    AutoCorrector,
    PerformanceMetrics,
    QualityScore
)

from .optimizations import (
    SmartCache,
    ToolResultCache,
    PromptCache,
    ContextCompressor,
    ParallelExecutor,
    ModelRouter,
    SmartRetry,
    HealthChecker,
    get_tool_cache,
    get_prompt_cache,
    get_context_compressor,
    get_parallel_executor,
    get_model_router,
    get_smart_retry,
    get_health_checker
)

__version__ = "2.0.0"
__all__ = [
    # Orchestrator
    'SmartOrchestrator',
    'AgentRegistry',
    'PromptAnalyzer',
    'ExecutionMode',
    'get_orchestrator',
    
    # Cost tracking
    'SmartCostTracker',
    'CostEntry',
    'BudgetAlert',
    'get_cost_tracker',
    
    # Debugger
    'SmartDebugger',
    'ErrorType',
    'FixStrategy',
    'FixResult',
    'get_debugger',
    
    # Team
    'TeamCollaboration',
    'RealtimeCollaboration',
    'TeamMember',
    'Project',
    'Task',
    'Comment',
    
    # Monitoring
    'SelfMonitor',
    'AutoCorrector',
    'PerformanceMetrics',
    'QualityScore',
    
    # Optimizations
    'SmartCache',
    'ToolResultCache',
    'PromptCache',
    'ContextCompressor',
    'ParallelExecutor',
    'ModelRouter',
    'SmartRetry',
    'HealthChecker',
    'get_tool_cache',
    'get_prompt_cache',
    'get_context_compressor',
    'get_parallel_executor',
    'get_model_router',
    'get_smart_retry',
    'get_health_checker',
]
