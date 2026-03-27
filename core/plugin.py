import os
import sys
import json
import importlib
import importlib.util
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import asyncio
import watchdog.observers
from watchdog.events import FileSystemEventHandler

@dataclass
class PluginMetadata:
    name: str
    version: str
    author: str
    description: str
    hooks: List[str]
    dependencies: List[str]
    enabled: bool = True
    last_loaded: Optional[str] = None
    load_time_ms: float = 0.0

@dataclass
class HookContext:
    plugin_name: str
    hook_name: str
    timestamp: float
    execution_time_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None

class Plugin:
    """Base class for all plugins"""
    
    metadata: PluginMetadata = None
    
    def __init__(self):
        self._hooks: Dict[str, List[Callable]] = {}
        self._enabled = True
    
    def register_hook(self, hook_name: str, callback: Callable):
        """Register a hook handler"""
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        self._hooks[hook_name].append(callback)
    
    def on(self, hook_name: str):
        """Decorator for registering hooks"""
        def decorator(func):
            self.register_hook(hook_name, func)
            return func
        return decorator
    
    async def execute_hook(self, hook_name: str, context: Dict) -> List[Any]:
        """Execute all handlers for a hook"""
        results = []
        for handler in self._hooks.get(hook_name, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(context)
                else:
                    result = handler(context)
                results.append(result)
            except Exception as e:
                print(f"Plugin {self.metadata.name} hook {hook_name} error: {e}")
        return results
    
    def initialize(self):
        """Called when plugin is loaded"""
        pass
    
    def shutdown(self):
        """Called when plugin is unloaded"""
        pass

class PluginManager:
    HOOKS = [
        'pre_orchestrate',
        'post_orchestrate',
        'pre_tool_call',
        'post_tool_call',
        'pre_agent_execute',
        'post_agent_execute',
        'on_error',
        'on_cost_threshold',
        'on_quality_low',
        'on_security_alert',
        'on_task_complete',
        'on_config_change'
    ]
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(exist_ok=True)
        self.plugins: Dict[str, Plugin] = {}
        self.hooks: Dict[str, List[tuple]] = {h: [] for h in self.HOOKS}
        self.execution_history: List[HookContext] = []
        self.hot_reload = True
        self.observer = None
        self._setup_file_watcher()
        self._load_all_plugins()
    
    def _setup_file_watcher(self):
        """Setup file system watcher for hot reload"""
        if not self.hot_reload:
            return
        
        class PluginEventHandler(FileSystemEventHandler):
            def __init__(self, manager):
                self.manager = manager
            
            def on_modified(self, event):
                if event.src_path.endswith('.py'):
                    plugin_name = Path(event.src_path).stem
                    if plugin_name in self.manager.plugins:
                        print(f"🔄 Hot reloading plugin: {plugin_name}")
                        self.manager.reload_plugin(plugin_name)
            
            def on_created(self, event):
                if event.src_path.endswith('.py'):
                    plugin_name = Path(event.src_path).stem
                    if plugin_name not in self.manager.plugins:
                        print(f"📦 Loading new plugin: {plugin_name}")
                        self.manager.load_plugin(event.src_path)
        
        self.observer = watchdog.observers.Observer()
        self.observer.schedule(
            PluginEventHandler(self),
            str(self.plugins_dir),
            recursive=True
        )
        self.observer.start()
    
    def _load_all_plugins(self):
        """Load all plugins from plugins directory"""
        if not self.plugins_dir.exists():
            return
        
        for plugin_file in self.plugins_dir.glob("*.py"):
            if plugin_file.name.startswith('_'):
                continue
            self.load_plugin(plugin_file)
    
    def load_plugin(self, plugin_path: str) -> bool:
        """Load a plugin from file"""
        plugin_path = Path(plugin_path)
        plugin_name = plugin_path.stem
        
        try:
            start_time = datetime.now().timestamp()
            
            # Load module
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[plugin_name] = module
            spec.loader.exec_module(module)
            
            # Find plugin class
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, Plugin) and 
                    attr != Plugin):
                    plugin_class = attr
                    break
            
            if not plugin_class:
                print(f"No plugin class found in {plugin_name}")
                return False
            
            # Instantiate plugin
            plugin = plugin_class()
            
            # Set metadata if not defined
            if not plugin.metadata:
                plugin.metadata = PluginMetadata(
                    name=plugin_name,
                    version="1.0.0",
                    author="unknown",
                    description="",
                    hooks=[],
                    dependencies=[]
                )
            
            # Calculate load time
            load_time = (datetime.now().timestamp() - start_time) * 1000
            plugin.metadata.load_time_ms = load_time
            plugin.metadata.last_loaded = datetime.now().isoformat()
            
            # Register hooks
            self._register_plugin_hooks(plugin)
            
            # Initialize plugin
            plugin.initialize()
            
            # Store plugin
            self.plugins[plugin_name] = plugin
            
            print(f"✅ Loaded plugin: {plugin_name} (v{plugin.metadata.version}) in {load_time:.1f}ms")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load plugin {plugin_name}: {e}")
            return False
    
    def reload_plugin(self, plugin_name: str) -> bool:
        """Hot reload a plugin"""
        if plugin_name not in self.plugins:
            return False
        
        # Unload existing
        self.unload_plugin(plugin_name)
        
        # Reload
        plugin_path = self.plugins_dir / f"{plugin_name}.py"
        return self.load_plugin(plugin_path)
    
    def unload_plugin(self, plugin_name: str):
        """Unload a plugin"""
        if plugin_name not in self.plugins:
            return
        
        plugin = self.plugins[plugin_name]
        
        # Unregister hooks
        for hook_name in self.HOOKS:
            self.hooks[hook_name] = [
                (p, h) for p, h in self.hooks[hook_name] 
                if p != plugin
            ]
        
        # Shutdown plugin
        plugin.shutdown()
        
        # Remove from registry
        del self.plugins[plugin_name]
        
        print(f"📤 Unloaded plugin: {plugin_name}")
    
    def _register_plugin_hooks(self, plugin: Plugin):
        """Register all hooks from a plugin"""
        for hook_name, handlers in plugin._hooks.items():
            if hook_name in self.HOOKS:
                for handler in handlers:
                    self.hooks[hook_name].append((plugin, handler))
    
    async def execute_hook(self, hook_name: str, context: Dict) -> Dict:
        """Execute a hook across all plugins"""
        if hook_name not in self.HOOKS:
            return {'results': [], 'errors': []}
        
        results = []
        errors = []
        
        for plugin, handler in self.hooks[hook_name]:
            if not plugin._enabled:
                continue
            
            start_time = datetime.now().timestamp()
            
            try:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(context)
                else:
                    result = handler(context)
                
                execution_time = (datetime.now().timestamp() - start_time) * 1000
                
                self.execution_history.append(HookContext(
                    plugin_name=plugin.metadata.name,
                    hook_name=hook_name,
                    timestamp=start_time,
                    execution_time_ms=execution_time,
                    success=True
                ))
                
                results.append({
                    'plugin': plugin.metadata.name,
                    'result': result
                })
                
            except Exception as e:
                execution_time = (datetime.now().timestamp() - start_time) * 1000
                
                self.execution_history.append(HookContext(
                    plugin_name=plugin.metadata.name,
                    hook_name=hook_name,
                    timestamp=start_time,
                    execution_time_ms=execution_time,
                    success=False,
                    error=str(e)
                ))
                
                errors.append({
                    'plugin': plugin.metadata.name,
                    'error': str(e)
                })
        
        return {
            'results': results,
            'errors': errors,
            'hook': hook_name,
            'timestamp': datetime.now().isoformat()
        }
    
    def enable_plugin(self, plugin_name: str):
        """Enable a plugin"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name]._enabled = True
            print(f"✅ Enabled plugin: {plugin_name}")
    
    def disable_plugin(self, plugin_name: str):
        """Disable a plugin"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name]._enabled = False
            print(f"⏸️  Disabled plugin: {plugin_name}")
    
    def list_plugins(self) -> List[Dict]:
        """List all loaded plugins"""
        return [
            {
                'name': p.metadata.name,
                'version': p.metadata.version,
                'author': p.metadata.author,
                'description': p.metadata.description,
                'enabled': p._enabled,
                'hooks': p.metadata.hooks,
                'load_time_ms': p.metadata.load_time_ms,
                'last_loaded': p.metadata.last_loaded
            }
            for p in self.plugins.values()
        ]
    
    def get_plugin_stats(self) -> Dict:
        """Get plugin execution statistics"""
        stats = {}
        
        for ctx in self.execution_history:
            key = f"{ctx.plugin_name}.{ctx.hook_name}"
            if key not in stats:
                stats[key] = {
                    'calls': 0,
                    'errors': 0,
                    'avg_execution_time': 0
                }
            
            stats[key]['calls'] += 1
            if not ctx.success:
                stats[key]['errors'] += 1
            
            # Update average
            current_avg = stats[key]['avg_execution_time']
            stats[key]['avg_execution_time'] = (
                (current_avg * (stats[key]['calls'] - 1)) + ctx.execution_time_ms
            ) / stats[key]['calls']
        
        return stats
    
    def stop(self):
        """Stop plugin manager and file watcher"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        # Shutdown all plugins
        for plugin in self.plugins.values():
            plugin.shutdown()

# Example plugin implementations
class CostMonitorPlugin(Plugin):
    """Example plugin that monitors costs"""
    
    metadata = PluginMetadata(
        name="cost_monitor",
        version="1.0.0",
        author="Hermes Team",
        description="Monitors API costs and sends alerts",
        hooks=['post_orchestrate', 'on_cost_threshold'],
        dependencies=[]
    )
    
    def __init__(self):
        super().__init__()
        self.total_cost = 0.0
        self.alert_threshold = 5.0
    
    def initialize(self):
        print("📊 Cost Monitor plugin initialized")
    
    @Plugin.on('post_orchestrate')
    def track_cost(self, context):
        cost = context.get('total_cost', 0)
        self.total_cost += cost
        
        if self.total_cost > self.alert_threshold:
            print(f"⚠️ Cost alert: ${self.total_cost:.2f} spent")
    
    @Plugin.on('on_cost_threshold')
    def handle_threshold(self, context):
        print(f"🚨 Cost threshold reached: {context}")

class SecurityPlugin(Plugin):
    """Example security plugin"""
    
    metadata = PluginMetadata(
        name="security_guard",
        version="1.0.0",
        author="Hermes Team",
        description="Security checks and logging",
        hooks=['pre_orchestrate', 'on_security_alert'],
        dependencies=[]
    )
    
    @Plugin.on('pre_orchestrate')
    def check_prompt(self, context):
        prompt = context.get('prompt', '')
        
        # Check for suspicious patterns
        suspicious = ['rm -rf', 'drop table', 'delete from']
        for pattern in suspicious:
            if pattern in prompt.lower():
                print(f"🛡️ Security: Suspicious pattern detected: {pattern}")
                return {'blocked': True, 'reason': 'suspicious_pattern'}
        
        return {'blocked': False}

# Global plugin manager
_plugin_manager = None

def get_plugin_manager() -> PluginManager:
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager
