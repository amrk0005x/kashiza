"""
Enhanced Kashiza API Server
Includes: Security, WebSocket Real-time Collaboration, Mobile Push Notifications
"""

import asyncio
import json
import os
import ssl
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks, Depends, Security, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
import uvicorn
import jwt

# Import wrapper components
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.security import get_security_manager, get_secure_env, RequestValidator, SecurityManager, SecureEnv
from core.plugin import get_plugin_manager
from core.orchestrator import get_orchestrator, ExecutionMode
from core.cost_tracker import get_cost_tracker
from core.auto_debugger import get_debugger
from core.team_collab import TeamCollaboration, RealtimeCollaboration, TeamMember, Project, Task
from core.self_monitor import SelfMonitor, AutoCorrector
from core.optimizations import (
    get_tool_cache, get_prompt_cache, get_context_compressor,
    get_parallel_executor, get_model_router, get_smart_retry, get_health_checker
)
from skills.pc_control.controller import PCController
from skills.ab_testing.tester import ABTester
from skills.git_integration.manager import GitManager
from templates.engine import TemplateEngine
from market.store import AgentMarket, PackInstaller

# Security setup
security = HTTPBearer()
request_validator = RequestValidator()

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

class ConnectionManager:
    """Enhanced WebSocket connection manager with rooms"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_rooms: Dict[str, Set[str]] = {}
        self.rooms: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.user_rooms[client_id] = set()
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        # Remove from all rooms
        if client_id in self.user_rooms:
            for room in self.user_rooms[client_id]:
                if room in self.rooms and client_id in self.rooms[room]:
                    self.rooms[room].remove(client_id)
            del self.user_rooms[client_id]
    
    async def join_room(self, client_id: str, room: str):
        if room not in self.rooms:
            self.rooms[room] = set()
        self.rooms[room].add(client_id)
        self.user_rooms[client_id].add(room)
    
    async def leave_room(self, client_id: str, room: str):
        if room in self.rooms and client_id in self.rooms[room]:
            self.rooms[room].remove(client_id)
        if client_id in self.user_rooms and room in self.user_rooms[client_id]:
            self.user_rooms[client_id].remove(room)
    
    async def send_to_client(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except:
                self.disconnect(client_id)
    
    async def broadcast_to_room(self, room: str, message: dict, exclude: str = None):
        if room not in self.rooms:
            return
        
        disconnected = []
        for client_id in self.rooms[room]:
            if client_id == exclude:
                continue
            try:
                if client_id in self.active_connections:
                    await self.active_connections[client_id].send_json(message)
            except:
                disconnected.append(client_id)
        
        for client_id in disconnected:
            self.disconnect(client_id)
    
    async def broadcast(self, message: dict, exclude: str = None):
        disconnected = []
        for client_id, connection in self.active_connections.items():
            if client_id == exclude:
                continue
            try:
                await connection.send_json(message)
            except:
                disconnected.append(client_id)
        
        for client_id in disconnected:
            self.disconnect(client_id)

manager = ConnectionManager()

# Push notification manager
class PushNotificationManager:
    """Manage push notifications for mobile clients"""
    
    def __init__(self):
        self.tokens: Dict[str, Dict] = {}  # user_id -> {platform, token, preferences}
    
    def register_token(self, user_id: str, platform: str, token: str, 
                      preferences: Dict = None):
        """Register device push token"""
        self.tokens[user_id] = {
            'platform': platform,
            'token': token,
            'preferences': preferences or {},
            'registered_at': datetime.now().isoformat()
        }
    
    async def send_notification(self, user_id: str, title: str, body: str, 
                               data: Dict = None):
        """Send push notification"""
        if user_id not in self.tokens:
            return False
        
        token_info = self.tokens[user_id]
        
        # Check preferences
        prefs = token_info.get('preferences', {})
        notification_type = data.get('type', 'general') if data else 'general'
        
        if notification_type == 'task_completed' and not prefs.get('task_completed', True):
            return False
        if notification_type == 'cost_alert' and not prefs.get('cost_alerts', True):
            return False
        
        # Send to appropriate platform
        if token_info['platform'] == 'ios':
            return await self._send_apns(token_info['token'], title, body, data)
        elif token_info['platform'] == 'android':
            return await self._send_fcm(token_info['token'], title, body, data)
        
        return False
    
    async def _send_apns(self, token: str, title: str, body: str, data: Dict):
        """Send Apple Push Notification"""
        # Implementation would use APNS library
        print(f"[APNS] To {token[:20]}...: {title}")
        return True
    
    async def _send_fcm(self, token: str, title: str, body: str, data: Dict):
        """Send Firebase Cloud Message"""
        # Implementation would use Firebase Admin SDK
        print(f"[FCM] To {token[:20]}...: {title}")
        return True
    
    async def broadcast_to_project(self, project_id: str, title: str, body: str,
                                   data: Dict = None, exclude_user: str = None):
        """Send notification to all project members"""
        # Get project members from team_collab
        team = TeamCollaboration()
        project = team.get_project(project_id)
        
        if not project:
            return
        
        for member_id in project.member_ids:
            if member_id == exclude_user:
                continue
            await self.send_notification(member_id, title, body, data)

push_manager = PushNotificationManager()

# ==================== AUTHENTICATION ====================

def create_token(user_id: str, role: str = 'user') -> str:
    """Create JWT token"""
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict:
    """Verify JWT token"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==================== APP LIFESPAN ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    plugin_manager = get_plugin_manager()
    security_manager = get_security_manager()
    
    # Verify environment keys
    key_status = security_manager.verify_environment_keys()
    print("🔐 API Keys status:", {k: '✅' if v else '❌' for k, v in key_status.items()})
    
    # Load plugins
    plugins = plugin_manager.list_plugins()
    print(f"🔌 Loaded {len(plugins)} plugins")
    
    # Start monitoring
    asyncio.create_task(monitoring_task())
    
    yield
    
    # Shutdown
    plugin_manager.stop()
    print("👋 Server shutting down")

