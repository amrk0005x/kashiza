#!/usr/bin/env python3
"""
Demo complète du Kashiza v3.0
Montre toutes les features: Conditioning, Skills, Teams, Security
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.orchestrator import AgentOrchestrator, AgentRole, ExecutionMode
from core.conditioning import ConditioningManager, ConditioningMode
from core.skill_adapter import SkillAdapter
from core.team_manager import TeamManager, FirstContactHandler, UserRole
from core.security import SecurityManager, SecurityLevel

async def demo_conditioning():
    """Démo du système de conditioning"""
    print("\n" + "="*60)
    print("🎯 DEMO: Conditioning System")
    print("="*60)
    
    cm = ConditioningManager()
    
    # Liste les modes disponibles
    print("\n📋 Available conditioning modes:")
    for mode in cm.list_modes():
        status = "✅ ACTIVE" if mode["active"] else ""
        print(f"   {mode['icon']} /{mode['mode']:12} - {mode['name']} {status}")
    
    # Active le mode dev
    print("\n💻 Activating /dev mode...")
    template = cm.activate_mode(ConditioningMode.DEV)
    print(f"   System prompt: {template.system_prompt[:100]}...")
    
    # Wrap un prompt
    user_prompt = "Crée une fonction de tri rapide"
    wrapped = cm.wrap_prompt(user_prompt)
    print(f"\n   Original: {user_prompt}")
    print(f"   Wrapped:\n{wrapped[:300]}...")
    
    # Active le mode marketing
    print("\n📈 Switching to /marketing mode...")
    template = cm.activate_mode(ConditioningMode.MARKETING)
    print(f"   Description: {template.description}")
    print(f"   Temperature: {template.temperature}")
    
    cm.deactivate()
    print("\n✅ Conditioning demo complete")

async def demo_skills():
    """Démo de l'adaptateur de skills"""
    print("\n" + "="*60)
    print("🔌 DEMO: Skill Adapter (Hermes + OpenClaw + Native)")
    print("="*60)
    
    adapter = SkillAdapter()
    
    # Découverte
    print("\n🔍 Discovering skills...")
    skills = adapter.discover_skills()
    
    by_source = {}
    for skill in skills:
        source = skill.source.value
        by_source[source] = by_source.get(source, 0) + 1
    
    for source, count in by_source.items():
        print(f"   • {source}: {count} skills")
    
    # Affiche quelques skills
    print("\n📦 Sample skills:")
    for skill in skills[:5]:
        print(f"   • {skill.name} ({skill.source.value} v{skill.version})")
        print(f"     {skill.description[:60]}...")
    
    # Crée un template de skill wrapper
    print("\n📝 Creating wrapper skill template...")
    template_path = adapter.create_wrapper_skill_template(
        "my_custom_skill",
        "A custom skill for demonstration"
    )
    print(f"   Created at: {template_path}")
    
    print("\n✅ Skills demo complete")

async def demo_teams():
    """Démo de la gestion d'équipe"""
    print("\n" + "="*60)
    print("👥 DEMO: Team Collaboration")
    print("="*60)
    
    tm = TeamManager()
    
    # Premier contact
    print("\n🆕 First contact simulation...")
    fch = FirstContactHandler(tm)
    
    contact_id = "demo_user_123"
    result = fch.initiate_contact(contact_id, "demo")
    print(f"   Status: {result['status']}")
    print(f"   Message: {result['message']}")
    
    # Répond avec le nom
    result = fch.process_response(contact_id, "Alice")
    print(f"\n   After name response:")
    print(f"   Step: {result['step']}")
    print(f"   Message: {result['message']}")
    
    # Répond avec l'email
    result = fch.process_response(contact_id, "alice@example.com")
    print(f"\n   After email response:")
    print(f"   Status: {result['status']}")
    print(f"   User ID: {result['user_id']}")
    print(f"   API Key: {result['api_key'][:20]}...")
    
    # Crée une équipe
    print("\n👥 Creating team...")
    user_id = result['user_id']
    team = tm.create_team("Demo Team", user_id)
    print(f"   Team: {team.name} ({team.id[:8]}...)")
    
    # Génère un code d'invitation
    invite_code = tm.generate_invite_code(team.id, UserRole.MEMBER)
    print(f"   Invite code: {invite_code}")
    
    # Crée un autre utilisateur et le fait rejoindre
    print("\n📝 Creating second user...")
    user2 = tm.register_user("Bob", "bob@example.com")
    print(f"   User: {user2.name} ({user2.id[:8]}...)")
    
    success = tm.join_team_with_code(invite_code, user2.id)
    print(f"   Joined team: {success}")
    
    # Liste les équipes
    print("\n📊 Team statistics:")
    stats = tm.get_stats()
    for key, value in stats.items():
        print(f"   • {key}: {value}")
    
    print("\n✅ Team demo complete")

