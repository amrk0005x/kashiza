#!/usr/bin/env python3
"""
Kashiza - Advanced Multi-Agent Orchestration System
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def print_banner():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ██╗  ██╗ █████╗ ███████╗██╗  ██╗██╗███████╗ █████╗         ║
║   ██║ ██╔╝██╔══██╗██╔════╝██║  ██║██║╚══███╔╝██╔══██╗        ║
║   █████╔╝ ███████║███████╗███████║██║  ███╔╝ ███████║        ║
║   ██╔═██╗ ██╔══██║╚════██║██╔══██║██║ ███╔╝  ██╔══██║        ║
║   ██║  ██╗██║  ██║███████║██║  ██║██║███████╗██║  ██║        ║
║   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝        ║
║                                                               ║
║              Advanced Multi-Agent Orchestration               ║
║                         v2.1.0                                ║
╚═══════════════════════════════════════════════════════════════╝
""")

def cmd_api(args):
    """Start the API server"""
    from api.server import main
    main()

def cmd_orchestrate(args):
    """Execute a task with orchestration"""
    import asyncio
    from core.orchestrator import get_orchestrator, ExecutionMode
    
    async def run():
        orchestrator = get_orchestrator()
        
        print(f"🤖 Analyzing prompt: {args.prompt[:50]}...")
        
        mode = ExecutionMode(args.mode) if args.mode else ExecutionMode.AUTO
        
        results = await orchestrator.execute_task(
            prompt=args.prompt,
            mode=mode
        )
        
        print("\n" + "="*60)
        print("RESULTS:")
        print("="*60)
        
        for i, result in enumerate(results, 1):
            print(f"\n[{i}] Agent: {result.agent_id}")
            print(f"    Time: {result.execution_time:.2f}s | Tokens: {result.tokens_used} | Cost: ${result.cost:.4f}")
            print(f"    Output:\n{result.output[:500]}..." if len(result.output) > 500 else f"    Output:\n{result.output}")
        
        total_cost = sum(r.cost for r in results)
        total_time = sum(r.execution_time for r in results)
        
        print("\n" + "="*60)
        print(f"Total Cost: ${total_cost:.4f} | Total Time: {total_time:.2f}s")
        print("="*60)
    
    asyncio.run(run())

def cmd_analyze(args):
    """Analyze a prompt and recommend agents"""
    from core.orchestrator import get_orchestrator
    
    orchestrator = get_orchestrator()
    
    print(f"🔍 Analyzing: {args.prompt[:50]}...")
    
    analysis = orchestrator.analyzer.analyze(args.prompt)
    selected = orchestrator.select_agents(args.prompt)
    
    print("\n" + "="*60)
    print("ANALYSIS:")
    print("="*60)
    print(f"\nComplexity: {analysis['complexity']}")
    print(f"Urgency: {analysis['urgency']}")
    print(f"Estimated Tokens: {analysis['estimated_tokens']:.0f}")
    print(f"Requires Multiple Agents: {analysis['requires_multiple_agents']}")
    
    print("\nDetected Specialties:")
    for specialty, score in analysis['specialties'][:5]:
        print(f"  - {specialty}: {score:.1f}")
    
    print("\n" + "="*60)
    print("RECOMMENDED AGENTS:")
    print("="*60)
    for agent in selected:
        print(f"  • {agent.name} ({agent.specialty})")
        print(f"    Model: {agent.model} | Cost: ${agent.cost_per_1k_tokens}/1k tokens")

def cmd_agents(args):
    """List available agents"""
    from core.orchestrator import get_orchestrator
    
    orchestrator = get_orchestrator()
    agents = orchestrator.registry.list_all()
    
    print("\n" + "="*60)
    print("AVAILABLE AGENTS:")
    print("="*60)
    
    for agent in agents:
        print(f"\n{agent.name} (ID: {agent.id})")
        print(f"  Specialty: {agent.specialty}")
        print(f"  Model: {agent.model}")
        print(f"  Skills: {', '.join(agent.skills[:5])}")
        print(f"  Cost: ${agent.cost_per_1k_tokens}/1k tokens")

