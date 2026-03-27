"""
Kashiza - Basic Usage Examples
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.orchestrator import get_orchestrator, ExecutionMode
from core.cost_tracker import get_cost_tracker
from core.team_collab import TeamCollaboration
from templates.engine import TemplateEngine
from market.store import AgentMarket

async def example_orchestration():
    """Example: Automatic agent selection and task execution"""
    print("=" * 60)
    print("Example 1: Automatic Agent Selection")
    print("=" * 60)
    
    orchestrator = get_orchestrator()
    
    # Task prompt
    prompt = "Create a Python FastAPI endpoint for user authentication with JWT tokens"
    
    print(f"\nPrompt: {prompt}\n")
    
    # Analyze the prompt
    analysis = orchestrator.analyzer.analyze(prompt)
    print("Analysis:")
    print(f"  Complexity: {analysis['complexity']}")
    print(f"  Urgency: {analysis['urgency']}")
    print(f"  Requires multiple agents: {analysis['requires_multiple_agents']}")
    
    # See which agents would be selected
    selected = orchestrator.select_agents(prompt)
    print(f"\nSelected agents: {[a.name for a in selected]}")
    
    # Execute the task
    print("\nExecuting...")
    results = await orchestrator.execute_task(prompt)
    
    for result in results:
        print(f"\n[{result.agent_id}]")
        print(f"  Time: {result.execution_time:.2f}s")
        print(f"  Tokens: {result.tokens_used}")
        print(f"  Cost: ${result.cost:.4f}")
        print(f"  Output preview: {result.output[:200]}...")

async def example_cost_tracking():
    """Example: Cost tracking and budget management"""
    print("\n" + "=" * 60)
    print("Example 2: Cost Tracking")
    print("=" * 60)
    
    tracker = get_cost_tracker()
    
    # Check current budget status
    status = tracker.get_budget_status()
    print(f"\nDaily: ${status['daily']['spent']:.2f} / ${status['daily']['budget']:.2f}")
    print(f"Monthly: ${status['monthly']['spent']:.2f} / ${status['monthly']['budget']:.2f}")
    
    # Get model recommendation for a task
    recommendation = tracker.get_model_recommendation(
        "Write a complex machine learning algorithm"
    )
    print(f"\nTask complexity: {recommendation['task_complexity']}")
    print("\nRecommended models:")
    for rec in recommendation['recommendations'][:3]:
        print(f"  • {rec['model']}: ${rec['estimated_cost']:.4f} (quality: {rec['quality_score']}/10)")

async def example_team_collaboration():
    """Example: Team collaboration features"""
    print("\n" + "=" * 60)
    print("Example 3: Team Collaboration")
    print("=" * 60)
    
    team = TeamCollaboration()
    
    # Create team members
    alice = team.create_member("Alice", "alice@example.com", "developer")
    bob = team.create_member("Bob", "bob@example.com", "manager")
    
    print(f"\nCreated members:")
    print(f"  • {alice.name} ({alice.role}) - ID: {alice.id}")
    print(f"  • {bob.name} ({bob.role}) - ID: {bob.id}")
    
    # Create a project
    project = team.create_project(
        name="AI Platform",
        description="Building an AI-powered platform",
        owner_id=bob.id
    )
    print(f"\nCreated project: {project.name} (ID: {project.id})")
    
    # Add Alice to project
    team.add_project_member(project.id, alice.id, bob.id)
    print(f"Added {alice.name} to project")
    
    # Create tasks
    task1 = team.create_task(
        project_id=project.id,
        title="Design API",
        description="Create API specification",
        creator_id=bob.id,
        assignee_id=alice.id
    )
    print(f"\nCreated task: {task1.title} (assigned to {alice.name})")
    
    # Get project stats
    stats = team.get_project_stats(project.id)
    print(f"\nProject stats:")
    print(f"  Total tasks: {stats['total_tasks']}")
    print(f"  By status: {stats['by_status']}")

def example_templates():
    """Example: Project templates"""
    print("\n" + "=" * 60)
    print("Example 4: Project Templates")
    print("=" * 60)
    
    engine = TemplateEngine()
    
    # List available templates
    templates = engine.list_templates()
    print("\nAvailable templates:")
    for t in templates:
        print(f"  • {t['name']} ({t['id']}) - {t['category']}")
    
    # Create project from template
    print("\nCreating FastAPI project...")
    result = engine.create_project(
        template_id='web_api',
        project_path='/tmp/my_api',
        variables={'project_name': 'MyAPI'}
    )
    
    if result['success']:
        print(f"✅ Created at: {result['path']}")
        print(f"   Files: {result['files_created']}")

def example_market():
    """Example: Agent market"""
    print("\n" + "=" * 60)
    print("Example 5: Agent Market")
    print("=" * 60)
    
    market = AgentMarket()
    
    # Browse packs
    packs = market.search()
    print(f"\nAvailable packs: {len(packs)}")
    
    for pack in packs[:3]:
        print(f"\n  • {pack.name} (${pack.price:.2f})")
        print(f"    {pack.description}")
        print(f"    Tags: {', '.join(pack.tags)}")
    
    # Get categories
    categories = market.get_categories()
    print(f"\nCategories: {', '.join(categories)}")

async def main():
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "HERMES WRAPPER EXAMPLES" + " " * 20 + "║")
    print("╚" + "═" * 58 + "╝")
    
    try:
        await example_orchestration()
    except Exception as e:
        print(f"Orchestration example skipped: {e}")
    
    try:
        await example_cost_tracking()
    except Exception as e:
        print(f"Cost tracking example skipped: {e}")
    
    try:
        await example_team_collaboration()
    except Exception as e:
        print(f"Team collaboration example skipped: {e}")
    
    try:
        example_templates()
    except Exception as e:
        print(f"Templates example skipped: {e}")
    
    try:
        example_market()
    except Exception as e:
        print(f"Market example skipped: {e}")
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
