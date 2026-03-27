"""
Team Manager pour Kashiza
Gestion multi-utilisateur avec demande de nom au premier contact
"""
import os
import json
import hashlib
import secrets
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from enum import Enum
import uuid

class UserRole(Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    GUEST = "guest"

class Permission(Enum):
    CREATE_AGENT = "create_agent"
    DELETE_AGENT = "delete_agent"
    EXECUTE_TASK = "execute_task"
    MANAGE_TEAM = "manage_team"
    VIEW_LOGS = "view_logs"
    MANAGE_BILLING = "manage_billing"
    INVITE_USERS = "invite_users"
    MANAGE_PLUGINS = "manage_plugins"

ROLE_PERMISSIONS = {
    UserRole.OWNER: [
        Permission.CREATE_AGENT, Permission.DELETE_AGENT, Permission.EXECUTE_TASK,
        Permission.MANAGE_TEAM, Permission.VIEW_LOGS, Permission.MANAGE_BILLING,
        Permission.INVITE_USERS, Permission.MANAGE_PLUGINS
    ],
    UserRole.ADMIN: [
        Permission.CREATE_AGENT, Permission.DELETE_AGENT, Permission.EXECUTE_TASK,
        Permission.MANAGE_TEAM, Permission.VIEW_LOGS, Permission.INVITE_USERS,
        Permission.MANAGE_PLUGINS
    ],
    UserRole.MEMBER: [
        Permission.CREATE_AGENT, Permission.EXECUTE_TASK, Permission.VIEW_LOGS
    ],
    UserRole.GUEST: [
        Permission.EXECUTE_TASK
    ]
}

@dataclass
class User:
    id: str
    name: str
    email: Optional[str]
    role: UserRole
    created_at: str
    last_active: str
    preferences: Dict = field(default_factory=dict)
    api_key: Optional[str] = None
    session_count: int = 0
    is_active: bool = True
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data["role"] = self.role.value
        data["api_key"] = "***" if self.api_key else None
        return data
    
    def has_permission(self, permission: Permission) -> bool:
        return permission in ROLE_PERMISSIONS.get(self.role, [])

@dataclass
class Team:
    id: str
    name: str
    owner_id: str
    created_at: str
    members: Dict[str, UserRole] = field(default_factory=dict)
    settings: Dict = field(default_factory=dict)
    invite_codes: List[str] = field(default_factory=list)
    max_members: int = 10

class TeamManager:
    """Gère les équipes et utilisateurs multi-utilisateurs"""
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.path.expanduser("~/.kashiza/team")
        os.makedirs(self.storage_path, exist_ok=True)
        
        self.users_file = os.path.join(self.storage_path, "users.json")
        self.teams_file = os.path.join(self.storage_path, "teams.json")
        self.sessions_file = os.path.join(self.storage_path, "sessions.json")
        
        self.users: Dict[str, User] = {}
        self.teams: Dict[str, Team] = {}
        self.active_sessions: Dict[str, Dict] = {}
        
        self._load_data()
    
    def _load_data(self):
        """Charge les données persistantes"""
        if os.path.exists(self.users_file):
            with open(self.users_file) as f:
                data = json.load(f)
                for uid, udata in data.items():
                    self.users[uid] = User(
                        id=udata["id"],
                        name=udata["name"],
                        email=udata.get("email"),
                        role=UserRole(udata["role"]),
                        created_at=udata["created_at"],
                        last_active=udata["last_active"],
                        preferences=udata.get("preferences", {}),
                        api_key=udata.get("api_key"),
                        session_count=udata.get("session_count", 0),
                        is_active=udata.get("is_active", True)
                    )
        
        if os.path.exists(self.teams_file):
            with open(self.teams_file) as f:
                data = json.load(f)
                for tid, tdata in data.items():
                    members = {
                        uid: UserRole(r) for uid, r in tdata.get("members", {}).items()
                    }
                    self.teams[tid] = Team(
                        id=tdata["id"],
                        name=tdata["name"],
                        owner_id=tdata["owner_id"],
                        created_at=tdata["created_at"],
                        members=members,
                        settings=tdata.get("settings", {}),
                        invite_codes=tdata.get("invite_codes", []),
                        max_members=tdata.get("max_members", 10)
                    )
    
    def _save_data(self):
        """Sauvegarde les données"""
        users_data = {
            uid: {
                **asdict(user),
                "role": user.role.value
            }
            for uid, user in self.users.items()
        }
        
        teams_data = {
            tid: {
                **asdict(team),
                "members": {
                    uid: role.value for uid, role in team.members.items()
                }
            }
            for tid, team in self.teams.items()
        }
        
        with open(self.users_file, "w") as f:
            json.dump(users_data, f, indent=2)
        
        with open(self.teams_file, "w") as f:
            json.dump(teams_data, f, indent=2)
    
    def register_user(self, name: str, email: Optional[str] = None, 
                      role: UserRole = UserRole.MEMBER) -> User:
        """Enregistre un nouvel utilisateur"""
        user_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # Génère une API key
        api_key = f"hw_{secrets.token_urlsafe(32)}"
        
        user = User(
            id=user_id,
            name=name,
            email=email,
            role=role,
            created_at=now,
            last_active=now,
            api_key=api_key
        )
        
        self.users[user_id] = user
        self._save_data()
        
        return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Récupère un utilisateur par ID"""
        return self.users.get(user_id)
    
    def get_user_by_api_key(self, api_key: str) -> Optional[User]:
        """Récupère un utilisateur par API key"""
        for user in self.users.values():
            if user.api_key == api_key:
                return user
        return None
    
    def update_user_activity(self, user_id: str):
        """Met à jour l'activité d'un utilisateur"""
        user = self.users.get(user_id)
        if user:
            user.last_active = datetime.now().isoformat()
            user.session_count += 1
            self._save_data()
    
    def list_users(self) -> List[Dict]:
        """Liste tous les utilisateurs"""
        return [u.to_dict() for u in self.users.values()]
    
    def create_team(self, name: str, owner_id: str) -> Team:
        """Crée une nouvelle équipe"""
        # Vérifie que l'owner existe
        owner = self.users.get(owner_id)
        if not owner:
            raise ValueError(f"Owner not found: {owner_id}")
        
        team_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        team = Team(
            id=team_id,
            name=name,
            owner_id=owner_id,
            created_at=now,
            members={owner_id: UserRole.OWNER}
        )
        
        self.teams[team_id] = team
        self._save_data()
        
        return team
    
    def get_team(self, team_id: str) -> Optional[Team]:
        """Récupère une équipe"""
        return self.teams.get(team_id)
    
    def add_team_member(self, team_id: str, user_id: str, 
                        role: UserRole = UserRole.MEMBER) -> bool:
        """Ajoute un membre à une équipe"""
        team = self.teams.get(team_id)
        user = self.users.get(user_id)
        
        if not team or not user:
            return False
        
        if len(team.members) >= team.max_members:
            raise ValueError("Team is full")
        
        team.members[user_id] = role
        self._save_data()
        
        return True
    
    def remove_team_member(self, team_id: str, user_id: str) -> bool:
        """Retire un membre d'une équipe"""
        team = self.teams.get(team_id)
        if not team:
            return False
        
        if user_id == team.owner_id:
            raise ValueError("Cannot remove team owner")
        
        if user_id in team.members:
            del team.members[user_id]
            self._save_data()
            return True
        
        return False
    
    def generate_invite_code(self, team_id: str, role: UserRole = UserRole.MEMBER,
                            expires_in_days: int = 7) -> str:
        """Génère un code d'invitation"""
        team = self.teams.get(team_id)
        if not team:
            raise ValueError("Team not found")
        
        code = secrets.token_urlsafe(16)
        invite = {
            "code": code,
            "team_id": team_id,
            "role": role.value,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=expires_in_days)).isoformat(),
            "used": False
        }
        
        team.invite_codes.append(code)
        
        # Sauvegarde l'invite séparément
        invites_file = os.path.join(self.storage_path, "invites.json")
        invites = {}
        if os.path.exists(invites_file):
            with open(invites_file) as f:
                invites = json.load(f)
        
        invites[code] = invite
        with open(invites_file, "w") as f:
            json.dump(invites, f, indent=2)
        
        self._save_data()
        
        return code
    
    def join_team_with_code(self, code: str, user_id: str) -> bool:
        """Rejoint une équipe avec un code d'invitation"""
        invites_file = os.path.join(self.storage_path, "invites.json")
        
        if not os.path.exists(invites_file):
            return False
        
        with open(invites_file) as f:
            invites = json.load(f)
        
        invite = invites.get(code)
        if not invite:
            return False
        
        if invite["used"]:
            return False
        
        expires = datetime.fromisoformat(invite["expires_at"])
        if datetime.now() > expires:
            return False
        
        team_id = invite["team_id"]
        role = UserRole(invite["role"])
        
        if self.add_team_member(team_id, user_id, role):
            invite["used"] = True
            invite["used_by"] = user_id
            invite["used_at"] = datetime.now().isoformat()
            
            with open(invites_file, "w") as f:
                json.dump(invites, f, indent=2)
            
            return True
        
        return False
    
    def get_user_teams(self, user_id: str) -> List[Dict]:
        """Récupère les équipes d'un utilisateur"""
        teams = []
        
        for team in self.teams.values():
            if user_id in team.members:
                teams.append({
                    "id": team.id,
                    "name": team.name,
                    "role": team.members[user_id].value,
                    "is_owner": team.owner_id == user_id,
                    "member_count": len(team.members)
                })
        
        return teams
    
    def get_team_members(self, team_id: str) -> List[Dict]:
        """Récupère les membres d'une équipe"""
        team = self.teams.get(team_id)
        if not team:
            return []
        
        members = []
        for user_id, role in team.members.items():
            user = self.users.get(user_id)
            if user:
                members.append({
                    **user.to_dict(),
                    "team_role": role.value
                })
        
        return members
    
    def check_permission(self, user_id: str, permission: Permission) -> bool:
        """Vérifie si un utilisateur a une permission"""
        user = self.users.get(user_id)
        if not user:
            return False
        
        return user.has_permission(permission)
    
    def create_session(self, user_id: str, metadata: Dict = None) -> str:
        """Crée une nouvelle session"""
        session_id = secrets.token_urlsafe(32)
        
        self.active_sessions[session_id] = {
            "id": session_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.update_user_activity(user_id)
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Récupère une session"""
        return self.active_sessions.get(session_id)
    
    def end_session(self, session_id: str):
        """Termine une session"""
        self.active_sessions.pop(session_id, None)
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Nettoie les vieilles sessions"""
        now = datetime.now()
        to_remove = []
        
        for sid, session in self.active_sessions.items():
            created = datetime.fromisoformat(session["created_at"])
            if (now - created).total_seconds() > max_age_hours * 3600:
                to_remove.append(sid)
        
        for sid in to_remove:
            del self.active_sessions[sid]
    
    def get_stats(self) -> Dict:
        """Statistiques globales"""
        return {
            "users": {
                "total": len(self.users),
                "active": sum(1 for u in self.users.values() if u.is_active)
            },
            "teams": {
                "total": len(self.teams),
                "total_members": sum(len(t.members) for t in self.teams.values())
            },
            "sessions": {
                "active": len(self.active_sessions)
            }
        }

class FirstContactHandler:
    """Gère le premier contact avec un utilisateur"""
    
    def __init__(self, team_manager: TeamManager):
        self.tm = team_manager
        self.pending_contacts: Dict[str, Dict] = {}
    
    def initiate_contact(self, contact_id: str, source: str = "unknown") -> Dict:
        """Initie un premier contact"""
        # Vérifie si déjà connu
        for user in self.tm.users.values():
            if user.email == contact_id or user.name == contact_id:
                return {
                    "status": "existing_user",
                    "user_id": user.id,
                    "message": f"Welcome back, {user.name}!"
                }
        
        # Nouveau contact
        self.pending_contacts[contact_id] = {
            "contact_id": contact_id,
            "source": source,
            "step": "awaiting_name",
            "started_at": datetime.now().isoformat()
        }
        
        return {
            "status": "new_user",
            "step": "awaiting_name",
            "message": "Welcome! This is your first time. What's your name?"
        }
    
    def process_response(self, contact_id: str, response: str) -> Dict:
        """Traite la réponse d'un nouveau contact"""
        contact = self.pending_contacts.get(contact_id)
        
        if not contact:
            return {"status": "error", "message": "No pending contact found"}
        
        step = contact.get("step")
        
        if step == "awaiting_name":
            contact["name"] = response.strip()
            contact["step"] = "awaiting_email_optional"
            
            return {
                "status": "ok",
                "step": "awaiting_email_optional",
                "message": f"Nice to meet you, {response.strip()}! Email (optional, press Enter to skip)?"
            }
        
        elif step == "awaiting_email_optional":
            email = response.strip() if response.strip() else None
            contact["email"] = email
            
            # Crée l'utilisateur
            user = self.tm.register_user(
                name=contact["name"],
                email=email,
                role=UserRole.MEMBER
            )
            
            del self.pending_contacts[contact_id]
            
            return {
                "status": "user_created",
                "user_id": user.id,
                "api_key": user.api_key,
                "message": f"Welcome aboard, {user.name}! Your API key: {user.api_key[:20]}..."
            }
        
        return {"status": "error", "message": "Unknown step"}

# Singleton global
_team_manager: Optional[TeamManager] = None
_first_contact: Optional[FirstContactHandler] = None

def get_team_manager() -> TeamManager:
    global _team_manager
    if _team_manager is None:
        _team_manager = TeamManager()
    return _team_manager

def get_first_contact_handler() -> FirstContactHandler:
    global _first_contact
    if _first_contact is None:
        _first_contact = FirstContactHandler(get_team_manager())
    return _first_contact
