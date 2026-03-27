import asyncio
import json
import os
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
import uvicorn

# Import wrapper components
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.orchestrator import get_orchestrator, ExecutionMode
from core.cost_tracker import get_cost_tracker
from core.auto_debugger import get_debugger
from core.team_collab import TeamCollaboration, RealtimeCollaboration
from core.self_monitor import SelfMonitor, AutoCorrector
from core.optimizations import (
    get_tool_cache, get_prompt_cache, get_context_compressor,
    get_parallel_executor, get_model_router, get_smart_retry, get_health_checker
)
from skills.pc_control.controller import PCController
from skills.ab_testing.tester import ABTester
from templates.engine import TemplateEngine
from market.store import AgentMarket, PackInstaller

app = FastAPI(
    title="Kashiza API",
    description="Advanced multi-agent orchestration API",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
orchestrator = get_orchestrator()
cost_tracker = get_cost_tracker()
debugger = get_debugger()
team_collab = TeamCollaboration()
realtime_collab = RealtimeCollaboration(team_collab)
monitor = SelfMonitor()
corrector = AutoCorrector(monitor)
template_engine = TemplateEngine()
market = AgentMarket()
pack_installer = PackInstaller(market)
pc_controller = PCController()
ab_tester = ABTester()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# ==================== REQUEST MODELS ====================

class TaskRequest(BaseModel):
    prompt: str
    mode: str = "auto"
    agents: List[str] = None
    context: Dict = None

class AgentRequest(BaseModel):
    name: str
    description: str
    skills: List[str]
    specialty: str
    model: str = "claude-3-sonnet-20240229"

class TeamMemberRequest(BaseModel):
    name: str
    email: str
    role: str = "developer"

class ProjectRequest(BaseModel):
    name: str
    description: str
    owner_id: str

class TemplateRequest(BaseModel):
    template_id: str
    project_path: str
    variables: Dict

class VoiceCommandRequest(BaseModel):
    audio_data: str
    language: str = "en-US"

# ==================== AGENT ENDPOINTS ====================

@app.get("/api/agents")
async def list_agents():
    agents = orchestrator.registry.list_all()
    return {
        "agents": [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "specialty": a.specialty,
                "skills": a.skills,
                "model": a.model,
                "cost_per_1k": a.cost_per_1k_tokens
            }
            for a in agents
        ]
    }

@app.post("/api/agents")
async def create_agent(request: AgentRequest):
    from core.orchestrator import AgentProfile
    
    agent = AgentProfile(
        id=request.name.lower().replace(" ", "_"),
        name=request.name,
        description=request.description,
        skills=request.skills,
        specialty=request.specialty,
        model=request.model
    )
    
    orchestrator.registry.register(agent)
    return {"success": True, "agent": {"id": agent.id, "name": agent.name}}

@app.post("/api/agents/{agent_id}/execute")
async def execute_agent(agent_id: str, request: TaskRequest):
    agent = orchestrator.registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    mode = ExecutionMode(request.mode) if request.mode != "auto" else ExecutionMode.AUTO
    
    results = await orchestrator.execute_task(
        prompt=request.prompt,
        agents=[agent],
        mode=mode,
        context=request.context
    )
    
    return {
        "success": True,
        "results": [
            {
                "agent_id": r.agent_id,
                "output": r.output,
                "execution_time": r.execution_time,
                "tokens_used": r.tokens_used,
                "cost": r.cost
            }
            for r in results
        ]
    }

# ==================== ORCHESTRATION ENDPOINTS ====================

@app.post("/api/orchestrate")
async def orchestrate_task(request: TaskRequest):
    mode = ExecutionMode(request.mode) if request.mode != "auto" else ExecutionMode.AUTO
    
    # Auto-select agents if none provided
    agents = None
    if request.agents:
        agents = [orchestrator.registry.get(aid) for aid in request.agents]
        agents = [a for a in agents if a]
    
    results = await orchestrator.execute_task(
        prompt=request.prompt,
        agents=agents,
        mode=mode,
        context=request.context
    )
    
    return {
        "success": True,
        "mode": mode.value,
        "agents_used": [r.agent_id for r in results],
        "results": [
            {
                "agent_id": r.agent_id,
                "output": r.output,
                "execution_time": r.execution_time,
                "tokens_used": r.tokens_used,
                "cost": r.cost
            }
            for r in results
        ],
        "total_cost": sum(r.cost for r in results),
        "total_time": sum(r.execution_time for r in results)
    }

@app.post("/api/orchestrate/analyze")
async def analyze_prompt(prompt: str):
    analysis = orchestrator.analyzer.analyze(prompt)
    selected = orchestrator.select_agents(prompt)
    
    return {
        "analysis": {
            "specialties": analysis["specialties"],
            "complexity": analysis["complexity"],
            "urgency": analysis["urgency"],
            "estimated_tokens": analysis["estimated_tokens"],
            "requires_multiple_agents": analysis["requires_multiple_agents"]
        },
        "recommended_agents": [
            {"id": a.id, "name": a.name, "specialty": a.specialty}
            for a in selected
        ],
        "recommended_mode": orchestrator._determine_mode(analysis).value
    }

# ==================== COST TRACKING ENDPOINTS ====================

@app.get("/api/costs")
async def get_costs():
    return cost_tracker.get_budget_status()

@app.get("/api/costs/report")
async def get_cost_report(days: int = 7):
    return cost_tracker.get_cost_report(days)

@app.get("/api/costs/recommendation")
async def get_model_recommendation(task: str):
    return cost_tracker.get_model_recommendation(task)

@app.post("/api/costs/budget")
async def update_budget(daily: float = None, monthly: float = None):
    if daily:
        cost_tracker.daily_budget = daily
    if monthly:
        cost_tracker.monthly_budget = monthly
    cost_tracker._save_config()
    return {"success": True, "budget": cost_tracker.get_budget_status()}

# ==================== TEAM COLLABORATION ENDPOINTS ====================

@app.get("/api/team/members")
async def list_team_members():
    return {"members": [vars(m) for m in team_collab.list_members()]}

@app.post("/api/team/members")
async def create_team_member(request: TeamMemberRequest, created_by: str = "system"):
    member = team_collab.create_member(
        name=request.name,
        email=request.email,
        role=request.role,
        created_by=created_by
    )
    return {"success": True, "member": vars(member)}

@app.get("/api/team/projects")
async def list_projects(member_id: str = None):
    return {"projects": [vars(p) for p in team_collab.list_projects(member_id)]}

@app.post("/api/team/projects")
async def create_project(request: ProjectRequest):
    project = team_collab.create_project(
        name=request.name,
        description=request.description,
        owner_id=request.owner_id
    )
    return {"success": True, "project": vars(project)}

@app.get("/api/team/projects/{project_id}/stats")
async def get_project_stats(project_id: str):
    return team_collab.get_project_stats(project_id)

@app.get("/api/team/tasks")
async def list_tasks(project_id: str = None, assignee_id: str = None, status: str = None):
    return {"tasks": [vars(t) for t in team_collab.list_tasks(project_id, assignee_id, status)]}

@app.post("/api/team/projects/{project_id}/tasks")
async def create_task(project_id: str, title: str, description: str, 
                     creator_id: str, assignee_id: str = None):
    task = team_collab.create_task(
        project_id=project_id,
        title=title,
        description=description,
        creator_id=creator_id,
        assignee_id=assignee_id
    )
    return {"success": True, "task": vars(task)}

@app.get("/api/team/overview")
async def get_team_overview():
    return team_collab.get_team_overview()

# ==================== MONITORING ENDPOINTS ====================

@app.get("/api/monitoring/status")
async def get_monitoring_status():
    return {
        "quality": {
            "current_score": monitor.get_average_quality(),
            "target": monitor.target_quality
        },
        "performance": monitor.generate_report() if monitor.metrics_history else {"status": "starting"},
        "cache_stats": {
            "tool_cache": get_tool_cache().get_stats(),
            "prompt_cache": get_prompt_cache().get_stats()
        }
    }

@app.post("/api/monitoring/auto-correct")
async def trigger_auto_correction():
    result = corrector.check_and_correct()
    return result

@app.get("/api/monitoring/health")
async def health_check():
    checks = await get_health_checker().run_checks()
    return {
        "status": get_health_checker().get_overall_status(),
        "checks": checks
    }

# ==================== PC CONTROL ENDPOINTS ====================

@app.get("/api/pc/files")
async def list_files(path: str = "~"):
    return pc_controller.list_directory(path)

