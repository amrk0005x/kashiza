# Kashiza - Security Features

## API Key Security

### 1. Encryption at Rest
- All API keys are encrypted using AES-256 via Fernet
- Master key derived using PBKDF2 with 480,000 iterations
- Keys stored in `~/.kashiza/.encrypted_keys` with 0600 permissions

### 2. Obfuscation
- Keys are obfuscated in logs: `sk-abc...xyz` → `sk-***xyz`
- Masking patterns for various key formats
- Secure logging prevents accidental key exposure

### 3. Access Control
- IP whitelisting per key
- Expiration dates for temporary keys
- Usage tracking and audit logs

### 4. Key Rotation
- Automatic key rotation support
- Old key invalidation
- Seamless transition

## Authentication & Authorization

### JWT Tokens
- HS256 algorithm
- 24-hour expiration
- Role-based access control (admin, developer, viewer)

### Request Validation
- Rate limiting (100 requests/minute per IP)
- IP blocking for abuse
- Suspicious pattern detection:
  - Directory traversal (`../`)
  - XSS attempts (`<script`)
  - SQL injection (`union select`)
  - Code injection (`eval(`)

### CORS Protection
- Whitelist-based origins
- Credentials support
- Method restrictions

## WebSocket Security

### Room-based Authorization
- Users can only join authorized rooms
- Project-specific isolation
- Typing/cursor position sharing

### Connection Management
- Client ID tracking
- Automatic cleanup on disconnect
- Broadcast exclusions

## Data Protection

### Environment Variables
- SecureEnv wrapper for key access
- In-memory caching with automatic cleanup
- Fallback to encrypted storage

### Audit Logging
- All key access logged
- Failed attempts tracked
- Security alerts for suspicious activity

## Usage Examples

```python
from core.security import get_security_manager, get_secure_env

# Store API key securely
security = get_security_manager()
key_hash = security.encrypt_api_key(
    service='openai',
    api_key='sk-...',
    ip_whitelist=['192.168.1.0/24'],
    expires_days=90
)

# Access key securely
secure_env = get_secure_env()
api_key = secure_env.get('OPENAI_API_KEY', client_ip='192.168.1.5')

# Mask in logs
masked = secure_env.mask_in_logs("Error with sk-abc123xyz")
# Result: "Error with sk-***xyz"
```

## Security Checklist

- [x] API key encryption
- [x] Key obfuscation in logs
- [x] IP whitelisting
- [x] Rate limiting
- [x] JWT authentication
- [x] Role-based access
- [x] Request validation
- [x] CORS protection
- [x] Audit logging
- [x] Key rotation
- [x] SSL/TLS support
- [x] Suspicious pattern detection
