"""
Example Plugin for Kashiza

This demonstrates how to create a plugin with hooks.
"""

from core.plugin import Plugin, PluginMetadata

class ExamplePlugin(Plugin):
    """Example plugin that demonstrates all hook points"""
    
    metadata = PluginMetadata(
        name="example",
        version="1.0.0",
        author="Hermes Team",
        description="Example plugin demonstrating hook system",
        hooks=[
            'pre_orchestrate',
            'post_orchestrate',
            'on_error',
            'on_task_complete'
        ],
        dependencies=[]
    )
    
    def __init__(self):
        super().__init__()
        self.task_count = 0
        self.total_cost = 0.0
    
    def initialize(self):
        """Called when plugin is loaded"""
        print(f"✅ Plugin '{self.metadata.name}' initialized")
    
    def shutdown(self):
        """Called when plugin is unloaded"""
        print(f"📊 Plugin '{self.metadata.name}' stats: {self.task_count} tasks, ${self.total_cost:.4f} cost")
    
    @Plugin.on('pre_orchestrate')
    def before_task(self, context):
        """Called before task execution"""
        prompt = context.get('prompt', '')
        print(f"🔔 [Example] Starting task: {prompt[:50]}...")
        return {'acknowledged': True}
    
    @Plugin.on('post_orchestrate')
    def after_task(self, context):
        """Called after task execution"""
        results = context.get('results', [])
        cost = sum(r.cost for r in results) if results else 0
        
        self.task_count += 1
        self.total_cost += cost
        
        print(f"✅ [Example] Task completed. Cost: ${cost:.4f}")
        
        # Alert if cost is high
        if cost > 0.5:
            print(f"🚨 [Example] High cost alert: ${cost:.4f}")
        
        return {
            'tasks_completed': self.task_count,
            'total_cost': self.total_cost
        }
    
    @Plugin.on('on_error')
    def handle_error(self, context):
        """Called when an error occurs"""
        error = context.get('error', 'Unknown error')
        print(f"❌ [Example] Error occurred: {error}")
        return {'logged': True}
    
    @Plugin.on('on_task_complete')
    def on_complete(self, context):
        """Called when task completes successfully"""
        print(f"🎉 [Example] Task completed successfully!")
        return {'celebrated': True}

# Plugin instance
plugin = ExamplePlugin()
