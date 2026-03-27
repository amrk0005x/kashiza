# Kashiza v2.2

**Advanced Multi-Agent Orchestration System** with enterprise-grade security.

**Supported AI Providers**: Anthropic (Claude) | OpenAI (GPT) | Google (Gemini) | Groq | Kimi | DeepSeek | Ollama (Local) | OpenRouter

## Quick Start

### Fresh Install (Production)

```bash
# One-liner install (Ubuntu/Debian)
curl -fsSL https://raw.githubusercontent.com/amrk0005x/kashiza/main/deploy/quick-install.sh | sudo bash

# Or manual install
git clone https://github.com/amrk0005x/kashiza.git
cd kashiza
sudo bash deploy/fresh-install.sh
```

### Development Install

```bash
# Clone repository
git clone https://github.com/amrk0005x/kashiza.git
cd kashiza

# Install dependencies
pip install -r requirements.txt

# Start server
python -c "from api.enhanced_server import main; main()"

# Or interactive CLI
python run_cli.py
```

### Docker Install

```bash
docker-compose -f deploy/docker-compose.yml up -d
```

**Dashboard**: http://localhost:8080

See [docs/INSTALL.md](docs/INSTALL.md) for detailed installation guide.

## Configuration

### AI Provider Setup

Add at least one API key to `.env`:

```bash
# Cloud Providers (pick at least one)
ANTHROPIC_API_KEY=sk-ant-...           # Claude models
OPENAI_API_KEY=sk-...                   # GPT models
GOOGLE_API_KEY=...                      # Gemini models
GROQ_API_KEY=gsk_...                    # Fast Llama/Mixtral
KIMI_API_KEY=...                        # Moonshot AI
DEEPSEEK_API_KEY=sk-...                 # DeepSeek models
OPENROUTER_API_KEY=sk-or-...            # Unified API access

# Local (optional - free, private)
OLLAMA_HOST=http://localhost:11434
```

See [docs/PROVIDERS.md](docs/PROVIDERS.md) for detailed setup instructions.

## API Endpoints

### Authentication
```bash
POST /auth/login                    # Get JWT token
GET  /auth/verify                   # Verify token
```

### Security
```bash
POST /security/keys/store           # Store API key securely
GET  /security/keys                 # List keys (obfuscated)
POST /security/keys/{svc}/rotate    # Rotate key
```

### Agents & Orchestration
```bash
GET  /api/agents                    # List agents
POST /api/orchestrate               # Execute with auto-selection
POST /api/orchestrate/analyze       # Analyze prompt
```

### Git Integration
```bash
GET  /api/git/status                # Git status
POST /api/git/commit                # Smart commit
POST /api/git/push                  # Push
POST /api/git/pr/create             # Create PR
GET  /api/git/pr/list               # List PRs
```

### WebSocket
```
ws://localhost:8080/ws/{client_id}
```

## Security Features

### API Key Encryption
```python
from core.security import get_security_manager

security = get_security_manager()

# Store with encryption
security.encrypt_api_key(
    service='openai',
    api_key='sk-...',
    ip_whitelist=['192.168.1.0/24'],
    expires_days=90
)

# Access (decrypted on-the-fly)
key = security.decrypt_api_key('openai', client_ip='192.168.1.5')
```

### Key Obfuscation
All API keys are automatically obfuscated in logs:
```
sk-abc123def456 → sk-***def456
```

### Authentication
- JWT tokens with 24h expiration
- Role-based access control
- Rate limiting (100 req/min)
- Request validation
- Suspicious pattern detection

## Plugin System

### Create a Plugin
```python
from core.plugin import Plugin, PluginMetadata

class MyPlugin(Plugin):
    metadata = PluginMetadata(
        name="my_plugin",
        version="1.0.0",
        author="You",
        description="My plugin",
        hooks=['post_orchestrate'],
        dependencies=[]
    )
    
    @Plugin.on('post_orchestrate')
    def after_task(self, context):
        print(f"Task completed: {context}")
        return {'processed': True}

plugin = MyPlugin()
```

### Available Hooks
- `pre_orchestrate` / `post_orchestrate`
- `pre_tool_call` / `post_tool_call`
- `pre_agent_execute` / `post_agent_execute`
- `on_error`, `on_cost_threshold`, `on_quality_low`
- `on_security_alert`, `on_task_complete`, `on_config_change`

## Git Integration

```python
from skills.git_integration import GitManager

git = GitManager('/path/to/repo')

# Smart commit (auto-generated message)
git.smart_commit(message="Optional custom message")

# Create PR
git.create_pr(
    repo="owner/repo",
    title="Feature: Add auth",
    body="Description...",
    head_branch="feature/auth"
)

# Analyze diff
analysis = git.analyze_diff()
print(f"Files changed: {analysis['files_changed']}")
```

## Project Templates

```bash
# List templates
python run.py templates

# Create from template
python run.py create web_api my_project --path ./my_api
```

Available templates:
- `web_api` - FastAPI + PostgreSQL + Docker
- `react_app` - React + TypeScript + Tailwind
- `python_cli` - CLI tool with Click
- `ml_training` - PyTorch training pipeline

## Team Collaboration

```python
from core.team_collab import TeamCollaboration

team = TeamCollaboration()

# Create team
alice = team.create_member("Alice", "alice@example.com", "developer")
bob = team.create_member("Bob", "bob@example.com", "manager")

# Create project
project = team.create_project("AI Platform", "Description", bob.id)
team.add_project_member(project.id, alice.id, bob.id)

# Create and assign task
task = team.create_task(
    project_id=project.id,
    title="Design API",
    description="Create API spec",
    creator_id=bob.id,
    assignee_id=alice.id
)
```

## Configuration

Edit `config/wrapper.yaml`:
```yaml
# Budget
daily_budget: 10.0
monthly_budget: 100.0

# Quality
target_quality: 7.0
auto_correct: true

# Security
rate_limit: 100
circuit_breaker_threshold: 5
```

## File Structure

```
kashiza/
├── core/
│   ├── orchestrator.py         # Multi-agent orchestration
│   ├── cost_tracker.py         # Cost tracking
│   ├── auto_debugger.py        # Error handling
│   ├── team_collab.py          # Team collaboration
│   ├── self_monitor.py         # Self-monitoring
│   ├── plugin.py               # Plugin system
│   ├── security.py             # Security features ⭐
│   └── optimizations.py        # Performance
├── skills/
│   ├── pc_control/
│   ├── ab_testing/
│   ├── voice/
│   └── git_integration/        # Git operations ⭐
├── api/
│   ├── server.py
│   └── enhanced_server.py      # Enhanced API 
├── mobile_api/
│   └── routes.py               # Mobile endpoints
├── web/
│   ├── dashboard.html
│   └── enhanced_dashboard.html # Enhanced UI 
├── templates/
│   └── engine.py
├── market/
│   └── store.py
├── plugins/
│   └── example_plugin.py       # Example plugin 
├── config/
│   └── wrapper.yaml
└── examples/
    └── basic_usage.py
```

## Environment Variables

```bash
# Required
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."

# Security (optional)
export HERMES_MASTER_KEY="your-master-key"
export JWT_SECRET="your-jwt-secret"
export SSL_KEYFILE="/path/to/key.pem"
export SSL_CERTFILE="/path/to/cert.pem"
```

## Dashboard

Access at `http://localhost:8080`

Features:
- Real-time collaboration (WebSocket)
- Live activity feed
- Security management
- Plugin control
- Cost tracking
- Team overview

## Uninstall

To completely remove Kashiza from your system:

```bash
# Easy uninstall
kashiza uninstall

# Or run directly
sudo bash /opt/kashiza/deploy/uninstall.sh
```

This will:
- Stop and remove the service
- Remove all files in `/opt/kashiza`
- Remove CLI commands
- Clean up firewall rules
- Optionally remove backups

## License

MIT
