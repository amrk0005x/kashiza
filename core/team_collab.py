import json
import time
import hashlib
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
from datetime import datetime
import asyncio

@dataclass
class TeamMember:
    id: str
    name: str
    email: str
    role: str
    permissions: List[str]
    status: str = "active"
    joined_at: str = None
    
    def __post_init__(self):
        if self.joined_at is None:
            self.joined_at = datetime.now().isoformat()

@dataclass
class Project:
    id: str
    name: str
    description: str
    owner_id: str
    member_ids: List[str]
    created_at: str = None
    status: str = "active"
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

@dataclass
class Task:
    id: str
    project_id: str
    title: str
    description: str
    assignee_id: Optional[str]
    creator_id: str
    status: str = "todo"
    priority: str = "medium"
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at

@dataclass
class Comment:
    id: str
    task_id: str
    author_id: str
    content: str
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

class TeamCollaboration:
    PERMISSIONS = {
        'admin': ['*'],
        'manager': ['create_project', 'manage_team', 'view_all', 'assign_tasks'],
        'developer': ['view_project', 'create_task', 'update_task', 'comment'],
        'viewer': ['view_project', 'comment']
    }
    
    def __init__(self, storage_path: str = "config/team_data.json"):
        self.storage_path = storage_path
        self.members: Dict[str, TeamMember] = {}
        self.projects: Dict[str, Project] = {}
        self.tasks: Dict[str, Task] = {}
        self.comments: Dict[str, List[Comment]] = defaultdict(list)
        self.activity_log: List[Dict] = []
        
        self._load_data()
    
    def _load_data(self):
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                for mid, mdata in data.get('members', {}).items():
                    self.members[mid] = TeamMember(**mdata)
                for pid, pdata in data.get('projects', {}).items():
                    self.projects[pid] = Project(**pdata)
                for tid, tdata in data.get('tasks', {}).items():
                    self.tasks[tid] = Task(**tdata)
        except:
            pass
    
    def _save_data(self):
        import os
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, 'w') as f:
            json.dump({
                'members': {mid: asdict(m) for mid, m in self.members.items()},
                'projects': {pid: asdict(p) for pid, p in self.projects.items()},
                'tasks': {tid: asdict(t) for tid, t in self.tasks.items()}
            }, f, indent=2)
    
    def _log_activity(self, action: str, user_id: str, details: Dict):
        self.activity_log.append({
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'user_id': user_id,
            'details': details
        })
    
    def _check_permission(self, user_id: str, permission: str) -> bool:
        member = self.members.get(user_id)
        if not member:
            return False
        
        role_perms = self.PERMISSIONS.get(member.role, [])
        return '*' in role_perms or permission in role_perms
    
    # ==================== MEMBERS ====================
    
    def create_member(self, name: str, email: str, role: str = "developer",
                      created_by: str = None) -> TeamMember:
        mid = hashlib.md5(f"{email}{time.time()}".encode()).hexdigest()[:12]
        
        member = TeamMember(
            id=mid,
            name=name,
            email=email,
            role=role,
            permissions=self.PERMISSIONS.get(role, [])
        )
        
        self.members[mid] = member
        self._save_data()
        self._log_activity('member_created', created_by or mid, {'member_id': mid})
        
        return member
    
    def get_member(self, member_id: str) -> Optional[TeamMember]:
        return self.members.get(member_id)
    
    def update_member_role(self, member_id: str, new_role: str, 
                           updated_by: str) -> bool:
        if not self._check_permission(updated_by, 'manage_team'):
            return False
        
        member = self.members.get(member_id)
        if member:
            member.role = new_role
            member.permissions = self.PERMISSIONS.get(new_role, [])
            self._save_data()
            self._log_activity('role_updated', updated_by, {
                'member_id': member_id, 'new_role': new_role
            })
            return True
        return False
    
    def list_members(self) -> List[TeamMember]:
        return list(self.members.values())
    
    # ==================== PROJECTS ====================
    
    def create_project(self, name: str, description: str, owner_id: str) -> Project:
        if not self._check_permission(owner_id, 'create_project'):
            raise PermissionError("Insufficient permissions")
        
        pid = hashlib.md5(f"{name}{time.time()}".encode()).hexdigest()[:12]
        
        project = Project(
            id=pid,
            name=name,
            description=description,
            owner_id=owner_id,
            member_ids=[owner_id]
        )
        
        self.projects[pid] = project
        self._save_data()
        self._log_activity('project_created', owner_id, {'project_id': pid})
        
        return project
    
    def get_project(self, project_id: str) -> Optional[Project]:
        return self.projects.get(project_id)
    
    def add_project_member(self, project_id: str, member_id: str, 
                          added_by: str) -> bool:
        if not self._check_permission(added_by, 'manage_team'):
            return False
        
        project = self.projects.get(project_id)
        if project and member_id in self.members:
            if member_id not in project.member_ids:
                project.member_ids.append(member_id)
                self._save_data()
                self._log_activity('member_added', added_by, {
                    'project_id': project_id, 'member_id': member_id
                })
            return True
        return False
    
    def remove_project_member(self, project_id: str, member_id: str,
                              removed_by: str) -> bool:
        project = self.projects.get(project_id)
        if project and member_id in project.member_ids:
            project.member_ids.remove(member_id)
            self._save_data()
            self._log_activity('member_removed', removed_by, {
                'project_id': project_id, 'member_id': member_id
            })
            return True
        return False
    
    def list_projects(self, member_id: str = None) -> List[Project]:
        if member_id:
            return [p for p in self.projects.values() if member_id in p.member_ids]
        return list(self.projects.values())
    
    # ==================== TASKS ====================
    
    def create_task(self, project_id: str, title: str, description: str,
                   creator_id: str, assignee_id: str = None,
                   priority: str = "medium") -> Task:
        if not self._check_permission(creator_id, 'create_task'):
            raise PermissionError("Insufficient permissions")
        
        project = self.projects.get(project_id)
        if not project or creator_id not in project.member_ids:
            raise ValueError("Not a project member")
        
        tid = hashlib.md5(f"{title}{time.time()}".encode()).hexdigest()[:12]
        
        task = Task(
            id=tid,
            project_id=project_id,
            title=title,
            description=description,
            assignee_id=assignee_id,
            creator_id=creator_id,
            priority=priority
        )
        
        self.tasks[tid] = task
        self._save_data()
        self._log_activity('task_created', creator_id, {'task_id': tid, 'project_id': project_id})
        
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, updates: Dict, updated_by: str) -> bool:
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        if not self._check_permission(updated_by, 'update_task'):
            return False
        
        allowed_fields = ['title', 'description', 'assignee_id', 'status', 'priority']
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(task, field, value)
        
        task.updated_at = datetime.now().isoformat()
        self._save_data()
        self._log_activity('task_updated', updated_by, {'task_id': task_id})
        
        return True
    
    def assign_task(self, task_id: str, assignee_id: str, assigned_by: str) -> bool:
        return self.update_task(task_id, {'assignee_id': assignee_id}, assigned_by)
    
    def list_tasks(self, project_id: str = None, assignee_id: str = None,
                   status: str = None) -> List[Task]:
        tasks = list(self.tasks.values())
        
        if project_id:
            tasks = [t for t in tasks if t.project_id == project_id]
        if assignee_id:
            tasks = [t for t in tasks if t.assignee_id == assignee_id]
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)
    
    # ==================== COMMENTS ====================
    
    def add_comment(self, task_id: str, content: str, author_id: str) -> Comment:
        if not self._check_permission(author_id, 'comment'):
            raise PermissionError("Insufficient permissions")
        
        cid = hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()[:12]
        
        comment = Comment(
            id=cid,
            task_id=task_id,
            author_id=author_id,
            content=content
        )
        
        self.comments[task_id].append(comment)
        self._log_activity('comment_added', author_id, {'task_id': task_id})
        
        return comment
    
    def get_comments(self, task_id: str) -> List[Comment]:
        return self.comments.get(task_id, [])
    
    # ==================== ANALYTICS ====================
    
    def get_project_stats(self, project_id: str) -> Dict:
        tasks = self.list_tasks(project_id=project_id)
        
        return {
            'total_tasks': len(tasks),
            'by_status': {
                'todo': len([t for t in tasks if t.status == 'todo']),
                'in_progress': len([t for t in tasks if t.status == 'in_progress']),
                'done': len([t for t in tasks if t.status == 'done'])
            },
            'by_priority': {
                'low': len([t for t in tasks if t.priority == 'low']),
                'medium': len([t for t in tasks if t.priority == 'medium']),
                'high': len([t for t in tasks if t.priority == 'high'])
            },
            'member_count': len(self.projects[project_id].member_ids) if project_id in self.projects else 0
        }
    
    def get_member_activity(self, member_id: str, days: int = 7) -> Dict:
        cutoff = time.time() - (days * 24 * 3600)
        
        activity = [a for a in self.activity_log 
                   if a['user_id'] == member_id and 
                   datetime.fromisoformat(a['timestamp']).timestamp() > cutoff]
        
        return {
            'total_actions': len(activity),
            'by_action': defaultdict(int),
            'recent': activity[-10:]
        }
    
    def get_team_overview(self) -> Dict:
        return {
            'members': len(self.members),
            'projects': len(self.projects),
            'tasks': {
                'total': len(self.tasks),
                'open': len([t for t in self.tasks.values() if t.status != 'done']),
                'completed': len([t for t in self.tasks.values() if t.status == 'done'])
            }
        }

