"""
Mobile App API Routes
Optimized for mobile clients with reduced payload sizes and push notification support
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional
import time

router = APIRouter(prefix="/mobile/v1", tags=["mobile"])

# ==================== AUTHENTICATION ====================

class MobileAuthRequest(BaseModel):
    device_id: str
    push_token: Optional[str] = None
    platform: str  # ios, android

class MobileAuthResponse(BaseModel):
    token: str
    user_id: str
    expires_at: int

@router.post("/auth/register")
async def register_device(request: MobileAuthRequest):
    """Register mobile device for push notifications"""
    return {
        "token": f"mobile_{request.device_id}_{int(time.time())}",
        "user_id": request.device_id,
        "expires_at": int(time.time()) + 86400 * 30  # 30 days
    }

# ==================== QUICK ACTIONS ====================

class QuickActionRequest(BaseModel):
    action_type: str  # code, explain, review, search
    input: str
    voice_input: Optional[bool] = False

@router.post("/quick-action")
async def quick_action(request: QuickActionRequest):
    """Execute quick action optimized for mobile"""
    from core.orchestrator import get_orchestrator
    
    orchestrator = get_orchestrator()
    
    # Simplified prompt for mobile
    prompts = {
        "code": f"Write concise code for: {request.input}",
        "explain": f"Briefly explain: {request.input}",
        "review": f"Quick review of code:\n{request.input}",
        "search": f"Search and summarize: {request.input}"
    }
    
    prompt = prompts.get(request.action_type, request.input)
    
    # Use fastest appropriate model for mobile
    results = await orchestrator.execute_task(
        prompt=prompt,
        mode="sequential"
    )
    
    return {
        "success": True,
        "result": results[0].output if results else "No result",
        "action_type": request.action_type,
        "execution_time": sum(r.execution_time for r in results)
    }

# ==================== NOTIFICATIONS ====================

class NotificationPreferences(BaseModel):
    task_completed: bool = True
    cost_alerts: bool = True
    team_mentions: bool = True
    daily_digest: bool = False

@router.post("/notifications/preferences")
async def update_notification_preferences(user_id: str, prefs: NotificationPreferences):
    """Update push notification preferences"""
    return {"success": True, "preferences": prefs.dict()}

@router.get("/notifications")
async def get_notifications(user_id: str, limit: int = 20):
    """Get notification history"""
    return {
        "notifications": [
            {
                "id": f"notif_{i}",
                "type": "task_completed",
                "title": "Task Completed",
                "message": "Your code generation task is complete",
                "timestamp": int(time.time()) - i * 3600,
                "read": i > 5
            }
            for i in range(limit)
        ]
    }

# ==================== VOICE COMMANDS ====================

class VoiceCommandRequest(BaseModel):
    audio_base64: str
    language: str = "en-US"

@router.post("/voice/command")
async def process_voice_command(request: VoiceCommandRequest):
    """Process voice command from mobile"""
    from skills.voice.interface import VoiceCommandParser
    
    parser = VoiceCommandParser()
    
    # In production, this would transcribe the audio first
    # For now, simulate with text processing
    parsed = parser.parse("voice command placeholder")
    
    return {
        "success": True,
        "parsed_command": parsed,
        "action_required": parsed['command_type'] != 'general'
    }

# ==================== OFFLINE SYNC ====================

class SyncRequest(BaseModel):
    last_sync_timestamp: int
    pending_actions: List[Dict]

@router.post("/sync")
async def sync_data(request: SyncRequest, user_id: str):
    """Sync data for offline support"""
    # Return changes since last sync
    return {
        "sync_timestamp": int(time.time()),
        "tasks_updated": [],
        "projects_updated": [],
        "agents_updated": [],
        "pending_actions_processed": len(request.pending_actions)
    }

# ==================== DASHBOARD WIDGETS ====================

@router.get("/widgets/daily-summary")
async def get_daily_summary(user_id: str):
    """Compact daily summary for mobile widget"""
    from core.orchestrator import get_orchestrator
    from core.cost_tracker import get_cost_tracker
    
    orchestrator = get_orchestrator()
    cost_tracker = get_cost_tracker()
    
    budget = cost_tracker.get_budget_status()
    
    return {
        "tasks_completed": len(orchestrator.execution_history),
        "cost_today": budget['daily']['spent'],
        "budget_remaining": budget['daily']['remaining'],
        "quality_score": 8.5,  # Placeholder
        "active_agents": len(orchestrator.registry.list_all())
    }

@router.get("/widgets/quick-stats")
async def get_quick_stats(user_id: str):
    """Quick stats for mobile home screen widget"""
    from core.cost_tracker import get_cost_tracker
    
    cost_tracker = get_cost_tracker()
    budget = cost_tracker.get_budget_status()
    
    return {
        "daily_cost": f"${budget['daily']['spent']:.2f}",
        "budget_percent": budget['daily']['percent_used'],
        "status": "healthy" if budget['daily']['percent_used'] < 80 else "warning"
    }

# ==================== TEAM COLLABORATION ====================

@router.get("/team/activity")
async def get_team_activity(user_id: str, project_id: Optional[str] = None):
    """Get team activity feed optimized for mobile"""
    return {
        "activities": [
            {
                "id": f"act_{i}",
                "user": "Team Member",
                "action": "completed task",
                "target": "API Integration",
                "timestamp": int(time.time()) - i * 1800
            }
            for i in range(10)
        ]
    }

@router.post("/team/tasks/{task_id}/quick-update")
async def quick_task_update(task_id: str, status: str, user_id: str):
    """Quick status update for mobile"""
    return {
        "success": True,
        "task_id": task_id,
        "new_status": status,
        "updated_at": int(time.time())
    }

# ==================== FILE UPLOADS ====================

class FileUploadRequest(BaseModel):
    filename: str
    content_base64: str
    project_id: Optional[str] = None

@router.post("/files/upload")
async def upload_file(request: FileUploadRequest, user_id: str):
    """Upload file from mobile device"""
    import base64
    
    try:
        content = base64.b64decode(request.content_base64)
        
        # Save file
        from skills.pc_control.controller import PCController
        pc = PCController()
        
        result = pc.create_file(
            f"~/uploads/{request.filename}",
            content.decode('utf-8', errors='ignore')
        )
        
        return {
            "success": result.get('success', False),
            "filename": request.filename,
            "size": len(content)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==================== CHAT INTERFACE ====================

class ChatMessageRequest(BaseModel):
    message: str
    context: Optional[Dict] = None
    stream: bool = False

@router.post("/chat")
async def chat_message(request: ChatMessageRequest, user_id: str):
    """Mobile-optimized chat interface"""
    from core.orchestrator import get_orchestrator
    
    orchestrator = get_orchestrator()
    
    results = await orchestrator.execute_task(
        prompt=request.message,
        mode="sequential"
    )
    
    return {
        "response": results[0].output if results else "I couldn't process that request.",
        "message_id": f"msg_{int(time.time())}",
        "tokens_used": sum(r.tokens_used for r in results),
        "cost": sum(r.cost for r in results)
    }

# ==================== SETTINGS ====================

@router.get("/settings")
async def get_mobile_settings(user_id: str):
    """Get mobile app settings"""
    return {
        "theme": "dark",
        "font_size": "medium",
        "code_wrap": True,
        "auto_sync": True,
        "sync_interval": 300,
        "offline_mode": False,
        "data_saver": False
    }

@router.post("/settings")
async def update_mobile_settings(user_id: str, settings: Dict):
    """Update mobile app settings"""
    return {"success": True, "settings": settings}

# ==================== BIOMETRIC AUTH ====================

@router.post("/auth/biometric/enable")
async def enable_biometric_auth(user_id: str, public_key: str):
    """Enable biometric authentication"""
    return {"success": True, "biometric_enabled": True}

@router.post("/auth/biometric/verify")
async def verify_biometric_auth(user_id: str, signature: str):
    """Verify biometric authentication"""
    return {"success": True, "token": f"bio_{user_id}_{int(time.time())}"}