app = FastAPI(
    title="Kashiza API",
    description="Advanced multi-agent orchestration with security",
    version="2.1.0",
    lifespan=lifespan
)

# Security middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "https://*.kashiza.dev"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

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

# ==================== SECURITY ENDPOINTS ====================

@app.post("/auth/login")
async def login(request: Request):
    """Login and get JWT token"""
    data = await request.json()
    username = data.get('username')
    password = data.get('password')
    
    # In production, verify against database
    if username and password:
        token = create_token(username, role='developer')
        return {'token': token, 'type': 'bearer'}
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/auth/verify")
async def verify_auth(token: Dict = Depends(verify_token)):
    """Verify token validity"""
    return {'valid': True, 'user_id': token['user_id'], 'role': token['role']}

@app.post("/security/keys/store")
async def store_api_key(request: Request, token: Dict = Depends(verify_token)):
    """Store API key securely"""
    data = await request.json()
    
    security_manager = get_security_manager()
    key_hash = security_manager.encrypt_api_key(
        service=data['service'],
        api_key=data['key'],
        ip_whitelist=data.get('ip_whitelist'),
        expires_days=data.get('expires_days')
    )
    
    return {'success': True, 'key_hash': key_hash}

@app.get("/security/keys")
async def list_api_keys(token: Dict = Depends(verify_token)):
    """List stored API keys (obfuscated)"""
    security_manager = get_security_manager()
    return {'keys': security_manager.get_key_info()}

@app.post("/security/keys/{service}/rotate")
async def rotate_api_key(service: str, request: Request, token: Dict = Depends(verify_token)):
    """Rotate API key"""
    data = await request.json()
    security_manager = get_security_manager()
    new_hash = security_manager.rotate_key(service, data['new_key'])
    return {'success': True, 'new_hash': new_hash}

@app.delete("/security/keys/{service}")
async def revoke_api_key(service: str, token: Dict = Depends(verify_token)):
    """Revoke API key"""
    security_manager = get_security_manager()
    security_manager.revoke_key(service)
    return {'success': True}

