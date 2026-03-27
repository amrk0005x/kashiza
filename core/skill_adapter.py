"""
Adaptateur de Skills pour Kashiza
Supporte les skills Hermes natifs et OpenClaw
"""
import os
import sys
import json
import importlib.util
import inspect
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Union
from pathlib import Path
from enum import Enum

class SkillSource(Enum):
    HERMES = "kashiza"
    OPENCLAW = "openclaw"
    WRAPPER = "wrapper"

@dataclass
class Skill:
    name: str
    description: str
    source: SkillSource
    version: str
    author: str
    path: str
    entry_point: str
    config_schema: Dict = field(default_factory=dict)
    hooks: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    loaded: bool = False
    module: Any = None
    instance: Any = None

class SkillAdapter:
    """Adapte les skills Hermes/OpenClaw pour le wrapper"""
    
    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self.active_skills: Dict[str, Skill] = {}
        self.hooks: Dict[str, List[Callable]] = {}
        self.kashiza_skills_path = os.path.expanduser("~/.kashiza/skills")
        self.wrapper_skills_path = os.path.expanduser("~/.kashiza/skills")
        self.openclaw_skills_path = os.path.expanduser("~/.openclaw/skills")
        
        # Crée les dossiers si besoin
        os.makedirs(self.wrapper_skills_path, exist_ok=True)
    
    def discover_skills(self) -> List[Skill]:
        """Découvre tous les skills disponibles"""
        discovered = []
        
        # Skills Hermes
        if os.path.exists(self.kashiza_skills_path):
            discovered.extend(self._scan_kashiza_skills(self.kashiza_skills_path))
        
        # Skills Wrapper natifs
        if os.path.exists(self.wrapper_skills_path):
            discovered.extend(self._scan_wrapper_skills(self.wrapper_skills_path))
        
        # Skills OpenClaw (si existant)
        if os.path.exists(self.openclaw_skills_path):
            discovered.extend(self._scan_openclaw_skills(self.openclaw_skills_path))
        
        # Registre les skills
        for skill in discovered:
            self.skills[skill.name] = skill
        
        return discovered
    
    def _scan_kashiza_skills(self, path: str) -> List[Skill]:
        """Scanne les skills Hermes (format SKILL.md + scripts/)"""
        skills = []
        
        for item in os.listdir(path):
            skill_dir = os.path.join(path, item)
            if not os.path.isdir(skill_dir):
                continue
            
            skill_md = os.path.join(skill_dir, "SKILL.md")
            if not os.path.exists(skill_md):
                continue
            
            # Parse SKILL.md
            try:
                metadata = self._parse_kashiza_skill_md(skill_md)
                
                # Cherche le point d'entrée
                entry_point = None
                for ext in [".py", ".js", ".sh"]:
                    candidate = os.path.join(skill_dir, f"main{ext}")
                    if os.path.exists(candidate):
                        entry_point = candidate
                        break
                
                # Cherche dans scripts/
                scripts_dir = os.path.join(skill_dir, "scripts")
                if not entry_point and os.path.exists(scripts_dir):
                    for script in os.listdir(scripts_dir):
                        if script.endswith((".py", ".js", ".sh")):
                            entry_point = os.path.join(scripts_dir, script)
                            break
                
                skill = Skill(
                    name=metadata.get("name", item),
                    description=metadata.get("description", ""),
                    source=SkillSource.HERMES,
                    version=metadata.get("version", "1.0.0"),
                    author=metadata.get("author", "Unknown"),
                    path=skill_dir,
                    entry_point=entry_point,
                    config_schema=metadata.get("config", {}),
                    hooks=metadata.get("hooks", []),
                    dependencies=metadata.get("dependencies", []),
                    metadata=metadata
                )
                skills.append(skill)
                
            except Exception as e:
                print(f"Error parsing Hermes skill {item}: {e}")
        
        return skills
    
    def _scan_wrapper_skills(self, path: str) -> List[Skill]:
        """Scanne les skills natifs du wrapper"""
        skills = []
        
        for item in os.listdir(path):
            skill_dir = os.path.join(path, item)
            if not os.path.isdir(skill_dir):
                continue
            
            # Cherche skill.json ou skill.py
            skill_json = os.path.join(skill_dir, "skill.json")
            skill_py = os.path.join(skill_dir, "skill.py")
            
            if os.path.exists(skill_json):
                try:
                    with open(skill_json) as f:
                        config = json.load(f)
                    
                    skill = Skill(
                        name=config.get("name", item),
                        description=config.get("description", ""),
                        source=SkillSource.WRAPPER,
                        version=config.get("version", "1.0.0"),
                        author=config.get("author", "Unknown"),
                        path=skill_dir,
                        entry_point=os.path.join(skill_dir, config.get("entry", "skill.py")),
                        config_schema=config.get("config_schema", {}),
                        hooks=config.get("hooks", []),
                        dependencies=config.get("dependencies", []),
                        tools=config.get("tools", []),
                        metadata=config
                    )
                    skills.append(skill)
                    
                except Exception as e:
                    print(f"Error loading wrapper skill {item}: {e}")
            
            elif os.path.exists(skill_py):
                # Skill simple Python
                skill = Skill(
                    name=item,
                    description=f"Wrapper skill: {item}",
                    source=SkillSource.WRAPPER,
                    version="1.0.0",
                    author="Unknown",
                    path=skill_dir,
                    entry_point=skill_py
                )
                skills.append(skill)
        
        return skills
    
    def _scan_openclaw_skills(self, path: str) -> List[Skill]:
        """Scanne les skills OpenClaw (format YAML/JSON)"""
        skills = []
        
        # OpenClaw utilise généralement des fichiers YAML
        for item in os.listdir(path):
            if not item.endswith((".yaml", ".yml", ".json")):
                continue
            
            skill_file = os.path.join(path, item)
            try:
                if item.endswith(".json"):
                    with open(skill_file) as f:
                        config = json.load(f)
                else:
                    import yaml
                    with open(skill_file) as f:
                        config = yaml.safe_load(f)
                
                skill = Skill(
                    name=config.get("name", item.replace(".yaml", "").replace(".yml", "").replace(".json", "")),
                    description=config.get("description", ""),
                    source=SkillSource.OPENCLAW,
                    version=config.get("version", "1.0.0"),
                    author=config.get("author", "Unknown"),
                    path=path,
                    entry_point=skill_file,
                    config_schema=config.get("inputs", {}),
                    hooks=config.get("hooks", []),
                    metadata=config
                )
                skills.append(skill)
                
            except Exception as e:
                print(f"Error parsing OpenClaw skill {item}: {e}")
        
        return skills
    
    def _parse_kashiza_skill_md(self, path: str) -> Dict:
        """Parse le SKILL.md d'Hermes pour extraire les métadonnées"""
        metadata = {}
        
        with open(path) as f:
            content = f.read()
        
        # Parse YAML frontmatter si présent
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    import yaml
                    metadata = yaml.safe_load(parts[1])
                except:
                    pass
                content = parts[2]
        
        # Extrait les infos du markdown
        lines = content.split("\n")
        for line in lines[:50]:  # Scan les 50 premières lignes
            if line.startswith("# ") and not metadata.get("name"):
                metadata["name"] = line[2:].strip()
            elif line.lower().startswith("description:"):
                metadata["description"] = line.split(":", 1)[1].strip()
        
        return metadata
    
    def load_skill(self, name: str) -> Optional[Skill]:
        """Charge un skill"""
        skill = self.skills.get(name)
        if not skill:
            return None
        
        if skill.loaded:
            return skill
        
        try:
            if skill.source == SkillSource.HERMES:
                self._load_kashiza_skill(skill)
            elif skill.source == SkillSource.WRAPPER:
                self._load_wrapper_skill(skill)
            elif skill.source == SkillSource.OPENCLAW:
                self._load_openclaw_skill(skill)
            
            skill.loaded = True
            self.active_skills[name] = skill
            
            # Enregistre les hooks
            for hook_name in skill.hooks:
                if hook_name not in self.hooks:
                    self.hooks[hook_name] = []
                self.hooks[hook_name].append(skill)
            
            return skill
            
        except Exception as e:
            print(f"Error loading skill {name}: {e}")
            return None
    
    def _load_kashiza_skill(self, skill: Skill):
        """Charge un skill Hermes"""
        if not skill.entry_point:
            return
        
        if skill.entry_point.endswith(".py"):
            # Charge comme module Python
            spec = importlib.util.spec_from_file_location(skill.name, skill.entry_point)
            module = importlib.util.module_from_spec(spec)
            sys.modules[skill.name] = module
            spec.loader.exec_module(module)
            skill.module = module
            
            # Instancie si classe Skill présente
            if hasattr(module, "Skill"):
                skill.instance = module.Skill()
        
        elif skill.entry_point.endswith(".js"):
            # Node.js skill - exécutable via subprocess
            skill.metadata["runtime"] = "node"
        
        elif skill.entry_point.endswith(".sh"):
            # Shell skill
            skill.metadata["runtime"] = "bash"
    
    def _load_wrapper_skill(self, skill: Skill):
        """Charge un skill natif du wrapper"""
        if not skill.entry_point or not os.path.exists(skill.entry_point):
            raise ValueError(f"Entry point not found: {skill.entry_point}")
        
        spec = importlib.util.spec_from_file_location(skill.name, skill.entry_point)
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"wrapper_skill.{skill.name}"] = module
        spec.loader.exec_module(module)
        skill.module = module
        
        # Cherche une classe WrapperSkill ou similaire
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if inspect.isclass(attr) and attr_name.endswith("Skill"):
                skill.instance = attr()
                break
    
    def _load_openclaw_skill(self, skill: Skill):
        """Charge un skill OpenClaw"""
        # OpenClaw skills sont généralement des configs qui définissent des workflows
        skill.metadata["type"] = "openclaw_workflow"
    
    def unload_skill(self, name: str):
        """Décharge un skill"""
        skill = self.active_skills.pop(name, None)
        if skill:
            skill.loaded = False
            skill.module = None
            skill.instance = None
            
            # Retire les hooks
            for hook_name in skill.hooks:
                if hook_name in self.hooks:
                    self.hooks[hook_name] = [s for s in self.hooks[hook_name] if s.name != name]
    
    def execute_skill(self, name: str, context: Dict = None, **kwargs) -> Any:
        """Exécute un skill"""
        skill = self.active_skills.get(name) or self.load_skill(name)
        
        if not skill:
            raise ValueError(f"Skill not found: {name}")
        
        if not skill.loaded:
            raise RuntimeError(f"Skill not loaded: {name}")
        
        context = context or {}
        
        # Exécute selon le type
        if skill.source == SkillSource.HERMES:
            return self._execute_kashiza_skill(skill, context, **kwargs)
        elif skill.source == SkillSource.WRAPPER:
            return self._execute_wrapper_skill(skill, context, **kwargs)
        elif skill.source == SkillSource.OPENCLAW:
            return self._execute_openclaw_skill(skill, context, **kwargs)
    
    def _execute_kashiza_skill(self, skill: Skill, context: Dict, **kwargs):
        """Exécute un skill Hermes"""
        if skill.instance and hasattr(skill.instance, "execute"):
            return skill.instance.execute(context, **kwargs)
        
        elif skill.entry_point.endswith(".py") and skill.module:
            # Cherche une fonction execute ou main
            if hasattr(skill.module, "execute"):
                return skill.module.execute(context, **kwargs)
            elif hasattr(skill.module, "main"):
                return skill.module.main(context, **kwargs)
        
        elif skill.entry_point.endswith(".js"):
            import subprocess
            import json
            
            # Passe le contexte en JSON via stdin
            result = subprocess.run(
                ["node", skill.entry_point],
                input=json.dumps({**context, **kwargs}),
                capture_output=True,
                text=True,
                cwd=skill.path
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Skill execution failed: {result.stderr}")
            
            try:
                return json.loads(result.stdout)
            except:
                return result.stdout
        
        elif skill.entry_point.endswith(".sh"):
            import subprocess
            
            env = os.environ.copy()
            env.update({k: str(v) for k, v in {**context, **kwargs}.items()})
            
            result = subprocess.run(
                ["bash", skill.entry_point],
                capture_output=True,
                text=True,
                cwd=skill.path,
                env=env
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Skill execution failed: {result.stderr}")
            
            return result.stdout
    
    def _execute_wrapper_skill(self, skill: Skill, context: Dict, **kwargs):
        """Exécute un skill wrapper natif"""
        if skill.instance:
            if hasattr(skill.instance, "execute"):
                return skill.instance.execute(context, **kwargs)
            elif hasattr(skill.instance, "run"):
                return skill.instance.run(context, **kwargs)
        
        if skill.module:
            if hasattr(skill.module, "execute"):
                return skill.module.execute(context, **kwargs)
            elif hasattr(skill.module, "main"):
                return skill.module.main(context, **kwargs)
    
    def _execute_openclaw_skill(self, skill: Skill, context: Dict, **kwargs):
        """Exécute un skill OpenClaw (workflow)"""
        # Charge le workflow
        workflow = skill.metadata
        
        # Exécute les étapes
        results = {}
        for step in workflow.get("steps", []):
            step_name = step.get("name", "unnamed")
            step_type = step.get("type", "llm")
            
            if step_type == "llm":
                # Appel LLM
                prompt = step.get("prompt", "").format(**context, **results, **kwargs)
                # TODO: Intégrer avec l'orchestrateur
                results[step_name] = f"[LLM Response for: {prompt[:50]}...]"
            
            elif step_type == "tool":
                # Appel outil
                tool_name = step.get("tool")
                tool_input = step.get("input", {})
                # TODO: Intégrer avec les outils
                results[step_name] = f"[Tool {tool_name} result]"
            
            elif step_type == "condition":
                # Condition
                condition = step.get("if", "true")
                # Évalue la condition (simplifié)
                results[step_name] = f"[Condition: {condition}]"
        
        return results
    
    def call_hook(self, hook_name: str, data: Any) -> Any:
        """Appelle tous les skills enregistrés sur un hook"""
        results = []
        
        for skill in self.hooks.get(hook_name, []):
            if skill.loaded and skill.instance:
                hook_method = getattr(skill.instance, f"on_{hook_name}", None)
                if hook_method:
                    try:
                        result = hook_method(data)
                        results.append({"skill": skill.name, "result": result})
                    except Exception as e:
                        print(f"Hook error in {skill.name}: {e}")
        
        return results
    
    def get_skill_info(self, name: str = None) -> Union[Dict, List[Dict]]:
        """Récupère les infos d'un skill ou de tous les skills"""
        if name:
            skill = self.skills.get(name)
            if not skill:
                return None
            return {
                "name": skill.name,
                "description": skill.description,
                "source": skill.source.value,
                "version": skill.version,
                "author": skill.author,
                "loaded": skill.loaded,
                "hooks": skill.hooks,
                "dependencies": skill.dependencies
            }
        
        return [self.get_skill_info(name) for name in self.skills.keys()]
    
    def create_wrapper_skill_template(self, name: str, description: str = ""):
        """Crée un template pour un nouveau skill wrapper"""
        skill_dir = os.path.join(self.wrapper_skills_path, name)
        os.makedirs(skill_dir, exist_ok=True)
        
        # skill.json
        config = {
            "name": name,
            "description": description,
            "version": "1.0.0",
            "author": "",
            "entry": "skill.py",
            "hooks": ["pre_execute", "post_execute"],
            "tools": [],
            "dependencies": [],
            "config_schema": {}
        }
        
        with open(os.path.join(skill_dir, "skill.json"), "w") as f:
            json.dump(config, f, indent=2)
        
        # skill.py
        skill_code = f'''"""
{name} Skill for Kashiza
{description}
"""

class {name.title().replace("_", "")}Skill:
    """Skill implementation"""
    
    def __init__(self):
        self.name = "{name}"
        self.config = {{}}
    
    def initialize(self, config: dict):
        """Initialize with configuration"""
        self.config = config
        return self
    
    def execute(self, context: dict, **kwargs):
        """Execute the skill"""
        # Your implementation here
        result = {{
            "status": "success",
            "data": None
        }}
        return result
    
    def on_pre_execute(self, data):
        """Hook: Called before task execution"""
        pass
    
    def on_post_execute(self, data):
        """Hook: Called after task execution"""
        pass
'''
        
        with open(os.path.join(skill_dir, "skill.py"), "w") as f:
            f.write(skill_code)
        
        return skill_dir

# Singleton global
_skill_adapter: Optional[SkillAdapter] = None

def get_skill_adapter() -> SkillAdapter:
    global _skill_adapter
    if _skill_adapter is None:
        _skill_adapter = SkillAdapter()
    return _skill_adapter
