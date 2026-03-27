import os
import base64
import hashlib
import hmac
import json
import secrets
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import getpass

@dataclass
class APIKey:
    service: str
    key_hash: str
    encrypted_value: bytes
    created_at: str
    last_used: Optional[str] = None
    usage_count: int = 0
    ip_whitelist: List[str] = None
    expires_at: Optional[str] = None

class SecurityManager:
    def __init__(self, master_key: str = None):
        self.master_key = master_key or self._get_master_key()
        self.cipher = self._init_cipher()
        self.api_keys: Dict[str, APIKey] = {}
        self.audit_log: List[Dict] = []
        self._load_keys()
    
    def _get_master_key(self) -> str:
        key_env = os.getenv('HERMES_MASTER_KEY')
        if key_env:
            return key_env
        
        key_file = os.path.expanduser('~/.kashiza/.master_key')
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read().decode()
        
        # Generate new master key
        key = secrets.token_urlsafe(32)
        os.makedirs(os.path.dirname(key_file), exist_ok=True)
        with open(key_file, 'wb') as f:
            f.write(key.encode())
        os.chmod(key_file, 0o600)
        return key
    
    def _init_cipher(self) -> Fernet:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'kashiza_salt_v1',
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
        return Fernet(key)
    
    def _obfuscate_key(self, key: str) -> str:
        """Obfuscate API key for display/logging"""
        if len(key) <= 8:
            return '*' * len(key)
        return key[:4] + '*' * (len(key) - 8) + key[-4:]
    
    def encrypt_api_key(self, service: str, api_key: str, 
                       ip_whitelist: List[str] = None,
                       expires_days: int = None) -> str:
        """Encrypt and store API key securely"""
        encrypted = self.cipher.encrypt(api_key.encode())
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
        
        expires = None
        if expires_days:
            expires = (datetime.now() + timedelta(days=expires_days)).isoformat()
        
        api_key_obj = APIKey(
            service=service,
            key_hash=key_hash,
            encrypted_value=encrypted,
            created_at=datetime.now().isoformat(),
            ip_whitelist=ip_whitelist,
            expires_at=expires
        )
        
        self.api_keys[service] = api_key_obj
        self._save_keys()
        self._audit('key_stored', service, {'hash': key_hash})
        
        return key_hash
    
    def decrypt_api_key(self, service: str, client_ip: str = None) -> Optional[str]:
        """Decrypt API key with security checks"""
        if service not in self.api_keys:
            self._audit('key_access_denied', service, {'reason': 'not_found'})
            return None
        
        key_obj = self.api_keys[service]
        
        # Check expiration
        if key_obj.expires_at:
            if datetime.now() > datetime.fromisoformat(key_obj.expires_at):
                self._audit('key_access_denied', service, {'reason': 'expired'})
                return None
        
        # Check IP whitelist
        if key_obj.ip_whitelist and client_ip:
            if client_ip not in key_obj.ip_whitelist:
                self._audit('key_access_denied', service, {
                    'reason': 'ip_not_whitelisted',
                    'ip': client_ip
                })
                return None
        
        try:
            decrypted = self.cipher.decrypt(key_obj.encrypted_value).decode()
            key_obj.last_used = datetime.now().isoformat()
            key_obj.usage_count += 1
            self._save_keys()
            self._audit('key_accessed', service, {'hash': key_obj.key_hash})
            return decrypted
        except Exception as e:
            self._audit('key_decrypt_failed', service, {'error': str(e)})
            return None
    
    def rotate_key(self, service: str, new_key: str) -> str:
        """Rotate API key"""
        old_hash = self.api_keys.get(service, {}).key_hash if service in self.api_keys else None
        new_hash = self.encrypt_api_key(service, new_key)
        self._audit('key_rotated', service, {'old_hash': old_hash, 'new_hash': new_hash})
        return new_hash
    
    def revoke_key(self, service: str):
        """Revoke API key"""
        if service in self.api_keys:
            del self.api_keys[service]
            self._save_keys()
            self._audit('key_revoked', service, {})
    
    def _save_keys(self):
        keys_file = os.path.expanduser('~/.kashiza/.encrypted_keys')
        os.makedirs(os.path.dirname(keys_file), exist_ok=True)
        
        data = {}
        for service, key_obj in self.api_keys.items():
            data[service] = {
                'service': key_obj.service,
                'key_hash': key_obj.key_hash,
                'encrypted_value': base64.b64encode(key_obj.encrypted_value).decode(),
                'created_at': key_obj.created_at,
                'last_used': key_obj.last_used,
                'usage_count': key_obj.usage_count,
                'ip_whitelist': key_obj.ip_whitelist,
                'expires_at': key_obj.expires_at
            }
        
        with open(keys_file, 'w') as f:
            json.dump(data, f)
        os.chmod(keys_file, 0o600)
    
    def _load_keys(self):
        keys_file = os.path.expanduser('~/.kashiza/.encrypted_keys')
        if not os.path.exists(keys_file):
            return
        
        try:
            with open(keys_file, 'r') as f:
                data = json.load(f)
            
            for service, key_data in data.items():
                self.api_keys[service] = APIKey(
                    service=key_data['service'],
                    key_hash=key_data['key_hash'],
                    encrypted_value=base64.b64decode(key_data['encrypted_value']),
                    created_at=key_data['created_at'],
                    last_used=key_data.get('last_used'),
                    usage_count=key_data.get('usage_count', 0),
                    ip_whitelist=key_data.get('ip_whitelist'),
                    expires_at=key_data.get('expires_at')
                )
        except Exception as e:
            print(f"Warning: Could not load encrypted keys: {e}")
    
    def _audit(self, action: str, service: str, details: Dict):
        self.audit_log.append({
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'service': service,
            'details': details
        })
    
    def get_key_info(self, service: str = None) -> List[Dict]:
        """Get info about stored keys (without revealing values)"""
        keys = []
        for svc, key_obj in self.api_keys.items():
            if service and svc != service:
                continue
            keys.append({
                'service': svc,
                'key_hash': key_obj.key_hash,
                'created_at': key_obj.created_at,
                'last_used': key_obj.last_used,
                'usage_count': key_obj.usage_count,
                'expires_at': key_obj.expires_at,
                'status': 'active' if not key_obj.expires_at or 
                         datetime.now() < datetime.fromisoformat(key_obj.expires_at) else 'expired'
            })
        return keys
    
    def verify_environment_keys(self) -> Dict[str, bool]:
        """Verify that required API keys are present in environment"""
        required_keys = [
            'ANTHROPIC_API_KEY',
            'OPENAI_API_KEY',
            'GROQ_API_KEY',
            'ELEVENLABS_API_KEY'
        ]
        
        results = {}
        for key in required_keys:
            value = os.getenv(key)
            if value:
                # Store securely if not already stored
                if key.lower().replace('_api_key', '') not in self.api_keys:
                    self.encrypt_api_key(
                        key.lower().replace('_api_key', ''),
                        value
                    )
                results[key] = True
            else:
                results[key] = False
        
        return results

class SecureEnv:
    """Secure environment variable manager"""
    
    def __init__(self, security_manager: SecurityManager):
        self.security = security_manager
        self._cache: Dict[str, str] = {}
    
    def get(self, key: str, client_ip: str = None) -> Optional[str]:
        """Get API key securely"""
        # Check cache first
        if key in self._cache:
            return self._cache[key]
        
        # Try to get from secure storage
        service = key.lower().replace('_api_key', '').replace('api_key_', '')
        decrypted = self.security.decrypt_api_key(service, client_ip)
        
        if decrypted:
            self._cache[key] = decrypted
            return decrypted
        
        # Fall back to environment
        return os.getenv(key)
    
    def clear_cache(self):
        """Clear key cache"""
        self._cache.clear()
    
    def mask_in_logs(self, text: str) -> str:
        """Mask API keys in log messages"""
        import re
        
        # Mask patterns like sk-..., ant-..., etc.
        patterns = [
            (r'sk-[a-zA-Z0-9]{48}', 'sk-***'),
            (r'ant-api[0-9a-zA-Z-_]{30,}', 'ant-api***'),
            (r'gsk_[a-zA-Z0-9]{32}', 'gsk_***'),
            (r'[0-9a-f]{64}', '***'),
        ]
        
        result = text
        for pattern, replacement in patterns:
            result = re.sub(pattern, replacement, result)
        
        return result

class RequestValidator:
    """Validate incoming requests for security"""
    
    def __init__(self):
        self.rate_limits: Dict[str, List[float]] = {}
        self.blocked_ips: set = set()
        self.suspicious_patterns = [
            r'\.\./',  # Directory traversal
            r'<script',  # XSS
            r'union\s+select',  # SQL injection
            r'eval\s*\(',  # Code injection
        ]
    
    def validate_request(self, client_ip: str, headers: Dict, 
                        body: str = None) -> Dict:
        """Validate request for security issues"""
        issues = []
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            return {'valid': False, 'reason': 'IP blocked'}
        
        # Rate limiting
        now = datetime.now().timestamp()
        if client_ip not in self.rate_limits:
            self.rate_limits[client_ip] = []
        
        # Clean old requests (older than 1 minute)
        self.rate_limits[client_ip] = [
            t for t in self.rate_limits[client_ip] 
            if now - t < 60
        ]
        
        # Check limit (100 requests per minute)
        if len(self.rate_limits[client_ip]) > 100:
            self.blocked_ips.add(client_ip)
            return {'valid': False, 'reason': 'Rate limit exceeded'}
        
        self.rate_limits[client_ip].append(now)
        
        # Check for suspicious patterns
        if body:
            import re
            for pattern in self.suspicious_patterns:
                if re.search(pattern, body, re.IGNORECASE):
                    issues.append(f'Suspicious pattern detected: {pattern}')
        
        # Validate headers
        user_agent = headers.get('user-agent', '')
        if not user_agent or len(user_agent) < 5:
            issues.append('Missing or invalid User-Agent')
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }

# Global security instance
_security_manager = None
_secure_env = None

def get_security_manager() -> SecurityManager:
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager

def get_secure_env() -> SecureEnv:
    global _secure_env
    if _secure_env is None:
        _secure_env = SecureEnv(get_security_manager())
    return _secure_env