# ==================== ENHANCED WEBSOCKET ====================

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get('type')
            
            if msg_type == 'join_room':
                room = data.get('room')
                await manager.join_room(client_id, room)
                await manager.broadcast_to_room(room, {
                    'type': 'user_joined',
                    'client_id': client_id,
                    'room': room,
                    'timestamp': datetime.now().isoformat()
                }, exclude=client_id)
            
            elif msg_type == 'leave_room':
                room = data.get('room')
                await manager.leave_room(client_id, room)
            
            elif msg_type == 'subscribe_project':
                project_id = data.get('project_id')
                await manager.join_room(client_id, f"project:{project_id}")
                
                # Also subscribe via realtime collaboration
                user_id = data.get('user_id')
                await realtime_collab.subscribe(project_id, user_id, websocket)
            
            elif msg_type == 'typing':
                room = data.get('room')
                await manager.broadcast_to_room(room, {
                    'type': 'user_typing',
                    'client_id': client_id,
                    'user_name': data.get('user_name'),
                    'timestamp': datetime.now().isoformat()
                }, exclude=client_id)
            
            elif msg_type == 'cursor_position':
                room = data.get('room')
                await manager.broadcast_to_room(room, {
                    'type': 'cursor_update',
                    'client_id': client_id,
                    'position': data.get('position'),
                    'timestamp': datetime.now().isoformat()
                }, exclude=client_id)
            
            elif msg_type == 'execute_task':
                prompt = data.get('prompt')
                mode = data.get('mode', 'auto')
                room = data.get('room')
                
                await manager.broadcast_to_room(room, {
                    'type': 'task_started',
                    'client_id': client_id,
                    'prompt': prompt,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Execute with plugin hooks
                plugin_manager = get_plugin_manager()
                await plugin_manager.execute_hook('pre_orchestrate', {
                    'prompt': prompt,
                    'client_id': client_id
                })
                
                results = await orchestrator.execute_task(
                    prompt=prompt,
                    mode=ExecutionMode(mode) if mode != 'auto' else ExecutionMode.AUTO
                )
                
                await plugin_manager.execute_hook('post_orchestrate', {
                    'prompt': prompt,
                    'results': results,
                    'client_id': client_id
                })
                
                for result in results:
                    await manager.broadcast_to_room(room, {
                        'type': 'agent_result',
                        'client_id': client_id,
                        'agent_id': result.agent_id,
                        'output': result.output[:500],
                        'cost': result.cost,
                        'timestamp': datetime.now().isoformat()
                    })
                
                await manager.broadcast_to_room(room, {
                    'type': 'task_completed',
                    'client_id': client_id,
                    'total_cost': sum(r.cost for r in results),
                    'timestamp': datetime.now().isoformat()
                })
            
            elif msg_type == 'chat_message':
                room = data.get('room')
                message = data.get('message')
                
                await manager.broadcast_to_room(room, {
                    'type': 'chat_message',
                    'client_id': client_id,
                    'user_name': data.get('user_name'),
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                })
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)

# ==================== PUSH NOTIFICATIONS ====================

@app.post("/mobile/push/register")
async def register_push_token(request: Request, token: Dict = Depends(verify_token)):
    """Register device for push notifications"""
    data = await request.json()
    
    push_manager.register_token(
        user_id=token['user_id'],
        platform=data['platform'],
        token=data['push_token'],
        preferences=data.get('preferences', {})
    )
    
    return {'success': True}

@app.post("/mobile/push/send")
async def send_push_notification(request: Request, token: Dict = Depends(verify_token)):
    """Send push notification (admin only)"""
    if token.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    data = await request.json()
    
    success = await push_manager.send_notification(
        user_id=data['user_id'],
        title=data['title'],
        body=data['body'],
        data=data.get('data')
    )
    
    return {'success': success}

# ==================== ENHANCED TEAM COLLAB ====================

@app.post("/api/team/projects/{project_id}/notify")
async def notify_project_members(project_id: str, request: Request, 
                                  token: Dict = Depends(verify_token)):
    """Send notification to all project members"""
    data = await request.json()
    
    await push_manager.broadcast_to_project(
        project_id=project_id,
        title=data['title'],
        body=data['body'],
        data={'type': 'project_notification', 'project_id': project_id},
        exclude_user=token['user_id']
    )
    
    # Also broadcast via WebSocket
    await manager.broadcast_to_room(f"project:{project_id}", {
        'type': 'project_notification',
        'title': data['title'],
        'message': data['body'],
        'timestamp': datetime.now().isoformat()
    })
    
    return {'success': True}

# ==================== PLUGINS ====================

@app.get("/api/plugins")
async def list_plugins(token: Dict = Depends(verify_token)):
    """List loaded plugins"""
    plugin_manager = get_plugin_manager()
    return {'plugins': plugin_manager.list_plugins()}

@app.post("/api/plugins/{plugin_name}/reload")
async def reload_plugin(plugin_name: str, token: Dict = Depends(verify_token)):
    """Hot reload a plugin"""
    if token.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    plugin_manager = get_plugin_manager()
    success = plugin_manager.reload_plugin(plugin_name)
    return {'success': success}

@app.post("/api/plugins/{plugin_name}/enable")
async def enable_plugin(plugin_name: str, token: Dict = Depends(verify_token)):
    """Enable a plugin"""
    plugin_manager = get_plugin_manager()
    plugin_manager.enable_plugin(plugin_name)
    return {'success': True}

@app.post("/api/plugins/{plugin_name}/disable")
async def disable_plugin(plugin_name: str, token: Dict = Depends(verify_token)):
    """Disable a plugin"""
    plugin_manager = get_plugin_manager()
    plugin_manager.disable_plugin(plugin_name)
    return {'success': True}

@app.get("/api/plugins/stats")
async def get_plugin_stats(token: Dict = Depends(verify_token)):
    """Get plugin execution statistics"""
    plugin_manager = get_plugin_manager()
    return {'stats': plugin_manager.get_plugin_stats()}

# ==================== GIT INTEGRATION ====================

@app.get("/api/git/status")
async def git_status(path: str = '.', token: Dict = Depends(verify_token)):
    """Get git status"""
    git = GitManager(path)
    return git.get_status()

@app.post("/api/git/commit")
async def git_commit(request: Request, token: Dict = Depends(verify_token)):
    """Create smart commit"""
    data = await request.json()
    git = GitManager(data.get('path', '.'))
    return git.smart_commit(data.get('path'), data.get('message'))

@app.post("/api/git/push")
async def git_push(request: Request, token: Dict = Depends(verify_token)):
    """Push to remote"""
    data = await request.json()
    git = GitManager(data.get('path', '.'))
    success = git.push(
        remote=data.get('remote', 'origin'),
        branch=data.get('branch'),
        force=data.get('force', False)
    )
    return {'success': success}

@app.get("/api/git/branches")
async def git_branches(path: str = '.', token: Dict = Depends(verify_token)):
    """List branches"""
    git = GitManager(path)
    branches = git.get_branches()
    return {'branches': [b.__dict__ for b in branches]}

@app.post("/api/git/pr/create")
async def create_pr(request: Request, token: Dict = Depends(verify_token)):
    """Create pull request"""
    data = await request.json()
    git = GitManager()
    return git.create_pr(
        repo=data['repo'],
        title=data['title'],
        body=data['body'],
        head_branch=data['head_branch'],
        base_branch=data.get('base_branch', 'main')
    )

@app.get("/api/git/pr/list")
async def list_prs(repo: str, state: str = 'open', token: Dict = Depends(verify_token)):
    """List pull requests"""
    git = GitManager()
    return {'prs': git.list_prs(repo, state)}

@app.get("/api/git/diff/analyze")
async def analyze_diff(path: str = '.', token: Dict = Depends(verify_token)):
    """Analyze code diff"""
    git = GitManager(path)
    return git.analyze_diff(path)

# ==================== BACKGROUND TASKS ====================

async def monitoring_task():
    """Background monitoring task"""
    while True:
        try:
            monitor.collect_metrics()
            
            # Check quality and auto-correct
            quality = monitor.get_average_quality()
            if quality > 0 and quality < 7:
                result = corrector.check_and_correct()
                if result['corrections']:
                    # Notify admins
                    await manager.broadcast({
                        'type': 'system_alert',
                        'alert_type': 'quality_correction',
                        'message': f'Auto-corrected {len(result["corrections"])} issues',
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Check cost thresholds
            budget = cost_tracker.get_budget_status()
            if budget['daily']['percent_used'] > 80:
                await manager.broadcast({
                    'type': 'system_alert',
                    'alert_type': 'cost_warning',
                    'message': f'Daily budget {budget["daily"]["percent_used"]:.0f}% used',
                    'timestamp': datetime.now().isoformat()
                })
            
            await asyncio.sleep(60)
        except Exception as e:
            print(f"Monitoring error: {e}")
            await asyncio.sleep(60)

# ==================== MAIN ====================

def main():
    # SSL configuration for production
    ssl_keyfile = os.getenv('SSL_KEYFILE')
    ssl_certfile = os.getenv('SSL_CERTFILE')
    
    ssl_context = None
    if ssl_keyfile and ssl_certfile:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(ssl_certfile, ssl_keyfile)
    
    uvicorn.run(
        "api.enhanced_server:app",
        host="0.0.0.0",
        port=int(os.getenv('PORT', 8080)),
        reload=True,
        log_level="info",
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile
    )

if __name__ == "__main__":
    main()