class RealtimeCollaboration:
    def __init__(self, team: TeamCollaboration):
        self.team = team
        self.connections: Dict[str, List] = {}
        self.active_users: Dict[str, str] = {}
    
    async def subscribe(self, project_id: str, user_id: str, websocket):
        if project_id not in self.connections:
            self.connections[project_id] = []
        
        self.connections[project_id].append(websocket)
        self.active_users[user_id] = project_id
        
        # Notify others
        await self.broadcast(project_id, {
            'type': 'user_joined',
            'user_id': user_id
        }, exclude=websocket)
    
    async def unsubscribe(self, project_id: str, user_id: str, websocket):
        if project_id in self.connections:
            self.connections[project_id] = [w for w in self.connections[project_id] if w != websocket]
        
        del self.active_users[user_id]
        
        await self.broadcast(project_id, {
            'type': 'user_left',
            'user_id': user_id
        })
    
    async def broadcast(self, project_id: str, message: Dict, exclude=None):
        if project_id not in self.connections:
            return
        
        for ws in self.connections[project_id]:
            if ws != exclude:
                try:
                    await ws.send_json(message)
                except:
                    pass
    
    async def notify_task_update(self, task_id: str):
        task = self.team.get_task(task_id)
        if task:
            await self.broadcast(task.project_id, {
                'type': 'task_updated',
                'task': asdict(task)
            })