@app.post("/api/pc/files/read")
async def read_file(path: str, offset: int = 0, limit: int = 1000):
    return pc_controller.read_file(path, offset, limit)

@app.post("/api/pc/files/write")
async def write_file(path: str, content: str):
    return pc_controller.create_file(path, content)

@app.post("/api/pc/command")
async def run_command(command: str, timeout: int = 60):
    return pc_controller.run_command(command, timeout)

@app.get("/api/pc/system")
async def get_system_info():
    return pc_controller.get_system_info()

@app.get("/api/pc/processes")
async def list_processes(limit: int = 20):
    return pc_controller.list_processes(limit)

@app.post("/api/pc/screenshot")
async def take_screenshot(output_path: str = None):
    return pc_controller.screenshot(output_path)

# ==================== TEMPLATE ENDPOINTS ====================

@app.get("/api/templates")
async def list_templates(category: str = None):
    return {"templates": template_engine.list_templates(category)}

@app.post("/api/templates/create")
async def create_from_template(request: TemplateRequest):
    return template_engine.create_project(
        request.template_id,
        request.project_path,
        request.variables
    )

# ==================== MARKET ENDPOINTS ====================

@app.get("/api/market/packs")
async def list_market_packs(category: str = None, query: str = None):
    return {"packs": [vars(p) for p in market.search(query, category)]}

@app.post("/api/market/packs/{pack_id}/install")
async def install_pack(pack_id: str):
    return pack_installer.install_with_dependencies(pack_id)

@app.get("/api/market/installed")
async def list_installed_packs():
    return {"packs": [vars(p) for p in market.list_installed()]}

# ==================== A/B TESTING ENDPOINTS ====================

@app.get("/api/ab-tests")
async def list_ab_tests():
    return {"tests": list(ab_tester.active_tests.keys())}

@app.post("/api/ab-tests")
async def create_ab_test(name: str, variant_ids: List[str], traffic_split: List[float] = None):
    test_id = ab_tester.create_test(name, variant_ids, traffic_split)
    return {"success": True, "test_id": test_id}

@app.get("/api/ab-tests/{test_id}/stats")
async def get_ab_test_stats(test_id: str):
    return ab_tester.get_test_stats(test_id)

# ==================== WEBSOCKET ====================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get('type') == 'subscribe_project':
                project_id = data.get('project_id')
                user_id = data.get('user_id')
                await realtime_collab.subscribe(project_id, user_id, websocket)
            
            elif data.get('type') == 'execute_task':
                prompt = data.get('prompt')
                mode = data.get('mode', 'auto')
                
                await manager.broadcast({
                    'type': 'task_started',
                    'prompt': prompt,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Execute and stream results
                results = await orchestrator.execute_task(
                    prompt=prompt,
                    mode=ExecutionMode(mode) if mode != 'auto' else ExecutionMode.AUTO
                )
                
                for result in results:
                    await websocket.send_json({
                        'type': 'agent_result',
                        'agent_id': result.agent_id,
                        'output': result.output[:500],  # Truncate for WS
                        'cost': result.cost,
                        'timestamp': datetime.now().isoformat()
                    })
                
                await manager.broadcast({
                    'type': 'task_completed',
                    'total_cost': sum(r.cost for r in results),
                    'timestamp': datetime.now().isoformat()
                })
            
            elif data.get('type') == 'monitoring_subscribe':
                # Send initial monitoring data
                await websocket.send_json({
                    'type': 'monitoring_data',
                    'data': await get_monitoring_status()
                })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ==================== DASHBOARD ====================

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    dashboard_path = os.path.join(os.path.dirname(__file__), "../web/dashboard.html")
    if os.path.exists(dashboard_path):
        with open(dashboard_path) as f:
            return f.read()
    return HTMLResponse(content="<h1>Kashiza API</h1><p>Dashboard not found. API is running.</p>")

# ==================== BACKGROUND TASKS ====================

async def monitoring_task():
    while True:
        try:
            monitor.collect_metrics()
            
            # Auto-correct if quality is low
            quality = monitor.get_average_quality()
            if quality > 0 and quality < 7:
                corrector.check_and_correct()
            
            await asyncio.sleep(60)
        except Exception as e:
            print(f"Monitoring error: {e}")
            await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(monitoring_task())

# ==================== MAIN ====================

def main():
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