def cmd_costs(args):
    """Show cost tracking info"""
    from core.cost_tracker import get_cost_tracker
    
    tracker = get_cost_tracker()
    status = tracker.get_budget_status()
    
    print("\n" + "="*60)
    print("COST TRACKING:")
    print("="*60)
    
    print("\nDaily Budget:")
    print(f"  Spent: ${status['daily']['spent']:.2f} / ${status['daily']['budget']:.2f}")
    print(f"  Remaining: ${status['daily']['remaining']:.2f}")
    print(f"  Used: {status['daily']['percent_used']:.1f}%")
    
    print("\nMonthly Budget:")
    print(f"  Spent: ${status['monthly']['spent']:.2f} / ${status['monthly']['budget']:.2f}")
    print(f"  Remaining: ${status['monthly']['remaining']:.2f}")
    print(f"  Used: {status['monthly']['percent_used']:.1f}%")

def cmd_templates(args):
    """List project templates"""
    from templates.engine import TemplateEngine
    
    engine = TemplateEngine()
    templates = engine.list_templates(args.category)
    
    print("\n" + "="*60)
    print("PROJECT TEMPLATES:")
    print("="*60)
    
    for t in templates:
        print(f"\n{t['name']} (ID: {t['id']})")
        print(f"  Category: {t['category']}")
        print(f"  {t['description']}")

def cmd_create(args):
    """Create project from template"""
    from templates.engine import TemplateEngine
    
    engine = TemplateEngine()
    result = engine.create_project(
        args.template,
        args.path,
        {'project_name': args.name}
    )
    
    if result['success']:
        print(f"✅ Project created at {result['path']}")
        print(f"   Files created: {result['files_created']}")
    else:
        print(f"❌ Error: {result['error']}")

def cmd_market(args):
    """Browse agent market"""
    from market.store import AgentMarket
    
    market = AgentMarket()
    packs = market.search(category=args.category)
    
    print("\n" + "="*60)
    print("AGENT MARKET:")
    print("="*60)
    
    for pack in packs:
        print(f"\n{pack.name} (ID: {pack.id})")
        print(f"  Category: {pack.category}")
        print(f"  Price: ${pack.price:.2f}")
        print(f"  Rating: {pack.rating:.1f}/5.0")
        print(f"  {pack.description}")

def cmd_install(args):
    """Install agent pack"""
    from market.store import AgentMarket, PackInstaller
    
    market = AgentMarket()
    installer = PackInstaller(market)
    
    print(f"📦 Installing {args.pack_id}...")
    
    result = installer.install_with_dependencies(args.pack_id)
    
    if result['success']:
        print(f"✅ Pack installed successfully!")
    else:
        print(f"❌ Error: {result['error']}")
        if 'install_commands' in result:
            print("\nMissing requirements. Install with:")
            for req, cmd in result['install_commands'].items():
                print(f"  {req}: {cmd}")

def cmd_monitor(args):
    """Run self-monitoring"""
    from core.self_monitor import SelfMonitor, AutoCorrector
    
    monitor = SelfMonitor()
    corrector = AutoCorrector(monitor)
    
    print("🔍 Running system monitoring...")
    
    monitor.collect_metrics()
    quality = monitor.get_average_quality()
    
    print(f"\nCurrent Quality Score: {quality:.1f}/10")
    
    if quality < 7:
        print("⚠️ Quality below threshold. Running auto-correction...")
        result = corrector.check_and_correct()
        print(f"\nCorrections applied: {len(result['corrections'])}")
        for corr in result['corrections']:
            print(f"  - {corr['action']}")
    else:
        print("✅ System operating within normal parameters")

def cmd_pc(args):
    """PC Control commands"""
    from skills.pc_control.controller import PCController
    
    pc = PCController()
    
    if args.command == "info":
        result = pc.get_system_info()
        print(json.dumps(result, indent=2))
    elif args.command == "list":
        result = pc.list_directory(args.path or "~")
        for entry in result.get('entries', []):
            icon = "📁" if entry['type'] == 'directory' else "📄"
            print(f"{icon} {entry['name']}")
    elif args.command == "run":
        result = pc.run_command(args.args)
        print(result.get('stdout', ''))
        if result.get('stderr'):
            print("STDERR:", result.get('stderr'))