async def demo_security():
    """Démo du système de sécurité"""
    print("\n" + "="*60)
    print("🔒 DEMO: Security & Pairing")
    print("="*60)
    
    sm = SecurityManager()
    
    # Affiche les niveaux de sécurité
    print("\n🛡️  Security levels:")
    for level in SecurityLevel:
        policy = sm.get_policy(level)
        print(f"   • {level.value.upper():10} - {policy.name}")
        print(f"     Rate limit: {policy.rate_limit_per_minute}/min")
        print(f"     Session timeout: {policy.session_timeout_minutes}min")
        print(f"     Audit: {'✅' if policy.audit_all_actions else '❌'}")
        if policy.require_pairing:
            print(f"     Pairing: Required")
    
    # Simulation de pairing
    print("\n📱 Device pairing simulation...")
    
    # Crée un utilisateur
    tm = TeamManager()
    user = tm.register_user("Security Demo User")
    
    # Demande de pairing
    device_info = {
        "name": "iPhone Demo",
        "os": "iOS 17",
        "browser": "Safari"
    }
    
    request = sm.pairing.create_pairing_request(user.id, device_info)
    print(f"   Pairing code: {request['pairing_code']}")
    print(f"   Expires in: {request['expires_in']}s")
    
    # Confirmation
    result = sm.pairing.confirm_pairing(request['pairing_code'], user.id)
    if result and result.get("status") == "success":
        print(f"   ✅ Device paired!")
        print(f"   Device token: {result['device_token'][:20]}...")
    
    # Vérification
    devices = sm.pairing.list_user_devices(user.id)
    print(f"\n   Paired devices: {len(devices)}")
    for device in devices:
        print(f"   • {device['device_info']['name']} ({device['trust_level']})")
    
    # Check d'opération
    print("\n🔍 Security check simulation...")
    check = sm.check_operation(
        operation="delete_agent",
        user_id=user.id,
        device_token=result['device_token'] if result else None,
        user_level=SecurityLevel.HIGH
    )
    print(f"   Operation: delete_agent")
    print(f"   Allowed: {check['allowed']}")
    if not check['allowed'] and check.get('pending_approval'):
        print(f"   ⚠️  Approval required (ID: {check['approval_id'][:8]}...)")
    
    # Statut de sécurité
    print("\n📊 Security status:")
    status = sm.get_user_security_status(user.id, result['device_token'] if result else None)
    print(f"   Paired devices: {status['paired_devices']}")
    print(f"   Device verified: {status['device_verified']}")
    if status['recommendations']:
        print(f"   Recommendations:")
        for rec in status['recommendations']:
            print(f"     • {rec}")
    
    print("\n✅ Security demo complete")

async def demo_orchestrator():
    """Démo de l'orchestrateur multi-agent"""
    print("\n" + "="*60)
    print("🤖 DEMO: Multi-Agent Orchestration")
    print("="*60)
    
    orch = AgentOrchestrator()
    
    # Crée des agents
    print("\n👤 Creating agents...")
    coder = orch.create_agent("python-coder", "python-dev", "gpt-4o", AgentRole.WORKER)
    reviewer = orch.create_agent("code-reviewer", "review", "gpt-4o-mini", AgentRole.REVIEWER)
    architect = orch.create_agent("architect", "design", "gpt-4o", AgentRole.PLANNER)
    
    print(f"   Created: {coder.name}, {reviewer.name}, {architect.name}")
    
    # Liste les agents
    print("\n📋 Agent list:")
    for agent in orch.list_agents():
        print(f"   • {agent['name']} ({agent['role']}) - {agent['specialty']}")
    
    # Simule une exécution (en vrai, ça appellerait les LLMs)
    print("\n⚡ Simulating task execution...")
    print("   Mode: HIERARCHICAL")
    print("   Task: Design and implement a REST API")
    print("   Agents: architect (manager) → coder (worker)")
    
    # Note: En vrai on ferait:
    # result = await orch.execute_task(
    #     description="Create a REST API",
    #     agents=[architect, coder, reviewer],
    #     mode=ExecutionMode.HIERARCHICAL
    # )
    
    print("\n   [Simulation output would appear here...]")
    print("   - Architect creates plan")
    print("   - Coder implements endpoints")  
    print("   - Reviewer validates code")
    print("   - Final output delivered")
    
    print("\n✅ Orchestrator demo complete")

async def main():
    """Lance toutes les démos"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   🔱 Kashiza v3.0 - Complete Feature Demo                 ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    await demo_conditioning()
    await demo_skills()
    await demo_teams()
    await demo_security()
    await demo_orchestrator()
    
    print("\n" + "="*60)
    print("🎉 All demos completed successfully!")
    print("="*60)
    print("""
Next steps:
  1. Start the server: python run.py
  2. Open dashboard: http://localhost:8080
  3. Register a user: POST /api/users/register
  4. Try conditioning: POST /api/conditioning/activate
  5. Execute tasks: POST /api/tasks

Documentation: See README.md
    """)

if __name__ == "__main__":
    asyncio.run(main())
