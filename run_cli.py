#!/usr/bin/env python3
"""
Kashiza v2.1 - CLI Mode (No FastAPI required)
Demonstrates all features without web server dependencies
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.orchestrator import AgentOrchestrator, AgentRole, ExecutionMode
from core.conditioning import ConditioningManager, ConditioningMode
from core.skill_adapter import SkillAdapter
from core.team_manager import TeamManager, FirstContactHandler, UserRole
from core.security import SecurityManager, SecurityLevel

BANNER = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   ██╗  ██╗ █████╗ ███████╗██╗  ██╗██╗███████╗ █████╗             ║
║   ██║ ██╔╝██╔══██╗██╔════╝██║  ██║██║╚══███╔╝██╔══██╗            ║
║   █████╔╝ ███████║███████╗███████║██║  ███╔╝ ███████║            ║
║   ██╔═██╗ ██╔══██║╚════██║██╔══██║██║ ███╔╝  ██╔══██║            ║
║   ██║  ██╗██║  ██║███████║██║  ██║██║███████╗██║  ██║            ║
║   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝            ║
║                                                                  ║
║   Kashiza v2.2 - Multi-Agent Orchestration Platform              ║
║   Anthropic | OpenAI | Google | Groq | Kimi | DeepSeek           ║
║   Ollama (Local) | OpenRouter                                    ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║   Available Commands:                                            ║
║   • mode <name>     - Activate conditioning mode                 ║
║   • agents          - List/create agents                         ║
║   • task            - Execute multi-agent task                   ║
║   • skills          - List/load skills                           ║
║   • providers       - List AI providers and models               ║
║   • user            - User/team management                       ║
║   • pair            - Device pairing                             ║
║   • demo            - Run full feature demo                      ║
║   • quit            - Exit                                       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

class KashizaCLI:
    def __init__(self):
        self.orch = AgentOrchestrator()
        self.conditioning = ConditioningManager()
        self.skills = SkillAdapter()
        self.team = TeamManager()
        self.security = SecurityManager()
        self.first_contact = FirstContactHandler(self.team)
        self.current_user = None
        
        # Create default agents
        self._create_default_agents()
    
    def _create_default_agents(self):
        """Create default agents"""
        configs = [
            ("general", "general", "gpt-4o-mini", AgentRole.WORKER),
            ("coder", "python", "gpt-4o", AgentRole.WORKER),
            ("reviewer", "code-review", "gpt-4o-mini", AgentRole.REVIEWER),
            ("architect", "system-design", "gpt-4o", AgentRole.PLANNER),
        ]
        for name, specialty, model, role in configs:
            self.orch.create_agent(name, specialty, model, role)
    
    def run(self):
        """Main loop"""
        print(BANNER)
        
        while True:
            try:
                prompt = "🔱"
                if self.conditioning.active_mode:
                    prompt = f"{self.conditioning.active_template.icon}"
                if self.current_user:
                    prompt += f" {self.current_user.name}"
                prompt += "> "
                
                cmd = input(prompt).strip()
                
                if not cmd:
                    continue
                
                parts = cmd.split()
                action = parts[0].lower()
                args = parts[1:]
                
                if action == "quit":
                    print("👋 Goodbye!")
                    break
                elif action == "mode":
                    self.handle_mode(args)
                elif action == "agents":
                    self.handle_agents(args)
                elif action == "task":
                    self.handle_task(args)
                elif action == "skills":
                    self.handle_skills(args)
                elif action == "user":
                    self.handle_user(args)
                elif action == "pair":
                    self.handle_pairing(args)
                elif action == "demo":
                    self.run_demo()
                elif action == "providers":
                    self.handle_providers(args)
                elif action == "help":
                    self.show_help()
                else:
                    print(f"Unknown command: {action}. Type 'help' for commands.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def handle_mode(self, args):
        """Handle conditioning modes"""
        if not args:
            print("\n📋 Available modes:")
            for mode in self.conditioning.list_modes():
                status = "✅ ACTIVE" if mode["active"] else ""
                print(f"  {mode['icon']} /{mode['mode']:12} - {mode['name']} {status}")
            print("\nUsage: mode <mode_name>")
            return
        
        mode_name = args[0].lower()
        try:
            mode = ConditioningMode(mode_name)
            template = self.conditioning.activate_mode(mode)
            print(f"\n✅ Activated {template.icon} {template.name} mode")
            print(f"   Temperature: {template.temperature}")
            print(f"   Description: {template.description}")
        except ValueError:
            print(f"❌ Unknown mode: {mode_name}")
    
    def handle_agents(self, args):
        """Handle agent commands"""
        if not args or args[0] == "list":
            print("\n🤖 Agents:")
            for agent in self.orch.list_agents():
                print(f"  • {agent['name']:15} ({agent['role']:10}) - {agent['specialty']}")
        elif args[0] == "create":
            if len(args) < 3:
                print("Usage: agents create <name> <specialty> [model]")
                return
            name, specialty = args[1], args[2]
            model = args[3] if len(args) > 3 else "gpt-4o-mini"
            agent = self.orch.create_agent(name, specialty, model, AgentRole.WORKER)
            print(f"✅ Created agent: {agent.name}")
    
    def handle_task(self, args):
        """Handle task execution"""
        import asyncio
        
        print("\n⚡ Execute Task")
        print(f"Available agents: {', '.join(a.name for a in self.orch.agents.values())}")
        
        description = input("Task description: ").strip()
        if not description:
            print("❌ Description required")
            return
        
        agent_names = input("Agent names (comma-separated): ").strip().split(",")
        agents = []
        for name in agent_names:
            name = name.strip()
            for agent in self.orch.agents.values():
                if agent.name == name:
                    agents.append(agent)
                    break
        
        if not agents:
            print("❌ No valid agents selected")
            return
        
        mode_input = input("Mode (sequential/parallel/collaborative/hierarchical): ").strip()
        mode_map = {
            "sequential": ExecutionMode.SEQUENTIAL,
            "parallel": ExecutionMode.PARALLEL,
            "collaborative": ExecutionMode.COLLABORATIVE,
            "hierarchical": ExecutionMode.HIERARCHICAL
        }
        mode = mode_map.get(mode_input, ExecutionMode.SEQUENTIAL)
        
        print(f"\n🚀 Executing with {len(agents)} agents in {mode.value} mode...")
        
        # Apply conditioning if active
        if self.conditioning.active_mode:
            description = self.conditioning.wrap_prompt(description)
        
        # Run async
        async def run():
            return await self.orch.execute_task(description, agents, mode)
        
        try:
            result = asyncio.run(run())
            print(f"\n✅ Task completed!")
            print(f"   Mode: {result.get('mode')}")
            print(f"   Results: {len(result.get('results', []))} agent responses")
        except Exception as e:
            print(f"❌ Task failed: {e}")
    
    def handle_skills(self, args):
        """Handle skill commands"""
        if not args or args[0] == "list":
            print("\n🔌 Skills:")
            skills = self.skills.discover_skills()
            for skill in skills[:10]:
                print(f"  • {skill.name:20} ({skill.source.value:8}) v{skill.version}")
            if len(skills) > 10:
                print(f"  ... and {len(skills) - 10} more")
        elif args[0] == "load" and len(args) > 1:
            skill = self.skills.load_skill(args[1])
            if skill:
                print(f"✅ Loaded skill: {skill.name}")
            else:
                print(f"❌ Skill not found: {args[1]}")
    
    def handle_providers(self, args):
        """Handle AI provider commands"""
        from core.providers import get_provider_manager, ProviderType
        
        pm = get_provider_manager()
        
        if not args or args[0] == "list":
            print("\n🤖 AI Providers:")
            print("=" * 60)
            
            providers = pm.list_available_providers()
            if not providers:
                print("  ⚠️  No providers configured")
                print("\n  Set API keys in .env file:")
                print("  • ANTHROPIC_API_KEY - for Claude models")
                print("  • OPENAI_API_KEY - for GPT models")
                print("  • GOOGLE_API_KEY - for Gemini models")
                print("  • GROQ_API_KEY - for fast Llama/Mixtral")
                print("  • KIMI_API_KEY - for Moonshot AI")
                print("  • DEEPSEEK_API_KEY - for DeepSeek models")
                print("  • OPENROUTER_API_KEY - for unified access")
                print("  • OLLAMA_HOST - for local models (optional)")
                return
            
            for provider in providers:
                status = "✅" if pm.is_provider_available(provider.type) else "❌"
                print(f"\n  {status} {provider.name}")
                
                # Show available models
                models = pm.list_models_by_provider(provider.type)
                available_models = [m for m in models if pm.is_model_available(m.id)]
                for model in available_models[:5]:
                    price = f"${model.input_price}/1k" if model.input_price > 0 else "FREE"
                    print(f"      • {model.name:25} ({price})")
                if len(available_models) > 5:
                    print(f"      ... and {len(available_models) - 5} more")
            
            # Summary
            all_available = pm.list_available_models()
            print(f"\n" + "=" * 60)
            print(f"Total: {len(all_available)} models available")
            
        elif args[0] == "models":
            print("\n📋 All Available Models:")
            print("=" * 80)
            print(f"{'Model':<30} {'Provider':<12} {'Price/1k':<12} {'Quality':<8} {'Speed':<8}")
            print("-" * 80)
            
            models = pm.list_available_models()
            for model in sorted(models, key=lambda m: (m.provider.value, m.name)):
                price = f"${model.input_price:.4f}" if model.input_price > 0 else "FREE"
                print(f"{model.name:<30} {model.provider.value:<12} {price:<12} "
                      f"{model.quality_score:<8} {model.speed_score:<8}")
            
        elif args[0] == "recommend":
            complexity = args[1] if len(args) > 1 else "medium"
            priority = args[2] if len(args) > 2 else "balanced"
            
            recommended = pm.recommend_model(complexity, priority)
            print(f"\n🎯 Recommended model for {complexity} complexity ({priority} priority):")
            print(f"   Model: {recommended}")
            
            model_info = pm.get_model(recommended)
            if model_info:
                print(f"   Provider: {model_info.provider.value}")
                print(f"   Quality: {model_info.quality_score}/10")
                print(f"   Speed: {model_info.speed_score}/10")
                print(f"   Price: ${model_info.input_price}/1k tokens")
                
        elif args[0] == "compare":
            print("\n📊 Model Comparison:")
            print("=" * 90)
            comparison = pm.get_model_comparison()
            print(f"{'Model':<25} {'Provider':<12} {'Price In':<10} {'Price Out':<10} {'Q':<3} {'S':<3}")
            print("-" * 90)
            for m in sorted(comparison, key=lambda x: (x['provider'], x['name'])):
                avail = "✅" if m['available'] else "❌"
                price_in = pm.format_price(m['input_price'])
                price_out = pm.format_price(m['output_price'])
                print(f"{avail} {m['name']:<22} {m['provider']:<12} {price_in:<10} "
                      f"{price_out:<10} {m['quality']:<3} {m['speed']:<3}")
        
        elif args[0] == "test" and len(args) > 1:
            provider_name = args[1].lower()
            print(f"\n🧪 Testing {provider_name} connection...")
            
            provider_map = {
                "anthropic": ProviderType.ANTHROPIC,
                "openai": ProviderType.OPENAI,
                "google": ProviderType.GOOGLE,
                "groq": ProviderType.GROQ,
                "kimi": ProviderType.KIMI,
                "deepseek": ProviderType.DEEPSEEK,
                "ollama": ProviderType.OLLAMA,
                "openrouter": ProviderType.OPENROUTER,
            }
            
            pt = provider_map.get(provider_name)
            if not pt:
                print(f"❌ Unknown provider: {provider_name}")
                print(f"   Available: {', '.join(provider_map.keys())}")
                return
            
            if pm.is_provider_available(pt):
                api_key = pm.get_api_key(pt)
                base_url = pm.get_base_url(pt)
                print(f"✅ {provider_name} is configured")
                if api_key:
                    masked = api_key[:10] + "..." if len(api_key) > 10 else "***"
                    print(f"   Key: {masked}")
                if base_url:
                    print(f"   URL: {base_url}")
                
                # List available models
                models = pm.list_models_by_provider(pt)
                available = [m for m in models if pm.is_model_available(m.id)]
                print(f"   Models: {len(available)} available")
                for m in available[:3]:
                    print(f"      • {m.name}")
            else:
                print(f"❌ {provider_name} is not configured")
                provider = pm.get_provider(pt)
                if provider:
                    print(f"   Set {provider.api_key_env} in .env")
        
        else:
            print("\nUsage: providers [list|models|recommend|compare|test <provider>]")
            print("  list           - List configured providers")
            print("  models         - List all available models")
            print("  recommend      - Get model recommendation")
            print("  compare        - Compare all models")
            print("  test <name>    - Test provider configuration")
    
    def handle_user(self, args):
        """Handle user/team commands"""
        if not args:
            if self.current_user:
                print(f"\n👤 Current user: {self.current_user.name}")
                teams = self.team.get_user_teams(self.current_user.id)
                print(f"   Teams: {len(teams)}")
                for t in teams:
                    print(f"     • {t['name']} ({t['role']})")
            else:
                print("\nNo user logged in. Use: user register <name>")
            return
        
        if args[0] == "register" and len(args) > 1:
            name = args[1]
            email = args[2] if len(args) > 2 else None
            user = self.team.register_user(name, email)
            self.current_user = user
            print(f"\n✅ User registered: {user.name}")
            print(f"   API Key: {user.api_key}")
            print(f"   ⚠️  Save this API key - it won't be shown again!")
        
        elif args[0] == "login" and len(args) > 1:
            # Simulate login with name
            for user in self.team.users.values():
                if user.name == args[1]:
                    self.current_user = user
                    print(f"✅ Logged in as: {user.name}")
                    return
            print("❌ User not found")
        
        elif args[0] == "team" and args[1] == "create" and len(args) > 2:
            if not self.current_user:
                print("❌ Login first: user login <name>")
                return
            team = self.team.create_team(args[2], self.current_user.id)
            print(f"✅ Created team: {team.name}")
    
    def handle_pairing(self, args):
        """Handle device pairing"""
        if not self.current_user:
            print("❌ Login first: user login <name>")
            return
        
        if not args or args[0] == "request":
            device_info = {"name": "CLI Device", "os": "Unknown"}
            result = self.security.pairing.create_pairing_request(
                self.current_user.id, device_info
            )
            print(f"\n📱 Pairing Request")
            print(f"   Code: {result['pairing_code']}")
            print(f"   Expires in: {result['expires_in']}s")
            print(f"   Use: pair confirm {result['pairing_code']}")
        
        elif args[0] == "confirm" and len(args) > 1:
            result = self.security.pairing.confirm_pairing(args[1], self.current_user.id)
            if result and result.get("status") == "success":
                print(f"✅ Device paired!")
                print(f"   Token: {result['device_token'][:20]}...")
            else:
                print("❌ Invalid or expired code")
        
        elif args[0] == "list":
            devices = self.security.pairing.list_user_devices(self.current_user.id)
            print(f"\n📱 Paired devices ({len(devices)}):")
            for d in devices:
                status = "✅" if d['is_active'] else "❌"
                print(f"   {status} {d['device_info']['name']} ({d['trust_level']})")
    
    def run_demo(self):
        """Run the complete demo"""
        import subprocess
        subprocess.run([sys.executable, "examples/complete_demo.py"])
    
    def show_help(self):
        """Show help"""
        print("""
Commands:
  mode [name]              - List or activate conditioning mode
  agents [list|create]     - Manage agents
  task                     - Execute a multi-agent task
  skills [list|load]       - Manage skills
  providers [list|models|recommend|compare|test] - AI providers
  user [register|login]    - User management
  pair [request|confirm]   - Device pairing
  demo                     - Run full feature demo
  quit                     - Exit
        """)

if __name__ == "__main__":
    cli = KashizaCLI()
    cli.run()