def cmd_team(args):
    """Team collaboration commands"""
    from core.team_collab import TeamCollaboration
    
    team = TeamCollaboration()
    
    if args.subcommand == "members":
        members = team.list_members()
        print("\nTeam Members:")
        for m in members:
            print(f"  • {m.name} ({m.role}) - {m.email}")
    
    elif args.subcommand == "projects":
        projects = team.list_projects()
        print("\nProjects:")
        for p in projects:
            print(f"  • {p.name} - {len(p.member_ids)} members")
    
    elif args.subcommand == "create-member":
        member = team.create_member(args.name, args.email, args.role)
        print(f"✅ Created member: {member.name} (ID: {member.id})")
    
    elif args.subcommand == "create-project":
        project = team.create_project(args.name, args.description, args.owner)
        print(f"✅ Created project: {project.name} (ID: {project.id})")

def main():
    parser = argparse.ArgumentParser(
        description="Kashiza - Advanced Multi-Agent Orchestration",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # API server
    api_parser = subparsers.add_parser('api', help='Start API server')
    api_parser.set_defaults(func=cmd_api)
    
    # Orchestrate
    orch_parser = subparsers.add_parser('orchestrate', help='Execute task with orchestration')
    orch_parser.add_argument('prompt', help='Task prompt')
    orch_parser.add_argument('--mode', choices=['sequential', 'parallel', 'collaborative', 'hierarchical', 'auto'], 
                            default='auto', help='Execution mode')
    orch_parser.set_defaults(func=cmd_orchestrate)
    
    # Analyze
    analyze_parser = subparsers.add_parser('analyze', help='Analyze prompt and recommend agents')
    analyze_parser.add_argument('prompt', help='Prompt to analyze')
    analyze_parser.set_defaults(func=cmd_analyze)
    
    # Agents
    agents_parser = subparsers.add_parser('agents', help='List available agents')
    agents_parser.set_defaults(func=cmd_agents)
    
    # Costs
    costs_parser = subparsers.add_parser('costs', help='Show cost tracking')
    costs_parser.set_defaults(func=cmd_costs)
    
    # Templates
    templates_parser = subparsers.add_parser('templates', help='List project templates')
    templates_parser.add_argument('--category', help='Filter by category')
    templates_parser.set_defaults(func=cmd_templates)
    
    # Create project
    create_parser = subparsers.add_parser('create', help='Create project from template')
    create_parser.add_argument('template', help='Template ID')
    create_parser.add_argument('name', help='Project name')
    create_parser.add_argument('--path', default='.', help='Output path')
    create_parser.set_defaults(func=cmd_create)
    
    # Market
    market_parser = subparsers.add_parser('market', help='Browse agent market')
    market_parser.add_argument('--category', help='Filter by category')
    market_parser.set_defaults(func=cmd_market)
    
    # Install
    install_parser = subparsers.add_parser('install', help='Install agent pack')
    install_parser.add_argument('pack_id', help='Pack ID')
    install_parser.set_defaults(func=cmd_install)
    
    # Monitor
    monitor_parser = subparsers.add_parser('monitor', help='Run self-monitoring')
    monitor_parser.set_defaults(func=cmd_monitor)
    
    # PC Control
    pc_parser = subparsers.add_parser('pc', help='PC control commands')
    pc_parser.add_argument('command', choices=['info', 'list', 'run'])
    pc_parser.add_argument('--path', help='Path for list command')
    pc_parser.add_argument('--args', help='Arguments for run command')
    pc_parser.set_defaults(func=cmd_pc)
    
    # Team
    team_parser = subparsers.add_parser('team', help='Team collaboration')
    team_parser.add_argument('subcommand', choices=['members', 'projects', 'create-member', 'create-project'])
    team_parser.add_argument('--name', help='Name for create commands')
    team_parser.add_argument('--email', help='Email for create-member')
    team_parser.add_argument('--role', default='developer', help='Role for create-member')
    team_parser.add_argument('--description', default='', help='Description for create-project')
    team_parser.add_argument('--owner', help='Owner ID for create-project')
    team_parser.set_defaults(func=cmd_team)
    
    args = parser.parse_args()
    
    print_banner()
    
    if args.command:
        args.func(args)
    else:
        parser.print_help()
        print("\n💡 Quick start:")
        print("  python run.py api              # Start API server")
        print("  python run.py agents           # List agents")
        print("  python run.py orchestrate 'Write a Python function to sort a list'")
        print("  python run.py templates        # List templates")

if __name__ == '__main__':
    main()
